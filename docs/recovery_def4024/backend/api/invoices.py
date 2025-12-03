"""Invoice ingestion endpoints."""

from __future__ import annotations

import io
import logging
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.schemas.invoices import (
    InvoiceCatalogImportRequest,
    InvoiceCatalogImportSummary,
    InvoiceExtractDocument,
    InvoiceExtractRequest,
    InvoiceExtractResponse,
    InvoiceHistoryEntry,
    InvoiceHistoryResponse,
    InvoiceImportRequest,
    InvoiceImportSummary,
    InvoiceLine,
)
from backend.services import invoices as invoices_service
from core.invoice_extractor import extract_text_from_file
from backend.dependencies.tenant import Tenant, get_current_tenant

try:  # pragma: no cover
    import python_multipart  # type: ignore  # noqa: F401

    MULTIPART_AVAILABLE = True
except ImportError:  # pragma: no cover
    MULTIPART_AVAILABLE = False

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/invoices", tags=["invoices"])

EXPORTED_COLUMNS = [
    "nom",
    "codes",
    "numero_article",
    "qte_init",
    "quantite_recue",
    "prix_achat",
    "prix_vente",
    "tva",
    "tva_code",
    "produit_id",
    "catalogue_id",
    "catalogue_nom",
    "catalogue_categorie",
    "facture_date",
    "invoice_id",
]
TEXT_COLUMNS = {"nom", "codes", "numero_article", "catalogue_nom", "catalogue_categorie", "facture_date", "invoice_id"}


def _ensure_valid_invoice_lines(lines: list[InvoiceLine], tenant_id: int | None = None) -> None:
    errors = []
    invoice_ids: set[str] = set()
    for idx, line in enumerate(lines, start=1):
        quantite = line.quantite_recue or line.qte_init
        if quantite is None or quantite <= 0:
            errors.append(f"Ligne {idx}: quantité requise > 0.")
        if line.prix_achat < 0:
            errors.append(f"Ligne {idx}: prix d'achat négatif signalé.")
        invoice_id = (line.invoice_id or "").strip() if hasattr(line, "invoice_id") else ""
        if not invoice_id:
            errors.append(f"Ligne {idx}: identifiant facture manquant (invoice_id).")
        else:
            invoice_ids.add(invoice_id)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))
    if tenant_id and invoice_ids:
        duplicates = invoices_service.find_processed_invoice_ids(invoice_ids, tenant_id=tenant_id)
        if duplicates:
            formatted = ", ".join(sorted(duplicates))
            raise HTTPException(
                status_code=400,
                detail=f"Les factures suivantes ont déjà été traitées: {formatted}",
            )


def _serialize_minimal(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []

    working = df.copy()
    for column in EXPORTED_COLUMNS:
        if column not in working.columns:
            if column in TEXT_COLUMNS:
                working[column] = ""
            else:
                working[column] = 0

    working = working[EXPORTED_COLUMNS]
    for column in TEXT_COLUMNS:
        working[column] = working[column].fillna("")

    numeric_columns = [col for col in EXPORTED_COLUMNS if col not in TEXT_COLUMNS]
    for column in numeric_columns:
        working[column] = pd.to_numeric(working[column], errors="coerce").fillna(0)

    return working.to_dict(orient="records")


def _group_items_by_invoice(
    items: list[dict[str, Any]],
    attachments: dict[str, dict[str, str]] | None = None,
) -> list[InvoiceExtractDocument]:
    if not items:
        return []

    grouped: dict[str, dict[str, Any]] = {}
    fallback_counter = 0

    for item in items:
        raw_invoice_id = str(item.get("invoice_id") or "").strip()
        if not raw_invoice_id:
            fallback_counter += 1
            raw_invoice_id = f"INV-{fallback_counter:03d}"
            item["invoice_id"] = raw_invoice_id
        bucket = grouped.setdefault(
            raw_invoice_id,
            {"invoice_id": raw_invoice_id, "facture_date": item.get("facture_date"), "items": []},
        )
        if not bucket.get("facture_date") and item.get("facture_date"):
            bucket["facture_date"] = item["facture_date"]
        bucket["items"].append(item)

    documents: list[InvoiceExtractDocument] = []
    for data in grouped.values():
        attachment = (attachments or {}).get(data["invoice_id"]) or {}
        documents.append(
            InvoiceExtractDocument(
                invoice_id=data["invoice_id"],
                facture_date=data.get("facture_date"),
                line_count=len(data["items"]),
                 pdf_path=attachment.get("file_path"),
                items=data["items"],
            )
        )

    documents.sort(key=lambda doc: doc.invoice_id)
    return documents


@router.post("/extract", response_model=InvoiceExtractResponse)
def extract_invoice(payload: InvoiceExtractRequest, tenant: Tenant = Depends(get_current_tenant)):
    try:
        lines_df = invoices_service.extract_invoice_lines(
            payload.text,
            margin_percent=payload.margin_percent,
            supplier_hint=payload.supplier_hint,
        )
        enriched = invoices_service.enrich_lines_with_catalog(
            lines_df,
            margin_percent=payload.margin_percent,
            tenant_id=tenant.id,
        )
        items = _serialize_minimal(enriched)
        documents = _group_items_by_invoice(items)
        return InvoiceExtractResponse(items=items, documents=documents)
    except Exception as exc:  # pragma: no cover - fallback runtime
        LOGGER.exception("Invoice text extraction failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if MULTIPART_AVAILABLE:

    @router.post("/extract/file", response_model=InvoiceExtractResponse)
    async def extract_invoice_from_file(
        file: UploadFile = File(...),
        margin_percent: float = Form(40.0),
        supplier_hint: str | None = Form(default=None),
        tenant: Tenant = Depends(get_current_tenant),
    ):
        try:
            content = await file.read()
            buffer = io.BytesIO(content)
            buffer.name = file.filename  # type: ignore[attr-defined]
            text = extract_text_from_file(buffer)
            stored_docs = invoices_service.persist_invoice_documents(
                content,
                tenant_id=tenant.id,
                supplier=supplier_hint or tenant.name,
            )
            lines_df = invoices_service.extract_invoice_lines(
                text,
                margin_percent=margin_percent,
                supplier_hint=supplier_hint,
            )
            enriched = invoices_service.enrich_lines_with_catalog(
                lines_df,
                margin_percent=margin_percent,
                tenant_id=tenant.id,
            )
            items = _serialize_minimal(enriched)
            documents = _group_items_by_invoice(items, attachments=stored_docs)
            return InvoiceExtractResponse(items=items, documents=documents)
        except Exception as exc:
            LOGGER.exception("Invoice file extraction failed: %s", file.filename)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
else:  # pragma: no cover - optional route
    LOGGER.warning("python-multipart non installé : /invoices/extract/file désactivé.")


@router.post("/import", response_model=InvoiceImportSummary)
def import_invoice(payload: InvoiceImportRequest, tenant: Tenant = Depends(get_current_tenant)):
    if not payload.lines:
        raise HTTPException(status_code=400, detail="Aucune ligne fournie.")

    _ensure_valid_invoice_lines(payload.lines, tenant_id=tenant.id)

    df = pd.DataFrame([line.model_dump() for line in payload.lines])
    try:
        summary = invoices_service.apply_invoice_import(
            df,
            username=payload.username or "api_user",
            supplier=payload.supplier,
            movement_type=payload.movement_type,
            invoice_date=payload.invoice_date,
            tenant_id=tenant.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return InvoiceImportSummary(**summary)


@router.post("/catalog/import", response_model=InvoiceCatalogImportSummary)
def import_catalog(payload: InvoiceCatalogImportRequest, tenant: Tenant = Depends(get_current_tenant)):
    if not payload.lines:
        raise HTTPException(status_code=400, detail="Aucune ligne fournie.")

    _ensure_valid_invoice_lines(payload.lines, tenant_id=tenant.id)

    df = pd.DataFrame([line.model_dump() for line in payload.lines])
    try:
        summary = invoices_service.import_catalog_from_invoice(
            df,
            supplier=payload.supplier,
            initialize_stock=payload.initialize_stock,
            invoice_date=payload.invoice_date,
            tenant_id=tenant.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return InvoiceCatalogImportSummary(**summary)
@router.get("/history", response_model=InvoiceHistoryResponse)
def get_invoice_history(
    supplier: str | None = None,
    invoice_id: str | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    limit: int = 100,
    tenant: Tenant = Depends(get_current_tenant),
):
    entries = invoices_service.list_processed_invoices(
        tenant_id=tenant.id,
        supplier=supplier,
        invoice_id=invoice_id,
        date_start=date_start,
        date_end=date_end,
        limit=limit,
    )
    return InvoiceHistoryResponse(
        items=[InvoiceHistoryEntry(**entry) for entry in entries],
    )


@router.get("/history/{invoice_id}/file")
def download_invoice_file(invoice_id: str, tenant: Tenant = Depends(get_current_tenant)):
    path = invoices_service.get_processed_invoice_file(tenant_id=tenant.id, invoice_id=invoice_id)
    if not path:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    return FileResponse(path, filename=path.name)
