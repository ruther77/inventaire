"""Routeur API des rapports."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.schemas.reports import ReportsOverview
from backend.services import reports as reports_service
from backend.dependencies.tenant import Tenant, get_current_tenant

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/overview", response_model=ReportsOverview)
def get_reports_overview(tenant: Tenant = Depends(get_current_tenant)):
    """Retourne les analytics agrégées pour l'espace rapports."""

    data = reports_service.build_overview(tenant_id=tenant.id)
    return ReportsOverview(**data)


@router.get("/export/{report_type}")
def export_report_dataset(
    report_type: str,
    limit: int = Query(default=5000, ge=10, le=50_000),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Diffuse un export CSV pour le dataset demandé."""

    try:
        filename, payload = reports_service.export_dataset(report_type, limit, tenant_id=tenant.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return StreamingResponse(
        iter([payload]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
