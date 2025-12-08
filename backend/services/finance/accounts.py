"""Services pour la gestion des comptes financiers."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import text

from core.data_repository import exec_sql_return_id, query_df
from backend.schemas.finance import FinanceAccountCreate


def _fetch_entity_currency(entity_id: int) -> Optional[str]:
    df = query_df(
        text("SELECT currency FROM finance_entities WHERE id = :entity_id"),
        params={"entity_id": int(entity_id)},
    )
    if df.empty:
        return None
    value = df.iloc[0].currency
    return str(value) if value else None


def create_account(payload: FinanceAccountCreate) -> dict[str, Any]:
    """Crée un compte financier en validant la cohérence devise/entité."""

    expected_currency = _fetch_entity_currency(payload.entity_id)
    if expected_currency and expected_currency.upper() != payload.currency.upper():
        raise ValueError(f"Devise incohérente avec l'entité (attendu {expected_currency}).")

    account_id = exec_sql_return_id(
        text(
            """
            INSERT INTO finance_accounts (
                entity_id,
                type,
                label,
                iban,
                bic,
                currency,
                is_active,
                metadata
            ) VALUES (
                :entity_id,
                :type,
                :label,
                :iban,
                :bic,
                :currency,
                :is_active,
                :metadata
            )
            RETURNING id
            """
        ),
        params=payload.dict(),
    )
    return {
        "id": account_id,
        "entity_id": payload.entity_id,
        "type": payload.type,
        "label": payload.label,
        "currency": payload.currency,
        "is_active": payload.is_active,
        "iban": payload.iban,
    }


def list_accounts(entity_id: Optional[int] = None, is_active: Optional[bool] = None) -> list[dict[str, Any]]:
    """Liste les comptes avec filtres simples."""

    clauses: list[str] = []
    params: dict[str, Any] = {}
    if entity_id is not None:
        clauses.append("entity_id = :entity_id")
        params["entity_id"] = int(entity_id)
    if is_active is not None:
        clauses.append("is_active = :is_active")
        params["is_active"] = bool(is_active)

    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses)

    df = query_df(
        text(
            f"""
            SELECT id, entity_id, type, label, iban, bic, currency, is_active, metadata
            FROM finance_accounts
            {where_sql}
            ORDER BY entity_id, label
            """
        ),
        params=params or None,
    )
    if df.empty:
        return []
    return df.to_dict("records")
