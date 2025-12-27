"""
Module de gestion des jobs zero-click (import automatisé).

Ce module fournit les services pour:
- Création de jobs d'import automatisé de factures
- Suivi du statut des jobs (pending, processing, completed, failed)
- Persistance en base de données avec tracking temporel
- Gestion des erreurs et retry automatiques
- Récupération de l'état et de l'historique des jobs

Workflow zero-click:
1. Client uploade une facture PDF
2. Job créé avec statut 'pending'
3. Worker Celery traite le job en arrière-plan
4. Extraction OCR des données (supplier, items, amounts)
5. Application des marges et règles métier
6. Création automatique des produits/commandes si auto_confirm=True
7. Job marqué 'completed' ou 'failed' avec résultat/erreur

Statuts possibles:
- pending: Job créé, en attente de traitement
- processing: Job en cours de traitement par un worker
- completed: Job terminé avec succès
- failed: Job échoué avec message d'erreur

Note:
    Les jobs sont associés à un tenant_id pour isolation multi-tenant
    et à un session_id optionnel pour le tracking utilisateur.
"""

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
    session_id: str | None = None,
) -> dict[str, Any]:
    """Crée un nouveau job zero-click en base de données."""
    sql = text("""
        INSERT INTO zero_click_jobs (
            job_id, tenant_id, session_id, status, filename, supplier_hint,
            margin_percent, auto_confirm, created_at, updated_at
        )
        VALUES (
            :job_id, :tenant_id, :session_id, 'pending', :filename, :supplier_hint,
            :margin_percent, :auto_confirm, NOW(), NOW()
        )
        RETURNING job_id, status, created_at
    """)

    result = execute_raw_sql(
        sql,
        params={
            "job_id": job_id,
            "tenant_id": tenant_id,
            "session_id": session_id,
            "filename": filename,
            "supplier_hint": supplier_hint,
            "margin_percent": margin_percent,
            "auto_confirm": auto_confirm,
        },
        fetch=True,
    )

    if result and len(result) > 0:
        row = result[0]
        return {
            "job_id": row[0] if len(row) > 0 else None,
            "status": row[1] if len(row) > 1 else "pending",
            "created_at": row[2] if len(row) > 2 else None,
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
            job_id, tenant_id, session_id, status, filename, supplier_hint,
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
        "session_id": row[2],
        "status": row[3],
        "filename": row[4],
        "supplier_hint": row[5],
        "margin_percent": float(row[6]) if row[6] is not None else 40.0,
        "auto_confirm": bool(row[7]) if row[7] is not None else True,
        "result": json.loads(row[8]) if row[8] else None,
        "error": row[9],
        "created_at": row[10],
        "updated_at": row[11],
        "completed_at": row[12],
    }


def list_jobs(
    tenant_id: int,
    status: str | None = None,
    session_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Liste les jobs d'un tenant avec filtres optionnels."""
    where_clause = "tenant_id = :tenant_id"
    params: dict[str, Any] = {"tenant_id": tenant_id, "limit": limit, "offset": offset}

    if status:
        where_clause += " AND status = :status"
        params["status"] = status

    if session_id:
        where_clause += " AND session_id = :session_id"
        params["session_id"] = session_id

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
            job_id, tenant_id, session_id, status, filename, supplier_hint,
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
            "session_id": row[2],
            "status": row[3],
            "filename": row[4],
            "supplier_hint": row[5],
            "margin_percent": float(row[6]) if row[6] is not None else 40.0,
            "auto_confirm": bool(row[7]) if row[7] is not None else True,
            "result": json.loads(row[8]) if row[8] else None,
            "error": row[9],
            "created_at": row[10],
            "updated_at": row[11],
            "completed_at": row[12],
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


def list_import_sessions(
    tenant_id: int,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Liste les sessions d'import avec statistiques agrégées."""
    # Compter le total de sessions
    count_sql = text("""
        SELECT COUNT(DISTINCT session_id)
        FROM zero_click_jobs
        WHERE tenant_id = :tenant_id
          AND session_id IS NOT NULL
    """)

    count_result = execute_raw_sql(count_sql, params={"tenant_id": tenant_id}, fetch=True)
    total = count_result[0][0] if count_result else 0

    # Récupérer les sessions avec stats
    sql = text("""
        SELECT
            session_id,
            MIN(created_at) as date_debut,
            MAX(completed_at) as date_fin,
            COUNT(*) as nb_imports,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as nb_completed,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as nb_failed,
            SUM(
                CASE
                    WHEN result IS NOT NULL
                    THEN COALESCE((result->>'rows_received')::int, 0)
                    ELSE 0
                END
            ) as total_lignes,
            SUM(
                CASE
                    WHEN result IS NOT NULL
                    THEN COALESCE((result->>'movements_created')::int, 0)
                    ELSE 0
                END
            ) as total_mouvements,
            SUM(
                CASE
                    WHEN result IS NOT NULL
                    THEN COALESCE((result->>'products_created')::int, 0)
                    ELSE 0
                END
            ) as total_produits_crees,
            STRING_AGG(DISTINCT supplier_hint, ', ' ORDER BY supplier_hint) as fournisseurs
        FROM zero_click_jobs
        WHERE tenant_id = :tenant_id
          AND session_id IS NOT NULL
        GROUP BY session_id
        ORDER BY date_debut DESC
        LIMIT :limit OFFSET :offset
    """)

    result = execute_raw_sql(
        sql,
        params={"tenant_id": tenant_id, "limit": limit, "offset": offset},
        fetch=True,
    )

    if not result:
        return [], total

    sessions = []
    for row in result:
        sessions.append({
            "session_id": row[0],
            "date_debut": row[1],
            "date_fin": row[2],
            "nb_imports": row[3],
            "nb_completed": row[4],
            "nb_failed": row[5],
            "total_lignes": row[6] or 0,
            "total_mouvements": row[7] or 0,
            "total_produits_crees": row[8] or 0,
            "fournisseurs": row[9],
        })

    return sessions, total


def get_session_details(
    session_id: str,
    tenant_id: int,
) -> dict[str, Any] | None:
    """Récupère tous les imports d'une session donnée."""
    # Récupérer les jobs de la session
    jobs, total = list_jobs(
        tenant_id=tenant_id,
        session_id=session_id,
        limit=1000,  # Limite haute pour récupérer tous les imports d'une session
        offset=0,
    )

    if not jobs:
        return None

    # Calculer les statistiques de la session
    session_stats = {
        "session_id": session_id,
        "nb_imports": len(jobs),
        "nb_completed": sum(1 for j in jobs if j["status"] == "completed"),
        "nb_failed": sum(1 for j in jobs if j["status"] == "failed"),
        "nb_pending": sum(1 for j in jobs if j["status"] in ("pending", "processing")),
        "date_debut": min(j["created_at"] for j in jobs if j["created_at"]),
        "date_fin": max((j["completed_at"] for j in jobs if j["completed_at"]), default=None),
        "total_lignes": sum(
            j["result"].get("rows_received", 0)
            for j in jobs
            if j["result"]
        ),
        "total_mouvements": sum(
            j["result"].get("movements_created", 0)
            for j in jobs
            if j["result"]
        ),
        "total_produits_crees": sum(
            j["result"].get("products_created", 0)
            for j in jobs
            if j["result"]
        ),
        "fournisseurs": list(set(
            j["supplier_hint"]
            for j in jobs
            if j.get("supplier_hint")
        )),
        "imports": jobs,
    }

    return session_stats


__all__ = [
    "create_job",
    "update_job_status",
    "get_job",
    "list_jobs",
    "delete_old_jobs",
    "list_import_sessions",
    "get_session_details",
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
