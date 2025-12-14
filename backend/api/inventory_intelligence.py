"""
API Endpoints pour Inventory Intelligence
==========================================

Endpoints pour:
- EOQ (Economic Order Quantity)
- Safety Stock
- Reorder Points
- ABC-XYZ Classification
- Stockout Predictions
- Dead Stock Detection
- Reorder Suggestions
"""

from decimal import Decimal
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.dependencies.tenant import Tenant, get_current_tenant
from core.data_repository import query_df
from core.finance.inventory_intelligence import (
    InventoryIntelligence,
    ServiceLevel,
    StockClassification,
)

router = APIRouter(prefix="/inventory-intelligence", tags=["inventory-intelligence"])


# =============================================================================
# SCHEMAS
# =============================================================================

class EOQRequest(BaseModel):
    product_id: int
    annual_demand: float = Field(..., gt=0)
    unit_cost: float = Field(..., gt=0)
    ordering_cost: float = Field(default=25.0, gt=0)
    holding_cost_rate: float = Field(default=0.25, gt=0, le=1)
    min_order_qty: Optional[int] = None
    max_order_qty: Optional[int] = None
    supplier_moq: Optional[int] = None


class EOQResponse(BaseModel):
    product_id: int
    eoq: int
    adjusted_eoq: Optional[int] = None
    adjustment_reason: Optional[str] = None
    orders_per_year: float
    total_ordering_cost: float
    total_holding_cost: float
    total_cost: float


class SafetyStockRequest(BaseModel):
    product_id: int
    average_daily_demand: float = Field(..., gt=0)
    demand_std_dev: float = Field(..., ge=0)
    average_lead_time_days: float = Field(..., gt=0)
    lead_time_std_dev: float = Field(default=0.0, ge=0)
    service_level: str = Field(default="STANDARD")  # LOW, STANDARD, HIGH, CRITICAL
    unit_cost: Optional[float] = None


class SafetyStockResponse(BaseModel):
    product_id: int
    safety_stock: int
    safety_stock_value: float
    safety_stock_days: float
    service_level: str
    z_score: float


class ReorderPointResponse(BaseModel):
    product_id: int
    product_name: str
    reorder_level: int
    safety_stock: int
    lead_time_demand: int
    current_stock: int
    needs_reorder: bool
    days_until_stockout: Optional[float]
    urgency: str
    suggested_order_qty: int


class StockoutPredictionResponse(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    average_daily_consumption: float
    predicted_stockout_date: datetime
    days_until_stockout: float
    confidence: float
    risk_level: str
    recommended_action: str


class DeadStockResponse(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    stock_value: float
    last_movement_date: Optional[datetime]
    days_without_movement: int
    monthly_rotation: float
    recommendation: str
    potential_loss: float


class ABCXYZResponse(BaseModel):
    product_id: int
    product_name: str
    abc_class: str
    xyz_class: str
    combined_class: str
    annual_value: float
    cumulative_value_pct: float
    coefficient_variation: float
    recommended_strategy: str
    review_frequency: str
    safety_stock_policy: str


class ReorderSuggestionResponse(BaseModel):
    product_id: int
    product_name: str
    supplier_id: Optional[int]
    supplier_name: Optional[str]
    suggested_quantity: int
    suggested_order_date: datetime
    expected_delivery_date: datetime
    reason: str
    priority: str
    estimated_cost: float
    current_stock: int
    reorder_point: int
    eoq: int
    safety_stock: int


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_products_for_analysis(tenant_id: int) -> List[dict]:
    """Récupère les produits avec leurs stats pour l'analyse.

    Le tenant 'intelligence' (id=4) a accès à tous les produits (épicerie).
    Les autres tenants ne voient que leurs propres produits.
    """
    # Le tenant intelligence (4) accède au tenant épicerie (1)
    product_tenant = 1 if tenant_id == 4 else tenant_id

    sql = """
        WITH consumption AS (
            SELECT
                produit_id,
                AVG(quantite) as avg_daily,
                STDDEV(quantite) as std_dev,
                SUM(quantite) as total_90d
            FROM mouvements_stock
            WHERE tenant_id = :product_tenant
              AND type = 'SORTIE'
              AND date_mvt >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY produit_id
        ),
        last_movement AS (
            SELECT
                produit_id,
                MAX(date_mvt) as last_date
            FROM mouvements_stock
            WHERE tenant_id = :product_tenant
            GROUP BY produit_id
        )
        SELECT
            p.id as product_id,
            p.nom as product_name,
            p.stock_actuel as current_stock,
            p.prix_achat as unit_cost,
            NULL::integer as supplier_id,
            NULL::text as supplier_name,
            COALESCE(c.avg_daily, 0) as avg_daily_demand,
            COALESCE(c.std_dev, 0) as demand_std_dev,
            COALESCE(c.total_90d, 0) as consumption_90d,
            lm.last_date as last_movement_date
        FROM produits p
        LEFT JOIN consumption c ON c.produit_id = p.id
        LEFT JOIN last_movement lm ON lm.produit_id = p.id
        WHERE p.tenant_id = :product_tenant
          AND p.actif = true
    """
    df = query_df(sql, params={"product_tenant": product_tenant})
    if df.empty:
        return []
    return df.to_dict('records')


def _get_service_level(level_str: str) -> ServiceLevel:
    """Convertit string en ServiceLevel enum"""
    mapping = {
        "LOW": ServiceLevel.LOW,
        "STANDARD": ServiceLevel.STANDARD,
        "HIGH": ServiceLevel.HIGH,
        "CRITICAL": ServiceLevel.CRITICAL,
    }
    return mapping.get(level_str.upper(), ServiceLevel.STANDARD)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/eoq", response_model=EOQResponse)
def calculate_eoq(
    request: EOQRequest,
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Calcule la quantité économique de commande (EOQ) avec la formule de Wilson.

    EOQ = sqrt((2 * D * S) / H)
    - D = Demande annuelle
    - S = Coût par commande
    - H = Coût de stockage par unité par an
    """
    inv = InventoryIntelligence()

    result = inv.calculate_eoq(
        product_id=request.product_id,
        annual_demand=Decimal(str(request.annual_demand)),
        unit_cost=Decimal(str(request.unit_cost)),
        ordering_cost=Decimal(str(request.ordering_cost)),
        holding_cost_rate=request.holding_cost_rate,
        min_order_qty=request.min_order_qty,
        max_order_qty=request.max_order_qty,
        supplier_moq=request.supplier_moq
    )

    return EOQResponse(
        product_id=result.product_id,
        eoq=result.eoq,
        adjusted_eoq=result.adjusted_eoq,
        adjustment_reason=result.adjustment_reason,
        orders_per_year=result.orders_per_year,
        total_ordering_cost=float(result.total_ordering_cost),
        total_holding_cost=float(result.total_holding_cost),
        total_cost=float(result.total_cost)
    )


@router.post("/safety-stock", response_model=SafetyStockResponse)
def calculate_safety_stock(
    request: SafetyStockRequest,
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Calcule le stock de sécurité pour un niveau de service donné.

    SS = Z * sqrt(LT * σd² + d² * σLT²)
    - Z = Z-score pour le niveau de service
    - LT = Lead time moyen
    - σd = Écart-type de la demande
    - d = Demande moyenne
    - σLT = Écart-type du lead time
    """
    inv = InventoryIntelligence()
    service_level = _get_service_level(request.service_level)

    result = inv.calculate_safety_stock(
        product_id=request.product_id,
        average_daily_demand=Decimal(str(request.average_daily_demand)),
        demand_std_dev=Decimal(str(request.demand_std_dev)),
        average_lead_time_days=request.average_lead_time_days,
        lead_time_std_dev=request.lead_time_std_dev,
        service_level=service_level,
        unit_cost=Decimal(str(request.unit_cost)) if request.unit_cost else None
    )

    return SafetyStockResponse(
        product_id=result.product_id,
        safety_stock=result.safety_stock,
        safety_stock_value=float(result.safety_stock_value),
        safety_stock_days=result.safety_stock_days,
        service_level=result.service_level.name,
        z_score=result.z_score
    )


@router.get("/reorder-points", response_model=List[ReorderPointResponse])
def get_reorder_points(
    lead_time_days: float = Query(default=3.0, gt=0),
    service_level: str = Query(default="STANDARD"),
    only_needs_reorder: bool = Query(default=False),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne les points de réapprovisionnement pour tous les produits.
    Filtre optionnel pour ne montrer que ceux nécessitant une commande.
    """
    inv = InventoryIntelligence()
    products = _get_products_for_analysis(tenant.id)
    sl = _get_service_level(service_level)

    results = []
    for p in products:
        if p['avg_daily_demand'] <= 0:
            continue

        # Safety stock
        ss = inv.calculate_safety_stock(
            product_id=p['product_id'],
            average_daily_demand=Decimal(str(p['avg_daily_demand'])),
            demand_std_dev=Decimal(str(p['demand_std_dev'] or 0)),
            average_lead_time_days=lead_time_days,
            service_level=sl
        )

        # EOQ
        annual_demand = Decimal(str(p['avg_daily_demand'])) * 365
        eoq = inv.calculate_eoq(
            product_id=p['product_id'],
            annual_demand=annual_demand,
            unit_cost=Decimal(str(p['unit_cost'] or 1))
        )

        # Reorder point
        rop = inv.calculate_reorder_point(
            product_id=p['product_id'],
            current_stock=int(p['current_stock'] or 0),
            average_daily_demand=Decimal(str(p['avg_daily_demand'])),
            lead_time_days=lead_time_days,
            safety_stock=ss.safety_stock,
            eoq=eoq.adjusted_eoq or eoq.eoq
        )

        if only_needs_reorder and not rop.needs_reorder:
            continue

        results.append(ReorderPointResponse(
            product_id=rop.product_id,
            product_name=p['product_name'],
            reorder_level=rop.reorder_level,
            safety_stock=rop.safety_stock,
            lead_time_demand=rop.lead_time_demand,
            current_stock=rop.current_stock,
            needs_reorder=rop.needs_reorder,
            days_until_stockout=rop.days_until_stockout,
            urgency=rop.urgency,
            suggested_order_qty=rop.suggested_order_qty
        ))

    # Trier par urgence
    urgency_order = {"critical": 0, "urgent": 1, "normal": 2, "ok": 3}
    results.sort(key=lambda x: urgency_order.get(x.urgency, 9))

    return results


@router.get("/stockout-predictions", response_model=List[StockoutPredictionResponse])
def predict_stockouts(
    horizon_days: int = Query(default=30, ge=1, le=90),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Prédit les ruptures de stock dans les N prochains jours.
    Trie par urgence (jours restants avant rupture).
    """
    inv = InventoryIntelligence()
    products = _get_products_for_analysis(tenant.id)

    products_for_prediction = []
    for p in products:
        if p['avg_daily_demand'] > 0 and (p['current_stock'] or 0) > 0:
            # Détecter tendance
            trend = "stable"
            products_for_prediction.append({
                "product_id": p['product_id'],
                "product_name": p['product_name'],
                "current_stock": int(p['current_stock'] or 0),
                "average_daily_consumption": Decimal(str(p['avg_daily_demand'])),
                "consumption_trend": trend,
                "lead_time_days": 3
            })

    predictions = inv.predict_stockouts(products_for_prediction, horizon_days)

    return [
        StockoutPredictionResponse(
            product_id=pred.product_id,
            product_name=pred.product_name,
            current_stock=pred.current_stock,
            average_daily_consumption=float(pred.average_daily_consumption),
            predicted_stockout_date=pred.predicted_stockout_date,
            days_until_stockout=pred.days_until_stockout,
            confidence=pred.confidence,
            risk_level=pred.risk_level,
            recommended_action=pred.recommended_action
        )
        for pred in predictions
    ]


@router.get("/dead-stock", response_model=List[DeadStockResponse])
def get_dead_stock(
    rotation_threshold: float = Query(default=0.3, ge=0, le=1),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Détecte les produits en stock mort (rotation < seuil/mois).
    Stock mort = peu ou pas de mouvement, capital immobilisé.
    """
    inv = InventoryIntelligence()
    products = _get_products_for_analysis(tenant.id)

    products_with_stock = []
    for p in products:
        if (p['current_stock'] or 0) > 0:
            monthly_consumption = (p['consumption_90d'] or 0) / 3
            products_with_stock.append({
                "product_id": p['product_id'],
                "product_name": p['product_name'],
                "current_stock": int(p['current_stock']),
                "unit_cost": Decimal(str(p['unit_cost'] or 0)),
                "last_movement_date": p['last_movement_date'],
                "monthly_consumption": Decimal(str(monthly_consumption))
            })

    dead_stock = inv.detect_dead_stock(products_with_stock, rotation_threshold)

    return [
        DeadStockResponse(
            product_id=item.product_id,
            product_name=item.product_name,
            current_stock=item.current_stock,
            stock_value=float(item.stock_value),
            last_movement_date=item.last_movement_date,
            days_without_movement=item.days_without_movement,
            monthly_rotation=item.monthly_rotation,
            recommendation=item.recommendation,
            potential_loss=float(item.potential_loss)
        )
        for item in dead_stock
    ]


@router.get("/abc-xyz", response_model=List[ABCXYZResponse])
def get_abc_xyz_classification(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Classification ABC-XYZ des produits.

    - ABC: Basée sur la valeur (A=80% valeur, B=15%, C=5%)
    - XYZ: Basée sur la variabilité (X=stable, Y=variable, Z=erratique)

    Retourne des stratégies de gestion recommandées.
    """
    inv = InventoryIntelligence()
    products = _get_products_for_analysis(tenant.id)

    products_for_classification = []
    for p in products:
        annual_value = (p['consumption_90d'] or 0) * 4 * (p['unit_cost'] or 0)
        avg = p['avg_daily_demand'] or 0
        std = p['demand_std_dev'] or 0
        cv = std / avg if avg > 0 else 1.0

        products_for_classification.append({
            "product_id": p['product_id'],
            "product_name": p['product_name'],
            "annual_value": Decimal(str(annual_value)),
            "coefficient_variation": cv
        })

    if not products_for_classification:
        return []

    classifications = inv.classify_abc_xyz(products_for_classification)

    # Créer un mapping pour les noms
    name_map = {p['product_id']: p['product_name'] for p in products_for_classification}

    return [
        ABCXYZResponse(
            product_id=c.product_id,
            product_name=name_map.get(c.product_id, ""),
            abc_class=c.abc_class.value,
            xyz_class=c.xyz_class.value,
            combined_class=c.combined_class,
            annual_value=float(c.annual_value),
            cumulative_value_pct=c.cumulative_value_pct,
            coefficient_variation=c.coefficient_variation,
            recommended_strategy=c.recommended_strategy,
            review_frequency=c.review_frequency,
            safety_stock_policy=c.safety_stock_policy
        )
        for c in classifications
    ]


@router.get("/reorder-suggestions", response_model=List[ReorderSuggestionResponse])
def get_reorder_suggestions(
    lead_time_days: float = Query(default=3.0, gt=0),
    service_level: str = Query(default="STANDARD"),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Génère des suggestions de réapprovisionnement automatiques.
    Priorise par urgence (critical > high > normal > low).
    """
    inv = InventoryIntelligence()
    products = _get_products_for_analysis(tenant.id)
    sl = _get_service_level(service_level)

    products_for_suggestion = []
    suppliers = {}

    for p in products:
        if p['avg_daily_demand'] <= 0:
            continue

        annual_demand = Decimal(str(p['avg_daily_demand'])) * 365

        products_for_suggestion.append({
            "product_id": p['product_id'],
            "product_name": p['product_name'],
            "supplier_id": p.get('supplier_id'),
            "current_stock": int(p['current_stock'] or 0),
            "unit_cost": Decimal(str(p['unit_cost'] or 1)),
            "annual_demand": annual_demand,
            "average_daily_demand": Decimal(str(p['avg_daily_demand'])),
            "demand_std_dev": Decimal(str(p['demand_std_dev'] or 0)),
            "lead_time_days": lead_time_days
        })

        if p.get('supplier_id') and p['supplier_id'] not in suppliers:
            suppliers[p['supplier_id']] = {
                "name": p.get('supplier_name'),
                "lead_time": lead_time_days
            }

    suggestions = inv.generate_reorder_suggestions(products_for_suggestion, suppliers)

    return [
        ReorderSuggestionResponse(
            product_id=s.product_id,
            product_name=s.product_name,
            supplier_id=s.supplier_id,
            supplier_name=s.supplier_name,
            suggested_quantity=s.suggested_quantity,
            suggested_order_date=s.suggested_order_date,
            expected_delivery_date=s.expected_delivery_date,
            reason=s.reason,
            priority=s.priority,
            estimated_cost=float(s.estimated_cost),
            current_stock=s.current_stock,
            reorder_point=s.reorder_point,
            eoq=s.eoq,
            safety_stock=s.safety_stock
        )
        for s in suggestions
    ]


@router.get("/summary")
def get_inventory_intelligence_summary(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Résumé de l'intelligence d'inventaire:
    - Nombre de produits nécessitant réapprovisionnement
    - Valeur du stock mort
    - Distribution ABC-XYZ
    - Alertes urgentes
    """
    inv = InventoryIntelligence()
    products = _get_products_for_analysis(tenant.id)

    # Compteurs
    needs_reorder = 0
    critical_count = 0
    total_dead_stock_value = 0
    abc_distribution = {"A": 0, "B": 0, "C": 0}
    xyz_distribution = {"X": 0, "Y": 0, "Z": 0}

    products_for_analysis = []
    for p in products:
        if p['avg_daily_demand'] > 0:
            annual_value = (p['consumption_90d'] or 0) * 4 * (p['unit_cost'] or 0)
            avg = p['avg_daily_demand']
            std = p['demand_std_dev'] or 0
            cv = std / avg if avg > 0 else 1.0

            products_for_analysis.append({
                "product_id": p['product_id'],
                "annual_value": Decimal(str(annual_value)),
                "coefficient_variation": cv
            })

            # Check reorder
            ss = inv.calculate_safety_stock(
                product_id=p['product_id'],
                average_daily_demand=Decimal(str(p['avg_daily_demand'])),
                demand_std_dev=Decimal(str(p['demand_std_dev'] or 0)),
                average_lead_time_days=3.0
            )

            eoq = inv.calculate_eoq(
                product_id=p['product_id'],
                annual_demand=Decimal(str(p['avg_daily_demand'])) * 365,
                unit_cost=Decimal(str(p['unit_cost'] or 1))
            )

            rop = inv.calculate_reorder_point(
                product_id=p['product_id'],
                current_stock=int(p['current_stock'] or 0),
                average_daily_demand=Decimal(str(p['avg_daily_demand'])),
                lead_time_days=3.0,
                safety_stock=ss.safety_stock,
                eoq=eoq.eoq
            )

            if rop.needs_reorder:
                needs_reorder += 1
            if rop.urgency == "critical":
                critical_count += 1

    # ABC-XYZ classification
    if products_for_analysis:
        classifications = inv.classify_abc_xyz(products_for_analysis)
        for c in classifications:
            abc_distribution[c.abc_class.value] = abc_distribution.get(c.abc_class.value, 0) + 1
            xyz_distribution[c.xyz_class.value] = xyz_distribution.get(c.xyz_class.value, 0) + 1

    # Dead stock
    products_with_stock = []
    for p in products:
        if (p['current_stock'] or 0) > 0:
            monthly_consumption = (p['consumption_90d'] or 0) / 3
            products_with_stock.append({
                "product_id": p['product_id'],
                "product_name": p['product_name'],
                "current_stock": int(p['current_stock']),
                "unit_cost": Decimal(str(p['unit_cost'] or 0)),
                "last_movement_date": p['last_movement_date'],
                "monthly_consumption": Decimal(str(monthly_consumption))
            })

    dead_stock = inv.detect_dead_stock(products_with_stock)
    total_dead_stock_value = sum(float(item.stock_value) for item in dead_stock)

    return {
        "total_products_analyzed": len(products),
        "needs_reorder_count": needs_reorder,
        "critical_alerts_count": critical_count,
        "dead_stock_count": len(dead_stock),
        "dead_stock_value": total_dead_stock_value,
        "abc_distribution": abc_distribution,
        "xyz_distribution": xyz_distribution
    }
