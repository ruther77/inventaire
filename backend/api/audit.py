"""Audit & discrepancies API routes."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.schemas.audit import (
    AuditActionOut,
    AuditActionsResponse,
    AuditAssignmentRequest,
    AuditDiagnosticsResponse,
    AuditResolutionLogResponse,
    AuditResolutionRequest,
)
from backend.services import audit as audit_service
from backend.dependencies.tenant import Tenant, get_current_tenant

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/diagnostics", response_model=AuditDiagnosticsResponse)
def get_diagnostics(
    categories: Optional[List[str]] = Query(
        default=None,
        description="Répéter le paramètre pour filtrer par catégorie.",
    ),
    levels: Optional[List[str]] = Query(default=None, description="Filtrer par niveau d'écart."),
    min_abs: Optional[float] = Query(default=None, ge=0.0),
    max_abs: Optional[float] = Query(default=None, ge=0.0),
    tenant: Tenant = Depends(get_current_tenant),
):
    return audit_service.list_diagnostics(
        categories=categories,
        levels=levels,
        min_abs=min_abs,
        max_abs=max_abs,
        tenant_id=tenant.id,
    )


@router.get("/actions", response_model=AuditActionsResponse)
def get_actions(
    include_closed: bool = Query(default=False),
    tenant: Tenant = Depends(get_current_tenant),
):
    items = audit_service.list_actions(include_closed=include_closed, tenant_id=tenant.id)
    return AuditActionsResponse(items=items)


@router.get("/resolutions", response_model=AuditResolutionLogResponse)
def get_resolution_log(
    limit: int = Query(default=100, ge=1, le=500),
    tenant: Tenant = Depends(get_current_tenant),
):
    items = audit_service.list_resolution_log(limit=limit, tenant_id=tenant.id)
    return AuditResolutionLogResponse(items=items)


@router.post("/assignments", response_model=AuditActionOut, status_code=201)
def create_assignment(payload: AuditAssignmentRequest, tenant: Tenant = Depends(get_current_tenant)):
    try:
        return audit_service.create_assignment(
            product_id=payload.product_id,
            responsable=payload.responsable,
            note=payload.note,
            due_date=payload.due_date,
            create_task=payload.create_task,
            tenant_id=tenant.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/actions/{action_id}/status", response_model=AuditActionOut)
def update_action_status(
    action_id: int,
    payload: AuditResolutionRequest,
    tenant: Tenant = Depends(get_current_tenant),
):
    try:
        audit_service.update_action_status(
            action_id=action_id,
            status=payload.status,
            note=payload.note,
            tenant_id=tenant.id,
        )
        # Return updated representation
        items = audit_service.list_actions(include_closed=True)
        for item in items:
            if item["id"] == action_id:
                return item
        raise HTTPException(status_code=404, detail="Action introuvable après mise à jour.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
