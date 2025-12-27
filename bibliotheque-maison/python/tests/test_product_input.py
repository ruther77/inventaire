"""Tests pour catalog.product_input."""

from __future__ import annotations

from catalog.product_input import ProductInput, from_row


def test_product_input_as_dict():
    product = ProductInput(
        code_barre="123",
        libelle="Test",
        prix_achat_ht=1.2,
        prix_vente_ttc=2.4,
        tva=5.5,
    )
    payload = product.as_dict()
    assert payload["code_barre"] == "123"
    assert payload["nom"] == "Test"
    assert payload["prix_achat"] == 1.2
    assert payload["prix_vente"] == 2.4
    assert payload["codes"] == "123"


def test_product_input_from_row():
    row = {
        "codes": "456",
        "nom": "Produit",
        "prix_achat": 1.1,
        "prix_vente": 2.2,
    }
    product = from_row(row)
    assert product.code_barre == "456"
    assert product.libelle == "Produit"
    assert product.prix_achat_ht == 1.1
    assert product.prix_vente_ttc == 2.2
