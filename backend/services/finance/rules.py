"""Services de gestion des règles de catégorisation finance."""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import text

from core.data_repository import get_engine, query_df
from backend.schemas.finance_rules import FinanceRuleCreate


def list_rules(entity_id: int | None = None, is_active: bool | None = None) -> List[dict]:
    """Liste les règles de catégorisation.

    Si entity_id est fourni, retourne les règles de cette entité ET les règles
    partagées (entity_id = NULL) accessibles par toutes les entités.
    """
    clauses: List[str] = []
    params: Dict[str, Any] = {}
    if entity_id is not None:
        # Inclure les règles de l'entité + les règles partagées (entity_id IS NULL)
        clauses.append("(r.entity_id = :entity_id OR r.entity_id IS NULL)")
        params["entity_id"] = int(entity_id)
    if is_active is not None:
        clauses.append("r.is_active = :is_active")
        params["is_active"] = bool(is_active)
    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses)
    df = query_df(
        text(
            f"""
            SELECT
              r.id,
              r.entity_id,
              r.category_id,
              r.name,
              r.keywords,
            r.apply_to_autre_only,
            r.is_active,
            r.amount_min,
            r.amount_max,
            r.regex_pattern,
            r.created_at,
            r.updated_at,
            c.name AS category_name,
            c.code AS category_code
            FROM finance_rules r
            LEFT JOIN finance_categories c ON c.id = r.category_id
            {where_sql}
            ORDER BY r.updated_at DESC NULLS LAST, r.id DESC
            """
        ),
        params=params or None,
    )
    if df.empty:
        return []
    # Convertir les colonnes datetime en strings ISO pour la sérialisation JSON
    for col in ["created_at", "updated_at"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x.isoformat() if hasattr(x, "isoformat") else x)
    return df.where(df.notna(), None).to_dict("records")


def create_rule(payload: FinanceRuleCreate) -> dict:
    eng = get_engine()
    with eng.begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO finance_rules (entity_id, category_id, name, keywords, apply_to_autre_only, is_active, amount_min, amount_max, regex_pattern)
                VALUES (:entity_id, :category_id, :name, :keywords, :apply_to_autre_only, :is_active, :amount_min, :amount_max, :regex_pattern)
                RETURNING id, entity_id, category_id, name, keywords, apply_to_autre_only, is_active, amount_min, amount_max, regex_pattern, created_at, updated_at
                """
            ),
            {
                "entity_id": payload.entity_id,
                "category_id": payload.category_id,
                "name": payload.name,
                "keywords": payload.keywords,
                "apply_to_autre_only": payload.apply_to_autre_only,
                "is_active": payload.is_active,
                "amount_min": payload.amount_min,
                "amount_max": payload.amount_max,
                "regex_pattern": payload.regex_pattern,
            },
        ).fetchone()
    return dict(row._mapping)


def update_rule(rule_id: int, fields: Dict[str, Any]) -> dict:
    allowed = {"name", "keywords", "apply_to_autre_only", "is_active", "category_id", "amount_min", "amount_max", "regex_pattern"}
    updates = []
    params: Dict[str, Any] = {"id": int(rule_id)}
    for key, value in fields.items():
        if key in allowed:
            updates.append(f"{key} = :{key}")
            params[key] = value
    if not updates:
        raise ValueError("Aucun champ modifiable fourni.")
    sql = text(
        f"""
        UPDATE finance_rules
        SET {', '.join(updates)}, updated_at = now()
        WHERE id = :id
        RETURNING id, entity_id, category_id, name, keywords, apply_to_autre_only, is_active, created_at, updated_at
        """
    )
    eng = get_engine()
    with eng.begin() as conn:
        row = conn.execute(sql, params).fetchone()
        if not row:
            raise ValueError("Règle introuvable.")
    return dict(row._mapping)


def delete_rule(rule_id: int) -> dict:
    eng = get_engine()
    with eng.begin() as conn:
        row = conn.execute(
            text(
                "DELETE FROM finance_rules WHERE id = :id RETURNING id"
            ),
            {"id": int(rule_id)},
        ).fetchone()
        if not row:
            raise ValueError("Règle introuvable.")
    return {"id": rule_id, "deleted": True}


def record_import(account_id: int, file_name: str, summary: dict | None, error: str | None) -> None:
    """Enregistre un import (succès/échec) dans finance_imports."""

    status = "DONE" if error is None else "ERROR"
    inserted = summary.get("inserted") if summary else None
    total = summary.get("total") if summary else None
    eng = get_engine()
    with eng.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO finance_imports (account_id, file_name, source, inserted, total, status, error)
                VALUES (:account_id, :file_name, :source, :inserted, :total, :status, :error)
                """
            ),
            {
                "account_id": account_id,
                "file_name": file_name,
                "source": "IMPORT",
                "inserted": inserted,
                "total": total,
                "status": status,
                "error": error,
            },
        )
