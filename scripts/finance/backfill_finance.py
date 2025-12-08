"""Backfill des données restaurant vers le modèle finance_* (réutilise le mapper core)."""

from backend.services.mappers.restaurant_to_finance import run_backfill


def main() -> None:
    run_backfill()


if __name__ == "__main__":
    main()
