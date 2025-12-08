"""Importe des relevés bancaires PDF (LCL) dans restaurant_bank_statements."""

from __future__ import annotations

import argparse
from pathlib import Path

from core.tenant_service import ensure_tenants_table
from backend.services import restaurant as restaurant_service


def _iter_files(sources: list[Path]) -> list[Path]:
    pdfs: list[Path] = []
    for src in sources:
        if src.is_dir():
            pdfs.extend(sorted(p for p in src.rglob("*.pdf") if p.is_file()))
        elif src.is_file() and src.suffix.lower() == ".pdf":
            pdfs.append(src)
    return pdfs


def _get_tenant_id(code: str) -> int:
    from sqlalchemy import text
    from core.data_repository import get_engine

    eng = get_engine()
    ensure_tenants_table()
    with eng.begin() as conn:
        row = conn.execute(text("SELECT id FROM tenants WHERE code = :code"), {"code": code}).fetchone()
        if not row:
            raise RuntimeError(f"Tenant '{code}' introuvable.")
        return int(row.id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Importe un ou plusieurs relevés bancaires PDF (format LCL).")
    parser.add_argument("--account", required=True, help="Code du compte (ex: 'incontournable' ou 'noutam').")
    parser.add_argument("--tenant", default="restaurant", help="Code du tenant (défaut: restaurant).")
    parser.add_argument("paths", nargs="+", type=Path, help="Fichiers ou dossiers contenant les PDF.")
    args = parser.parse_args()

    pdf_files = _iter_files(args.paths)
    if not pdf_files:
        raise SystemExit("Aucun fichier PDF trouvé.")

    tenant_id = _get_tenant_id(args.tenant)
    inserted_total = 0
    detected_total = 0
    for pdf in pdf_files:
        with pdf.open("rb") as fp:
            summary = restaurant_service.import_bank_statements_from_pdf(
                tenant_id=tenant_id,
                account=args.account,
                pdf_bytes=fp.read(),
            )
        inserted_total += summary["inserted"]
        detected_total += summary["total"]
        duplicates = summary["total"] - summary["inserted"]
        print(f"{pdf.name}: {summary['inserted']} lignes ajoutées ({duplicates} doublon(s) ignoré(s)).")

    print(f"Terminé : {inserted_total} mouvements insérés ({detected_total} détectés).")


if __name__ == "__main__":
    main()
