"""NewCMS Restaurant and Mobile API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text

from backend.dependencies.tenant import Tenant, get_current_tenant
from core.data_repository import get_engine, query_df
from newCMS.backend.schemas.restaurant import (
    RestaurantOverviewResponse,
    RestaurantOverviewMetrics,
    RestaurantPlatCost,
    RestaurantStockLocation,
    RestaurantIngredientAlert,
    RestaurantTopPlat,
    MobileInventoryListResponse,
    MobileInventoryItem,
    MobileScanRequest,
    MobileScanResponse,
    MobileAdjustRequest,
    MobileAdjustResponse,
)

router = APIRouter(prefix="/newcms", tags=["newcms-restaurant"])


# ============================================================================
# RESTAURANT OVERVIEW
# ============================================================================

@router.get("/restaurant/overview", response_model=RestaurantOverviewResponse)
def get_restaurant_overview(tenant: Tenant = Depends(get_current_tenant)):
    """
    Aggregate restaurant overview: plat costs, alerts, stock by location, top plats by margin.

    Returns:
    - Plat costs with food cost %
    - Ingredient stock alerts (rupture, alerte)
    - Stock aggregated by location (bar, cuisine, cave)
    - Top 5 plats by margin %
    """
    # 1. Plat costs with food cost %
    plat_costs_sql = text("""
        WITH ingredient_costs AS (
            SELECT
                pi.plat_id,
                SUM(pi.quantite_batch * COALESCE(i.cout_unitaire, 0)) AS cout_matiere
            FROM plat_ingredients pi
            JOIN ingredients i ON i.id = pi.ingredient_id
            WHERE pi.tenant_id = :tenant_id
            GROUP BY pi.plat_id
        )
        SELECT
            p.id AS plat_id,
            p.nom,
            p.prix_vente_ttc,
            COALESCE(ic.cout_matiere, 0) AS cout_matiere,
            CASE
                WHEN p.prix_vente_ttc > 0 THEN
                    ROUND((COALESCE(ic.cout_matiere, 0) / p.prix_vente_ttc * 100)::numeric, 2)
                ELSE 0
            END AS food_cost_pct,
            CASE
                WHEN p.prix_vente_ttc > 0 THEN
                    ROUND(((p.prix_vente_ttc - COALESCE(ic.cout_matiere, 0)) / p.prix_vente_ttc * 100)::numeric, 2)
                ELSE 0
            END AS marge_pct
        FROM plats p
        LEFT JOIN ingredient_costs ic ON ic.plat_id = p.id
        WHERE p.tenant_id = :tenant_id AND p.actif = true
        ORDER BY p.nom
    """)

    plat_costs_df = query_df(plat_costs_sql, {"tenant_id": tenant.id})
    plat_costs = [
        RestaurantPlatCost(
            plat_id=int(row["plat_id"]),
            nom=row["nom"],
            food_cost_pct=float(row["food_cost_pct"]),
            marge_pct=float(row["marge_pct"]),
            prix_vente_ttc=float(row["prix_vente_ttc"]),
            cout_matiere=float(row["cout_matiere"]),
        )
        for row in plat_costs_df.to_dict("records")
    ] if not plat_costs_df.empty else []

    # 2. Ingredient stock alerts (low stock or out of stock)
    alert_sql = text("""
        SELECT
            i.id AS ingredient_id,
            i.nom,
            COALESCE(i.stock_actuel, 0) AS stock_actuel,
            COALESCE(i.seuil_alerte, 5) AS seuil_alerte,
            CASE
                WHEN COALESCE(i.stock_actuel, 0) <= 0 THEN 'rupture'
                WHEN COALESCE(i.stock_actuel, 0) < COALESCE(i.seuil_alerte, 5) THEN 'alerte'
                ELSE 'ok'
            END AS status
        FROM ingredients i
        WHERE i.tenant_id = :tenant_id
          AND COALESCE(i.stock_actuel, 0) < COALESCE(i.seuil_alerte, 5)
        ORDER BY stock_actuel ASC, i.nom
        LIMIT 20
    """)

    alerts_df = query_df(alert_sql, {"tenant_id": tenant.id})
    ingredient_alerts = [
        RestaurantIngredientAlert(
            ingredient_id=int(row["ingredient_id"]),
            nom=row["nom"],
            stock_actuel=float(row["stock_actuel"]),
            seuil_alerte=float(row["seuil_alerte"]),
            status=row["status"],
        )
        for row in alerts_df.to_dict("records")
    ] if not alerts_df.empty else []

    # 3. Stock by location (stub - extend with real location logic later)
    # For now, we just show total stock by type (ingredients vs produits)
    stock_locations = [
        RestaurantStockLocation(location="cuisine", count=len(plat_costs), valeur=sum(p.cout_matiere for p in plat_costs)),
        RestaurantStockLocation(location="bar", count=0, valeur=0.0),
        RestaurantStockLocation(location="cave", count=0, valeur=0.0),
    ]

    # 4. Top 5 plats by margin %
    top_plats = sorted(plat_costs, key=lambda x: x.marge_pct, reverse=True)[:5]
    top_plats_list = [
        RestaurantTopPlat(
            plat_id=p.plat_id,
            nom=p.nom,
            marge_pct=p.marge_pct,
            prix_vente_ttc=p.prix_vente_ttc,
            cout_matiere=p.cout_matiere,
        )
        for p in top_plats
    ]

    # Metrics
    avg_food_cost = sum(p.food_cost_pct for p in plat_costs) / len(plat_costs) if plat_costs else 0.0

    metrics = RestaurantOverviewMetrics(
        total_plats=len(plat_costs),
        avg_food_cost_pct=round(avg_food_cost, 2),
        alerts_count=len(ingredient_alerts),
        top_plats=top_plats_list,
    )

    return RestaurantOverviewResponse(
        metrics=metrics,
        plat_costs=plat_costs,
        stock_locations=stock_locations,
        ingredient_alerts=ingredient_alerts,
    )


# ============================================================================
# MOBILE ENDPOINTS
# ============================================================================

@router.get("/mobile/inventory", response_model=MobileInventoryListResponse)
def get_mobile_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Lightweight paginated inventory list for mobile scanning.

    Returns scannable items (code_barre, nom, stock_actuel, seuil_alerte).
    Optimized for fast mobile response.
    """
    offset = (page - 1) * page_size

    # Search in ingredients (restaurant stock)
    search_clause = ""
    params = {"tenant_id": tenant.id, "limit": page_size, "offset": offset}

    if search:
        search_clause = "AND (i.nom ILIKE :search OR i.code_barre ILIKE :search)"
        params["search"] = f"%{search}%"

    inventory_sql = text(f"""
        SELECT
            i.id,
            i.nom,
            i.code_barre,
            COALESCE(i.stock_actuel, 0) AS stock_actuel,
            COALESCE(i.seuil_alerte, 5) AS seuil_alerte,
            'ingredient' AS categorie
        FROM ingredients i
        WHERE i.tenant_id = :tenant_id
          {search_clause}
        ORDER BY i.nom
        LIMIT :limit OFFSET :offset
    """)

    count_sql = text(f"""
        SELECT COUNT(*) AS total
        FROM ingredients i
        WHERE i.tenant_id = :tenant_id
          {search_clause}
    """)

    items_df = query_df(inventory_sql, params)
    count_row = query_df(count_sql, params)
    total = int(count_row["total"].iloc[0]) if not count_row.empty else 0

    items = [
        MobileInventoryItem(
            id=int(row["id"]),
            nom=row["nom"],
            code_barre=row.get("code_barre"),
            stock_actuel=float(row["stock_actuel"]),
            seuil_alerte=float(row["seuil_alerte"]),
            categorie=row.get("categorie"),
        )
        for row in items_df.to_dict("records")
    ] if not items_df.empty else []

    return MobileInventoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/mobile/scan", response_model=MobileScanResponse)
def scan_barcode(
    payload: MobileScanRequest,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Barcode scan lookup.

    Returns product details + stock if found, enables quick adjustment.
    Fast response optimized for mobile.
    """
    scan_sql = text("""
        SELECT
            i.id,
            i.nom,
            i.code_barre,
            COALESCE(i.stock_actuel, 0) AS stock_actuel,
            COALESCE(i.seuil_alerte, 5) AS seuil_alerte,
            'ingredient' AS categorie
        FROM ingredients i
        WHERE i.tenant_id = :tenant_id
          AND i.code_barre = :code_barre
        LIMIT 1
    """)

    result_df = query_df(scan_sql, {"tenant_id": tenant.id, "code_barre": payload.code_barre})

    if result_df.empty:
        return MobileScanResponse(
            found=False,
            product=None,
            message=f"Aucun produit trouvé pour le code-barres: {payload.code_barre}",
        )

    row = result_df.iloc[0]
    product = MobileInventoryItem(
        id=int(row["id"]),
        nom=row["nom"],
        code_barre=row.get("code_barre"),
        stock_actuel=float(row["stock_actuel"]),
        seuil_alerte=float(row["seuil_alerte"]),
        categorie=row.get("categorie"),
    )

    return MobileScanResponse(
        found=True,
        product=product,
        message=None,
    )


@router.post("/mobile/adjust", response_model=MobileAdjustResponse)
def adjust_stock(
    payload: MobileAdjustRequest,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Adjust stock from mobile (+1/-1 or absolute value).

    Supports adjustment reasons: breakage, theft, error, expiry, other.
    Creates movement record for audit trail.
    """
    if payload.reason not in ["breakage", "theft", "error", "expiry", "other"]:
        raise HTTPException(status_code=400, detail="Invalid adjustment reason")

    with get_engine().begin() as conn:
        # Get current stock
        current_row = conn.execute(
            text("""
                SELECT i.nom, COALESCE(i.stock_actuel, 0) AS stock_actuel
                FROM ingredients i
                WHERE i.id = :product_id AND i.tenant_id = :tenant_id
                FOR UPDATE
            """),
            {"product_id": payload.product_id, "tenant_id": tenant.id},
        ).fetchone()

        if not current_row:
            raise HTTPException(status_code=404, detail="Product not found")

        old_stock = float(current_row.stock_actuel)
        product_name = current_row.nom

        # Calculate new stock
        if payload.adjustment_type == "absolute":
            new_stock = max(0.0, float(payload.adjustment))
            actual_adjustment = new_stock - old_stock
        else:  # delta
            new_stock = max(0.0, old_stock + float(payload.adjustment))
            actual_adjustment = float(payload.adjustment)

        # Update stock
        conn.execute(
            text("""
                UPDATE ingredients
                SET stock_actuel = :new_stock
                WHERE id = :product_id AND tenant_id = :tenant_id
            """),
            {"new_stock": new_stock, "product_id": payload.product_id, "tenant_id": tenant.id},
        )

        # Create movement record
        movement_type = "ajustement_mobile_in" if actual_adjustment > 0 else "ajustement_mobile_out"
        conn.execute(
            text("""
                INSERT INTO mouvements_stock (
                    tenant_id,
                    produit_id,
                    type,
                    quantite,
                    date_mvt,
                    source
                )
                VALUES (
                    :tenant_id,
                    :product_id,
                    :type,
                    :quantite,
                    NOW(),
                    :source
                )
            """),
            {
                "tenant_id": tenant.id,
                "product_id": payload.product_id,
                "type": movement_type,
                "quantite": abs(actual_adjustment),
                "source": f"mobile_adjust:{payload.reason}:{payload.notes or ''}",
            },
        )

    return MobileAdjustResponse(
        product_id=payload.product_id,
        product_name=product_name,
        old_stock=round(old_stock, 2),
        new_stock=round(new_stock, 2),
        adjustment=round(actual_adjustment, 2),
        reason=payload.reason,
        timestamp=datetime.utcnow(),
    )


__all__ = ["router"]
