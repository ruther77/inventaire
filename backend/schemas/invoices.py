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
    file_hash: Optional[str] = None  # SHA-256 hash for duplicate prevention


class InvoiceExtractResponse(BaseModel):
    items: List[InvoiceLine]
    documents: List[InvoiceExtractDocument] = Field(default_factory=list)


class InvoiceHistoryEntry(BaseModel):
    invoice_id: str
    supplier: Optional[str] = None
    facture_date: Optional[str] = None
    line_count: int
    total_ttc: Optional[float] = None
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Champs calculés pour le frontend (alias)
    reference: Optional[str] = None
    fournisseur: Optional[str] = None
    montant: Optional[float] = None
    total: Optional[float] = None
    status: str = "pending"
    id: Optional[str] = None

    model_config = {
        "from_attributes": True,
    }

    def model_post_init(self, __context):
        """Initialise les champs alias après création."""
        if self.reference is None:
            object.__setattr__(self, 'reference', self.invoice_id)
        if self.id is None:
            object.__setattr__(self, 'id', self.invoice_id)
        if self.fournisseur is None:
            object.__setattr__(self, 'fournisseur', self.supplier)
        if self.montant is None:
            object.__setattr__(self, 'montant', self.total_ttc)
        if self.total is None:
            object.__setattr__(self, 'total', self.total_ttc)
        if self.status == "pending":
            object.__setattr__(self, 'status', "processed" if self.line_count > 0 else "pending")


class InvoiceHistoryResponse(BaseModel):
    items: List[InvoiceHistoryEntry]


class InvoiceImportRequest(BaseModel):
    lines: List[InvoiceLine]
    supplier: Optional[str] = None
    movement_type: str = Field(default="ENTREE")
    reception_date: Optional[date] = None
    invoice_date: Optional[date] = None
    username: Optional[str] = None
    file_hash: Optional[str] = None  # SHA-256 hash for duplicate prevention


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


# === LIGNES (liaison / création produit / validation stock) ===


class InvoiceLineLinkRequest(BaseModel):
    line: InvoiceLine
    product_id: int


class InvoiceLineLinkResponse(BaseModel):
    line: InvoiceLine


class InvoiceLineCreateProductRequest(BaseModel):
    line: InvoiceLine
    supplier: Optional[str] = None
    initialize_stock: bool = Field(default=False)
    invoice_date: Optional[date] = None


class InvoiceLineCreateProductResponse(BaseModel):
    summary: InvoiceCatalogImportSummary


class InvoiceStockConfirmRequest(BaseModel):
    lines: List[InvoiceLine]
    movement_type: str = Field(default="ENTREE")
    supplier: Optional[str] = None
    invoice_date: Optional[date] = None
    username: Optional[str] = None


class ZeroClickJobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    filename: Optional[str] = None
    supplier_hint: Optional[str] = None
    margin_percent: float = 40.0
    auto_confirm: bool = True
    summary: Optional[InvoiceImportSummary] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ZeroClickJobListResponse(BaseModel):
    items: List[ZeroClickJobStatus]
    total: int


class ImportSession(BaseModel):
    session_id: str
    date_debut: datetime
    date_fin: Optional[datetime] = None
    nb_imports: int
    nb_completed: int = 0
    nb_failed: int = 0
    total_lignes: int = 0
    total_mouvements: int = 0
    total_produits_crees: int = 0
    fournisseurs: Optional[str] = None


class ImportSessionListResponse(BaseModel):
    items: List[ImportSession]
    total: int


class ImportSessionDetails(BaseModel):
    session_id: str
    date_debut: datetime
    date_fin: Optional[datetime] = None
    nb_imports: int
    nb_completed: int = 0
    nb_failed: int = 0
    nb_pending: int = 0
    total_lignes: int = 0
    total_mouvements: int = 0
    total_produits_crees: int = 0
    fournisseurs: List[str] = Field(default_factory=list)
    imports: List[ZeroClickJobStatus] = Field(default_factory=list)


__all__ = [
    "InvoiceExtractRequest",
    "InvoiceExtractResponse",
    "InvoiceExtractDocument",
    "InvoiceLine",
    "InvoiceImportRequest",
    "InvoiceImportSummary",
    "InvoiceCatalogImportRequest",
    "InvoiceCatalogImportSummary",
    "InvoiceLineLinkRequest",
    "InvoiceLineLinkResponse",
    "InvoiceLineCreateProductRequest",
    "InvoiceLineCreateProductResponse",
    "InvoiceStockConfirmRequest",
    "ZeroClickJobStatus",
    "ZeroClickJobListResponse",
    "ImportSession",
    "ImportSessionListResponse",
    "ImportSessionDetails",
]
