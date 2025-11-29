"""Pydantic schemas for reporting endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class ReportKPIs(BaseModel):
    total_products: int = Field(0, ge=0)
    units_available: float = 0.0
    stock_value: float = 0.0
    alert_count: int = Field(0, ge=0)
    negative_count: int = Field(0, ge=0)


class CategoryBreakdownEntry(BaseModel):
    category: str
    units: float
    value: float


class ValueLeaderEntry(BaseModel):
    id: int
    nom: str
    stock: float
    prix_achat: float | None = None
    valeur_achat: float


class AlertEntry(BaseModel):
    id: int
    nom: str
    categorie: str | None = None
    stock_actuel: float
    seuil_alerte: float | None = None


class RotationEntry(BaseModel):
    id: int
    nom: str
    entrees_30j: float | None = None
    sorties_30j: float | None = None


class SupplierEntry(BaseModel):
    fournisseur: str
    quantite: float | None = None
    valeur: float | None = None


class CapitalSnapshotEntry(BaseModel):
    stock_value: float
    bank_balance: float
    cash_balance: float
    total_assets: float
    snapshot_date: datetime | None = None


class ReportsOverview(BaseModel):
    kpis: ReportKPIs
    category_breakdown: List[CategoryBreakdownEntry]
    top_value: List[ValueLeaderEntry]
    low_stock: List[AlertEntry]
    negative_stock: List[AlertEntry]
    rotation: List[RotationEntry]
    supplier_inflows: List[SupplierEntry]
    capital_snapshot: CapitalSnapshotEntry



__all__ = ["ReportsOverview"]
