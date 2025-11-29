"""Schemas for dashboard metrics."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class DashboardKPIs(BaseModel):
    total_produits: int
    valeur_stock_ht: float
    quantite_stock_total: float
    alerte_stock_bas: int
    stock_epuise: int


class TopEntry(BaseModel):
    nom: str
    valeur_stock: float | None = None
    quantite_vendue: float | None = None


class StatusEntry(BaseModel):
    statut_stock: str
    nombre: int


class DashboardResponse(BaseModel):
    kpis: DashboardKPIs
    top_stock_value: List[TopEntry]
    top_sales: List[TopEntry]
    status_distribution: List[StatusEntry]


__all__ = ['DashboardResponse', 'DashboardKPIs']
