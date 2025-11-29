"""Stock & movement endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.schemas.stock import (
    MovementTimeseriesResponse,
    RecentMovementsResponse,
    StockAdjustmentRequest,
    StockAdjustmentResponse,
)
from backend.services import stock as stock_service
from backend.dependencies.tenant import Tenant, get_current_tenant

router = APIRouter(prefix="/stock", tags=["stock"])


@router.get("/movements/timeseries", response_model=MovementTimeseriesResponse)
def get_movement_timeseries(
    window_days: int = Query(30, ge=1, le=365),
    product_id: int | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
):
    df = stock_service.fetch_movement_timeseries(
        window_days=window_days,
        product_id=product_id,
        tenant_id=tenant.id,
    )
    items = df.to_dict(orient="records")
    return MovementTimeseriesResponse(items=items)


@router.get("/movements/recent", response_model=RecentMovementsResponse)
def get_recent_movements(
    limit: int = Query(50, ge=1, le=500),
    product_id: int | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
):
    df = stock_service.fetch_recent_movements(
        limit=limit,
        product_id=product_id,
        tenant_id=tenant.id,
    )
    items = df.to_dict(orient="records")
    return RecentMovementsResponse(items=items)


@router.post("/adjustments", response_model=StockAdjustmentResponse)
def create_stock_adjustment(
    payload: StockAdjustmentRequest,
    tenant: Tenant = Depends(get_current_tenant),
):
    try:
        result = stock_service.adjust_stock_level(
            payload.product_id,
            payload.target_quantity,
            username=payload.username,
            tenant_id=tenant.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return StockAdjustmentResponse(**result)
