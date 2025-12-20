"""
Core Infrastructure Module
===========================

Infrastructure transversale pour le projet.
Compatible avec le plan de restructuration 2025-12.

Composants:
- EventBus: Bus d'événements pour event sourcing
- AuditTrail: Piste d'audit complète
- DataRepository: Accès données unifié
"""

# Re-export depuis core/finance
from core.finance.event_sourcing import (
    EventType,
    Event,
    EventStore,
    EventDispatcher,
    emit_invoice_imported,
    emit_price_updated,
    emit_stock_movement,
)

from core.finance.audit_trail import (
    AuditAction,
    AuditEntity,
    AuditSeverity,
    AuditContext,
    AuditDiff,
    AuditEntry,
    AuditSearchCriteria,
    AuditReport,
    AuditTrail,
    audit_action,
    create_audit_trail,
    AUDIT_LOG_SCHEMA,
)

# Re-export depuis core/
from core.data_repository import (
    get_engine,
    get_session,
    DataRepository,
)

__all__ = [
    # Event Sourcing
    "EventType",
    "Event",
    "EventStore",
    "EventDispatcher",
    "emit_invoice_imported",
    "emit_price_updated",
    "emit_stock_movement",

    # Audit Trail
    "AuditAction",
    "AuditEntity",
    "AuditSeverity",
    "AuditContext",
    "AuditDiff",
    "AuditEntry",
    "AuditSearchCriteria",
    "AuditReport",
    "AuditTrail",
    "audit_action",
    "create_audit_trail",
    "AUDIT_LOG_SCHEMA",

    # Data Repository
    "get_engine",
    "get_session",
    "DataRepository",
]
