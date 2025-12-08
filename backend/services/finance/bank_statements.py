"""Services pour la gestion des relevés bancaires."""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import text

from core.data_repository import query_df


def search_bank_statements(
    *,
    account_id: Optional[int] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    size: int = 50,
    sort: str = "-imported_at",
) -> Dict[str, Any]:
    """Recherche paginée sur les relevés bancaires."""

    safe_page = max(1, int(page))
    safe_size = max(1, min(int(size), 500))
    offset = (safe_page - 1) * safe_size

    clauses: list[str] = []
    params: Dict[str, Any] = {}

    if account_id is not None:
        clauses.append("bs.account_id = :account_id")
        params["account_id"] = int(account_id)
    if period_start:
        clauses.append("bs.period_start >= :period_start")
        params["period_start"] = period_start
    if period_end:
        clauses.append("bs.period_end <= :period_end")
        params["period_end"] = period_end

    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses)

    # Define sort mapping
    sort_map = {
        "imported_at": "bs.imported_at ASC, bs.id ASC",
        "-imported_at": "bs.imported_at DESC, bs.id DESC",
        "period_start": "bs.period_start ASC, bs.id ASC",
        "-period_start": "bs.period_start DESC, bs.id DESC",
        "period_end": "bs.period_end ASC, bs.id ASC",
        "-period_end": "bs.period_end DESC, bs.id DESC",
        "account": "a.label ASC, bs.id ASC",
        "-account": "a.label DESC, bs.id DESC",
    }
    order_by = sort_map.get(sort, sort_map["-imported_at"])

    base_select = f"""
        FROM finance_bank_statements bs
        JOIN finance_accounts a ON a.id = bs.account_id
        {where_sql}
    """

    # Count total
    count_df = query_df(
        text(f"SELECT COUNT(*) AS total {base_select}"),
        params=params or None,
    )
    total = int(count_df.iloc[0]["total"]) if not count_df.empty else 0

    # Get data
    data_df = query_df(
        text(
            f"""
            SELECT
                bs.id,
                bs.account_id,
                a.label AS account_label,
                bs.period_start,
                bs.period_end,
                bs.source,
                bs.imported_at,
                bs.file_name,
                bs.hash,
                (
                    SELECT COUNT(*)
                    FROM finance_bank_statement_lines bsl
                    WHERE bsl.statement_id = bs.id
                ) AS line_count,
                (
                    SELECT SUM(bsl.montant)
                    FROM finance_bank_statement_lines bsl
                    WHERE bsl.statement_id = bs.id
                ) AS total_amount
            {base_select}
            ORDER BY {order_by}
            LIMIT :limit OFFSET :offset
            """
        ),
        params={**params, "limit": safe_size, "offset": offset},
    )

    items = data_df.where(data_df.notna(), None).to_dict("records") if not data_df.empty else []

    return {
        "items": items,
        "page": safe_page,
        "size": safe_size,
        "total": total,
        "sort": sort,
        "filters_applied": {
            "account_id": account_id,
            "period_start": period_start,
            "period_end": period_end,
            "status": status,
        },
    }
