"""Pydantic schemas for the supply planning API."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SupplyPlanParamsSchema(BaseModel):
    target_coverage: int = Field(..., ge=1, description="Nombre de jours de stock visés.")
    alert_threshold: int = Field(..., ge=1, description="Seuil d’alerte en jours de couverture.")
    min_daily_sales: float = Field(..., ge=0, description="Filtre des produits à faible rotation.")
    categories: Optional[List[str]] = Field(
        default=None,
        description="Liste optionnelle de catégories incluses dans le plan.",
    )
    search: Optional[str] = Field(
        default=None,
        description="Terme de recherche appliqué côté serveur.",
    )


class SupplyPlanSummarySchema(BaseModel):
    analyzed: int
    recommended_count: int
    units_to_order: int
    value_total: float
    margin_total: float


class SupplyPlanItemSchema(BaseModel):
    id: int
    nom: str
    categorie: Optional[str] = None
    ventes_jour: float
    stock_actuel: float
    couverture_jours: Optional[float] = None
    ecart_couverture: Optional[float] = None
    niveau_priorite: str
    quantite_a_commander: int
    valeur_commande: float
    marge_pct: Optional[float] = None
    marge_commande: float
    fournisseur: Optional[str] = None
    ean: Optional[str] = None


class SupplierBreakdownSchema(BaseModel):
    fournisseur: str
    articles: int
    quantite: int
    valeur: float
    marge: float


class SupplyPlanResponseSchema(BaseModel):
    params: SupplyPlanParamsSchema
    summary: SupplyPlanSummarySchema
    available_categories: List[str]
    items: List[SupplyPlanItemSchema]
    supplier_breakdown: List[SupplierBreakdownSchema]


__all__ = [
    "SupplyPlanParamsSchema",
    "SupplyPlanSummarySchema",
    "SupplyPlanItemSchema",
    "SupplierBreakdownSchema",
    "SupplyPlanResponseSchema",
]
