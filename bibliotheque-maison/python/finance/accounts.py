"""Helpers de comptes finance avec stockage injectable."""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class AccountRepository(Protocol):
    def fetch_entity_currency(self, entity_id: int) -> str | None:
        ...

    def create_account(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        ...

    def list_accounts(self, entity_id: int | None = None, is_active: bool | None = None) -> list[Mapping[str, Any]]:
        ...


def create_account(
    repo: AccountRepository,
    *,
    entity_id: int,
    account_type: str,
    label: str,
    currency: str,
    iban: str | None = None,
    bic: str | None = None,
    is_active: bool = True,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if entity_id is None or int(entity_id) <= 0:
        raise ValueError("entity_id must be a positive integer.")
    clean_label = (label or "").strip()
    clean_type = (account_type or "").strip()
    clean_currency = (currency or "").strip()
    if not clean_label:
        raise ValueError("label must be provided.")
    if not clean_type:
        raise ValueError("account_type must be provided.")
    if not clean_currency:
        raise ValueError("currency must be provided.")

    expected = repo.fetch_entity_currency(int(entity_id))
    if expected and expected.upper() != clean_currency.upper():
        raise ValueError(f"Currency mismatch (expected {expected}).")

    payload = {
        "entity_id": int(entity_id),
        "type": clean_type,
        "label": clean_label,
        "iban": iban,
        "bic": bic,
        "currency": clean_currency.upper(),
        "is_active": bool(is_active),
        "metadata": dict(metadata) if metadata else {},
    }
    created = repo.create_account(payload)
    return dict(created)


def list_accounts(
    repo: AccountRepository,
    *,
    entity_id: int | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    if entity_id is not None and int(entity_id) <= 0:
        raise ValueError("entity_id must be a positive integer.")
    rows = repo.list_accounts(
        int(entity_id) if entity_id is not None else None,
        bool(is_active) if is_active is not None else None,
    )
    return [dict(row) for row in rows]


__all__ = ["AccountRepository", "create_account", "list_accounts"]
