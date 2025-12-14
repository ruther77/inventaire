"""Service functions for Restaurant Overview & Food Cost (UX 4.7)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

from sqlalchemy import text

from core.data_repository import get_engine, query_df
from backend.services.restaurant.utils import _safe_float


def _get_period_days(period: str) -> int:
    """Convert period string to number of days."""
    mapping = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    return mapping.get(period, 30)


def get_restaurant_overview(tenant_id: int, period: str = "30d") -> dict[str, Any]:
    """
    Get restaurant overview with metrics, top plats, and alerts.

    Returns:
    - Revenue for period
    - Global food cost %
    - Active plats count
    - Top 5 plats by sales
    - Alerts (low margins, stock issues)
    """
    days = _get_period_days(period)
    start_date = datetime.now() - timedelta(days=days)

    # Get metrics
    metrics_sql = text("""
        SELECT
            COUNT(DISTINCT CASE WHEN p.actif THEN p.id END) as active_plats_count,
            COUNT(p.id) as total_plats_count,
            AVG(CASE WHEN p.prix_vente_ttc > 0
                THEN ((p.prix_vente_ttc - COALESCE(pc.cout_matiere, 0)) / p.prix_vente_ttc * 100)
                ELSE 0 END) as avg_margin_pct
        FROM restaurant_plats p
        LEFT JOIN restaurant_plat_costs pc ON pc.plat_id = p.id AND pc.tenant_id = p.tenant_id
        WHERE p.tenant_id = :tenant_id
    """)

    metrics_df = query_df(metrics_sql, {"tenant_id": tenant_id})

    if metrics_df.empty:
        metrics = {
            "revenue": 0.0,
            "food_cost_pct": 0.0,
            "active_plats_count": 0,
            "total_plats_count": 0,
            "avg_margin_pct": 0.0,
        }
    else:
        row = metrics_df.iloc[0]
        # Mock revenue for now (would come from sales data)
        revenue = 15000.0 + (days * 50)  # Mock data
        food_cost_pct = 100.0 - _safe_float(row.get("avg_margin_pct", 0))

        metrics = {
            "revenue": revenue,
            "food_cost_pct": food_cost_pct,
            "active_plats_count": int(row.get("active_plats_count", 0)),
            "total_plats_count": int(row.get("total_plats_count", 0)),
            "avg_margin_pct": _safe_float(row.get("avg_margin_pct", 0)),
        }

    # Get top plats (mock data for sales)
    top_plats_sql = text("""
        SELECT
            p.id as plat_id,
            p.nom,
            COALESCE(pc.marge_pct, 0) as margin_pct
        FROM restaurant_plats p
        LEFT JOIN restaurant_plat_costs pc ON pc.plat_id = p.id AND pc.tenant_id = p.tenant_id
        WHERE p.tenant_id = :tenant_id AND p.actif = TRUE
        ORDER BY p.prix_vente_ttc DESC
        LIMIT 5
    """)

    top_plats_df = query_df(top_plats_sql, {"tenant_id": tenant_id})
    top_plats = []
    for idx, row in top_plats_df.iterrows():
        # Mock sales data
        sales_count = 50 - (idx * 10)
        revenue = sales_count * 12.5
        top_plats.append({
            "plat_id": int(row["plat_id"]),
            "nom": row["nom"],
            "sales_count": sales_count,
            "revenue": revenue,
            "margin_pct": _safe_float(row["margin_pct"]),
        })

    # Get alerts
    alerts_sql = text("""
        SELECT
            alert_type,
            severity,
            COUNT(*) as count,
            MIN(message) as message
        FROM restaurant_alerts
        WHERE tenant_id = :tenant_id
        GROUP BY alert_type, severity
        ORDER BY
            CASE severity
                WHEN 'critical' THEN 1
                WHEN 'warning' THEN 2
                ELSE 3
            END,
            count DESC
    """)

    alerts_df = query_df(alerts_sql, {"tenant_id": tenant_id})
    alerts = []
    for _, row in alerts_df.iterrows():
        alerts.append({
            "alert_type": row["alert_type"],
            "severity": row["severity"],
            "message": row["message"],
            "count": int(row["count"]),
        })

    return {
        "period": period,
        "metrics": metrics,
        "top_plats": top_plats,
        "alerts": alerts,
        "generated_at": datetime.now(),
    }


def list_plats_paginated(
    tenant_id: int,
    page: int = 1,
    page_size: int = 50,
    categorie: Optional[str] = None,
    actif: Optional[bool] = None,
    min_margin_pct: Optional[float] = None,
    sort_by: str = "nom",
    sort_desc: bool = False,
) -> dict[str, Any]:
    """
    List plats with pagination, filters, and sorting.
    """
    # Build WHERE clause
    where_clauses = ["p.tenant_id = :tenant_id"]
    params: dict[str, Any] = {"tenant_id": tenant_id}

    if categorie:
        where_clauses.append("p.categorie = :categorie")
        params["categorie"] = categorie

    if actif is not None:
        where_clauses.append("p.actif = :actif")
        params["actif"] = actif

    if min_margin_pct is not None:
        where_clauses.append("COALESCE(pc.marge_pct, 0) >= :min_margin_pct")
        params["min_margin_pct"] = min_margin_pct

    where_sql = " AND ".join(where_clauses)

    # Build ORDER BY clause
    sort_columns = {
        "nom": "p.nom",
        "margin_pct": "COALESCE(pc.marge_pct, 0)",
        "prix_vente_ttc": "p.prix_vente_ttc",
        "sales_count": "p.id",  # Mock - would be from sales table
    }
    order_column = sort_columns.get(sort_by, "p.nom")
    order_direction = "DESC" if sort_desc else "ASC"

    # Count total
    count_sql = text(f"""
        SELECT COUNT(*) as total
        FROM restaurant_plats p
        LEFT JOIN restaurant_plat_costs pc ON pc.plat_id = p.id AND pc.tenant_id = p.tenant_id
        WHERE {where_sql}
    """)

    count_df = query_df(count_sql, params)
    total = int(count_df.iloc[0]["total"]) if not count_df.empty else 0

    # Get paginated items
    offset = (page - 1) * page_size
    params["limit"] = page_size
    params["offset"] = offset

    items_sql = text(f"""
        SELECT
            p.id,
            p.nom,
            p.categorie as categorie,
            p.prix_vente_ttc,
            p.actif,
            COALESCE(pc.cout_matiere, 0) as cout_matiere,
            COALESCE(pc.marge_brute, 0) as marge_brute,
            COALESCE(pc.marge_pct, 0) as marge_pct
        FROM restaurant_plats p
        LEFT JOIN restaurant_plat_costs pc ON pc.plat_id = p.id AND pc.tenant_id = p.tenant_id
        WHERE {where_sql}
        ORDER BY {order_column} {order_direction}
        LIMIT :limit OFFSET :offset
    """)

    items_df = query_df(items_sql, params)
    items = []
    for _, row in items_df.iterrows():
        cost = _safe_float(row["cout_matiere"])
        price = _safe_float(row["prix_vente_ttc"])
        food_cost_pct = (cost / price * 100) if price > 0 else 0.0

        items.append({
            "id": int(row["id"]),
            "nom": row["nom"],
            "categorie": row["categorie"],
            "prix_vente_ttc": price,
            "cout_matiere": cost,
            "marge_brute": _safe_float(row["marge_brute"]),
            "marge_pct": _safe_float(row["marge_pct"]),
            "food_cost_pct": food_cost_pct,
            "actif": bool(row["actif"]),
            "sales_count": None,  # Mock - would come from sales data
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_plat_detail(tenant_id: int, plat_id: int) -> dict[str, Any]:
    """
    Get complete plat details with ingredients and price history.
    """
    # Get plat base info
    plat_sql = text("""
        SELECT
            p.id,
            p.nom,
            p.categorie as categorie,
            p.prix_vente_ttc,
            p.actif,
            COALESCE(pc.cout_matiere, 0) as cout_matiere,
            COALESCE(pc.marge_brute, 0) as marge_brute,
            COALESCE(pc.marge_pct, 0) as marge_pct
        FROM restaurant_plats p
        LEFT JOIN restaurant_plat_costs pc ON pc.plat_id = p.id AND pc.tenant_id = p.tenant_id
        WHERE p.tenant_id = :tenant_id AND p.id = :plat_id
    """)

    plat_df = query_df(plat_sql, {"tenant_id": tenant_id, "plat_id": plat_id})
    if plat_df.empty:
        raise ValueError(f"Plat {plat_id} not found")

    plat = plat_df.iloc[0]
    cost = _safe_float(plat["cout_matiere"])
    price = _safe_float(plat["prix_vente_ttc"])
    food_cost_pct = (cost / price * 100) if price > 0 else 0.0

    # Get ingredients
    ing_sql = text("""
        SELECT
            pi.ingredient_id,
            i.nom,
            pi.quantite as quantite,
            i.unite_base as unite,
            i.cout_unitaire as unit_price
        FROM restaurant_plat_ingredients pi
        JOIN restaurant_ingredients i ON i.id = pi.ingredient_id AND i.tenant_id = pi.tenant_id
        WHERE pi.tenant_id = :tenant_id AND pi.plat_id = :plat_id
        ORDER BY i.nom
    """)

    ing_df = query_df(ing_sql, {"tenant_id": tenant_id, "plat_id": plat_id})
    ingredients = []
    for _, row in ing_df.iterrows():
        unit_price = _safe_float(row["unit_price"])
        quantite = _safe_float(row["quantite"])
        total_cost = unit_price * quantite
        cost_percentage = (total_cost / cost * 100) if cost > 0 else 0.0

        ingredients.append({
            "ingredient_id": int(row["ingredient_id"]),
            "nom": row["nom"],
            "quantite": quantite,
            "unite": row["unite"],
            "unit_price": unit_price,
            "total_cost": total_cost,
            "cost_percentage": cost_percentage,
        })

    # Get price history (last 10 changes)
    history_sql = text("""
        SELECT id, plat_id, prix_vente_ttc, changed_at
        FROM restaurant_plat_price_history
        WHERE tenant_id = :tenant_id AND plat_id = :plat_id
        ORDER BY changed_at DESC
        LIMIT 10
    """)

    history_df = query_df(history_sql, {"tenant_id": tenant_id, "plat_id": plat_id})
    price_history = []
    for _, row in history_df.iterrows():
        price_history.append({
            "id": int(row["id"]),
            "plat_id": int(row["plat_id"]),
            "plat_nom": plat["nom"],
            "prix_vente_ttc": _safe_float(row["prix_vente_ttc"]),
            "changed_at": row["changed_at"],
        })

    return {
        "id": int(plat["id"]),
        "nom": plat["nom"],
        "categorie": plat["categorie"],
        "selling_price": price,
        "cost": cost,
        "margin": _safe_float(plat["marge_brute"]),
        "margin_pct": _safe_float(plat["marge_pct"]),
        "food_cost_pct": food_cost_pct,
        "is_active": bool(plat["actif"]),
        "ingredients": ingredients,
        "price_history": price_history,
    }


def get_plat_cost_breakdown(tenant_id: int, plat_id: int) -> dict[str, Any]:
    """
    Get cost breakdown by ingredient with price trends.
    """
    # Get plat name and total cost
    plat_sql = text("""
        SELECT p.nom, COALESCE(pc.cout_matiere, 0) as total_cost
        FROM restaurant_plats p
        LEFT JOIN restaurant_plat_costs pc ON pc.plat_id = p.id AND pc.tenant_id = p.tenant_id
        WHERE p.tenant_id = :tenant_id AND p.id = :plat_id
    """)

    plat_df = query_df(plat_sql, {"tenant_id": tenant_id, "plat_id": plat_id})
    if plat_df.empty:
        raise ValueError(f"Plat {plat_id} not found")

    plat_nom = plat_df.iloc[0]["nom"]
    total_cost = _safe_float(plat_df.iloc[0]["total_cost"])

    # Get ingredients with costs
    ing_sql = text("""
        SELECT
            pi.ingredient_id,
            i.nom,
            pi.quantite * i.cout_unitaire as cost
        FROM restaurant_plat_ingredients pi
        JOIN restaurant_ingredients i ON i.id = pi.ingredient_id AND i.tenant_id = pi.tenant_id
        WHERE pi.tenant_id = :tenant_id AND pi.plat_id = :plat_id
        ORDER BY cost DESC
    """)

    ing_df = query_df(ing_sql, {"tenant_id": tenant_id, "plat_id": plat_id})

    items = []
    for _, row in ing_df.iterrows():
        cost = _safe_float(row["cost"])
        cost_percentage = (cost / total_cost * 100) if total_cost > 0 else 0.0

        # Mock price trend (would come from price history)
        price_trend_30d = None  # Could calculate from history

        items.append({
            "ingredient_id": int(row["ingredient_id"]),
            "nom": row["nom"],
            "cost": cost,
            "cost_percentage": cost_percentage,
            "price_trend_30d": price_trend_30d,
        })

    return {
        "plat_id": plat_id,
        "plat_nom": plat_nom,
        "total_cost": total_cost,
        "items": items,
    }


def list_ingredients_enhanced(tenant_id: int) -> list[dict[str, Any]]:
    """
    List ingredients with supplier and price trend information.
    """
    sql = text("""
        SELECT
            i.id,
            i.nom,
            i.unite_base,
            i.cout_unitaire,
            i.stock_actuel
        FROM restaurant_ingredients i
        WHERE i.tenant_id = :tenant_id
        ORDER BY i.nom
    """)

    df = query_df(sql, {"tenant_id": tenant_id})

    ingredients = []
    for _, row in df.iterrows():
        ingredients.append({
            "id": int(row["id"]),
            "nom": row["nom"],
            "unite_base": row["unite_base"],
            "cout_unitaire": _safe_float(row["cout_unitaire"]),
            "stock_actuel": _safe_float(row["stock_actuel"]),
            "main_supplier": None,  # Would come from supplier mapping
            "price_trend_30d": None,  # Would calculate from price history
        })

    return ingredients


def get_ingredient_price_history_detail(tenant_id: int, ingredient_id: int) -> dict[str, Any]:
    """
    Get detailed price history for an ingredient.
    """
    # Get ingredient name
    ing_sql = text("""
        SELECT nom FROM restaurant_ingredients
        WHERE tenant_id = :tenant_id AND id = :ingredient_id
    """)

    ing_df = query_df(ing_sql, {"tenant_id": tenant_id, "ingredient_id": ingredient_id})
    if ing_df.empty:
        raise ValueError(f"Ingredient {ingredient_id} not found")

    ingredient_nom = ing_df.iloc[0]["nom"]

    # Get history
    history_sql = text("""
        SELECT id, ingredient_id, cout_unitaire, changed_at
        FROM restaurant_ingredient_price_history
        WHERE tenant_id = :tenant_id AND ingredient_id = :ingredient_id
        ORDER BY changed_at DESC
        LIMIT 50
    """)

    history_df = query_df(history_sql, {"tenant_id": tenant_id, "ingredient_id": ingredient_id})

    history = []
    for _, row in history_df.iterrows():
        history.append({
            "id": int(row["id"]),
            "ingredient_id": int(row["ingredient_id"]),
            "ingredient_nom": ingredient_nom,
            "cout_unitaire": _safe_float(row["cout_unitaire"]),
            "changed_at": row["changed_at"],
        })

    return {
        "ingredient_id": ingredient_id,
        "ingredient_nom": ingredient_nom,
        "history": history,
    }


def analyze_food_cost(
    tenant_id: int,
    period: str = "30d",
    target_food_cost: float = 30.0,
) -> dict[str, Any]:
    """
    Analyze food cost with trends and recommendations.
    """
    days = _get_period_days(period)

    # Get global food cost
    global_sql = text("""
        SELECT
            AVG(CASE WHEN p.prix_vente_ttc > 0
                THEN (COALESCE(pc.cout_matiere, 0) / p.prix_vente_ttc * 100)
                ELSE 0 END) as global_food_cost_pct
        FROM restaurant_plats p
        LEFT JOIN restaurant_plat_costs pc ON pc.plat_id = p.id AND pc.tenant_id = p.tenant_id
        WHERE p.tenant_id = :tenant_id AND p.actif = TRUE
    """)

    global_df = query_df(global_sql, {"tenant_id": tenant_id})
    global_food_cost_pct = _safe_float(global_df.iloc[0]["global_food_cost_pct"]) if not global_df.empty else 0.0

    # Food cost by category
    category_sql = text("""
        SELECT
            p.categorie as categorie,
            AVG(CASE WHEN p.prix_vente_ttc > 0
                THEN (COALESCE(pc.cout_matiere, 0) / p.prix_vente_ttc * 100)
                ELSE 0 END) as avg_food_cost_pct,
            COUNT(*) as plat_count
        FROM restaurant_plats p
        LEFT JOIN restaurant_plat_costs pc ON pc.plat_id = p.id AND pc.tenant_id = p.tenant_id
        WHERE p.tenant_id = :tenant_id AND p.actif = TRUE
        GROUP BY p.categorie
        ORDER BY avg_food_cost_pct DESC
    """)

    category_df = query_df(category_sql, {"tenant_id": tenant_id})
    by_category = []
    for _, row in category_df.iterrows():
        by_category.append({
            "categorie": row["categorie"] or "Non catégorisé",
            "avg_food_cost_pct": _safe_float(row["avg_food_cost_pct"]),
            "plat_count": int(row["plat_count"]),
            "total_revenue": 0.0,  # Mock - would come from sales
        })

    # Mock trend data
    trend = []
    for i in range(6):
        trend.append({
            "period": f"M-{5-i}",
            "food_cost_pct": global_food_cost_pct + (i - 3) * 0.5,  # Mock variation
            "revenue": 0.0,  # Mock
        })

    # Generate recommendations
    recommendations = []
    if global_food_cost_pct > target_food_cost:
        diff = global_food_cost_pct - target_food_cost
        recommendations.append({
            "priority": "high",
            "category": "cost",
            "message": f"Food cost {diff:.1f}% au-dessus de la cible. Revoyez les prix d'achat ou augmentez les prix de vente.",
            "estimated_impact": None,
        })

    # Check for high food cost categories
    for cat in by_category:
        if cat["avg_food_cost_pct"] > target_food_cost + 5:
            recommendations.append({
                "priority": "medium",
                "category": "pricing",
                "message": f"Catégorie '{cat['categorie']}': food cost élevé à {cat['avg_food_cost_pct']:.1f}%",
                "estimated_impact": None,
            })

    return {
        "period": period,
        "global_food_cost_pct": global_food_cost_pct,
        "target_food_cost_pct": target_food_cost,
        "by_category": by_category,
        "trend": trend,
        "recommendations": recommendations,
    }


def simulate_price_change(
    tenant_id: int,
    plat_id: int,
    new_price: Optional[float] = None,
    target_margin_pct: Optional[float] = None,
) -> dict[str, Any]:
    """
    Simulate impact of price change on margins and food cost.
    """
    # Get current plat data
    plat_sql = text("""
        SELECT
            p.nom,
            p.prix_vente_ttc,
            COALESCE(pc.cout_matiere, 0) as cout_matiere,
            COALESCE(pc.marge_brute, 0) as marge_brute,
            COALESCE(pc.marge_pct, 0) as marge_pct
        FROM restaurant_plats p
        LEFT JOIN restaurant_plat_costs pc ON pc.plat_id = p.id AND pc.tenant_id = p.tenant_id
        WHERE p.tenant_id = :tenant_id AND p.id = :plat_id
    """)

    plat_df = query_df(plat_sql, {"tenant_id": tenant_id, "plat_id": plat_id})
    if plat_df.empty:
        raise ValueError(f"Plat {plat_id} not found")

    plat = plat_df.iloc[0]
    current_price = _safe_float(plat["prix_vente_ttc"])
    cost = _safe_float(plat["cout_matiere"])
    current_margin = _safe_float(plat["marge_brute"])
    current_margin_pct = _safe_float(plat["marge_pct"])
    current_food_cost_pct = (cost / current_price * 100) if current_price > 0 else 0.0

    # Calculate simulated price
    if new_price is not None:
        simulated_price = new_price
    elif target_margin_pct is not None:
        # Price = Cost / (1 - target_margin_pct/100)
        simulated_price = cost / (1 - target_margin_pct / 100) if target_margin_pct < 100 else current_price
    else:
        raise ValueError("Either new_price or target_margin_pct must be provided")

    # Calculate simulated metrics
    simulated_margin = simulated_price - cost
    simulated_margin_pct = (simulated_margin / simulated_price * 100) if simulated_price > 0 else 0.0
    simulated_food_cost_pct = (cost / simulated_price * 100) if simulated_price > 0 else 0.0

    # Calculate impact
    margin_change = simulated_margin - current_margin
    margin_pct_change = simulated_margin_pct - current_margin_pct
    food_cost_change = simulated_food_cost_pct - current_food_cost_pct

    # Estimate annual impact (assume 50 sales per month)
    annual_sales = 50 * 12
    annual_impact = margin_change * annual_sales

    return {
        "plat_id": plat_id,
        "plat_nom": plat["nom"],
        "current": {
            "selling_price": current_price,
            "cost": cost,
            "margin": current_margin,
            "margin_pct": current_margin_pct,
            "food_cost_pct": current_food_cost_pct,
        },
        "simulated": {
            "selling_price": simulated_price,
            "cost": cost,
            "margin": simulated_margin,
            "margin_pct": simulated_margin_pct,
            "food_cost_pct": simulated_food_cost_pct,
        },
        "impact": {
            "margin_change": margin_change,
            "margin_pct_change": margin_pct_change,
            "food_cost_change": food_cost_change,
            "annual_impact": annual_impact,
        },
    }


def list_alerts_detailed(
    tenant_id: int,
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    List detailed restaurant alerts with filters.
    """
    where_clauses = ["a.tenant_id = :tenant_id"]
    params: dict[str, Any] = {"tenant_id": tenant_id}

    if alert_type:
        where_clauses.append("a.alert_type = :alert_type")
        params["alert_type"] = alert_type

    if severity:
        where_clauses.append("a.severity = :severity")
        params["severity"] = severity

    where_sql = " AND ".join(where_clauses)

    sql = text(f"""
        SELECT
            a.id,
            a.alert_type,
            a.severity,
            a.message,
            a.plat_id,
            p.nom as plat_nom,
            a.current_value,
            a.threshold,
            a.created_at
        FROM restaurant_alerts a
        LEFT JOIN restaurant_plats p ON p.id = a.plat_id
        WHERE {where_sql}
        ORDER BY
            CASE a.severity
                WHEN 'critical' THEN 1
                WHEN 'warning' THEN 2
                ELSE 3
            END,
            a.created_at DESC
    """)

    df = query_df(sql, params)

    alerts = []
    for _, row in df.iterrows():
        alerts.append({
            "id": int(row["id"]),
            "alert_type": row["alert_type"],
            "severity": row["severity"],
            "message": row["message"],
            "plat_id": int(row["plat_id"]) if row["plat_id"] else None,
            "plat_nom": row["plat_nom"],
            "ingredient_id": None,  # Would come from ingredient alerts
            "ingredient_nom": None,
            "current_value": _safe_float(row["current_value"]) if row["current_value"] is not None else None,
            "threshold": _safe_float(row["threshold"]) if row["threshold"] is not None else None,
            "created_at": row["created_at"],
        })

    return alerts
