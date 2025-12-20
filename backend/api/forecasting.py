"""
API Endpoints pour Forecasting Engine
=====================================

Endpoints pour:
- Sales Forecasting (Holt-Winters, régression)
- Stock Depletion Forecasting
- Cash Flow Forecasting
- Price Trend Forecasting
"""

from decimal import Decimal
from typing import List, Optional
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.dependencies.tenant import Tenant, get_current_tenant
from core.data_repository import query_df
from core.finance.forecasting import (
    ForecastingEngine,
    ForecastMethod,
    ForecastType,
)

router = APIRouter(prefix="/forecasting", tags=["forecasting"])


# =============================================================================
# SCHEMAS
# =============================================================================

class ForecastPoint(BaseModel):
    date: date
    value: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class SalesForecastRequest(BaseModel):
    horizon_days: int = Field(default=30, ge=1, le=365)
    method: Optional[str] = None  # HOLT_WINTERS, EXPONENTIAL_SMOOTHING, LINEAR_REGRESSION, MOVING_AVERAGE


class SalesForecastResponse(BaseModel):
    method: str
    horizon_days: int
    predictions: List[ForecastPoint]
    confidence: float
    trend: str
    seasonality_detected: bool
    metrics: dict


class ProductForecastResponse(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    average_daily_consumption: float
    predicted_depletion_date: Optional[date]
    days_until_depletion: Optional[float]
    confidence: float
    recommended_reorder_date: Optional[date]


class CashFlowForecastResponse(BaseModel):
    period_start: date
    period_end: date
    predictions: List[ForecastPoint]
    total_inflows: float
    total_outflows: float
    net_cash_flow: float
    ending_balance: float
    alerts: List[str]


class PriceTrendResponse(BaseModel):
    product_id: int
    product_name: str
    current_price: float
    predicted_prices: List[ForecastPoint]
    trend_direction: str  # "en hausse", "en baisse", "stable"
    trend_strength: float  # 0-1
    volatility: float


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_effective_tenant(tenant_id: int) -> int:
    """Le tenant intelligence (4) accède aux données restaurant (2)."""
    return 2 if tenant_id == 4 else tenant_id


def _get_sales_history(tenant_id: int, days: int = 90) -> List[dict]:
    """Récupère l'historique des ventes depuis restaurant_sales"""
    effective_tenant = _get_effective_tenant(tenant_id)
    sql = """
        SELECT
            sold_at::date as date,
            SUM(quantity * p.prix_vente_ttc) as amount
        FROM restaurant_sales rs
        JOIN restaurant_plats p ON p.id = rs.plat_id
        WHERE rs.tenant_id = :tenant_id
          AND rs.sold_at >= CURRENT_DATE - :days * INTERVAL '1 day'
        GROUP BY sold_at::date
        ORDER BY sold_at::date
    """
    df = query_df(sql, params={"tenant_id": effective_tenant, "days": days})
    if df.empty:
        return []
    return [{"date": row['date'], "amount": Decimal(str(row['amount'] or 0))} for _, row in df.iterrows()]


def _get_product_consumption(tenant_id: int, product_id: int, days: int = 90) -> List[dict]:
    """Récupère l'historique de consommation d'un produit"""
    # Pour les produits, utiliser tenant épicerie (1)
    effective_tenant = 1 if tenant_id == 4 else tenant_id
    sql = """
        SELECT
            date_mvt::date as date,
            SUM(quantite) as quantity
        FROM mouvements_stock
        WHERE tenant_id = :tenant_id
          AND produit_id = :product_id
          AND type = 'SORTIE'
          AND date_mvt >= CURRENT_DATE - :days * INTERVAL '1 day'
        GROUP BY date_mvt::date
        ORDER BY date
    """
    df = query_df(sql, params={"tenant_id": effective_tenant, "product_id": product_id, "days": days})
    if df.empty:
        return []
    return [{"date": row['date'], "quantity": Decimal(str(row['quantity']))} for _, row in df.iterrows()]


def _get_cash_transactions(tenant_id: int, days: int = 90) -> List[dict]:
    """Récupère les transactions de trésorerie depuis finance_transactions.

    Note: finance_transactions utilise entity_id (pas tenant_id).
    On mappe: tenant 4 (intelligence) -> entity 2 ou 3, autres -> même ID.
    """
    # Mapper tenant vers entity: restaurant=2, trésorerie=3
    entity_id = 2 if tenant_id == 4 else tenant_id
    sql = """
        SELECT
            date_operation::date as date,
            CASE WHEN direction = 'IN' THEN CAST(amount AS NUMERIC) ELSE 0 END as inflow,
            CASE WHEN direction = 'OUT' THEN CAST(amount AS NUMERIC) ELSE 0 END as outflow,
            COALESCE(label, '') as libelle
        FROM finance_transactions
        WHERE entity_id = :entity_id
          AND date_operation >= CURRENT_DATE - :days * INTERVAL '1 day'
        ORDER BY date_operation
    """
    df = query_df(sql, params={"entity_id": entity_id, "days": days})
    if df.empty:
        return []
    return df.to_dict('records')


def _get_price_history(tenant_id: int, product_id: int, days: int = 180) -> List[dict]:
    """Récupère l'historique des prix d'un produit"""
    sql = """
        SELECT
            recorded_at::date as date,
            prix_achat as price
        FROM produits_price_history
        WHERE produit_id = :product_id
          AND recorded_at >= CURRENT_DATE - :days * INTERVAL '1 day'
        ORDER BY recorded_at
    """
    df = query_df(sql, params={"product_id": product_id, "days": days})
    if df.empty:
        return []
    return [{"date": row['date'], "price": Decimal(str(row['price']))} for _, row in df.iterrows()]


def _get_method_enum(method_str: Optional[str]) -> Optional[ForecastMethod]:
    """Convertit string en ForecastMethod enum"""
    if not method_str:
        return None
    mapping = {
        "HOLT_WINTERS": ForecastMethod.HOLT_WINTERS,
        "EXPONENTIAL_SMOOTHING": ForecastMethod.EXPONENTIAL_SMOOTHING,
        "LINEAR_REGRESSION": ForecastMethod.LINEAR_REGRESSION,
        "MOVING_AVERAGE": ForecastMethod.MOVING_AVERAGE,
    }
    return mapping.get(method_str.upper())


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/sales", response_model=SalesForecastResponse)
def forecast_sales(
    request: SalesForecastRequest,
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Prévision des ventes avec plusieurs algorithmes disponibles:
    - HOLT_WINTERS: Triple exponential smoothing (saisonnalité)
    - EXPONENTIAL_SMOOTHING: Lissage simple
    - LINEAR_REGRESSION: Tendance linéaire
    - MOVING_AVERAGE: Moyenne mobile

    Si aucune méthode n'est spécifiée, la meilleure est choisie automatiquement.
    """
    engine = ForecastingEngine(tenant_id=tenant.id)
    sales_data = _get_sales_history(tenant.id, days=180)

    if len(sales_data) < 7:
        raise HTTPException(
            status_code=400,
            detail="Pas assez de données historiques pour la prévision (minimum 7 jours)"
        )

    method = _get_method_enum(request.method)
    forecast = engine.forecast_sales(sales_data, request.horizon_days, method)

    # Construire les points de prévision
    start_date = date.today() + timedelta(days=1)
    predictions = []
    for i, value in enumerate(forecast.predictions):
        pred_date = start_date + timedelta(days=i)
        lower = forecast.lower_bounds[i] if forecast.lower_bounds else None
        upper = forecast.upper_bounds[i] if forecast.upper_bounds else None
        predictions.append(ForecastPoint(
            date=pred_date,
            value=float(value),
            lower_bound=float(lower) if lower else None,
            upper_bound=float(upper) if upper else None
        ))

    return SalesForecastResponse(
        method=forecast.method.value,
        horizon_days=request.horizon_days,
        predictions=predictions,
        confidence=forecast.confidence,
        trend=forecast.trend,
        seasonality_detected=forecast.seasonality_detected,
        metrics=forecast.metrics
    )


@router.get("/stock-depletion", response_model=List[ProductForecastResponse])
def forecast_stock_depletion(
    days_horizon: int = Query(default=60, ge=1, le=180),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Prévoit la date d'épuisement du stock pour chaque produit.
    Inclut une recommandation de date de réapprovisionnement.
    """
    # Récupérer les produits avec stock
    sql = """
        SELECT
            p.id as product_id,
            p.nom as product_name,
            p.stock_actuel as current_stock,
            AVG(sm.quantite) as avg_daily
        FROM produits p
        LEFT JOIN mouvements_stock sm ON sm.produit_id = p.id
            AND sm.tenant_id = p.tenant_id
            AND sm.type = 'SORTIE'
            AND sm.date_mvt >= CURRENT_DATE - INTERVAL '30 days'
        WHERE p.tenant_id = :tenant_id
          AND p.actif = true
          AND p.stock_actuel > 0
        GROUP BY p.id, p.nom, p.stock_actuel
        HAVING AVG(sm.quantite) > 0
    """
    df = query_df(sql, params={"tenant_id": tenant.id})

    results = []
    for _, row in df.iterrows():
        current_stock = float(row['current_stock'] or 0)
        avg_daily = float(row['avg_daily'] or 0)

        if avg_daily > 0:
            days_until = current_stock / avg_daily
            depletion_date = date.today() + timedelta(days=days_until)

            # Recommander commande 5 jours avant épuisement
            reorder_date = depletion_date - timedelta(days=5)
            if reorder_date < date.today():
                reorder_date = date.today()
        else:
            days_until = None
            depletion_date = None
            reorder_date = None

        results.append(ProductForecastResponse(
            product_id=int(row['product_id']),
            product_name=row['product_name'],
            current_stock=int(current_stock),
            average_daily_consumption=avg_daily,
            predicted_depletion_date=depletion_date if days_until and days_until <= days_horizon else None,
            days_until_depletion=days_until if days_until and days_until <= days_horizon else None,
            confidence=0.85,
            recommended_reorder_date=reorder_date if days_until and days_until <= days_horizon else None
        ))

    # Trier par jours restants
    results.sort(key=lambda x: x.days_until_depletion or float('inf'))

    return results


@router.get("/cash-flow", response_model=CashFlowForecastResponse)
def forecast_cash_flow(
    horizon_days: int = Query(default=30, ge=7, le=90),
    starting_balance: float = Query(default=0.0),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Prévision de trésorerie basée sur:
    - Historique des encaissements
    - Historique des décaissements
    - Détection des charges récurrentes

    Retourne les prévisions jour par jour avec alertes si solde négatif.
    """
    try:
        engine = ForecastingEngine(tenant_id=tenant.id)
        # forecast_cashflow fait ses propres requêtes en base
        forecast = engine.forecast_cashflow(horizon_days=horizon_days)

        # Construire les points de prévision depuis le résultat
        predictions = []
        total_inflows = 0.0
        total_outflows = 0.0
        alerts = []

        for day in forecast.daily_forecasts:
            predictions.append(ForecastPoint(
                date=date.fromisoformat(day["date"]),
                value=float(day["net"]),
                lower_bound=float(day["balance"]) * 0.9,
                upper_bound=float(day["balance"]) * 1.1
            ))
            total_inflows += day["inflow"]
            total_outflows += day["outflow"]
            if day["balance"] < 0:
                alerts.append(f"Solde négatif prévu le {day['date']}: {day['balance']:.2f}€")

        return CashFlowForecastResponse(
            period_start=date.today() + timedelta(days=1),
            period_end=date.today() + timedelta(days=horizon_days),
            predictions=predictions,
            total_inflows=total_inflows,
            total_outflows=total_outflows,
            net_cash_flow=total_inflows - total_outflows,
            ending_balance=forecast.daily_forecasts[-1]["balance"] if forecast.daily_forecasts else starting_balance,
            alerts=alerts[:5]
        )
    except Exception as e:
        # En cas d'erreur, retourner une prévision vide
        import logging
        logging.warning(f"Erreur forecast cash-flow: {e}")
        today = date.today()
        return CashFlowForecastResponse(
            period_start=today,
            period_end=today + timedelta(days=horizon_days),
            predictions=[],
            total_inflows=0,
            total_outflows=0,
            net_cash_flow=0,
            ending_balance=starting_balance,
            alerts=["Pas assez de données historiques pour la prévision"]
        )


@router.get("/price-trend/{product_id}", response_model=PriceTrendResponse)
def forecast_price_trend(
    product_id: int,
    horizon_days: int = Query(default=30, ge=7, le=90),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Prévision de l'évolution des prix d'un produit.
    Utile pour anticiper les hausses et négocier avec les fournisseurs.
    """
    # Récupérer le produit
    product_sql = """
        SELECT id, nom, prix_achat
        FROM produits
        WHERE id = :product_id AND tenant_id = :tenant_id
    """
    product_df = query_df(product_sql, params={"product_id": product_id, "tenant_id": tenant.id})

    if product_df.empty:
        raise HTTPException(status_code=404, detail="Produit non trouvé")

    product = product_df.iloc[0]
    price_history = _get_price_history(tenant.id, product_id, days=180)

    if len(price_history) < 3:
        # Pas assez d'historique, retourner prix stable
        current_price = float(product['prix_achat'] or 0)
        return PriceTrendResponse(
            product_id=product_id,
            product_name=product['nom'],
            current_price=current_price,
            predicted_prices=[
                ForecastPoint(
                    date=date.today() + timedelta(days=i),
                    value=current_price
                )
                for i in range(1, horizon_days + 1)
            ],
            trend_direction="stable",
            trend_strength=0.0,
            volatility=0.0
        )

    engine = ForecastingEngine(tenant_id=tenant.id)
    forecast = engine.forecast_price_trend(price_history, horizon_days)

    # Déterminer la tendance
    first_price = float(price_history[0]['price'])
    last_price = float(price_history[-1]['price'])
    change_pct = (last_price - first_price) / first_price if first_price > 0 else 0

    if change_pct > 0.05:
        trend_direction = "increasing"
    elif change_pct < -0.05:
        trend_direction = "decreasing"
    else:
        trend_direction = "stable"

    trend_strength = min(abs(change_pct), 1.0)

    # Calculer volatilité
    prices = [float(p['price']) for p in price_history]
    if len(prices) > 1:
        import statistics
        volatility = statistics.stdev(prices) / statistics.mean(prices) if statistics.mean(prices) > 0 else 0
    else:
        volatility = 0

    # Construire prévisions
    start_date = date.today() + timedelta(days=1)
    predictions = [
        ForecastPoint(
            date=start_date + timedelta(days=i),
            value=float(forecast.predictions[i]),
            lower_bound=float(forecast.lower_bounds[i]) if forecast.lower_bounds else None,
            upper_bound=float(forecast.upper_bounds[i]) if forecast.upper_bounds else None
        )
        for i in range(len(forecast.predictions))
    ]

    return PriceTrendResponse(
        product_id=product_id,
        product_name=product['nom'],
        current_price=last_price,
        predicted_prices=predictions,
        trend_direction=trend_direction,
        trend_strength=trend_strength,
        volatility=volatility
    )


@router.get("/summary")
def get_forecasting_summary(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Résumé des prévisions:
    - Tendance ventes (hausse/baisse)
    - Produits en épuisement imminent
    - Prévision trésorerie 7 jours
    """
    # Ventes récentes vs précédent (depuis restaurant_sales)
    # Tenant intelligence (4) accède au tenant restaurant (2)
    sales_tenant = 2 if tenant.id == 4 else tenant.id
    sales_sql = """
        SELECT
            SUM(CASE WHEN rs.sold_at >= CURRENT_DATE - INTERVAL '7 days' THEN rs.quantity * p.prix_vente_ttc ELSE 0 END) as recent,
            SUM(CASE WHEN rs.sold_at >= CURRENT_DATE - INTERVAL '14 days' AND rs.sold_at < CURRENT_DATE - INTERVAL '7 days'
                THEN rs.quantity * p.prix_vente_ttc ELSE 0 END) as previous
        FROM restaurant_sales rs
        JOIN restaurant_plats p ON p.id = rs.plat_id
        WHERE rs.tenant_id = :tenant_id
          AND rs.sold_at >= CURRENT_DATE - INTERVAL '14 days'
    """
    sales_df = query_df(sales_sql, params={"tenant_id": sales_tenant})

    recent_sales = float(sales_df.iloc[0]['recent'] or 0) if not sales_df.empty else 0
    previous_sales = float(sales_df.iloc[0]['previous'] or 0) if not sales_df.empty else 0

    if previous_sales > 0:
        sales_trend_pct = ((recent_sales - previous_sales) / previous_sales) * 100
    else:
        sales_trend_pct = 0

    # Produits en épuisement < 7 jours
    # Tenant intelligence (4) accède au tenant épicerie (1)
    product_tenant = 1 if tenant.id == 4 else tenant.id
    depletion_sql = """
        SELECT COUNT(*) as count
        FROM produits p
        LEFT JOIN (
            SELECT produit_id, AVG(quantite) as avg_daily
            FROM mouvements_stock
            WHERE tenant_id = :tenant_id
              AND type = 'SORTIE'
              AND date_mvt >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY produit_id
        ) sm ON sm.produit_id = p.id
        WHERE p.tenant_id = :tenant_id
          AND p.actif = true
          AND p.stock_actuel > 0
          AND sm.avg_daily > 0
          AND p.stock_actuel / sm.avg_daily < 7
    """
    depletion_df = query_df(depletion_sql, params={"tenant_id": product_tenant})
    products_depleting = int(depletion_df.iloc[0]['count'] or 0) if not depletion_df.empty else 0

    # Trésorerie 7 derniers jours (depuis finance_transactions)
    # finance_transactions utilise entity_id (pas tenant_id)
    cash_entity = 2 if tenant.id == 4 else tenant.id
    cash_sql = """
        SELECT
            SUM(CASE WHEN direction = 'IN' THEN CAST(amount AS NUMERIC) ELSE 0 END) as inflows,
            SUM(CASE WHEN direction = 'OUT' THEN CAST(amount AS NUMERIC) ELSE 0 END) as outflows
        FROM finance_transactions
        WHERE entity_id = :entity_id
          AND date_operation >= CURRENT_DATE - INTERVAL '7 days'
    """
    cash_df = query_df(cash_sql, params={"entity_id": cash_entity})

    recent_inflows = float(cash_df.iloc[0]['inflows'] or 0) if not cash_df.empty else 0
    recent_outflows = float(cash_df.iloc[0]['outflows'] or 0) if not cash_df.empty else 0

    return {
        "sales": {
            "recent_7_days": recent_sales,
            "previous_7_days": previous_sales,
            "trend_pct": round(sales_trend_pct, 1),
            "trend_direction": "up" if sales_trend_pct > 5 else "down" if sales_trend_pct < -5 else "stable"
        },
        "stock": {
            "products_depleting_7_days": products_depleting
        },
        "cash_flow": {
            "recent_inflows": recent_inflows,
            "recent_outflows": recent_outflows,
            "net_flow_7_days": recent_inflows - recent_outflows
        }
    }
