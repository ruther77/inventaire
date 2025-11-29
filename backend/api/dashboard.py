"""Dashboard endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.schemas.dashboard import DashboardResponse
from backend.services import dashboard as dashboard_service
from backend.dependencies.tenant import Tenant, get_current_tenant

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardResponse)
def get_dashboard_metrics(tenant: Tenant = Depends(get_current_tenant)):
    data = dashboard_service.fetch_dashboard_metrics(tenant_id=tenant.id)
    return DashboardResponse(**data)
