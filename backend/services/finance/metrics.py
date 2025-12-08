"""Services de métriques/logs import/reco (simplifié)."""

from __future__ import annotations

import logging
from typing import Any, Dict

from sqlalchemy import text

from core.data_repository import get_engine

LOGGER = logging.getLogger(__name__)


def record_reco_run(summary: Dict[str, Any]) -> None:
    LOGGER.info("Reco run: %s", summary)


def record_import_metrics(account_id: int, inserted: int | None, total: int | None, status: str, error: str | None) -> None:
    LOGGER.info("Import account=%s status=%s inserted=%s total=%s error=%s", account_id, status, inserted, total, error)


def increment_import_progress(import_id: int, inserted: int, total: int) -> None:
    eng = get_engine()
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE finance_imports
                SET inserted = :inserted,
                    total = :total,
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {"id": import_id, "inserted": inserted, "total": total},
        )
