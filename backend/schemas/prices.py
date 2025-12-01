"""Pydantic schemas for price history endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PriceHistoryItem(BaseModel):
    id: Optional[int] = None
    produit_id: Optional[int] = None
    code: Optional[str] = None
    nom: Optional[str] = None
    ean: Optional[str] = None
    fournisseur: Optional[str] = None
    prix_achat: float
    prev_prix_achat: Optional[float] = None
    prev_facture_date: Optional[datetime] = None
    delta_prix: Optional[float] = None
    delta_pct: Optional[float] = None
    prix_vente: Optional[float] = None
    marge_unitaire: Optional[float] = None
    marge_pct: Optional[float] = None
    margin_alert: Optional[bool] = None
    stock_alert: Optional[bool] = None
    stockout_repeated: Optional[bool] = None
    stockout_events: Optional[int] = None
    stock_actuel: Optional[float] = None
    seuil_alerte: Optional[float] = None
    quantite: Optional[float] = None
    montant: Optional[float] = None
    facture_date: datetime
    source_context: Optional[str] = None


class PriceHistoryResponse(BaseModel):
    items: List[PriceHistoryItem]


class LatestPriceEntry(PriceHistoryItem):
    """Vue simplifiée du dernier prix connu par code."""


class LatestPriceResponse(BaseModel):
    items: List[LatestPriceEntry]


__all__ = ["PriceHistoryItem", "PriceHistoryResponse", "LatestPriceEntry", "LatestPriceResponse"]
