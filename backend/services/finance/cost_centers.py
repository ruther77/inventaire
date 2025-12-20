"""Services de consultation et création des centres de coûts finance."""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import text

from core.data_repository import get_engine, query_df


def create_cost_center(entity_id: int, code: str, name: str) -> dict:
    """Crée un nouveau centre de coûts finance et le retourne."""
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO finance_cost_centers (entity_id, code, name, is_active)
                VALUES (:entity_id, :code, :name, true)
                RETURNING id, entity_id, code, name, is_active
                """
            ),
            {"entity_id": entity_id, "code": code, "name": name},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else {}


def list_cost_centers(entity_id: int | None = None, is_active: bool | None = None) -> List[dict]:
    """Retourne les centres de coûts finance disponibles, optionnellement filtrés.

    Si entity_id est fourni, retourne les centres de coûts de cette entité ET les centres
    partagés (entity_id = NULL) accessibles par toutes les entités.
    """

    clauses: List[str] = []
    params: Dict[str, Any] = {}
    if entity_id is not None:
        # Inclure les centres de l'entité + les centres partagés (entity_id IS NULL)
        clauses.append("(entity_id = :entity_id OR entity_id IS NULL)")
        params["entity_id"] = int(entity_id)
    if is_active is not None:
        clauses.append("is_active = :is_active")
        params["is_active"] = is_active

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    df = query_df(
        text(
            f"""
            SELECT id, entity_id, code, name, is_active
            FROM finance_cost_centers
            {where_sql}
            ORDER BY entity_id NULLS LAST, code
            """
        ),
        params=params or None,
    )
    return df.where(df.notna(), None).to_dict("records") if not df.empty else []
