"""Endpoints d'analytics basiques (KPI consolidés par tenant)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.dependencies.auth import optional_api_key
from backend.dependencies.security import enforce_default_rbac
from backend.dependencies.tenant import Tenant, get_current_tenant
from core.data_repository import query_df


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(optional_api_key), Depends(enforce_default_rbac)],
)


class MovementStat(BaseModel):
    type: str
    count: int = Field(0, ge=0)
    quantity: float = Field(0, ge=0)


class TopProduct(BaseModel):
    id: int
    nom: str
    qty: float
    revenue: float
    margin: float


class TopCategory(BaseModel):
    categorie: str
    qty: float
    revenue: float
    margin: float


class AnalyticsSummary(BaseModel):
    products_active: int = Field(0, ge=0)
    stock_value_sale: float = 0.0
    stock_value_purchase: float = 0.0
    movements_last_30d: list[MovementStat] = []
    sales_qty_30d: float = 0.0
    sales_revenue_30d: float = 0.0
    sales_margin_30d: float = 0.0
    top_products_30d: list[TopProduct] = []
    top_categories_30d: list[TopCategory] = []


def _fetch_summary(tenant_id: int) -> AnalyticsSummary:
    stock_sql = """
        SELECT
            COUNT(*) FILTER (WHERE actif) AS products_active,
            COALESCE(SUM(COALESCE(prix_vente, 0) * COALESCE(stock_actuel, 0)), 0) AS stock_value_sale,
            COALESCE(SUM(COALESCE(prix_achat, 0) * COALESCE(stock_actuel, 0)), 0) AS stock_value_purchase
        FROM produits
        WHERE tenant_id = :tenant_id
    """
    stock_df = query_df(stock_sql, params={"tenant_id": tenant_id})
    row = stock_df.iloc[0] if not stock_df.empty else None

    since = datetime.now(timezone.utc) - timedelta(days=30)
    movements_sql = """
        SELECT type, COUNT(*) AS count, COALESCE(SUM(quantite), 0) AS quantity
        FROM mouvements_stock
        WHERE tenant_id = :tenant_id
          AND date_mvt >= :since
        GROUP BY type
    """
    mov_df = query_df(movements_sql, params={"tenant_id": tenant_id, "since": since})

    movements = [
        MovementStat(type=str(record["type"]), count=int(record["count"]), quantity=float(record["quantity"] or 0))
        for record in mov_df.to_dict("records")
    ] if not mov_df.empty else []

    sales_sql = """
        SELECT
            COALESCE(SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END), 0) AS qty,
            COALESCE(SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite * COALESCE(p.prix_vente, 0) ELSE 0 END), 0) AS revenue,
            COALESCE(SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite * COALESCE(p.prix_achat, 0) ELSE 0 END), 0) AS cost
        FROM mouvements_stock m
        JOIN produits p ON p.id = m.produit_id AND p.tenant_id = m.tenant_id
        WHERE m.tenant_id = :tenant_id
          AND m.date_mvt >= :since
    """
    sales_df = query_df(sales_sql, params={"tenant_id": tenant_id, "since": since})
    sales_row = sales_df.iloc[0] if not sales_df.empty else None
    sales_qty = float(sales_row["qty"] or 0) if sales_row is not None else 0.0
    sales_rev = float(sales_row["revenue"] or 0) if sales_row is not None else 0.0
    sales_cost = float(sales_row["cost"] or 0) if sales_row is not None else 0.0
    sales_margin = sales_rev - sales_cost

    top_products_sql = """
        SELECT
            p.id,
            p.nom,
            COALESCE(SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END), 0) AS qty,
            COALESCE(SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite * COALESCE(p.prix_vente, 0) ELSE 0 END), 0) AS revenue,
            COALESCE(SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite * (COALESCE(p.prix_vente, 0) - COALESCE(p.prix_achat, 0)) ELSE 0 END), 0) AS margin
        FROM produits p
        JOIN mouvements_stock m ON m.produit_id = p.id AND m.tenant_id = p.tenant_id
        WHERE p.tenant_id = :tenant_id AND m.date_mvt >= :since
        GROUP BY p.id, p.nom
        ORDER BY revenue DESC
        LIMIT 5
    """
    top_prod_df = query_df(top_products_sql, params={"tenant_id": tenant_id, "since": since})
    top_products = [
        TopProduct(
            id=int(rec["id"]),
            nom=str(rec["nom"]),
            qty=float(rec["qty"] or 0),
            revenue=float(rec["revenue"] or 0),
            margin=float(rec["margin"] or 0),
        )
        for rec in (top_prod_df.to_dict("records") if not top_prod_df.empty else [])
    ]

    top_categories_sql = """
        SELECT
            COALESCE(p.categorie, 'Non classé') AS categorie,
            COALESCE(SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END), 0) AS qty,
            COALESCE(SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite * COALESCE(p.prix_vente, 0) ELSE 0 END), 0) AS revenue,
            COALESCE(SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite * (COALESCE(p.prix_vente, 0) - COALESCE(p.prix_achat, 0)) ELSE 0 END), 0) AS margin
        FROM produits p
        JOIN mouvements_stock m ON m.produit_id = p.id AND m.tenant_id = p.tenant_id
        WHERE p.tenant_id = :tenant_id AND m.date_mvt >= :since
        GROUP BY COALESCE(p.categorie, 'Non classé')
        ORDER BY revenue DESC
        LIMIT 5
    """
    top_cat_df = query_df(top_categories_sql, params={"tenant_id": tenant_id, "since": since})
    top_categories = [
        TopCategory(
            categorie=str(rec["categorie"]),
            qty=float(rec["qty"] or 0),
            revenue=float(rec["revenue"] or 0),
            margin=float(rec["margin"] or 0),
        )
        for rec in (top_cat_df.to_dict("records") if not top_cat_df.empty else [])
    ]

    return AnalyticsSummary(
        products_active=int(row["products_active"]) if row is not None else 0,
        stock_value_sale=float(row["stock_value_sale"]) if row is not None else 0.0,
        stock_value_purchase=float(row["stock_value_purchase"]) if row is not None else 0.0,
        movements_last_30d=movements,
        sales_qty_30d=sales_qty,
        sales_revenue_30d=sales_rev,
        sales_margin_30d=sales_margin,
        top_products_30d=top_products,
        top_categories_30d=top_categories,
    )


@router.get("/summary", response_model=AnalyticsSummary)
def get_summary(tenant: Tenant = Depends(get_current_tenant)) -> AnalyticsSummary:
    """Retourne quelques KPI agrégés (stock et mouvements récents) pour le tenant courant."""

    return _fetch_summary(tenant.id)
