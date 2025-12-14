"""
Event Sourcing pour opérations financières critiques.

Fonctionnalités:
- Stockage immuable de tous les événements
- Replay d'historique
- Audit trail complet
- Webhooks internes
- Projection d'état courant
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, List, Dict
from dataclasses import dataclass, field, asdict
from uuid import uuid4
import threading

from sqlalchemy import text
from core.data_repository import get_engine


class EventType(str, Enum):
    """Types d'événements financiers."""
    # Factures
    INVOICE_IMPORTED = "invoice.imported"
    INVOICE_VALIDATED = "invoice.validated"
    INVOICE_REJECTED = "invoice.rejected"
    INVOICE_PAID = "invoice.paid"

    # Relevés bancaires
    BANK_STATEMENT_IMPORTED = "bank_statement.imported"
    BANK_TRANSACTION_CATEGORIZED = "bank_transaction.categorized"
    BANK_TRANSACTION_RECONCILED = "bank_transaction.reconciled"

    # Prix
    PRICE_UPDATED = "price.updated"
    PRICE_ALERT_TRIGGERED = "price.alert_triggered"

    # Stock
    STOCK_MOVEMENT = "stock.movement"
    STOCK_ADJUSTMENT = "stock.adjustment"
    STOCK_ALERT = "stock.alert"
    INVENTORY_SNAPSHOT = "inventory.snapshot"

    # Dépenses
    EXPENSE_CREATED = "expense.created"
    EXPENSE_CATEGORIZED = "expense.categorized"
    EXPENSE_APPROVED = "expense.approved"

    # Fournisseurs
    SUPPLIER_SCORE_UPDATED = "supplier.score_updated"
    SUPPLIER_CREATED = "supplier.created"

    # Produits
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DEACTIVATED = "product.deactivated"

    # Marges
    MARGIN_CALCULATED = "margin.calculated"
    MARGIN_ALERT = "margin.alert"

    # Prévisions
    FORECAST_GENERATED = "forecast.generated"

    # Rapprochement
    RECONCILIATION_MATCHED = "reconciliation.matched"
    RECONCILIATION_FAILED = "reconciliation.failed"


@dataclass
class Event:
    """Représentation d'un événement immuable."""
    event_id: str
    event_type: EventType
    aggregate_type: str  # invoice, product, transaction, etc.
    aggregate_id: str
    tenant_id: int
    user_id: Optional[int]
    timestamp: datetime
    version: int
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    checksum: str = ""

    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        """Calcule un checksum pour garantir l'intégrité."""
        data = f"{self.event_id}:{self.event_type}:{self.aggregate_id}:{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['event_type'] = self.event_type.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Event:
        data = data.copy()
        data['event_type'] = EventType(data['event_type'])
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class EventStore:
    """Store persistant pour les événements."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._ensure_table()

    def _ensure_table(self):
        """Crée la table event_log si nécessaire."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS event_log (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(36) UNIQUE NOT NULL,
                    event_type VARCHAR(100) NOT NULL,
                    aggregate_type VARCHAR(50) NOT NULL,
                    aggregate_id VARCHAR(100) NOT NULL,
                    tenant_id INTEGER NOT NULL,
                    user_id INTEGER,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    version INTEGER NOT NULL DEFAULT 1,
                    payload JSONB NOT NULL DEFAULT '{}',
                    metadata JSONB NOT NULL DEFAULT '{}',
                    checksum VARCHAR(16) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_event_log_aggregate
                    ON event_log(aggregate_type, aggregate_id);
                CREATE INDEX IF NOT EXISTS idx_event_log_tenant
                    ON event_log(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_event_log_type
                    ON event_log(event_type);
                CREATE INDEX IF NOT EXISTS idx_event_log_timestamp
                    ON event_log(timestamp);
            """))

    def append(self, event: Event) -> Event:
        """Ajoute un événement au store (immuable)."""
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO event_log
                    (event_id, event_type, aggregate_type, aggregate_id,
                     tenant_id, user_id, timestamp, version, payload, metadata, checksum)
                    VALUES
                    (:event_id, :event_type, :aggregate_type, :aggregate_id,
                     :tenant_id, :user_id, :timestamp, :version, :payload, :metadata, :checksum)
                """),
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "aggregate_type": event.aggregate_type,
                    "aggregate_id": event.aggregate_id,
                    "tenant_id": event.tenant_id,
                    "user_id": event.user_id,
                    "timestamp": event.timestamp,
                    "version": event.version,
                    "payload": json.dumps(event.payload),
                    "metadata": json.dumps(event.metadata),
                    "checksum": event.checksum,
                }
            )

        # Dispatch aux handlers
        self._dispatch(event)

        return event

    def get_events(
        self,
        aggregate_type: str,
        aggregate_id: str,
        tenant_id: int,
        from_version: int = 0
    ) -> List[Event]:
        """Récupère tous les événements d'un agrégat."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT event_id, event_type, aggregate_type, aggregate_id,
                           tenant_id, user_id, timestamp, version, payload, metadata, checksum
                    FROM event_log
                    WHERE aggregate_type = :aggregate_type
                      AND aggregate_id = :aggregate_id
                      AND tenant_id = :tenant_id
                      AND version > :from_version
                    ORDER BY version ASC
                """),
                {
                    "aggregate_type": aggregate_type,
                    "aggregate_id": aggregate_id,
                    "tenant_id": tenant_id,
                    "from_version": from_version,
                }
            )

            events = []
            for row in result:
                events.append(Event(
                    event_id=row.event_id,
                    event_type=EventType(row.event_type),
                    aggregate_type=row.aggregate_type,
                    aggregate_id=row.aggregate_id,
                    tenant_id=row.tenant_id,
                    user_id=row.user_id,
                    timestamp=row.timestamp,
                    version=row.version,
                    payload=row.payload if isinstance(row.payload, dict) else json.loads(row.payload),
                    metadata=row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata),
                    checksum=row.checksum,
                ))

            return events

    def get_events_by_type(
        self,
        event_type: EventType,
        tenant_id: int,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """Récupère les événements d'un type donné."""
        engine = get_engine()

        query = """
            SELECT event_id, event_type, aggregate_type, aggregate_id,
                   tenant_id, user_id, timestamp, version, payload, metadata, checksum
            FROM event_log
            WHERE event_type = :event_type
              AND tenant_id = :tenant_id
        """
        params = {
            "event_type": event_type.value,
            "tenant_id": tenant_id,
            "limit": limit,
        }

        if since:
            query += " AND timestamp > :since"
            params["since"] = since

        query += " ORDER BY timestamp DESC LIMIT :limit"

        with engine.connect() as conn:
            result = conn.execute(text(query), params)

            events = []
            for row in result:
                events.append(Event(
                    event_id=row.event_id,
                    event_type=EventType(row.event_type),
                    aggregate_type=row.aggregate_type,
                    aggregate_id=row.aggregate_id,
                    tenant_id=row.tenant_id,
                    user_id=row.user_id,
                    timestamp=row.timestamp,
                    version=row.version,
                    payload=row.payload if isinstance(row.payload, dict) else json.loads(row.payload),
                    metadata=row.metadata if isinstance(row.metadata, dict) else json.loads(row.metadata),
                    checksum=row.checksum,
                ))

            return events

    def get_latest_version(
        self,
        aggregate_type: str,
        aggregate_id: str,
        tenant_id: int
    ) -> int:
        """Retourne la dernière version d'un agrégat."""
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT COALESCE(MAX(version), 0) as max_version
                    FROM event_log
                    WHERE aggregate_type = :aggregate_type
                      AND aggregate_id = :aggregate_id
                      AND tenant_id = :tenant_id
                """),
                {
                    "aggregate_type": aggregate_type,
                    "aggregate_id": aggregate_id,
                    "tenant_id": tenant_id,
                }
            )
            row = result.fetchone()
            return row.max_version if row else 0

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        """Abonne un handler à un type d'événement."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def _dispatch(self, event: Event):
        """Dispatch l'événement aux handlers abonnés."""
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                # Log l'erreur mais ne bloque pas
                print(f"Error in event handler: {e}")


class EventDispatcher:
    """Dispatcher haut niveau pour créer et publier des événements."""

    def __init__(self, tenant_id: int, user_id: Optional[int] = None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.store = EventStore()

    def emit(
        self,
        event_type: EventType,
        aggregate_type: str,
        aggregate_id: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Event:
        """Émet un nouvel événement."""
        version = self.store.get_latest_version(
            aggregate_type, aggregate_id, self.tenant_id
        ) + 1

        event = Event(
            event_id=str(uuid4()),
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            timestamp=datetime.utcnow(),
            version=version,
            payload=payload,
            metadata=metadata or {},
        )

        return self.store.append(event)

    def replay(
        self,
        aggregate_type: str,
        aggregate_id: str,
        projector: Callable[[Any, Event], Any],
        initial_state: Any = None
    ) -> Any:
        """Rejoue tous les événements pour reconstruire l'état."""
        events = self.store.get_events(
            aggregate_type, aggregate_id, self.tenant_id
        )

        state = initial_state
        for event in events:
            state = projector(state, event)

        return state


# Fonctions utilitaires pour les cas d'usage courants
def emit_invoice_imported(
    tenant_id: int,
    invoice_id: str,
    filename: str,
    supplier: str,
    total: float,
    items_count: int,
    user_id: Optional[int] = None
) -> Event:
    """Émet un événement d'import de facture."""
    dispatcher = EventDispatcher(tenant_id, user_id)
    return dispatcher.emit(
        EventType.INVOICE_IMPORTED,
        "invoice",
        invoice_id,
        {
            "filename": filename,
            "supplier": supplier,
            "total": total,
            "items_count": items_count,
        }
    )


def emit_price_updated(
    tenant_id: int,
    product_id: int,
    old_price: float,
    new_price: float,
    supplier: str,
    source: str,
    user_id: Optional[int] = None
) -> Event:
    """Émet un événement de mise à jour de prix."""
    dispatcher = EventDispatcher(tenant_id, user_id)
    variation_pct = ((new_price - old_price) / old_price * 100) if old_price > 0 else 0

    return dispatcher.emit(
        EventType.PRICE_UPDATED,
        "product",
        str(product_id),
        {
            "old_price": old_price,
            "new_price": new_price,
            "variation_pct": round(variation_pct, 2),
            "supplier": supplier,
            "source": source,
        }
    )


def emit_stock_movement(
    tenant_id: int,
    product_id: int,
    movement_type: str,  # in, out, adjustment
    quantity: float,
    reason: str,
    reference: Optional[str] = None,
    user_id: Optional[int] = None
) -> Event:
    """Émet un événement de mouvement de stock."""
    dispatcher = EventDispatcher(tenant_id, user_id)
    return dispatcher.emit(
        EventType.STOCK_MOVEMENT,
        "product",
        str(product_id),
        {
            "movement_type": movement_type,
            "quantity": quantity,
            "reason": reason,
            "reference": reference,
        }
    )


def emit_bank_transaction_categorized(
    tenant_id: int,
    transaction_id: str,
    category: str,
    confidence: float,
    method: str,  # manual, rule, ml
    user_id: Optional[int] = None
) -> Event:
    """Émet un événement de catégorisation de transaction."""
    dispatcher = EventDispatcher(tenant_id, user_id)
    return dispatcher.emit(
        EventType.BANK_TRANSACTION_CATEGORIZED,
        "transaction",
        transaction_id,
        {
            "category": category,
            "confidence": confidence,
            "method": method,
        }
    )


def get_aggregate_history(
    tenant_id: int,
    aggregate_type: str,
    aggregate_id: str
) -> List[Dict[str, Any]]:
    """Retourne l'historique complet d'un agrégat."""
    store = EventStore()
    events = store.get_events(aggregate_type, aggregate_id, tenant_id)
    return [e.to_dict() for e in events]


def get_recent_events(
    tenant_id: int,
    event_type: Optional[EventType] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Retourne les événements récents."""
    store = EventStore()
    engine = get_engine()

    query = """
        SELECT event_id, event_type, aggregate_type, aggregate_id,
               tenant_id, user_id, timestamp, version, payload, metadata, checksum
        FROM event_log
        WHERE tenant_id = :tenant_id
    """
    params = {"tenant_id": tenant_id, "limit": limit}

    if event_type:
        query += " AND event_type = :event_type"
        params["event_type"] = event_type.value

    query += " ORDER BY timestamp DESC LIMIT :limit"

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        events = []
        for row in result:
            events.append({
                "event_id": row.event_id,
                "event_type": row.event_type,
                "aggregate_type": row.aggregate_type,
                "aggregate_id": row.aggregate_id,
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "payload": row.payload if isinstance(row.payload, dict) else json.loads(row.payload),
            })
        return events
