"""Services de consultation des imports finance (statut, erreurs)."""

from __future__ import annotations

from typing import List

from sqlalchemy import text

from core.data_repository import get_engine, query_df


def list_imports() -> List[dict]:
    df = query_df(
        text(
            """
            SELECT
              i.id,
              i.account_id,
              a.label AS account_label,
              i.file_name,
              i.source,
              i.inserted,
              i.total,
              i.status,
              i.error,
              i.created_at,
              i.updated_at
            FROM finance_imports i
            LEFT JOIN finance_accounts a ON a.id = i.account_id
            ORDER BY i.created_at DESC
            LIMIT 200
            """
        )
    )
    return df.where(df.notna(), None).to_dict("records") if not df.empty else []


def update_import_progress(import_id: int, inserted: int, total: int | None = None, status: str | None = None) -> None:
    eng = get_engine()
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE finance_imports
                SET inserted = :inserted,
                    total = COALESCE(:total, total),
                    status = COALESCE(:status, status),
                    updated_at = now()
                WHERE id = :id
                """
            ),
            {"id": import_id, "inserted": inserted, "total": total, "status": status},
        )
