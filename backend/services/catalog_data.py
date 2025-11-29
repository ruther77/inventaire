"""Shared catalog data loaders usable by FastAPI and Streamlit."""

from __future__ import annotations

import re
from typing import Final

import pandas as pd

from core.data_repository import query_df


_MIN_GTIN_LENGTH: Final[int] = 3
_MAX_GTIN_LENGTH: Final[int] = 14

_CUSTOMER_CATALOG_SQL = """
    WITH ventes_30j AS (
        SELECT
            m.produit_id,
            SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END) AS qte_sorties_30j
        FROM mouvements_stock m
        WHERE m.tenant_id = :tenant_id
          AND m.date_mvt >= now() - INTERVAL '30 days'
        GROUP BY m.produit_id
    )
    SELECT
        p.id,
        p.nom,
        p.categorie,
        COALESCE(p.prix_achat, 0) AS prix_achat,
        COALESCE(p.prix_vente, 0) AS prix_vente,
        COALESCE(p.tva, 0) AS tva,
        COALESCE(p.stock_actuel, 0) AS stock_actuel,
        COALESCE(tv.qte_sorties_30j, 0) AS ventes_30j,
        barcode.code AS ean,
        COALESCE(ic.abc_class, 'C') AS abc_class,
        COALESCE(ic.xyz_class, 'Z') AS xyz_class
    FROM produits p
    LEFT JOIN ventes_30j tv ON tv.produit_id = p.id
    LEFT JOIN LATERAL (
        SELECT pb.code
        FROM produits_barcodes pb
        WHERE pb.produit_id = p.id
          AND pb.tenant_id = p.tenant_id
        ORDER BY pb.is_principal DESC, pb.created_at ASC, pb.id ASC
        LIMIT 1
    ) AS barcode ON TRUE
    LEFT JOIN inventory_classifications ic
        ON ic.product_id = p.id AND ic.tenant_id = p.tenant_id
    WHERE p.actif = TRUE
      AND p.tenant_id = :tenant_id
    ORDER BY p.categorie, p.nom;
"""

_RECENT_SUPPLIERS_SQL = """
    SELECT DISTINCT ON (m.produit_id)
        m.produit_id,
        COALESCE(NULLIF(TRIM(m.source), ''), 'Non renseigné') AS fournisseur,
        m.date_mvt
    FROM mouvements_stock m
    WHERE m.type = 'ENTREE'
      AND m.tenant_id = :tenant_id
    ORDER BY m.produit_id, m.date_mvt DESC
"""


def _normalize_ean(value: str | int | float | None) -> str:
    """Return a canonical GTIN if valid, otherwise an empty string."""

    if value is None:
        return ""

    text = str(value).strip()
    if not text:
        return ""

    digits_only = re.sub(r"\D", "", text)
    if not digits_only:
        return ""

    length = len(digits_only)
    if length < _MIN_GTIN_LENGTH or length > _MAX_GTIN_LENGTH:
        return ""

    return digits_only


def fetch_customer_catalog(*, tenant_id: int = 1) -> pd.DataFrame:
    """Return the active catalog enriched with rolling sales and main barcode."""

    df = query_df(_CUSTOMER_CATALOG_SQL, params={"tenant_id": int(tenant_id)})
    if df.empty:
        return df.assign(
            categorie=[],
            prix_achat=[],
            prix_vente=[],
            tva=[],
            stock_actuel=[],
            ventes_30j=[],
            ean=[],
        )

    expected_cols = {"categorie", "prix_achat", "prix_vente", "tva", "stock_actuel", "ventes_30j"}
    for col in expected_cols:
        if col not in df.columns:
            df[col] = 0

    numeric_cols = ["prix_achat", "prix_vente", "tva", "stock_actuel", "ventes_30j"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    if "id" in df.columns:
        df["id"] = pd.to_numeric(df["id"], errors="coerce").fillna(0).astype(int)

    if "categorie" in df.columns:
        df["categorie"] = df["categorie"].fillna("Autre")
    else:
        df["categorie"] = "Autre"

    if "ean" in df.columns:
        df["ean"] = df["ean"].fillna("").astype(str)
    else:
        df["ean"] = ""

    for col, default in (("abc_class", "C"), ("xyz_class", "Z")):
        if col in df.columns:
            df[col] = df[col].fillna(default)
        else:
            df[col] = default

    df["ean"] = df["ean"].map(_normalize_ean)
    return df


def fetch_recent_suppliers(*, tenant_id: int = 1) -> pd.DataFrame:
    """Return the most recent incoming-movement source per product."""

    df = query_df(_RECENT_SUPPLIERS_SQL, params={"tenant_id": int(tenant_id)})
    if df.empty:
        return pd.DataFrame(columns=["produit_id", "fournisseur", "date_mvt"])

    if "fournisseur" in df.columns:
        df["fournisseur"] = df["fournisseur"].fillna("Non renseigné")
    else:
        df["fournisseur"] = "Non renseigné"
    return df


__all__ = ["fetch_customer_catalog", "fetch_recent_suppliers"]
