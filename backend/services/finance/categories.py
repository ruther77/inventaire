"""Services de consultation des catégories finance."""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import text

from core.data_repository import get_engine, query_df


def create_category(entity_id: int, code: str, name: str, type_: str = "EXPENSE") -> dict:
    """Crée une nouvelle catégorie finance et la retourne."""
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO finance_categories (entity_id, code, name, type)
                VALUES (:entity_id, :code, :name, :type)
                RETURNING id, entity_id, code, name, type
                """
            ),
            {"entity_id": entity_id, "code": code, "name": name, "type": type_},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else {}


def list_categories(entity_id: int | None = None, is_active: bool | None = None) -> List[dict]:
    """Retourne les catégories finance disponibles, optionnellement filtrées.

    Si entity_id est fourni, retourne les catégories de cette entité ET les catégories
    partagées (entity_id = NULL) accessibles par toutes les entités.
    """

    clauses: List[str] = []
    params: Dict[str, Any] = {}
    if entity_id is not None:
        # Inclure les catégories de l'entité + les catégories partagées (entity_id IS NULL)
        clauses.append("(entity_id = :entity_id OR entity_id IS NULL)")
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
