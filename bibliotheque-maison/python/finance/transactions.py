"""Helpers de transactions finance avec stockage injectable."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Protocol


class TransactionRepository(Protocol):
    def get_lock_status(self, transaction_id: int) -> tuple[bool, datetime | None]:
        ...

    def update_transaction(self, transaction_id: int, payload: Mapping[str, Any]) -> None:
        ...

    def lock_transaction(self, transaction_id: int, locked_at: datetime) -> bool:
        ...


def update_transaction(
    repo: TransactionRepository,
    *,
    transaction_id: int,
    note: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    if transaction_id is None or int(transaction_id) <= 0:
        raise ValueError("transaction_id must be a positive integer.")

    exists, locked_at = repo.get_lock_status(int(transaction_id))
    if not exists:
        raise ValueError("Transaction not found.")
    if locked_at:
        raise ValueError("Transaction is locked.")

    payload: dict[str, Any] = {}
    if note is not None:
        payload["note"] = note
    if status:
        payload["status"] = status.strip().upper()

    if not payload:
        return {"id": int(transaction_id)}

    payload["updated_at"] = datetime.now(timezone.utc)
    repo.update_transaction(int(transaction_id), payload)
    return {"id": int(transaction_id), "note": note, "status": payload.get("status")}


def lock_transaction(repo: TransactionRepository, *, transaction_id: int) -> dict[str, Any]:
    if transaction_id is None or int(transaction_id) <= 0:
        raise ValueError("transaction_id must be a positive integer.")
    locked = repo.lock_transaction(int(transaction_id), datetime.now(timezone.utc))
    if not locked:
        raise ValueError("Transaction not found or already locked.")
    return {"id": int(transaction_id), "locked": True}


__all__ = ["TransactionRepository", "lock_transaction", "update_transaction"]
