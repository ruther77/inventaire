"""Tests pour finance.event_sourcing."""

from __future__ import annotations

from finance.event_sourcing import (
    Event,
    EventDispatcher,
    EventType,
    emit_invoice_imported,
    get_aggregate_history,
)


class MemoryEventRepo:
    def __init__(self):
        self.events = []

    def append(self, event: Event) -> Event:
        self.events.append(event)
        return event

    def get_events(self, aggregate_type, aggregate_id, tenant_id, *, from_version=0):
        return [
            e for e in self.events
            if e.aggregate_type == aggregate_type
            and e.aggregate_id == aggregate_id
            and e.tenant_id == tenant_id
            and e.version > from_version
        ]


def test_emit_invoice_imported():
    repo = MemoryEventRepo()
    event = emit_invoice_imported(
        repo,
        tenant_id=1,
        invoice_id="inv-1",
        filename="file.pdf",
        supplier="Supplier",
        total=10.0,
        items_count=2,
    )
    assert event.event_type == EventType.INVOICE_IMPORTED
    assert repo.events


def test_get_aggregate_history():
    repo = MemoryEventRepo()
    dispatcher = EventDispatcher(repo, 1)
    dispatcher.emit(EventType.PRICE_UPDATED, "product", "1", {"value": 10})
    history = get_aggregate_history(repo, tenant_id=1, aggregate_type="product", aggregate_id="1")
    assert history
