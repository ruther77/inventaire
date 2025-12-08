"""Orchestre l'import PDF → création de charges → reclassification."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from sqlalchemy import text

from backend.services import restaurant as restaurant_service
from core.data_repository import get_engine
from core.tenant_service import ensure_tenants_table

def _iter_pdfs(sources: Iterable[Path]) -> list[Path]:
    pdfs: list[Path] = []
    for src in sources:
        if src.is_dir():
            pdfs.extend(sorted(p for p in src.rglob("*.pdf") if p.is_file()))
        elif src.is_file() and src.suffix.lower() == ".pdf":
            pdfs.append(src)
    return pdfs


def _tenant_id(code: str) -> int:
    eng = get_engine()
    ensure_tenants_table()
    with eng.begin() as conn:
        row = conn.execute(text("SELECT id FROM tenants WHERE code = :code"), {"code": code}).fetchone()
    if not row:
        raise RuntimeError(f"Tenant '{code}' introuvable.")
    return int(row.id)


def _import_pdfs(tenant_id: int, account: str, pdfs: Iterable[Path]) -> tuple[int, int]:
    inserted = 0
    detected = 0
    for pdf in pdfs:
        with pdf.open("rb") as fp:
            summary = restaurant_service.import_bank_statements_from_pdf(
                tenant_id=tenant_id, account=account, pdf_bytes=fp.read()
            )
        inserted += summary["inserted"]
        detected += summary["total"]
        dups = summary["total"] - summary["inserted"]
        print(f"{pdf.name}: {summary['inserted']} lignes insérées ({dups} doublon(s)).")
    return inserted, detected


def _create_charges(tenant_id: int, account: str) -> int:
    entries = restaurant_service.list_bank_statements(tenant_id, account=account)
    pending = [row for row in entries if not row.get("depense_id")]
    created = 0
    for stmt in pending:
        try:
            restaurant_service.create_expense_from_bank_statement(tenant_id, stmt["id"], {})
        except Exception as exc:  # pragma: no cover - script only
            print(f"Erreur charge #{stmt['id']}: {exc}")
        else:
            created += 1
    return created


def _reclassify(tenant_id: int, account: str | None) -> int:
    statements = restaurant_service.list_bank_statements(tenant_id, account=account)
    updated = 0
    for stmt in statements:
        new_cat = restaurant_service._guess_category(stmt.get("libelle"), stmt.get("type") or "Sortie")
        if (stmt.get("categorie") or "").strip().upper() == (new_cat or "").strip().upper():
            continue
        restaurant_service.update_bank_statement(tenant_id, stmt["id"], {"categorie": new_cat})
        updated += 1
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Flux complet : PDF → charges → catégories.")
    parser.add_argument("--tenant", default="restaurant", help="Code du tenant (default: restaurant).")
    parser.add_argument("--account", required=True, help="Compte bancaire (format utilisé par l'app).")
    parser.add_argument("--pdf", nargs="+", type=Path, required=True, help="Fichiers ou dossiers PDF.")
    parser.add_argument("--skip-charges", action="store_true", help="Ne pas générer les charges.")
    parser.add_argument("--skip-reclassify", action="store_true", help="Ne pas relancer la reclassification.")
    args = parser.parse_args()

    tenant_id = _tenant_id(args.tenant)
    pdfs = _iter_pdfs(args.pdf)
    if not pdfs:
        raise SystemExit("Aucun PDF trouvé.")

    print("Import des PDF...")
    inserted, detected = _import_pdfs(tenant_id, args.account, pdfs)
    print(f"Import terminé : {inserted}/{detected} lignes insérées.")

    if not args.skip_charges:
        print("Création automatique des charges...")
        created = _create_charges(tenant_id, args.account)
        print(f"{created} charges créées.")

    if not args.skip_reclassify:
        print("Reclassification des catégories...")
        updated = _reclassify(tenant_id, args.account)
        print(f"{updated} relevé(s) recatégorisé(s).")


if __name__ == "__main__":
    main()
