from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .prices import LatestPriceEntry


class TenantCapitalSnapshot(BaseModel):
    tenant_id: int
    code: str
    name: str
    stock_value: float
    bank_balance: float
    cash_balance: float
    total_assets: float
    snapshot_date: Optional[datetime]


class GlobalCapitalSnapshot(BaseModel):
    stock_value: float
    bank_balance: float
    cash_balance: float
    total_assets: float
    snapshot_date: Optional[datetime] = None


class CapitalEntitySnapshot(BaseModel):
    entity_id: int
    code: str
    name: str
    stock_value: float
    bank_balance: float
    cash_balance: float
    total_assets: float
    members: List[TenantCapitalSnapshot]


class CapitalOverviewResponse(BaseModel):
    entities: List[CapitalEntitySnapshot]
    global_summary: GlobalCapitalSnapshot = Field(...)
    latest_prices: List[LatestPriceEntry]


__all__ = [
    "TenantCapitalSnapshot",
    "GlobalCapitalSnapshot",
    "CapitalEntitySnapshot",
    "CapitalOverviewResponse",
]
