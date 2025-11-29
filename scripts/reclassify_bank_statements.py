"""Reclasse les relevés bancaires existants avec les règles actuelles."""

from __future__ import annotations

import argparse
from typing import Iterable

from backend.services import restaurant as restaurant_service


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Réexécute la reconnaissance de catégories sur les relevés bancaires.")
    parser.add_argument("--tenant", type=int, required=True, help="ID du tenant à traiter.")
    parser.add_argument("--account", type=str, help="Filtre sur le compte bancaire (optionnel).")
    parser.add_argument("--dry-run", action="store_true", help="Affiche les modifications sans les appliquer.")
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="Reclasse uniquement les lignes sans catégorie déjà définie.",
    )
    return parser.parse_args()


def _filter_statements(statements: Iterable[dict[str, object]], only_missing: bool) -> list[dict[str, object]]:
    if only_missing:
        return [stmt for stmt in statements if not stmt.get("categorie")]
    return list(statements)


def main() -> None:
    args = _parse_args()
    statements = restaurant_service.list_bank_statements(args.tenant, account=args.account)
    candidates = _filter_statements(statements, args.only_missing)

    if not candidates:
        print("Aucun relevé à reclassement.")
        return

    print(f"{len(candidates)} relevé(s) seront analysés ({'dry-run' if args.dry_run else 'maj'})")
    updates = 0
    for stmt in candidates:
        new_category = restaurant_service._guess_category(stmt.get("libelle"), stmt.get("type") or "Sortie")
        old = stmt.get("categorie") or ""
        new = new_category or ""
        if old.strip().upper() == new.strip().upper():
            continue
        print(f"[{stmt['id']}] {stmt.get('libelle')}: {old or '(vide)'} → {new or '(vide)'}")
        updates += 1
        if not args.dry_run:
            restaurant_service.update_bank_statement(
                args.tenant,
                stmt["id"],
                {"categorie": new_category},
            )

    print(f"{updates} relevé(s) recatégorisé(s).")


if __name__ == "__main__":
    main()
