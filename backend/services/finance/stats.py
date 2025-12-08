"""Services de synthèse finance (catégories, comptes)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sqlalchemy import text

from core.data_repository import query_df

logger = logging.getLogger(__name__)

# Active l'utilisation des vues matérialisées (plus rapide, mais données légèrement décalées)
USE_MATERIALIZED_VIEWS = True


def categories_stats(entity_id: int | None = None) -> List[dict]:
    params: Dict[str, Any] = {}

    # Essayer d'abord la vue matérialisée (plus rapide)
    if USE_MATERIALIZED_VIEWS:
        try:
            clauses: List[str] = []
            if entity_id is not None:
                clauses.append("entity_id = :entity_id")
                params["entity_id"] = int(entity_id)
            where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""

            df = query_df(
                text(
                    f"""
                    SELECT id, name, code,
                           SUM(inflow) AS inflow,
                           SUM(outflow) AS outflow,
                           SUM(lines) AS lines
                    FROM mv_finance_category_stats
                    {where_sql}
                    GROUP BY id, name, code
                    ORDER BY SUM(outflow) DESC NULLS LAST, SUM(inflow) DESC NULLS LAST
                    """
                ),
                params=params or None,
            )
            if not df.empty:
                return df.where(df.notna(), None).to_dict("records")
        except Exception as exc:
            logger.debug("Materialized view unavailable, falling back: %s", exc)

    # Fallback sur la requête directe
    clauses = ["t.direction IN ('IN','OUT')"]
    params = {}
    if entity_id is not None:
        clauses.append("t.entity_id = :entity_id")
        params["entity_id"] = int(entity_id)
    where_sql = "WHERE " + " AND ".join(clauses)
    df = query_df(
        text(
            f"""
            SELECT
              c.id,
              c.name,
              c.code,
              SUM(CASE WHEN t.direction = 'IN' THEN tl.montant_ttc ELSE 0 END) AS inflow,
              SUM(CASE WHEN t.direction = 'OUT' THEN tl.montant_ttc ELSE 0 END) AS outflow,
              COUNT(*) AS lines
            FROM finance_transaction_lines tl
            JOIN finance_transactions t ON t.id = tl.transaction_id
            LEFT JOIN finance_categories c ON c.id = tl.category_id
            {where_sql}
            GROUP BY c.id, c.name, c.code
            ORDER BY outflow DESC NULLS LAST, inflow DESC NULLS LAST
            """
        ),
        params=params or None,
    )
    return df.where(df.notna(), None).to_dict("records") if not df.empty else []


def accounts_overview(entity_id: int | None = None) -> List[dict]:
    params: Dict[str, Any] = {}

    # Essayer d'abord la vue matérialisée (plus rapide)
    if USE_MATERIALIZED_VIEWS:
        try:
            clauses: List[str] = []
            if entity_id is not None:
                clauses.append("entity_id = :entity_id")
                params["entity_id"] = int(entity_id)
            where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""

            df = query_df(
                text(
                    f"""
                    SELECT id, label,
                           SUM(inflow) AS inflow,
                           SUM(outflow) AS outflow,
                           MAX(last_activity) AS last_activity
                    FROM mv_finance_account_stats
                    {where_sql}
                    GROUP BY id, label
                    ORDER BY label
                    """
                ),
                params=params or None,
            )
            if not df.empty:
                rows = df.where(df.notna(), None).to_dict("records")
                for r in rows:
                    r["balance"] = (r.get("inflow") or 0) - (r.get("outflow") or 0)
                return rows
        except Exception as exc:
            logger.debug("Materialized view unavailable, falling back: %s", exc)

    # Fallback sur la requête directe
    clauses = ["t.direction IN ('IN','OUT')"]
    params = {}
    if entity_id is not None:
        clauses.append("t.entity_id = :entity_id")
        params["entity_id"] = int(entity_id)
    where_sql = "WHERE " + " AND ".join(clauses)
    df = query_df(
        text(
            f"""
            SELECT
              a.id,
              a.label,
              SUM(CASE WHEN t.direction = 'IN' THEN tl.montant_ttc ELSE 0 END) AS inflow,
              SUM(CASE WHEN t.direction = 'OUT' THEN tl.montant_ttc ELSE 0 END) AS outflow,
              MAX(t.date_operation)::date AS last_activity
            FROM finance_transaction_lines tl
            JOIN finance_transactions t ON t.id = tl.transaction_id
            JOIN finance_accounts a ON a.id = t.account_id
            {where_sql}
            GROUP BY a.id, a.label
            ORDER BY a.label
            """
        ),
        params=params or None,
    )
    rows = df.where(df.notna(), None).to_dict("records") if not df.empty else []
    for r in rows:
        r["balance"] = (r.get("inflow") or 0) - (r.get("outflow") or 0)
    return rows


def refresh_materialized_views() -> dict:
    """Rafraîchit les vues matérialisées de stats finance. À appeler périodiquement."""
    from core.data_repository import exec_sql

    refreshed = []
    for view_name in ["mv_finance_category_stats", "mv_finance_account_stats"]:
        try:
            exec_sql(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}"))
            refreshed.append(view_name)
        except Exception as exc:
            logger.warning("Failed to refresh %s: %s", view_name, exc)
    return {"refreshed": refreshed}


def timeline_stats(
    entity_id: int | None = None,
    months: int | None = 12,
    granularity: str = "monthly",
) -> List[dict]:
    """
    Retourne la chronologie agrégée des flux (inflow/outflow) par période.
    granularity: 'daily', 'weekly', 'monthly'
    """
    params: Dict[str, Any] = {}
    clauses: List[str] = ["t.direction IN ('IN','OUT')"]

    if entity_id is not None:
        clauses.append("t.entity_id = :entity_id")
        params["entity_id"] = int(entity_id)

    if months is not None and months > 0:
        clauses.append("t.date_operation >= CURRENT_DATE - INTERVAL ':months months'")
        params["months"] = int(months)

    where_sql = "WHERE " + " AND ".join(clauses)

    # Déterminer le format de regroupement
    if granularity == "daily":
        date_trunc = "day"
        date_format = "YYYY-MM-DD"
    elif granularity == "weekly":
        date_trunc = "week"
        date_format = "IYYY-IW"
    else:  # monthly par défaut
        date_trunc = "month"
        date_format = "YYYY-MM"

    df = query_df(
        text(
            f"""
            SELECT
              TO_CHAR(DATE_TRUNC('{date_trunc}', t.date_operation), '{date_format}') AS period,
              DATE_TRUNC('{date_trunc}', t.date_operation)::date AS period_start,
              SUM(CASE WHEN t.direction = 'IN' THEN tl.montant_ttc ELSE 0 END) AS inflow,
              SUM(CASE WHEN t.direction = 'OUT' THEN tl.montant_ttc ELSE 0 END) AS outflow,
              COUNT(*) AS tx_count
            FROM finance_transaction_lines tl
            JOIN finance_transactions t ON t.id = tl.transaction_id
            {where_sql}
            GROUP BY DATE_TRUNC('{date_trunc}', t.date_operation)
            ORDER BY DATE_TRUNC('{date_trunc}', t.date_operation)
            """
        ),
        params=params or None,
    )

    if df.empty:
        return []

    rows = df.where(df.notna(), None).to_dict("records")

    # Calculer le solde cumulé
    cumulative = 0.0
    for r in rows:
        inflow = float(r.get("inflow") or 0)
        outflow = float(r.get("outflow") or 0)
        r["net"] = inflow - outflow
        cumulative += r["net"]
        r["cumulative_balance"] = cumulative

    return rows


def category_breakdown(
    entity_id: int | None = None,
    months: int | None = 12,
    direction: str | None = None,
) -> List[dict]:
    """
    Retourne la répartition par catégorie pour les graphiques (pie/bar charts).
    direction: 'IN', 'OUT', ou None pour les deux.
    """
    params: Dict[str, Any] = {}
    clauses: List[str] = []

    if direction and direction.upper() in ("IN", "OUT"):
        clauses.append("t.direction = :direction")
        params["direction"] = direction.upper()
    else:
        clauses.append("t.direction IN ('IN','OUT')")

    if entity_id is not None:
        clauses.append("t.entity_id = :entity_id")
        params["entity_id"] = int(entity_id)

    if months is not None and months > 0:
        clauses.append("t.date_operation >= CURRENT_DATE - INTERVAL ':months months'")
        params["months"] = int(months)

    where_sql = "WHERE " + " AND ".join(clauses)

    df = query_df(
        text(
            f"""
            SELECT
              COALESCE(c.id, 0) AS category_id,
              COALESCE(c.name, 'Non catégorisé') AS category_name,
              COALESCE(c.code, 'uncategorized') AS category_code,
              SUM(tl.montant_ttc) AS amount,
              COUNT(*) AS tx_count
            FROM finance_transaction_lines tl
            JOIN finance_transactions t ON t.id = tl.transaction_id
            LEFT JOIN finance_categories c ON c.id = tl.category_id
            {where_sql}
            GROUP BY c.id, c.name, c.code
            ORDER BY SUM(tl.montant_ttc) DESC
            """
        ),
        params=params or None,
    )

    if df.empty:
        return []

    rows = df.where(df.notna(), None).to_dict("records")

    # Calculer les pourcentages
    total = sum(float(r.get("amount") or 0) for r in rows)
    for r in rows:
        amount = float(r.get("amount") or 0)
        r["percentage"] = round(amount / total * 100, 2) if total > 0 else 0.0

    return rows


def treasury_summary(entity_id: int | None = None) -> dict:
    """
    Retourne un résumé de trésorerie: totaux, solde, alertes.
    """
    params: Dict[str, Any] = {}
    clauses: List[str] = ["t.direction IN ('IN','OUT')"]

    if entity_id is not None:
        clauses.append("t.entity_id = :entity_id")
        params["entity_id"] = int(entity_id)

    where_sql = "WHERE " + " AND ".join(clauses)

    df = query_df(
        text(
            f"""
            SELECT
              SUM(CASE WHEN t.direction = 'IN' THEN tl.montant_ttc ELSE 0 END) AS total_inflow,
              SUM(CASE WHEN t.direction = 'OUT' THEN tl.montant_ttc ELSE 0 END) AS total_outflow,
              COUNT(*) AS total_transactions,
              MIN(t.date_operation) AS first_date,
              MAX(t.date_operation) AS last_date
            FROM finance_transaction_lines tl
            JOIN finance_transactions t ON t.id = tl.transaction_id
            {where_sql}
            """
        ),
        params=params or None,
    )

    if df.empty:
        return {
            "total_inflow": 0,
            "total_outflow": 0,
            "net_balance": 0,
            "total_transactions": 0,
            "first_date": None,
            "last_date": None,
        }

    row = df.iloc[0]
    inflow = float(row.get("total_inflow") or 0)
    outflow = float(row.get("total_outflow") or 0)

    return {
        "total_inflow": inflow,
        "total_outflow": outflow,
        "net_balance": inflow - outflow,
        "total_transactions": int(row.get("total_transactions") or 0),
        "first_date": str(row.get("first_date")) if row.get("first_date") else None,
        "last_date": str(row.get("last_date")) if row.get("last_date") else None,
    }
