# SPDX-License-Identifier: MIT
"""CLI helper to turn bank statement lines into restaurant charges."""

from __future__ import annotations

import argparse
import sys
from typing import Iterable

from backend.services import restaurant as restaurant_service


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transforme les relevés bancaires importés en charges restaurant."
    )
    parser.add_argument("--tenant", type=int, required=True, help="ID du tenant à traiter.")
    parser.add_argument("--account", type=str, help="Filtre sur un compte bancaire précis.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Nombre maximum d'entrées à traiter (par défaut : toutes).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche les lignes qui seraient traitées sans créer de charge.",
    )
    return parser.parse_args()


def _filter_statements(statements: Iterable[dict[str, object]], limit: int | None) -> list[dict[str, object]]:
    pending = [stmt for stmt in statements if not stmt.get("depense_id")]
    if limit is not None:
        pending = pending[:limit]
    return pending


def main() -> None:
    args = _parse_args()
    statements = restaurant_service.list_bank_statements(args.tenant, account=args.account)
    pending = _filter_statements(statements, args.limit)

    if not pending:
        print("Aucun relevé bancaire en attente de conversion.")
        sys.exit(0)

    print(f"{len(pending)} relevé(s) sans charge détecté(s).")
    if args.dry_run:
        for stmt in pending:
            print(f"- {stmt['date']} · {stmt['libelle']} ({stmt['montant']} €)")
        sys.exit(0)

    converted = 0
    for stmt in pending:
        try:
            restaurant_service.create_expense_from_bank_statement(args.tenant, stmt["id"], {})
        except Exception as exc:  # pragma: no cover - script only
            print(f"Erreur sur la ligne #{stmt['id']}: {exc}")
        else:
            converted += 1
            print(f"Charge générée pour le relevé #{stmt['id']} ({stmt['libelle']}).")

    print(f"{converted} charge(s) créées.")


if __name__ == "__main__":
    main()
