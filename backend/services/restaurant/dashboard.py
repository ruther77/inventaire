"""Dashboard overview and forecast services for restaurant module."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from backend.services.catalog_data import fetch_customer_catalog
from core.inventory_forecast import forecast_daily_consumption
from backend.services.restaurant.constants import ALLOWED_FORECAST_GRANULARITY
from backend.services.restaurant.utils import _safe_float
from backend.services.restaurant.expenses import (
    expense_summary_by_month,
    expense_summary_by_cost_center,
)
from backend.services.restaurant.ingredients import list_plats, list_ingredients


def build_dashboard_overview(tenant_id: int) -> dict[str, Any]:
    """Assemble indicators for Dashboard page (expenses, dish margins, stocks)."""
    monthly = expense_summary_by_month(tenant_id, months=6)
    by_center = expense_summary_by_cost_center(tenant_id, months=3)
    plats = list_plats(tenant_id)
    ingredients = list_ingredients(tenant_id)
    low_stock = [ing for ing in ingredients if _safe_float(ing.get("stock_actuel")) <= 3]

    current_month_charges = _safe_float(monthly[0]["total_ht"]) if monthly else 0.0
    avg_margin = (
        sum(max(0.0, _safe_float(plat.get("marge_pct"))) for plat in plats) / len(plats)
        if plats
        else 0.0
    )
    active_menu = sum(1 for plat in plats if plat.get("actif"))
    margin_alerts = sum(1 for plat in plats if _safe_float(plat.get("marge_pct")) < 30.0)

    return {
        "metrics": {
            "current_month_charges": round(current_month_charges, 2),
            "avg_margin_pct": round(avg_margin, 2),
            "active_menu_items": active_menu,
            "margin_alerts": margin_alerts,
        },
        "charges_monthly": monthly,
        "charges_by_center": by_center,
        "menu_costs": plats,
        "low_stock_ingredients": low_stock,
    }


def _build_forecast_timeline(total_units: float, total_value: float, horizon: int, granularity: str) -> List[dict[str, Any]]:
    """Project expected consumption over the chosen scenario (daily/weekly/monthly)."""
    if total_units < 0:
        total_units = 0.0
    if total_value < 0:
        total_value = 0.0
    today = date.today()
    step = {"daily": 1, "weekly": 7, "monthly": 30}[granularity]
    remaining = horizon
    offset = 0
    timeline: List[dict[str, Any]] = []
    while remaining > 0:
        window = min(step, remaining)
        start = today + timedelta(days=offset)
        end = start + timedelta(days=window - 1)
        timeline.append(
            {
                "period_start": start,
                "period_end": end,
                "expected_units": round(total_units * window, 2),
                "expected_value": round(total_value * window, 2),
            }
        )
        offset += window
        remaining -= window
    return timeline


def build_forecast_overview(
    tenant_id: int,
    horizon_days: int = 30,
    granularity: str = "weekly",
    top_limit: int = 8,
) -> dict[str, Any]:
    """Build forecast view (estimated daily consumption, timeline, TOP products)."""
    safe_horizon = max(1, min(int(horizon_days), 180))
    granularity_key = granularity if granularity in ALLOWED_FORECAST_GRANULARITY else "weekly"
    catalog_df = fetch_customer_catalog(tenant_id=tenant_id)
    forecast_map = forecast_daily_consumption(tenant_id=tenant_id, horizon=safe_horizon)
    generated_at = datetime.utcnow()

    empty_result = {
        "horizon_days": safe_horizon,
        "granularity": granularity_key,
        "generated_at": generated_at,
        "metrics": {
            "total_daily_units": 0.0,
            "total_daily_value": 0.0,
            "at_risk_items": 0,
            "median_cover_days": None,
        },
        "timeline": _build_forecast_timeline(0.0, 0.0, safe_horizon, granularity_key),
        "top_products": [],
        "categories": [],
    }

    if catalog_df.empty or not forecast_map:
        return empty_result

    forecast_records = [
        {"product_id": int(pid), "forecast_daily": max(float(value or 0), 0.0)}
        for pid, value in forecast_map.items()
        if value and value > 0
    ]
    if not forecast_records:
        return empty_result

    forecast_df = pd.DataFrame.from_records(forecast_records)
    merged = forecast_df.merge(catalog_df, left_on="product_id", right_on="id", how="left")
    if merged.empty:
        return empty_result

    numeric_cols = ["prix_vente", "stock_actuel"]
    for col in numeric_cols:
        merged[col] = pd.to_numeric(merged.get(col), errors="coerce").fillna(0.0)

    merged["categorie"] = merged.get("categorie", "Autre").fillna("Autre")
    merged["nom"] = merged.get("nom", "Produit").fillna("Produit")
    merged["ean"] = merged.get("ean", "").fillna("")
    merged["forecast_value"] = merged["forecast_daily"] * merged["prix_vente"]
    merged["stock_cover_days"] = np.where(
        merged["forecast_daily"] > 0,
        merged["stock_actuel"] / merged["forecast_daily"],
        np.inf,
    )

    risk_threshold = max(3, min(14, safe_horizon))
    merged["risk_level"] = np.select(
        [
            merged["stock_cover_days"] <= 1,
            merged["stock_cover_days"] <= risk_threshold / 2,
            merged["stock_cover_days"] <= risk_threshold,
        ],
        ["critique", "alerte", "surveillance"],
        default="ok",
    )
    risk_priority = {"critique": 0, "alerte": 1, "surveillance": 2, "ok": 3}
    merged["risk_priority"] = merged["risk_level"].map(risk_priority)

    total_units = float(merged["forecast_daily"].sum())
    total_value = float(merged["forecast_value"].sum())
    at_risk = int((merged["risk_level"].isin(["critique", "alerte"])).sum())
    finite_cover = merged.loc[np.isfinite(merged["stock_cover_days"]), "stock_cover_days"]
    median_cover = float(finite_cover.median()) if not finite_cover.empty else None

    top_limit = max(1, int(top_limit))
    top_df = (
        merged.sort_values(by=["risk_priority", "stock_cover_days", "forecast_value"], ascending=[True, True, False])
        .head(top_limit)
        .copy()
    )

    categories_df = (
        merged.groupby("categorie", dropna=False)[["forecast_daily", "forecast_value"]]
        .sum()
        .reset_index()
        .sort_values(by="forecast_value", ascending=False)
    )

    return {
        "horizon_days": safe_horizon,
        "granularity": granularity_key,
        "generated_at": generated_at,
        "metrics": {
            "total_daily_units": round(total_units, 2),
            "total_daily_value": round(total_value, 2),
            "at_risk_items": at_risk,
            "median_cover_days": round(median_cover, 2) if median_cover is not None else None,
        },
        "timeline": _build_forecast_timeline(total_units, total_value, safe_horizon, granularity_key),
        "top_products": [
            {
                "product_id": int(row["product_id"]),
                "nom": row["nom"],
                "categorie": row["categorie"],
                "ean": row.get("ean"),
                "forecast_daily": round(float(row["forecast_daily"]), 2),
                "forecast_value": round(float(row["forecast_value"]), 2),
                "stock_actuel": round(float(row["stock_actuel"]), 2),
                "stock_cover_days": None
                if not np.isfinite(row["stock_cover_days"])
                else round(float(row["stock_cover_days"]), 2),
                "risk_level": row["risk_level"],
            }
            for row in top_df.to_dict("records")
        ],
        "categories": [
            {
                "categorie": row["categorie"] or "Autre",
                "forecast_daily": round(float(row["forecast_daily"]), 2),
                "forecast_value": round(float(row["forecast_value"]), 2),
            }
            for row in categories_df.to_dict("records")
        ],
    }
