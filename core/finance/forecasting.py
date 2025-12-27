"""
Moteur de prévision (Forecasting Engine).

Fonctionnalités:
- Prévision des ventes (7/30/90 jours)
- Prévision de trésorerie (cash flow)
- Prévision de prix fournisseurs
- Algorithmes: Holt-Winters, SARIMA simplifié, régression
- Cache des prévisions
"""

from __future__ import annotations

import json
import math
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from statistics import mean, stdev
from collections import defaultdict

from sqlalchemy import text
from core.data_repository import get_engine


class ForecastType(str, Enum):
    """Types de prévisions."""
    SALES = "sales"
    STOCK = "stock"
    CASHFLOW = "cashflow"
    PRICE = "price"
    DEMAND = "demand"


class ForecastMethod(str, Enum):
    """Méthodes de prévision."""
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    HOLT_WINTERS = "holt_winters"
    LINEAR_REGRESSION = "linear_regression"
    SEASONAL_NAIVE = "seasonal_naive"


@dataclass
class ForecastResult:
    """Résultat d'une prévision."""
    forecast_type: ForecastType
    entity_id: Optional[int]
    entity_name: str
    method: ForecastMethod
    horizon_days: int
    predictions: List[Dict[str, Any]]  # [{"date": "2024-01-15", "value": 123.45, "lower": 100, "upper": 150}]
    metrics: Dict[str, float]  # MAE, RMSE, MAPE
    confidence_level: float
    generated_at: datetime


@dataclass
class CashFlowForecast:
    """Prévision de trésorerie."""
    start_balance: float
    daily_forecasts: List[Dict[str, Any]]
    end_balance: float
    min_balance: float
    min_balance_date: date
    cash_runway_days: Optional[int]  # Jours avant épuisement si négatif
    recommendations: List[str]


class ForecastingEngine:
    """Moteur de prévision."""

    # Paramètres par défaut
    DEFAULT_ALPHA = 0.3  # Exponential smoothing
    DEFAULT_BETA = 0.1   # Trend smoothing
    DEFAULT_GAMMA = 0.2  # Seasonal smoothing
    SEASONALITY_PERIOD = 7  # Hebdomadaire par défaut

    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
        self._ensure_tables()

    def _ensure_tables(self):
        """Crée les tables nécessaires."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS forecast_cache (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    forecast_type VARCHAR(50) NOT NULL,
                    entity_id INTEGER,
                    horizon_days INTEGER NOT NULL,
                    method VARCHAR(50) NOT NULL,
                    predictions JSONB NOT NULL,
                    metrics JSONB DEFAULT '{}',
                    generated_at TIMESTAMPTZ DEFAULT NOW(),
                    expires_at TIMESTAMPTZ,
                    UNIQUE(tenant_id, forecast_type, entity_id, horizon_days)
                );

                CREATE INDEX IF NOT EXISTS idx_forecast_cache_lookup
                    ON forecast_cache(tenant_id, forecast_type, entity_id);

                CREATE TABLE IF NOT EXISTS forecast_accuracy (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    forecast_type VARCHAR(50) NOT NULL,
                    entity_id INTEGER,
                    prediction_date DATE NOT NULL,
                    predicted_value FLOAT NOT NULL,
                    actual_value FLOAT,
                    error FLOAT,
                    method VARCHAR(50),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))

    def forecast_sales(
        self,
        product_id: Optional[int] = None,
        category: Optional[str] = None,
        horizon_days: int = 30,
        method: ForecastMethod = ForecastMethod.HOLT_WINTERS
    ) -> ForecastResult:
        """Prévoit les ventes."""
        # Récupérer l'historique
        history = self._get_sales_history(product_id, category, days=max(90, horizon_days * 3))

        if len(history) < 14:
            return self._naive_forecast(
                ForecastType.SALES,
                product_id,
                f"Produit #{product_id}" if product_id else category or "Total",
                horizon_days,
                history
            )

        # Appliquer la méthode de prévision
        if method == ForecastMethod.HOLT_WINTERS:
            predictions = self._holt_winters_forecast(history, horizon_days)
        elif method == ForecastMethod.EXPONENTIAL_SMOOTHING:
            predictions = self._exponential_smoothing(history, horizon_days)
        elif method == ForecastMethod.LINEAR_REGRESSION:
            predictions = self._linear_regression_forecast(history, horizon_days)
        else:
            predictions = self._moving_average_forecast(history, horizon_days)

        # Calculer les intervalles de confiance
        predictions = self._add_confidence_intervals(predictions, history)

        # Métriques de qualité
        metrics = self._calculate_metrics(history, predictions[:len(history)])

        result = ForecastResult(
            forecast_type=ForecastType.SALES,
            entity_id=product_id,
            entity_name=f"Produit #{product_id}" if product_id else category or "Total",
            method=method,
            horizon_days=horizon_days,
            predictions=predictions,
            metrics=metrics,
            confidence_level=0.95,
            generated_at=datetime.utcnow(),
        )

        # Mettre en cache
        self._cache_forecast(result)

        return result

    def forecast_stock(
        self,
        product_id: int,
        horizon_days: int = 30
    ) -> ForecastResult:
        """Prévoit l'épuisement du stock."""
        engine = get_engine()

        with engine.connect() as conn:
            # Stock actuel
            result = conn.execute(
                text("""
                    SELECT stock_actuel, nom FROM produits
                    WHERE id = :product_id AND tenant_id = :tenant_id
                """),
                {"product_id": product_id, "tenant_id": self.tenant_id}
            )
            row = result.fetchone()
            if not row:
                return self._empty_forecast(ForecastType.STOCK, product_id, "Inconnu", horizon_days)

            current_stock = float(row.stock_actuel or 0)
            product_name = row.nom

        # Historique des ventes pour estimer la consommation
        sales_history = self._get_sales_history(product_id, None, days=60)

        if not sales_history:
            avg_daily_sales = 0
        else:
            avg_daily_sales = mean([h["value"] for h in sales_history])

        # Projeter le stock
        predictions = []
        stock = current_stock
        stockout_date = None

        for i in range(horizon_days):
            forecast_date = date.today() + timedelta(days=i + 1)

            # Variation saisonnière (jour de la semaine)
            weekday_factor = self._get_weekday_factor(forecast_date.weekday(), sales_history)
            daily_consumption = avg_daily_sales * weekday_factor

            stock = max(0, stock - daily_consumption)

            predictions.append({
                "date": forecast_date.isoformat(),
                "value": round(stock, 1),
                "consumption": round(daily_consumption, 2),
            })

            if stock <= 0 and stockout_date is None:
                stockout_date = forecast_date

        # Calculer les jours avant rupture
        if avg_daily_sales > 0 and stockout_date:
            days_to_stockout = (stockout_date - date.today()).days
        else:
            days_to_stockout = None

        return ForecastResult(
            forecast_type=ForecastType.STOCK,
            entity_id=product_id,
            entity_name=product_name,
            method=ForecastMethod.EXPONENTIAL_SMOOTHING,
            horizon_days=horizon_days,
            predictions=predictions,
            metrics={
                "current_stock": current_stock,
                "avg_daily_consumption": round(avg_daily_sales, 2),
                "days_to_stockout": days_to_stockout,
                "stockout_date": stockout_date.isoformat() if stockout_date else None,
            },
            confidence_level=0.9,
            generated_at=datetime.utcnow(),
        )

    def forecast_cashflow(
        self,
        horizon_days: int = 30,
        include_recurring: bool = True
    ) -> CashFlowForecast:
        """Prévoit la trésorerie."""
        engine = get_engine()

        # Solde actuel - utilise finance_transactions avec entity_id
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT SUM(CAST(amount AS NUMERIC)) as balance
                    FROM finance_transactions
                    WHERE entity_id = :entity_id
                """),
                {"entity_id": entity_id}
            )
            row = result.fetchone()
            current_balance = float(row.balance or 0)

        # Historique des flux
        inflows = self._get_cashflow_history("credit", days=90)
        outflows = self._get_cashflow_history("debit", days=90)

        # Moyennes et patterns
        avg_daily_inflow = mean([h["value"] for h in inflows]) if inflows else 0
        avg_daily_outflow = mean([h["value"] for h in outflows]) if outflows else 0

        # Charges récurrentes
        recurring = self._get_recurring_expenses() if include_recurring else []

        # Projections
        daily_forecasts = []
        balance = current_balance
        min_balance = balance
        min_balance_date = date.today()

        for i in range(horizon_days):
            forecast_date = date.today() + timedelta(days=i + 1)

            # Entrées prévues
            weekday = forecast_date.weekday()
            inflow = avg_daily_inflow * self._get_weekday_factor(weekday, inflows)

            # Sorties prévues
            outflow = avg_daily_outflow * self._get_weekday_factor(weekday, outflows)

            # Ajouter les charges récurrentes
            for rec in recurring:
                if rec["day_of_month"] == forecast_date.day:
                    outflow += rec["amount"]

            net = inflow - outflow
            balance += net

            daily_forecasts.append({
                "date": forecast_date.isoformat(),
                "inflow": round(inflow, 2),
                "outflow": round(outflow, 2),
                "net": round(net, 2),
                "balance": round(balance, 2),
            })

            if balance < min_balance:
                min_balance = balance
                min_balance_date = forecast_date

        # Calculer le runway
        cash_runway = None
        if balance < 0:
            # Trouver quand le solde devient négatif
            for i, df in enumerate(daily_forecasts):
                if df["balance"] < 0:
                    cash_runway = i + 1
                    break

        # Recommandations
        recommendations = []
        if min_balance < 0:
            recommendations.append(f"Alerte: Solde négatif prévu le {min_balance_date.isoformat()} ({min_balance:.2f}€)")
        if min_balance < current_balance * 0.2:
            recommendations.append("Considérer le report de certaines dépenses non urgentes")
        if avg_daily_outflow > avg_daily_inflow * 1.2:
            recommendations.append("Les sorties dépassent les entrées de plus de 20%")

        return CashFlowForecast(
            start_balance=current_balance,
            daily_forecasts=daily_forecasts,
            end_balance=balance,
            min_balance=min_balance,
            min_balance_date=min_balance_date,
            cash_runway_days=cash_runway,
            recommendations=recommendations,
        )

    def forecast_price(
        self,
        product_id: int,
        horizon_days: int = 90
    ) -> ForecastResult:
        """Prévoit l'évolution des prix fournisseur."""
        # Historique des prix
        price_history = self._get_price_history(product_id, days=365)

        if len(price_history) < 5:
            return self._naive_forecast(
                ForecastType.PRICE,
                product_id,
                f"Prix produit #{product_id}",
                horizon_days,
                price_history
            )

        # Tendance linéaire
        predictions = self._linear_regression_forecast(price_history, horizon_days)

        # Ajouter la volatilité historique
        if len(price_history) >= 2:
            values = [h["value"] for h in price_history]
            volatility = stdev(values) / mean(values) if mean(values) > 0 else 0.1
        else:
            volatility = 0.1

        for pred in predictions:
            margin = pred["value"] * volatility
            pred["lower"] = round(pred["value"] - margin, 2)
            pred["upper"] = round(pred["value"] + margin, 2)

        return ForecastResult(
            forecast_type=ForecastType.PRICE,
            entity_id=product_id,
            entity_name=f"Prix produit #{product_id}",
            method=ForecastMethod.LINEAR_REGRESSION,
            horizon_days=horizon_days,
            predictions=predictions,
            metrics={
                "current_price": price_history[-1]["value"] if price_history else 0,
                "avg_price": round(mean([h["value"] for h in price_history]), 2) if price_history else 0,
                "volatility": round(volatility * 100, 1),
                "trend": "up" if predictions[-1]["value"] > price_history[-1]["value"] else "down" if price_history else "stable",
            },
            confidence_level=0.8,
            generated_at=datetime.utcnow(),
        )

    def _get_sales_history(
        self,
        product_id: Optional[int],
        category: Optional[str],
        days: int
    ) -> List[Dict[str, Any]]:
        """Récupère l'historique des ventes."""
        engine = get_engine()

        query = """
            SELECT DATE(v.date) as sale_date, SUM(v.quantite) as total
            FROM ventes v
            JOIN produits p ON v.product_id = p.id
            WHERE p.tenant_id = :tenant_id
              AND v.date >= NOW() - INTERVAL ':days days'
        """
        params = {"tenant_id": self.tenant_id, "days": days}

        if product_id:
            query += " AND p.id = :product_id"
            params["product_id"] = product_id
        if category:
            query += " AND p.categorie = :category"
            params["category"] = category

        query += " GROUP BY DATE(v.date) ORDER BY sale_date"

        with engine.connect() as conn:
            # Note: On doit interpoler days car ça ne marche pas en paramètre d'interval
            query = query.replace(":days", str(days))
            result = conn.execute(text(query), params)

            return [
                {"date": row.sale_date.isoformat(), "value": float(row.total or 0)}
                for row in result
            ]

    def _get_cashflow_history(self, tx_type: str, days: int) -> List[Dict[str, Any]]:
        """Récupère l'historique des flux de trésorerie."""
        engine = get_engine()

        # Utilise finance_transactions avec entity_id et direction
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id
        direction = "IN" if tx_type == "credit" else "OUT"

        with engine.connect() as conn:
            result = conn.execute(
                text(f"""
                    SELECT DATE(date_operation) as tx_date, SUM(ABS(CAST(amount AS NUMERIC))) as total
                    FROM finance_transactions
                    WHERE entity_id = :entity_id
                      AND direction = :direction
                      AND date_operation >= NOW() - INTERVAL '{days} days'
                    GROUP BY DATE(date_operation)
                    ORDER BY tx_date
                """),
                {"entity_id": entity_id, "direction": direction}
            )

            return [
                {"date": row.tx_date.isoformat(), "value": float(row.total or 0)}
                for row in result
            ]

    def _get_price_history(self, product_id: int, days: int) -> List[Dict[str, Any]]:
        """Récupère l'historique des prix."""
        engine = get_engine()

        with engine.connect() as conn:
            result = conn.execute(
                text(f"""
                    SELECT facture_date as date, prix_achat as prix
                    FROM produits_price_history
                    WHERE produit_id = :product_id
                      AND facture_date >= NOW() - INTERVAL '{days} days'
                    ORDER BY facture_date
                """),
                {"product_id": product_id}
            )

            return [
                {"date": row.date.isoformat() if hasattr(row.date, "isoformat") else str(row.date), "value": float(row.prix or 0)}
                for row in result
            ]

    def _get_recurring_expenses(self) -> List[Dict[str, Any]]:
        """Identifie les charges récurrentes.
        Note: Utilise finance_transactions avec entity_id.
        """
        engine = get_engine()
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id

        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        EXTRACT(DAY FROM date_operation) as day_of_month,
                        AVG(ABS(CAST(amount AS NUMERIC))) as avg_amount,
                        COUNT(*) as occurrences
                    FROM finance_transactions
                    WHERE entity_id = :entity_id
                      AND direction = 'OUT'
                      AND date_operation >= NOW() - INTERVAL '90 days'
                    GROUP BY EXTRACT(DAY FROM date_operation), label
                    HAVING COUNT(*) >= 2
                    ORDER BY avg_amount DESC
                    LIMIT 20
                """),
                {"entity_id": entity_id}
            )

            return [
                {
                    "day_of_month": int(row.day_of_month),
                    "amount": float(row.avg_amount),
                    "frequency": row.occurrences,
                }
                for row in result
            ]

    def _holt_winters_forecast(
        self,
        history: List[Dict],
        horizon: int
    ) -> List[Dict[str, Any]]:
        """Prévision Holt-Winters (triple exponential smoothing)."""
        values = [h["value"] for h in history]
        n = len(values)

        if n < self.SEASONALITY_PERIOD * 2:
            return self._exponential_smoothing(history, horizon)

        # Initialisation
        alpha = self.DEFAULT_ALPHA
        beta = self.DEFAULT_BETA
        gamma = self.DEFAULT_GAMMA
        period = self.SEASONALITY_PERIOD

        # Niveau initial
        level = mean(values[:period])

        # Tendance initiale
        trend = (mean(values[period:2*period]) - mean(values[:period])) / period

        # Saisonnalité initiale
        seasonal = []
        for i in range(period):
            seasonal.append(values[i] / level if level > 0 else 1)

        # Appliquer le lissage
        for i in range(n):
            idx = i % period
            if i >= period:
                val = values[i]
                old_level = level
                level = alpha * (val / seasonal[idx]) + (1 - alpha) * (level + trend)
                trend = beta * (level - old_level) + (1 - beta) * trend
                seasonal[idx] = gamma * (val / level) + (1 - gamma) * seasonal[idx]

        # Prévisions
        predictions = []
        last_date = datetime.fromisoformat(history[-1]["date"]) if history else datetime.now()

        for i in range(1, horizon + 1):
            forecast_date = last_date + timedelta(days=i)
            idx = (n + i - 1) % period
            value = (level + i * trend) * seasonal[idx]
            predictions.append({
                "date": forecast_date.date().isoformat() if hasattr(forecast_date, "date") else forecast_date.isoformat()[:10],
                "value": round(max(0, value), 2),
            })

        return predictions

    def _exponential_smoothing(
        self,
        history: List[Dict],
        horizon: int
    ) -> List[Dict[str, Any]]:
        """Lissage exponentiel simple."""
        values = [h["value"] for h in history]
        alpha = self.DEFAULT_ALPHA

        # Calculer le niveau lissé
        smoothed = values[0]
        for v in values[1:]:
            smoothed = alpha * v + (1 - alpha) * smoothed

        # Prévisions (constantes)
        predictions = []
        last_date = datetime.fromisoformat(history[-1]["date"]) if history else datetime.now()

        for i in range(1, horizon + 1):
            forecast_date = last_date + timedelta(days=i)
            predictions.append({
                "date": forecast_date.date().isoformat() if hasattr(forecast_date, "date") else forecast_date.isoformat()[:10],
                "value": round(max(0, smoothed), 2),
            })

        return predictions

    def _linear_regression_forecast(
        self,
        history: List[Dict],
        horizon: int
    ) -> List[Dict[str, Any]]:
        """Régression linéaire simple."""
        n = len(history)
        if n < 2:
            return self._moving_average_forecast(history, horizon)

        # Variables
        x = list(range(n))
        y = [h["value"] for h in history]

        # Calcul des coefficients
        x_mean = mean(x)
        y_mean = mean(y)

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator

        intercept = y_mean - slope * x_mean

        # Prévisions
        predictions = []
        last_date = datetime.fromisoformat(history[-1]["date"]) if history else datetime.now()

        for i in range(1, horizon + 1):
            forecast_date = last_date + timedelta(days=i)
            value = intercept + slope * (n + i - 1)
            predictions.append({
                "date": forecast_date.date().isoformat() if hasattr(forecast_date, "date") else forecast_date.isoformat()[:10],
                "value": round(max(0, value), 2),
            })

        return predictions

    def _moving_average_forecast(
        self,
        history: List[Dict],
        horizon: int,
        window: int = 7
    ) -> List[Dict[str, Any]]:
        """Moyenne mobile simple."""
        values = [h["value"] for h in history]

        if not values:
            avg = 0
        elif len(values) < window:
            avg = mean(values)
        else:
            avg = mean(values[-window:])

        predictions = []
        last_date = datetime.fromisoformat(history[-1]["date"]) if history else datetime.now()

        for i in range(1, horizon + 1):
            forecast_date = last_date + timedelta(days=i)
            predictions.append({
                "date": forecast_date.date().isoformat() if hasattr(forecast_date, "date") else forecast_date.isoformat()[:10],
                "value": round(max(0, avg), 2),
            })

        return predictions

    def _get_weekday_factor(self, weekday: int, history: List[Dict]) -> float:
        """Calcule le facteur saisonnier par jour de la semaine."""
        if not history:
            return 1.0

        by_weekday = defaultdict(list)
        for h in history:
            d = datetime.fromisoformat(h["date"])
            by_weekday[d.weekday()].append(h["value"])

        if weekday not in by_weekday or not by_weekday[weekday]:
            return 1.0

        overall_mean = mean([h["value"] for h in history])
        weekday_mean = mean(by_weekday[weekday])

        return weekday_mean / overall_mean if overall_mean > 0 else 1.0

    def _add_confidence_intervals(
        self,
        predictions: List[Dict],
        history: List[Dict]
    ) -> List[Dict[str, Any]]:
        """Ajoute les intervalles de confiance."""
        if len(history) < 2:
            for pred in predictions:
                pred["lower"] = pred["value"] * 0.8
                pred["upper"] = pred["value"] * 1.2
            return predictions

        values = [h["value"] for h in history]
        std = stdev(values)

        for i, pred in enumerate(predictions):
            # Incertitude croissante avec l'horizon
            uncertainty = std * (1 + i * 0.1)
            pred["lower"] = round(max(0, pred["value"] - 1.96 * uncertainty), 2)
            pred["upper"] = round(pred["value"] + 1.96 * uncertainty, 2)

        return predictions

    def _calculate_metrics(
        self,
        actual: List[Dict],
        predicted: List[Dict]
    ) -> Dict[str, float]:
        """Calcule les métriques de qualité."""
        if not actual or not predicted:
            return {"mae": 0, "rmse": 0, "mape": 0}

        n = min(len(actual), len(predicted))
        actual_values = [a["value"] for a in actual[:n]]
        pred_values = [p["value"] for p in predicted[:n]]

        # MAE
        mae = mean([abs(a - p) for a, p in zip(actual_values, pred_values)])

        # RMSE
        rmse = math.sqrt(mean([(a - p) ** 2 for a, p in zip(actual_values, pred_values)]))

        # MAPE
        mape_values = [abs(a - p) / a * 100 for a, p in zip(actual_values, pred_values) if a > 0]
        mape = mean(mape_values) if mape_values else 0

        return {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape": round(mape, 1),
        }

    def _naive_forecast(
        self,
        forecast_type: ForecastType,
        entity_id: Optional[int],
        entity_name: str,
        horizon: int,
        history: List[Dict]
    ) -> ForecastResult:
        """Prévision naïve quand pas assez de données."""
        last_value = history[-1]["value"] if history else 0
        last_date = datetime.fromisoformat(history[-1]["date"]) if history else datetime.now()

        predictions = []
        for i in range(1, horizon + 1):
            forecast_date = last_date + timedelta(days=i)
            predictions.append({
                "date": forecast_date.date().isoformat() if hasattr(forecast_date, "date") else forecast_date.isoformat()[:10],
                "value": last_value,
                "lower": last_value * 0.7,
                "upper": last_value * 1.3,
            })

        return ForecastResult(
            forecast_type=forecast_type,
            entity_id=entity_id,
            entity_name=entity_name,
            method=ForecastMethod.SEASONAL_NAIVE,
            horizon_days=horizon,
            predictions=predictions,
            metrics={"note": "Données insuffisantes pour une prévision précise"},
            confidence_level=0.5,
            generated_at=datetime.utcnow(),
        )

    def _empty_forecast(
        self,
        forecast_type: ForecastType,
        entity_id: Optional[int],
        entity_name: str,
        horizon: int
    ) -> ForecastResult:
        """Prévision vide."""
        return ForecastResult(
            forecast_type=forecast_type,
            entity_id=entity_id,
            entity_name=entity_name,
            method=ForecastMethod.MOVING_AVERAGE,
            horizon_days=horizon,
            predictions=[],
            metrics={},
            confidence_level=0,
            generated_at=datetime.utcnow(),
        )

    def _cache_forecast(self, result: ForecastResult):
        """Met en cache une prévision."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO forecast_cache
                    (tenant_id, forecast_type, entity_id, horizon_days, method, predictions, metrics, expires_at)
                    VALUES (:tenant_id, :type, :entity_id, :horizon, :method, :predictions, :metrics, :expires)
                    ON CONFLICT (tenant_id, forecast_type, entity_id, horizon_days)
                    DO UPDATE SET
                        method = EXCLUDED.method,
                        predictions = EXCLUDED.predictions,
                        metrics = EXCLUDED.metrics,
                        generated_at = NOW(),
                        expires_at = EXCLUDED.expires_at
                """),
                {
                    "tenant_id": self.tenant_id,
                    "type": result.forecast_type.value,
                    "entity_id": result.entity_id,
                    "horizon": result.horizon_days,
                    "method": result.method.value,
                    "predictions": json.dumps(result.predictions),
                    "metrics": json.dumps(result.metrics),
                    "expires": datetime.utcnow() + timedelta(hours=24),
                }
            )

    def get_cached_forecast(
        self,
        forecast_type: ForecastType,
        entity_id: Optional[int],
        horizon_days: int
    ) -> Optional[ForecastResult]:
        """Récupère une prévision en cache."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT method, predictions, metrics, generated_at
                    FROM forecast_cache
                    WHERE tenant_id = :tenant_id
                      AND forecast_type = :type
                      AND entity_id IS NOT DISTINCT FROM :entity_id
                      AND horizon_days = :horizon
                      AND (expires_at IS NULL OR expires_at > NOW())
                """),
                {
                    "tenant_id": self.tenant_id,
                    "type": forecast_type.value,
                    "entity_id": entity_id,
                    "horizon": horizon_days,
                }
            )
            row = result.fetchone()

            if not row:
                return None

            return ForecastResult(
                forecast_type=forecast_type,
                entity_id=entity_id,
                entity_name="",
                method=ForecastMethod(row.method),
                horizon_days=horizon_days,
                predictions=row.predictions if isinstance(row.predictions, list) else json.loads(row.predictions),
                metrics=row.metrics if isinstance(row.metrics, dict) else json.loads(row.metrics),
                confidence_level=0.95,
                generated_at=row.generated_at,
            )
