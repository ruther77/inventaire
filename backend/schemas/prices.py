"""Schémas Pydantic pour les endpoints d'historique des prix."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel
from pydantic import Field


class PriceHistoryResponse(BaseModel):
    items: List[dict[str, Any]]


class LatestPriceResponse(BaseModel):
    items: List[dict[str, Any]]


class PriceCorrectionItem(BaseModel):
    product_id: Optional[int] = Field(None, description="ID produit cible (sinon code_barre)")
    code: Optional[str] = Field(None, description="Code-barres pour retrouver le produit")
    prix_achat: Optional[float] = Field(None, ge=0)
    prix_vente: Optional[float] = Field(None, ge=0)
    tva: Optional[float] = Field(None, ge=0)


class BulkPriceCorrectionRequest(BaseModel):
    items: List[PriceCorrectionItem]


class BulkPriceCorrectionResponse(BaseModel):
    updated: int
    skipped: List[dict[str, Any]]


__all__ = [
    "PriceHistoryResponse",
    "LatestPriceResponse",
    "PriceCorrectionItem",
    "BulkPriceCorrectionRequest",
    "BulkPriceCorrectionResponse",
]
