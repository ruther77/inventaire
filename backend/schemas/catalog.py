from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BarcodeList(BaseModel):
    codes: List[str] = Field(default_factory=list)


class ProductBase(BaseModel):
    nom: str = Field(..., min_length=1, max_length=255)
    prix_achat: float = Field(0, ge=0)
    prix_vente: float = Field(0, ge=0)
    tva: float = Field(0, ge=0)
    categorie: Optional[str] = Field(default=None, max_length=120)
    seuil_alerte: float = Field(0, ge=0)
    actif: bool = True


class ProductCreate(ProductBase):
    stock_actuel: float = Field(0, ge=0)
    codes: List[str] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=255)
    prix_achat: Optional[float] = Field(default=None, ge=0)
    prix_vente: Optional[float] = Field(default=None, ge=0)
    tva: Optional[float] = Field(default=None, ge=0)
    categorie: Optional[str] = Field(default=None, max_length=120)
    seuil_alerte: Optional[float] = Field(default=None, ge=0)
    stock_actuel: Optional[float] = Field(default=None, ge=0)
    actif: Optional[bool] = None
    codes: Optional[List[str]] = None


class ProductOut(ProductBase):
    id: int
    stock_actuel: float = 0
    codes: List[str] = Field(default_factory=list)
    status: str = Field('ok')

    model_config = dict(from_attributes=True)


class PagingMeta(BaseModel):
    page: int
    per_page: int
    total: int


class ProductPage(BaseModel):
    items: List[ProductOut]
    meta: PagingMeta
