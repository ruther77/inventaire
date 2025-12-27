"""Endpoints stock et mouvements."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.schemas.stock import (
    MovementTimeseriesResponse,
    RecentMovementsResponse,
    SnapshotComparisonRequest,
    SnapshotComparisonResponse,
    SnapshotCreateRequest,
    SnapshotCreateResponse,
    SnapshotHistoryResponse,
    StockAdjustmentRequest,
    StockAdjustmentResponse,
)
from backend.services import stock as stock_service
from backend.dependencies.tenant import Tenant, get_current_tenant
from core import inventory_snapshots

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


@router.post("/snapshots/create", response_model=SnapshotCreateResponse)
def create_inventory_snapshot(
    payload: SnapshotCreateRequest = SnapshotCreateRequest(),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Create a snapshot of current inventory values.

    This endpoint manually triggers the creation of an inventory snapshot
    for reporting and comparison purposes. Snapshots capture:
    - Total stock value across all products
    - Breakdown by category
    - Product counts and quantities

    By default, creates a snapshot for today. You can optionally specify
    a different date using the snapshot_date parameter.
    """
    try:
        result = inventory_snapshots.create_daily_snapshot(
            tenant_id=tenant.id,
            snapshot_date=payload.snapshot_date,
        )
        return SnapshotCreateResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create snapshot: {str(exc)}",
        ) from exc


@router.get("/snapshots/compare", response_model=SnapshotComparisonResponse)
def compare_inventory_snapshots(
    date1: date = Query(..., description="First comparison date (typically earlier)"),
    date2: date = Query(..., description="Second comparison date (typically later)"),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Compare inventory snapshots between two dates.

    Returns the difference in stock value and percentage change between
    two snapshot dates. Useful for period-over-period analysis.

    Query Parameters:
    - date1: First date (YYYY-MM-DD format)
    - date2: Second date (YYYY-MM-DD format)

    The response includes:
    - Data from both snapshots
    - Absolute difference in value
    - Percentage change
    - Evolution indicator (increase/decrease/stable)
    """
    try:
        result = inventory_snapshots.get_snapshot_comparison(
            tenant_id=tenant.id,
            date1=date1,
            date2=date2,
        )
        return SnapshotComparisonResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare snapshots: {str(exc)}",
        ) from exc


@router.get("/snapshots/history", response_model=SnapshotHistoryResponse)
def get_snapshot_history(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of snapshots"),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Get historical inventory snapshots.

    Returns a list of snapshots for the specified period, ordered by date
    descending (most recent first).

    Query Parameters:
    - days: Number of days to look back (default: 30)
    - limit: Maximum number of snapshots to return (default: 100)
    """
    try:
        snapshots = inventory_snapshots.get_snapshot_history(
            tenant_id=tenant.id,
            days=days,
            limit=limit,
        )
        return SnapshotHistoryResponse(items=snapshots)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch snapshot history: {str(exc)}",
        ) from exc
