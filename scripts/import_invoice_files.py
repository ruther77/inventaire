"""CLI to import supplier invoices (PDF/DOCX/TXT) end-to-end."""

from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

import sys
from pathlib import Path as _PathHelper

sys.path.append(str(_PathHelper(__file__).resolve().parents[1]))

from backend.services import invoices as invoices_service
from core import invoice_extractor
from core.consolidation_loader import sync_invoice_dataframe
from core.data_repository import get_engine
from core.tenant_service import ensure_tenants_table


def _resolve_tenant_id(code: str) -> int:
    ensure_tenants_table()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(text("SELECT id FROM tenants WHERE code = :code"), {"code": code}).fetchone()
    if not row:
        raise SystemExit(f"Tenant '{code}' introuvable. Ajoutez-le dans la table tenants.")
    return int(row.id)


def _read_text_from_path(path: Path) -> str:
    with path.open("rb") as handle:
        class _Adapter:
            name = path.name
            type = path.suffix

            def __init__(self, data: bytes):
                self._buffer = data

            def read(self):
                return self._buffer

            def getvalue(self):
                return self._buffer

        return invoice_extractor.extract_text_from_file(_Adapter(handle.read()))


def _infer_invoice_reference(path: Path) -> str:
    return path.stem.replace(' ', '_')


def _infer_invoice_datetime(df: pd.DataFrame, fallback: datetime | None = None) -> datetime | None:
    if "facture_date" in df.columns:
        parsed = pd.to_datetime(df["facture_date"], errors="coerce").dropna()
        if not parsed.empty:
            ts = parsed.iloc[0]
            if isinstance(ts, pd.Timestamp):
                return ts.to_pydatetime()
            if isinstance(ts, datetime):
                return ts
            if isinstance(ts, date):
                return datetime.combine(ts, datetime.min.time())
    return fallback


def _import_single_file(
    path: Path,
    *,
    tenant_id: int,
    supplier: str,
    username: str,
    margin_percent: float,
    initialize_stock: bool,
    invoice_date: datetime | None,
    force: bool = False,
) -> dict:
    print(f"Traitement de {path} …")
    text_content = _read_text_from_path(path)
    extracted_df = invoices_service.extract_invoice_lines(
        text_content,
        margin_percent=margin_percent,
        supplier_hint=supplier,
    )
    if extracted_df.empty:
        print("  → Aucune ligne détectée, fichier ignoré.")
        return {"lines": 0}

    enriched_df = invoices_service.enrich_lines_with_catalog(
        extracted_df, margin_percent=margin_percent, tenant_id=tenant_id
    )

    invoice_ids: set[str] = set()
    if "invoice_id" in enriched_df.columns:
        invoice_ids = {
            str(value).strip()
            for value in enriched_df["invoice_id"].dropna().tolist()
            if str(value).strip()
        }

    if invoice_ids and not force:
        already_processed = invoices_service.find_processed_invoice_ids(invoice_ids, tenant_id=tenant_id)
        if already_processed:
            print(
                "  → Factures déjà importées: " + ", ".join(sorted(already_processed)) +
                ". Ajoutez --force pour rejouer l'import."
            )
            return {"lines": 0, "skipped_invoices": sorted(already_processed)}

    inferred_datetime = _infer_invoice_datetime(enriched_df, invoice_date)

    invoices_service.import_catalog_from_invoice(
        enriched_df,
        supplier=supplier,
        initialize_stock=initialize_stock,
        invoice_date=inferred_datetime,
        tenant_id=tenant_id,
    )

    invoices_service.apply_invoice_import(
        enriched_df,
        username=username,
        supplier=supplier,
        invoice_date=inferred_datetime,
        tenant_id=tenant_id,
    )

    consolidation_summary = sync_invoice_dataframe(
        enriched_df,
        tenant_id=tenant_id,
        supplier_name=supplier,
        invoice_reference=_infer_invoice_reference(path),
        invoice_date=(inferred_datetime.date() if isinstance(inferred_datetime, datetime) else None),
    )

    print(
        f"  → {len(enriched_df)} ligne(s) importées, "
        f"{consolidation_summary['lines_inserted']} ligne(s) consolidées."
    )
    return {"lines": len(enriched_df), **consolidation_summary}


def main() -> None:
    parser = argparse.ArgumentParser(description="Import complet de factures fournisseurs (PDF/DOCX).")
    parser.add_argument("files", nargs="+", type=Path, help="Fichiers ou dossiers à traiter.")
    parser.add_argument("--tenant", default="epicerie", help="Code tenant (default: epicerie).")
    parser.add_argument("--supplier", default="METRO", help="Nom du fournisseur (default: METRO).")
    parser.add_argument("--username", default="import_bot", help="Utilisateur appliqué aux mouvements.")
    parser.add_argument("--margin", type=float, default=40.0, help="Marge cible (%) pour l'extraction.")
    parser.add_argument(
        "--invoice-date",
        type=str,
        default=None,
        help="Date de facture (YYYY-MM-DD). Si absent, tentative d'inférence dans le document.",
    )
    parser.add_argument(
        "--initialize-stock",
        action="store_true",
        help="Initialiser le stock lors de la création produit (passé à import_catalog_from_invoice).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Réimporte les factures déjà présentes dans processed_invoices.",
    )
    args = parser.parse_args()

    tenant_id = _resolve_tenant_id(args.tenant)
    invoice_dt = None
    if args.invoice_date:
        invoice_dt = datetime.strptime(args.invoice_date, "%Y-%m-%d")

    paths: list[Path] = []
    for src in args.files:
        if src.is_dir():
            paths.extend(sorted(p for p in src.rglob("*") if p.suffix.lower() in {".pdf", ".doc", ".docx", ".txt"}))
        elif src.exists():
            paths.append(src)

    if not paths:
        raise SystemExit("Aucun fichier valide fourni.")

    total_lines = 0
    for path in paths:
        summary = _import_single_file(
            path,
            tenant_id=tenant_id,
            supplier=args.supplier,
            username=args.username,
            margin_percent=args.margin,
            initialize_stock=args.initialize_stock,
            invoice_date=invoice_dt,
            force=args.force,
        )
        total_lines += summary.get("lines", 0)

    print(f"Import terminé : {total_lines} ligne(s) traitées.")


if __name__ == "__main__":
    main()
