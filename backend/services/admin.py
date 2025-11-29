"""Admin utilities exposed through the FastAPI router."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.backup_manager import (
    BackupError,
    BinaryStatus,
    build_backup_timeline,
    check_backup_tools,
    compute_backup_statistics,
    create_backup,
    delete_backup,
    integrity_report,
    list_backups,
    load_backup_settings,
    plan_next_backup,
    restore_backup,
    save_backup_settings,
    suggest_retention_cleanup,
)
from core.data_repository import query_df
from core.user_service import ALLOWED_ROLES, list_users as list_users_df, reset_user_password, update_user_role

ALLOWED_TABLE_PREVIEWS: frozenset[str] = frozenset({"produits", "produits_barcodes", "mouvements_stock"})


def _records(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    df = query_df(sql, params=params)
    if df.empty:
        return []
    return df.to_dict(orient="records")


def fetch_table_counts(*, tenant_id: int) -> list[dict[str, Any]]:
    sql = """
        SELECT 'produits' AS table, COUNT(*) AS lignes FROM produits WHERE tenant_id = :tenant_id
        UNION ALL
        SELECT 'produits_barcodes' AS table, COUNT(*) AS lignes FROM produits_barcodes WHERE tenant_id = :tenant_id
        UNION ALL
        SELECT 'mouvements_stock' AS table, COUNT(*) AS lignes FROM mouvements_stock WHERE tenant_id = :tenant_id
    """
    return _records(sql, params={"tenant_id": int(tenant_id)})


def fetch_stock_diagnostics(*, tenant_id: int, limit: int = 50) -> list[dict[str, Any]]:
    sql = f"""
        WITH stock_compare AS (
            SELECT
                p.id,
                p.nom,
                p.stock_actuel,
                COALESCE(SUM(CASE
                    WHEN m.type = 'ENTREE' THEN m.quantite
                    WHEN m.type = 'SORTIE' THEN -m.quantite
                    WHEN m.type = 'INVENTAIRE' THEN m.quantite
                    WHEN m.type = 'TRANSFERT' THEN m.quantite
                    ELSE 0
                END), 0) AS stock_calcule
            FROM produits p
            LEFT JOIN mouvements_stock m ON m.produit_id = p.id AND m.tenant_id = :tenant_id
            WHERE p.tenant_id = :tenant_id
            GROUP BY p.id, p.nom, p.stock_actuel
        )
        SELECT
            id,
            nom,
            stock_actuel,
            stock_calcule,
            ROUND(stock_actuel - stock_calcule, 3) AS ecart
        FROM stock_compare
        WHERE ABS(stock_actuel - stock_calcule) > 0.001
        ORDER BY ABS(stock_actuel - stock_calcule) DESC, nom
        LIMIT {max(1, int(limit))}
    """
    return _records(sql, params={"tenant_id": int(tenant_id)})


def fetch_recent_movements(*, tenant_id: int, limit: int = 20) -> list[dict[str, Any]]:
    sql = """
        SELECT
            m.date_mvt,
            p.nom AS produit,
            m.type,
            m.quantite,
            m.source
        FROM mouvements_stock m
        JOIN produits p ON p.id = m.produit_id
        WHERE m.tenant_id = :tenant_id
          AND p.tenant_id = :tenant_id
        ORDER BY m.date_mvt DESC
        LIMIT :limit
    """
    df = query_df(sql, params={"limit": max(1, int(limit)), "tenant_id": int(tenant_id)})
    if df.empty:
        return []
    df["date_mvt"] = df["date_mvt"].astype("datetime64[ns]")
    return df.to_dict(orient="records")


def fetch_table_preview(table_name: str, limit: int = 50) -> list[dict[str, Any]]:
    if table_name not in ALLOWED_TABLE_PREVIEWS:
        raise ValueError("Table non autorisée.")
    sql = f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT :limit"
    return _records(sql, params={"limit": max(1, int(limit))})


def serialize_backup(metadata) -> dict[str, Any]:
    return {
        "name": metadata.name,
        "size_bytes": metadata.size_bytes,
        "created_at": metadata.created_at,
        "path": str(metadata.path),
    }


def serialize_binary_status(status: BinaryStatus) -> dict[str, Any]:
    return {
        "name": status.name,
        "configured": status.configured,
        "resolved": status.resolved,
        "source": status.source,
        "available": status.available,
    }


def fetch_backup_overview() -> dict[str, Any]:
    backups = list_backups()
    settings = load_backup_settings()
    tools = check_backup_tools()

    summary: dict[str, Any] = {
        "count": len(backups),
        "stats": compute_backup_statistics(backups),
        "next_run": None,
    }

    if backups:
        next_run = plan_next_backup(settings, last_backup=backups[0])
    else:
        next_run = plan_next_backup(settings)

    if next_run:
        summary["next_run"] = next_run

    recent = [serialize_backup(meta) for meta in backups[:20]]
    timeline = build_backup_timeline(backups[:50])

    cleanup = [
        meta.name
        for meta in suggest_retention_cleanup(
            backups,
            retention_days=settings.get("retention_days"),
            max_backups=settings.get("max_backups"),
        )
    ]

    return {
        "summary": summary,
        "recent": recent,
        "timeline": timeline,
        "tool_status": [serialize_binary_status(status) for status in tools],
        "settings": settings,
        "suggested_cleanup": cleanup,
    }


def fetch_admin_overview(*, tenant_id: int) -> dict[str, Any]:
    return {
        "backups": fetch_backup_overview(),
        "table_counts": fetch_table_counts(tenant_id=tenant_id),
        "diagnostics": fetch_stock_diagnostics(tenant_id=tenant_id),
        "recent_movements": fetch_recent_movements(tenant_id=tenant_id),
    }


def list_admin_users() -> list[dict[str, Any]]:
    df = list_users_df()
    if df.empty:
        return []
    df["created_at"] = df["created_at"].astype("datetime64[ns]")
    return df.to_dict(orient="records")


def update_role(user_id: int, role: str) -> None:
    update_user_role(int(user_id), role)


def reset_password(user_id: int, new_password: str | None = None) -> str:
    return reset_user_password(int(user_id), new_password)


def save_settings(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = {
        "frequency": payload.get("frequency", "manual"),
        "time": payload.get("time", "02:00"),
        "weekday": int(payload.get("weekday", 0)),
        "retention_days": int(payload.get("retention_days", 30)),
        "max_backups": int(payload.get("max_backups", 20)),
        "notifications": payload.get("notifications", []),
        "integrity_checks": bool(payload.get("integrity_checks", True)),
    }
    cleaned["weekday"] = max(0, min(cleaned["weekday"], 6))
    cleaned["retention_days"] = max(1, min(cleaned["retention_days"], 365))
    cleaned["max_backups"] = max(1, min(cleaned["max_backups"], 500))
    save_backup_settings(cleaned)
    return cleaned


def create_backup_now(label: str | None = None) -> dict[str, Any]:
    metadata = create_backup(label=label, database_url=None)
    return serialize_backup(metadata)


def restore_backup_file(filename: str) -> None:
    restore_backup(filename, database_url=None)


def delete_backup_file(filename: str) -> None:
    delete_backup(filename)


def run_integrity_report() -> list[dict[str, Any]]:
    backups = list_backups()
    report = integrity_report(backups)
    for row in report:
        if isinstance(row.get("created_at"), datetime):
            row["created_at"] = row["created_at"].isoformat()
    return report


__all__ = [
    "ALLOWED_ROLES",
    "BackupError",
    "create_backup_now",
    "delete_backup_file",
    "fetch_admin_overview",
    "fetch_backup_overview",
    "fetch_recent_movements",
    "fetch_stock_diagnostics",
    "fetch_table_counts",
    "fetch_table_preview",
    "list_admin_users",
    "reset_password",
    "restore_backup_file",
    "run_integrity_report",
    "save_settings",
    "update_role",
]
