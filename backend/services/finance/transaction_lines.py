from __future__ import annotations

from typing import Iterable, Dict, Any
from sqlalchemy import text
from core.data_repository import get_engine
from core.finance.transaction_line_defaults import fill_missing_transaction_lines


def mark_incomplete(transaction_ids: Iterable[int]) -> Dict[str, Any]:
    """Crée des lignes par défaut et marque les transactions comme incompletes via data_quality_flags."""
    ids = [int(x) for x in transaction_ids if x is not None]
    if not ids:
        return {"created": 0}
    created = fill_missing_transaction_lines(ids)["created"]

    engine = get_engine()
    with engine.begin() as conn:
        for tx_id in ids:
            conn.execute(
                text(
                    """
                    INSERT INTO data_quality_flags (table_name, row_id, issue, details)
                    VALUES ('finance_transactions', :row_id, 'INCOMPLETE_LINE', jsonb_build_object('transaction_id', :row_id))
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"row_id": str(tx_id)},
            )
    return {"created": created}
