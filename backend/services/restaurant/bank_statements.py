"""Bank statement operations and summaries for restaurant module."""

from __future__ import annotations

from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import text

from core.data_repository import get_engine, query_df
from backend.services.restaurant.constants import CATEGORY_GROUP_PRESETS
from backend.services.restaurant.utils import (
    _safe_float,
    _get_restaurant_entity_id,
    _get_grouping_preset,
    _resolve_group_name,
    _ensure_depense_category,
)
from backend.services.restaurant.pdf_parser import parse_bank_statement_pdf
from backend.services.restaurant.expenses import get_expense_detail


def list_bank_statements(tenant_id: int, account: str | None = None) -> List[dict[str, Any]]:
    """Return bank statement lines using finance_* tables (optional account filter)."""
    entity_id = _get_restaurant_entity_id()
    account_clause = "AND a.label = :account" if account else ""
    sql = text(
        f"""
        SELECT
          tl.id AS id,
          a.label AS account,
          t.date_operation::date AS date,
          COALESCE(b.libelle_banque, t.note, '') AS libelle,
          c.name AS categorie,
          COALESCE(tl.montant_ttc, tl.montant_ht, 0) AS montant,
          CASE WHEN t.direction = 'IN' THEN 'Entree' ELSE 'Sortie' END AS type,
          TO_CHAR(t.date_operation, 'YYYY-MM') AS mois,
          NULL::bigint AS depense_id
        FROM finance_transaction_lines tl
        JOIN finance_transactions t ON t.id = tl.transaction_id
        JOIN finance_accounts a ON a.id = t.account_id
        LEFT JOIN finance_categories c ON c.id = tl.category_id
        LEFT JOIN finance_bank_statement_lines b
          ON t.ref_externe LIKE 'stmtline:%'
         AND b.id = CAST(substring(t.ref_externe FROM 'stmtline:(\\d+)') AS BIGINT)
        WHERE t.entity_id = :entity_id
          AND t.status = 'CONFIRMED'
          AND t.direction IN ('IN', 'OUT')
          {account_clause}
        ORDER BY t.date_operation DESC, tl.id DESC
        """
    )
    params: dict[str, Any] = {"entity_id": entity_id}
    if account:
        params["account"] = account
    df = query_df(sql, params)
    if df.empty:
        return []

    df = df.where(pd.notna(df), None)
    return df.to_dict("records")


def list_bank_accounts_overview(tenant_id: int) -> List[dict[str, Any]]:
    """Summary by account (volume, flows, last activity)."""
    entity_id = _get_restaurant_entity_id()
    sql = text(
        """
        SELECT
            a.label AS account,
            COUNT(*) AS operations,
            SUM(CASE WHEN t.direction = 'IN' THEN COALESCE(tl.montant_ttc, tl.montant_ht, 0) ELSE 0 END) AS inflow,
            SUM(CASE WHEN t.direction = 'OUT' THEN COALESCE(tl.montant_ttc, tl.montant_ht, 0) ELSE 0 END) AS outflow,
            MAX(t.date_operation)::date AS last_activity
        FROM finance_transaction_lines tl
        JOIN finance_transactions t ON t.id = tl.transaction_id
        JOIN finance_accounts a ON a.id = t.account_id
        WHERE t.entity_id = :entity_id
          AND t.status = 'CONFIRMED'
          AND t.direction IN ('IN', 'OUT')
        GROUP BY a.label
        ORDER BY a.label
        """
    )
    df = query_df(sql, {"entity_id": entity_id})
    overview: List[dict[str, Any]] = []
    today = date.today()
    if df.empty:
        return overview

    for record in df.to_dict("records"):
        last_activity = record.get("last_activity")
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.strptime(last_activity, "%Y-%m-%d").date()
            except ValueError:
                last_activity = None
        balance = _safe_float(record.get("inflow")) - _safe_float(record.get("outflow"))
        days_since: Optional[int] = None
        if isinstance(last_activity, date):
            days_since = (today - last_activity).days

        if days_since is None:
            status = "disconnected"
        elif days_since <= 7:
            status = "connected"
        elif days_since <= 30:
            status = "warning"
        else:
            status = "error"

        overview.append(
            {
                "account": record.get("account"),
                "display_name": record.get("account"),
                "provider": (record.get("account") or "").split()[0] if record.get("account") else None,
                "status": status,
                "balance": round(balance, 2),
                "inflow": round(_safe_float(record.get("inflow")), 2),
                "outflow": round(_safe_float(record.get("outflow")), 2),
                "operations": int(record.get("operations") or 0),
                "last_activity": last_activity,
                "currency": "EUR",
            }
        )
    return overview


def create_bank_statement(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Insert an imported/edited bank statement line."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_bank_statements (
                    tenant_id, account, date, libelle, categorie, montant, type, mois
                ) VALUES (
                    :tenant, :account, :date, :libelle, :categorie, :montant, :type, :mois
                )
                RETURNING id, account, date, libelle, categorie, montant, type, mois, depense_id
                """
            ),
            {
                **payload,
                "tenant": tenant_id,
            },
        ).fetchone()
    return dict(row._mapping)


def update_bank_statement(tenant_id: int, entry_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Update an existing statement and return enriched version."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                UPDATE restaurant_bank_statements
                SET account = :account,
                    date = :date,
                    libelle = :libelle,
                    categorie = :categorie,
                    montant = :montant,
                    type = :type,
                    mois = :mois,
                    depense_id = COALESCE(:depense_id, depense_id)
                WHERE tenant_id = :tenant AND id = :id
                RETURNING id, account, date, libelle, categorie, montant, type, mois, depense_id
                """
            ),
            {
                **payload,
                "tenant": tenant_id,
                "id": entry_id,
            },
        ).fetchone()
        if not row:
            raise RuntimeError("Releve introuvable")
    return dict(row._mapping)


def import_bank_statements_from_pdf(tenant_id: int, account: str, pdf_bytes: bytes) -> dict[str, int]:
    """Parse a PDF statement and insert new operations for the given account."""
    entries = parse_bank_statement_pdf(pdf_bytes)
    if not entries:
        return {"inserted": 0, "total": 0}

    inserted = 0
    with get_engine().begin() as conn:
        for entry in entries:
            params = {
                "tenant": tenant_id,
                "account": account,
                "date": entry["date"],
                "libelle": entry["libelle"],
                "categorie": entry.get("categorie"),
                "montant": entry["montant"],
                "type": entry["type"],
                "mois": entry["mois"],
                "source": entry.get("source", "pdf"),
            }
            row = conn.execute(
                text(
                    """
                    INSERT INTO restaurant_bank_statements (
                        tenant_id, account, date, libelle, categorie,
                        montant, type, mois, source
                    ) VALUES (
                        :tenant, :account, :date, :libelle, :categorie,
                        :montant, :type, :mois, :source
                    )
                    ON CONFLICT DO NOTHING
                    RETURNING id
                    """
                ),
                params,
            ).fetchone()
            if row:
                inserted += 1
    return {"inserted": inserted, "total": len(entries)}


def create_expense_from_bank_statement(tenant_id: int, entry_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Create an expense from a bank statement and link them."""
    eng = get_engine()
    with eng.begin() as conn:
        statement = conn.execute(
            text(
                """
                SELECT id, account, date, libelle, categorie, montant, type, mois, depense_id
                FROM restaurant_bank_statements
                WHERE tenant_id = :tenant AND id = :id
                """
            ),
            {"tenant": tenant_id, "id": entry_id},
        ).fetchone()
        if not statement:
            raise RuntimeError("Releve introuvable")
        if statement.depense_id:
            raise RuntimeError("Une depense est deja associee a ce releve")

        libelle = payload.get("libelle") or statement.libelle
        montant_ht = payload.get("montant_ht")
        if montant_ht is None:
            montant_ht = abs(_safe_float(statement.montant))
        date_operation = payload.get("date_operation") or statement.date
        category_name = payload.get("categorie_nom") or statement.categorie
        category_id = payload.get("categorie_id")
        if not category_id:
            category_id = _ensure_depense_category(conn, tenant_id, category_name)
        params = {
            "tenant": tenant_id,
            "categorie_id": category_id,
            "fournisseur_id": payload.get("fournisseur_id"),
            "cost_center_id": payload.get("cost_center_id"),
            "libelle": libelle,
            "unite": payload.get("unite"),
            "quantite": payload.get("quantite"),
            "prix_unitaire": payload.get("prix_unitaire"),
            "montant_ht": montant_ht,
            "tva_pct": payload.get("tva_pct", 20.0),
            "date_operation": date_operation,
            "source": "bank_statement",
            "ref_externe": f"statement:{entry_id}",
        }
        expense_row = conn.execute(
            text(
                """
                INSERT INTO restaurant_depenses (
                    tenant_id, categorie_id, fournisseur_id, cost_center_id,
                    libelle, unite, quantite, prix_unitaire, montant_ht,
                    tva_pct, date_operation, source, ref_externe
                ) VALUES (
                    :tenant, :categorie_id, :fournisseur_id, :cost_center_id,
                    :libelle, :unite, :quantite, :prix_unitaire, :montant_ht,
                    :tva_pct, :date_operation, :source, :ref_externe
                )
                RETURNING id, libelle, montant_ht, date_operation
                """
            ),
            params,
        ).fetchone()

        conn.execute(
            text(
                """
                UPDATE restaurant_bank_statements
                SET depense_id = :depense_id
                WHERE tenant_id = :tenant AND id = :id
                """
            ),
            {"tenant": tenant_id, "id": entry_id, "depense_id": expense_row.id},
        )

    expense = get_expense_detail(tenant_id, expense_row.id)
    updated_statement = list_bank_statements(tenant_id, account=statement.account)
    statement_dict = next((item for item in updated_statement if item["id"] == entry_id), None)
    return {"expense": expense, "statement": statement_dict}


def transfer_from_epicerie(tenant_id: int, produit_restaurant_id: int, quantite: float = 1.0) -> Dict[str, Any]:
    """Call SQL function transfer_from_epicerie for cross movements epicerie -> restaurant."""
    eng = get_engine()
    with eng.begin() as conn:
        rows = conn.execute(
            text("SELECT * FROM transfer_from_epicerie(:pid, :qty)"),
            {"pid": int(produit_restaurant_id), "qty": float(quantite)},
        ).mappings().all()
    if not rows:
        raise RuntimeError("Aucun mouvement genere (mapping manquant ?)")
    return {"movements": rows}


def get_bank_statement_summary(
    tenant_id: int, account: str | None = None, months: int = 6, grouping: str | None = None
) -> Dict[str, Any]:
    """Build daily/weekly/monthly aggregates and category groups."""
    entity_id = _get_restaurant_entity_id()
    window: int | None = None
    if months and months > 0:
        window = max(1, min(months, 120))
    preset_name, preset = _get_grouping_preset(grouping)
    account_clause = "AND a.label = :account" if account else ""
    date_clause = ""
    if window is not None:
        date_clause = f"AND t.date_operation >= (CURRENT_DATE - INTERVAL '{window} months')"
    sql = text(
        f"""
        SELECT
          t.date_operation::date AS date,
          TO_CHAR(t.date_operation, 'YYYY-MM') AS mois,
          c.name AS categorie,
          COALESCE(tl.montant_ttc, tl.montant_ht, 0) AS montant,
          CASE WHEN t.direction = 'IN' THEN 'Entree' ELSE 'Sortie' END AS type
        FROM finance_transaction_lines tl
        JOIN finance_transactions t ON t.id = tl.transaction_id
        JOIN finance_accounts a ON a.id = t.account_id
        LEFT JOIN finance_categories c ON c.id = tl.category_id
        WHERE t.entity_id = :entity_id
          AND t.status = 'CONFIRMED'
          AND t.direction IN ('IN', 'OUT')
          {account_clause}
          {date_clause}
        ORDER BY t.date_operation ASC, tl.id ASC
        """
    )
    params: Dict[str, Any] = {"entity_id": entity_id}
    if account:
        params["account"] = account
    df = query_df(sql, params)

    monthly_ordered: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    weekly_ordered: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    daily_ordered: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    groups_totals: Dict[str, Dict[str, float]] = defaultdict(lambda: {"entrees": 0.0, "sorties": 0.0})

    if not df.empty:
        for row in df.to_dict("records"):
            row_date = row.get("date")
            if isinstance(row_date, str):
                try:
                    row_date = datetime.strptime(row_date, "%Y-%m-%d").date()
                except ValueError:
                    row_date = None
            if not isinstance(row_date, date):
                row_date = date.today()
            month_key = row.get("mois") or row_date.strftime("%Y-%m")
            iso_week = row_date.isocalendar()
            week_key = f"{iso_week.year}-W{iso_week.week:02d}"
            week_start = row_date - timedelta(days=row_date.weekday())
            week_end = week_start + timedelta(days=6)
            day_key = row_date.isoformat()
            entry_type = row.get("type") or "Sortie"
            amount = _safe_float(row.get("montant"))
            month_bucket = monthly_ordered.setdefault(
                month_key, {"mois": month_key, "entrees": 0.0, "sorties": 0.0}
            )
            week_bucket = weekly_ordered.setdefault(
                week_key,
                {
                    "semaine": week_key,
                    "start_date": week_start,
                    "end_date": week_end,
                    "entrees": 0.0,
                    "sorties": 0.0,
                },
            )
            day_bucket = daily_ordered.setdefault(
                day_key,
                {
                    "jour": row_date,
                    "entrees": 0.0,
                    "sorties": 0.0,
                },
            )
            if entry_type == "Entree":
                month_bucket["entrees"] += amount
                week_bucket["entrees"] += amount
                day_bucket["entrees"] += amount
            else:
                month_bucket["sorties"] += amount
                week_bucket["sorties"] += amount
                day_bucket["sorties"] += amount

            group_name = _resolve_group_name(row.get("categorie"), entry_type, preset)
            group_bucket = groups_totals[group_name]
            if entry_type == "Entree":
                group_bucket["entrees"] += amount
            else:
                group_bucket["sorties"] += amount

    monthly_summary: List[Dict[str, Any]] = []
    for bucket in monthly_ordered.values():
        bucket["net"] = bucket["entrees"] - bucket["sorties"]
        monthly_summary.append(
            {
                "mois": bucket["mois"],
                "entrees": round(bucket["entrees"], 2),
                "sorties": round(bucket["sorties"], 2),
                "net": round(bucket["net"], 2),
            }
        )

    weekly_summary: List[Dict[str, Any]] = []
    for bucket in weekly_ordered.values():
        net = bucket["entrees"] - bucket["sorties"]
        weekly_summary.append(
            {
                "semaine": bucket["semaine"],
                "start_date": bucket["start_date"],
                "end_date": bucket["end_date"],
                "entrees": round(bucket["entrees"], 2),
                "sorties": round(bucket["sorties"], 2),
                "net": round(net, 2),
            }
        )

    daily_summary: List[Dict[str, Any]] = []
    for bucket in daily_ordered.values():
        net = bucket["entrees"] - bucket["sorties"]
        daily_summary.append(
            {
                "jour": bucket["jour"],
                "entrees": round(bucket["entrees"], 2),
                "sorties": round(bucket["sorties"], 2),
                "net": round(net, 2),
            }
        )

    group_summary: List[Dict[str, Any]] = []
    for group_name, totals in groups_totals.items():
        net = totals["entrees"] - totals["sorties"]
        group_summary.append(
            {
                "group": group_name,
                "entrees": round(totals["entrees"], 2),
                "sorties": round(totals["sorties"], 2),
                "net": round(net, 2),
            }
        )
    group_summary.sort(key=lambda item: item["sorties"], reverse=True)

    forecast_value: float | None = None
    if monthly_summary:
        recent = [item["net"] for item in monthly_summary[-3:] if item["net"] is not None]
        if recent:
            forecast_value = round(sum(recent) / len(recent), 2)

    presets_meta = [
        {
            "name": key,
            "label": value.get("label", key.title()),
            "groups": list(value.get("groups", {}).keys()),
        }
        for key, value in CATEGORY_GROUP_PRESETS.items()
    ]

    effective_months = window if window is not None else 0
    return {
        "account": account,
        "months": effective_months,
        "grouping": preset_name,
        "monthly": monthly_summary,
        "weekly": weekly_summary,
        "daily": daily_summary,
        "groups": group_summary,
        "forecast_next_month": forecast_value,
        "presets": presets_meta,
    }
