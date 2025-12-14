"""Service helpers for Restaurant Menus & Costs (Scénario 3.6)."""

from __future__ import annotations

from typing import Any, List

from sqlalchemy import text

from core.data_repository import query_df
from backend.schemas.restaurant import (
    RestaurantMenuOverview,
    RestaurantMenuMetrics,
    RestaurantMenuPlatCost,
    RestaurantMenuTopPlat,
    RestaurantMenuIngredientAlert,
)
from backend.services.restaurant.utils import _safe_float


def get_menu_overview(tenant_id: int) -> RestaurantMenuOverview:
    """
    Aggregated view of menus & costs for a restaurant tenant.
    - Computes food cost & margin per plat from restaurant tables
    - Flags low/rupture ingredients
    """
    # Coûts plats + food cost %
    plat_costs_sql = text("""
        WITH ingredient_costs AS (
            SELECT
                rpi.plat_id,
                SUM(rpi.quantite * COALESCE(ri.cout_unitaire, 0)) AS cout_matiere
            FROM restaurant_plat_ingredients rpi
            JOIN restaurant_ingredients ri ON ri.id = rpi.ingredient_id AND ri.tenant_id = rpi.tenant_id
            WHERE rpi.tenant_id = :tenant_id
            GROUP BY rpi.plat_id
        )
        SELECT
            rp.id AS plat_id,
            rp.nom,
            COALESCE(rp.prix_vente_ttc, 0) AS prix_vente_ttc,
            COALESCE(ic.cout_matiere, 0) AS cout_matiere,
            CASE WHEN COALESCE(rp.prix_vente_ttc, 0) > 0
                 THEN (COALESCE(ic.cout_matiere, 0) / rp.prix_vente_ttc * 100)
                 ELSE 0 END AS food_cost_pct,
            CASE WHEN COALESCE(rp.prix_vente_ttc, 0) > 0
                 THEN ((rp.prix_vente_ttc - COALESCE(ic.cout_matiere, 0)) / rp.prix_vente_ttc * 100)
                 ELSE 0 END AS marge_pct
        FROM restaurant_plats rp
        LEFT JOIN ingredient_costs ic ON ic.plat_id = rp.id
        WHERE rp.tenant_id = :tenant_id AND rp.actif = TRUE
        ORDER BY rp.nom
    """)

    plat_costs_df = query_df(plat_costs_sql, {"tenant_id": tenant_id})
    plat_costs: List[RestaurantMenuPlatCost] = []
    for _, row in plat_costs_df.iterrows():
        plat_costs.append(
            RestaurantMenuPlatCost(
                plat_id=int(row["plat_id"]),
                nom=row["nom"],
                prix_vente_ttc=_safe_float(row["prix_vente_ttc"]),
                cout_matiere=_safe_float(row["cout_matiere"]),
                food_cost_pct=_safe_float(row["food_cost_pct"]),
                marge_pct=_safe_float(row["marge_pct"]),
            )
        )

    # Alertes ingrédients (rupture / stock bas)
    ingredient_alerts_sql = text("""
        SELECT
            ri.id AS ingredient_id,
            ri.nom,
            ri.stock_actuel,
            ri.cout_unitaire,
            CASE
                WHEN ri.stock_actuel <= 0 THEN 'rupture'
                WHEN ri.stock_actuel < 5 THEN 'bas'
                ELSE 'ok'
            END AS status
        FROM restaurant_ingredients ri
        WHERE ri.tenant_id = :tenant_id
        ORDER BY ri.stock_actuel ASC
    """)

    alerts_df = query_df(ingredient_alerts_sql, {"tenant_id": tenant_id})
    ingredient_alerts: List[RestaurantMenuIngredientAlert] = []
    for _, row in alerts_df.iterrows():
        if row["status"] == "ok":
            continue
        ingredient_alerts.append(
            RestaurantMenuIngredientAlert(
                ingredient_id=int(row["ingredient_id"]),
                nom=row["nom"],
                stock_actuel=_safe_float(row["stock_actuel"]),
                cout_unitaire=_safe_float(row["cout_unitaire"]),
                status=row["status"],
            )
        )

    # Top plats par marge
    top_plats_sorted = sorted(plat_costs, key=lambda p: p.marge_pct, reverse=True)[:5]
    top_plats = [
        RestaurantMenuTopPlat(
            plat_id=p.plat_id,
            nom=p.nom,
            marge_pct=p.marge_pct,
            prix_vente_ttc=p.prix_vente_ttc,
            cout_matiere=p.cout_matiere,
        )
        for p in top_plats_sorted
    ]

    avg_food_cost = sum(p.food_cost_pct for p in plat_costs) / len(plat_costs) if plat_costs else 0.0
    metrics = RestaurantMenuMetrics(
        total_plats=len(plat_costs),
        avg_food_cost_pct=round(avg_food_cost, 2),
        alerts_count=len(ingredient_alerts),
        top_plats=top_plats,
    )

    return RestaurantMenuOverview(
        metrics=metrics,
        plat_costs=plat_costs,
        ingredient_alerts=ingredient_alerts,
    )
