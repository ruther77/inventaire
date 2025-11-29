"""Pydantic schemas for invoice extraction/import endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class InvoiceExtractRequest(BaseModel):
    text: str
    margin_percent: float = Field(default=40.0, ge=0, le=400)
    supplier_hint: Optional[str] = None


class InvoiceLine(BaseModel):
    nom: str
    codes: Optional[str] = None
    numero_article: Optional[str] = None
    qte_init: float = 0
    quantite_recue: float = 0
    prix_achat: float = 0
    prix_vente: float = 0
    tva: float = 0
    produit_id: Optional[int] = None
    catalogue_id: Optional[int] = None
    catalogue_nom: Optional[str] = None
    catalogue_categorie: Optional[str] = None
    facture_date: Optional[str] = None
    invoice_id: Optional[str] = None


class InvoiceExtractDocument(BaseModel):
    invoice_id: str
    facture_date: Optional[str] = None
    line_count: int
    items: List[InvoiceLine]
    pdf_path: Optional[str] = None


class InvoiceExtractResponse(BaseModel):
    items: List[InvoiceLine]
    documents: List[InvoiceExtractDocument] = Field(default_factory=list)


class InvoiceHistoryEntry(BaseModel):
    invoice_id: str
    supplier: Optional[str] = None
    facture_date: Optional[str] = None
    line_count: int
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class InvoiceHistoryResponse(BaseModel):
    items: List[InvoiceHistoryEntry]


class InvoiceImportRequest(BaseModel):
    lines: List[InvoiceLine]
    supplier: Optional[str] = None
    movement_type: str = Field(default="ENTREE")
    reception_date: Optional[date] = None
    invoice_date: Optional[date] = None
    username: Optional[str] = None


class InvoiceImportSummary(BaseModel):
    rows_received: int
    movements_created: int
    quantity_total: float
    errors: List[str]


class BarcodeSummary(BaseModel):
    added: int
    conflicts: int
    skipped: int


class InvoiceCatalogImportRequest(BaseModel):
    lines: List[InvoiceLine]
    supplier: Optional[str] = None
    username: Optional[str] = None
    initialize_stock: bool = Field(default=False, description="Créer les mouvements de stock associés.")
    invoice_date: Optional[date] = None


class InvoiceCatalogImportSummary(BaseModel):
    rows_received: int
    rows_processed: int
    created: int
    updated: int
    stock_initialized: int
    barcode: BarcodeSummary
    errors: List[str]
    rejected_rows: List[dict[str, Any]]
    rejected_csv: Optional[str]


__all__ = [
    "InvoiceExtractRequest",
    "InvoiceExtractResponse",
    "InvoiceExtractDocument",
    "InvoiceLine",
    "InvoiceImportRequest",
    "InvoiceImportSummary",
    "InvoiceCatalogImportRequest",
    "InvoiceCatalogImportSummary",
]
