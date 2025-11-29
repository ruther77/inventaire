"""Reusable sample datasets for service-level tests."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    import pandas as pd  # noqa: F401


def _pd():
    """Lazy import pandas to avoid hard dependency during collection."""

    try:
        return importlib.import_module("pandas")
    except ModuleNotFoundError as exc:  # pragma: no cover - tests skip beforehand
        raise RuntimeError("pandas is required for sample datasets") from exc


def make_catalog_df() -> pd.DataFrame:
    """Return a deterministic catalog covering multiple categories/cases."""

    pd = _pd()
    return pd.DataFrame(
        [
            {
                "id": 1,
                "nom": "Eau gazeuse 1L",
                "categorie": "Boissons",
                "prix_achat": 0.6,
                "prix_vente": 1.4,
                "stock_actuel": 6,
                "ventes_30j": 45,
                "ean": "1234567890123",
            },
            {
                "id": 2,
                "nom": "Pâtes complètes",
                "categorie": "Epicerie",
                "prix_achat": 1.1,
                "prix_vente": 2.4,
                "stock_actuel": 1,
                "ventes_30j": 5,
                "ean": "9876543210987",
            },
            {
                "id": 3,
                "nom": "Savon liquide",
                "categorie": "Hygiene",
                "prix_achat": 2.0,
                "prix_vente": 3.9,
                "stock_actuel": 30,
                "ventes_30j": 0,
                "ean": "",
            },
            {
                "id": 4,
                "nom": "Jus mangue",
                "categorie": "Boissons",
                "prix_achat": 1.2,
                "prix_vente": 2.5,
                "stock_actuel": 0,
                "ventes_30j": 12,
                "ean": "0011223344556",
            },
        ]
    )


def make_suppliers_df() -> pd.DataFrame:
    pd = _pd()
    return pd.DataFrame(
        [
            {"produit_id": 1, "fournisseur": "Metro", "date_mvt": "2024-01-05"},
            {"produit_id": 2, "fournisseur": "Grossiste Local", "date_mvt": "2024-01-04"},
            {"produit_id": 4, "fournisseur": "Metro", "date_mvt": "2024-01-02"},
        ]
    )


def make_audit_diag_df() -> pd.DataFrame:
    pd = _pd()
    return pd.DataFrame(
        [
            {"id": 1, "nom": "Produit A", "stock_actuel": 10, "stock_calcule": 2, "ecart": 8},
            {"id": 2, "nom": "Produit B", "stock_actuel": 5, "stock_calcule": 9, "ecart": -4},
            {"id": 3, "nom": "Produit C", "stock_actuel": 0, "stock_calcule": 0, "ecart": 0},
        ]
    )


def make_audit_actions_df() -> pd.DataFrame:
    pd = _pd()
    return pd.DataFrame(
        [
            {
                "id": 10,
                "product_id": 1,
                "responsable": "Alice",
                "note": "Vérifier réception",
                "status": "A investiguer",
                "due_date": None,
                "created_at": pd.Timestamp("2024-01-01"),
                "updated_at": pd.Timestamp("2024-01-02"),
            },
            {
                "id": 11,
                "product_id": 2,
                "responsable": "Bob",
                "note": "Contrôle inventaire",
                "status": "En cours",
                "due_date": None,
                "created_at": pd.Timestamp("2024-01-03"),
                "updated_at": pd.Timestamp("2024-01-04"),
            },
        ]
    )


def make_dashboard_stock_df() -> pd.DataFrame:
    pd = _pd()
    return pd.DataFrame(
        [
            {
                "nom": "Produit valeur",
                "quantite_stock": 20,
                "prix_vente": 5.0,
                "valeur_stock": 100.0,
            },
            {
                "nom": "Produit valeur 2",
                "quantite_stock": 10,
                "prix_vente": 8.0,
                "valeur_stock": 80.0,
            },
        ]
    )
