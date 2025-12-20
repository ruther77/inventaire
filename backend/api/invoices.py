"""Endpoints d'ingestion de factures."""

from __future__ import annotations

import io
import logging
import uuid
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.schemas.invoices import (
    ImportSession,
    ImportSessionDetails,
    ImportSessionListResponse,
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
    InvoiceLineCreateProductRequest,
    InvoiceLineCreateProductResponse,
    InvoiceLineLinkRequest,
    InvoiceLineLinkResponse,
    InvoiceStockConfirmRequest,
    ZeroClickJobListResponse,
    ZeroClickJobStatus,
)
from backend.services import invoices as invoices_service
from backend.services import zero_click_jobs as job_service
from backend.services import product_matching
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
    # Colonnes d'anomalie de prix
    "is_anomaly",
    "price_anomaly",
    "price_anomaly_pct",
    "price_anomaly_description",
    "last_price",
    "suggestion",
    # Colonnes de suggestion IA pour produits non-matchés
    "has_suggestion",
    "suggestion_id",
    "suggestion_nom",
    "suggestion_score",
    "suggestion_type",
]
TEXT_COLUMNS = {
    "nom", "codes", "numero_article", "catalogue_nom", "catalogue_categorie",
    "facture_date", "invoice_id", "price_anomaly", "price_anomaly_description",
    "suggestion", "suggestion_nom", "suggestion_type"
}
BOOL_COLUMNS = {"is_anomaly", "has_suggestion"}


def _ensure_valid_invoice_lines(
    lines: list[InvoiceLine],
    tenant_id: int | None = None,
    require_invoice_id: bool = True,
) -> None:
    errors = []
    invoice_ids: set[str] = set()
    for idx, line in enumerate(lines, start=1):
        quantite = line.quantite_recue or line.qte_init
        if quantite is None or quantite <= 0:
            errors.append(f"Ligne {idx}: quantité requise > 0.")
        if line.prix_achat < 0:
            errors.append(f"Ligne {idx}: prix d'achat négatif signalé.")
        invoice_id = (line.invoice_id or "").strip() if hasattr(line, "invoice_id") else ""
        if require_invoice_id and not invoice_id:
            errors.append(f"Ligne {idx}: identifiant facture manquant (invoice_id).")
        elif invoice_id:
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
            elif column in BOOL_COLUMNS:
                working[column] = False
            else:
                working[column] = 0

    working = working[EXPORTED_COLUMNS]

    # Traiter les colonnes texte
    for column in TEXT_COLUMNS:
        working[column] = working[column].fillna("")

    # Traiter les colonnes booléennes
    for column in BOOL_COLUMNS:
        working[column] = working[column].fillna(False).astype(bool)

    # Traiter les colonnes numériques (tout sauf texte et bool)
    numeric_columns = [col for col in EXPORTED_COLUMNS if col not in TEXT_COLUMNS and col not in BOOL_COLUMNS]
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


def _process_zero_click_bytes(
    *,
    file_bytes: bytes,
    filename: str,
    margin_percent: float,
    supplier_hint: str | None,
    auto_confirm: bool,
    tenant: Tenant,
) -> InvoiceImportSummary | dict[str, Any]:
    buffer = io.BytesIO(file_bytes)
    buffer.name = filename  # type: ignore[attr-defined]

    # 1. Extraction du texte
    text = extract_text_from_file(buffer)

    # 2. Stockage du document source
    invoices_service.persist_invoice_documents(
        file_bytes,
        tenant_id=tenant.id,
        supplier=supplier_hint or tenant.name,
    )

    # 3. Extraction des lignes
    lines_df = invoices_service.extract_invoice_lines(
        text,
        margin_percent=margin_percent,
        supplier_hint=supplier_hint,
        tenant_id=tenant.id,
    )

    if lines_df.empty:
        raise HTTPException(status_code=400, detail="Aucune ligne extraite du PDF")

    # 4. Enrichissement avec le catalogue (MATCHING AUTOMATIQUE)
    enriched = invoices_service.enrich_lines_with_catalog(
        lines_df,
        margin_percent=margin_percent,
        tenant_id=tenant.id,
    )

    # 4b. CRÉATION AUTOMATIQUE DES PRODUITS MANQUANTS
    unmatched_lines = enriched[enriched["produit_id"].isna()].copy()
    products_created = 0
    if not unmatched_lines.empty and auto_confirm:
        LOGGER.info(f"Création automatique de {len(unmatched_lines)} produits manquants")
        try:
            catalog_summary = invoices_service.import_catalog_from_invoice(
                unmatched_lines,
                supplier=supplier_hint or "Import",
                initialize_stock=False,  # Le stock sera mis à jour dans apply_invoice_import
                invoice_date=None,
                tenant_id=tenant.id,
            )
            products_created = catalog_summary.get("created", 0)

            # Re-enrichir pour récupérer les nouveaux produit_id
            enriched = invoices_service.enrich_lines_with_catalog(
                lines_df,
                margin_percent=margin_percent,
                tenant_id=tenant.id,
            )
            LOGGER.info(f"✅ {products_created} produits créés automatiquement")
        except Exception as create_exc:
            LOGGER.warning(f"Échec création auto produits: {create_exc}")

    # 5. Analyse de qualité (optionnel)
    quality_report = None
    try:
        from core.import_analyzer import analyze_invoice_import

        quality_report = analyze_invoice_import(enriched, filename or "upload")
    except Exception:
        quality_report = None

    if auto_confirm:
        # Déterminer le fournisseur depuis le hint ou le nom de fichier
        supplier = supplier_hint or "Import"
        if not supplier_hint and filename:
            filename_upper = (filename or "").upper()
            if "METRO" in filename_upper:
                supplier = "METRO"
            elif "EUROCIEL" in filename_upper:
                supplier = "EUROCIEL"
            elif "TAIYAT" in filename_upper or "TAI" in filename_upper:
                supplier = "TAIYAT"

        # 6. APPLICATION AUTOMATIQUE (MISE À JOUR STOCK)
        summary = invoices_service.apply_invoice_import(
            enriched,
            username="zero_click",
            supplier=supplier,
            movement_type="ENTREE",
            invoice_date=None,  # Sera inféré
            tenant_id=tenant.id,
        )

        # Ajouter le nombre de produits créés
        summary["products_created"] = products_created

        # 7. Synchroniser vers fact_invoices
        try:
            from core.consolidation_loader import sync_invoice_dataframe

            invoice_ref = (
                enriched["invoice_id"].iloc[0]
                if "invoice_id" in enriched.columns and not enriched.empty
                else None
            )
            sync_result = sync_invoice_dataframe(
                enriched,
                tenant_id=tenant.id,
                supplier_name=supplier,
                invoice_reference=invoice_ref,
                analyze=False,  # Déjà fait ci-dessus
            )
            summary["fact_invoices_lines"] = sync_result.get("lines_inserted", 0)
        except Exception as sync_exc:
            LOGGER.warning("Sync fact_invoices échoué: %s", sync_exc)
            summary["fact_invoices_lines"] = 0

        # Ajouter le rapport de qualité
        if quality_report:
            summary["quality_score"] = quality_report.quality_score
            summary["quality_flags"] = quality_report.quality_flags

        return InvoiceImportSummary(**summary)

    # Mode preview : renvoyer les items
    items = _serialize_minimal(enriched)
    return {
        "mode": "preview",
        "line_count": len(items),
        "items": items,
        "quality_score": quality_report.quality_score if quality_report else None,
    }


@router.post("/extract", response_model=InvoiceExtractResponse)
def extract_invoice(payload: InvoiceExtractRequest, tenant: Tenant = Depends(get_current_tenant)):
    try:
        lines_df = invoices_service.extract_invoice_lines(
            payload.text,
            margin_percent=payload.margin_percent,
            supplier_hint=payload.supplier_hint,
            tenant_id=tenant.id,
        )
        enriched = invoices_service.enrich_lines_with_catalog(
            lines_df,
            margin_percent=payload.margin_percent,
            tenant_id=tenant.id,
        )
        items = _serialize_minimal(enriched)
        documents = _group_items_by_invoice(items)
        return InvoiceExtractResponse(items=items, documents=documents)
    except Exception as exc:  # pragma: no cover - repli à l'exécution
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
                tenant_id=tenant.id,
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

    # Pour l'import catalogue, invoice_id n'est pas obligatoire
    _ensure_valid_invoice_lines(payload.lines, tenant_id=tenant.id, require_invoice_id=False)

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


@router.post("/lines/link", response_model=InvoiceLineLinkResponse)
def link_invoice_line(payload: InvoiceLineLinkRequest, tenant: Tenant = Depends(get_current_tenant)):
    """Associe une ligne extraite à un produit existant et renvoie la ligne enrichie."""
    df = pd.DataFrame([payload.line.model_dump()])
    df["produit_id"] = payload.product_id
    enriched = invoices_service.enrich_lines_with_catalog(df, margin_percent=40.0, tenant_id=tenant.id)
    if enriched.empty:
        raise HTTPException(status_code=400, detail="Ligne invalide")
    line_dict = enriched.iloc[0].to_dict()
    return InvoiceLineLinkResponse(line=InvoiceLine.model_validate(line_dict))


@router.post("/lines/create-product", response_model=InvoiceLineCreateProductResponse)
def create_product_from_line(payload: InvoiceLineCreateProductRequest, tenant: Tenant = Depends(get_current_tenant)):
    """Crée un produit à partir d'une ligne de facture, optionnellement avec stock initial."""
    df = pd.DataFrame([payload.line.model_dump()])
    summary = invoices_service.import_catalog_from_invoice(
        df,
        supplier=payload.supplier,
        initialize_stock=payload.initialize_stock,
        invoice_date=payload.invoice_date,
        tenant_id=tenant.id,
    )
    return InvoiceLineCreateProductResponse(summary=InvoiceCatalogImportSummary(**summary))


@router.post("/lines/confirm-stock", response_model=InvoiceImportSummary)
def confirm_invoice_stock(payload: InvoiceStockConfirmRequest, tenant: Tenant = Depends(get_current_tenant)):
    """Valide les mouvements de stock pour des lignes sélectionnées."""
    if not payload.lines:
        raise HTTPException(status_code=400, detail="Aucune ligne fournie.")

    _ensure_valid_invoice_lines(payload.lines, tenant_id=tenant.id, require_invoice_id=False)
    df = pd.DataFrame([line.model_dump() for line in payload.lines])
    summary = invoices_service.apply_invoice_import(
        df,
        username=payload.username or "ui",
        supplier=payload.supplier,
        movement_type=payload.movement_type,
        invoice_date=payload.invoice_date,
        tenant_id=tenant.id,
    )
    return InvoiceImportSummary(**summary)
if MULTIPART_AVAILABLE:

    @router.post("/zero-click", response_model=InvoiceImportSummary)
    async def zero_click_import(
        file: UploadFile = File(...),
        margin_percent: float = Form(40.0),
        supplier_hint: str | None = Form(default=None),
        auto_confirm: bool = Form(default=True),
        tenant: Tenant = Depends(get_current_tenant),
    ):
        try:
            content = await file.read()
            return _process_zero_click_bytes(
                file_bytes=content,
                filename=file.filename or "upload",
                margin_percent=margin_percent,
                supplier_hint=supplier_hint,
                auto_confirm=auto_confirm,
                tenant=tenant,
            )
        except HTTPException:
            raise
        except Exception as exc:
            LOGGER.exception("Zero-click import failed: %s", file.filename)
            raise HTTPException(status_code=400, detail=str(exc)) from exc


    @router.post("/zero-click/jobs", response_model=ZeroClickJobStatus)
    async def zero_click_job(
        file: UploadFile = File(...),
        margin_percent: float = Form(40.0),
        supplier_hint: str | None = Form(default=None),
        auto_confirm: bool = Form(default=True),
        session_id: str | None = Form(default=None),
        tenant: Tenant = Depends(get_current_tenant),
    ):
        """Lance un job zero-click async et retourne immédiatement le job_id pour polling."""
        job_id = str(uuid.uuid4())

        # Créer le job en base avec statut "pending"
        try:
            job_service.create_job(
                job_id=job_id,
                tenant_id=tenant.id,
                filename=file.filename,
                supplier_hint=supplier_hint,
                margin_percent=margin_percent,
                auto_confirm=auto_confirm,
                session_id=session_id,
            )
        except Exception as exc:
            LOGGER.exception("Échec de création du job %s", job_id)
            raise HTTPException(status_code=500, detail=f"Échec de création du job: {exc}") from exc

        # Marquer le job comme "processing"
        job_service.update_job_status(job_id, "processing")

        # Traiter le fichier de manière synchrone (pour cette version)
        # Dans une vraie implémentation async, on utiliserait Celery/RQ/Background Tasks
        try:
            content = await file.read()
            result = _process_zero_click_bytes(
                file_bytes=content,
                filename=file.filename or "upload",
                margin_percent=margin_percent,
                supplier_hint=supplier_hint,
                auto_confirm=auto_confirm,
                tenant=tenant,
            )

            # Convertir le résultat en dict pour le stockage JSON
            if isinstance(result, InvoiceImportSummary):
                result_dict = result.model_dump()
            else:
                result_dict = result

            # Mettre à jour le job avec le résultat
            job_service.update_job_status(job_id, "completed", result=result_dict)

            # Récupérer et retourner le job complet
            job_data = job_service.get_job(job_id, tenant_id=tenant.id)
            if not job_data:
                raise HTTPException(status_code=404, detail="Job introuvable après traitement")

            # Reconstruire le summary depuis result
            summary = None
            if job_data.get("result"):
                summary = InvoiceImportSummary(**job_data["result"])

            return ZeroClickJobStatus(
                job_id=job_data["job_id"],
                status=job_data["status"],
                filename=job_data.get("filename"),
                supplier_hint=job_data.get("supplier_hint"),
                margin_percent=job_data.get("margin_percent", 40.0),
                auto_confirm=job_data.get("auto_confirm", True),
                summary=summary,
                error=job_data.get("error"),
                created_at=job_data.get("created_at"),
                updated_at=job_data.get("updated_at"),
                completed_at=job_data.get("completed_at"),
            )

        except HTTPException as exc:
            job_service.update_job_status(job_id, "failed", error=str(exc.detail))
            raise
        except Exception as exc:  # pragma: no cover - runtime
            LOGGER.exception("Zero-click job failed: %s", file.filename)
            job_service.update_job_status(job_id, "failed", error=str(exc))
            raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/zero-click/jobs", response_model=ZeroClickJobListResponse)
def list_zero_click_jobs(
    status: str | None = None,
    session_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    tenant: Tenant = Depends(get_current_tenant),
):
    """Liste les jobs zero-click récents pour le tenant courant."""
    jobs_data, total = job_service.list_jobs(
        tenant_id=tenant.id,
        status=status,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )

    items = []
    for job_data in jobs_data:
        # Reconstruire le summary depuis result si disponible
        summary = None
        if job_data.get("result"):
            try:
                summary = InvoiceImportSummary(**job_data["result"])
            except Exception as exc:
                LOGGER.warning("Impossible de reconstruire le summary pour job %s: %s", job_data["job_id"], exc)

        items.append(
            ZeroClickJobStatus(
                job_id=job_data["job_id"],
                status=job_data["status"],
                filename=job_data.get("filename"),
                supplier_hint=job_data.get("supplier_hint"),
                margin_percent=job_data.get("margin_percent", 40.0),
                auto_confirm=job_data.get("auto_confirm", True),
                summary=summary,
                error=job_data.get("error"),
                created_at=job_data.get("created_at"),
                updated_at=job_data.get("updated_at"),
                completed_at=job_data.get("completed_at"),
            )
        )

    return ZeroClickJobListResponse(items=items, total=total)


@router.get("/zero-click/jobs/{job_id}", response_model=ZeroClickJobStatus)
def get_zero_click_job(job_id: str, tenant: Tenant = Depends(get_current_tenant)):
    """Récupère le statut d'un job zero-click par son ID."""
    job_data = job_service.get_job(job_id, tenant_id=tenant.id)

    if not job_data:
        raise HTTPException(status_code=404, detail="Job introuvable")

    # Reconstruire le summary depuis result si disponible
    summary = None
    if job_data.get("result"):
        try:
            summary = InvoiceImportSummary(**job_data["result"])
        except Exception as exc:
            LOGGER.warning("Impossible de reconstruire le summary pour job %s: %s", job_id, exc)

    return ZeroClickJobStatus(
        job_id=job_data["job_id"],
        status=job_data["status"],
        filename=job_data.get("filename"),
        supplier_hint=job_data.get("supplier_hint"),
        margin_percent=job_data.get("margin_percent", 40.0),
        auto_confirm=job_data.get("auto_confirm", True),
        summary=summary,
        error=job_data.get("error"),
        created_at=job_data.get("created_at"),
        updated_at=job_data.get("updated_at"),
        completed_at=job_data.get("completed_at"),
    )


@router.get("/match-suggestions")
def get_product_match_suggestions(
    query: str,
    max_results: int = 5,
    min_score: float = 60.0,
    tenant: Tenant = Depends(get_current_tenant),
):
    """Retourne des suggestions de matching flou pour un nom de produit.

    Args:
        query: Nom de produit recherché
        max_results: Nombre maximum de suggestions (défaut : 5)
        min_score: Score de correspondance minimum 0-100 (défaut : 60.0)
        tenant: Tenant courant

    Returns:
        Liste de suggestions produits avec scores de correspondance
    """
    if not query or not query.strip():
        return {"suggestions": []}

    suggestions = product_matching.get_fuzzy_product_matches(
        query,
        tenant_id=tenant.id,
        max_results=max_results,
        min_score=min_score,
    )

    return {"suggestions": suggestions}


@router.get("/sessions", response_model=ImportSessionListResponse)
def list_import_sessions(
    limit: int = 50,
    offset: int = 0,
    tenant: Tenant = Depends(get_current_tenant),
):
    """Liste les sessions d'import avec statistiques agrégées."""
    sessions_data, total = job_service.list_import_sessions(
        tenant_id=tenant.id,
        limit=limit,
        offset=offset,
    )

    items = []
    for session_data in sessions_data:
        items.append(ImportSession(**session_data))

    return ImportSessionListResponse(items=items, total=total)


@router.get("/sessions/{session_id}", response_model=ImportSessionDetails)
def get_import_session_details(
    session_id: str,
    tenant: Tenant = Depends(get_current_tenant),
):
    """Récupère les détails d'une session d'import avec tous ses imports."""
    session_data = job_service.get_session_details(
        session_id=session_id,
        tenant_id=tenant.id,
    )

    if not session_data:
        raise HTTPException(status_code=404, detail="Session introuvable")

    # Convertir les imports en ZeroClickJobStatus
    imports = []
    for job_data in session_data.get("imports", []):
        summary = None
        if job_data.get("result"):
            try:
                summary = InvoiceImportSummary(**job_data["result"])
            except Exception as exc:
                LOGGER.warning("Impossible de reconstruire le summary pour job %s: %s", job_data["job_id"], exc)

        imports.append(
            ZeroClickJobStatus(
                job_id=job_data["job_id"],
                status=job_data["status"],
                filename=job_data.get("filename"),
                supplier_hint=job_data.get("supplier_hint"),
                margin_percent=job_data.get("margin_percent", 40.0),
                auto_confirm=job_data.get("auto_confirm", True),
                summary=summary,
                error=job_data.get("error"),
                created_at=job_data.get("created_at"),
                updated_at=job_data.get("updated_at"),
                completed_at=job_data.get("completed_at"),
            )
        )

    return ImportSessionDetails(
        session_id=session_data["session_id"],
        date_debut=session_data["date_debut"],
        date_fin=session_data.get("date_fin"),
        nb_imports=session_data["nb_imports"],
        nb_completed=session_data.get("nb_completed", 0),
        nb_failed=session_data.get("nb_failed", 0),
        nb_pending=session_data.get("nb_pending", 0),
        total_lignes=session_data.get("total_lignes", 0),
        total_mouvements=session_data.get("total_mouvements", 0),
        total_produits_crees=session_data.get("total_produits_crees", 0),
        fournisseurs=session_data.get("fournisseurs", []),
        imports=imports,
    )


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
