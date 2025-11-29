"""Admin & tooling endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.schemas.admin import (
    AdminOverviewResponse,
    AdminUsersResponse,
    BackupCreationPayload,
    BackupMetadataModel,
    BackupSettingsModel,
    IntegrityReportEntry,
    ResetPasswordPayload,
    UpdateRolePayload,
)
from backend.services import admin as admin_service
from backend.dependencies.tenant import Tenant, get_current_tenant
from backend.dependencies.security import require_roles

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_roles("admin"))],
)


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview(tenant: Tenant = Depends(get_current_tenant)):
    payload = admin_service.fetch_admin_overview(tenant_id=tenant.id)
    return AdminOverviewResponse(**payload)


@router.get("/users", response_model=AdminUsersResponse)
def list_users():
    users = admin_service.list_admin_users()
    return AdminUsersResponse(users=users, roles=list(admin_service.ALLOWED_ROLES))


@router.post("/users/{user_id}/role")
def change_user_role(user_id: int, payload: UpdateRolePayload):
    try:
        admin_service.update_role(user_id, payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"status": "updated"}


@router.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: int, payload: ResetPasswordPayload | None = None):
    try:
        password = admin_service.reset_password(user_id, (payload or ResetPasswordPayload()).new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"password": password}


@router.post("/backups", response_model=BackupMetadataModel)
def create_backup(payload: BackupCreationPayload | None = None):
    try:
        metadata = admin_service.create_backup_now((payload or BackupCreationPayload()).label)
    except admin_service.BackupError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return BackupMetadataModel(**metadata)


@router.post("/backups/{filename}/restore")
def restore_backup(filename: str):
    try:
        admin_service.restore_backup_file(filename)
    except admin_service.BackupError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return {"status": "restored"}


@router.delete("/backups/{filename}")
def delete_backup(filename: str):
    try:
        admin_service.delete_backup_file(filename)
    except admin_service.BackupError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return {"status": "deleted"}


@router.get("/backups/integrity", response_model=list[IntegrityReportEntry])
def get_integrity_report():
    data = admin_service.run_integrity_report()
    return [IntegrityReportEntry(**item) for item in data]


@router.get("/settings", response_model=BackupSettingsModel)
def get_backup_settings():
    overview = admin_service.fetch_backup_overview()
    return BackupSettingsModel(**overview["settings"])


@router.put("/settings", response_model=BackupSettingsModel)
def update_backup_settings(payload: BackupSettingsModel):
    settings = admin_service.save_settings(payload.dict())
    return BackupSettingsModel(**settings)
