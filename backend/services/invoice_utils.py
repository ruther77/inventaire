"""Shared helpers for invoice data normalization."""

from __future__ import annotations

import pandas as pd


def prepare_invoice_dataframe(source_df: pd.DataFrame, margin_rate: float) -> pd.DataFrame:
    """Normalize numeric columns and compute margins/totals for invoice lines."""

    if not isinstance(source_df, pd.DataFrame) or source_df.empty:
        return source_df

    working_df = source_df.copy()

    if "quantite_recue" not in working_df.columns and "qte_init" in working_df.columns:
        working_df["quantite_recue"] = working_df["qte_init"]
    elif "quantite_recue" in working_df.columns and "qte_init" in working_df.columns:
        working_df["quantite_recue"] = working_df["quantite_recue"].fillna(working_df["qte_init"])

    numeric_defaults: dict[str, float] = {
        "prix_achat": 0.0,
        "prix_vente": 0.0,
        "tva": 0.0,
        "prix_achat_catalogue": 0.0,
        "prix_vente_catalogue": 0.0,
        "tva_catalogue": 0.0,
        "quantite_recue": 0.0,
        "qte_init": 0.0,
    }

    for column, default_value in numeric_defaults.items():
        if column not in working_df.columns:
            working_df[column] = default_value
        working_df[column] = pd.to_numeric(working_df[column], errors="coerce").fillna(default_value)

    safe_margin = max(0.0, float(margin_rate))
    working_df["prix_vente_minimum"] = (working_df["prix_achat"] * (1.0 + safe_margin)).round(2)
    working_df["montant_ht"] = (working_df["prix_achat"] * working_df["quantite_recue"]).round(2)
    working_df["montant_tva"] = (working_df["montant_ht"] * (working_df["tva"] / 100.0)).round(2)
    working_df["montant_ttc"] = (working_df["montant_ht"] + working_df["montant_tva"]).round(2)

    working_df["prix_vente_catalogue_ttc"] = (
        working_df["prix_vente_catalogue"] * (1.0 + working_df["tva_catalogue"] / 100.0)
    ).round(2)

    purchase_base = working_df["prix_achat"].replace(0, pd.NA)
    working_df["marge_catalogue_pct"] = (
        (working_df["prix_vente_catalogue"] - working_df["prix_achat"]) / purchase_base
    ).multiply(100).fillna(0.0).round(2)

    working_df["alerte_marge"] = working_df["prix_vente_catalogue"] < working_df["prix_vente_minimum"]

    return working_df


__all__ = ["prepare_invoice_dataframe"]
