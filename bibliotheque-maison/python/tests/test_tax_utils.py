"""Tests pour le module calculation.tax_utils."""

from __future__ import annotations

from decimal import Decimal

import pytest

from calculation.tax_utils import (
    infer_tva,
    calculate_ht_from_ttc,
    calculate_ttc_from_ht,
    calculate_tva_amount,
    infer_category,
    categorize_product,
    TVA_20_CATEGORIES,
)


class TestInferTva:
    """Tests pour infer_tva."""

    def test_alcohol_categories(self):
        """Teste les catégories alcool (20%)."""
        assert infer_tva("Spiritueux") == 20.0
        assert infer_tva("Bières") == 20.0
        assert infer_tva("Vins rouges") == 20.0

    def test_soft_drinks(self):
        """Teste les boissons non alcoolisées (20%)."""
        assert infer_tva("Softs / Énergisants") == 20.0

    def test_food_categories(self):
        """Teste les catégories alimentaires (5.5%)."""
        # Par défaut, les catégories non définies sont à 5.5%
        assert infer_tva("Épicerie") == 5.5
        assert infer_tva("Boulangerie") == 5.5

    def test_restaurant_categories(self):
        """Teste les catégories restauration (10%)."""
        assert infer_tva("Restauration") == 10.0
        assert infer_tva("Transport") == 10.0

    def test_unknown_category(self):
        """Teste les catégories inconnues."""
        assert infer_tva("Catégorie Inconnue") == 5.5

    def test_custom_default(self):
        """Teste la valeur par défaut personnalisée."""
        assert infer_tva("Inconnu", default_tva=10.0) == 10.0

    def test_custom_mapping(self):
        """Teste le mapping personnalisé."""
        custom = {"Mon Produit": 7.5}
        assert infer_tva("Mon Produit", custom_mapping=custom) == 7.5


class TestCalculateHtFromTtc:
    """Tests pour calculate_ht_from_ttc."""

    def test_20_percent(self):
        """Teste le calcul avec 20% de TVA."""
        result = calculate_ht_from_ttc(Decimal("120.00"), 20.0)
        assert result == Decimal("100.00")

    def test_5_5_percent(self):
        """Teste le calcul avec 5.5% de TVA."""
        result = calculate_ht_from_ttc(Decimal("10.55"), 5.5)
        assert result == Decimal("10.00")

    def test_10_percent(self):
        """Teste le calcul avec 10% de TVA."""
        result = calculate_ht_from_ttc(Decimal("11.00"), 10.0)
        assert result == Decimal("10.00")

    def test_precision(self):
        """Teste la précision des arrondis."""
        result = calculate_ht_from_ttc(Decimal("123.45"), 20.0, precision=2)
        assert str(result).count('.') <= 1
        decimals = str(result).split('.')[-1] if '.' in str(result) else ''
        assert len(decimals) <= 2

    def test_float_input(self):
        """Teste avec un float en entrée."""
        result = calculate_ht_from_ttc(120.00, 20.0)
        assert result == Decimal("100.00")


class TestCalculateTtcFromHt:
    """Tests pour calculate_ttc_from_ht."""

    def test_20_percent(self):
        """Teste le calcul avec 20% de TVA."""
        result = calculate_ttc_from_ht(Decimal("100.00"), 20.0)
        assert result == Decimal("120.00")

    def test_5_5_percent(self):
        """Teste le calcul avec 5.5% de TVA."""
        result = calculate_ttc_from_ht(Decimal("10.00"), 5.5)
        assert result == Decimal("10.55")

    def test_10_percent(self):
        """Teste le calcul avec 10% de TVA."""
        result = calculate_ttc_from_ht(Decimal("10.00"), 10.0)
        assert result == Decimal("11.00")

    def test_roundtrip(self):
        """Teste le cycle complet HT -> TTC -> HT."""
        ht_original = Decimal("100.00")
        ttc = calculate_ttc_from_ht(ht_original, 20.0)
        ht_recovered = calculate_ht_from_ttc(ttc, 20.0)
        assert ht_original == ht_recovered


class TestCalculateTvaAmount:
    """Tests pour calculate_tva_amount."""

    def test_basic_calculation(self):
        """Teste le calcul basique du montant de TVA."""
        result = calculate_tva_amount(Decimal("120.00"), 20.0)
        assert result == Decimal("20.00")

    def test_5_5_percent(self):
        """Teste avec 5.5% de TVA."""
        result = calculate_tva_amount(Decimal("10.55"), 5.5)
        assert result == Decimal("0.55")

    def test_consistency(self):
        """Teste la cohérence avec les autres fonctions."""
        ttc = Decimal("120.00")
        tva_rate = 20.0
        ht = calculate_ht_from_ttc(ttc, tva_rate)
        tva = calculate_tva_amount(ttc, tva_rate)
        assert ht + tva == ttc


class TestInferCategory:
    """Tests pour infer_category."""

    def test_spirits(self):
        """Teste la détection des spiritueux."""
        assert infer_category("WHISKY JACK DANIELS") == "Spiritueux"
        assert infer_category("VODKA ABSOLUT") == "Spiritueux"
        assert infer_category("RHUM HAVANA CLUB") == "Spiritueux"

    def test_champagne(self):
        """Teste la détection du champagne."""
        assert infer_category("CHAMPAGNE MOËT") == "Effervescents / Champagne"
        assert infer_category("PROSECCO ITALIEN") == "Effervescents / Champagne"

    def test_wines(self):
        """Teste la détection des vins."""
        assert infer_category("VIN ROUGE BORDEAUX") == "Vins rouges"
        assert infer_category("MERLOT 2020") == "Vins rouges"

    def test_beers(self):
        """Teste la détection des bières."""
        assert infer_category("BIÈRE HEINEKEN") == "Bières"
        assert infer_category("IPA ARTISANALE") == "Bières"

    def test_soft_drinks(self):
        """Teste la détection des boissons softs."""
        assert infer_category("COCA COLA 33CL") == "Softs / Énergisants"
        assert infer_category("RED BULL") == "Softs / Énergisants"

    def test_food(self):
        """Teste la détection des aliments."""
        assert infer_category("RIZ BASMATI") == "Épicerie"
        assert infer_category("PATES BARILLA") == "Épicerie"

    def test_default_category(self):
        """Teste la catégorie par défaut."""
        assert infer_category("PRODUIT INCONNU") == "Épicerie"

    def test_custom_default(self):
        """Teste la catégorie par défaut personnalisée."""
        assert infer_category("PRODUIT INCONNU", default_category="Autre") == "Autre"

    def test_case_insensitive(self):
        """Teste l'insensibilité à la casse."""
        assert infer_category("whisky jack daniels") == "Spiritueux"


class TestCategorizeProduct:
    """Tests pour categorize_product."""

    def test_returns_tuple(self):
        """Teste que la fonction retourne un tuple."""
        result = categorize_product("WHISKY JACK DANIELS")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_category_and_tva(self):
        """Teste la cohérence catégorie/TVA."""
        category, tva = categorize_product("WHISKY JACK DANIELS")
        assert category == "Spiritueux"
        assert tva == 20.0

    def test_food_product(self):
        """Teste un produit alimentaire."""
        category, tva = categorize_product("RIZ BASMATI 1KG")
        assert category == "Épicerie"
        assert tva == 5.5

    def test_soft_drink(self):
        """Teste une boisson soft."""
        category, tva = categorize_product("COCA COLA 33CL")
        assert category == "Softs / Énergisants"
        assert tva == 20.0


class TestIntegration:
    """Tests d'intégration."""

    def test_full_workflow(self, sample_products):
        """Teste le workflow complet de catégorisation."""
        for product in sample_products:
            category, tva = categorize_product(product)

            # Vérifier que la catégorie est valide
            assert isinstance(category, str)
            assert len(category) > 0

            # Vérifier que la TVA est valide
            assert tva in [2.1, 5.5, 10.0, 20.0]

            # Vérifier la cohérence
            inferred_tva = infer_tva(category)
            assert inferred_tva == tva

    def test_price_calculation_workflow(self):
        """Teste le calcul de prix complet."""
        # Simuler un produit avec son prix et sa TVA
        products = [
            ("WHISKY JACK DANIELS", Decimal("30.00")),  # Alcool 20%
            ("RIZ BASMATI", Decimal("2.50")),           # Épicerie 5.5%
        ]

        for product_name, prix_ht in products:
            category, tva = categorize_product(product_name)
            prix_ttc = calculate_ttc_from_ht(prix_ht, tva)
            montant_tva = calculate_tva_amount(prix_ttc, tva)

            # Vérifier la cohérence
            assert prix_ht + montant_tva == prix_ttc
            assert calculate_ht_from_ttc(prix_ttc, tva) == prix_ht
