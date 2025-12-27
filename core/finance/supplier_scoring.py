"""
Scoring intelligent des fournisseurs.

Fonctionnalités:
- Score qualité multi-critères
- Volatilité des prix
- Ponctualité des livraisons
- Taux d'erreurs factures
- Écarts stock théorique/réel
- Historique et tendances
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
from statistics import mean, stdev

from sqlalchemy import text
from core.data_repository import get_engine


class ScoreDimension(str, Enum):
    """Dimensions du score fournisseur."""
    PRICE_STABILITY = "price_stability"
    DELIVERY_RELIABILITY = "delivery_reliability"
    INVOICE_ACCURACY = "invoice_accuracy"
    STOCK_ACCURACY = "stock_accuracy"
    PAYMENT_TERMS = "payment_terms"
    RESPONSIVENESS = "responsiveness"
    PRODUCT_QUALITY = "product_quality"


@dataclass
class SupplierScore:
    """Score complet d'un fournisseur."""
    supplier_id: Optional[int]
    supplier_name: str
    overall_score: float  # 0-100
    grade: str  # A, B, C, D, F
    dimensions: Dict[ScoreDimension, float]
    metrics: Dict[str, Any]
    trend: str  # improving, stable, declining
    last_updated: datetime
    history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PriceVolatilityMetrics:
    """Métriques de volatilité des prix."""
    avg_variation_pct: float
    max_variation_pct: float
    volatility_index: float  # Écart-type des variations
    price_increases: int
    price_decreases: int
    stable_prices: int
    trend: str  # increasing, decreasing, volatile, stable


class SupplierScoreCalculator:
    """Calculateur de score fournisseur."""

    # Poids par défaut (fallback si pas de profil)
    DEFAULT_DIMENSION_WEIGHTS = {
        ScoreDimension.PRICE_STABILITY: 0.25,
        ScoreDimension.DELIVERY_RELIABILITY: 0.20,
        ScoreDimension.INVOICE_ACCURACY: 0.15,
        ScoreDimension.STOCK_ACCURACY: 0.15,
        ScoreDimension.PAYMENT_TERMS: 0.10,
        ScoreDimension.RESPONSIVENESS: 0.10,
        ScoreDimension.PRODUCT_QUALITY: 0.05,
    }

    def __init__(self, tenant_id: int):
        self.tenant_id = tenant_id
        self._ensure_tables()

    def _ensure_tables(self):
        """Crée les tables nécessaires."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS supplier_score_history (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    supplier_id INTEGER,
                    supplier_name VARCHAR(200) NOT NULL,
                    overall_score FLOAT NOT NULL,
                    grade VARCHAR(2) NOT NULL,
                    dimensions JSONB NOT NULL DEFAULT '{}',
                    metrics JSONB NOT NULL DEFAULT '{}',
                    calculated_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_supplier_score_tenant
                    ON supplier_score_history(tenant_id, supplier_name);
                CREATE INDEX IF NOT EXISTS idx_supplier_score_date
                    ON supplier_score_history(tenant_id, calculated_at);

                CREATE TABLE IF NOT EXISTS supplier_delivery_log (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    supplier_name VARCHAR(200) NOT NULL,
                    expected_date DATE,
                    actual_date DATE,
                    invoice_id INTEGER,
                    delay_days INTEGER,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS supplier_invoice_issues (
                    id SERIAL PRIMARY KEY,
                    tenant_id INTEGER NOT NULL,
                    supplier_name VARCHAR(200) NOT NULL,
                    invoice_id INTEGER,
                    issue_type VARCHAR(50), -- price_error, quantity_error, missing_item, duplicate
                    severity VARCHAR(20), -- low, medium, high
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """))

    def _load_profile_weights(
        self,
        supplier_id: Optional[int] = None,
        supplier_name: Optional[str] = None
    ) -> Dict[ScoreDimension, float]:
        """Charge les poids du profil de scoring pour un fournisseur.

        Args:
            supplier_id: ID du fournisseur dans dim_supplier
            supplier_name: Nom du fournisseur (fallback si pas d'ID)

        Returns:
            Dictionnaire des poids par dimension (somme = 1.0)
        """
        engine = get_engine()

        with engine.connect() as conn:
            # Try to load profile from dim_supplier if supplier_id provided
            if supplier_id:
                result = conn.execute(
                    text("""
                        SELECT
                            sp.price_stability_weight,
                            sp.delivery_reliability_weight,
                            sp.invoice_accuracy_weight,
                            sp.stock_accuracy_weight,
                            sp.payment_terms_weight,
                            sp.responsiveness_weight,
                            sp.product_quality_weight
                        FROM dim_supplier ds
                        JOIN supplier_scoring_profiles sp ON ds.scoring_profile_id = sp.id
                        WHERE ds.id = :supplier_id
                    """),
                    {"supplier_id": supplier_id}
                )
                row = result.fetchone()
                if row:
                    # Convert percentages to decimals (25.0 -> 0.25)
                    return {
                        ScoreDimension.PRICE_STABILITY: float(row[0]) / 100,
                        ScoreDimension.DELIVERY_RELIABILITY: float(row[1]) / 100,
                        ScoreDimension.INVOICE_ACCURACY: float(row[2]) / 100,
                        ScoreDimension.STOCK_ACCURACY: float(row[3]) / 100,
                        ScoreDimension.PAYMENT_TERMS: float(row[4]) / 100,
                        ScoreDimension.RESPONSIVENESS: float(row[5]) / 100,
                        ScoreDimension.PRODUCT_QUALITY: float(row[6]) / 100,
                    }

            # Fallback: Load default profile for tenant
            result = conn.execute(
                text("""
                    SELECT
                        price_stability_weight,
                        delivery_reliability_weight,
                        invoice_accuracy_weight,
                        stock_accuracy_weight,
                        payment_terms_weight,
                        responsiveness_weight,
                        product_quality_weight
                    FROM supplier_scoring_profiles
                    WHERE tenant_id = :tenant_id
                      AND is_default = true
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"tenant_id": self.tenant_id}
            )
            row = result.fetchone()

            if row:
                # Convert percentages to decimals
                return {
                    ScoreDimension.PRICE_STABILITY: float(row[0]) / 100,
                    ScoreDimension.DELIVERY_RELIABILITY: float(row[1]) / 100,
                    ScoreDimension.INVOICE_ACCURACY: float(row[2]) / 100,
                    ScoreDimension.STOCK_ACCURACY: float(row[3]) / 100,
                    ScoreDimension.PAYMENT_TERMS: float(row[4]) / 100,
                    ScoreDimension.RESPONSIVENESS: float(row[5]) / 100,
                    ScoreDimension.PRODUCT_QUALITY: float(row[6]) / 100,
                }

        # Ultimate fallback: hardcoded defaults
        return self.DEFAULT_DIMENSION_WEIGHTS

    def calculate_score(
        self,
        supplier_name: str,
        supplier_id: Optional[int] = None,
        period_days: int = 90
    ) -> SupplierScore:
        """Calcule le score complet d'un fournisseur."""
        since = datetime.utcnow() - timedelta(days=period_days)

        # Load dynamic weights for this supplier
        weights = self._load_profile_weights(supplier_id, supplier_name)

        dimensions = {}
        metrics = {}

        # 1. Stabilité des prix
        price_metrics = self._calculate_price_stability(supplier_name, since)
        dimensions[ScoreDimension.PRICE_STABILITY] = price_metrics["score"]
        metrics["price"] = price_metrics

        # 2. Fiabilité livraisons
        delivery_metrics = self._calculate_delivery_reliability(supplier_name, since)
        dimensions[ScoreDimension.DELIVERY_RELIABILITY] = delivery_metrics["score"]
        metrics["delivery"] = delivery_metrics

        # 3. Exactitude factures
        invoice_metrics = self._calculate_invoice_accuracy(supplier_name, since)
        dimensions[ScoreDimension.INVOICE_ACCURACY] = invoice_metrics["score"]
        metrics["invoice"] = invoice_metrics

        # 4. Exactitude stock
        stock_metrics = self._calculate_stock_accuracy(supplier_name, since)
        dimensions[ScoreDimension.STOCK_ACCURACY] = stock_metrics["score"]
        metrics["stock"] = stock_metrics

        # 5. Délais de paiement (score par défaut si pas de données)
        dimensions[ScoreDimension.PAYMENT_TERMS] = 80.0
        metrics["payment"] = {"score": 80.0, "note": "Données insuffisantes"}

        # 6. Réactivité
        dimensions[ScoreDimension.RESPONSIVENESS] = 75.0
        metrics["responsiveness"] = {"score": 75.0, "note": "Données insuffisantes"}

        # 7. Qualité produits
        dimensions[ScoreDimension.PRODUCT_QUALITY] = 80.0
        metrics["quality"] = {"score": 80.0, "note": "Données insuffisantes"}

        # Calcul score global pondéré (using dynamic weights)
        overall_score = sum(
            dimensions[dim] * weights[dim]
            for dim in weights.keys()
        )

        # Store weights used in metrics for transparency
        metrics["weights_used"] = {dim.value: round(weights[dim] * 100, 1) for dim in weights.keys()}

        # Grade
        grade = self._calculate_grade(overall_score)

        # Tendance
        trend = self._calculate_trend(supplier_name)

        # Historique récent
        history = self._get_score_history(supplier_name, limit=10)

        score = SupplierScore(
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            overall_score=round(overall_score, 1),
            grade=grade,
            dimensions={k: round(v, 1) for k, v in dimensions.items()},
            metrics=metrics,
            trend=trend,
            last_updated=datetime.utcnow(),
            history=history,
        )

        # Sauvegarder le score
        self._save_score(score)

        return score

    def _calculate_price_stability(
        self,
        supplier_name: str,
        since: datetime
    ) -> Dict[str, Any]:
        """Calcule le score de stabilité des prix."""
        engine = get_engine()
        with engine.connect() as conn:
            # Récupérer l'historique des prix
            result = conn.execute(
                text("""
                    SELECT
                        p.id as product_id,
                        p.nom as product_name,
                        ph.prix_achat as prix,
                        ph.facture_date as date,
                        LAG(ph.prix_achat) OVER (PARTITION BY p.id ORDER BY ph.facture_date) as prev_prix
                    FROM produits p
                    JOIN produits_price_history ph ON p.id = ph.produit_id
                    WHERE p.tenant_id = :tenant_id
                      AND LOWER(ph.fournisseur) LIKE LOWER(:supplier)
                      AND ph.facture_date >= :since
                    ORDER BY p.id, ph.facture_date
                """),
                {
                    "tenant_id": self.tenant_id,
                    "supplier": f"%{supplier_name}%",
                    "since": since,
                }
            )

            variations = []
            increases = 0
            decreases = 0
            stable = 0

            for row in result:
                if row.prev_prix and row.prev_prix > 0:
                    variation = (row.prix - row.prev_prix) / row.prev_prix * 100
                    variations.append(abs(variation))

                    if variation > 1:
                        increases += 1
                    elif variation < -1:
                        decreases += 1
                    else:
                        stable += 1

            if not variations:
                return {
                    "score": 80.0,
                    "avg_variation_pct": 0,
                    "max_variation_pct": 0,
                    "volatility_index": 0,
                    "increases": 0,
                    "decreases": 0,
                    "stable": 0,
                    "trend": "stable",
                    "note": "Données insuffisantes",
                }

            avg_variation = mean(variations)
            max_variation = max(variations)
            volatility = stdev(variations) if len(variations) > 1 else 0

            # Score: moins de variation = meilleur score
            # 0% variation = 100, 5% avg = 75, 10%+ = 50 ou moins
            score = max(0, 100 - (avg_variation * 5) - (volatility * 2))

            # Tendance
            if increases > decreases * 1.5:
                trend = "increasing"
            elif decreases > increases * 1.5:
                trend = "decreasing"
            elif volatility > 5:
                trend = "volatile"
            else:
                trend = "stable"

            return {
                "score": round(score, 1),
                "avg_variation_pct": round(avg_variation, 2),
                "max_variation_pct": round(max_variation, 2),
                "volatility_index": round(volatility, 2),
                "increases": increases,
                "decreases": decreases,
                "stable": stable,
                "trend": trend,
            }

    def _calculate_delivery_reliability(
        self,
        supplier_name: str,
        since: datetime
    ) -> Dict[str, Any]:
        """Calcule le score de fiabilité des livraisons."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN delay_days <= 0 THEN 1 ELSE 0 END) as on_time,
                        SUM(CASE WHEN delay_days BETWEEN 1 AND 2 THEN 1 ELSE 0 END) as slight_delay,
                        SUM(CASE WHEN delay_days > 2 THEN 1 ELSE 0 END) as late,
                        AVG(delay_days) as avg_delay
                    FROM supplier_delivery_log
                    WHERE tenant_id = :tenant_id
                      AND LOWER(supplier_name) LIKE LOWER(:supplier)
                      AND created_at >= :since
                """),
                {
                    "tenant_id": self.tenant_id,
                    "supplier": f"%{supplier_name}%",
                    "since": since,
                }
            )

            row = result.fetchone()

            if not row or row.total == 0:
                return {
                    "score": 80.0,
                    "total_deliveries": 0,
                    "on_time_rate": 0,
                    "avg_delay_days": 0,
                    "note": "Données insuffisantes",
                }

            on_time_rate = (row.on_time or 0) / row.total * 100
            score = on_time_rate * 0.8 + (100 - min(100, (row.avg_delay or 0) * 10)) * 0.2

            return {
                "score": round(score, 1),
                "total_deliveries": row.total,
                "on_time": row.on_time or 0,
                "slight_delay": row.slight_delay or 0,
                "late": row.late or 0,
                "on_time_rate": round(on_time_rate, 1),
                "avg_delay_days": round(row.avg_delay or 0, 1),
            }

    def _calculate_invoice_accuracy(
        self,
        supplier_name: str,
        since: datetime
    ) -> Dict[str, Any]:
        """Calcule le score d'exactitude des factures.
        Note: Utilise finance_invoices_supplier/finance_vendors avec entity_id.
        """
        engine = get_engine()
        # Conversion tenant_id -> entity_id
        entity_id = 2 if self.tenant_id == 4 else self.tenant_id

        with engine.connect() as conn:
            # Compter les factures totales
            total_result = conn.execute(
                text("""
                    SELECT COUNT(DISTINCT f.id) as total
                    FROM finance_invoices_supplier f
                    JOIN finance_vendors v ON v.id = f.vendor_id
                    WHERE f.entity_id = :entity_id
                      AND LOWER(v.name) LIKE LOWER(:supplier)
                      AND f.created_at >= :since
                """),
                {
                    "entity_id": entity_id,
                    "supplier": f"%{supplier_name}%",
                    "since": since,
                }
            )
            total_row = total_result.fetchone()
            total_invoices = total_row.total if total_row else 0

            # Compter les problèmes
            issues_result = conn.execute(
                text("""
                    SELECT
                        COUNT(*) as total_issues,
                        SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as critical,
                        SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium,
                        SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as minor
                    FROM supplier_invoice_issues
                    WHERE tenant_id = :tenant_id
                      AND LOWER(supplier_name) LIKE LOWER(:supplier)
                      AND created_at >= :since
                """),
                {
                    "tenant_id": self.tenant_id,
                    "supplier": f"%{supplier_name}%",
                    "since": since,
                }
            )
            issues_row = issues_result.fetchone()

            if total_invoices == 0:
                return {
                    "score": 80.0,
                    "total_invoices": 0,
                    "error_rate": 0,
                    "note": "Données insuffisantes",
                }

            total_issues = issues_row.total_issues or 0
            error_rate = total_issues / total_invoices * 100

            # Pénalités par sévérité
            penalty = (
                (issues_row.critical or 0) * 10 +
                (issues_row.medium or 0) * 5 +
                (issues_row.minor or 0) * 2
            ) / total_invoices

            score = max(0, 100 - error_rate * 2 - penalty)

            return {
                "score": round(score, 1),
                "total_invoices": total_invoices,
                "total_issues": total_issues,
                "critical_issues": issues_row.critical or 0,
                "medium_issues": issues_row.medium or 0,
                "minor_issues": issues_row.minor or 0,
                "error_rate": round(error_rate, 1),
            }

    def _calculate_stock_accuracy(
        self,
        supplier_name: str,
        since: datetime
    ) -> Dict[str, Any]:
        """Calcule le score d'exactitude du stock."""
        try:
            engine = get_engine()
            with engine.connect() as conn:
                # Vérifier si la table existe
                table_check = conn.execute(
                    text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = 'inventaire_snapshots'
                        )
                    """)
                )
                if not table_check.fetchone()[0]:
                    return {
                        "score": 80.0,
                        "total_checks": 0,
                        "accuracy_rate": 0,
                        "note": "Table inventaire_snapshots non disponible",
                    }

                # Comparer stock théorique vs réel lors des inventaires
                result = conn.execute(
                    text("""
                        SELECT
                            COUNT(*) as total_checks,
                            AVG(ABS(ecart_pct)) as avg_deviation_pct,
                            MAX(ABS(ecart_pct)) as max_deviation_pct,
                            SUM(CASE WHEN ABS(ecart_pct) <= 2 THEN 1 ELSE 0 END) as accurate
                        FROM (
                            SELECT
                                i.product_id,
                                CASE WHEN i.stock_theorique > 0
                                    THEN (i.stock_reel - i.stock_theorique) / i.stock_theorique * 100
                                    ELSE 0
                                END as ecart_pct
                            FROM inventaire_snapshots i
                            JOIN produits p ON i.product_id = p.id
                            WHERE p.tenant_id = :tenant_id
                              AND i.date >= :since
                              AND EXISTS (
                                  SELECT 1 FROM produits_price_history hp
                                  WHERE hp.produit_id = p.id
                                    AND LOWER(hp.fournisseur) LIKE LOWER(:supplier)
                              )
                        ) sub
                    """),
                    {
                        "tenant_id": self.tenant_id,
                        "supplier": f"%{supplier_name}%",
                        "since": since,
                    }
                )

                row = result.fetchone()

                if not row or row.total_checks == 0:
                    return {
                        "score": 80.0,
                        "total_checks": 0,
                        "accuracy_rate": 0,
                        "note": "Données insuffisantes",
                    }

                accuracy_rate = (row.accurate or 0) / row.total_checks * 100
                avg_deviation = row.avg_deviation_pct or 0

                score = accuracy_rate * 0.7 + max(0, 100 - avg_deviation * 5) * 0.3

                return {
                    "score": round(score, 1),
                    "total_checks": row.total_checks,
                    "accurate_checks": row.accurate or 0,
                    "accuracy_rate": round(accuracy_rate, 1),
                    "avg_deviation_pct": round(avg_deviation, 2),
                    "max_deviation_pct": round(row.max_deviation_pct or 0, 2),
                }
        except Exception as e:
            logger.warning(f"Stock accuracy calculation failed: {e}")
            return {
                "score": 80.0,
                "total_checks": 0,
                "accuracy_rate": 0,
                "note": "Calcul non disponible",
            }

    def _calculate_grade(self, score: float) -> str:
        """Convertit un score en grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _calculate_trend(self, supplier_name: str) -> str:
        """Calcule la tendance du score."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT overall_score, calculated_at
                    FROM supplier_score_history
                    WHERE tenant_id = :tenant_id
                      AND LOWER(supplier_name) LIKE LOWER(:supplier)
                    ORDER BY calculated_at DESC
                    LIMIT 5
                """),
                {
                    "tenant_id": self.tenant_id,
                    "supplier": f"%{supplier_name}%",
                }
            )

            scores = [row.overall_score for row in result]

            if len(scores) < 2:
                return "stable"

            recent_avg = mean(scores[:2])
            older_avg = mean(scores[2:]) if len(scores) > 2 else scores[-1]

            diff = recent_avg - older_avg
            if diff > 5:
                return "improving"
            elif diff < -5:
                return "declining"
            else:
                return "stable"

    def _get_score_history(
        self,
        supplier_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Récupère l'historique des scores."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT overall_score, grade, calculated_at
                    FROM supplier_score_history
                    WHERE tenant_id = :tenant_id
                      AND LOWER(supplier_name) LIKE LOWER(:supplier)
                    ORDER BY calculated_at DESC
                    LIMIT :limit
                """),
                {
                    "tenant_id": self.tenant_id,
                    "supplier": f"%{supplier_name}%",
                    "limit": limit,
                }
            )

            return [
                {
                    "score": row.overall_score,
                    "grade": row.grade,
                    "date": row.calculated_at.isoformat() if row.calculated_at else None,
                }
                for row in result
            ]

    def _save_score(self, score: SupplierScore):
        """Sauvegarde le score calculé."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO supplier_score_history
                    (tenant_id, supplier_id, supplier_name, overall_score, grade, dimensions, metrics)
                    VALUES (:tenant_id, :supplier_id, :supplier_name, :overall_score, :grade, :dimensions, :metrics)
                """),
                {
                    "tenant_id": self.tenant_id,
                    "supplier_id": score.supplier_id,
                    "supplier_name": score.supplier_name,
                    "overall_score": score.overall_score,
                    "grade": score.grade,
                    "dimensions": json.dumps({k.value: v for k, v in score.dimensions.items()}),
                    "metrics": json.dumps(score.metrics),
                }
            )

    def get_supplier_name_by_id(self, supplier_id: int) -> Optional[str]:
        """Récupère le nom d'un fournisseur par son ID."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT supplier_name
                    FROM supplier_score_history
                    WHERE tenant_id = :tenant_id AND supplier_id = :supplier_id
                    ORDER BY calculated_at DESC
                    LIMIT 1
                """),
                {"tenant_id": self.tenant_id, "supplier_id": supplier_id}
            )
            row = result.fetchone()
            return row.supplier_name if row else None

    def get_all_suppliers_ranking(self) -> List[Dict[str, Any]]:
        """Retourne le classement de tous les fournisseurs."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    WITH latest_scores AS (
                        SELECT DISTINCT ON (supplier_name)
                            supplier_id,
                            supplier_name,
                            overall_score,
                            grade,
                            dimensions,
                            calculated_at
                        FROM supplier_score_history
                        WHERE tenant_id = :tenant_id
                        ORDER BY supplier_name, calculated_at DESC
                    )
                    SELECT * FROM latest_scores
                    ORDER BY overall_score DESC
                """),
                {"tenant_id": self.tenant_id}
            )

            return [
                {
                    "supplier_id": row.supplier_id,
                    "supplier_name": row.supplier_name,
                    "score": row.overall_score,
                    "grade": row.grade,
                    "dimensions": row.dimensions if isinstance(row.dimensions, dict) else json.loads(row.dimensions),
                    "last_updated": row.calculated_at.isoformat() if row.calculated_at else None,
                }
                for row in result
            ]

    def get_supplier_comparison(
        self,
        suppliers: List[str]
    ) -> Dict[str, Any]:
        """Compare plusieurs fournisseurs."""
        scores = []
        for supplier in suppliers:
            score = self.calculate_score(supplier)
            scores.append({
                "supplier": supplier,
                "overall_score": score.overall_score,
                "grade": score.grade,
                "dimensions": {k.value: v for k, v in score.dimensions.items()},
            })

        # Classement par dimension
        rankings = {}
        for dim in ScoreDimension:
            sorted_by_dim = sorted(
                scores,
                key=lambda x: x["dimensions"].get(dim.value, 0),
                reverse=True
            )
            rankings[dim.value] = [s["supplier"] for s in sorted_by_dim]

        return {
            "suppliers": scores,
            "rankings": rankings,
            "best_overall": max(scores, key=lambda x: x["overall_score"])["supplier"] if scores else None,
        }

    def record_delivery(
        self,
        supplier_name: str,
        expected_date: datetime,
        actual_date: datetime,
        invoice_id: Optional[int] = None
    ):
        """Enregistre une livraison pour le suivi."""
        delay_days = (actual_date - expected_date).days

        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO supplier_delivery_log
                    (tenant_id, supplier_name, expected_date, actual_date, invoice_id, delay_days)
                    VALUES (:tenant_id, :supplier_name, :expected_date, :actual_date, :invoice_id, :delay_days)
                """),
                {
                    "tenant_id": self.tenant_id,
                    "supplier_name": supplier_name,
                    "expected_date": expected_date,
                    "actual_date": actual_date,
                    "invoice_id": invoice_id,
                    "delay_days": delay_days,
                }
            )

    def record_invoice_issue(
        self,
        supplier_name: str,
        issue_type: str,
        severity: str,
        invoice_id: Optional[int] = None
    ):
        """Enregistre un problème de facture."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO supplier_invoice_issues
                    (tenant_id, supplier_name, invoice_id, issue_type, severity)
                    VALUES (:tenant_id, :supplier_name, :invoice_id, :issue_type, :severity)
                """),
                {
                    "tenant_id": self.tenant_id,
                    "supplier_name": supplier_name,
                    "invoice_id": invoice_id,
                    "issue_type": issue_type,
                    "severity": severity,
                }
            )
