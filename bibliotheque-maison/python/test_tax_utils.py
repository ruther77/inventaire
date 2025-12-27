#!/usr/bin/env python3
"""Test script pour valider le module tax_utils.py"""

from decimal import Decimal
from calculation.tax_utils import (
    infer_tva,
    infer_tva_from_category,
    calculate_ht_from_ttc,
    calculate_ttc_from_ht,
    calculate_tva_amount,
    infer_category,
    categorize_product,
)


def test_infer_tva():
    """Test de la fonction infer_tva (calcul du taux depuis montants)"""
    print("=== Test infer_tva ===")

    # Test TVA 20%
    result = infer_tva(Decimal("120.00"), Decimal("100.00"))
    print(f"infer_tva(120.00, 100.00) = {result}")
    assert result == Decimal("20.00"), f"Expected 20.00, got {result}"

    # Test TVA 10%
    result = infer_tva(Decimal("110.00"), Decimal("100.00"))
    print(f"infer_tva(110.00, 100.00) = {result}")
    assert result == Decimal("10.00"), f"Expected 10.00, got {result}"

    # Test TVA 5.5%
    result = infer_tva(Decimal("105.50"), Decimal("100.00"))
    print(f"infer_tva(105.50, 100.00) = {result}")
    assert result == Decimal("5.50"), f"Expected 5.50, got {result}"

    # Test division par zéro
    result = infer_tva(Decimal("100.00"), Decimal("0.00"))
    print(f"infer_tva(100.00, 0.00) = {result} (protection division par zéro)")
    assert result == Decimal("0.00"), f"Expected 0.00, got {result}"

    print("OK\n")


def test_calculate_ht_from_ttc():
    """Test de calculate_ht_from_ttc"""
    print("=== Test calculate_ht_from_ttc ===")

    result = calculate_ht_from_ttc(Decimal("120.00"), 20.0)
    print(f"calculate_ht_from_ttc(120.00, 20%) = {result}")
    assert result == Decimal("100.00"), f"Expected 100.00, got {result}"

    result = calculate_ht_from_ttc(Decimal("10.55"), 5.5)
    print(f"calculate_ht_from_ttc(10.55, 5.5%) = {result}")
    assert result == Decimal("10.00"), f"Expected 10.00, got {result}"

    print("OK\n")


def test_calculate_ttc_from_ht():
    """Test de calculate_ttc_from_ht"""
    print("=== Test calculate_ttc_from_ht ===")

    result = calculate_ttc_from_ht(Decimal("100.00"), 20.0)
    print(f"calculate_ttc_from_ht(100.00, 20%) = {result}")
    assert result == Decimal("120.00"), f"Expected 120.00, got {result}"

    result = calculate_ttc_from_ht(Decimal("10.00"), 5.5)
    print(f"calculate_ttc_from_ht(10.00, 5.5%) = {result}")
    assert result == Decimal("10.55"), f"Expected 10.55, got {result}"

    print("OK\n")


def test_calculate_tva_amount():
    """Test de calculate_tva_amount avec is_ttc"""
    print("=== Test calculate_tva_amount ===")

    # Depuis TTC
    result = calculate_tva_amount(Decimal("120.00"), 20.0, is_ttc=True)
    print(f"calculate_tva_amount(120.00, 20%, is_ttc=True) = {result}")
    assert result == Decimal("20.00"), f"Expected 20.00, got {result}"

    # Depuis HT
    result = calculate_tva_amount(Decimal("100.00"), 20.0, is_ttc=False)
    print(f"calculate_tva_amount(100.00, 20%, is_ttc=False) = {result}")
    assert result == Decimal("20.00"), f"Expected 20.00, got {result}"

    # Test TVA 10% depuis TTC
    result = calculate_tva_amount(Decimal("110.00"), 10.0, is_ttc=True)
    print(f"calculate_tva_amount(110.00, 10%, is_ttc=True) = {result}")
    assert result == Decimal("10.00"), f"Expected 10.00, got {result}"

    print("OK\n")


def test_infer_category():
    """Test de infer_category"""
    print("=== Test infer_category ===")

    result = infer_category("WHISKY JACK DANIELS")
    print(f'infer_category("WHISKY JACK DANIELS") = {result}')
    assert result == "Spiritueux", f"Expected 'Spiritueux', got {result}"

    result = infer_category("COCA COLA 33CL")
    print(f'infer_category("COCA COLA 33CL") = {result}')
    assert result == "Softs / Énergisants", f"Expected 'Softs / Énergisants', got {result}"

    result = infer_category("RIZ BASMATI")
    print(f'infer_category("RIZ BASMATI") = {result}')
    assert result == "Épicerie", f"Expected 'Épicerie', got {result}"

    result = infer_category("ARTICLE INCONNU")
    print(f'infer_category("ARTICLE INCONNU") = {result}')
    assert result == "Épicerie", f"Expected 'Épicerie', got {result}"

    print("OK\n")


def test_categorize_product():
    """Test de categorize_product"""
    print("=== Test categorize_product ===")

    category, tva = categorize_product("WHISKY JACK DANIELS")
    print(f'categorize_product("WHISKY JACK DANIELS") = ({category}, {tva})')
    assert category == "Spiritueux", f"Expected 'Spiritueux', got {category}"
    assert tva == 20.0, f"Expected 20.0, got {tva}"

    category, tva = categorize_product("RIZ BASMATI")
    print(f'categorize_product("RIZ BASMATI") = ({category}, {tva})')
    assert category == "Épicerie", f"Expected 'Épicerie', got {category}"
    assert tva == 5.5, f"Expected 5.5, got {tva}"

    category, tva = categorize_product("CHAMPAGNE MOËT")
    print(f'categorize_product("CHAMPAGNE MOËT") = ({category}, {tva})')
    assert category == "Effervescents / Champagne", f"Expected 'Effervescents / Champagne', got {category}"
    assert tva == 20.0, f"Expected 20.0, got {tva}"

    print("OK\n")


def test_infer_tva_from_category():
    """Test de infer_tva_from_category"""
    print("=== Test infer_tva_from_category ===")

    result = infer_tva_from_category("Spiritueux")
    print(f'infer_tva_from_category("Spiritueux") = {result}')
    assert result == 20.0, f"Expected 20.0, got {result}"

    result = infer_tva_from_category("Épicerie")
    print(f'infer_tva_from_category("Épicerie") = {result}')
    assert result == 5.5, f"Expected 5.5, got {result}"

    result = infer_tva_from_category("Restauration")
    print(f'infer_tva_from_category("Restauration") = {result}')
    assert result == 10.0, f"Expected 10.0, got {result}"

    result = infer_tva_from_category("Inconnu")
    print(f'infer_tva_from_category("Inconnu") = {result} (default)')
    assert result == 5.5, f"Expected 5.5, got {result}"

    print("OK\n")


if __name__ == "__main__":
    print("Tests du module tax_utils.py\n")
    print("=" * 50)
    print()

    try:
        test_infer_tva()
        test_calculate_ht_from_ttc()
        test_calculate_ttc_from_ht()
        test_calculate_tva_amount()
        test_infer_category()
        test_categorize_product()
        test_infer_tva_from_category()

        print("=" * 50)
        print("\nTous les tests sont passés avec succès!")

    except AssertionError as e:
        print(f"\nERREUR: {e}")
        exit(1)
    except Exception as e:
        print(f"\nERREUR inattendue: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
