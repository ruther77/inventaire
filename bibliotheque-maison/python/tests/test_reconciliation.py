"""Tests pour finance.reconciliation."""

from __future__ import annotations

from finance.reconciliation import fetch_matches


class MemoryReconRepo:
    def __init__(self):
        self.records = []

    def fetch_matches(self, tenant_id, status=None):
        return [record for record in self.records if record.get("tenant_id") == tenant_id]


def test_fetch_matches_returns_records():
    repo = MemoryReconRepo()
    repo.records.append({"tenant_id": 1, "status": "pending"})
    matches = fetch_matches(repo, tenant_id=1)
    assert len(matches) == 1
