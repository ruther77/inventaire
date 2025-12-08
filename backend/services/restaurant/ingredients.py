"""Ingredient and plat management services for restaurant module."""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import text

from core.data_repository import get_engine, query_df
from core import restaurant_costs
from backend.services.restaurant.utils import _safe_float


def list_ingredients(tenant_id: int) -> List[dict[str, Any]]:
    """Return available ingredients for composing dishes."""
    df = query_df(
        text(
            """
            SELECT id, nom, unite_base, cout_unitaire, stock_actuel
            FROM restaurant_ingredients
            WHERE tenant_id = :tenant
            ORDER BY nom
            """
        ),
        {"tenant": tenant_id},
    )
    return df.to_dict("records") if not df.empty else []


def create_ingredient(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Create an ingredient with unit price and initial stock."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_ingredients (tenant_id, nom, unite_base, cout_unitaire, stock_actuel)
                VALUES (:tenant, :nom, :unite_base, :cout_unitaire, :stock_actuel)
                RETURNING id, nom, unite_base, cout_unitaire, stock_actuel
                """
            ),
            {**payload, "tenant": tenant_id},
        ).fetchone()
    return dict(row._mapping)


def update_ingredient_price(tenant_id: int, ingredient_id: int, new_price: float) -> dict[str, Any]:
    """Update ingredient cost and recalculate dish margins."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                UPDATE restaurant_ingredients
                SET cout_unitaire = :price
                WHERE tenant_id = :tenant AND id = :ingredient_id
                RETURNING id, nom, unite_base, cout_unitaire, stock_actuel
                """
            ),
            {"tenant": tenant_id, "ingredient_id": ingredient_id, "price": new_price},
        ).fetchone()
        if not row:
            raise RuntimeError("Ingredient introuvable")
    refresh_plat_costs(tenant_id)
    return dict(row._mapping)


def list_plats(tenant_id: int) -> List[dict[str, Any]]:
    """Load dishes with gross margin and percentage calculated from linked ingredients."""
    plats_df = query_df(
        text(
            """
            WITH couts AS (
                SELECT
                    rpi.plat_id,
                    SUM(rpi.quantite * COALESCE(ri.cout_unitaire, 0)) AS cout_matiere
                FROM restaurant_plat_ingredients rpi
                JOIN restaurant_ingredients ri ON ri.id = rpi.ingredient_id
                WHERE rpi.tenant_id = :tenant
                GROUP BY rpi.plat_id
            )
            SELECT
                p.id,
                p.nom,
                p.categorie,
                p.prix_vente_ttc,
                p.actif,
                COALESCE(c.cout_matiere, 0) AS cout_matiere
            FROM restaurant_plats p
            LEFT JOIN couts c ON c.plat_id = p.id
            WHERE p.tenant_id = :tenant
            ORDER BY p.nom
            """
        ),
        {"tenant": tenant_id},
    )
    if plats_df.empty:
        return []

    plats_df["cout_matiere"] = plats_df["cout_matiere"].fillna(0.0)
    plats_df["marge_brute"] = plats_df["prix_vente_ttc"].fillna(0.0) - plats_df["cout_matiere"]
    plats_df["marge_pct"] = plats_df.apply(
        lambda row: (row["marge_brute"] / row["prix_vente_ttc"] * 100) if row["prix_vente_ttc"] else 0.0,
        axis=1,
    )

    plat_ids = plats_df["id"].tolist()
    ing_df = None
    if plat_ids:
        placeholder_tokens = []
        params: Dict[str, Any] = {"tenant": tenant_id}
        for idx, pid in enumerate(plat_ids):
            token = f"pid_{idx}"
            placeholder_tokens.append(f":{token}")
            params[token] = pid

        sql = text(
            f"""
            SELECT rpi.id,
                   rpi.plat_id,
                   rpi.ingredient_id,
                   ri.nom,
                   rpi.quantite,
                   rpi.unite
            FROM restaurant_plat_ingredients rpi
            JOIN restaurant_ingredients ri ON ri.id = rpi.ingredient_id
            WHERE rpi.tenant_id = :tenant
              AND rpi.plat_id IN ({", ".join(placeholder_tokens)})
            """
        )
        ing_df = query_df(sql, params=params)

    grouped = {}
    if ing_df is not None and not ing_df.empty:
        for row in ing_df.to_dict("records"):
            grouped.setdefault(row["plat_id"], []).append(row)

    results = []
    for plat in plats_df.to_dict("records"):
        plat["ingredients"] = grouped.get(plat["id"], [])
        plat["cout_matiere"] = _safe_float(plat.get("cout_matiere"))
        plat["marge_brute"] = _safe_float(plat.get("marge_brute"))
        plat["marge_pct"] = _safe_float(plat.get("marge_pct"))
        results.append(plat)
    return results


def refresh_plat_costs(tenant_id: int, margin_threshold: float = 35.0) -> dict[str, Any]:
    """Delegate cost/margin recalculation to shared utilities."""
    return restaurant_costs.refresh_plat_costs(tenant_id=tenant_id, margin_threshold=margin_threshold)


def list_plat_alerts(tenant_id: int) -> List[dict[str, Any]]:
    """Return margin alerts generated by the previous recalculation."""
    return restaurant_costs.list_margin_alerts(tenant_id=tenant_id)


def create_plat(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a dish and initialize totals/margins from linked ingredients."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_plats (tenant_id, nom, categorie, prix_vente_ttc, actif)
                VALUES (:tenant, :nom, :categorie, :prix_vente_ttc, :actif)
                RETURNING id, nom, categorie, prix_vente_ttc, actif
                """
            ),
            {**payload, "tenant": tenant_id},
        ).fetchone()
    base = dict(row._mapping)
    price = _safe_float(base.get("prix_vente_ttc"))
    base.update(
        {
            "cout_matiere": 0.0,
            "marge_brute": price,
            "marge_pct": 100.0 if price else 0.0,
            "ingredients": [],
        }
    )
    refresh_plat_costs(tenant_id)
    return base


def attach_ingredient_to_plat(tenant_id: int, plat_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Associate an ingredient with a dish with cost recalculation."""
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO restaurant_plat_ingredients (tenant_id, plat_id, ingredient_id, quantite, unite)
                VALUES (:tenant, :plat_id, :ingredient_id, :quantite, :unite)
                ON CONFLICT (plat_id, ingredient_id)
                DO UPDATE SET quantite = EXCLUDED.quantite, unite = EXCLUDED.unite
                """
            ),
            {"tenant": tenant_id, "plat_id": plat_id, **payload},
        )
    refresh_plat_costs(tenant_id)
    return {"status": "ok"}


def update_plat_price(tenant_id: int, plat_id: int, new_price: float) -> dict[str, Any]:
    """Update dish TTC price and recalculate linked margins."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                UPDATE restaurant_plats
                SET prix_vente_ttc = :price
                WHERE tenant_id = :tenant AND id = :plat_id
                RETURNING id, nom, categorie, prix_vente_ttc, actif
                """
            ),
            {"tenant": tenant_id, "plat_id": plat_id, "price": new_price},
        ).fetchone()
        if not row:
            raise RuntimeError("Plat introuvable")
    refresh_plat_costs(tenant_id)
    plats = list_plats(tenant_id)
    updated = next((plat for plat in plats if plat["id"] == plat_id), None)
    return updated or dict(row._mapping)


def list_ingredient_price_history(tenant_id: int, ingredient_id: int) -> List[dict[str, Any]]:
    """Show price history for a given ingredient."""
    df = query_df(
        text(
            """
            SELECT h.id, h.ingredient_id, ri.nom AS ingredient_nom, h.cout_unitaire, h.changed_at
            FROM restaurant_ingredient_price_history h
            JOIN restaurant_ingredients ri ON ri.id = h.ingredient_id
            WHERE h.tenant_id = :tenant AND h.ingredient_id = :ingredient
            ORDER BY h.changed_at DESC
            """
        ),
        {"tenant": tenant_id, "ingredient": ingredient_id},
    )
    return df.to_dict("records") if not df.empty else []


def list_plat_price_history(tenant_id: int, plat_id: int) -> List[dict[str, Any]]:
    """Show price history for a given dish."""
    df = query_df(
        text(
            """
            SELECT h.id, h.plat_id, p.nom AS plat_nom, h.prix_vente_ttc, h.changed_at
            FROM restaurant_plat_price_history h
            JOIN restaurant_plats p ON p.id = h.plat_id
            WHERE h.tenant_id = :tenant AND h.plat_id = :plat
            ORDER BY h.changed_at DESC
            """
        ),
        {"tenant": tenant_id, "plat": plat_id},
    )
    return df.to_dict("records") if not df.empty else []


def list_recent_price_changes(tenant_id: int, limit: int = 12) -> dict[str, list[dict[str, Any]]]:
    """Return latest price modifications for ingredients and dishes."""
    safe_limit = max(1, min(limit, 200))
    ingredient_sql = text(
        f"""
        SELECT h.id, h.ingredient_id, ri.nom AS ingredient_nom, h.cout_unitaire, h.changed_at
        FROM restaurant_ingredient_price_history h
        JOIN restaurant_ingredients ri ON ri.id = h.ingredient_id
        WHERE h.tenant_id = :tenant
        ORDER BY h.changed_at DESC
        LIMIT {safe_limit}
        """
    )
    plat_sql = text(
        f"""
        SELECT h.id, h.plat_id, p.nom AS plat_nom, h.prix_vente_ttc, h.changed_at
        FROM restaurant_plat_price_history h
        JOIN restaurant_plats p ON p.id = h.plat_id
        WHERE h.tenant_id = :tenant
        ORDER BY h.changed_at DESC
        LIMIT {safe_limit}
        """
    )
    ingredient_df = query_df(ingredient_sql, {"tenant": tenant_id})
    plat_df = query_df(plat_sql, {"tenant": tenant_id})
    return {
        "ingredients": ingredient_df.to_dict("records") if not ingredient_df.empty else [],
        "plats": plat_df.to_dict("records") if not plat_df.empty else [],
    }
