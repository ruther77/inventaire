"""Stock analytics and adjustments."""

from __future__ import annotations

from typing import Optional

import pandas as pd
from sqlalchemy import text

from core.data_repository import get_engine, query_df


def fetch_movement_timeseries(
    window_days: int = 30,
    product_id: Optional[int] = None,
    *,
    tenant_id: int = 1,
) -> pd.DataFrame:
    sql = """
        SELECT
            date_trunc('day', m.date_mvt) AS jour,
            m.type,
            SUM(m.quantite) AS quantite
        FROM mouvements_stock m
        WHERE m.date_mvt >= now() - (:window * INTERVAL '1 day')
          AND m.tenant_id = :tenant_id
    """
    params: dict[str, object] = {
        "window": int(max(1, window_days)),
        "tenant_id": int(tenant_id),
    }
    if product_id is not None:
        sql += " AND m.produit_id = :pid"
        params["pid"] = int(product_id)

    sql += """
        GROUP BY 1, m.type
        ORDER BY jour ASC, m.type
    """
    df = query_df(sql, params=params)
    if not df.empty:
        df["jour"] = pd.to_datetime(df["jour"]).dt.date
    return df


def fetch_recent_movements(
    limit: int = 100,
    product_id: Optional[int] = None,
    *,
    tenant_id: int = 1,
) -> pd.DataFrame:
    sql = """
        SELECT
            m.id,
            m.date_mvt,
            p.id AS produit_id,
            p.nom AS produit,
            m.type,
            m.quantite,
            m.source
        FROM mouvements_stock m
        JOIN produits p ON p.id = m.produit_id
        WHERE m.tenant_id = :tenant_id
          AND p.tenant_id = :tenant_id
    """
    params: dict[str, object] = {
        "limit": int(max(1, limit)),
        "tenant_id": int(tenant_id),
    }
    if product_id is not None:
        sql += " AND m.produit_id = :pid"
        params["pid"] = int(product_id)

    sql += " ORDER BY m.date_mvt DESC LIMIT :limit"
    df = query_df(sql, params=params)
    return df


def adjust_stock_level(
    product_id: int,
    target_quantity: float,
    *,
    username: str | None = None,
    tenant_id: int = 1,
) -> dict[str, object]:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                "SELECT nom, COALESCE(stock_actuel, 0) AS stock_actuel "
                "FROM produits WHERE id = :pid AND tenant_id = :tenant_id FOR UPDATE"
            ),
            {"pid": product_id, "tenant_id": int(tenant_id)},
        ).fetchone()
        if row is None:
            raise ValueError(f"Produit {product_id} introuvable.")

        current_stock = float(row.stock_actuel or 0.0)
        delta = float(target_quantity) - current_stock
        if abs(delta) < 1e-6:
            return {
                "product_id": product_id,
                "product_name": row.nom,
                "current_stock": current_stock,
                "new_stock": current_stock,
                "movement_created": False,
            }

        movement_type = "ENTREE" if delta > 0 else "SORTIE"
        payload = {
            "pid": product_id,
            "type": movement_type,
            "quantite": abs(delta),
            "source": f"Ajustement API ({username or 'inconnu'})",
            "tenant_id": int(tenant_id),
        }
        conn.execute(
            text(
                """
                INSERT INTO mouvements_stock (produit_id, type, quantite, source, tenant_id)
                VALUES (:pid, :type, :quantite, :source, :tenant_id)
                """
            ),
            payload,
        )

    # Trigger updates stock_actuel; fetch new value
    with engine.connect() as conn:
        new_row = conn.execute(
            text("SELECT COALESCE(stock_actuel, 0) FROM produits WHERE id = :pid AND tenant_id = :tenant_id"),
            {"pid": product_id, "tenant_id": int(tenant_id)},
        ).fetchone()
        new_stock = float(new_row[0] if new_row else target_quantity)

    return {
        "product_id": product_id,
        "product_name": row.nom,
        "current_stock": current_stock,
        "new_stock": new_stock,
        "movement_created": True,
        "movement_type": movement_type,
        "movement_quantity": abs(delta),
    }


__all__ = ["fetch_movement_timeseries", "fetch_recent_movements", "adjust_stock_level"]
