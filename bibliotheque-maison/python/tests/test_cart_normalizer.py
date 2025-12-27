"""Tests pour utils.cart_normalizer."""

from __future__ import annotations

from utils.cart_normalizer import normalize_cart_rows


def test_normalize_cart_rows_basic():
    rows = [
        {
            "product_id": "42",
            "name": "Pain",
            "quantity": "2,5",
            "unit_price": "1,20",
            "vat": "5,5",
        }
    ]
    normalized = normalize_cart_rows(rows)
    assert normalized[0]["id"] == 42
    assert normalized[0]["nom"] == "Pain"
    assert normalized[0]["qty"] == 2.5
    assert normalized[0]["prix_vente"] == 1.2
    assert normalized[0]["tva"] == 5.5
    assert normalized[0]["prix_total"] == 3.0


def test_normalize_cart_rows_missing_name():
    rows = [{"id": 7, "qty": 3, "prix_vente": 2.0}]
    normalized = normalize_cart_rows(rows)
    assert normalized[0]["nom"] == "Produit 7"


def test_normalize_cart_rows_skips_invalid():
    rows = [None, "not-a-dict", {"id": 1}]
    normalized = normalize_cart_rows(rows)
    assert len(normalized) == 1
