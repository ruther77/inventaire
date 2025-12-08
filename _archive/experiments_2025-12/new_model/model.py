from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, List, Optional, Sequence


@dataclass
class Tenant:
    id: int
    code: str
    name: str


@dataclass
class Produit:
    id: int
    tenant: Tenant
    nom: str
    categorie: Optional[str]
    prix_achat: Decimal
    prix_vente: Decimal
    tva: Decimal
    stock_actuel: Decimal
    seuil_alerte: Decimal
    actif: bool = True


@dataclass
class ProductBarcode:
    code: str
    produit: Produit
    is_principal: bool = False


@dataclass
class RestaurantIngredient:
    id: int
    tenant: Tenant
    nom: str
    unite_base: str
    cout_unitaire: Decimal
    stock_actuel: Decimal


@dataclass
class RestaurantPlat:
    id: int
    tenant: Tenant
    nom: str
    categorie: Optional[str]
    prix_vente_ttc: Decimal
    actif: bool
    ingredients: Sequence[RestaurantIngredient] = field(default_factory=list)


@dataclass
class InvoiceLine:
    codes: str
    nom: str
    quantite_recue: Decimal
    prix_achat: Decimal
    tva: Decimal
    supplier: Optional[str]
    facture_date: date
    tenant: Tenant


@dataclass
class PriceHistoryEntry:
    code: str
    tenant: Tenant
    prix_achat: Decimal
    fournisseur: Optional[str]
    quantite: Decimal
    facture_date: date
    created_at: datetime


@dataclass
class CapitalSnapshot:
    tenant: Tenant
    snapshot_date: datetime
    stock_value: Decimal
    bank_balance: Decimal
    cash_balance: Decimal
    total_assets: Decimal


def aggregate_stock_value(produits: Iterable[Produit]) -> Decimal:
    return sum(
        (p.prix_achat if p.prix_vente <= 0 else p.prix_vente) * p.stock_actuel
        for p in produits
    )
