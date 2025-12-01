"""Invoice extraction and import services."""

from __future__ import annotations

import logging
from pathlib import Path
from datetime import date, datetime, time, timezone

import pandas as pd
from sqlalchemy import text

from backend.services.invoice_utils import prepare_invoice_dataframe
from core import invoice_extractor, products_loader
from core.data_repository import exec_sql, query_df
from core.inventory_service import match_invoice_products, register_invoice_reception
from core.pdf_utils import split_pdf_into_invoices
from core.price_history_service import record_price_history


def _normalize_invoice_datetime(value: datetime | date | None) -> datetime | None:
    """Uniformise une date/datetime de facture en datetime timezone-aware (UTC)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return datetime.combine(value, time.min, tzinfo=timezone.utc)


def extract_invoice_lines(
    text: str,
    *,
    margin_percent: float = 40.0,
    supplier_hint: str | None = None,
) -> pd.DataFrame:
    """Extract structured lines from raw invoice text."""

    if not text.strip():
        return pd.DataFrame()

    # Passage marge (%) -> taux pour le calcul du prix de vente proposé
    margin_rate = max(0.0, margin_percent) / 100.0
    return invoice_extractor.extract_products(
        text,
        supplier_hint=supplier_hint,
        margin_rate=margin_rate,
    )


def enrich_lines_with_catalog(
    lines: pd.DataFrame,
    *,
    margin_percent: float = 40.0,
    tenant_id: int = 1,
) -> pd.DataFrame:
    """Attach catalogue metadata (matches) to parsed invoice lines."""

    df = lines.copy()
    if "codes" not in df.columns or df.empty:
        return df

    # Normalise les codes bars pour matcher avec le catalogue (case/espaces)
    df["_code_lower"] = df["codes"].fillna("").astype(str).str.lower().str.strip()
    matches_df = match_invoice_products(df, tenant_id=tenant_id)
    if not matches_df.empty:
        matches_df = matches_df.rename(
            columns={
                "code": "_code_lower",
                "produit_id": "catalogue_id",
                "produit_nom": "catalogue_nom",
                "categorie": "catalogue_categorie",
                "prix_achat_catalogue": "prix_achat_catalogue",
            }
        )
        df = df.merge(matches_df, on="_code_lower", how="left")
        if "produit_id" not in df.columns:
            df["produit_id"] = df["catalogue_id"]
        else:
            df["produit_id"] = df["produit_id"].fillna(df["catalogue_id"])
    df.drop(columns=["_code_lower"], inplace=True, errors="ignore")
    for column in ("catalogue_id", "catalogue_nom", "catalogue_categorie"):
        if column not in df.columns:
            df[column] = None
    # Finalise les totaux/marges et colonnes numériques normalisées
    margin_rate = max(0.0, margin_percent) / 100.0
    return prepare_invoice_dataframe(df, margin_rate)


def _has_missing_product_ids(df: pd.DataFrame) -> bool:
    """Return True when at least one invoice line lacks a valid produit_id."""

    if "produit_id" not in df.columns:
        return True

    numeric_ids = pd.to_numeric(df["produit_id"], errors="coerce")
    return bool(numeric_ids.isna().any() or (numeric_ids <= 0).any())


def _prepare_lines_for_import(invoice_df: pd.DataFrame, *, tenant_id: int = 1) -> pd.DataFrame:
    """Ensure movements can be created even if the frontend lacks produit_id/quantities."""

    if not isinstance(invoice_df, pd.DataFrame) or invoice_df.empty:
        return invoice_df

    working_df = invoice_df.copy()

    has_codes = "codes" in working_df.columns
    if has_codes and _has_missing_product_ids(working_df):
        # Re-run the catalogue reconciliation with the latest DB state so newly
        # created products (or updated barcodes) are picked up automatically.
        return enrich_lines_with_catalog(working_df, margin_percent=40.0, tenant_id=tenant_id)

    if "quantite_recue" not in working_df.columns and "qte_init" in working_df.columns:
        working_df["quantite_recue"] = working_df["qte_init"]
    elif "quantite_recue" in working_df.columns and "qte_init" in working_df.columns:
        missing_mask = working_df["quantite_recue"].isna()
        if missing_mask.any():
            working_df.loc[missing_mask, "quantite_recue"] = working_df.loc[missing_mask, "qte_init"]

    return working_df


def apply_invoice_import(
    invoice_df: pd.DataFrame,
    *,
    username: str,
    supplier: str | None = None,
    movement_type: str = "ENTREE",
    invoice_date: datetime | date | None = None,
    tenant_id: int = 1,
) -> dict[str, object]:
    """Persist movements based on the invoice lines."""

    # Sécurise les données avant création des mouvements (quantités, produit_id)
    prepared_df = _prepare_lines_for_import(invoice_df, tenant_id=tenant_id)

    normalized_invoice_dt = _normalize_invoice_datetime(invoice_date)
    if normalized_invoice_dt is None and "facture_date" in invoice_df.columns and not invoice_df["facture_date"].dropna().empty:
        first_value = invoice_df["facture_date"].dropna().iloc[0]
        try:
            normalized_invoice_dt = _normalize_invoice_datetime(pd.to_datetime(first_value).to_pydatetime())
        except Exception:
            normalized_invoice_dt = None

    result = register_invoice_reception(
        prepared_df,
        username=username,
        supplier=supplier,
        movement_type=movement_type,
        reception_date=normalized_invoice_dt,
        tenant_id=tenant_id,
    )
    record_processed_invoices(prepared_df, supplier=supplier, tenant_id=tenant_id)
    return result


def import_catalog_from_invoice(
    invoice_df: pd.DataFrame,
    *,
    supplier: str | None = None,
    initialize_stock: bool = False,
    invoice_date: datetime | None = None,
    tenant_id: int = 1,
) -> dict[str, object]:
    """Create/update catalogue entries from invoice lines and log price history."""

    if not isinstance(invoice_df, pd.DataFrame):
        raise ValueError("Le format des lignes est invalide.")

    # 1) Création/MAJ produits + codes, 2) historisation des prix avec date facture
    summary = products_loader.load_products_from_df(
        invoice_df,
        initialize_stock=initialize_stock,
        tenant_id=tenant_id,
    )
    normalized_invoice_dt = _normalize_invoice_datetime(invoice_date)
    record_price_history(
        invoice_df,
        supplier=supplier,
        context="Extraction",
        invoice_date=normalized_invoice_dt or datetime.now(timezone.utc),
        tenant_id=tenant_id,
    )
    record_processed_invoices(invoice_df, supplier=supplier, tenant_id=tenant_id)
    return summary


__all__ = [
    "extract_invoice_lines",
    "enrich_lines_with_catalog",
    "apply_invoice_import",
    "import_catalog_from_invoice",
    "record_processed_invoices",
    "find_processed_invoice_ids",
    "persist_invoice_documents",
    "list_processed_invoices",
    "get_processed_invoice_file",
]
LOGGER = logging.getLogger(__name__)
INVOICE_ARCHIVE_DIR = Path("data/processed_invoices")
INVOICE_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def _build_invoice_filename(tenant_id: int, invoice_id: str) -> Path:
    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in invoice_id)
    return INVOICE_ARCHIVE_DIR / f"{tenant_id}_{safe_id}.pdf"


def _collect_invoice_groups(invoice_df: pd.DataFrame) -> list[dict[str, object]]:
    if not isinstance(invoice_df, pd.DataFrame) or invoice_df.empty or "invoice_id" not in invoice_df.columns:
        return []

    groups: list[dict[str, object]] = []
    for invoice_id, group in invoice_df.groupby("invoice_id"):
        invoice_key = str(invoice_id or "").strip()
        if not invoice_key:
            continue
        facture_date = None
        if "facture_date" in group.columns:
            facture_candidates = [str(value).strip() for value in group["facture_date"].dropna().tolist() if str(value).strip()]
            if facture_candidates:
                facture_date = facture_candidates[0]
        groups.append(
            {
                "invoice_id": invoice_key,
                "line_count": int(len(group)),
                "facture_date": facture_date,
            }
        )
    return groups


def _fetch_processed_invoice_ids(invoice_ids: set[str], *, tenant_id: int) -> set[str]:
    if not invoice_ids:
        return set()

    params: dict[str, object] = {"tenant_id": int(tenant_id)}
    placeholders: list[str] = []
    for idx, invoice_id in enumerate(sorted(invoice_ids)):
        key = f"invoice_{idx}"
        placeholders.append(f":{key}")
        params[key] = invoice_id

    sql = text(
        f"""
        SELECT invoice_id
        FROM processed_invoices
        WHERE tenant_id = :tenant_id
          AND invoice_id IN ({", ".join(placeholders)})
        """
    )

    try:
        df = query_df(sql, params=params)
    except Exception as exc:  # pragma: no cover - base indisponible
        LOGGER.warning("Impossible de vérifier les factures importées: %s", exc)
        return set()

    if df.empty:
        return set()
    return {str(entry) for entry in df["invoice_id"].tolist()}


def record_processed_invoices(invoice_df: pd.DataFrame, *, supplier: str | None, tenant_id: int) -> None:
    groups = _collect_invoice_groups(invoice_df)
    if not groups:
        return
    supplier_label = (supplier or "Inconnu").strip() or "Inconnu"
    sql = text(
        """
        INSERT INTO processed_invoices (tenant_id, invoice_id, supplier, facture_date, line_count, file_path)
        VALUES (:tenant_id, :invoice_id, :supplier, :facture_date, :line_count, :file_path)
        ON CONFLICT (tenant_id, invoice_id)
        DO UPDATE SET
            supplier = EXCLUDED.supplier,
            facture_date = COALESCE(EXCLUDED.facture_date, processed_invoices.facture_date),
            line_count = EXCLUDED.line_count,
            file_path = COALESCE(EXCLUDED.file_path, processed_invoices.file_path),
            updated_at = now()
        """
    )
    params_batch: list[dict[str, object]] = []
    for group in groups:
        invoice_id = group["invoice_id"]
        default_path = _build_invoice_filename(tenant_id, invoice_id)
        file_path = str(default_path) if default_path.exists() else None
        params_batch.append(
            {
                "tenant_id": int(tenant_id),
                "invoice_id": invoice_id,
                "supplier": supplier_label,
                "facture_date": group.get("facture_date"),
                "line_count": group.get("line_count", 0),
                "file_path": file_path,
            }
        )
    try:
        exec_sql(sql, params=params_batch)
    except Exception as exc:  # pragma: no cover - base indisponible
        LOGGER.warning("Impossible d'enregistrer les factures (batch): %s", exc)


def find_processed_invoice_ids(invoice_ids: set[str], *, tenant_id: int) -> set[str]:
    try:
        return _fetch_processed_invoice_ids(invoice_ids, tenant_id=tenant_id)
    except Exception:
        return set()


def list_processed_invoices(
    *,
    tenant_id: int,
    supplier: str | None = None,
    invoice_id: str | None = None,
    date_start: str | None = None,
    date_end: str | None = None,
    limit: int = 100,
) -> list[dict[str, object]]:
    filters = ["tenant_id = :tenant_id"]
    params: dict[str, object] = {"tenant_id": int(tenant_id), "limit": int(max(1, min(limit, 500)))}

    if supplier:
        filters.append("supplier ILIKE :supplier")
        params["supplier"] = f"%{supplier}%"
    if invoice_id:
        filters.append("invoice_id ILIKE :invoice_id")
        params["invoice_id"] = f"%{invoice_id}%"
    if date_start:
        filters.append("facture_date >= :date_start")
        params["date_start"] = date_start
    if date_end:
        filters.append("facture_date <= :date_end")
        params["date_end"] = date_end

    where_clause = " AND ".join(filters)
    sql = text(
        f"""
        SELECT invoice_id, supplier, facture_date, line_count, file_path, created_at, updated_at
        FROM processed_invoices
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
        """
    )

    df = query_df(sql, params=params)
    if df.empty:
        return []
    return df.to_dict(orient="records")


def persist_invoice_documents(pdf_bytes: bytes, *, tenant_id: int, supplier: str | None = None) -> dict[str, dict[str, str]]:
    """Découpe et stocke physiquement chaque facture détectée."""

    documents = split_pdf_into_invoices(pdf_bytes)
    if not documents:
        return {}

    stored: dict[str, dict[str, str]] = {}
    for entry in documents:
        invoice_id = str(entry.get("invoice_id") or "").strip()
        if not invoice_id:
            continue
        pdf_chunk: bytes = entry.get("pdf_bytes") or b""
        if not pdf_chunk:
            continue
        file_path = _build_invoice_filename(tenant_id, invoice_id)
        try:
            file_path.write_bytes(pdf_chunk)
            stored[invoice_id] = {
                "facture_date": entry.get("facture_date"),
                "file_path": str(file_path),
                "supplier": supplier,
            }
        except Exception as exc:  # pragma: no cover
            LOGGER.warning("Impossible de sauvegarder la facture %s: %s", invoice_id, exc)
    return stored


def get_processed_invoice_file(*, tenant_id: int, invoice_id: str) -> Path | None:
    if not invoice_id:
        return None
    sql = text(
        """
        SELECT file_path
        FROM processed_invoices
        WHERE tenant_id = :tenant_id AND invoice_id = :invoice_id
        LIMIT 1
        """
    )
    df = query_df(sql, params={"tenant_id": int(tenant_id), "invoice_id": invoice_id})
    if df.empty:
        # tente un chemin dérivé
        candidate = _build_invoice_filename(tenant_id, invoice_id)
        return candidate if candidate.exists() else None
    raw_path = df.iloc[0].get("file_path")
    if raw_path:
        path = Path(raw_path)
        if path.exists():
            return path
    candidate = _build_invoice_filename(tenant_id, invoice_id)
    return candidate if candidate.exists() else None
