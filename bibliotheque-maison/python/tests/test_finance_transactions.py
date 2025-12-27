"""Tests pour finance.transactions."""

from __future__ import annotations

from datetime import datetime, timezone

from finance.transactions import lock_transaction, update_transaction


class MemoryTransactionRepo:
    def __init__(self):
        self.records = {1: {"locked_at": None}}

    def get_lock_status(self, transaction_id: int):
        record = self.records.get(transaction_id)
        if not record:
            return False, None
        return True, record.get("locked_at")

    def update_transaction(self, transaction_id: int, payload):
        if transaction_id in self.records:
            self.records[transaction_id].update(payload)

    def lock_transaction(self, transaction_id: int, locked_at: datetime):
        record = self.records.get(transaction_id)
        if not record or record.get("locked_at"):
            return False
        record["locked_at"] = locked_at
        return True


def test_update_transaction():
    repo = MemoryTransactionRepo()
    result = update_transaction(repo, transaction_id=1, note="ok", status="confirmed")
    assert result["status"] == "CONFIRMED"


def test_lock_transaction():
    repo = MemoryTransactionRepo()
    result = lock_transaction(repo, transaction_id=1)
    assert result["locked"] is True
