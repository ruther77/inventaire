"""Services bas niveau pour les rapprochements banque ↔ transaction."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text

from core.data_repository import exec_sql_return_id, get_engine


def create_reconciliation(
    statement_line_id: int,
    transaction_id: int,
    *,
    status: str = "AUTO",
    created_by: int | None = None,
) -> dict[str, Any]:
    rec_id = exec_sql_return_id(
        text(
            """
            INSERT INTO finance_reconciliations (
                statement_line_id,
                transaction_id,
                status,
                created_by
            ) VALUES (
                :statement_line_id,
                :transaction_id,
                :status,
                :created_by
            )
            RETURNING id
            """
        ),
        params={
            "statement_line_id": int(statement_line_id),
            "transaction_id": int(transaction_id),
            "status": status,
            "created_by": created_by,
        },
    )
    return {"id": rec_id, "statement_line_id": statement_line_id, "transaction_id": transaction_id}


def delete_reconciliation(reconciliation_id: int) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM finance_reconciliations WHERE id = :id"),
            {"id": int(reconciliation_id)},
        )
        if result.rowcount == 0:
            raise ValueError("Rapprochement introuvable.")
