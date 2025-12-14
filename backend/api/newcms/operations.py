"""NewCMS Operations API - Unified operations dashboard endpoints."""

from __future__ import annotations

import base64
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.dependencies.tenant import Tenant, get_current_tenant_or_default
from backend.schemas.newcms import (
    OperationsOverviewResponse,
    CatalogProxyResponse,
    StockProxyResponse,
    InvoicesProxyResponse,
    InvoiceImportUploadRequest,
    InvoiceImportStatusResponse,
    InvoiceImportLineUpdateRequest,
    InvoiceImportActionResponse,
    PriceAnomalyResolveRequest,
    PriceAnomalyResolveResponse,
    CreateOrderRequest,
    CreateOrderResponse,
)
from backend.services import catalog as catalog_service
from backend.services import invoices as invoices_service
from backend.services import reports as reports_service
from core.data_repository import query_df, exec_sql
from sqlalchemy import text

router = APIRouter(prefix="/operations", tags=["newcms-operations"])
IMPORT_JOBS_PATH = Path(__file__).resolve().parents[2] / "data" / "newcms_import_jobs.json"


def _load_import_jobs() -> dict[str, Any]:
    if not IMPORT_JOBS_PATH.exists():
        return {}
    try:
        return json.loads(IMPORT_JOBS_PATH.read_text())
    except Exception:
        return {}


def _save_import_jobs(jobs: dict[str, Any]) -> None:
    IMPORT_JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMPORT_JOBS_PATH.write_text(json.dumps(jobs, indent=2, default=str))


def _to_date(value: Any) -> date | None:
    """Convertit un input possible (str/datetime/date) en date."""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed.date()
    except Exception:
        return None


def _none_if_nan(value: Any) -> Any:
    """Convertit les NaN/NaT en None pour éviter les erreurs SQL."""
    try:
        # pandas/numpy NaN/NaT
        if value != value:  # type: ignore[comparison-overlap]  # NaN != NaN
            return None
    except Exception:
        return value
    return value


def _normalize_line(line: dict[str, Any], default_invoice_date: date | None = None) -> dict[str, Any]:
    """Nettoie les valeurs de ligne avant stockage/retour."""
    line["quantity"] = _none_if_nan(line.get("quantity"))
    line["unit_price"] = _none_if_nan(line.get("unit_price"))
    line["tax_rate"] = _none_if_nan(line.get("tax_rate"))
    line["product_id"] = _none_if_nan(line.get("product_id"))
    inv_dt = line.get("invoice_date") or default_invoice_date
    line["invoice_date"] = _to_date(inv_dt)
    line["error"] = line.get("error")
    return line


def _get_job(job_id: str, *, tenant_id: int) -> dict[str, Any]:
    jobs = _load_import_jobs()
    job = jobs.get(job_id)
    if not job or job.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Import introuvable")
    if job.get("errors") is None:
        job["errors"] = []
    if job.get("invoice_date") is not None:
        job["invoice_date"] = _to_date(job["invoice_date"])
    for line in job.get("lines", []):
        _normalize_line(line, default_invoice_date=job.get("invoice_date"))
    return job


def _store_job(job: dict[str, Any]) -> None:
    jobs = _load_import_jobs()
    jobs[job["job_id"]] = job
    _save_import_jobs(jobs)


def _generate_dummy_lines(filename: str, invoice_date: date | None = None) -> list[dict[str, Any]]:
    base_label = filename.rsplit(".", 1)[0][:20] or "Facture"
    return [
        {
            "line_id": f"ln-{idx}",
            "description": f"{base_label} - ligne {idx + 1}",
            "quantity": float(quant),
            "unit_price": float(price),
            "tax_rate": 0.2,
            "product_id": None,
            "status": "pending",
            "notes": None,
            "invoice_date": invoice_date,
            "error": None,
        }
        for idx, (quant, price) in enumerate([(3, 12.5), (5, 3.2), (1, 54.0)])
    ]


class EmailWebhookPayload(BaseModel):
    subject: str | None = None
    from_email: str | None = None
    attachments: list[InvoiceImportUploadRequest] = Field(default_factory=list)


# =============================================================================
# Import staging (DB)
# =============================================================================


def _ensure_import_tables() -> None:
    """Crée les tables de staging si elles n'existent pas."""
    sql_jobs = """
        CREATE TABLE IF NOT EXISTS newcms_invoice_import_jobs (
            job_id TEXT PRIMARY KEY,
            tenant_id INT NOT NULL,
            filename TEXT,
            supplier TEXT,
            status TEXT NOT NULL,
            progress NUMERIC(5,2) DEFAULT 0,
            errors JSONB DEFAULT '[]'::jsonb,
            source TEXT,
            invoice_date DATE,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """
    sql_lines = """
        CREATE TABLE IF NOT EXISTS newcms_invoice_import_lines (
            id SERIAL PRIMARY KEY,
            job_id TEXT NOT NULL REFERENCES newcms_invoice_import_jobs(job_id) ON DELETE CASCADE,
            line_id TEXT,
            description TEXT,
            quantity NUMERIC(12,2),
            unit_price NUMERIC(12,2),
            tax_rate NUMERIC(5,3),
            product_id INT,
            status TEXT,
            notes TEXT,
            error TEXT,
            invoice_date DATE,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
    """
    exec_sql(sql_jobs)
    exec_sql(sql_lines)


def _store_job_db(job: dict[str, Any]) -> None:
    _ensure_import_tables()
    errors_param = job.get("errors", [])
    if not isinstance(errors_param, str):
        errors_param = json.dumps(errors_param)
    exec_sql(
        """
        INSERT INTO newcms_invoice_import_jobs (job_id, tenant_id, filename, supplier, status, progress, errors, source, invoice_date, created_at, updated_at)
        VALUES (:job_id, :tenant_id, :filename, :supplier, :status, :progress, CAST(:errors AS jsonb), :source, :invoice_date, :created_at, :updated_at)
        ON CONFLICT (job_id) DO UPDATE SET
            supplier = EXCLUDED.supplier,
            status = EXCLUDED.status,
            progress = EXCLUDED.progress,
            errors = EXCLUDED.errors,
            source = EXCLUDED.source,
            invoice_date = EXCLUDED.invoice_date,
            updated_at = EXCLUDED.updated_at
        """,
        params={
            "job_id": job["job_id"],
            "tenant_id": job["tenant_id"],
            "filename": job["filename"],
            "supplier": job.get("supplier"),
            "status": job["status"],
            "progress": job["progress"],
            "errors": errors_param,
            "source": job.get("source"),
            "invoice_date": _to_date(job.get("invoice_date")),
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
        },
    )
    # lignes
    exec_sql("DELETE FROM newcms_invoice_import_lines WHERE job_id = :job_id", params={"job_id": job["job_id"]})
    lines = job.get("lines", [])
    if lines:
        exec_sql(
            """
            INSERT INTO newcms_invoice_import_lines (job_id, line_id, description, quantity, unit_price, tax_rate, product_id, status, notes, error, invoice_date, created_at, updated_at)
            VALUES (:job_id, :line_id, :description, :quantity, :unit_price, :tax_rate, :product_id, :status, :notes, :error, :invoice_date, :created_at, :updated_at)
            """,
            params=[
                {
                    "job_id": job["job_id"],
                    "line_id": line.get("line_id"),
                    "description": line.get("description"),
                    "quantity": _none_if_nan(line.get("quantity")),
                    "unit_price": _none_if_nan(line.get("unit_price")),
                    "tax_rate": _none_if_nan(line.get("tax_rate")),
                    "product_id": _none_if_nan(line.get("product_id")),
                    "status": line.get("status"),
                    "notes": line.get("notes"),
                    "error": line.get("error"),
                    "invoice_date": _to_date(line.get("invoice_date") or job.get("invoice_date")),
                    "created_at": job["created_at"],
                    "updated_at": job["updated_at"],
                }
                for line in lines
            ],
        )


def _load_job_db(job_id: str, tenant_id: int) -> dict[str, Any] | None:
    _ensure_import_tables()
    job_df = query_df(
        """
        SELECT job_id, tenant_id, filename, supplier, status, progress, errors, source, invoice_date, created_at, updated_at
        FROM newcms_invoice_import_jobs
        WHERE job_id = :job_id AND tenant_id = :tenant_id
        """,
        params={"job_id": job_id, "tenant_id": tenant_id},
    )
    if job_df.empty:
        return None
    job_row = job_df.iloc[0].to_dict()
    if job_row.get("invoice_date") is not None:
        job_row["invoice_date"] = _to_date(job_row["invoice_date"])
    errors_val = job_row.get("errors")
    if isinstance(errors_val, str):
        try:
            job_row["errors"] = json.loads(errors_val)
        except Exception:
            job_row["errors"] = [errors_val]
    if job_row.get("errors") is None:
        job_row["errors"] = []
    lines_df = query_df(
        """
        SELECT line_id, description, quantity, unit_price, tax_rate, product_id, status, notes, invoice_date, error
        FROM newcms_invoice_import_lines
        WHERE job_id = :job_id
        ORDER BY id
        """,
        params={"job_id": job_id},
    )
    job_row["lines"] = lines_df.where(lines_df.notna(), None).to_dict("records") if not lines_df.empty else []
    for line in job_row["lines"]:
        if line.get("invoice_date") is not None:
            line["invoice_date"] = _to_date(line["invoice_date"])
        _normalize_line(line, default_invoice_date=job_row.get("invoice_date"))
    return job_row


@router.get("/overview", response_model=OperationsOverviewResponse, summary="Overview Opérations", tags=["newcms-operations"])
async def get_operations_overview(
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> OperationsOverviewResponse:
    """
    **Operations Overview - Vue d'ensemble opérationnelle**

    Endpoint agrégé qui fournit toutes les données critiques pour les opérations quotidiennes.
    Dashboard central pour la gestion du stock, factures et anomalies.

    ## Données retournées

    ### Stock critique (top 5)
    Produits avec `stock_actuel <= 0`:
    - Rupture totale
    - Commande urgente nécessaire
    - Impact sur les ventes

    ### Stock en alerte (top 5)
    Produits avec `0 < stock_actuel < seuil_alerte`:
    - Bientôt en rupture
    - Réapprovisionnement recommandé
    - Suivi préventif

    ### 5 dernières factures traitées
    - Date, fournisseur, montant
    - Statut de traitement
    - Lien vers la facture

    ### Anomalies de prix (14 derniers jours)
    Variations de prix > 10% détectées:
    - Produit concerné
    - Prix actuel vs prix précédent
    - Pourcentage de variation
    - Date de détection

    ### Actions en attente
    - Nombre d'imports de factures en attente
    - Nombre total d'alertes

    ## Format de réponse

    ```json
    {
      "success": true,
      "data": {
        "critical_stock": [...],
        "low_stock": [...],
        "recent_invoices": [...],
        "price_anomalies": [...],
        "pending_imports": 0,
        "alert_count": 12,
        "timestamp": "2025-12-11T10:00:00"
      },
      "meta": {}
    }
    ```

    ## Tags
    - newcms-operations
    """

    # 1. Stock critique et alerte
    critical_stock = []
    low_stock = []

    try:
        # Stock critique (quantité <= 0)
        critical_items = reports_service.fetch_low_stock(tenant_id=tenant.id, limit=10)
        critical_stock = [
            item for item in critical_items
            if item.get("stock_actuel", 0) <= 0
        ][:5]

        # Stock en alerte (0 < stock < seuil)
        low_stock = [
            item for item in critical_items
            if 0 < item.get("stock_actuel", 0) <= item.get("seuil_alerte", 0)
        ][:5]
    except Exception:
        # Fallback silencieux
        pass

    # 2. Dernières factures traitées (5 plus récentes)
    recent_invoices = []
    try:
        recent_invoices = invoices_service.list_processed_invoices(
            tenant_id=tenant.id,
            limit=5,
        )
    except Exception:
        pass

    # 3. Anomalies de prix (14 derniers jours)
    price_anomalies = []
    try:
        # Requête pour détecter les anomalies de prix récentes
        anomaly_sql = text("""
            SELECT
                p.id AS product_id,
                p.nom AS product_name,
                p.prix_achat AS current_price,
                ph.prix_achat AS previous_price,
                ph.facture_date,
                ABS(p.prix_achat - ph.prix_achat) AS price_difference,
                CASE
                    WHEN ph.prix_achat > 0 THEN
                        ROUND(((p.prix_achat - ph.prix_achat) / ph.prix_achat * 100)::numeric, 2)
                    ELSE 0
                END AS price_change_pct
            FROM produits p
            JOIN produits_price_history ph ON ph.produit_id = p.id
            WHERE p.tenant_id = :tenant_id
              AND ph.tenant_id = :tenant_id
              AND ph.facture_date >= :date_start
              AND ABS(p.prix_achat - ph.prix_achat) > 0.01
              AND ph.prix_achat > 0
              AND CASE
                    WHEN ph.prix_achat > 0 THEN
                        ABS((p.prix_achat - ph.prix_achat) / ph.prix_achat * 100)
                    ELSE 0
                  END > 10
            ORDER BY ABS(p.prix_achat - ph.prix_achat) DESC
            LIMIT 10
        """)

        date_start = (datetime.now() - timedelta(days=14)).date()
        df = query_df(anomaly_sql, params={
            "tenant_id": tenant.id,
            "date_start": date_start,
        })

        if not df.empty:
            price_anomalies = df.to_dict(orient="records")
    except Exception:
        pass

    # 4. Actions d'import en attente (factures non confirmées)
    # Pour simplifier, on compte les factures extraites mais non importées
    # Cela nécessiterait une table dédiée en production
    pending_imports = 0

    # Résumé des alertes
    alert_count = len(critical_stock) + len(low_stock)

    return OperationsOverviewResponse(
        success=True,
        data={
            "critical_stock": critical_stock,
            "low_stock": low_stock,
            "recent_invoices": recent_invoices,
            "price_anomalies": price_anomalies,
            "pending_imports": pending_imports,
            "alert_count": alert_count,
            "timestamp": datetime.now().isoformat(),
        },
        meta={},
    )


@router.get("/catalog", response_model=CatalogProxyResponse, summary="Catalogue produits paginé", tags=["newcms-operations"])
async def get_catalog_proxy(
    page: int = Query(default=1, ge=1, le=10000, description="Numéro de page"),
    per_page: int = Query(default=20, ge=1, le=100, description="Éléments par page (max 100)"),
    q: str | None = Query(default=None, description="Recherche textuelle (nom produit)"),
    category: str | None = Query(default=None, description="Filtrer par catégorie"),
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> CatalogProxyResponse:
    """
    **Catalogue produits - Liste paginée**

    Proxy vers le service catalog existant avec pagination optimisée.
    Permet de naviguer dans l'ensemble du catalogue avec filtres.

    ## Paramètres

    - **page**: Numéro de page (1-10000)
    - **per_page**: Éléments par page (1-100, défaut: 20)
    - **q**: Recherche textuelle sur le nom du produit
    - **category**: Filtrer par catégorie

    ## Tags
    - newcms-operations
    """
    items, total = catalog_service.list_products_page(
        tenant_id=tenant.id,
        search=q,
        category=category,
        status=None,
        page=page,
        per_page=per_page,
    )

    return CatalogProxyResponse(
        success=True,
        data={"items": items},
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
        },
    )


@router.get("/stock", response_model=StockProxyResponse, summary="Stock produits paginé", tags=["newcms-operations"])
async def get_stock_proxy(
    page: int = Query(default=1, ge=1, le=10000, description="Numéro de page"),
    per_page: int = Query(default=20, ge=1, le=100, description="Éléments par page (max 100)"),
    q: str | None = Query(default=None, description="Recherche textuelle"),
    status: str | None = Query(default=None, description="Filtrer par statut: critical, low, ok"),
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> StockProxyResponse:
    """
    **Stock produits - Liste paginée avec statuts**

    Endpoint pour consulter le stock avec filtrage par statut d'alerte.
    Permet d'identifier rapidement les produits nécessitant une action.

    ## Statuts disponibles

    - **critical**: Stock épuisé (`stock_actuel <= 0`)
      - Rupture totale
      - Action immédiate requise
    - **low**: Stock bas (`0 < stock_actuel < seuil_alerte`)
      - Réapprovisionnement recommandé
      - Suivi préventif
    - **ok**: Stock normal (`stock_actuel >= seuil_alerte`)
      - Aucune action nécessaire

    ## Paramètres

    - **page**: Numéro de page (1-10000)
    - **per_page**: Éléments par page (1-100, défaut: 20)
    - **q**: Recherche textuelle sur le nom
    - **status**: Filtrer par statut (critical/low/ok)

    ## Tags
    - newcms-operations
    """
    # Mapper les statuts newCMS vers les statuts du service
    status_mapping = {
        "critical": "critical",
        "low": "warning",  # Le service utilise "warning" pour stock < seuil
        "ok": "ok",
    }

    mapped_status = status_mapping.get(status) if status else None

    items, total = catalog_service.list_products_page(
        tenant_id=tenant.id,
        search=q,
        category=None,
        status=mapped_status,
        page=page,
        per_page=per_page,
    )

    return StockProxyResponse(
        success=True,
        data={"items": items},
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
        },
    )


@router.get("/invoices", response_model=InvoicesProxyResponse, summary="Factures traitées paginées", tags=["newcms-operations"])
async def get_invoices_proxy(
    page: int = Query(default=1, ge=1, le=10000, description="Numéro de page"),
    per_page: int = Query(default=20, ge=1, le=100, description="Éléments par page (max 100)"),
    status: str | None = Query(default=None, description="Statut (non implémenté)"),
    date_from: str | None = Query(default=None, description="Date début (YYYY-MM-DD)"),
    date_to: str | None = Query(default=None, description="Date fin (YYYY-MM-DD)"),
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> InvoicesProxyResponse:
    """
    **Factures traitées - Liste paginée**

    Endpoint pour consulter l'historique des factures importées et traitées.
    Permet de filtrer par plage de dates.

    ## Paramètres

    - **page**: Numéro de page (1-10000)
    - **per_page**: Éléments par page (1-100, défaut: 20)
    - **date_from, date_to**: Plage de dates (YYYY-MM-DD)
    - **status**: Filtrage par statut (non implémenté)

    ## Tags
    - newcms-operations
    """
    # Calcul de l'offset pour la pagination manuelle
    # Le service list_processed_invoices ne supporte que limit
    # On va charger plus et paginer en mémoire (non optimal mais fonctionnel)

    # Charger toutes les factures nécessaires pour cette page
    max_items = page * per_page
    all_items = invoices_service.list_processed_invoices(
        tenant_id=tenant.id,
        supplier=None,
        invoice_id=None,
        date_start=date_from,
        date_end=date_to,
        limit=max_items,  # Charger jusqu'à la page demandée
    )

    # Pagination manuelle
    offset = (page - 1) * per_page
    items = all_items[offset:offset + per_page]

    # Le total est approximatif (au minimum len(all_items))
    # Pour un vrai total, il faudrait une requête COUNT séparée
    total = len(all_items)

    return InvoicesProxyResponse(
        success=True,
        data={"items": items},
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
        },
    )


# =============================================================================
# Import factures (dropzone / scanner / email)
# =============================================================================


@router.post("/invoices/import", response_model=InvoiceImportStatusResponse, summary="Créer un job d'import facture")
async def create_invoice_import(
    payload: InvoiceImportUploadRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> InvoiceImportStatusResponse:
    """Reçoit un fichier (base64) et crée un job d'import dans un stockage léger."""
    try:
        base64.b64decode(payload.content_base64, validate=False)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Base64 invalide: {exc}") from exc

    invoice_dt = _to_date(payload.invoice_date)
    job_id = f"imp-{uuid4().hex[:8]}"
    now = datetime.utcnow()
    job = {
        "job_id": job_id,
        "tenant_id": tenant.id,
        "filename": payload.filename,
        "supplier": payload.supplier,
        "status": "ready",
        "progress": 1.0,
        "errors": [],
        "lines": _generate_dummy_lines(payload.filename, invoice_dt),
        "created_at": now,
        "updated_at": now,
        "source": payload.source or "upload",
        "invoice_date": invoice_dt,
    }
    _store_job(job)
    _store_job_db(job)
    return InvoiceImportStatusResponse(success=True, job=job)


@router.get("/invoices/import/{job_id}", response_model=InvoiceImportStatusResponse, summary="Statut d'un import facture")
async def get_invoice_import_status(
    job_id: str,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> InvoiceImportStatusResponse:
    job = _load_job_db(job_id, tenant.id) or _get_job(job_id, tenant_id=tenant.id)
    if not job:
        raise HTTPException(status_code=404, detail="Import introuvable")
    return InvoiceImportStatusResponse(success=True, job=job)


@router.post(
    "/invoices/import/{job_id}/lines/{line_id}",
    response_model=InvoiceImportActionResponse,
    summary="Corriger une ligne d'import",
)
async def update_invoice_import_line(
    job_id: str,
    line_id: str,
    payload: InvoiceImportLineUpdateRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> InvoiceImportActionResponse:
    job = _get_job(job_id, tenant_id=tenant.id)
    job_db = _load_job_db(job_id, tenant.id)
    if job_db:
        job = job_db
    lines: list[dict[str, Any]] = job.get("lines", [])
    match = next((line for line in lines if str(line.get("line_id")) == line_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Ligne introuvable")

    for key, value in payload.dict(exclude_none=True).items():
        if key == "invoice_date":
            match[key] = _to_date(value)
        else:
            match[key] = value
    match.setdefault("status", "corrected")
    _normalize_line(match, default_invoice_date=job.get("invoice_date"))
    job["updated_at"] = datetime.utcnow()
    _store_job(job)
    _store_job_db(job)
    return InvoiceImportActionResponse(success=True, job=job, message="Ligne mise à jour")


@router.post("/invoices/import/{job_id}/confirm", response_model=InvoiceImportActionResponse, summary="Confirmer un import")
async def confirm_invoice_import(
    job_id: str,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> InvoiceImportActionResponse:
    job = _load_job_db(job_id, tenant.id) or _get_job(job_id, tenant_id=tenant.id)
    job["errors"] = job.get("errors") or []
    job["status"] = "processing"
    job["progress"] = 0.5
    job["updated_at"] = datetime.utcnow()
    message = "Import confirmé"
    invoice_dt = _to_date(job.get("invoice_date"))
    # Validation basique des lignes pour remonter les erreurs côté UI
    line_errors: list[str] = []
    for line in job.get("lines", []):
        issues: list[str] = []
        if line.get("quantity") in (None, 0):
            issues.append("quantité manquante")
        if line.get("unit_price") is None:
            issues.append("prix manquant")
        if line.get("product_id") is None:
            issues.append("produit non sélectionné")
        if issues:
            line["error"] = "; ".join(issues)
            line_errors.append(f"{line.get('line_id')}: {line['error']}")
        else:
            line["error"] = None
        line["invoice_date"] = _to_date(line.get("invoice_date") or invoice_dt)
    if line_errors:
        job["status"] = "error"
        job["errors"] = line_errors
        _store_job(job)
        _store_job_db(job)
        return InvoiceImportActionResponse(success=False, job=job, message="Corrections nécessaires avant application")
    try:
        lines_df = pd.DataFrame(job.get("lines", []))
        if lines_df.empty:
            raise ValueError("Aucune ligne à appliquer")
        lines_df = lines_df.rename(
            columns={
                "description": "nom",
                "quantity": "quantite_recue",
                "unit_price": "prix_achat",
                "tax_rate": "tva",
                "product_id": "produit_id",
                "invoice_date": "facture_date",
            }
        )
        if invoice_dt and "facture_date" not in lines_df:
            lines_df["facture_date"] = invoice_dt
        if "facture_date" in lines_df and invoice_dt:
            lines_df["facture_date"] = lines_df["facture_date"].fillna(invoice_dt)
        if "facture_date" in lines_df and lines_df["facture_date"].notna().any():
            try:
                lines_df["facture_date"] = pd.to_datetime(lines_df["facture_date"]).dt.date
            except Exception:
                pass
        summary = invoices_service.apply_invoice_import(
            lines_df,
            username="newcms",
            supplier=job.get("supplier"),
            movement_type="ENTREE",
            invoice_date=invoice_dt,
            tenant_id=tenant.id,
        )
        job["summary"] = summary
        job["errors"] = []
        message = "Import appliqué (stock/prix)"
        job["status"] = "confirmed"
        job["progress"] = 1.0
    except Exception as exc:
        job.setdefault("errors", []).append(str(exc))
        job["status"] = "error"
        message = f"Erreur application import: {exc}"
    _store_job(job)
    _store_job_db(job)
    return InvoiceImportActionResponse(success=True, job=job, message=message)


@router.post("/invoices/import/{job_id}/cancel", response_model=InvoiceImportActionResponse, summary="Annuler un import")
async def cancel_invoice_import(
    job_id: str,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> InvoiceImportActionResponse:
    job = _get_job(job_id, tenant_id=tenant.id)
    job_db = _load_job_db(job_id, tenant.id)
    if job_db:
        job = job_db
    job["status"] = "canceled"
    job["updated_at"] = datetime.utcnow()
    _store_job(job)
    _store_job_db(job)
    return InvoiceImportActionResponse(success=True, job=job, message="Import annulé")


@router.post("/invoices/email-webhook", summary="Webhook email factures", tags=["internal"])
async def email_webhook_import(
    payload: EmailWebhookPayload,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict[str, Any]:
    created_jobs: list[dict[str, Any]] = []
    for attachment in payload.attachments:
        job_resp = await create_invoice_import(attachment, tenant)  # reuse handler
        created_jobs.append(job_resp.job)
    return {"success": True, "jobs": created_jobs, "count": len(created_jobs)}


# =============================================================================
# Actions tableau (prix / commandes)
# =============================================================================


@router.post(
    "/price-anomalies/{product_id}/resolve",
    response_model=PriceAnomalyResolveResponse,
    summary="Résoudre une anomalie de prix",
)
async def resolve_price_anomaly(
    product_id: int,
    payload: PriceAnomalyResolveRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> PriceAnomalyResolveResponse:
    applied = bool(payload.new_price is not None)
    message = "Anomalie enregistrée"
    if applied:
        message = "Nouveau prix pris en compte (simulation)"
    return PriceAnomalyResolveResponse(
        success=True,
        product_id=product_id,
        applied=applied,
        message=message,
    )


@router.post("/orders", response_model=CreateOrderResponse, summary="Créer une commande fournisseur")
async def create_supplier_order(
    payload: CreateOrderRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> CreateOrderResponse:
    total = 0.0
    for item in payload.items:
        unit = item.unit_price or 0.0
        total += unit * item.quantity
    order_id = f"ord-{uuid4().hex[:8]}"
    return CreateOrderResponse(
        success=True,
        order_id=order_id,
        supplier=payload.supplier,
        item_count=len(payload.items),
        total_estimated=round(total, 2),
    )
