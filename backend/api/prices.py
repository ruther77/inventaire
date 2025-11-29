"""Price history API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.schemas.prices import LatestPriceResponse, PriceHistoryResponse
from core.price_history_service import fetch_latest_price_per_code, fetch_price_history
from backend.dependencies.tenant import Tenant, get_current_tenant

router = APIRouter(prefix="/prices", tags=["prix"])


@router.get("/history", response_model=PriceHistoryResponse)
def get_price_history(
    product_id: Optional[int] = Query(default=None, alias="product_id"),
    code: Optional[str] = None,
    supplier: Optional[str] = None,
    search: Optional[str] = None,
    date_start: Optional[datetime] = Query(default=None),
    date_end: Optional[datetime] = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
    tenant: Tenant = Depends(get_current_tenant),
):
    df = fetch_price_history(
        produit_id=product_id,
        code=code,
        supplier=supplier,
        search=search,
        date_start=date_start,
        date_end=date_end,
        limit=limit,
        tenant_id=tenant.id,
    )
    if df.empty:
        return PriceHistoryResponse(items=[])

    df = df.replace({"": None})
    items = df.to_dict(orient="records")
    return PriceHistoryResponse(items=items)
@router.get("/latest", response_model=LatestPriceResponse)
def get_latest_price_history(
    codes: list[str] | None = Query(default=None, description="Filtrer sur une liste de codes (répéter le param)."),
    limit: int = Query(default=100, ge=1, le=500),
    tenant: Tenant = Depends(get_current_tenant),
):
    df = fetch_latest_price_per_code(tenant_id=tenant.id, codes=codes, limit=limit)
    if df.empty:
        return LatestPriceResponse(items=[])
    df = df.replace({"": None})
    items = df.to_dict(orient="records")
    return LatestPriceResponse(items=items)
