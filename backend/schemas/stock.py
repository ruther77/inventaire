"""Schemas for stock and movement endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MovementPoint(BaseModel):
    jour: date
    type: str
    quantite: float


class MovementTimeseriesResponse(BaseModel):
    items: List[MovementPoint]


class RecentMovement(BaseModel):
    id: int
    date_mvt: datetime
    produit_id: int
    produit: str
    type: str
    quantite: float
    source: Optional[str] = None


class RecentMovementsResponse(BaseModel):
    items: List[RecentMovement]


class StockAdjustmentRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    target_quantity: float = Field(..., ge=0)
    username: Optional[str] = None


class StockAdjustmentResponse(BaseModel):
    product_id: int
    product_name: str
    current_stock: float
    new_stock: float
    movement_created: bool
    movement_type: Optional[str] = None
    movement_quantity: Optional[float] = None


__all__ = [
    "MovementTimeseriesResponse",
    "MovementPoint",
    "RecentMovementsResponse",
    "RecentMovement",
    "StockAdjustmentRequest",
    "StockAdjustmentResponse",
]
