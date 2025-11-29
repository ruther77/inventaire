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
    fournisseur: Optional[str] = None
    prix_achat: float
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
