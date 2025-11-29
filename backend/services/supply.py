"""Supply planning computations reused by the REST API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np
import pandas as pd

from backend.services.catalog_data import fetch_customer_catalog, fetch_recent_suppliers
from core.inventory_forecast import forecast_daily_consumption


@dataclass(frozen=True)
class SupplyPlanParams:
    target_coverage: int
    alert_threshold: int
    min_daily_sales: float
    categories: Sequence[str] | None
    search: str | None


def _sanitize_float(value) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if np.isnan(numeric) or np.isinf(numeric):
        return None
    return numeric


def compute_supply_plan(
    target_coverage: int = 21,
    alert_threshold: int = 7,
    min_daily_sales: float = 0.0,
    categories: Iterable[str] | None = None,
    search: str | None = None,
    *,
    tenant_id: int = 1,
) -> dict[str, object]:
    """Return the dynamic supply plan matching the former Streamlit view."""

    safe_target = max(1, int(target_coverage))
    safe_alert = max(1, min(int(alert_threshold), safe_target))
    safe_min_sales = max(0.0, float(min_daily_sales))
    normalized_categories: list[str] | None = None
    if categories:
        normalized_categories = sorted({str(cat) for cat in categories if cat})
        if not normalized_categories:
            normalized_categories = None
    normalized_search = search.strip() if isinstance(search, str) else None
    params = SupplyPlanParams(
        target_coverage=safe_target,
        alert_threshold=safe_alert,
        min_daily_sales=safe_min_sales,
        categories=normalized_categories,
        search=normalized_search or None,
    )

    catalog_df = fetch_customer_catalog(tenant_id=int(tenant_id))
    if catalog_df.empty:
        return {
            "params": params.__dict__,
            "summary": {
                "analyzed": 0,
                "recommended_count": 0,
                "units_to_order": 0,
                "value_total": 0.0,
                "margin_total": 0.0,
            },
            "items": [],
            "supplier_breakdown": [],
        }

    planning_df = catalog_df.copy()
    planning_df["ventes_jour"] = (planning_df["ventes_30j"].fillna(0.0) / 30.0).clip(lower=0.0)
    planning_df["stock_actuel"] = planning_df["stock_actuel"].fillna(0.0).clip(lower=0.0)

    forecast_map = forecast_daily_consumption(tenant_id=int(tenant_id), horizon=safe_target)
    planning_df["ventes_prevision"] = planning_df["id"].map(lambda pid: forecast_map.get(int(pid)))
    planning_df["ventes_prevision"] = planning_df["ventes_prevision"].fillna(planning_df["ventes_jour"])

    daily_sales = planning_df["ventes_jour"]
    stock_levels = planning_df["stock_actuel"]
    planning_df["couverture_jours"] = np.where(
        daily_sales > 0,
        stock_levels / daily_sales,
        np.where(stock_levels > 0, np.inf, 0.0),
    )

    supplier_df = fetch_recent_suppliers(tenant_id=int(tenant_id))
    if not supplier_df.empty:
        planning_df = planning_df.merge(
            supplier_df.rename(columns={"produit_id": "id"}),
            how="left",
            on="id",
        )
    if "fournisseur" not in planning_df.columns:
        planning_df["fournisseur"] = "Non renseigné"
    else:
        planning_df["fournisseur"] = planning_df["fournisseur"].fillna("Non renseigné")

    planning_df["objectif_stock"] = np.maximum(safe_target * planning_df["ventes_jour"], 0.0)
    raw_reorder = planning_df["objectif_stock"] - planning_df["stock_actuel"]
    planning_df["quantite_a_commander"] = np.maximum(np.ceil(raw_reorder), 0).astype(int)
    planning_df["objectif_stock_prevision"] = np.maximum(safe_target * planning_df["ventes_prevision"], 0.0)
    raw_auto = planning_df["objectif_stock_prevision"] - planning_df["stock_actuel"]
    planning_df["quantite_auto"] = np.maximum(np.ceil(raw_auto), 0).astype(int)
    planning_df["tva"] = planning_df.get("tva", 0.0).fillna(0.0)
    tva_factor = (planning_df["tva"] / 100.0).clip(lower=0.0)
    tva_multiplier = (1 + tva_factor).replace(0, 1)
    sale_ht = planning_df["prix_vente"].fillna(0.0) / tva_multiplier
    sale_ht = sale_ht.replace([np.inf, -np.inf], 0.0).fillna(0.0)
    planning_df["prix_vente_ht"] = sale_ht
    planning_df["valeur_commande"] = planning_df["quantite_a_commander"] * planning_df["prix_vente"].fillna(0.0)
    planning_df["ecart_couverture"] = planning_df["couverture_jours"] - float(safe_target)
    planning_df["marge_unitaire"] = sale_ht - planning_df["prix_achat"].fillna(0.0)
    planning_df["marge_pct"] = np.where(
        sale_ht > 0,
        (planning_df["marge_unitaire"] / sale_ht.replace(0, np.nan)) * 100,
        np.nan,
    )
    planning_df["marge_commande"] = planning_df["marge_unitaire"] * planning_df["quantite_a_commander"]

    if safe_min_sales > 0:
        planning_df = planning_df[planning_df["ventes_jour"] >= safe_min_sales]

    all_categories = sorted(
        {cat for cat in planning_df["categorie"].dropna().unique().tolist() if isinstance(cat, str)}
    )

    if normalized_categories:
        planning_df = planning_df[planning_df["categorie"].isin(normalized_categories)]

    if params.search:
        lowered = params.search.lower()
        planning_df = planning_df[
            planning_df["nom"].str.contains(lowered, case=False, na=False)
            | planning_df["categorie"].str.contains(lowered, case=False, na=False)
            | planning_df["ean"].astype(str).str.contains(lowered, case=False, na=False)
        ]

    if planning_df.empty:
        return {
            "params": params.__dict__,
            "summary": {
                "analyzed": 0,
                "recommended_count": 0,
                "units_to_order": 0,
                "value_total": 0.0,
                "margin_total": 0.0,
            },
            "items": [],
            "supplier_breakdown": [],
        }

    if safe_min_sales <= 0:
        rotation_mask = planning_df["ventes_jour"] > 0
    else:
        rotation_mask = planning_df["ventes_jour"] >= safe_min_sales

    priority_levels = np.select(
        [
            rotation_mask & (planning_df["couverture_jours"] <= safe_alert),
            rotation_mask & (planning_df["quantite_a_commander"] > 0),
            planning_df["quantite_a_commander"] > 0,
        ],
        ["Critique", "Tendue", "Surveillance"],
        default="Confort",
    )
    planning_df["niveau_priorite"] = priority_levels
    priority_order = {"Critique": 0, "Tendue": 1, "Surveillance": 2, "Confort": 3}
    planning_df["ordre_priorite"] = planning_df["niveau_priorite"].map(priority_order)

    planning_df = planning_df.sort_values(
        by=["ordre_priorite", "couverture_jours", "ventes_jour"],
        ascending=[True, True, False],
    )

    summary = {
        "analyzed": int(len(planning_df)),
        "recommended_count": int((planning_df["quantite_a_commander"] > 0).sum()),
        "units_to_order": int(planning_df["quantite_a_commander"].sum()),
        "value_total": float(planning_df["valeur_commande"].sum()),
        "margin_total": float(planning_df["marge_commande"].sum()),
    }

    item_columns = [
        "id",
        "nom",
        "categorie",
        "ventes_jour",
        "stock_actuel",
        "couverture_jours",
        "ecart_couverture",
        "niveau_priorite",
        "quantite_a_commander",
        "quantite_auto",
        "valeur_commande",
        "ventes_prevision",
        "marge_pct",
        "marge_commande",
        "tva",
        "fournisseur",
        "ean",
        "abc_class",
        "xyz_class",
    ]

    result_items: List[dict[str, object]] = []
    for _, row in planning_df[item_columns].iterrows():
        item = {
            "id": int(row["id"]),
            "nom": row["nom"],
            "categorie": row.get("categorie"),
            "ventes_jour": float(row["ventes_jour"]),
            "stock_actuel": float(row["stock_actuel"]),
            "couverture_jours": _sanitize_float(row["couverture_jours"]),
            "ecart_couverture": _sanitize_float(row["ecart_couverture"]),
            "niveau_priorite": row["niveau_priorite"],
            "quantite_a_commander": int(row["quantite_a_commander"]),
            "quantite_auto": int(row.get("quantite_auto") or 0),
            "valeur_commande": float(row["valeur_commande"]),
            "ventes_prevision": float(row.get("ventes_prevision") or row["ventes_jour"]),
            "marge_pct": _sanitize_float(row["marge_pct"]),
            "marge_commande": float(row["marge_commande"]),
            "tva": _sanitize_float(row.get("tva")),
            "fournisseur": row.get("fournisseur"),
            "ean": row.get("ean"),
            "abc_class": row.get("abc_class"),
            "xyz_class": row.get("xyz_class"),
        }
        result_items.append(item)

    supplier_breakdown: list[dict[str, object]] = []
    order_candidates = planning_df[planning_df["quantite_a_commander"] > 0]
    if not order_candidates.empty:
        supplier_summary = (
            order_candidates.groupby("fournisseur", as_index=False)
            .agg(
                articles=("id", "count"),
                quantite=("quantite_a_commander", "sum"),
                valeur=("valeur_commande", "sum"),
                marge=("marge_commande", "sum"),
            )
            .sort_values("valeur", ascending=False)
        )
        for _, row in supplier_summary.iterrows():
            supplier_breakdown.append(
                {
                    "fournisseur": row["fournisseur"],
                    "articles": int(row["articles"]),
                    "quantite": int(row["quantite"]),
                    "valeur": float(row["valeur"]),
                    "marge": float(row["marge"]),
                }
            )

    return {
        "params": params.__dict__,
        "summary": summary,
        "available_categories": all_categories,
        "items": result_items,
        "supplier_breakdown": supplier_breakdown,
    }


__all__ = ["compute_supply_plan"]
