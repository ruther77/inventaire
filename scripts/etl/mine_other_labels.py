"""Extrait le top des libellés encore classés en 'autre' et propose un JSON de mapping.

Usage :
  DATABASE_URL=postgresql+psycopg2://... .venv/bin/python scripts/mine_other_labels.py --limit 100 --json out.json
"""

from __future__ import annotations

import json
import argparse
from collections import Counter
from pathlib import Path

from sqlalchemy import text

# Permet l'import local du core/ sans dépendre du backend
import sys
import os
from pathlib import Path as P

REPO_ROOT = P(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.data_repository import get_engine


def main() -> None:
    parser = argparse.ArgumentParser(description="Top libellés classés 'autre'.")
    parser.add_argument("--limit", type=int, default=50, help="Nombre de libellés à extraire (default: 50).")
    parser.add_argument("--json", type=Path, help="Chemin de fichier pour sauvegarder le mapping (optionnel).")
    args = parser.parse_args()

    eng = get_engine()
    with eng.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT COALESCE(b.libelle_banque, t.note, '') AS libelle
                FROM finance_transaction_lines tl
                JOIN finance_transactions t ON t.id = tl.transaction_id
                JOIN finance_categories c ON c.id = tl.category_id
                LEFT JOIN finance_bank_statement_lines b
                  ON t.ref_externe LIKE 'stmtline:%'
                 AND b.id = CAST(substring(t.ref_externe FROM 'stmtline:(\\d+)') AS BIGINT)
                WHERE c.code = 'autre'
                """
            )
        ).fetchall()

    counter = Counter()
    for r in rows:
        lib = " ".join((r.libelle or "").split())
        if lib:
            counter[lib] += 1

    top = counter.most_common(args.limit)
    mapping = [{"label": k, "count": v} for k, v in top]

    for item in mapping:
        print(f"{item['count']:>5} | {item['label']}")

    if args.json:
        args.json.write_text(json.dumps(mapping, ensure_ascii=False, indent=2))
        print(f"Écrit : {args.json}")


if __name__ == "__main__":
    main()
