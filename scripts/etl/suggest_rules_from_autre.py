"""Analyse les libellés encore classés en 'autre' et propose un regroupement normalisé.

- Normalisation avec suppression d'accents, majuscules, suppression des chiffres/ponctuations.
- Regroupe par clé canonique (tokens tronqués à 6 caractères pour gérer abréviations).
- Affiche le top N (défaut 50) et peut écrire un JSON exploitable pour créer des règles.

Usage :
  DATABASE_URL=postgresql+psycopg2://... .venv/bin/python scripts/suggest_rules_from_autre.py --limit 50 --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from sqlalchemy import text

# Import du core sans dépendre du backend complet
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.data_repository import get_engine  # type: ignore  # noqa: E402


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def canonical(label: str) -> str:
    """Normalise un libellé pour regrouper les abréviations/troncatures."""
    label = strip_accents(label.upper())
    # Remplacer chiffres et ponctuation par espace
    label = re.sub(r"[0-9]", " ", label)
    label = re.sub(r"[^A-Z]+", " ", label)
    tokens = [tok for tok in label.split() if tok]
    # Tronquer chaque token à 6 caractères pour rapprocher les abréviations
    tokens = [tok[:6] for tok in tokens]
    # Limiter la clé à 5 tokens pour éviter des clés trop longues
    return " ".join(tokens[:5])


def main() -> None:
    parser = argparse.ArgumentParser(description="Top des libellés en catégorie 'autre'.")
    parser.add_argument("--limit", type=int, default=50, help="Nombre d'entrées à afficher (défaut: 50).")
    parser.add_argument("--json", type=Path, help="Fichier JSON de sortie (optionnel).")
    args = parser.parse_args()

    eng = get_engine()
    with eng.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT COALESCE(b.libelle_banque, t.note, '') AS label
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
    examples: Dict[str, List[str]] = defaultdict(list)
    for r in rows:
        raw = " ".join((r.label or "").split())
        if not raw:
            continue
        key = canonical(raw)
        counter[key] += 1
        if len(examples[key]) < 3:
            examples[key].append(raw)

    top = counter.most_common(args.limit)
    for key, count in top:
        sample = "; ".join(examples[key])
        print(f"{count:>5} | {key} | {sample}")

    if args.json:
        payload = [{"key": k, "count": v, "examples": examples[k]} for k, v in top]
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"Écrit : {args.json}")


if __name__ == "__main__":
    main()
