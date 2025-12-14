"""Interfaces pour le catalogue (injection friendly)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Iterable

@dataclass
class ProductSummary:
    id: int
    nom: str
    categorie: str | None
    prix_vente: float
    prix_achat: float | None
    stock_actuel: float | None
    tva: float | None

class CatalogRepository(Protocol):
    def list_active_products(self, tenant_id: int) -> list[ProductSummary]:
        ...

    def find_product(self, identifier: str | int, tenant_id: int) -> ProductSummary | None:
        ...
