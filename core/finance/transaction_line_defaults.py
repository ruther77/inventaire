from __future__ import annotations

from typing import Dict, Any, Iterable
from sqlalchemy import text
from core.data_repository import get_engine


def fill_missing_transaction_lines(tx_ids: Iterable[int]) -> Dict[str, Any]:
    """Crée des transaction_lines vides pour les transactions données (si absents)."""
    ids = [int(x) for x in tx_ids if x is not None]
    if not ids:
        return {"created": 0}
    engine = get_engine()
    created = 0
    with engine.begin() as conn:
        existing = conn.execute(
            text(
                "SELECT transaction_id FROM finance_transaction_lines WHERE transaction_id = ANY(:ids)"
            ),
            {"ids": ids},
        ).fetchall()
        existing_ids = {int(row.transaction_id) for row in existing}
        missing = [i for i in ids if i not in existing_ids]
        for tx_id in missing:
            conn.execute(
                text(
                    """
                    INSERT INTO finance_transaction_lines (transaction_id, montant_ht, tva_pct, cost_center_id)
                    VALUES (:tx_id, 0, 0, NULL)
                    """
                ),
                {"tx_id": tx_id},
            )
            created += 1
    return {"created": created}
