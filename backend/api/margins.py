"""
API Endpoints pour Margin Calculator
====================================

Endpoints pour:
- Calcul de marges brutes/opérationnelles/nettes
- Calcul PAMP (Prix d'Achat Moyen Pondéré)
- Marges par produit/catégorie
- Marges restaurant (plats)
- Historique et snapshots
"""

from decimal import Decimal
from typing import List, Optional
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.dependencies.tenant import Tenant, get_current_tenant
from core.data_repository import query_df, exec_sql
from core.finance.margin_calculator import (
    MarginCalculator,
    MarginType,
    PeriodType,
)

router = APIRouter(prefix="/margins", tags=["margins"])


# =============================================================================
# SCHEMAS
# =============================================================================

class MarginRequest(BaseModel):
    revenue: float = Field(..., gt=0)
    direct_costs: float = Field(..., ge=0)
    indirect_costs: float = Field(default=0, ge=0)
    taxes: float = Field(default=0, ge=0)


class MarginResponse(BaseModel):
    revenue: float
    direct_costs: float
    indirect_costs: float
    gross_margin: float
    gross_margin_pct: float
    operating_margin: float
    operating_margin_pct: float
    net_margin: Optional[float] = None
    net_margin_pct: Optional[float] = None


class ProductMarginResponse(BaseModel):
    product_id: int
    product_name: str
    category: Optional[str]
    selling_price: float
    purchase_price: float
    pamp: Optional[float]  # Prix d'Achat Moyen Pondéré
    gross_margin: float
    gross_margin_pct: float
    volume_sold: float
    total_revenue: float
    total_margin: float


class CategoryMarginResponse(BaseModel):
    category: str
    product_count: int
    total_revenue: float
    total_cost: float
    gross_margin: float
    gross_margin_pct: float
    avg_margin_per_product: float


class PAMPResponse(BaseModel):
    product_id: int
    product_name: str
    current_pamp: float
    last_purchase_price: float
    price_change_pct: float
    purchase_history: List[dict]
    calculation_details: dict


class DishMarginResponse(BaseModel):
    dish_id: int
    dish_name: str
    selling_price: float
    ingredient_cost: float
    gross_margin: float
    gross_margin_pct: float
    food_cost_ratio: float
    ingredients: List[dict]


class MarginSnapshotResponse(BaseModel):
    snapshot_date: date
    period_type: str
    total_revenue: float
    total_cost: float
    gross_margin: float
    gross_margin_pct: float
    operating_margin: float
    operating_margin_pct: float
    top_margin_products: List[dict]
    low_margin_products: List[dict]


class MarginAlertResponse(BaseModel):
    product_id: int
    product_name: str
    current_margin_pct: float
    threshold_pct: float
    alert_type: str  # "below_threshold", "negative", "decreasing"
    severity: str
    recommendation: str


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _calculate_pamp(purchases: List[dict]) -> Decimal:
    """Calcule le PAMP à partir de l'historique d'achats"""
    if not purchases:
        return Decimal("0")

    total_qty = sum(p.get('quantity', 0) for p in purchases)
    total_value = sum(
        Decimal(str(p.get('quantity', 0))) * Decimal(str(p.get('unit_price', 0)))
        for p in purchases
    )

    if total_qty == 0:
        return Decimal("0")

    return total_value / Decimal(str(total_qty))


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/calculate", response_model=MarginResponse)
def calculate_margin(
    request: MarginRequest,
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Calcule les marges brute, opérationnelle et nette.

    - Marge brute = Revenue - Coûts directs
    - Marge opérationnelle = Marge brute - Coûts indirects
    - Marge nette = Marge opérationnelle - Taxes
    """
    revenue = Decimal(str(request.revenue))
    direct = Decimal(str(request.direct_costs))
    indirect = Decimal(str(request.indirect_costs))
    taxes = Decimal(str(request.taxes))

    gross = revenue - direct
    gross_pct = (gross / revenue * 100) if revenue > 0 else Decimal("0")

    operating = gross - indirect
    operating_pct = (operating / revenue * 100) if revenue > 0 else Decimal("0")

    net = operating - taxes if taxes > 0 else None
    net_pct = (net / revenue * 100) if net is not None and revenue > 0 else None

    return MarginResponse(
        revenue=float(revenue),
        direct_costs=float(direct),
        indirect_costs=float(indirect),
        gross_margin=float(gross),
        gross_margin_pct=float(gross_pct),
        operating_margin=float(operating),
        operating_margin_pct=float(operating_pct),
        net_margin=float(net) if net else None,
        net_margin_pct=float(net_pct) if net_pct else None
    )


@router.get("/products", response_model=List[ProductMarginResponse])
def get_product_margins(
    category: Optional[str] = Query(default=None),
    min_margin_pct: Optional[float] = Query(default=None),
    days_back: int = Query(default=30, ge=1, le=365),
    sort_by: str = Query(default="total_margin", regex="^(gross_margin_pct|total_margin|volume_sold)$"),
    limit: int = Query(default=100, le=500),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne les marges par produit avec:
    - Prix de vente et d'achat
    - PAMP (Prix d'Achat Moyen Pondéré)
    - Marge brute et pourcentage
    - Volume vendu et revenus
    """
    # Tenant intelligence (4) accède au tenant épicerie (1)
    effective_tenant = 1 if tenant.id == 4 else tenant.id
    conditions = ["p.tenant_id = :tenant_id", "p.actif = true"]
    params = {"tenant_id": effective_tenant, "days": days_back, "limit": limit}

    if category:
        conditions.append("p.categorie = :category")
        params["category"] = category

    sql = f"""
        WITH sortie AS (
            SELECT
                produit_id,
                SUM(quantite) as volume_sold,
                SUM(quantite * (SELECT prix_vente FROM produits WHERE id = produit_id)) as total_revenue
            FROM mouvements_stock
            WHERE tenant_id = :tenant_id
              AND type = 'SORTIE'
              AND date_mvt >= CURRENT_DATE - :days * INTERVAL '1 day'
            GROUP BY produit_id
        ),
        purchases AS (
            SELECT
                pb.produit_id,
                AVG(pph.prix_achat) as pamp
            FROM produits_price_history pph
            JOIN produits_barcodes pb ON pb.code = pph.code AND pb.tenant_id = pph.tenant_id
            WHERE pph.tenant_id = :tenant_id
              AND pph.facture_date >= CURRENT_DATE - INTERVAL '180 days'
            GROUP BY pb.produit_id
        )
        SELECT
            p.id as product_id,
            p.nom as product_name,
            p.categorie as category,
            p.prix_vente as selling_price,
            p.prix_achat as purchase_price,
            COALESCE(pu.pamp, p.prix_achat) as pamp,
            COALESCE(s.volume_sold, 0) as volume_sold,
            COALESCE(s.total_revenue, 0) as total_revenue,
            p.prix_vente - COALESCE(pu.pamp, p.prix_achat, 0) as gross_margin,
            CASE
                WHEN p.prix_vente > 0 THEN
                    (p.prix_vente - COALESCE(pu.pamp, p.prix_achat, 0)) / p.prix_vente * 100
                ELSE 0
            END as gross_margin_pct,
            (p.prix_vente - COALESCE(pu.pamp, p.prix_achat, 0)) * COALESCE(s.volume_sold, 0) as total_margin
        FROM produits p
        LEFT JOIN sortie s ON s.produit_id = p.id
        LEFT JOIN purchases pu ON pu.produit_id = p.id
        WHERE {' AND '.join(conditions)}
        ORDER BY {sort_by} DESC NULLS LAST
        LIMIT :limit
    """

    df = query_df(sql, params=params)

    if min_margin_pct is not None:
        df = df[df['gross_margin_pct'] >= min_margin_pct]

    return [
        ProductMarginResponse(
            product_id=int(row['product_id']),
            product_name=row['product_name'],
            category=row['category'],
            selling_price=float(row['selling_price'] or 0),
            purchase_price=float(row['purchase_price'] or 0),
            pamp=float(row['pamp']) if row['pamp'] else None,
            gross_margin=float(row['gross_margin'] or 0),
            gross_margin_pct=float(row['gross_margin_pct'] or 0),
            volume_sold=float(row['volume_sold'] or 0),
            total_revenue=float(row['total_revenue'] or 0),
            total_margin=float(row['total_margin'] or 0)
        )
        for _, row in df.iterrows()
    ]


@router.get("/categories", response_model=List[CategoryMarginResponse])
def get_category_margins(
    days_back: int = Query(default=30, ge=1, le=365),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne les marges agrégées par catégorie de produits.
    """
    # Tenant intelligence (4) accède au tenant épicerie (1)
    effective_tenant = 1 if tenant.id == 4 else tenant.id
    sql = """
        WITH category_sortie AS (
            SELECT
                p.categorie,
                COUNT(DISTINCT p.id) as product_count,
                SUM(s.quantite * p.prix_vente) as total_revenue,
                SUM(s.quantite * COALESCE(p.prix_achat, 0)) as total_cost
            FROM produits p
            LEFT JOIN mouvements_stock s ON s.produit_id = p.id
                AND s.type = 'SORTIE'
                AND s.date_mvt >= CURRENT_DATE - :days * INTERVAL '1 day'
            WHERE p.tenant_id = :tenant_id
              AND p.actif = true
              AND p.categorie IS NOT NULL
            GROUP BY p.categorie
        )
        SELECT
            categorie as category,
            product_count,
            COALESCE(total_revenue, 0) as total_revenue,
            COALESCE(total_cost, 0) as total_cost,
            COALESCE(total_revenue, 0) - COALESCE(total_cost, 0) as gross_margin,
            CASE
                WHEN COALESCE(total_revenue, 0) > 0 THEN
                    (COALESCE(total_revenue, 0) - COALESCE(total_cost, 0)) / total_revenue * 100
                ELSE 0
            END as gross_margin_pct
        FROM category_sortie
        ORDER BY gross_margin DESC
    """

    df = query_df(sql, params={"tenant_id": effective_tenant, "days": days_back})

    return [
        CategoryMarginResponse(
            category=row['category'],
            product_count=int(row['product_count']),
            total_revenue=float(row['total_revenue']),
            total_cost=float(row['total_cost']),
            gross_margin=float(row['gross_margin']),
            gross_margin_pct=float(row['gross_margin_pct']),
            avg_margin_per_product=float(row['gross_margin']) / int(row['product_count']) if row['product_count'] > 0 else 0
        )
        for _, row in df.iterrows()
    ]


@router.get("/pamp/{product_id}", response_model=PAMPResponse)
def get_product_pamp(
    product_id: int,
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne le PAMP (Prix d'Achat Moyen Pondéré) d'un produit
    avec l'historique des achats et le détail du calcul.
    """
    # Tenant intelligence (4) accède au tenant épicerie (1)
    effective_tenant = 1 if tenant.id == 4 else tenant.id
    # Infos produit
    product_sql = """
        SELECT id, nom, prix_achat
        FROM produits
        WHERE id = :product_id AND tenant_id = :tenant_id
    """
    product_df = query_df(product_sql, params={"product_id": product_id, "tenant_id": effective_tenant})

    if product_df.empty:
        raise HTTPException(status_code=404, detail="Produit non trouvé")

    product = product_df.iloc[0]

    # Historique achats depuis produits_price_history
    purchases_sql = """
        SELECT
            pph.recorded_at as date,
            1 as quantity,
            pph.prix_achat as unit_price,
            NULL as supplier_name
        FROM produits_price_history pph
        WHERE pph.produit_id = :product_id
          AND pph.recorded_at >= CURRENT_DATE - INTERVAL '365 days'
        ORDER BY pph.recorded_at DESC
    """
    purchases_df = query_df(purchases_sql, params={"product_id": product_id})

    purchase_history = [
        {
            "date": str(row['date']),
            "quantity": float(row['quantity']),
            "unit_price": float(row['unit_price']),
            "supplier": row['supplier_name']
        }
        for _, row in purchases_df.iterrows()
    ]

    # Calcul PAMP
    if purchase_history:
        total_qty = sum(p['quantity'] for p in purchase_history)
        total_value = sum(p['quantity'] * p['unit_price'] for p in purchase_history)
        pamp = total_value / total_qty if total_qty > 0 else 0
        last_price = purchase_history[0]['unit_price']
    else:
        pamp = float(product['prix_achat'] or 0)
        last_price = pamp
        total_qty = 0
        total_value = 0

    price_change = ((last_price - pamp) / pamp * 100) if pamp > 0 else 0

    return PAMPResponse(
        product_id=product_id,
        product_name=product['nom'],
        current_pamp=pamp,
        last_purchase_price=last_price,
        price_change_pct=price_change,
        purchase_history=purchase_history[:20],  # Limiter à 20 entrées
        calculation_details={
            "total_quantity": total_qty,
            "total_value": total_value,
            "formula": "PAMP = Σ(qty × prix) / Σ(qty)",
            "period": "365 jours"
        }
    )


@router.get("/dishes", response_model=List[DishMarginResponse])
def get_dish_margins(
    min_margin_pct: Optional[float] = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne les marges des plats du restaurant avec détail des ingrédients.
    Food cost ratio = Coût ingrédients / Prix de vente
    """
    # Tenant intelligence (4) accède au tenant restaurant (2)
    effective_tenant = 2 if tenant.id == 4 else tenant.id
    sql = """
        SELECT
            d.id as dish_id,
            d.nom as dish_name,
            d.prix_vente_ttc as selling_price,
            COALESCE(SUM(di.quantite * ing.cout_unitaire), 0) as ingredient_cost
        FROM restaurant_plats d
        LEFT JOIN restaurant_plat_ingredients di ON di.plat_id = d.id
        LEFT JOIN restaurant_ingredients ing ON ing.id = di.ingredient_id
        WHERE d.tenant_id = :tenant_id
          AND d.actif = true
        GROUP BY d.id, d.nom, d.prix_vente_ttc
        ORDER BY d.nom
    """

    df = query_df(sql, params={"tenant_id": effective_tenant})

    results = []
    for _, row in df.iterrows():
        selling = float(row['selling_price'] or 0)
        cost = float(row['ingredient_cost'] or 0)
        margin = selling - cost
        margin_pct = (margin / selling * 100) if selling > 0 else 0
        food_cost_ratio = (cost / selling) if selling > 0 else 0

        if min_margin_pct is not None and margin_pct < min_margin_pct:
            continue

        # Récupérer les ingrédients
        ing_sql = """
            SELECT
                ing.nom as ingredient_name,
                di.quantite as quantity,
                ing.cout_unitaire as unit_cost,
                di.quantite * ing.cout_unitaire as total_cost
            FROM restaurant_plat_ingredients di
            JOIN restaurant_ingredients ing ON ing.id = di.ingredient_id
            WHERE di.plat_id = :dish_id
        """
        ing_df = query_df(ing_sql, params={"dish_id": row['dish_id']})
        ingredients = ing_df.to_dict('records') if not ing_df.empty else []

        results.append(DishMarginResponse(
            dish_id=int(row['dish_id']),
            dish_name=row['dish_name'],
            selling_price=selling,
            ingredient_cost=cost,
            gross_margin=margin,
            gross_margin_pct=margin_pct,
            food_cost_ratio=food_cost_ratio,
            ingredients=ingredients
        ))

    return results


@router.get("/alerts", response_model=List[MarginAlertResponse])
def get_margin_alerts(
    threshold_pct: float = Query(default=20.0, ge=0, le=100),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne les alertes pour les produits avec des marges problématiques:
    - Marge négative
    - Marge sous le seuil
    """
    # Tenant intelligence (4) accède au tenant épicerie (1)
    effective_tenant = 1 if tenant.id == 4 else tenant.id
    sql = """
        SELECT
            p.id as product_id,
            p.nom as product_name,
            p.prix_vente,
            p.prix_achat,
            CASE
                WHEN p.prix_vente > 0 THEN
                    (p.prix_vente - COALESCE(p.prix_achat, 0)) / p.prix_vente * 100
                ELSE 0
            END as margin_pct
        FROM produits p
        WHERE p.tenant_id = :tenant_id
          AND p.actif = true
          AND p.prix_vente > 0
        ORDER BY margin_pct ASC
    """

    df = query_df(sql, params={"tenant_id": effective_tenant})
    alerts = []

    for _, row in df.iterrows():
        margin_pct = float(row['margin_pct'])

        if margin_pct < 0:
            alerts.append(MarginAlertResponse(
                product_id=int(row['product_id']),
                product_name=row['product_name'],
                current_margin_pct=margin_pct,
                threshold_pct=threshold_pct,
                alert_type="negative",
                severity="critical",
                recommendation="URGENT: Prix de vente inférieur au prix d'achat. Augmenter le prix ou revoir le fournisseur."
            ))
        elif margin_pct < threshold_pct:
            alerts.append(MarginAlertResponse(
                product_id=int(row['product_id']),
                product_name=row['product_name'],
                current_margin_pct=margin_pct,
                threshold_pct=threshold_pct,
                alert_type="below_threshold",
                severity="warning",
                recommendation=f"Marge sous le seuil de {threshold_pct}%. Considérer une augmentation de prix."
            ))

    return alerts


@router.get("/summary")
def get_margin_summary(
    days_back: int = Query(default=30, ge=1, le=365),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Résumé des marges:
    - Marge brute globale
    - Marge moyenne par catégorie
    - Top et flop produits
    - Évolution vs période précédente
    """
    # Tenant intelligence (4) accède au tenant épicerie (1)
    effective_tenant = 1 if tenant.id == 4 else tenant.id

    # Période actuelle - basé sur mouvements_stock SORTIE
    current_sql = """
        SELECT
            SUM(s.quantite * p.prix_vente) as revenue,
            SUM(s.quantite * COALESCE(p.prix_achat, 0)) as cost
        FROM mouvements_stock s
        JOIN produits p ON p.id = s.produit_id
        WHERE s.tenant_id = :tenant_id
          AND s.type = 'SORTIE'
          AND s.date_mvt >= CURRENT_DATE - :days * INTERVAL '1 day'
    """
    current_df = query_df(current_sql, params={"tenant_id": effective_tenant, "days": days_back})

    current_revenue = float(current_df.iloc[0]['revenue'] or 0) if not current_df.empty else 0
    current_cost = float(current_df.iloc[0]['cost'] or 0) if not current_df.empty else 0
    current_margin = current_revenue - current_cost
    current_margin_pct = (current_margin / current_revenue * 100) if current_revenue > 0 else 0

    # Période précédente
    previous_sql = """
        SELECT
            SUM(s.quantite * p.prix_vente) as revenue,
            SUM(s.quantite * COALESCE(p.prix_achat, 0)) as cost
        FROM mouvements_stock s
        JOIN produits p ON p.id = s.produit_id
        WHERE s.tenant_id = :tenant_id
          AND s.type = 'SORTIE'
          AND s.date_mvt >= CURRENT_DATE - :days * 2 * INTERVAL '1 day'
          AND s.date_mvt < CURRENT_DATE - :days * INTERVAL '1 day'
    """
    previous_df = query_df(previous_sql, params={"tenant_id": effective_tenant, "days": days_back})

    previous_revenue = float(previous_df.iloc[0]['revenue'] or 0) if not previous_df.empty else 0
    previous_cost = float(previous_df.iloc[0]['cost'] or 0) if not previous_df.empty else 0
    previous_margin_pct = ((previous_revenue - previous_cost) / previous_revenue * 100) if previous_revenue > 0 else 0

    # Évolution
    margin_evolution = current_margin_pct - previous_margin_pct

    return {
        "period_days": days_back,
        "current_period": {
            "revenue": current_revenue,
            "cost": current_cost,
            "gross_margin": current_margin,
            "gross_margin_pct": round(current_margin_pct, 2)
        },
        "previous_period": {
            "revenue": previous_revenue,
            "gross_margin_pct": round(previous_margin_pct, 2)
        },
        "evolution": {
            "margin_pct_change": round(margin_evolution, 2),
            "trend": "up" if margin_evolution > 0.5 else "down" if margin_evolution < -0.5 else "stable"
        }
    }
