#!/usr/bin/env python3
"""
Génère un SQL d'insertion pour les factures Eurociel à partir de docs/eurociel_factures_enriched.csv.

Tables cibles :
- produits (pour les NEW)
- produits_barcodes (placeholder 5 chiffres, is_principal=true)
- produits_price_history (quantités réelles, prix_achat HT)
- processed_invoices (une entrée par facture FA..., line_count)

Hypothèses :
- fournisseur = 'EUROCIEL'
- tenant_id = 1
- Montant_HT_calc = prix_unitaire * quantité (colonne Prix_achat_HT déjà unitaire)
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
import sys
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "eurociel_factures_enriched.csv"
OUT = ROOT / "docs" / "insert_eurociel_factures.sql"
sys.path.append(str(ROOT))
from scripts.reclassify_products import normalize_label  # type: ignore

TENANT_ID = 1
SUPPLIER = "EUROCIEL"


def main() -> None:
    with SRC.open() as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)

    # Produits à créer (norm -> data)
    products: Dict[str, Tuple[str, str, float, str]] = {}
    for row in rows:
        if row["Produit_ID"] == "NEW":
            norm = normalize_label(row["Produit"])
            products[norm] = (
                row["Produit"],
                row["Categorie"],
                float(row["TVA"]),
                row["EAN"],
            )

    data_rows = []
    for norm, (lib, cat, tva, code) in products.items():
        lib_sql = lib.replace("'", "''")
        cat_sql = cat.replace("'", "''")
        norm_sql = norm.replace("'", "''")
        data_rows.append(f"('{norm_sql}', '{lib_sql}', '{cat_sql}', {tva}, {TENANT_ID})")

    # Barcodes pour NEW uniquement (code déjà dans EAN)
    inserts_barcode = []
    for norm, (lib, cat, tva, code) in products.items():
        norm_sql = norm.replace("'", "''")
        pid_placeholder = f"(SELECT id FROM new_products WHERE norm = '{norm_sql}')"
        inserts_barcode.append(f"({pid_placeholder}, {TENANT_ID}, '{code}', true)")

    # Price history
    inserts_ph = []
    for row in rows:
        qty = row["Qté"].replace(",", ".")
        prix = row["Prix_achat_HT"]
        code = row["EAN"]
        invoice = row["invoice"]
        raw_date = row["invoice_date"] or "2025-12-03"
        # Normalise date (jj/mm/aa -> yyyy-mm-dd)
        try:
            date = datetime.strptime(raw_date, "%d/%m/%y").strftime("%Y-%m-%d")
        except Exception:
            date = raw_date
        inserts_ph.append(
            f"('{code}', {prix}, {qty}, '{date}', '{invoice}')"
        )

    # processed_invoices
    per_invoice = defaultdict(int)
    per_file = defaultdict(set)
    per_date = {}
    for row in rows:
        inv = row["invoice"]
        per_invoice[inv] += 1
        per_file[inv].add(row["file"])
        if inv not in per_date and row["invoice_date"]:
            try:
                per_date[inv] = datetime.strptime(row["invoice_date"], "%d/%m/%y").strftime("%Y-%m-%d")
            except Exception:
                per_date[inv] = "2025-12-03"
        elif inv not in per_date:
            per_date[inv] = "2025-12-03"

    processed_values = []
    for inv, count in sorted(per_invoice.items()):
        files = ",".join(sorted(per_file[inv]))
        inv_date = per_date.get(inv, "2025-12-03")
        processed_values.append(f"('{inv}', '{inv_date}', {count}, '{files}')")

    sql_lines = []
    sql_lines.append("BEGIN;")
    sql_lines.append(
        "-- Produits NEW Eurociel (idempotent)\n"
        "WITH data(norm, nom, categorie, tva, tenant_id) AS (\n"
        "  VALUES\n    "
        + ",\n    ".join(data_rows)
        + "\n),\n"
        "ins AS (\n"
        "  INSERT INTO produits (nom, categorie, tva, tenant_id)\n"
        "  SELECT nom, categorie, tva, tenant_id FROM data\n"
        "  ON CONFLICT DO NOTHING\n"
        "  RETURNING id, nom\n"
        "),\n"
        "ins_norm AS (\n"
        "  SELECT i.id, d.norm\n"
        "  FROM ins i\n"
        "  JOIN data d ON d.nom = i.nom\n"
        "),\n"
        "existing AS (\n"
        "  SELECT p.id, upper(d.norm) AS norm\n"
        "  FROM data d JOIN produits p ON lower(p.nom) = lower(d.nom)\n"
        "),\n"
        "new_products AS (\n"
        "  SELECT id, norm FROM ins_norm\n"
        "  UNION ALL\n"
        "  SELECT id, norm FROM existing\n"
        ")\n"
        "INSERT INTO produits_barcodes (produit_id, tenant_id, code, is_principal)\n"
        "VALUES\n    "
        + ",\n    ".join(inserts_barcode)
        + "\nON CONFLICT DO NOTHING;\n"
    )

    sql_lines.append(
        "-- Price history\n"
        "INSERT INTO produits_price_history (code, fournisseur, prix_achat, quantite, facture_date, source_context, tenant_id)\n"
        "VALUES\n    "
        + ",\n    ".join(
            f"('{code}', '{SUPPLIER}', {prix}, {qty}, '{date_iso}'::timestamptz, '{invoice}', {TENANT_ID})"
            for code, prix, qty, date_iso, invoice in (
                (
                    row["EAN"],
                    row["Prix_achat_HT"],
                    row["Qté"].replace(",", "."),
                    datetime.strptime(row["invoice_date"], "%d/%m/%y").strftime("%Y-%m-%d")
                    if row["invoice_date"]
                    else "2025-12-03",
                    row["invoice"],
                )
                for row in rows
            )
        )
        + ";\n"
    )

    sql_lines.append(
        "-- processed_invoices avec préfixe fournisseur (EUR-XXX)\n"
        "WITH data(inv_raw, inv_date, line_count, file_path) AS (\n"
        "  VALUES\n    "
        + ",\n    ".join(processed_values)
        + "\n), base AS (\n"
        "  SELECT COALESCE(MAX(REGEXP_REPLACE(invoice_id, '[^0-9]', '', 'g')::int), 0) AS last_num\n"
        "  FROM processed_invoices WHERE supplier = '" + SUPPLIER + "'\n"
        "), numbered AS (\n"
        "  SELECT inv_raw, inv_date, line_count, file_path,\n"
        "         ROW_NUMBER() OVER (ORDER BY inv_raw) AS rn\n"
        "  FROM data\n"
        ")\n"
        "INSERT INTO processed_invoices (tenant_id, invoice_id, supplier, facture_date, line_count, file_path)\n"
        "SELECT "
        f"{TENANT_ID}, "
        "'EUR-' || (base.last_num + n.rn) AS invoice_id, "
        f"'{SUPPLIER}', "
        "n.inv_date::timestamptz, n.line_count, n.file_path\n"
        "FROM numbered n CROSS JOIN base\n"
        "ON CONFLICT (tenant_id, invoice_id) DO NOTHING;\n"
    )

    sql_lines.append("COMMIT;")
    OUT.write_text("\n".join(sql_lines))
    print(f"SQL généré dans {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
from datetime import datetime
