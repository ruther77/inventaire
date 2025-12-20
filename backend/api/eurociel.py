"""Endpoints d'import de factures Eurociel."""

from __future__ import annotations

import io
import logging
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from backend.dependencies.tenant import Tenant, get_current_tenant
from backend.services import invoices as invoices_service
from core.invoice_extractor import extract_text_from_file

try:
    import python_multipart  # noqa: F401
    MULTIPART_AVAILABLE = True
except ImportError:
    MULTIPART_AVAILABLE = False

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/eurociel", tags=["eurociel"])


@router.post("/import")
async def import_eurociel_invoice(
    file: UploadFile = File(...),
    margin_percent: float = Form(40.0),
    initialize_stock: bool = Form(False),
    tenant: Tenant = Depends(get_current_tenant),
) -> dict[str, Any]:
    """
    Import direct d'une facture Eurociel : extraction + import catalogue en une seule étape.

    - Extrait les lignes produits du PDF
    - Crée/met à jour les produits dans le catalogue
    - Optionnellement initialise le stock avec les quantités détectées
    """
    if not MULTIPART_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Upload de fichiers non disponible (python-multipart manquant)",
        )

    try:
        content = await file.read()
        buffer = io.BytesIO(content)
        buffer.name = file.filename

        # 1. Extraction du texte depuis le PDF
        text = extract_text_from_file(buffer)
        if not text.strip():
            raise HTTPException(status_code=400, detail="Impossible d'extraire le texte du fichier")

        # 2. Stockage du PDF original
        stored_docs = invoices_service.persist_invoice_documents(
            content,
            tenant_id=tenant.id,
            supplier="Eurociel",
        )

        # 3. Extraction des lignes produits
        lines_df = invoices_service.extract_invoice_lines(
            text,
            margin_percent=margin_percent,
            supplier_hint="Eurociel",
        )

        if lines_df.empty:
            return {
                "success": True,
                "message": "Aucun produit détecté dans la facture",
                "rows_processed": 0,
                "created": 0,
                "updated": 0,
                "stock_initialized": 0,
                "documents_stored": len(stored_docs),
            }

        # 4. Enrichissement avec le catalogue existant
        enriched_df = invoices_service.enrich_lines_with_catalog(
            lines_df,
            margin_percent=margin_percent,
            tenant_id=tenant.id,
        )

        # 5. Import dans le catalogue
        summary = invoices_service.import_catalog_from_invoice(
            enriched_df,
            supplier="Eurociel",
            initialize_stock=initialize_stock,
            invoice_date=None,  # sera extrait du PDF si disponible
            tenant_id=tenant.id,
        )

        return {
            "success": True,
            "message": f"Import Eurociel terminé: {summary.get('created', 0)} créés, {summary.get('updated', 0)} mis à jour",
            "rows_processed": summary.get("rows_processed", 0),
            "created": summary.get("created", 0),
            "updated": summary.get("updated", 0),
            "stock_initialized": summary.get("stock_initialized", 0),
            "barcode": summary.get("barcode", {}),
            "errors": summary.get("errors", []),
            "documents_stored": len(stored_docs),
        }

    except HTTPException:
        raise
    except Exception as exc:
        LOGGER.exception("Eurociel import failed: %s", file.filename)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/status")
def eurociel_status(tenant: Tenant = Depends(get_current_tenant)) -> dict[str, Any]:
    """Retourne le statut des imports Eurociel pour ce tenant."""

    entries = invoices_service.list_processed_invoices(
        tenant_id=tenant.id,
        supplier="Eurociel",
        limit=50,
    )

    return {
        "total_invoices": len(entries),
        "recent_imports": entries[:10],
    }
