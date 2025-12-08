# SPDX-License-Identifier: MIT
"""Analyse les libellés de relevés pour trouver les alias courts les plus fréquents."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import date, timedelta

from sqlalchemy import text

from core.data_repository import query_df


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regroupe les relevés par alias tronqué.")
    parser.add_argument(
        "--tenant",
        type=int,
        required=True,
        help="ID de tenant (comme dans l'interface restaurant).",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=2,
        help="Nombre d'années à analyser (défaut: 2).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Nombre d'alias les plus fréquents à afficher.",
    )
    return parser.parse_args()


def _truncate_label(label: str | None) -> str:
    if not label:
        return ""
    cleaned = re.sub(r"[^A-Z0-9 ]+", " ", label.upper())
    tokens = [token for token in cleaned.split() if token]
    if not tokens:
        return ""
    return " ".join(tokens[:3])


def _fetch_labels(tenant_id: int, cutoff_date: date) -> list[str]:
    sql = text(
        """
        SELECT COALESCE(libelle, '') AS libelle
        FROM restaurant_bank_statements
        WHERE tenant_id = :tenant
          AND date >= :cutoff
        ORDER BY date DESC
        """
    )
    df = query_df(sql, {"tenant": tenant_id, "cutoff": cutoff_date})
    return df["libelle"].tolist()


def main() -> None:
    args = _parse_args()
    cutoff = date.today() - timedelta(days=args.years * 365)
    labels = _fetch_labels(args.tenant, cutoff)

    counter = Counter(_truncate_label(label) for label in labels)
    if not counter:
        print("Aucun relevé trouvé pour cette période.")
        return

    print(f"Top {args.limit} alias (tenant {args.tenant}, {len(labels)} relevés) :\n")
    for idx, (alias, count) in enumerate(counter.most_common(args.limit), start=1):
        print(f"{idx:>2}. {alias or '(vide)'} — {count} occurrences")


if __name__ == "__main__":
    main()
