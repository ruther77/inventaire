"""Tests pour finance.audit_trail."""

from __future__ import annotations

from datetime import datetime, timezone

from finance.audit_trail import (
    AuditAction,
    AuditContext,
    AuditEntity,
    AuditEntry,
    AuditSearchCriteria,
    get_entity_history,
    get_user_activity,
    log_update,
)


class MemoryAuditRepo:
    def __init__(self):
        self.entries = []

    def log(self, entry: AuditEntry) -> AuditEntry:
        self.entries.append(entry)
        return entry

    def search(self, criteria: AuditSearchCriteria):
        results = self.entries
        if criteria.entities:
            results = [e for e in results if e.entity in criteria.entities]
        if criteria.entity_ids:
            results = [e for e in results if e.entity_id in criteria.entity_ids]
        if criteria.user_ids:
            results = [e for e in results if e.context.user_id in criteria.user_ids]
        if criteria.tenant_ids:
            results = [e for e in results if e.context.tenant_id in criteria.tenant_ids]
        if criteria.start_date:
            results = [e for e in results if e.timestamp >= criteria.start_date]
        if criteria.end_date:
            results = [e for e in results if e.timestamp <= criteria.end_date]
        return results[: criteria.limit]


def test_log_update_creates_diff():
    repo = MemoryAuditRepo()
    context = AuditContext(user_id=1, tenant_id=2)
    entry = log_update(
        repo,
        entity=AuditEntity.PRODUCT,
        entity_id=42,
        before={"name": "Old", "price": 1},
        after={"name": "New", "price": 2},
        context=context,
    )
    assert entry.action == AuditAction.UPDATE
    assert entry.diff
    fields = {d.field for d in entry.diff}
    assert "name" in fields
    assert "price" in fields


def test_get_entity_history_filters():
    repo = MemoryAuditRepo()
    context = AuditContext(user_id=1, tenant_id=1)
    log_update(
        repo,
        entity=AuditEntity.PRODUCT,
        entity_id=1,
        before={"a": 1},
        after={"a": 2},
        context=context,
    )
    log_update(
        repo,
        entity=AuditEntity.USER,
        entity_id=2,
        before={"b": 1},
        after={"b": 2},
        context=context,
    )
    results = get_entity_history(repo, entity=AuditEntity.PRODUCT, entity_id=1)
    assert len(results) == 1
    assert results[0].entity == AuditEntity.PRODUCT


def test_get_user_activity_filters_by_user_and_start_date():
    repo = MemoryAuditRepo()
    context = AuditContext(user_id=5, tenant_id=1)
    log_update(
        repo,
        entity=AuditEntity.PRODUCT,
        entity_id=3,
        before={"a": 1},
        after={"a": 2},
        context=context,
    )
    start = datetime.now(timezone.utc)
    results = get_user_activity(repo, user_id=5, start_date=start)
    assert results == []
