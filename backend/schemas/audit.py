"""Pydantic schemas for audit endpoints."""

from __future__ import annotations

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class AuditSummary(BaseModel):
    anomalies: int
    delta: float
    assigned: int
    open_tasks: int


class AuditDiagnosticItem(BaseModel):
    product_id: int
    nom: str
    categorie: Optional[str] = None
    stock_actuel: float
    stock_calcule: float
    ecart: float
    ecart_abs: float
    niveau_ecart: str
    responsable: Optional[str] = None
    action_status: Optional[str] = None
    action_id: Optional[int] = None


class AuditDiagnosticsResponse(BaseModel):
    available_categories: List[str]
    summary: AuditSummary
    items: List[AuditDiagnosticItem]


class AuditAssignmentRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    responsable: str = Field(..., min_length=1)
    note: Optional[str] = None
    due_date: Optional[date] = None
    create_task: bool = True


class AuditActionOut(BaseModel):
    id: int
    product_id: int
    responsable: str
    note: Optional[str] = None
    status: str
    due_date: Optional[str] = None
    created_at: str


class AuditActionsResponse(BaseModel):
    items: List[AuditActionOut]


class AuditResolutionRequest(BaseModel):
    status: Literal["En cours", "Résolu"]
    note: Optional[str] = None


class AuditResolutionLogEntry(BaseModel):
    id: int
    action_id: Optional[int] = None
    product_id: int
    statut: str
    note: Optional[str] = None
    responsable: Optional[str] = None
    created_at: str


class AuditResolutionLogResponse(BaseModel):
    items: List[AuditResolutionLogEntry]


__all__ = [
    "AuditDiagnosticsResponse",
    "AuditAssignmentRequest",
    "AuditActionOut",
    "AuditActionsResponse",
    "AuditResolutionRequest",
    "AuditResolutionLogResponse",
]
