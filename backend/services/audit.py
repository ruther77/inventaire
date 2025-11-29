"""Audit and stock discrepancy services."""

from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, List, Sequence

import numpy as np
import pandas as pd
from sqlalchemy import text

from backend.services.catalog_data import fetch_customer_catalog
from core.data_repository import get_engine, query_df

CRITICAL_THRESHOLD = 10
MODERATE_THRESHOLD = 3
CLOSED_STATUS = "Clôturé"

_DIAGNOSTIC_SQL = """
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
        LEFT JOIN mouvements_stock m
            ON m.produit_id = p.id
           AND m.tenant_id = :tenant_id
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
"""


def _fetch_stock_diagnostics_df(tenant_id: int) -> pd.DataFrame:
    return query_df(_DIAGNOSTIC_SQL, params={"tenant_id": int(tenant_id)})


def _load_actions_df(tenant_id: int) -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, product_id, responsable, note, status, due_date, created_at, updated_at
                FROM audit_actions
                WHERE tenant_id = :tenant_id
                ORDER BY created_at ASC
                """
            ),
            {"tenant_id": int(tenant_id)},
        ).fetchall()

    if not rows:
        return pd.DataFrame(columns=["id", "product_id", "responsable", "note", "status", "due_date", "created_at"])

    return pd.DataFrame(
        rows,
        columns=["id", "product_id", "responsable", "note", "status", "due_date", "created_at", "updated_at"],
    )


def _load_resolution_log_df(tenant_id: int, limit: int | None = None) -> pd.DataFrame:
    limit_clause = ""
    if limit is not None and limit > 0:
        limit_clause = f"LIMIT {int(limit)}"

    sql = f"""
        SELECT id, action_id, product_id, statut, note, responsable, created_at
        FROM audit_resolution_log
        WHERE tenant_id = :tenant_id
        ORDER BY created_at DESC
        {limit_clause}
    """
    return query_df(sql, params={"tenant_id": int(tenant_id)})


def list_diagnostics(
    *,
    categories: Iterable[str] | None = None,
    levels: Iterable[str] | None = None,
    min_abs: float | None = None,
    max_abs: float | None = None,
    tenant_id: int = 1,
) -> dict[str, object]:
    diag_df = _fetch_stock_diagnostics_df(int(tenant_id))
    if diag_df.empty:
        return {
            "available_categories": [],
            "summary": {"anomalies": 0, "delta": 0.0, "assigned": 0, "open_tasks": 0},
            "items": [],
        }

    catalog_df = fetch_customer_catalog(tenant_id=int(tenant_id))[["id", "categorie"]]
    diag_df = diag_df.merge(catalog_df, on="id", how="left")
    diag_df["ecart_abs"] = diag_df["ecart"].abs()
    severity_levels = np.select(
        [
            diag_df["ecart_abs"] >= CRITICAL_THRESHOLD,
            diag_df["ecart_abs"] >= MODERATE_THRESHOLD,
        ],
        ["Critique", "Modéré"],
        default="Mineur",
    )
    diag_df["niveau_ecart"] = severity_levels

    actions_df = _load_actions_df(int(tenant_id))
    if not actions_df.empty:
        latest_actions = (
            actions_df.sort_values("created_at")
            .drop_duplicates("product_id", keep="last")
            .rename(columns={"id": "action_id", "status": "action_status"})
        )
        diag_df = diag_df.merge(
            latest_actions[["product_id", "action_id", "responsable", "action_status"]],
            left_on="id",
            right_on="product_id",
            how="left",
        )
        diag_df = diag_df.drop(columns=["product_id_y"], errors="ignore")
    else:
        diag_df["action_id"] = np.nan
        diag_df["responsable"] = None
        diag_df["action_status"] = None

    diag_df["categorie"] = diag_df["categorie"].fillna("Non renseigné")
    available_categories = sorted(diag_df["categorie"].dropna().unique().tolist())

    filtered = diag_df.copy()
    if categories:
        categories_set = {cat for cat in categories if cat}
        if categories_set:
            filtered = filtered[filtered["categorie"].isin(categories_set)]

    if levels:
        level_set = {level for level in levels if level}
        if level_set:
            filtered = filtered[filtered["niveau_ecart"].isin(level_set)]

    min_value = 0.0 if filtered.empty else float(filtered["ecart_abs"].min())
    max_value = 0.0 if filtered.empty else float(filtered["ecart_abs"].max())

    lower_bound = min_abs if min_abs is not None else min_value
    upper_bound = max_abs if max_abs is not None else max_value

    filtered = filtered[
        (filtered["ecart_abs"] >= lower_bound)
        & (filtered["ecart_abs"] <= (upper_bound if upper_bound >= lower_bound else lower_bound))
    ]

    open_tasks = 0
    if not actions_df.empty:
        open_tasks = int((actions_df["status"] != CLOSED_STATUS).sum())

    summary = {
        "anomalies": int(len(filtered)),
        "delta": float(filtered["ecart"].sum()) if not filtered.empty else 0.0,
        "assigned": int(filtered["action_id"].notna().sum()),
        "open_tasks": open_tasks,
    }

    items: List[dict[str, object]] = []
    for row in filtered.itertuples():
        items.append(
            {
                "product_id": int(row.id),
                "nom": row.nom,
                "categorie": row.categorie,
                "stock_actuel": float(row.stock_actuel),
                "stock_calcule": float(row.stock_calcule),
                "ecart": float(row.ecart),
                "ecart_abs": float(row.ecart_abs),
                "niveau_ecart": row.niveau_ecart,
                "responsable": row.responsable,
                "action_status": row.action_status,
                "action_id": int(row.action_id) if pd.notna(row.action_id) else None,
            }
        )

    return {
        "available_categories": available_categories,
        "summary": summary,
        "items": items,
    }


def list_actions(*, include_closed: bool = False, tenant_id: int = 1) -> list[dict[str, object]]:
    sql = f"""
        SELECT
            a.id,
            a.product_id,
            p.nom AS produit,
            a.responsable,
            a.note,
            a.status,
            a.due_date,
            a.created_at
        FROM audit_actions a
        JOIN produits p ON p.id = a.product_id
        WHERE p.tenant_id = :tenant_id AND a.tenant_id = :tenant_id
        {"AND a.status <> :closed" if not include_closed else ""}
        ORDER BY a.created_at DESC
    """

    params = {"tenant_id": int(tenant_id)}
    if not include_closed:
        params["closed"] = CLOSED_STATUS
    df = query_df(text(sql), params=params)
    if df.empty:
        return []
    return [
        {
            "id": int(row.id),
            "product_id": int(row.product_id),
            "produit": row.produit,
            "responsable": row.responsable,
            "note": row.note,
            "status": row.status,
            "due_date": row.due_date.isoformat() if row.due_date else None,
            "created_at": row.created_at.isoformat(),
        }
        for row in df.itertuples()
    ]


def list_resolution_log(limit: int = 100, *, tenant_id: int = 1) -> list[dict[str, object]]:
    df = _load_resolution_log_df(int(tenant_id), limit=limit)
    if df.empty:
        return []
    return [
        {
            "id": int(row.id),
            "action_id": int(row.action_id) if row.action_id is not None else None,
            "product_id": int(row.product_id),
            "statut": row.statut,
            "note": row.note,
            "responsable": row.responsable,
            "created_at": row.created_at.isoformat(),
        }
        for row in df.itertuples()
    ]


def create_assignment(
    *,
    product_id: int,
    responsable: str,
    note: str | None,
    due_date: date | None,
    create_task: bool,
    tenant_id: int = 1,
) -> dict[str, object]:
    if not responsable:
        raise ValueError("Le responsable est obligatoire.")

    status = "À compter" if create_task else "À investiguer"
    engine = get_engine()
    with engine.begin() as conn:
        product_exists = conn.execute(
            text("SELECT 1 FROM produits WHERE id = :pid AND tenant_id = :tenant_id"),
            {"pid": product_id, "tenant_id": int(tenant_id)},
        ).scalar()
        if not product_exists:
            raise ValueError("Produit introuvable pour ce tenant.")

        row = conn.execute(
            text(
                """
                INSERT INTO audit_actions (product_id, responsable, note, status, due_date, tenant_id)
                VALUES (:product_id, :responsable, :note, :status, :due_date, :tenant_id)
                RETURNING id, product_id, responsable, note, status, due_date, created_at
                """
            ),
            {
                "product_id": product_id,
                "responsable": responsable,
                "note": note,
                "status": status,
                "due_date": due_date,
                "tenant_id": int(tenant_id),
            },
        ).fetchone()

    return {
        "id": int(row.id),
        "product_id": int(row.product_id),
        "responsable": row.responsable,
        "note": row.note,
        "status": row.status,
        "due_date": row.due_date.isoformat() if row.due_date else None,
        "created_at": row.created_at.isoformat(),
    }


def update_action_status(
    *,
    action_id: int,
    status: str,
    note: str | None = None,
    tenant_id: int = 1,
) -> dict[str, object]:
    target_status = status
    if status == "Résolu":
        target_status = CLOSED_STATUS
    elif status not in {"En cours", "Résolu"}:
        raise ValueError("Statut invalide.")

    engine = get_engine()
    with engine.begin() as conn:
        action_row = conn.execute(
            text(
                """
                SELECT id, product_id, responsable
                FROM audit_actions
                WHERE id = :action_id AND tenant_id = :tenant_id
                """
            ),
            {"action_id": action_id, "tenant_id": int(tenant_id)},
        ).fetchone()

        if action_row is None:
            raise ValueError(f"Aucune action trouvée pour l'identifiant {action_id}.")

        conn.execute(
            text(
                """
                UPDATE audit_actions
                SET status = :status, updated_at = now()
                WHERE id = :action_id AND tenant_id = :tenant_id
                """
            ),
            {"status": target_status, "action_id": action_id, "tenant_id": int(tenant_id)},
        )

        conn.execute(
            text(
                """
                INSERT INTO audit_resolution_log (action_id, product_id, statut, note, responsable, tenant_id)
                VALUES (:action_id, :product_id, :statut, :note, :responsable, :tenant_id)
                """
            ),
            {
                "action_id": action_id,
                "product_id": action_row.product_id,
                "statut": status,
                "note": note,
                "responsable": action_row.responsable,
                "tenant_id": int(tenant_id),
            },
        )

    return {
        "action_id": action_id,
        "status": target_status,
    }


__all__ = [
    "list_diagnostics",
    "list_actions",
    "list_resolution_log",
    "create_assignment",
    "update_action_status",
]
