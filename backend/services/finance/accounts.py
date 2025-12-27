"""
Module de gestion des comptes financiers.

Ce module fournit les services pour:
- Création et gestion de comptes bancaires par entité
- Validation de cohérence devise/entité
- Listing et filtrage des comptes
- Mise à jour et suppression avec gestion du cache
- Support multi-devises (EUR, USD, etc.)

Les comptes sont liés à des entités (finance_entities) et peuvent être
de différents types (COMPTE_COURANT, CAISSE, EPARGNE, etc.).
Chaque compte suit une devise spécifique qui doit correspondre à celle
de son entité.
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import text

from core.data_repository import exec_sql_return_id, query_df
from backend.schemas.finance import FinanceAccountCreate
from backend.cache import cached, CacheTTL, invalidate_on_mutation


def _fetch_entity_currency(entity_id: int) -> Optional[str]:
    df = query_df(
        text("SELECT currency FROM finance_entities WHERE id = :entity_id"),
        params={"entity_id": int(entity_id)},
    )
    if df.empty:
        return None
    value = df.iloc[0].currency
    return str(value) if value else None


@invalidate_on_mutation(["finance_accounts"])
def create_account(payload: FinanceAccountCreate) -> dict[str, Any]:
    """
    Crée un nouveau compte financier avec validation.

    Valide que la devise du compte correspond à celle de l'entité avant
    la création. Invalide automatiquement le cache des comptes.

    Args:
        payload: Données du compte à créer incluant entity_id, type, label,
                 currency, IBAN, BIC, etc.

    Returns:
        Dict contenant les informations du compte créé avec son ID

    Raises:
        ValueError: Si la devise ne correspond pas à celle de l'entité

    Example:
        >>> account = create_account(FinanceAccountCreate(
        ...     entity_id=1,
        ...     type="COMPTE_COURANT",
        ...     label="Compte principal",
        ...     currency="EUR",
        ...     iban="FR7612345678901234567890123"
        ... ))
    """
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


@cached(ttl=CacheTTL.MEDIUM, prefix="finance_accounts", tenant_aware=False)
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


@invalidate_on_mutation(["finance_accounts"])
def update_account(account_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Met à jour un compte financier."""
    from core.data_repository import get_engine

    # Vérifier que le compte existe
    existing = get_account(account_id)
    if not existing:
        raise ValueError("Compte introuvable")

    # Sécurité : Construire la requête dynamiquement avec liste blanche de champs
    # Les noms de champs proviennent uniquement de allowed_fields (whitelist)
    # Les valeurs sont passées via des paramètres nommés pour éviter les injections SQL
    allowed_fields = {"label", "iban", "bic", "type", "is_active", "metadata"}
    updates = []
    params: dict[str, Any] = {"account_id": int(account_id)}

    for field in allowed_fields:
        if field in payload:
            # Sécurité : le nom du champ provient de la whitelist, pas de l'entrée utilisateur
            updates.append(f"{field} = :{field}")
            params[field] = payload[field]

    if not updates:
        return existing

    updates.append("updated_at = now()")
    update_sql = ", ".join(updates)

    # Sécurité : Construction sécurisée de la requête
    # Les noms de champs proviennent de allowed_fields (whitelist)
    # Aucune donnée utilisateur n'est interpolée directement dans la requête SQL
    with get_engine().begin() as conn:
        conn.execute(
            text(f"UPDATE finance_accounts SET {update_sql} WHERE id = :account_id"),
            params,
        )

    return get_account(account_id) or existing


@invalidate_on_mutation(["finance_accounts"])
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
            # Suppression logique : désactiver le compte
            conn.execute(
                text("UPDATE finance_accounts SET is_active = false, updated_at = now() WHERE id = :account_id"),
                {"account_id": account_id},
            )
        else:
            # Suppression définitive : supprimer le compte
            conn.execute(
                text("DELETE FROM finance_accounts WHERE id = :account_id"),
                {"account_id": account_id},
            )

    return True
