"""Tests pour finance.accounts."""

from __future__ import annotations

from finance.accounts import create_account, list_accounts


class MemoryAccountRepo:
    def __init__(self):
        self.accounts = []
        self.currency_by_entity = {1: "EUR"}

    def fetch_entity_currency(self, entity_id: int):
        return self.currency_by_entity.get(entity_id)

    def create_account(self, payload):
        payload = dict(payload)
        payload["id"] = len(self.accounts) + 1
        self.accounts.append(payload)
        return payload

    def list_accounts(self, entity_id=None, is_active=None):
        items = self.accounts
        if entity_id is not None:
            items = [item for item in items if item.get("entity_id") == entity_id]
        if is_active is not None:
            items = [item for item in items if item.get("is_active") == is_active]
        return items


def test_create_account_currency_match():
    repo = MemoryAccountRepo()
    created = create_account(
        repo,
        entity_id=1,
        account_type="BANK",
        label="Main",
        currency="EUR",
    )
    assert created["currency"] == "EUR"


def test_list_accounts():
    repo = MemoryAccountRepo()
    create_account(repo, entity_id=1, account_type="BANK", label="Main", currency="EUR")
    results = list_accounts(repo, entity_id=1)
    assert len(results) == 1
