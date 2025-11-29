"""Schemas for admin utilities."""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class TableCount(BaseModel):
    table: str
    lignes: int


class DiagnosticEntry(BaseModel):
    id: int
    nom: str
    stock_actuel: float
    stock_calcule: float
    ecart: float


class MovementEntry(BaseModel):
    date_mvt: datetime
    produit: str
    type: str
    quantite: float
    source: Optional[str] = None


class BackupStats(BaseModel):
    total_size_mb: float = 0.0
    average_size_mb: float = 0.0
    max_size_mb: float = 0.0
    min_size_mb: float = 0.0


class BackupSummary(BaseModel):
    count: int
    stats: BackupStats
    next_run: Optional[datetime] = None


class BackupMetadataModel(BaseModel):
    name: str
    size_bytes: int
    created_at: datetime
    path: str


class BackupTimelinePoint(BaseModel):
    name: str
    created_at: datetime
    size_mb: float


class BinaryStatusModel(BaseModel):
    name: str
    configured: str
    resolved: Optional[str] = None
    source: str
    available: bool


class BackupSettingsModel(BaseModel):
    frequency: Literal["manual", "daily", "weekly"] = "manual"
    time: str = "02:00"
    weekday: int = Field(0, ge=0, le=6)
    retention_days: int = Field(30, ge=1, le=365)
    max_backups: int = Field(20, ge=1, le=500)
    notifications: List[str] = Field(default_factory=list)
    integrity_checks: bool = True


class BackupOverview(BaseModel):
    summary: BackupSummary
    recent: List[BackupMetadataModel]
    timeline: List[BackupTimelinePoint]
    tool_status: List[BinaryStatusModel]
    settings: BackupSettingsModel
    suggested_cleanup: List[str]


class IntegrityReportEntry(BaseModel):
    name: str
    created_at: Optional[datetime] = None
    status: str
    details: str


class AdminOverviewResponse(BaseModel):
    backups: BackupOverview
    table_counts: List[TableCount]
    diagnostics: List[DiagnosticEntry]
    recent_movements: List[MovementEntry]


class AdminUser(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: datetime


class AdminUsersResponse(BaseModel):
    users: List[AdminUser]
    roles: List[str]


class UpdateRolePayload(BaseModel):
    role: str


class ResetPasswordPayload(BaseModel):
    new_password: Optional[str] = None


class BackupCreationPayload(BaseModel):
    label: Optional[str] = None


__all__ = [
    "AdminOverviewResponse",
    "AdminUser",
    "AdminUsersResponse",
    "BackupCreationPayload",
    "BackupOverview",
    "BackupSettingsModel",
    "IntegrityReportEntry",
    "ResetPasswordPayload",
    "UpdateRolePayload",
]
