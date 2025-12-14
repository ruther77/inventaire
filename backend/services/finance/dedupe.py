from __future__ import annotations

from typing import Dict, List
from sqlalchemy import text
from core.data_repository import get_engine


def dedupe_transactions() -> Dict[str, List[int]]:
    """Supprime les doublons finance_transactions (date_operation+amount) en gardant le plus petit id."""
    engine = get_engine()
    deleted: list[int] = []
    with engine.begin() as conn:
        dup_rows = conn.execute(
            text(
                """
                SELECT date_operation, amount, array_agg(id ORDER BY id) AS ids
                FROM finance_transactions
                GROUP BY date_operation, amount
                HAVING count(*) > 1
                """
            )
        ).fetchall()
        for row in dup_rows:
            ids = list(row.ids)
            keep = ids.pop(0)
            if ids:
                conn.execute(text("DELETE FROM finance_transactions WHERE id = ANY(:ids)"), {"ids": ids})
                deleted.extend(ids)
    return {"deleted": deleted}


def dedupe_statement_lines() -> Dict[str, List[int]]:
    """Supprime les doublons finance_bank_statement_lines (date_operation+montant) en gardant le plus petit id."""
    engine = get_engine()
    deleted: list[int] = []
    with engine.begin() as conn:
        dup_rows = conn.execute(
            text(
                """
                SELECT date_operation, montant, array_agg(id ORDER BY id) AS ids
                FROM finance_bank_statement_lines
                GROUP BY date_operation, montant
                HAVING count(*) > 1
                """
            )
        ).fetchall()
        for row in dup_rows:
            ids = list(row.ids)
            keep = ids.pop(0)
            if ids:
                conn.execute(text("DELETE FROM finance_bank_statement_lines WHERE id = ANY(:ids)"), {"ids": ids})
                deleted.extend(ids)
    return {"deleted": deleted}
