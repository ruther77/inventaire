"""Schémas pour les endpoints de stock et de mouvements."""

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


class CategoryBreakdown(BaseModel):
    categorie: str
    product_count: int
    total_quantity: float
    total_value: float


class SnapshotCreateRequest(BaseModel):
    snapshot_date: Optional[date] = None


class SnapshotCreateResponse(BaseModel):
    snapshot_id: int
    snapshot_date: str
    stock_value: float
    bank_balance: float
    cash_balance: float
    total_assets: float
    product_count: int
    total_quantity: float
    categories: List[CategoryBreakdown]


class SnapshotData(BaseModel):
    id: int
    date: str
    stock_value: float
    bank_balance: float
    cash_balance: float
    total_assets: float


class SnapshotComparisonRequest(BaseModel):
    date1: date
    date2: date


class SnapshotComparisonResponse(BaseModel):
    date1: str
    date2: str
    snapshot1: SnapshotData
    snapshot2: SnapshotData
    difference: float
    difference_pct: float
    evolution: str


class SnapshotHistoryItem(BaseModel):
    id: int
    snapshot_date: str
    stock_value: float
    bank_balance: float
    cash_balance: float
    total_assets: float
    created_at: str


class SnapshotHistoryResponse(BaseModel):
    items: List[SnapshotHistoryItem]


__all__ = [
    "MovementTimeseriesResponse",
    "MovementPoint",
    "RecentMovementsResponse",
    "RecentMovement",
    "StockAdjustmentRequest",
    "StockAdjustmentResponse",
    "CategoryBreakdown",
    "SnapshotCreateRequest",
    "SnapshotCreateResponse",
    "SnapshotData",
    "SnapshotComparisonRequest",
    "SnapshotComparisonResponse",
    "SnapshotHistoryItem",
    "SnapshotHistoryResponse",
]
