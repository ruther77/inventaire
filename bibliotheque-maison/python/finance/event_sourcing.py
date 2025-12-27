"""Helpers d'event sourcing avec stockage injectable."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Iterable, List, Mapping, Protocol
from uuid import uuid4


class EventType(str, Enum):
    """Types d'événements pris en charge."""
    INVOICE_IMPORTED = "invoice.imported"
    PRICE_UPDATED = "price.updated"
    STOCK_MOVEMENT = "stock.movement"
    BANK_TRANSACTION_CATEGORIZED = "bank_transaction.categorized"


@dataclass
class Event:
    """Représentation immuable d'un événement."""
    event_id: str
    event_type: EventType
    aggregate_type: str
    aggregate_id: str
    tenant_id: int
    user_id: int | None
    timestamp: datetime
    version: int
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    checksum: str = ""

    def __post_init__(self) -> None:
        if not self.checksum:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        data = f"{self.event_id}:{self.event_type.value}:{self.aggregate_id}:{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "payload": self.payload,
            "metadata": self.metadata,
            "checksum": self.checksum,
        }


class EventRepository(Protocol):
    """Interface de stockage pour l'event sourcing."""

    def append(self, event: Event) -> Event:
        ...

    def get_events(
        self,
        aggregate_type: str,
        aggregate_id: str,
        tenant_id: int,
        *,
        from_version: int = 0,
    ) -> List[Event]:
        ...


class EventDispatcher:
    """Diffuse des événements via un dépôt."""

    def __init__(self, repo: EventRepository, tenant_id: int, user_id: int | None = None):
        self.repo = repo
        self.tenant_id = int(tenant_id)
        self.user_id = user_id

    def emit(
        self,
        event_type: EventType,
        aggregate_type: str,
        aggregate_id: str,
        payload: Mapping[str, Any],
        *,
        metadata: Mapping[str, Any] | None = None,
        version: int = 1,
    ) -> Event:
        if not aggregate_type or not aggregate_id:
            raise ValueError("aggregate_type and aggregate_id are required.")
        if self.tenant_id <= 0:
            raise ValueError("tenant_id must be positive.")

        event = Event(
            event_id=str(uuid4()),
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=str(aggregate_id),
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            timestamp=datetime.now(timezone.utc),
            version=int(version),
            payload=dict(payload),
            metadata=dict(metadata) if metadata else {},
        )
        return self.repo.append(event)

    def replay(
        self,
        aggregate_type: str,
        aggregate_id: str,
        projector: Callable[[Any, Event], Any],
        *,
        initial_state: Any = None,
    ) -> Any:
        events = self.repo.get_events(aggregate_type, aggregate_id, self.tenant_id)
        state = initial_state
        for event in events:
            state = projector(state, event)
        return state


def emit_invoice_imported(
    repo: EventRepository,
    *,
    tenant_id: int,
    invoice_id: str,
    filename: str,
    supplier: str,
    total: float,
    items_count: int,
    user_id: int | None = None,
) -> Event:
    dispatcher = EventDispatcher(repo, tenant_id, user_id)
    return dispatcher.emit(
        EventType.INVOICE_IMPORTED,
        "invoice",
        invoice_id,
        {
            "filename": filename,
            "supplier": supplier,
            "total": float(total),
            "items_count": int(items_count),
        },
    )


def emit_price_updated(
    repo: EventRepository,
    *,
    tenant_id: int,
    product_id: int,
    old_price: float,
    new_price: float,
    supplier: str,
    source: str,
    user_id: int | None = None,
) -> Event:
    dispatcher = EventDispatcher(repo, tenant_id, user_id)
    if old_price != 0:
        variation_pct = (new_price - old_price) / old_price * 100
    else:
        variation_pct = 100.0 if new_price > 0 else 0.0

    return dispatcher.emit(
        EventType.PRICE_UPDATED,
        "product",
        str(product_id),
        {
            "old_price": float(old_price),
            "new_price": float(new_price),
            "variation_pct": round(variation_pct, 2),
            "supplier": supplier,
            "source": source,
        },
    )


def emit_stock_movement(
    repo: EventRepository,
    *,
    tenant_id: int,
    product_id: int,
    movement_type: str,
    quantity: float,
    reason: str,
    reference: str | None = None,
    user_id: int | None = None,
) -> Event:
    dispatcher = EventDispatcher(repo, tenant_id, user_id)
    return dispatcher.emit(
        EventType.STOCK_MOVEMENT,
        "product",
        str(product_id),
        {
            "movement_type": movement_type,
            "quantity": float(quantity),
            "reason": reason,
            "reference": reference,
        },
    )


def emit_bank_transaction_categorized(
    repo: EventRepository,
    *,
    tenant_id: int,
    transaction_id: str,
    category: str,
    confidence: float,
    method: str,
    user_id: int | None = None,
) -> Event:
    dispatcher = EventDispatcher(repo, tenant_id, user_id)
    return dispatcher.emit(
        EventType.BANK_TRANSACTION_CATEGORIZED,
        "transaction",
        transaction_id,
        {
            "category": category,
            "confidence": float(confidence),
            "method": method,
        },
    )


def get_aggregate_history(
    repo: EventRepository,
    *,
    tenant_id: int,
    aggregate_type: str,
    aggregate_id: str,
) -> List[dict[str, Any]]:
    if not aggregate_type or not aggregate_id:
        raise ValueError("aggregate_type and aggregate_id are required.")
    events = repo.get_events(aggregate_type, aggregate_id, int(tenant_id))
    return [event.to_dict() for event in events]


__all__ = [
    "Event",
    "EventDispatcher",
    "EventRepository",
    "EventType",
    "emit_bank_transaction_categorized",
    "emit_invoice_imported",
    "emit_price_updated",
    "emit_stock_movement",
    "get_aggregate_history",
]
