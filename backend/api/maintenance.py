"""Maintenance endpoints (backups)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.schemas.maintenance import BackupListResponse
from backend.services import maintenance as maintenance_service

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/backups", response_model=BackupListResponse)
def list_backups(limit: int = Query(default=100, ge=1, le=1000)):
    backups = maintenance_service.list_backups(limit=limit)
    return BackupListResponse(backups=backups)


@router.get("/backups/{filename}")
def download_backup(filename: str):
    backups = maintenance_service.list_backups()
    match = next((entry for entry in backups if entry["name"] == filename), None)
    if not match:
        raise HTTPException(status_code=404, detail="Sauvegarde introuvable.")
    path = Path(match["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Fichier absent du disque.")
    return FileResponse(path, filename=path.name)
