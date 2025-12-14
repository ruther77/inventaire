"""
Audit Trail Ultra Complet
=========================

Système d'audit exhaustif pour toutes les entités du système:
- Products, Invoices, Prices, Bank Statements, Charges
- Capture: who, what, when, before, after, ip, user_agent, tenant_id
- Retention configurable et archivage
- Recherche et reporting
- Conformité RGPD avec anonymisation
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from functools import wraps
import asyncio


class AuditAction(Enum):
    """Types d'actions auditées"""
    # CRUD de base
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    SOFT_DELETE = "soft_delete"
    RESTORE = "restore"

    # Actions spécifiques
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

    # Actions de sécurité
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"
    ACCESS_DENIED = "access_denied"

    # Actions financières
    PRICE_CHANGE = "price_change"
    STOCK_ADJUSTMENT = "stock_adjustment"
    INVOICE_PAID = "invoice_paid"
    PAYMENT_RECEIVED = "payment_received"
    CREDIT_NOTE = "credit_note"
    WRITE_OFF = "write_off"

    # Actions système
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    BULK_OPERATION = "bulk_operation"
    SCHEDULED_TASK = "scheduled_task"
    DATA_MIGRATION = "data_migration"


class AuditEntity(Enum):
    """Entités auditables"""
    PRODUCT = "product"
    INVOICE = "invoice"
    INVOICE_LINE = "invoice_line"
    PRICE = "price"
    PRICE_HISTORY = "price_history"
    BANK_STATEMENT = "bank_statement"
    BANK_TRANSACTION = "bank_transaction"
    CHARGE = "charge"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    USER = "user"
    TENANT = "tenant"
    STOCK_MOVEMENT = "stock_movement"
    INVENTORY = "inventory"
    CATEGORY = "category"
    MAPPING = "mapping"
    RULE = "rule"
    REPORT = "report"
    SETTING = "setting"
    FILE = "file"
    RECONCILIATION = "reconciliation"
    ANALYTIC_ENTRY = "analytic_entry"
    BUDGET = "budget"


class AuditSeverity(Enum):
    """Niveau de sévérité pour filtrage et alertes"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"


@dataclass
class AuditContext:
    """Contexte de l'action auditée"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    user_email: Optional[str] = None
    tenant_id: Optional[int] = None
    tenant_name: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None  # Pour tracer les opérations liées
    source: Optional[str] = None  # "web", "api", "cli", "scheduled", "system"


@dataclass
class AuditDiff:
    """Différence avant/après pour les modifications"""
    field: str
    old_value: Any
    new_value: Any
    field_type: str = "string"  # "string", "number", "boolean", "date", "json", "decimal"


@dataclass
class AuditEntry:
    """Entrée d'audit complète"""
    id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)

    # Action
    action: AuditAction = AuditAction.READ
    entity: AuditEntity = AuditEntity.PRODUCT
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None  # Nom lisible pour recherche

    # Contexte
    context: AuditContext = field(default_factory=AuditContext)

    # Données
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    diff: Optional[List[AuditDiff]] = None

    # Métadonnées
    severity: AuditSeverity = AuditSeverity.INFO
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)

    # Intégrité
    checksum: Optional[str] = None
    parent_audit_id: Optional[int] = None  # Pour opérations liées

    def calculate_checksum(self) -> str:
        """Calcule un checksum pour garantir l'intégrité"""
        data = {
            "timestamp": self.timestamp.isoformat(),
            "action": self.action.value,
            "entity": self.entity.value,
            "entity_id": self.entity_id,
            "user_id": self.context.user_id if self.context else None,
            "tenant_id": self.context.tenant_id if self.context else None,
            "before": json.dumps(self.before_state, sort_keys=True, default=str) if self.before_state else None,
            "after": json.dumps(self.after_state, sort_keys=True, default=str) if self.after_state else None,
        }
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class AuditSearchCriteria:
    """Critères de recherche dans l'audit"""
    # Période
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Filtres
    actions: Optional[List[AuditAction]] = None
    entities: Optional[List[AuditEntity]] = None
    entity_ids: Optional[List[int]] = None
    user_ids: Optional[List[int]] = None
    tenant_ids: Optional[List[int]] = None
    severities: Optional[List[AuditSeverity]] = None
    tags: Optional[List[str]] = None

    # Recherche texte
    search_text: Optional[str] = None
    ip_address: Optional[str] = None

    # Pagination
    limit: int = 100
    offset: int = 0
    order_by: str = "timestamp"
    order_desc: bool = True


@dataclass
class AuditReport:
    """Rapport d'audit agrégé"""
    period_start: datetime
    period_end: datetime
    total_entries: int

    # Par action
    actions_count: Dict[str, int] = field(default_factory=dict)
    # Par entité
    entities_count: Dict[str, int] = field(default_factory=dict)
    # Par utilisateur
    users_activity: Dict[str, int] = field(default_factory=dict)
    # Par sévérité
    severity_count: Dict[str, int] = field(default_factory=dict)

    # Alertes
    security_events: int = 0
    failed_logins: int = 0
    suspicious_activities: List[Dict[str, Any]] = field(default_factory=list)


class AuditTrail:
    """
    Système d'audit trail complet
    """

    def __init__(self, db_pool=None, retention_days: int = 365):
        self.db_pool = db_pool
        self.retention_days = retention_days
        self._buffer: List[AuditEntry] = []
        self._buffer_size = 100
        self._sensitive_fields = {
            "password", "password_hash", "token", "secret",
            "api_key", "credit_card", "ssn", "iban"
        }

    # =========================================================================
    # LOGGING D'AUDIT
    # =========================================================================

    async def log(
        self,
        action: AuditAction,
        entity: AuditEntity,
        entity_id: Optional[int] = None,
        entity_name: Optional[str] = None,
        context: Optional[AuditContext] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        tags: Optional[List[str]] = None,
        parent_audit_id: Optional[int] = None
    ) -> AuditEntry:
        """
        Enregistre une entrée d'audit
        """
        # Masquer les champs sensibles
        if before_state:
            before_state = self._mask_sensitive(before_state)
        if after_state:
            after_state = self._mask_sensitive(after_state)

        # Calculer le diff
        diff = None
        if before_state and after_state:
            diff = self._calculate_diff(before_state, after_state)

        # Créer l'entrée
        entry = AuditEntry(
            timestamp=datetime.now(),
            action=action,
            entity=entity,
            entity_id=entity_id,
            entity_name=entity_name,
            context=context or AuditContext(),
            before_state=before_state,
            after_state=after_state,
            diff=diff,
            severity=severity,
            description=description,
            metadata=metadata,
            tags=tags or [],
            parent_audit_id=parent_audit_id
        )

        # Checksum pour intégrité
        entry.checksum = entry.calculate_checksum()

        # Persister
        if self.db_pool:
            entry.id = await self._persist_entry(entry)
        else:
            # Buffer en mémoire si pas de DB
            self._buffer.append(entry)
            if len(self._buffer) > self._buffer_size:
                self._buffer.pop(0)

        return entry

    async def log_create(
        self,
        entity: AuditEntity,
        entity_id: int,
        data: Dict[str, Any],
        context: AuditContext,
        entity_name: Optional[str] = None
    ) -> AuditEntry:
        """Shortcut pour création"""
        return await self.log(
            action=AuditAction.CREATE,
            entity=entity,
            entity_id=entity_id,
            entity_name=entity_name,
            context=context,
            after_state=data,
            description=f"Created {entity.value} #{entity_id}"
        )

    async def log_update(
        self,
        entity: AuditEntity,
        entity_id: int,
        before: Dict[str, Any],
        after: Dict[str, Any],
        context: AuditContext,
        entity_name: Optional[str] = None
    ) -> AuditEntry:
        """Shortcut pour mise à jour"""
        return await self.log(
            action=AuditAction.UPDATE,
            entity=entity,
            entity_id=entity_id,
            entity_name=entity_name,
            context=context,
            before_state=before,
            after_state=after,
            description=f"Updated {entity.value} #{entity_id}"
        )

    async def log_delete(
        self,
        entity: AuditEntity,
        entity_id: int,
        data: Dict[str, Any],
        context: AuditContext,
        entity_name: Optional[str] = None,
        soft_delete: bool = False
    ) -> AuditEntry:
        """Shortcut pour suppression"""
        action = AuditAction.SOFT_DELETE if soft_delete else AuditAction.DELETE
        return await self.log(
            action=action,
            entity=entity,
            entity_id=entity_id,
            entity_name=entity_name,
            context=context,
            before_state=data,
            description=f"{'Soft deleted' if soft_delete else 'Deleted'} {entity.value} #{entity_id}",
            severity=AuditSeverity.WARNING
        )

    async def log_security_event(
        self,
        action: AuditAction,
        context: AuditContext,
        description: str,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """Log événement de sécurité"""
        return await self.log(
            action=action,
            entity=AuditEntity.USER,
            entity_id=context.user_id,
            context=context,
            description=description,
            metadata=metadata,
            severity=AuditSeverity.SECURITY if not success else AuditSeverity.INFO,
            tags=["security", "authentication"] if action in [
                AuditAction.LOGIN, AuditAction.LOGOUT, AuditAction.LOGIN_FAILED
            ] else ["security"]
        )

    async def log_bulk_operation(
        self,
        action: AuditAction,
        entity: AuditEntity,
        entity_ids: List[int],
        context: AuditContext,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """Log opération en masse"""
        return await self.log(
            action=AuditAction.BULK_OPERATION,
            entity=entity,
            context=context,
            description=description,
            metadata={
                "bulk_action": action.value,
                "entity_ids": entity_ids,
                "count": len(entity_ids),
                **(metadata or {})
            },
            severity=AuditSeverity.WARNING,
            tags=["bulk"]
        )

    # =========================================================================
    # MASQUAGE ET DIFF
    # =========================================================================

    def _mask_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Masque les champs sensibles"""
        masked = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self._sensitive_fields):
                masked[key] = "***MASKED***"
            elif isinstance(value, dict):
                masked[key] = self._mask_sensitive(value)
            else:
                masked[key] = value
        return masked

    def _calculate_diff(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> List[AuditDiff]:
        """Calcule les différences entre deux états"""
        diffs = []
        all_keys = set(before.keys()) | set(after.keys())

        for key in all_keys:
            old_val = before.get(key)
            new_val = after.get(key)

            # Normaliser pour comparaison
            old_str = self._normalize_value(old_val)
            new_str = self._normalize_value(new_val)

            if old_str != new_str:
                diffs.append(AuditDiff(
                    field=key,
                    old_value=old_val,
                    new_value=new_val,
                    field_type=self._detect_type(new_val or old_val)
                ))

        return diffs

    def _normalize_value(self, value: Any) -> str:
        """Normalise une valeur pour comparaison"""
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True, default=str)
        if isinstance(value, Decimal):
            return str(value.normalize())
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def _detect_type(self, value: Any) -> str:
        """Détecte le type d'une valeur"""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, (int, float)):
            return "number"
        if isinstance(value, Decimal):
            return "decimal"
        if isinstance(value, datetime):
            return "datetime"
        if isinstance(value, (dict, list)):
            return "json"
        return "string"

    # =========================================================================
    # PERSISTANCE
    # =========================================================================

    async def _persist_entry(self, entry: AuditEntry) -> int:
        """Persiste une entrée d'audit dans la base"""
        if not self.db_pool:
            return 0

        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO audit_log (
                    timestamp, action, entity, entity_id, entity_name,
                    user_id, username, user_email, tenant_id,
                    ip_address, user_agent, request_id, session_id, correlation_id, source,
                    before_state, after_state, diff,
                    severity, description, metadata, tags,
                    checksum, parent_audit_id
                ) VALUES (
                    $1, $2, $3, $4, $5,
                    $6, $7, $8, $9,
                    $10, $11, $12, $13, $14, $15,
                    $16, $17, $18,
                    $19, $20, $21, $22,
                    $23, $24
                )
                RETURNING id
            """,
                entry.timestamp,
                entry.action.value,
                entry.entity.value,
                entry.entity_id,
                entry.entity_name,
                entry.context.user_id if entry.context else None,
                entry.context.username if entry.context else None,
                entry.context.user_email if entry.context else None,
                entry.context.tenant_id if entry.context else None,
                entry.context.ip_address if entry.context else None,
                entry.context.user_agent if entry.context else None,
                entry.context.request_id if entry.context else None,
                entry.context.session_id if entry.context else None,
                entry.context.correlation_id if entry.context else None,
                entry.context.source if entry.context else None,
                json.dumps(entry.before_state, default=str) if entry.before_state else None,
                json.dumps(entry.after_state, default=str) if entry.after_state else None,
                json.dumps([asdict(d) for d in entry.diff], default=str) if entry.diff else None,
                entry.severity.value,
                entry.description,
                json.dumps(entry.metadata, default=str) if entry.metadata else None,
                entry.tags,
                entry.checksum,
                entry.parent_audit_id
            )
            return row["id"]

    # =========================================================================
    # RECHERCHE
    # =========================================================================

    async def search(self, criteria: AuditSearchCriteria) -> List[AuditEntry]:
        """Recherche dans l'audit log"""
        if not self.db_pool:
            return self._search_buffer(criteria)

        async with self.db_pool.acquire() as conn:
            # Construire la requête
            conditions = ["1=1"]
            params = []
            param_idx = 1

            if criteria.start_date:
                conditions.append(f"timestamp >= ${param_idx}")
                params.append(criteria.start_date)
                param_idx += 1

            if criteria.end_date:
                conditions.append(f"timestamp <= ${param_idx}")
                params.append(criteria.end_date)
                param_idx += 1

            if criteria.actions:
                placeholders = ", ".join(f"${param_idx + i}" for i in range(len(criteria.actions)))
                conditions.append(f"action IN ({placeholders})")
                params.extend([a.value for a in criteria.actions])
                param_idx += len(criteria.actions)

            if criteria.entities:
                placeholders = ", ".join(f"${param_idx + i}" for i in range(len(criteria.entities)))
                conditions.append(f"entity IN ({placeholders})")
                params.extend([e.value for e in criteria.entities])
                param_idx += len(criteria.entities)

            if criteria.entity_ids:
                placeholders = ", ".join(f"${param_idx + i}" for i in range(len(criteria.entity_ids)))
                conditions.append(f"entity_id IN ({placeholders})")
                params.extend(criteria.entity_ids)
                param_idx += len(criteria.entity_ids)

            if criteria.user_ids:
                placeholders = ", ".join(f"${param_idx + i}" for i in range(len(criteria.user_ids)))
                conditions.append(f"user_id IN ({placeholders})")
                params.extend(criteria.user_ids)
                param_idx += len(criteria.user_ids)

            if criteria.tenant_ids:
                placeholders = ", ".join(f"${param_idx + i}" for i in range(len(criteria.tenant_ids)))
                conditions.append(f"tenant_id IN ({placeholders})")
                params.extend(criteria.tenant_ids)
                param_idx += len(criteria.tenant_ids)

            if criteria.severities:
                placeholders = ", ".join(f"${param_idx + i}" for i in range(len(criteria.severities)))
                conditions.append(f"severity IN ({placeholders})")
                params.extend([s.value for s in criteria.severities])
                param_idx += len(criteria.severities)

            if criteria.search_text:
                conditions.append(f"(description ILIKE ${param_idx} OR entity_name ILIKE ${param_idx})")
                params.append(f"%{criteria.search_text}%")
                param_idx += 1

            if criteria.ip_address:
                conditions.append(f"ip_address = ${param_idx}")
                params.append(criteria.ip_address)
                param_idx += 1

            if criteria.tags:
                conditions.append(f"tags && ${param_idx}")
                params.append(criteria.tags)
                param_idx += 1

            # Order
            order_dir = "DESC" if criteria.order_desc else "ASC"
            order_col = criteria.order_by if criteria.order_by in ["timestamp", "severity", "entity", "action"] else "timestamp"

            # Requête finale
            query = f"""
                SELECT * FROM audit_log
                WHERE {' AND '.join(conditions)}
                ORDER BY {order_col} {order_dir}
                LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """
            params.extend([criteria.limit, criteria.offset])

            rows = await conn.fetch(query, *params)

            return [self._row_to_entry(row) for row in rows]

    def _search_buffer(self, criteria: AuditSearchCriteria) -> List[AuditEntry]:
        """Recherche dans le buffer mémoire"""
        results = []
        for entry in reversed(self._buffer):
            if criteria.start_date and entry.timestamp < criteria.start_date:
                continue
            if criteria.end_date and entry.timestamp > criteria.end_date:
                continue
            if criteria.actions and entry.action not in criteria.actions:
                continue
            if criteria.entities and entry.entity not in criteria.entities:
                continue
            if criteria.entity_ids and entry.entity_id not in criteria.entity_ids:
                continue
            if criteria.severities and entry.severity not in criteria.severities:
                continue

            results.append(entry)
            if len(results) >= criteria.limit:
                break

        return results[criteria.offset:criteria.offset + criteria.limit]

    def _row_to_entry(self, row: Dict[str, Any]) -> AuditEntry:
        """Convertit une ligne DB en AuditEntry"""
        context = AuditContext(
            user_id=row.get("user_id"),
            username=row.get("username"),
            user_email=row.get("user_email"),
            tenant_id=row.get("tenant_id"),
            ip_address=row.get("ip_address"),
            user_agent=row.get("user_agent"),
            request_id=row.get("request_id"),
            session_id=row.get("session_id"),
            correlation_id=row.get("correlation_id"),
            source=row.get("source")
        )

        diff_data = row.get("diff")
        diff = None
        if diff_data:
            if isinstance(diff_data, str):
                diff_data = json.loads(diff_data)
            diff = [
                AuditDiff(
                    field=d["field"],
                    old_value=d["old_value"],
                    new_value=d["new_value"],
                    field_type=d.get("field_type", "string")
                )
                for d in diff_data
            ]

        before_state = row.get("before_state")
        if isinstance(before_state, str):
            before_state = json.loads(before_state)

        after_state = row.get("after_state")
        if isinstance(after_state, str):
            after_state = json.loads(after_state)

        metadata = row.get("metadata")
        if isinstance(metadata, str):
            metadata = json.loads(metadata)

        return AuditEntry(
            id=row.get("id"),
            timestamp=row.get("timestamp"),
            action=AuditAction(row.get("action")),
            entity=AuditEntity(row.get("entity")),
            entity_id=row.get("entity_id"),
            entity_name=row.get("entity_name"),
            context=context,
            before_state=before_state,
            after_state=after_state,
            diff=diff,
            severity=AuditSeverity(row.get("severity", "info")),
            description=row.get("description"),
            metadata=metadata,
            tags=row.get("tags", []),
            checksum=row.get("checksum"),
            parent_audit_id=row.get("parent_audit_id")
        )

    # =========================================================================
    # REPORTING
    # =========================================================================

    async def generate_report(
        self,
        tenant_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> AuditReport:
        """Génère un rapport d'audit pour une période"""
        if not self.db_pool:
            return AuditReport(
                period_start=start_date,
                period_end=end_date,
                total_entries=0
            )

        async with self.db_pool.acquire() as conn:
            # Comptage total
            total = await conn.fetchval("""
                SELECT COUNT(*) FROM audit_log
                WHERE tenant_id = $1 AND timestamp BETWEEN $2 AND $3
            """, tenant_id, start_date, end_date)

            # Par action
            actions_rows = await conn.fetch("""
                SELECT action, COUNT(*) as count FROM audit_log
                WHERE tenant_id = $1 AND timestamp BETWEEN $2 AND $3
                GROUP BY action ORDER BY count DESC
            """, tenant_id, start_date, end_date)
            actions_count = {row["action"]: row["count"] for row in actions_rows}

            # Par entité
            entities_rows = await conn.fetch("""
                SELECT entity, COUNT(*) as count FROM audit_log
                WHERE tenant_id = $1 AND timestamp BETWEEN $2 AND $3
                GROUP BY entity ORDER BY count DESC
            """, tenant_id, start_date, end_date)
            entities_count = {row["entity"]: row["count"] for row in entities_rows}

            # Par utilisateur
            users_rows = await conn.fetch("""
                SELECT username, COUNT(*) as count FROM audit_log
                WHERE tenant_id = $1 AND timestamp BETWEEN $2 AND $3
                  AND username IS NOT NULL
                GROUP BY username ORDER BY count DESC
                LIMIT 20
            """, tenant_id, start_date, end_date)
            users_activity = {row["username"]: row["count"] for row in users_rows}

            # Par sévérité
            severity_rows = await conn.fetch("""
                SELECT severity, COUNT(*) as count FROM audit_log
                WHERE tenant_id = $1 AND timestamp BETWEEN $2 AND $3
                GROUP BY severity
            """, tenant_id, start_date, end_date)
            severity_count = {row["severity"]: row["count"] for row in severity_rows}

            # Événements sécurité
            security_events = await conn.fetchval("""
                SELECT COUNT(*) FROM audit_log
                WHERE tenant_id = $1 AND timestamp BETWEEN $2 AND $3
                  AND severity = 'security'
            """, tenant_id, start_date, end_date)

            # Échecs login
            failed_logins = await conn.fetchval("""
                SELECT COUNT(*) FROM audit_log
                WHERE tenant_id = $1 AND timestamp BETWEEN $2 AND $3
                  AND action = 'login_failed'
            """, tenant_id, start_date, end_date)

            # Activités suspectes (ex: beaucoup d'échecs depuis même IP)
            suspicious = await conn.fetch("""
                SELECT ip_address, COUNT(*) as count
                FROM audit_log
                WHERE tenant_id = $1 AND timestamp BETWEEN $2 AND $3
                  AND action = 'login_failed'
                GROUP BY ip_address
                HAVING COUNT(*) > 5
            """, tenant_id, start_date, end_date)
            suspicious_activities = [
                {"type": "multiple_failed_logins", "ip": row["ip_address"], "count": row["count"]}
                for row in suspicious
            ]

            return AuditReport(
                period_start=start_date,
                period_end=end_date,
                total_entries=total or 0,
                actions_count=actions_count,
                entities_count=entities_count,
                users_activity=users_activity,
                severity_count=severity_count,
                security_events=security_events or 0,
                failed_logins=failed_logins or 0,
                suspicious_activities=suspicious_activities
            )

    # =========================================================================
    # ENTITY HISTORY
    # =========================================================================

    async def get_entity_history(
        self,
        entity: AuditEntity,
        entity_id: int,
        tenant_id: Optional[int] = None,
        limit: int = 50
    ) -> List[AuditEntry]:
        """Récupère l'historique complet d'une entité"""
        criteria = AuditSearchCriteria(
            entities=[entity],
            entity_ids=[entity_id],
            tenant_ids=[tenant_id] if tenant_id else None,
            limit=limit
        )
        return await self.search(criteria)

    async def get_user_activity(
        self,
        user_id: int,
        tenant_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """Récupère l'activité d'un utilisateur"""
        criteria = AuditSearchCriteria(
            user_ids=[user_id],
            tenant_ids=[tenant_id] if tenant_id else None,
            start_date=start_date or datetime.now() - timedelta(days=30),
            limit=limit
        )
        return await self.search(criteria)

    # =========================================================================
    # MAINTENANCE
    # =========================================================================

    async def purge_old_entries(self, before_date: Optional[datetime] = None):
        """Purge les entrées anciennes selon la rétention"""
        if not self.db_pool:
            return 0

        cutoff = before_date or datetime.now() - timedelta(days=self.retention_days)

        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM audit_log
                WHERE timestamp < $1
                  AND severity NOT IN ('security', 'critical')
            """, cutoff)

            # Extraire le nombre de lignes supprimées
            return int(result.split()[-1]) if result else 0

    async def archive_entries(
        self,
        before_date: datetime,
        archive_table: str = "audit_log_archive"
    ):
        """Archive les entrées vers une table archive"""
        if not self.db_pool:
            return 0

        async with self.db_pool.acquire() as conn:
            # Copier vers archive
            await conn.execute(f"""
                INSERT INTO {archive_table}
                SELECT * FROM audit_log WHERE timestamp < $1
            """, before_date)

            # Supprimer de la table principale
            result = await conn.execute("""
                DELETE FROM audit_log WHERE timestamp < $1
            """, before_date)

            return int(result.split()[-1]) if result else 0

    # =========================================================================
    # RGPD / ANONYMISATION
    # =========================================================================

    async def anonymize_user_data(self, user_id: int, tenant_id: int):
        """Anonymise les données d'un utilisateur (RGPD)"""
        if not self.db_pool:
            return

        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE audit_log
                SET
                    username = 'ANONYMIZED',
                    user_email = 'anonymized@example.com',
                    ip_address = '0.0.0.0',
                    user_agent = 'ANONYMIZED',
                    before_state = CASE
                        WHEN before_state IS NOT NULL THEN '{"anonymized": true}'::jsonb
                        ELSE NULL
                    END,
                    after_state = CASE
                        WHEN after_state IS NOT NULL THEN '{"anonymized": true}'::jsonb
                        ELSE NULL
                    END,
                    diff = NULL,
                    metadata = CASE
                        WHEN metadata IS NOT NULL THEN '{"anonymized": true}'::jsonb
                        ELSE NULL
                    END
                WHERE user_id = $1 AND tenant_id = $2
            """, user_id, tenant_id)

    async def export_user_data(self, user_id: int, tenant_id: int) -> List[Dict[str, Any]]:
        """Exporte toutes les données d'audit d'un utilisateur (RGPD)"""
        entries = await self.get_user_activity(user_id, tenant_id, limit=10000)
        return [
            {
                "timestamp": entry.timestamp.isoformat(),
                "action": entry.action.value,
                "entity": entry.entity.value,
                "entity_id": entry.entity_id,
                "description": entry.description,
                "ip_address": entry.context.ip_address if entry.context else None
            }
            for entry in entries
        ]


# =============================================================================
# DECORATEUR POUR AUDIT AUTOMATIQUE
# =============================================================================

def audit_action(
    action: AuditAction,
    entity: AuditEntity,
    get_entity_id=None,
    get_before_state=None,
    get_after_state=None,
    severity: AuditSeverity = AuditSeverity.INFO
):
    """
    Décorateur pour auditer automatiquement une fonction

    Usage:
        @audit_action(AuditAction.UPDATE, AuditEntity.PRODUCT, get_entity_id=lambda args: args[0])
        async def update_product(product_id: int, data: dict):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Récupérer le trail depuis le contexte ou créer un nouveau
            trail = kwargs.pop("_audit_trail", None) or AuditTrail()
            context = kwargs.pop("_audit_context", None) or AuditContext()

            entity_id = get_entity_id(args, kwargs) if get_entity_id else None
            before = await get_before_state(args, kwargs) if get_before_state else None

            try:
                result = await func(*args, **kwargs)

                after = await get_after_state(args, kwargs, result) if get_after_state else None

                await trail.log(
                    action=action,
                    entity=entity,
                    entity_id=entity_id,
                    context=context,
                    before_state=before,
                    after_state=after,
                    severity=severity
                )

                return result

            except Exception as e:
                await trail.log(
                    action=action,
                    entity=entity,
                    entity_id=entity_id,
                    context=context,
                    before_state=before,
                    severity=AuditSeverity.ERROR,
                    description=f"Error: {str(e)}",
                    metadata={"exception": type(e).__name__, "message": str(e)}
                )
                raise

        return wrapper
    return decorator


# =============================================================================
# SQL SCHEMA
# =============================================================================

AUDIT_LOG_SCHEMA = """
-- Table principale d'audit
CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Action
    action VARCHAR(50) NOT NULL,
    entity VARCHAR(50) NOT NULL,
    entity_id INTEGER,
    entity_name VARCHAR(255),

    -- Contexte utilisateur
    user_id INTEGER,
    username VARCHAR(100),
    user_email VARCHAR(255),
    tenant_id INTEGER,

    -- Contexte technique
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    session_id VARCHAR(100),
    correlation_id VARCHAR(100),
    source VARCHAR(50),

    -- Données
    before_state JSONB,
    after_state JSONB,
    diff JSONB,

    -- Métadonnées
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    description TEXT,
    metadata JSONB,
    tags TEXT[] DEFAULT '{}',

    -- Intégrité
    checksum VARCHAR(32),
    parent_audit_id BIGINT REFERENCES audit_log(id)
);

-- Index pour recherche rapide
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_tenant ON audit_log(tenant_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_severity ON audit_log(severity);
CREATE INDEX IF NOT EXISTS idx_audit_log_tags ON audit_log USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_audit_log_ip ON audit_log(ip_address);

-- Table d'archive (même structure)
CREATE TABLE IF NOT EXISTS audit_log_archive (LIKE audit_log INCLUDING ALL);

-- Partitionnement par mois (optionnel pour gros volumes)
-- CREATE TABLE audit_log_partitioned (LIKE audit_log INCLUDING ALL)
-- PARTITION BY RANGE (timestamp);
"""


# =============================================================================
# FACTORY
# =============================================================================

def create_audit_trail(db_pool=None, retention_days: int = 365) -> AuditTrail:
    """Factory function pour créer un AuditTrail"""
    return AuditTrail(db_pool=db_pool, retention_days=retention_days)


# Exemple d'utilisation
if __name__ == "__main__":
    async def demo():
        trail = AuditTrail()

        # Contexte utilisateur
        ctx = AuditContext(
            user_id=1,
            username="admin",
            user_email="admin@example.com",
            tenant_id=1,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            source="web"
        )

        # Log création
        await trail.log_create(
            entity=AuditEntity.PRODUCT,
            entity_id=42,
            data={"name": "Tomate", "price": 2.50, "category": "Légumes"},
            context=ctx,
            entity_name="Tomate"
        )

        # Log update
        await trail.log_update(
            entity=AuditEntity.PRODUCT,
            entity_id=42,
            before={"name": "Tomate", "price": 2.50},
            after={"name": "Tomate", "price": 2.75},
            context=ctx,
            entity_name="Tomate"
        )

        # Log sécurité
        await trail.log_security_event(
            action=AuditAction.LOGIN,
            context=ctx,
            description="User logged in successfully"
        )

        # Recherche
        entries = await trail.search(AuditSearchCriteria(
            entities=[AuditEntity.PRODUCT],
            limit=10
        ))

        for entry in entries:
            print(f"{entry.timestamp} - {entry.action.value} - {entry.entity.value} #{entry.entity_id}")
            if entry.diff:
                for d in entry.diff:
                    print(f"  {d.field}: {d.old_value} -> {d.new_value}")

    asyncio.run(demo())
