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


def get_account(account_id: int) -> dict[str, Any] | None:
    """Récupère un compte par son ID."""
    df = query_df(
        text(
            """
            SELECT id, entity_id, type, label, iban, bic, currency, is_active, metadata, created_at, updated_at
            FROM finance_accounts
            WHERE id = :account_id
            """
        ),
        params={"account_id": int(account_id)},
    )
    if df.empty:
        return None
    return df.to_dict("records")[0]


def update_account(account_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Met à jour un compte financier."""
    from core.data_repository import get_engine

    # Vérifier que le compte existe
    existing = get_account(account_id)
    if not existing:
        raise ValueError("Compte introuvable")

    # Construire la requête dynamiquement
    allowed_fields = {"label", "iban", "bic", "type", "is_active", "metadata"}
    updates = []
    params: dict[str, Any] = {"account_id": int(account_id)}

    for field in allowed_fields:
        if field in payload:
            updates.append(f"{field} = :{field}")
            params[field] = payload[field]

    if not updates:
        return existing

    updates.append("updated_at = now()")
    update_sql = ", ".join(updates)

    with get_engine().begin() as conn:
        conn.execute(
            text(f"UPDATE finance_accounts SET {update_sql} WHERE id = :account_id"),
            params,
        )

    return get_account(account_id) or existing


def delete_account(account_id: int) -> bool:
    """Supprime un compte financier (soft delete via is_active=false, ou hard delete si pas de données)."""
    from core.data_repository import get_engine

    existing = get_account(account_id)
    if not existing:
        raise ValueError("Compte introuvable")

    with get_engine().begin() as conn:
        # Vérifier si le compte a des transactions ou relevés associés
        has_data = conn.execute(
            text(
                """
                SELECT 1 FROM (
                    SELECT 1 FROM finance_transactions WHERE account_id = :account_id LIMIT 1
                    UNION ALL
                    SELECT 1 FROM finance_bank_statements WHERE account_id = :account_id LIMIT 1
                ) sub LIMIT 1
                """
            ),
            {"account_id": account_id},
        ).fetchone()

        if has_data:
            # Soft delete: désactiver le compte
            conn.execute(
                text("UPDATE finance_accounts SET is_active = false, updated_at = now() WHERE id = :account_id"),
                {"account_id": account_id},
            )
        else:
            # Hard delete: supprimer le compte
            conn.execute(
                text("DELETE FROM finance_accounts WHERE id = :account_id"),
                {"account_id": account_id},
            )

    return True
