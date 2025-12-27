"""Helpers d'audit trail avec stockage injectable."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Iterable, List, Mapping, Protocol


class AuditAction(Enum):
    """Actions d'audit."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SOFT_DELETE = "soft_delete"
    RESTORE = "restore"
    IMPORT = "import"
    EXPORT = "export"
    APPROVE = "approve"
    REJECT = "reject"
    VALIDATE = "validate"
    INVALIDATE = "invalidate"
    RECONCILE = "reconcile"
    CLASSIFY = "classify"
    RECLASSIFY = "reclassify"
    MERGE = "merge"
    SPLIT = "split"
    DUPLICATE = "duplicate"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"
    ACCESS_DENIED = "access_denied"
    PRICE_CHANGE = "price_change"
    STOCK_ADJUSTMENT = "stock_adjustment"
    INVOICE_PAID = "invoice_paid"
    PAYMENT_RECEIVED = "payment_received"
    CREDIT_NOTE = "credit_note"
    WRITE_OFF = "write_off"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    BULK_OPERATION = "bulk_operation"
    SCHEDULED_TASK = "scheduled_task"
    DATA_MIGRATION = "data_migration"


class AuditEntity(Enum):
    """Entités auditables."""
    PRODUCT = "product"
    INVOICE = "invoice"
    PRICE = "price"
    BANK_STATEMENT = "bank_statement"
    BANK_TRANSACTION = "bank_transaction"
    CHARGE = "charge"
    USER = "user"
    TENANT = "tenant"
    CATEGORY = "category"
    RULE = "rule"


@dataclass(frozen=True)
class AuditContext:
    """Contexte d'une entrée d'audit."""
    user_id: int | None = None
    username: str | None = None
    user_email: str | None = None
    tenant_id: int | None = None
    tenant_name: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    session_id: str | None = None
    correlation_id: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class AuditDiff:
    """Différence au niveau champ pour les mises à jour."""
    field: str
    old_value: Any
    new_value: Any
    field_type: str = "string"


@dataclass
class AuditEntry:
    """Payload d'une entrée d'audit."""
    timestamp: datetime
    action: AuditAction
    entity: AuditEntity
    entity_id: int | None
    context: AuditContext
    entity_name: str | None = None
    before_state: Mapping[str, Any] | None = None
    after_state: Mapping[str, Any] | None = None
    diff: List[AuditDiff] | None = None
    description: str | None = None
    metadata: Mapping[str, Any] | None = None
    tags: List[str] = field(default_factory=list)
    checksum: str | None = None

    def calculate_checksum(self) -> str:
        """Calcule un checksum pour les vérifications d'intégrité."""
        data = {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "entity": self.entity.value,
            "entity_id": self.entity_id,
            "user_id": self.context.user_id,
            "tenant_id": self.context.tenant_id,
            "before": json.dumps(self.before_state, sort_keys=True, default=str) if self.before_state else None,
            "after": json.dumps(self.after_state, sort_keys=True, default=str) if self.after_state else None,
        }
        payload = json.dumps(data, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class AuditSearchCriteria:
    """Critères de recherche pour les entrées d'audit."""
    start_date: datetime | None = None
    end_date: datetime | None = None
    actions: List[AuditAction] | None = None
    entities: List[AuditEntity] | None = None
    entity_ids: List[int] | None = None
    user_ids: List[int] | None = None
    tenant_ids: List[int] | None = None
    limit: int = 100


class AuditRepository(Protocol):
    """Interface de stockage des entrées d'audit."""

    def log(self, entry: AuditEntry) -> AuditEntry:
        ...

    def search(self, criteria: AuditSearchCriteria) -> List[AuditEntry]:
        ...


def _field_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, datetime):
        return "date"
    if isinstance(value, (dict, list, tuple)):
        return "json"
    return "string"


def _compute_diff(before: Mapping[str, Any], after: Mapping[str, Any]) -> List[AuditDiff]:
    diffs: List[AuditDiff] = []
    keys = set(before.keys()) | set(after.keys())
    for key in sorted(keys):
        old = before.get(key)
        new = after.get(key)
        if old != new:
            diffs.append(AuditDiff(field=key, old_value=old, new_value=new, field_type=_field_type(new)))
    return diffs


def log_update(
    repo: AuditRepository,
    *,
    entity: AuditEntity,
    entity_id: int,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    context: AuditContext,
    entity_name: str | None = None,
) -> AuditEntry:
    """Journalise une entrée d'audit de mise à jour."""
    if entity_id is None or int(entity_id) <= 0:
        raise ValueError("entity_id must be a positive integer.")
    if before is None or after is None:
        raise ValueError("before and after states must be provided.")

    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc),
        action=AuditAction.UPDATE,
        entity=entity,
        entity_id=int(entity_id),
        entity_name=entity_name,
        context=context,
        before_state=before,
        after_state=after,
        diff=_compute_diff(before, after),
        description=f"Updated {entity.value} #{entity_id}",
    )
    entry.checksum = entry.calculate_checksum()
    return repo.log(entry)


def get_entity_history(
    repo: AuditRepository,
    *,
    entity: AuditEntity,
    entity_id: int,
    tenant_id: int | None = None,
    limit: int = 50,
) -> List[AuditEntry]:
    """Retourne l'historique d'audit d'une entité."""
    if entity_id is None or int(entity_id) <= 0:
        raise ValueError("entity_id must be a positive integer.")
    criteria = AuditSearchCriteria(
        entities=[entity],
        entity_ids=[int(entity_id)],
        tenant_ids=[tenant_id] if tenant_id is not None else None,
        limit=limit,
    )
    return repo.search(criteria)


def get_user_activity(
    repo: AuditRepository,
    *,
    user_id: int,
    tenant_id: int | None = None,
    start_date: datetime | None = None,
    limit: int = 100,
) -> List[AuditEntry]:
    """Retourne l'activité d'audit d'un utilisateur."""
    if user_id is None or int(user_id) <= 0:
        raise ValueError("user_id must be a positive integer.")
    start = start_date or datetime.now(timezone.utc) - timedelta(days=30)
    criteria = AuditSearchCriteria(
        user_ids=[int(user_id)],
        tenant_ids=[tenant_id] if tenant_id is not None else None,
        start_date=start,
        limit=limit,
    )
    return repo.search(criteria)


__all__ = [
    "AuditAction",
    "AuditContext",
    "AuditDiff",
    "AuditEntity",
    "AuditEntry",
    "AuditRepository",
    "AuditSearchCriteria",
    "get_entity_history",
    "get_user_activity",
    "log_update",
]
