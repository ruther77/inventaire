"""
Module de statistiques et agrégations financières.

Ce module fournit les services pour:
- Statistiques par catégorie (inflow/outflow/count)
- Vue d'ensemble des comptes avec soldes
- Chronologie agrégée des flux financiers
- Répartition par catégorie pour graphiques
- Résumé de trésorerie consolidé

Performance:
Utilise des vues matérialisées pour optimiser les requêtes lourdes:
- mv_daily_balance: Solde journalier par compte (rafraîchissement quotidien)
- mv_category_monthly: Répartition mensuelle par catégorie
- mv_reconciliation_status: État de rapprochement par compte
- mv_top_vendors: Top fournisseurs par montant
- mv_import_summary: Résumé des importations

Les vues sont rafraîchies manuellement via refresh_materialized_views() ou
automatiquement par un job périodique. En cas d'indisponibilité, le système
bascule automatiquement sur des requêtes directes (fallback).

Note:
    Les vues matérialisées offrent des gains de 10x à 100x en performance
    sur les requêtes d'agrégation complexes, au prix d'une fraîcheur
    des données potentiellement décalée.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sqlalchemy import text

from core.data_repository import query_df
from backend.cache import cached, CacheTTL

logger = logging.getLogger(__name__)

# Active l'utilisation des vues matérialisées (plus rapide)
# Les vues sont rafraîchies via refresh_materialized_views()
USE_MATERIALIZED_VIEWS = True


def categories_stats(entity_id: int | None = None) -> List[dict]:
    """Retourne les stats par catégorie (inflow/outflow/count)."""
    params: Dict[str, Any] = {}

    # Utiliser la vue matérialisée mv_category_monthly
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
                    SELECT
                        COALESCE(category_id, 0) AS id,
                        COALESCE(category_name, 'Non catégorisé') AS name,
                        SUM(CASE WHEN direction = 'IN' THEN total_amount ELSE 0 END) AS inflow,
                        SUM(CASE WHEN direction = 'OUT' THEN total_amount ELSE 0 END) AS outflow,
                        SUM(tx_count) AS lines
                    FROM mv_category_monthly
                    {where_sql}
                    GROUP BY COALESCE(category_id, 0), COALESCE(category_name, 'Non catégorisé')
                    ORDER BY SUM(CASE WHEN direction = 'OUT' THEN total_amount ELSE 0 END) DESC NULLS LAST
                    """
                ),
                params=params or None,
            )
            if not df.empty:
                return df.where(df.notna(), None).to_dict("records")
        except Exception as exc:
            logger.debug("Vue matérialisée indisponible, fallback: %s", exc)

    # Repli sur la requête directe
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
              COALESCE(c.id, 0) AS id,
              COALESCE(c.name, 'Non catégorisé') AS name,
              COALESCE(c.code, 'uncategorized') AS code,
              SUM(CASE WHEN t.direction = 'IN' THEN t.amount ELSE 0 END) AS inflow,
              SUM(CASE WHEN t.direction = 'OUT' THEN t.amount ELSE 0 END) AS outflow,
              COUNT(*) AS lines
            FROM finance_transactions t
            LEFT JOIN finance_transaction_lines tl ON tl.transaction_id = t.id
            LEFT JOIN finance_transaction_classification tc ON tc.transaction_id = t.id
            LEFT JOIN finance_categories c ON c.id = COALESCE(tl.category_id, tc.category_id)
            {where_sql}
            GROUP BY COALESCE(c.id, 0), COALESCE(c.name, 'Non catégorisé'), COALESCE(c.code, 'uncategorized')
            ORDER BY outflow DESC NULLS LAST, inflow DESC NULLS LAST
            """
        ),
        params=params or None,
    )
    return df.where(df.notna(), None).to_dict("records") if not df.empty else []


def accounts_overview(entity_id: int | None = None) -> List[dict]:
    """Retourne un aperçu de chaque compte (inflow/outflow/balance/match_rate)."""
    params: Dict[str, Any] = {}

    # Utiliser la vue matérialisée mv_reconciliation_status
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
                    SELECT
                        account_id AS id,
                        account_name AS label,
                        total_credits AS inflow,
                        total_debits AS outflow,
                        total_credits - total_debits AS balance,
                        last_transaction AS last_activity,
                        total_transactions,
                        matched_with_invoice,
                        unmatched,
                        match_rate_percent
                    FROM mv_reconciliation_status
                    {where_sql}
                    ORDER BY account_name
                    """
                ),
                params=params or None,
            )
            if not df.empty:
                return df.where(df.notna(), None).to_dict("records")
        except Exception as exc:
            logger.debug("Vue matérialisée indisponible, fallback: %s", exc)

    # Repli sur la requête directe
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
              SUM(CASE WHEN t.direction = 'IN' THEN t.amount ELSE 0 END) AS inflow,
              SUM(CASE WHEN t.direction = 'OUT' THEN t.amount ELSE 0 END) AS outflow,
              MAX(t.date_operation)::date AS last_activity
            FROM finance_transactions t
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
    """Rafraîchit les vues matérialisées de stats finance.

    Délègue au service views.py pour un rafraîchissement complet.
    """
    from backend.services.finance.views import refresh_materialized_views as refresh_views

    results = refresh_views(concurrent=True)
    return {
        "refreshed": [r.view_name for r in results if r.status == "success"],
        "failed": [r.view_name for r in results if r.status != "success"],
        "details": [
            {"view": r.view_name, "status": r.status, "duration_ms": r.duration_ms}
            for r in results
        ],
    }


def timeline_stats(
    entity_id: int | None = None,
    months: int | None = 12,
    granularity: str = "monthly",
    account_id: int | None = None,
) -> List[dict]:
    """Retourne la chronologie agrégée des flux (inflow/outflow) par période.

    Args:
        entity_id: Filtrer par entité
        months: Nombre de mois d'historique (défaut: 12)
        granularity: 'daily', 'weekly', 'monthly'
        account_id: Filtrer par compte (utilise mv_daily_balance)
    """
    params: Dict[str, Any] = {}

    # Pour la granularité journalière avec account_id, utiliser mv_daily_balance
    if USE_MATERIALIZED_VIEWS and granularity == "daily" and account_id is not None:
        try:
            clauses: List[str] = ["account_id = :account_id"]
            params["account_id"] = int(account_id)

            if months is not None and months > 0:
                clauses.append(f"date >= CURRENT_DATE - INTERVAL '{int(months)} months'")

            where_sql = "WHERE " + " AND ".join(clauses)

            df = query_df(
                text(
                    f"""
                    SELECT
                        TO_CHAR(date, 'YYYY-MM-DD') AS period,
                        date AS period_start,
                        credits AS inflow,
                        debits AS outflow,
                        net,
                        transaction_count AS tx_count
                    FROM mv_daily_balance
                    {where_sql}
                    ORDER BY date
                    """
                ),
                params=params or None,
            )

            if not df.empty:
                rows = df.where(df.notna(), None).to_dict("records")
                # Calculer le solde cumulé
                cumulative = 0.0
                for r in rows:
                    cumulative += float(r.get("net") or 0)
                    r["cumulative_balance"] = cumulative
                return rows
        except Exception as exc:
            logger.debug("Vue matérialisée indisponible, fallback: %s", exc)

    # Repli sur la requête directe
    clauses = ["t.direction IN ('IN','OUT')"]
    params = {}

    if entity_id is not None:
        clauses.append("t.entity_id = :entity_id")
        params["entity_id"] = int(entity_id)

    if account_id is not None:
        clauses.append("t.account_id = :account_id")
        params["account_id"] = int(account_id)

    if months is not None and months > 0:
        clauses.append(f"t.date_operation >= CURRENT_DATE - INTERVAL '{int(months)} months'")

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
              SUM(CASE WHEN t.direction = 'IN' THEN t.amount ELSE 0 END) AS inflow,
              SUM(CASE WHEN t.direction = 'OUT' THEN t.amount ELSE 0 END) AS outflow,
              COUNT(*) AS tx_count
            FROM finance_transactions t
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
    """Retourne la répartition par catégorie pour les graphiques (pie/bar charts).

    Args:
        entity_id: Filtrer par entité
        months: Nombre de mois d'historique (défaut: 12)
        direction: 'IN', 'OUT', ou None pour les deux
    """
    params: Dict[str, Any] = {}

    # Utiliser la vue matérialisée mv_category_monthly
    if USE_MATERIALIZED_VIEWS:
        try:
            clauses: List[str] = []

            if direction and direction.upper() in ("IN", "OUT"):
                clauses.append("direction = :direction")
                params["direction"] = direction.upper()

            if entity_id is not None:
                clauses.append("entity_id = :entity_id")
                params["entity_id"] = int(entity_id)

            if months is not None and months > 0:
                clauses.append(f"month >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '{int(months)} months')")

            where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""

            df = query_df(
                text(
                    f"""
                    SELECT
                        COALESCE(category_id, 0) AS category_id,
                        COALESCE(category_name, 'Non catégorisé') AS category_name,
                        SUM(total_amount) AS amount,
                        SUM(tx_count) AS tx_count
                    FROM mv_category_monthly
                    {where_sql}
                    GROUP BY COALESCE(category_id, 0), COALESCE(category_name, 'Non catégorisé')
                    ORDER BY SUM(total_amount) DESC
                    """
                ),
                params=params or None,
            )

            if not df.empty:
                rows = df.where(df.notna(), None).to_dict("records")
                total = sum(float(r.get("amount") or 0) for r in rows)
                for r in rows:
                    amount = float(r.get("amount") or 0)
                    r["percentage"] = round(amount / total * 100, 2) if total > 0 else 0.0
                return rows
        except Exception as exc:
            logger.debug("Vue matérialisée indisponible, fallback: %s", exc)

    # Repli sur la requête directe
    clauses = []

    if direction and direction.upper() in ("IN", "OUT"):
        clauses.append("t.direction = :direction")
        params["direction"] = direction.upper()
    else:
        clauses.append("t.direction IN ('IN','OUT')")

    if entity_id is not None:
        clauses.append("t.entity_id = :entity_id")
        params["entity_id"] = int(entity_id)

    if months is not None and months > 0:
        clauses.append(f"t.date_operation >= CURRENT_DATE - INTERVAL '{int(months)} months'")

    where_sql = "WHERE " + " AND ".join(clauses)

    df = query_df(
        text(
            f"""
            SELECT
              COALESCE(c.id, 0) AS category_id,
              COALESCE(c.name, 'Non catégorisé') AS category_name,
              COALESCE(c.code, 'uncategorized') AS category_code,
              SUM(t.amount) AS amount,
              COUNT(*) AS tx_count
            FROM finance_transactions t
            LEFT JOIN finance_transaction_lines tl ON tl.transaction_id = t.id
            LEFT JOIN finance_transaction_classification tc ON tc.transaction_id = t.id
            LEFT JOIN finance_categories c ON c.id = COALESCE(tl.category_id, tc.category_id)
            {where_sql}
            GROUP BY c.id, c.name, c.code
            ORDER BY SUM(t.amount) DESC
            """
        ),
        params=params or None,
    )

    if df.empty:
        return []

    rows = df.where(df.notna(), None).to_dict("records")
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
              SUM(CASE WHEN t.direction = 'IN' THEN t.amount ELSE 0 END) AS total_inflow,
              SUM(CASE WHEN t.direction = 'OUT' THEN t.amount ELSE 0 END) AS total_outflow,
              COUNT(*) AS total_transactions,
              MIN(t.date_operation) AS first_date,
              MAX(t.date_operation) AS last_date
            FROM finance_transactions t
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


def top_vendors(
    entity_id: int | None = None,
    months: int | None = 12,
    limit: int = 20,
) -> List[dict]:
    """Retourne les principaux fournisseurs par montant.

    Utilise la vue matérialisée mv_top_vendors.

    Args:
        entity_id: Filtrer par entité
        months: Nombre de mois d'historique (défaut: 12)
        limit: Nombre max de résultats (défaut: 20)
    """
    params: Dict[str, Any] = {"limit": limit}
    clauses: List[str] = []

    if entity_id is not None:
        clauses.append("entity_id = :entity_id")
        params["entity_id"] = int(entity_id)

    if months is not None and months > 0:
        clauses.append(f"month >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '{int(months)} months')")

    where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""

    df = query_df(
        text(
            f"""
            SELECT
                vendor_name,
                vendor_id,
                SUM(invoice_count) AS invoice_count,
                SUM(total_amount) AS total_amount,
                AVG(avg_amount) AS avg_amount,
                MIN(first_transaction) AS first_transaction,
                MAX(last_transaction) AS last_transaction
            FROM mv_top_vendors
            {where_sql}
            GROUP BY vendor_name, vendor_id
            ORDER BY SUM(total_amount) DESC
            LIMIT :limit
            """
        ),
        params=params,
    )

    if df.empty:
        return []

    return df.where(df.notna(), None).to_dict("records")


def import_summary(
    account_id: int | None = None,
    months: int | None = 12,
) -> List[dict]:
    """Retourne le résumé des importations par compte et période.

    Utilise la vue matérialisée mv_import_summary.

    Args:
        account_id: Filtrer par compte
        months: Nombre de mois d'historique (défaut: 12)
    """
    params: Dict[str, Any] = {}
    clauses: List[str] = []

    if account_id is not None:
        clauses.append("account_id = :account_id")
        params["account_id"] = int(account_id)

    if months is not None and months > 0:
        clauses.append(f"period_month >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '{int(months)} months')")

    where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""

    df = query_df(
        text(
            f"""
            SELECT
                account_id,
                account_name,
                period_month,
                statement_count,
                total_lines,
                earliest_period,
                latest_period,
                last_import
            FROM mv_import_summary
            {where_sql}
            ORDER BY period_month DESC
            """
        ),
        params=params or None,
    )

    if df.empty:
        return []

    return df.where(df.notna(), None).to_dict("records")


@cached(ttl=CacheTTL.SHORT, prefix="reconciliation_dashboard", tenant_aware=False)
def reconciliation_dashboard(entity_id: int | None = None) -> List[dict]:
    """Retourne le dashboard de rapprochement par compte.

    Utilise la vue matérialisée mv_reconciliation_status.

    Args:
        entity_id: Filtrer par entité
    """
    params: Dict[str, Any] = {}
    clauses: List[str] = []

    if entity_id is not None:
        clauses.append("entity_id = :entity_id")
        params["entity_id"] = int(entity_id)

    where_sql = "WHERE " + " AND ".join(clauses) if clauses else ""

    df = query_df(
        text(
            f"""
            SELECT
                account_id,
                account_name,
                total_transactions,
                matched_with_invoice,
                unmatched,
                match_rate_percent,
                first_transaction,
                last_transaction,
                total_debits,
                total_credits
            FROM mv_reconciliation_status
            {where_sql}
            ORDER BY total_transactions DESC
            """
        ),
        params=params or None,
    )

    if df.empty:
        return []

    return df.where(df.notna(), None).to_dict("records")
