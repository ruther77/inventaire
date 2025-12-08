"""Services de consultation des catégories finance."""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import text

from core.data_repository import query_df


def list_categories(entity_id: int | None = None, is_active: bool | None = None) -> List[dict]:
    """Retourne les catégories finance disponibles, optionnellement filtrées."""

    clauses: List[str] = []
    params: Dict[str, Any] = {}
    if entity_id is not None:
        clauses.append("entity_id = :entity_id")
        params["entity_id"] = int(entity_id)
    # Certains schémas n'ont pas encore la colonne is_active; on ignore le filtre pour compatibilité.
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    df = query_df(
        text(
            f"""
            SELECT id, entity_id, code, name, type
            FROM finance_categories
            {where_sql}
            ORDER BY entity_id NULLS LAST, code
            """
        ),
        params=params or None,
    )
    return df.where(df.notna(), None).to_dict("records") if not df.empty else []
