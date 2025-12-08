"""Importe les catégories du mapping fournisseur → catégorie dans le module charges Restaurant HQ."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from sqlalchemy import text

from core.data_repository import get_engine
from core.tenant_service import ensure_tenants_table


def _fetch_tenant_id(conn, code: str) -> int:
    row = conn.execute(text("SELECT id FROM tenants WHERE code = :code"), {"code": code}).fetchone()
    if not row:
        raise RuntimeError(f"Tenant '{code}' introuvable.")
    return int(row.id)


def _read_categories(source: Path) -> set[str]:
    categories: set[str] = set()
    with source.open(encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if "category" not in reader.fieldnames:
            raise ValueError("Le fichier CSV doit contenir une colonne 'category'.")
        for row in reader:
            value = (row.get("category") or "").strip()
            if value:
                categories.add(value)
    return categories


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ajoute/actualise les catégories Restaurant HQ à partir d’un mapping fournisseur → catégorie."
    )
    parser.add_argument("csv", type=Path, help="Chemin du fichier CSV (ex: docs/invoices/vendor_category_mapping.csv).")
    parser.add_argument("--tenant", default="restaurant", help="Code du tenant Restaurant HQ.")
    args = parser.parse_args()

    if not args.csv.exists():
        raise FileNotFoundError(args.csv)

    categories = _read_categories(args.csv)
    if not categories:
        print("Aucune catégorie détectée.")
        return

    ensure_tenants_table()
    engine = get_engine()
    with engine.begin() as conn:
        tenant_id = _fetch_tenant_id(conn, args.tenant)
        inserted = 0
        for label in sorted(categories):
            row = conn.execute(
                text(
                    """
                    INSERT INTO restaurant_depense_categories (tenant_id, nom)
                    VALUES (:tenant_id, :nom)
                    ON CONFLICT (tenant_id, nom) DO NOTHING
                    RETURNING id
                    """
                ),
                {"tenant_id": tenant_id, "nom": label},
            ).fetchone()
            if row:
                inserted += 1
    print(f"{inserted} catégorie(s) importée(s) pour le tenant '{args.tenant}'.")


if __name__ == "__main__":
    main()
