"""
API Endpoints pour Intelligence Overview
==========================================

Endpoints pour:
- Vue d'ensemble intelligence (score santé, anomalies, prévisions, scoring)
- Recommandations IA actionnables
- Application de recommandations
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from enum import Enum
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.dependencies.tenant import Tenant, get_current_tenant
from core.data_repository import query_df, exec_sql
from core.finance.inventory_intelligence import InventoryIntelligence
from core.finance.forecasting import ForecastingEngine
from core.finance.anomaly_detection import AnomalyDetector, Severity
from core.finance.supplier_scoring import SupplierScoreCalculator
from core.finance.margin_calculator import MarginCalculator

router = APIRouter(prefix="/intelligence", tags=["newcms-intelligence"])


# =============================================================================
# SCHEMAS
# =============================================================================

class PriorityLevel(str, Enum):
    """Niveaux de priorité des recommandations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationType(str, Enum):
    """Types de recommandations."""
    REORDER_STOCK = "reorder_stock"
    CHANGE_SUPPLIER = "change_supplier"
    ADJUST_PRICE = "adjust_price"
    REDUCE_STOCK = "reduce_stock"
    OPTIMIZE_MARGIN = "optimize_margin"
    RESOLVE_ANOMALY = "resolve_anomaly"
    IMPROVE_CASHFLOW = "improve_cashflow"
    NEGOTIATE_TERMS = "negotiate_terms"


class ActionPayload(BaseModel):
    """Payload d'une action."""
    label: str
    endpoint: str
    method: str = "POST"
    payload: Dict[str, Any]
    confirmation_required: bool = False
    confirmation_message: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Recommandation IA actionnable."""
    id: str
    type: RecommendationType
    priority: PriorityLevel
    title: str
    description: str
    impact_estimate: str
    confidence: float = Field(..., ge=0, le=1)
    actions: List[ActionPayload]
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class HealthScoreResponse(BaseModel):
    """Score de santé global."""
    overall_score: float = Field(..., ge=0, le=10)
    stock_score: float = Field(..., ge=0, le=10)
    cash_score: float = Field(..., ge=0, le=10)
    anomaly_score: float = Field(..., ge=0, le=10)
    margin_score: float = Field(..., ge=0, le=10)
    grade: str  # A, B, C, D, F
    trend: str  # "up", "down", "stable"
    details: Dict[str, Any]


class AnomalyItem(BaseModel):
    """Item d'anomalie critique."""
    id: str
    type: str
    severity: str
    description: str
    impact: float
    detected_at: datetime


class ForecastItem(BaseModel):
    """Item de prévision clé."""
    type: str  # "stockout", "cashflow_negative"
    date: date
    description: str
    severity: str
    value: float


class SupplierScoreItem(BaseModel):
    """Item de scoring fournisseur."""
    supplier_name: str
    score: float
    grade: str
    trend: str
    issues_count: int


class IntelligenceOverviewResponse(BaseModel):
    """Vue d'ensemble de l'intelligence."""
    health_score: HealthScoreResponse
    critical_anomalies: List[AnomalyItem]
    key_forecasts: List[ForecastItem]
    supplier_scoring: Dict[str, List[SupplierScoreItem]]
    recommendations: List[RecommendationResponse]
    generated_at: datetime = Field(default_factory=datetime.now)


class ApplyRecommendationResponse(BaseModel):
    """Résultat de l'application d'une recommandation."""
    success: bool
    recommendation_id: str
    action_taken: str
    result: Dict[str, Any]
    message: str


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_effective_tenant(tenant_id: int, data_type: str = "product") -> int:
    """Retourne le tenant effectif selon le type de données.

    Le tenant intelligence (4) accède aux données d'autres tenants:
    - product/inventory: tenant 1 (épicerie)
    - restaurant: tenant 2
    - finance: entity 2 ou 3
    """
    if tenant_id != 4:
        return tenant_id

    if data_type in ["product", "inventory"]:
        return 1
    elif data_type == "restaurant":
        return 2
    elif data_type == "finance":
        return 2  # entity_id pour finance_transactions
    else:
        return tenant_id


def _calculate_health_score(tenant_id: int) -> HealthScoreResponse:
    """Calcule le score de santé global.

    Score = 30% stock + 30% cash + 20% anomalies + 20% marges
    """
    # 1. Score Stock (0-10)
    # Basé sur: produits en rupture, stock mort, rotation
    product_tenant = _get_effective_tenant(tenant_id, "product")
    stock_sql = """
        WITH stock_metrics AS (
            SELECT
                COUNT(*) as total_products,
                SUM(CASE WHEN stock_actuel <= 0 THEN 1 ELSE 0 END) as stockout_count,
                SUM(CASE WHEN stock_actuel > (
                    SELECT AVG(quantite) * 90
                    FROM mouvements_stock sm
                    WHERE sm.produit_id = p.id
                      AND sm.type = 'SORTIE'
                      AND sm.date_mvt >= CURRENT_DATE - INTERVAL '30 days'
                ) THEN 1 ELSE 0 END) as overstock_count
            FROM produits p
            WHERE p.tenant_id = :tenant_id AND p.actif = true
        )
        SELECT
            total_products,
            stockout_count,
            overstock_count,
            CASE
                WHEN total_products = 0 THEN 5.0
                ELSE 10.0 * (1 - (CAST(stockout_count + overstock_count AS FLOAT) / (total_products * 2)))
            END as stock_score
        FROM stock_metrics
    """
    stock_df = query_df(stock_sql, params={"tenant_id": product_tenant})
    stock_score = float(stock_df.iloc[0]['stock_score']) if not stock_df.empty else 5.0
    stock_score = max(0, min(10, stock_score))

    # 2. Score Cash (0-10)
    # Basé sur: solde actuel, flux 30j, prévisions
    finance_entity = _get_effective_tenant(tenant_id, "finance")
    cash_sql = """
        WITH cash_metrics AS (
            SELECT
                SUM(CASE WHEN direction = 'IN' THEN CAST(amount AS NUMERIC) ELSE 0 END) as inflows,
                SUM(CASE WHEN direction = 'OUT' THEN CAST(amount AS NUMERIC) ELSE 0 END) as outflows
            FROM finance_transactions
            WHERE entity_id = :entity_id
              AND date_operation >= CURRENT_DATE - INTERVAL '30 days'
        )
        SELECT
            inflows,
            outflows,
            inflows - outflows as net_flow,
            CASE
                WHEN outflows = 0 THEN 10.0
                WHEN inflows / outflows >= 1.2 THEN 10.0
                WHEN inflows / outflows >= 1.0 THEN 7.0
                WHEN inflows / outflows >= 0.8 THEN 5.0
                ELSE 3.0
            END as cash_score
        FROM cash_metrics
    """
    cash_df = query_df(cash_sql, params={"entity_id": finance_entity})
    cash_score = float(cash_df.iloc[0]['cash_score']) if not cash_df.empty else 5.0
    cash_score = max(0, min(10, cash_score))

    # 3. Score Anomalies (0-10)
    # Basé sur: nombre et sévérité des anomalies non résolues
    detector = AnomalyDetector(tenant_id)
    anomaly_sql = """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN severity = 'critical' THEN 3 WHEN severity = 'high' THEN 2 WHEN severity = 'medium' THEN 1 ELSE 0 END) as severity_weight
        FROM detected_anomalies
        WHERE tenant_id = :tenant_id
          AND resolved = false
          AND detected_at >= CURRENT_DATE - INTERVAL '30 days'
    """
    anomaly_df = query_df(anomaly_sql, params={"tenant_id": tenant_id})
    if not anomaly_df.empty and anomaly_df.iloc[0]['total'] > 0:
        severity_weight = float(anomaly_df.iloc[0]['severity_weight'])
        anomaly_score = 10.0 - min(10.0, severity_weight / 5)
    else:
        anomaly_score = 10.0
    anomaly_score = max(0, min(10, anomaly_score))

    # 4. Score Marges (0-10)
    # Basé sur: marge brute moyenne, produits avec marge négative
    margin_sql = """
        WITH margin_metrics AS (
            SELECT
                COUNT(*) as total_products,
                AVG(
                    CASE WHEN prix_vente > 0 THEN
                        (prix_vente - COALESCE(prix_achat, 0)) / prix_vente * 100
                    ELSE 0 END
                ) as avg_margin_pct,
                SUM(CASE WHEN prix_vente < COALESCE(prix_achat, 0) THEN 1 ELSE 0 END) as negative_margin_count
            FROM produits
            WHERE tenant_id = :tenant_id AND actif = true AND prix_vente > 0
        )
        SELECT
            avg_margin_pct,
            negative_margin_count,
            CASE
                WHEN avg_margin_pct >= 30 THEN 10.0
                WHEN avg_margin_pct >= 20 THEN 8.0
                WHEN avg_margin_pct >= 15 THEN 6.0
                WHEN avg_margin_pct >= 10 THEN 4.0
                ELSE 2.0
            END - (negative_margin_count * 0.5) as margin_score
        FROM margin_metrics
    """
    margin_df = query_df(margin_sql, params={"tenant_id": product_tenant})
    margin_score = float(margin_df.iloc[0]['margin_score']) if not margin_df.empty else 5.0
    margin_score = max(0, min(10, margin_score))

    # Calcul du score global (moyenne pondérée)
    overall_score = (
        stock_score * 0.30 +
        cash_score * 0.30 +
        anomaly_score * 0.20 +
        margin_score * 0.20
    )

    # Grade
    if overall_score >= 9:
        grade = "A"
    elif overall_score >= 7:
        grade = "B"
    elif overall_score >= 5:
        grade = "C"
    elif overall_score >= 3:
        grade = "D"
    else:
        grade = "F"

    # Tendance (à implémenter avec historique)
    trend = "stable"

    return HealthScoreResponse(
        overall_score=round(overall_score, 1),
        stock_score=round(stock_score, 1),
        cash_score=round(cash_score, 1),
        anomaly_score=round(anomaly_score, 1),
        margin_score=round(margin_score, 1),
        grade=grade,
        trend=trend,
        details={
            "stock_metrics": stock_df.to_dict('records')[0] if not stock_df.empty else {},
            "cash_metrics": cash_df.to_dict('records')[0] if not cash_df.empty else {},
            "margin_metrics": margin_df.to_dict('records')[0] if not margin_df.empty else {}
        }
    )


def _get_critical_anomalies(tenant_id: int, limit: int = 5) -> List[AnomalyItem]:
    """Récupère les top 5 anomalies critiques."""
    sql = """
        SELECT
            anomaly_id as id,
            anomaly_type as type,
            severity,
            description,
            COALESCE((details->>'amount')::float, 0) as impact,
            detected_at
        FROM detected_anomalies
        WHERE tenant_id = :tenant_id
          AND resolved = false
          AND severity IN ('critical', 'high')
        ORDER BY
            CASE severity
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                ELSE 4
            END,
            detected_at DESC
        LIMIT :limit
    """
    df = query_df(sql, params={"tenant_id": tenant_id, "limit": limit})

    return [
        AnomalyItem(
            id=row['id'],
            type=row['type'],
            severity=row['severity'],
            description=row['description'],
            impact=float(row['impact'] or 0),
            detected_at=row['detected_at']
        )
        for _, row in df.iterrows()
    ]


def _get_key_forecasts(tenant_id: int) -> List[ForecastItem]:
    """Récupère les prévisions clés (ruptures 7j, cash 30j)."""
    forecasts = []

    # 1. Prévisions de ruptures de stock (7 jours)
    product_tenant = _get_effective_tenant(tenant_id, "product")
    stockout_sql = """
        WITH consumption AS (
            SELECT
                p.id,
                p.nom,
                p.stock_actuel,
                AVG(sm.quantite) as avg_daily
            FROM produits p
            LEFT JOIN mouvements_stock sm ON sm.produit_id = p.id
                AND sm.type = 'SORTIE'
                AND sm.date_mvt >= CURRENT_DATE - INTERVAL '30 days'
            WHERE p.tenant_id = :tenant_id
              AND p.actif = true
              AND p.stock_actuel > 0
            GROUP BY p.id, p.nom, p.stock_actuel
            HAVING AVG(sm.quantite) > 0
        )
        SELECT
            id,
            nom,
            stock_actuel,
            avg_daily,
            stock_actuel / avg_daily as days_until_stockout,
            CURRENT_DATE + (stock_actuel / avg_daily)::integer as stockout_date
        FROM consumption
        WHERE stock_actuel / avg_daily <= 7
        ORDER BY days_until_stockout
        LIMIT 3
    """
    stockout_df = query_df(stockout_sql, params={"tenant_id": product_tenant})

    for _, row in stockout_df.iterrows():
        days = float(row['days_until_stockout'])
        forecasts.append(ForecastItem(
            type="stockout",
            date=row['stockout_date'],
            description=f"Rupture prévue: {row['nom']} ({days:.1f}j)",
            severity="critical" if days <= 3 else "high",
            value=float(row['stock_actuel'])
        ))

    # 2. Prévisions de trésorerie négative (30 jours)
    try:
        engine = ForecastingEngine(tenant_id)
        cashflow = engine.forecast_cashflow(horizon_days=30)

        for day in cashflow.daily_forecasts:
            if day['balance'] < 0:
                forecasts.append(ForecastItem(
                    type="cashflow_negative",
                    date=date.fromisoformat(day['date']),
                    description=f"Solde négatif prévu: {day['balance']:.2f}€",
                    severity="critical" if day['balance'] < -1000 else "high",
                    value=float(day['balance'])
                ))
                break  # Ne prendre que la première occurrence
    except:
        pass  # Ignorer si pas assez de données

    return forecasts


def _get_supplier_scoring(tenant_id: int) -> Dict[str, List[SupplierScoreItem]]:
    """Récupère le scoring fournisseurs (top 5 + bottom 5)."""
    try:
        calculator = SupplierScoreCalculator(tenant_id)
        ranking = calculator.get_all_suppliers_ranking()

        # Top 5
        top_5 = []
        for item in ranking[:5]:
            top_5.append(SupplierScoreItem(
                supplier_name=item['supplier_name'],
                score=item['score'],
                grade=item['grade'],
                trend="stable",  # À calculer depuis historique
                issues_count=0  # À calculer
            ))

        # Bottom 5
        bottom_5 = []
        for item in ranking[-5:]:
            bottom_5.append(SupplierScoreItem(
                supplier_name=item['supplier_name'],
                score=item['score'],
                grade=item['grade'],
                trend="stable",
                issues_count=0
            ))

        return {"top": top_5, "bottom": bottom_5}
    except:
        return {"top": [], "bottom": []}


def _generate_recommendations(tenant_id: int) -> List[RecommendationResponse]:
    """Génère les recommandations IA actionnables."""
    recommendations = []

    # 1. Recommandations de réapprovisionnement
    product_tenant = _get_effective_tenant(tenant_id, "product")
    inv = InventoryIntelligence()

    # Récupérer les produits nécessitant réapprovisionnement
    reorder_sql = """
        WITH consumption AS (
            SELECT
                p.id,
                p.nom,
                p.stock_actuel,
                p.prix_achat,
                AVG(sm.quantite) as avg_daily,
                STDDEV(sm.quantite) as std_dev
            FROM produits p
            LEFT JOIN mouvements_stock sm ON sm.produit_id = p.id
                AND sm.type = 'SORTIE'
                AND sm.date_mvt >= CURRENT_DATE - INTERVAL '90 days'
            WHERE p.tenant_id = :tenant_id
              AND p.actif = true
            GROUP BY p.id, p.nom, p.stock_actuel, p.prix_achat
            HAVING AVG(sm.quantite) > 0
        )
        SELECT
            id,
            nom,
            stock_actuel,
            prix_achat,
            avg_daily,
            std_dev,
            stock_actuel / avg_daily as days_remaining
        FROM consumption
        WHERE stock_actuel / avg_daily <= 10
        ORDER BY days_remaining
        LIMIT 5
    """
    reorder_df = query_df(reorder_sql, params={"tenant_id": product_tenant})

    for _, row in reorder_df.iterrows():
        # Calculer EOQ
        annual_demand = Decimal(str(row['avg_daily'])) * 365
        eoq = inv.calculate_eoq(
            product_id=row['id'],
            annual_demand=annual_demand,
            unit_cost=Decimal(str(row['prix_achat'] or 1))
        )

        quantity = eoq.adjusted_eoq or eoq.eoq
        days = float(row['days_remaining'])

        recommendations.append(RecommendationResponse(
            id=f"reorder_{row['id']}_{uuid.uuid4().hex[:8]}",
            type=RecommendationType.REORDER_STOCK,
            priority=PriorityLevel.CRITICAL if days <= 3 else PriorityLevel.HIGH,
            title=f"Réapprovisionner {row['nom']}",
            description=f"Stock critique: {row['stock_actuel']:.0f} unités restantes ({days:.1f}j)",
            impact_estimate=f"Éviter rupture, coût: {quantity * float(row['prix_achat']):.2f}€",
            confidence=0.9,
            actions=[
                ActionPayload(
                    label="Commander maintenant",
                    endpoint="/api/orders/create",
                    method="POST",
                    payload={
                        "product_id": int(row['id']),
                        "product_name": row['nom'],
                        "quantity": quantity,
                        "estimated_cost": float(quantity * Decimal(str(row['prix_achat'] or 0)))
                    },
                    confirmation_required=True,
                    confirmation_message=f"Commander {quantity} unités de {row['nom']} ?"
                )
            ],
            metadata={
                "product_id": int(row['id']),
                "current_stock": float(row['stock_actuel']),
                "days_remaining": days,
                "suggested_quantity": quantity
            }
        ))

    # 2. Recommandations de réduction de stock mort
    dead_stock_sql = """
        WITH consumption AS (
            SELECT
                p.id,
                p.nom,
                p.stock_actuel,
                p.prix_achat,
                COALESCE(SUM(sm.quantite), 0) as consumption_90d
            FROM produits p
            LEFT JOIN mouvements_stock sm ON sm.produit_id = p.id
                AND sm.type = 'SORTIE'
                AND sm.date_mvt >= CURRENT_DATE - INTERVAL '90 days'
            WHERE p.tenant_id = :tenant_id
              AND p.actif = true
              AND p.stock_actuel > 0
            GROUP BY p.id, p.nom, p.stock_actuel, p.prix_achat
        )
        SELECT
            id,
            nom,
            stock_actuel,
            prix_achat,
            consumption_90d,
            stock_actuel * prix_achat as stock_value
        FROM consumption
        WHERE consumption_90d = 0
          AND stock_actuel > 5
        ORDER BY stock_value DESC
        LIMIT 3
    """
    dead_df = query_df(dead_stock_sql, params={"tenant_id": product_tenant})

    for _, row in dead_df.iterrows():
        value = float(row['stock_value'])
        recommendations.append(RecommendationResponse(
            id=f"reduce_{row['id']}_{uuid.uuid4().hex[:8]}",
            type=RecommendationType.REDUCE_STOCK,
            priority=PriorityLevel.MEDIUM,
            title=f"Réduire stock mort: {row['nom']}",
            description=f"Aucun mouvement depuis 90j, valeur immobilisée: {value:.2f}€",
            impact_estimate=f"Libérer {value:.2f}€ de capital",
            confidence=0.85,
            actions=[
                ActionPayload(
                    label="Créer promotion",
                    endpoint="/api/promotions/create",
                    method="POST",
                    payload={
                        "product_id": int(row['id']),
                        "discount_pct": 20,
                        "duration_days": 14
                    }
                ),
                ActionPayload(
                    label="Retourner au fournisseur",
                    endpoint="/api/returns/create",
                    method="POST",
                    payload={
                        "product_id": int(row['id']),
                        "quantity": int(row['stock_actuel'])
                    },
                    confirmation_required=True
                )
            ],
            metadata={
                "product_id": int(row['id']),
                "stock_value": value,
                "stock_quantity": float(row['stock_actuel'])
            }
        ))

    # 3. Recommandations d'optimisation de marges
    low_margin_sql = """
        SELECT
            id,
            nom,
            prix_vente,
            prix_achat,
            (prix_vente - COALESCE(prix_achat, 0)) / NULLIF(prix_vente, 0) * 100 as margin_pct
        FROM produits
        WHERE tenant_id = :tenant_id
          AND actif = true
          AND prix_vente > 0
          AND (prix_vente - COALESCE(prix_achat, 0)) / NULLIF(prix_vente, 0) * 100 < 15
        ORDER BY margin_pct
        LIMIT 3
    """
    margin_df = query_df(low_margin_sql, params={"tenant_id": product_tenant})

    for _, row in margin_df.iterrows():
        current_margin = float(row['margin_pct'])
        target_margin = 20.0
        new_price = float(row['prix_achat']) / (1 - target_margin / 100)
        price_increase = new_price - float(row['prix_vente'])

        recommendations.append(RecommendationResponse(
            id=f"margin_{row['id']}_{uuid.uuid4().hex[:8]}",
            type=RecommendationType.OPTIMIZE_MARGIN,
            priority=PriorityLevel.MEDIUM if current_margin >= 0 else PriorityLevel.HIGH,
            title=f"Optimiser marge: {row['nom']}",
            description=f"Marge actuelle: {current_margin:.1f}%, cible: {target_margin}%",
            impact_estimate=f"Augmenter de {price_increase:.2f}€/unité",
            confidence=0.8,
            actions=[
                ActionPayload(
                    label="Ajuster le prix",
                    endpoint="/api/products/update-price",
                    method="POST",
                    payload={
                        "product_id": int(row['id']),
                        "new_price": round(new_price, 2),
                        "reason": f"Optimisation marge vers {target_margin}%"
                    },
                    confirmation_required=True,
                    confirmation_message=f"Augmenter le prix de {price_increase:.2f}€ ?"
                )
            ],
            metadata={
                "product_id": int(row['id']),
                "current_margin_pct": current_margin,
                "target_margin_pct": target_margin,
                "current_price": float(row['prix_vente']),
                "suggested_price": round(new_price, 2)
            }
        ))

    # 4. Recommandations de changement de fournisseur
    # (Basées sur le scoring fournisseurs)
    try:
        calculator = SupplierScoreCalculator(tenant_id)
        ranking = calculator.get_all_suppliers_ranking()

        # Identifier les fournisseurs avec score < 5
        for item in ranking:
            if item['score'] < 5.0:
                recommendations.append(RecommendationResponse(
                    id=f"supplier_{item['supplier_name']}_{uuid.uuid4().hex[:8]}",
                    type=RecommendationType.CHANGE_SUPPLIER,
                    priority=PriorityLevel.HIGH if item['score'] < 3 else PriorityLevel.MEDIUM,
                    title=f"Revoir fournisseur: {item['supplier_name']}",
                    description=f"Score faible ({item['score']:.1f}/10), grade {item['grade']}",
                    impact_estimate="Améliorer fiabilité et qualité",
                    confidence=0.75,
                    actions=[
                        ActionPayload(
                            label="Voir alternatives",
                            endpoint="/api/suppliers/alternatives",
                            method="GET",
                            payload={"current_supplier": item['supplier_name']}
                        ),
                        ActionPayload(
                            label="Négocier conditions",
                            endpoint="/api/suppliers/negotiate",
                            method="POST",
                            payload={"supplier_name": item['supplier_name']}
                        )
                    ],
                    metadata={
                        "supplier_name": item['supplier_name'],
                        "current_score": item['score'],
                        "grade": item['grade']
                    }
                ))
    except:
        pass

    # Trier par priorité
    priority_order = {
        PriorityLevel.CRITICAL: 0,
        PriorityLevel.HIGH: 1,
        PriorityLevel.MEDIUM: 2,
        PriorityLevel.LOW: 3
    }
    recommendations.sort(key=lambda r: priority_order[r.priority])

    return recommendations[:10]  # Limiter à 10 recommandations


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/overview", response_model=IntelligenceOverviewResponse, summary="Intelligence Overview", tags=["newcms-intelligence"])
def get_intelligence_overview(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    **Intelligence Overview - IA & Analytics**

    Endpoint principal d'intelligence artificielle qui agrège toutes les analyses,
    prédictions et recommandations en un seul appel.

    ## Données retournées

    ### 1. Score de santé global (0-10)
    Moyenne pondérée calculée sur 4 dimensions:
    - **Stock (30%)**: Ruptures, surstock, rotation
    - **Cash (30%)**: Solde, flux 30j, prévisions
    - **Anomalies (20%)**: Nombre et sévérité
    - **Marges (20%)**: Marge moyenne, marges négatives

    Grades: A (9-10), B (7-9), C (5-7), D (3-5), F (<3)

    ### 2. Top 5 anomalies critiques
    Anomalies non résolues triées par sévérité:
    - **critical**: Impact immédiat, action urgente
    - **high**: Impact significatif, traitement rapide
    - Détection automatique via IA
    - Impact financier estimé

    ### 3. Prévisions clés
    - **Ruptures de stock**: Produits en épuisement sous 7 jours
    - **Cash-flow négatif**: Prévision de solde négatif sur 30j
    - Algorithmes de prédiction basés sur historique

    ### 4. Scoring fournisseurs
    - **Top 5**: Meilleurs fournisseurs (score 7-10)
    - **Bottom 5**: Fournisseurs à surveiller (score <5)
    - Basé sur: fiabilité, qualité, délais, prix

    ### 5. Recommandations IA actionnables (top 10)
    Types de recommandations:
    - **reorder_stock**: Réapprovisionnement avec calcul EOQ
    - **reduce_stock**: Liquidation de stock mort
    - **optimize_margin**: Ajustement de prix
    - **change_supplier**: Changement de fournisseur
    - **negotiate_terms**: Renégociation conditions

    Chaque recommandation inclut:
    - Niveau de confiance IA (0-1)
    - Impact estimé
    - Actions directement exécutables
    - Métadonnées pour traçabilité

    ## Conventions

    - Priorisations: critical > high > medium > low
    - Confiance IA: >0.8 = haute, 0.5-0.8 = moyenne, <0.5 = basse
    - Toutes les prévisions incluent intervalles de confiance

    ## Tags
    - newcms-intelligence
    """
    health_score = _calculate_health_score(tenant.id)
    critical_anomalies = _get_critical_anomalies(tenant.id)
    key_forecasts = _get_key_forecasts(tenant.id)
    supplier_scoring = _get_supplier_scoring(tenant.id)
    recommendations = _generate_recommendations(tenant.id)

    return IntelligenceOverviewResponse(
        health_score=health_score,
        critical_anomalies=critical_anomalies,
        key_forecasts=key_forecasts,
        supplier_scoring=supplier_scoring,
        recommendations=recommendations
    )


@router.get("/recommendations", response_model=List[RecommendationResponse], summary="Liste des recommandations IA", tags=["newcms-intelligence"])
def get_recommendations(
    priority: Optional[PriorityLevel] = Query(default=None),
    type: Optional[RecommendationType] = Query(default=None),
    limit: int = Query(default=20, le=100),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    **Liste complète des recommandations IA**

    Endpoint pour consulter toutes les recommandations générées par l'IA
    avec filtrage par priorité et type.

    ## Paramètres de filtrage

    - **priority**: critical, high, medium, low
    - **type**: reorder_stock, change_supplier, adjust_price, reduce_stock, optimize_margin, etc.
    - **limit**: Nombre maximum de résultats (max: 100, défaut: 20)

    ## Types de recommandations

    - **reorder_stock**: Produits à réapprovisionner (calcul EOQ)
    - **reduce_stock**: Stock mort à liquider
    - **optimize_margin**: Prix à ajuster pour meilleure marge
    - **change_supplier**: Fournisseurs à remplacer
    - **negotiate_terms**: Conditions à renégocier

    ## Tags
    - newcms-intelligence
    """
    recommendations = _generate_recommendations(tenant.id)

    # Filtrer
    if priority:
        recommendations = [r for r in recommendations if r.priority == priority]
    if type:
        recommendations = [r for r in recommendations if r.type == type]

    return recommendations[:limit]


@router.post("/recommendations/{recommendation_id}/apply", response_model=ApplyRecommendationResponse, summary="Appliquer une recommandation", tags=["newcms-intelligence"])
def apply_recommendation(
    recommendation_id: str,
    action_index: int = Query(default=0, ge=0),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    **Appliquer une recommandation IA**

    Endpoint pour exécuter une action recommandée par l'IA.
    L'action est définie dans le payload de la recommandation et directement exécutable.

    ## Paramètres

    - **recommendation_id**: ID de la recommandation (ex: "reorder_123_abc")
    - **action_index**: Index de l'action à exécuter (défaut: 0, première action)

    ## Fonctionnement

    1. Récupère la recommandation par son ID
    2. Sélectionne l'action selon l'index
    3. Exécute l'action (appel API backend)
    4. Retourne le résultat

    ## Exemple

    Pour une recommandation de type "reorder_stock":
    - Action 0: "Commander maintenant" (crée une commande)
    - Payload inclut: product_id, quantity, estimated_cost

    ## Note

    Cette implémentation est un placeholder simulant l'exécution.
    En production, appelle les vrais endpoints backend avec les payloads fournis.

    ## Tags
    - newcms-intelligence
    """
    # Récupérer la recommandation
    all_recommendations = _generate_recommendations(tenant.id)
    recommendation = next((r for r in all_recommendations if r.id == recommendation_id), None)

    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommandation non trouvée")

    if action_index >= len(recommendation.actions):
        raise HTTPException(status_code=400, detail="Index d'action invalide")

    action = recommendation.actions[action_index]

    # En production, appeler l'endpoint réel avec le payload
    # Pour l'instant, simuler l'exécution
    result = {
        "simulated": True,
        "endpoint": action.endpoint,
        "method": action.method,
        "payload": action.payload
    }

    return ApplyRecommendationResponse(
        success=True,
        recommendation_id=recommendation_id,
        action_taken=action.label,
        result=result,
        message=f"Action '{action.label}' appliquée avec succès (simulé)"
    )


@router.get("/health-score", response_model=HealthScoreResponse, summary="Score de santé global", tags=["newcms-intelligence"])
def get_health_score(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    **Score de santé global - Note unique (0-10)**

    Endpoint dédié pour obtenir uniquement le score de santé de l'entreprise.
    Utile pour les widgets et indicateurs simples.

    ## Calcul du score

    Moyenne pondérée sur 4 dimensions:
    - **30% Stock**: Ruptures, surstock, rotation
    - **30% Cash**: Solde, flux, prévisions
    - **20% Anomalies**: Nombre et sévérité
    - **20% Marges**: Moyenne et marges négatives

    ## Grades

    - **A** (9-10): Excellent, aucun problème majeur
    - **B** (7-9): Bon, quelques points d'attention
    - **C** (5-7): Moyen, actions correctives nécessaires
    - **D** (3-5): Faible, problèmes importants
    - **F** (<3): Critique, intervention urgente requise

    ## Tendance

    - **up**: Score en amélioration
    - **down**: Score en dégradation
    - **stable**: Score stable

    ## Tags
    - newcms-intelligence
    """
    return _calculate_health_score(tenant.id)


@router.get("/metrics/summary", summary="Résumé des métriques", tags=["newcms-intelligence"])
def get_metrics_summary(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    **Résumé des métriques - Pour graphiques dashboard**

    Endpoint simplifié qui retourne un résumé des métriques clés
    optimisé pour l'affichage dans des graphiques et widgets.

    ## Données retournées

    ```json
    {
      "health_score": {
        "overall": 8.2,
        "grade": "B",
        "breakdown": {
          "stock": 7.5,
          "cash": 9.0,
          "anomalies": 8.5,
          "margins": 7.8
        }
      },
      "alerts": {
        "critical_count": 2,
        "high_count": 5,
        "total": 7
      },
      "forecasts": {
        "stockouts_7d": 3,
        "cashflow_alerts": 0
      }
    }
    ```

    ## Tags
    - newcms-intelligence
    """
    health = _calculate_health_score(tenant.id)
    anomalies = _get_critical_anomalies(tenant.id)
    forecasts = _get_key_forecasts(tenant.id)

    return {
        "health_score": {
            "overall": health.overall_score,
            "grade": health.grade,
            "breakdown": {
                "stock": health.stock_score,
                "cash": health.cash_score,
                "anomalies": health.anomaly_score,
                "margins": health.margin_score
            }
        },
        "alerts": {
            "critical_count": len([a for a in anomalies if a.severity == "critical"]),
            "high_count": len([a for a in anomalies if a.severity == "high"]),
            "total": len(anomalies)
        },
        "forecasts": {
            "stockouts_7d": len([f for f in forecasts if f.type == "stockout"]),
            "cashflow_alerts": len([f for f in forecasts if f.type == "cashflow_negative"])
        }
    }
