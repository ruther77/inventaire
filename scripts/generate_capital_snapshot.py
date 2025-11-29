"""Script cron/launchpad pour générer un snapshot quotidien du capital."""

from __future__ import annotations

from backend.services import capital as capital_service


def main() -> None:
    capital_service.persist_daily_snapshot()


if __name__ == "__main__":
    main()
