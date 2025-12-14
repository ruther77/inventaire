"""Schemas for newCMS restaurant endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# Restaurant Overview Schemas
class RestaurantPlatCost(BaseModel):
    """Light plat cost summary for overview."""
    plat_id: int
    nom: str
    food_cost_pct: float
    marge_pct: float
    prix_vente_ttc: float
    cout_matiere: float


class RestaurantStockLocation(BaseModel):
    """Stock per location (bar, cuisine, cave)."""
    location: str
    count: int
    valeur: float


class RestaurantIngredientAlert(BaseModel):
    """Ingredient stock alert."""
    ingredient_id: int
    nom: str
    stock_actuel: float
    seuil_alerte: float
    status: str  # 'rupture', 'alerte', 'ok'


class RestaurantTopPlat(BaseModel):
    """Top plat by margin."""
    plat_id: int
    nom: str
    marge_pct: float
    prix_vente_ttc: float
    cout_matiere: float


class RestaurantOverviewMetrics(BaseModel):
    """Aggregated metrics for restaurant overview."""
    total_plats: int
    avg_food_cost_pct: float
    alerts_count: int
    top_plats: List[RestaurantTopPlat]


class RestaurantOverviewResponse(BaseModel):
    """Complete restaurant overview response."""
    metrics: RestaurantOverviewMetrics
    plat_costs: List[RestaurantPlatCost]
    stock_locations: List[RestaurantStockLocation]
    ingredient_alerts: List[RestaurantIngredientAlert]


# Mobile Inventory Schemas
class MobileInventoryItem(BaseModel):
    """Lightweight inventory item for mobile scanning."""
    id: int
    nom: str
    code_barre: Optional[str] = None
    stock_actuel: float
    seuil_alerte: float
    categorie: Optional[str] = None


class MobileInventoryListResponse(BaseModel):
    """Paginated inventory list for mobile."""
    items: List[MobileInventoryItem]
    total: int
    page: int
    page_size: int


# Mobile Scan Schemas
class MobileScanRequest(BaseModel):
    """Barcode scan request."""
    code_barre: str = Field(..., min_length=1)


class MobileScanResponse(BaseModel):
    """Product found by barcode scan."""
    found: bool
    product: Optional[MobileInventoryItem] = None
    message: Optional[str] = None


# Mobile Stock Adjustment Schemas
class MobileAdjustRequest(BaseModel):
    """Stock adjustment request from mobile."""
    product_id: int = Field(..., gt=0)
    adjustment: float = Field(..., description="Delta: +1, -1, or absolute value")
    adjustment_type: str = Field(default="delta", description="'delta' for +/- or 'absolute' for exact value")
    reason: str = Field(..., description="breakage, theft, error, expiry, other")
    notes: Optional[str] = None


class MobileAdjustResponse(BaseModel):
    """Stock adjustment confirmation."""
    product_id: int
    product_name: str
    old_stock: float
    new_stock: float
    adjustment: float
    reason: str
    timestamp: datetime


__all__ = [
    "RestaurantOverviewResponse",
    "RestaurantOverviewMetrics",
    "RestaurantPlatCost",
    "RestaurantStockLocation",
    "RestaurantIngredientAlert",
    "RestaurantTopPlat",
    "MobileInventoryListResponse",
    "MobileInventoryItem",
    "MobileScanRequest",
    "MobileScanResponse",
    "MobileAdjustRequest",
    "MobileAdjustResponse",
]
