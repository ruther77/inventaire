"""Service pour gérer les jobs zero-click avec persistance en base de données."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from core.data_repository import exec_sql, get_engine, query_df

LOGGER = logging.getLogger(__name__)


def create_job(
    job_id: str,
    tenant_id: int,
    filename: str | None = None,
    supplier_hint: str | None = None,
    margin_percent: float = 40.0,
    auto_confirm: bool = True,
) -> dict[str, Any]:
    """Crée un nouveau job zero-click en base de données."""
    sql = text("""
        INSERT INTO zero_click_jobs (
            job_id, tenant_id, status, filename, supplier_hint,
            margin_percent, auto_confirm, created_at, updated_at
        )
        VALUES (
            :job_id, :tenant_id, 'pending', :filename, :supplier_hint,
            :margin_percent, :auto_confirm, NOW(), NOW()
        )
        RETURNING job_id, status, created_at
    """)

    result = execute_raw_sql(
        sql,
        params={
            "job_id": job_id,
            "tenant_id": tenant_id,
            "filename": filename,
            "supplier_hint": supplier_hint,
            "margin_percent": margin_percent,
            "auto_confirm": auto_confirm,
        },
        fetch=True,
    )

    if result:
        return {
            "job_id": result[0][0],
            "status": result[0][1],
            "created_at": result[0][2],
        }

    raise RuntimeError("Échec de création du job")


def update_job_status(
    job_id: str,
    status: str,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    """Met à jour le statut d'un job."""
    now = datetime.now(timezone.utc)

    params: dict[str, Any] = {
        "job_id": job_id,
        "status": status,
        "updated_at": now,
    }

    if status in ("completed", "failed"):
        params["completed_at"] = now
    else:
        params["completed_at"] = None

    if result is not None:
        import json
        params["result"] = json.dumps(result)
    else:
        params["result"] = None

    params["error"] = error

    sql = text("""
        UPDATE zero_click_jobs
        SET status = :status,
            result = :result::jsonb,
            error = :error,
            updated_at = :updated_at,
            completed_at = :completed_at
        WHERE job_id = :job_id
    """)

    execute_raw_sql(sql, params=params)


def get_job(job_id: str, tenant_id: int | None = None) -> dict[str, Any] | None:
    """Récupère un job par son ID."""
    where_clause = "job_id = :job_id"
    params: dict[str, Any] = {"job_id": job_id}

    if tenant_id is not None:
        where_clause += " AND tenant_id = :tenant_id"
        params["tenant_id"] = tenant_id

    sql = text(f"""
        SELECT
            job_id, tenant_id, status, filename, supplier_hint,
            margin_percent, auto_confirm, result, error,
            created_at, updated_at, completed_at
        FROM zero_click_jobs
        WHERE {where_clause}
    """)

    result = execute_raw_sql(sql, params=params, fetch=True)

    if not result:
        return None

    row = result[0]
    import json

    return {
        "job_id": row[0],
        "tenant_id": row[1],
        "status": row[2],
        "filename": row[3],
        "supplier_hint": row[4],
        "margin_percent": float(row[5]) if row[5] is not None else 40.0,
        "auto_confirm": bool(row[6]) if row[6] is not None else True,
        "result": json.loads(row[7]) if row[7] else None,
        "error": row[8],
        "created_at": row[9],
        "updated_at": row[10],
        "completed_at": row[11],
    }


def list_jobs(
    tenant_id: int,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Liste les jobs d'un tenant avec filtres optionnels."""
    where_clause = "tenant_id = :tenant_id"
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit, "offset": offset}

    if status:
        where_clause += " AND status = :status"
        params["status"] = status

    # Compter le total
    count_sql = text(f"""
        SELECT COUNT(*)
        FROM zero_click_jobs
        WHERE {where_clause}
    """)

    count_result = execute_raw_sql(count_sql, params=params, fetch=True)
    total = count_result[0][0] if count_result else 0

    # Récupérer les jobs
    sql = text(f"""
        SELECT
            job_id, tenant_id, status, filename, supplier_hint,
            margin_percent, auto_confirm, result, error,
            created_at, updated_at, completed_at
        FROM zero_click_jobs
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """)

    result = execute_raw_sql(sql, params=params, fetch=True)

    if not result:
        return [], total

    import json

    jobs = []
    for row in result:
        jobs.append({
            "job_id": row[0],
            "tenant_id": row[1],
            "status": row[2],
            "filename": row[3],
            "supplier_hint": row[4],
            "margin_percent": float(row[5]) if row[5] is not None else 40.0,
            "auto_confirm": bool(row[6]) if row[6] is not None else True,
            "result": json.loads(row[7]) if row[7] else None,
            "error": row[8],
            "created_at": row[9],
            "updated_at": row[10],
            "completed_at": row[11],
        })

    return jobs, total


def delete_old_jobs(days: int = 30) -> int:
    """Supprime les jobs terminés de plus de N jours."""
    sql = text("""
        DELETE FROM zero_click_jobs
        WHERE completed_at IS NOT NULL
          AND completed_at < NOW() - INTERVAL ':days days'
    """)

    result = execute_raw_sql(sql, params={"days": days})
    return result if isinstance(result, int) else 0


__all__ = [
    "create_job",
    "update_job_status",
    "get_job",
    "list_jobs",
    "delete_old_jobs",
]
def execute_raw_sql(sql, params=None, fetch=False):
    """Compat: exécution SQL simple avec option de fetch."""
    stmt = text(sql) if isinstance(sql, str) else sql
    eng = get_engine()
    with eng.begin() as conn:
        result = conn.execute(stmt, params or {})
        if fetch:
            return result.fetchall()
        return None
