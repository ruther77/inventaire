"""
API Endpoints pour Audit Trail
==============================

Endpoints pour:
- Consultation de l'historique d'audit
- Recherche avancée
- Rapports d'audit
- Historique par entité
- Export RGPD
"""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.dependencies.tenant import Tenant, get_current_tenant
from core.data_repository import query_df, exec_sql
from core.finance.audit_trail import (
    AuditTrail,
    AuditAction,
    AuditEntity,
    AuditSeverity,
    AuditContext,
    AuditSearchCriteria,
    AUDIT_LOG_SCHEMA,
)

router = APIRouter(prefix="/audit-trail", tags=["audit-trail"])


# =============================================================================
# SCHEMAS
# =============================================================================

class AuditEntryResponse(BaseModel):
    id: int
    timestamp: datetime
    action: str
    entity: str
    entity_id: Optional[int]
    entity_name: Optional[str]
    user_id: Optional[int]
    username: Optional[str]
    ip_address: Optional[str]
    severity: str
    description: Optional[str]
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None
    diff: Optional[List[dict]] = None
    tags: List[str] = []


class AuditSearchRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    actions: Optional[List[str]] = None
    entities: Optional[List[str]] = None
    entity_ids: Optional[List[int]] = None
    user_ids: Optional[List[int]] = None
    severities: Optional[List[str]] = None
    search_text: Optional[str] = None
    ip_address: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class AuditReportResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_entries: int
    actions_count: dict
    entities_count: dict
    users_activity: dict
    severity_count: dict
    security_events: int
    failed_logins: int
    suspicious_activities: List[dict]


class EntityHistoryResponse(BaseModel):
    entity: str
    entity_id: int
    total_changes: int
    first_seen: Optional[datetime]
    last_modified: Optional[datetime]
    history: List[AuditEntryResponse]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _ensure_audit_table():
    """S'assure que la table audit_log existe"""
    try:
        exec_sql(AUDIT_LOG_SCHEMA)
    except Exception:
        pass  # Table existe probablement déjà


def _row_to_response(row: dict) -> AuditEntryResponse:
    """Convertit une ligne DB en response"""
    import json

    before_state = row.get('before_state')
    if isinstance(before_state, str):
        before_state = json.loads(before_state)

    after_state = row.get('after_state')
    if isinstance(after_state, str):
        after_state = json.loads(after_state)

    diff = row.get('diff')
    if isinstance(diff, str):
        diff = json.loads(diff)

    return AuditEntryResponse(
        id=row['id'],
        timestamp=row['timestamp'],
        action=row['action'],
        entity=row['entity'],
        entity_id=row.get('entity_id'),
        entity_name=row.get('entity_name'),
        user_id=row.get('user_id'),
        username=row.get('username'),
        ip_address=str(row['ip_address']) if row.get('ip_address') else None,
        severity=row.get('severity', 'info'),
        description=row.get('description'),
        before_state=before_state,
        after_state=after_state,
        diff=diff,
        tags=row.get('tags', [])
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/entries", response_model=List[AuditEntryResponse])
def list_audit_entries(
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    action: Optional[str] = Query(default=None),
    entity: Optional[str] = Query(default=None),
    entity_id: Optional[int] = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Liste les entrées d'audit avec filtres optionnels.
    """
    _ensure_audit_table()

    conditions = ["tenant_id = :tenant_id"]
    params = {"tenant_id": tenant.id, "limit": limit, "offset": offset}

    if start_date:
        conditions.append("timestamp >= :start_date")
        params["start_date"] = start_date

    if end_date:
        conditions.append("timestamp <= :end_date")
        params["end_date"] = end_date

    if action:
        conditions.append("action = :action")
        params["action"] = action

    if entity:
        conditions.append("entity = :entity")
        params["entity"] = entity

    if entity_id:
        conditions.append("entity_id = :entity_id")
        params["entity_id"] = entity_id

    if user_id:
        conditions.append("user_id = :user_id")
        params["user_id"] = user_id

    if severity:
        conditions.append("severity = :severity")
        params["severity"] = severity

    if search:
        conditions.append("(description ILIKE :search OR entity_name ILIKE :search)")
        params["search"] = f"%{search}%"

    sql = f"""
        SELECT * FROM audit_log
        WHERE {' AND '.join(conditions)}
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
    """

    df = query_df(sql, params=params)
    if df.empty:
        return []

    return [_row_to_response(row) for _, row in df.iterrows()]


@router.post("/search", response_model=List[AuditEntryResponse])
def search_audit_entries(
    request: AuditSearchRequest,
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Recherche avancée dans l'audit log avec critères multiples.
    """
    _ensure_audit_table()

    conditions = ["tenant_id = :tenant_id"]
    params = {"tenant_id": tenant.id, "limit": request.limit, "offset": request.offset}

    if request.start_date:
        conditions.append("timestamp >= :start_date")
        params["start_date"] = request.start_date

    if request.end_date:
        conditions.append("timestamp <= :end_date")
        params["end_date"] = request.end_date

    if request.actions:
        conditions.append("action = ANY(:actions)")
        params["actions"] = request.actions

    if request.entities:
        conditions.append("entity = ANY(:entities)")
        params["entities"] = request.entities

    if request.entity_ids:
        conditions.append("entity_id = ANY(:entity_ids)")
        params["entity_ids"] = request.entity_ids

    if request.user_ids:
        conditions.append("user_id = ANY(:user_ids)")
        params["user_ids"] = request.user_ids

    if request.severities:
        conditions.append("severity = ANY(:severities)")
        params["severities"] = request.severities

    if request.search_text:
        conditions.append("(description ILIKE :search OR entity_name ILIKE :search)")
        params["search"] = f"%{request.search_text}%"

    if request.ip_address:
        conditions.append("ip_address = :ip_address")
        params["ip_address"] = request.ip_address

    if request.tags:
        conditions.append("tags && :tags")
        params["tags"] = request.tags

    sql = f"""
        SELECT * FROM audit_log
        WHERE {' AND '.join(conditions)}
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
    """

    df = query_df(sql, params=params)
    if df.empty:
        return []

    return [_row_to_response(row) for _, row in df.iterrows()]


@router.get("/entity/{entity}/{entity_id}", response_model=EntityHistoryResponse)
def get_entity_history(
    entity: str,
    entity_id: int,
    limit: int = Query(default=50, le=500),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne l'historique complet des modifications d'une entité.
    """
    _ensure_audit_table()

    sql = """
        SELECT * FROM audit_log
        WHERE tenant_id = :tenant_id
          AND entity = :entity
          AND entity_id = :entity_id
        ORDER BY timestamp DESC
        LIMIT :limit
    """

    df = query_df(sql, params={
        "tenant_id": tenant.id,
        "entity": entity,
        "entity_id": entity_id,
        "limit": limit
    })

    if df.empty:
        return EntityHistoryResponse(
            entity=entity,
            entity_id=entity_id,
            total_changes=0,
            first_seen=None,
            last_modified=None,
            history=[]
        )

    history = [_row_to_response(row) for _, row in df.iterrows()]

    return EntityHistoryResponse(
        entity=entity,
        entity_id=entity_id,
        total_changes=len(history),
        first_seen=history[-1].timestamp if history else None,
        last_modified=history[0].timestamp if history else None,
        history=history
    )


@router.get("/user/{user_id}", response_model=List[AuditEntryResponse])
def get_user_activity(
    user_id: int,
    start_date: Optional[datetime] = Query(default=None),
    limit: int = Query(default=100, le=500),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne l'activité d'un utilisateur spécifique.
    """
    _ensure_audit_table()

    conditions = ["tenant_id = :tenant_id", "user_id = :user_id"]
    params = {"tenant_id": tenant.id, "user_id": user_id, "limit": limit}

    if start_date:
        conditions.append("timestamp >= :start_date")
        params["start_date"] = start_date
    else:
        # Par défaut, 30 derniers jours
        params["start_date"] = datetime.now() - timedelta(days=30)
        conditions.append("timestamp >= :start_date")

    sql = f"""
        SELECT * FROM audit_log
        WHERE {' AND '.join(conditions)}
        ORDER BY timestamp DESC
        LIMIT :limit
    """

    df = query_df(sql, params=params)
    if df.empty:
        return []

    return [_row_to_response(row) for _, row in df.iterrows()]


@router.get("/report", response_model=AuditReportResponse)
def generate_audit_report(
    start_date: datetime = Query(default=None, description="Start date for report (defaults to 30 days ago)"),
    end_date: datetime = Query(default=None, description="End date for report (defaults to now)"),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Génère un rapport d'audit agrégé pour une période donnée.
    """
    _ensure_audit_table()

    # Défauts: 30 derniers jours si non spécifié
    from datetime import timedelta
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    params = {"tenant_id": tenant.id, "start_date": start_date, "end_date": end_date}

    # Total
    total_sql = """
        SELECT COUNT(*) as total FROM audit_log
        WHERE tenant_id = :tenant_id AND timestamp BETWEEN :start_date AND :end_date
    """
    total_df = query_df(total_sql, params=params)
    total = int(total_df.iloc[0]['total']) if not total_df.empty else 0

    # Par action
    actions_sql = """
        SELECT action, COUNT(*) as count FROM audit_log
        WHERE tenant_id = :tenant_id AND timestamp BETWEEN :start_date AND :end_date
        GROUP BY action ORDER BY count DESC
    """
    actions_df = query_df(actions_sql, params=params)
    actions_count = {row['action']: int(row['count']) for _, row in actions_df.iterrows()}

    # Par entité
    entities_sql = """
        SELECT entity, COUNT(*) as count FROM audit_log
        WHERE tenant_id = :tenant_id AND timestamp BETWEEN :start_date AND :end_date
        GROUP BY entity ORDER BY count DESC
    """
    entities_df = query_df(entities_sql, params=params)
    entities_count = {row['entity']: int(row['count']) for _, row in entities_df.iterrows()}

    # Par utilisateur
    users_sql = """
        SELECT username, COUNT(*) as count FROM audit_log
        WHERE tenant_id = :tenant_id AND timestamp BETWEEN :start_date AND :end_date
          AND username IS NOT NULL
        GROUP BY username ORDER BY count DESC LIMIT 20
    """
    users_df = query_df(users_sql, params=params)
    users_activity = {row['username']: int(row['count']) for _, row in users_df.iterrows()}

    # Par sévérité
    severity_sql = """
        SELECT severity, COUNT(*) as count FROM audit_log
        WHERE tenant_id = :tenant_id AND timestamp BETWEEN :start_date AND :end_date
        GROUP BY severity
    """
    severity_df = query_df(severity_sql, params=params)
    severity_count = {row['severity']: int(row['count']) for _, row in severity_df.iterrows()}

    # Événements sécurité
    security_sql = """
        SELECT COUNT(*) as count FROM audit_log
        WHERE tenant_id = :tenant_id AND timestamp BETWEEN :start_date AND :end_date
          AND severity = 'security'
    """
    security_df = query_df(security_sql, params=params)
    security_events = int(security_df.iloc[0]['count']) if not security_df.empty else 0

    # Échecs login
    failed_sql = """
        SELECT COUNT(*) as count FROM audit_log
        WHERE tenant_id = :tenant_id AND timestamp BETWEEN :start_date AND :end_date
          AND action = 'login_failed'
    """
    failed_df = query_df(failed_sql, params=params)
    failed_logins = int(failed_df.iloc[0]['count']) if not failed_df.empty else 0

    # Activités suspectes
    suspicious_sql = """
        SELECT ip_address::text, COUNT(*) as count
        FROM audit_log
        WHERE tenant_id = :tenant_id AND timestamp BETWEEN :start_date AND :end_date
          AND action = 'login_failed'
        GROUP BY ip_address
        HAVING COUNT(*) > 5
    """
    suspicious_df = query_df(suspicious_sql, params=params)
    suspicious_activities = [
        {"type": "multiple_failed_logins", "ip": row['ip_address'], "count": int(row['count'])}
        for _, row in suspicious_df.iterrows()
    ]

    return AuditReportResponse(
        period_start=start_date,
        period_end=end_date,
        total_entries=total,
        actions_count=actions_count,
        entities_count=entities_count,
        users_activity=users_activity,
        severity_count=severity_count,
        security_events=security_events,
        failed_logins=failed_logins,
        suspicious_activities=suspicious_activities
    )


@router.get("/security-events", response_model=List[AuditEntryResponse])
def get_security_events(
    days: int = Query(default=7, ge=1, le=90),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne les événements de sécurité récents.
    """
    _ensure_audit_table()

    sql = """
        SELECT * FROM audit_log
        WHERE tenant_id = :tenant_id
          AND timestamp >= CURRENT_TIMESTAMP - :days * INTERVAL '1 day'
          AND (severity = 'security' OR action IN ('login_failed', 'access_denied', 'permission_change'))
        ORDER BY timestamp DESC
        LIMIT 100
    """

    df = query_df(sql, params={"tenant_id": tenant.id, "days": days})
    if df.empty:
        return []

    return [_row_to_response(row) for _, row in df.iterrows()]


@router.get("/recent-changes", response_model=List[AuditEntryResponse])
def get_recent_changes(
    entity: Optional[str] = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Retourne les modifications récentes (dernières N heures).
    """
    _ensure_audit_table()

    conditions = [
        "tenant_id = :tenant_id",
        "timestamp >= CURRENT_TIMESTAMP - :hours * INTERVAL '1 hour'",
        "action IN ('create', 'update', 'delete', 'soft_delete')"
    ]
    params = {"tenant_id": tenant.id, "hours": hours}

    if entity:
        conditions.append("entity = :entity")
        params["entity"] = entity

    sql = f"""
        SELECT * FROM audit_log
        WHERE {' AND '.join(conditions)}
        ORDER BY timestamp DESC
        LIMIT 100
    """

    df = query_df(sql, params=params)
    if df.empty:
        return []

    return [_row_to_response(row) for _, row in df.iterrows()]


@router.get("/rgpd/export/{user_id}")
def export_user_data_rgpd(
    user_id: int,
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Export RGPD: Retourne toutes les données d'audit d'un utilisateur.
    """

    _ensure_audit_table()

    sql = """
        SELECT
            timestamp,
            action,
            entity,
            entity_id,
            description,
            ip_address::text
        FROM audit_log
        WHERE tenant_id = :tenant_id AND user_id = :user_id
        ORDER BY timestamp DESC
    """

    df = query_df(sql, params={"tenant_id": tenant.id, "user_id": user_id})

    return {
        "user_id": user_id,
        "export_date": datetime.now().isoformat(),
        "total_entries": len(df),
        "data": df.to_dict('records') if not df.empty else []
    }


@router.delete("/rgpd/anonymize/{user_id}")
def anonymize_user_data_rgpd(
    user_id: int,
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    RGPD: Anonymise les données d'un utilisateur dans l'audit log.
    Action irréversible!
    """
    _ensure_audit_table()

    sql = """
        UPDATE audit_log
        SET
            username = 'ANONYMIZED',
            user_email = 'anonymized@example.com',
            ip_address = '0.0.0.0',
            user_agent = 'ANONYMIZED',
            before_state = CASE WHEN before_state IS NOT NULL THEN '{"anonymized": true}'::jsonb ELSE NULL END,
            after_state = CASE WHEN after_state IS NOT NULL THEN '{"anonymized": true}'::jsonb ELSE NULL END,
            diff = NULL,
            metadata = CASE WHEN metadata IS NOT NULL THEN '{"anonymized": true}'::jsonb ELSE NULL END
        WHERE user_id = :user_id AND tenant_id = :tenant_id
    """

    exec_sql(sql, params={"user_id": user_id, "tenant_id": tenant.id})

    return {
        "status": "anonymized",
        "user_id": user_id,
        "anonymized_at": datetime.now().isoformat()
    }


@router.get("/summary")
def get_audit_summary(
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Résumé de l'activité d'audit:
    - Entrées aujourd'hui
    - Entrées cette semaine
    - Top actions
    - Alertes sécurité
    """
    _ensure_audit_table()

    params = {"tenant_id": tenant.id}

    # Aujourd'hui
    today_sql = """
        SELECT COUNT(*) as count FROM audit_log
        WHERE tenant_id = :tenant_id AND timestamp >= CURRENT_DATE
    """
    today_df = query_df(today_sql, params=params)
    today_count = int(today_df.iloc[0]['count']) if not today_df.empty else 0

    # Cette semaine
    week_sql = """
        SELECT COUNT(*) as count FROM audit_log
        WHERE tenant_id = :tenant_id AND timestamp >= CURRENT_DATE - INTERVAL '7 days'
    """
    week_df = query_df(week_sql, params=params)
    week_count = int(week_df.iloc[0]['count']) if not week_df.empty else 0

    # Top 5 actions aujourd'hui
    top_actions_sql = """
        SELECT action, COUNT(*) as count FROM audit_log
        WHERE tenant_id = :tenant_id AND timestamp >= CURRENT_DATE
        GROUP BY action ORDER BY count DESC LIMIT 5
    """
    top_actions_df = query_df(top_actions_sql, params=params)
    top_actions = [
        {"action": row['action'], "count": int(row['count'])}
        for _, row in top_actions_df.iterrows()
    ]

    # Alertes sécurité (7 derniers jours)
    security_sql = """
        SELECT COUNT(*) as count FROM audit_log
        WHERE tenant_id = :tenant_id
          AND timestamp >= CURRENT_DATE - INTERVAL '7 days'
          AND (severity = 'security' OR action = 'login_failed')
    """
    security_df = query_df(security_sql, params=params)
    security_alerts = int(security_df.iloc[0]['count']) if not security_df.empty else 0

    return {
        "entries_today": today_count,
        "entries_this_week": week_count,
        "top_actions_today": top_actions,
        "security_alerts_7_days": security_alerts
    }
