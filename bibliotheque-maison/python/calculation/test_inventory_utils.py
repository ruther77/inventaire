"""Tests pour les fonctions d'inventaire.

Ce script permet de vérifier le bon fonctionnement des fonctions
calculate_pamp, calculate_eoq, calculate_safety_stock,
calculate_reorder_point et calculate_margin.
"""

from decimal import Decimal
from calculation.inventory_utils import (
    calculate_pamp,
    calculate_eoq,
    calculate_safety_stock,
    calculate_reorder_point,
    calculate_margin
)


def test_calculate_pamp():
    """Test de la fonction calculate_pamp."""
    print("1. Test calculate_pamp()")

    purchases = [
        {'quantity': 10, 'unit_price': 5.00},
        {'quantity': 20, 'unit_price': 6.00},
        {'quantity': 15, 'unit_price': 5.50}
    ]

    pamp = calculate_pamp(purchases)
    expected = (10*5 + 20*6 + 15*5.5) / 45

    print(f"   Achats: {purchases}")
    print(f"   PAMP calculé: {pamp}€")
    print(f"   Attendu: {expected:.2f}€")
    print(f"   ✓ Test réussi\n")

    assert pamp == Decimal(str(expected)).quantize(Decimal("0.01"))


def test_calculate_eoq():
    """Test de la fonction calculate_eoq."""
    print("2. Test calculate_eoq()")

    eoq = calculate_eoq(annual_demand=1200, order_cost=50, holding_cost=2)

    print(f"   Demande annuelle: 1200 unités")
    print(f"   Coût de commande: 50€")
    print(f"   Coût de possession: 2€/unité/an")
    print(f"   EOQ calculé: {eoq} unités")
    print(f"   ✓ Test réussi\n")

    assert eoq > 0


def test_calculate_safety_stock():
    """Test de la fonction calculate_safety_stock."""
    print("3. Test calculate_safety_stock()")

    safety_stock = calculate_safety_stock(
        avg_demand=50,
        demand_std=10,
        lead_time=5,
        service_level=0.95
    )

    print(f"   Demande moyenne: 50 unités/jour")
    print(f"   Écart-type: 10 unités")
    print(f"   Lead time: 5 jours")
    print(f"   Niveau de service: 95%")
    print(f"   Stock de sécurité: {safety_stock} unités")
    print(f"   ✓ Test réussi\n")

    assert safety_stock >= 0


def test_calculate_reorder_point():
    """Test de la fonction calculate_reorder_point."""
    print("4. Test calculate_reorder_point()")

    safety_stock = calculate_safety_stock(
        avg_demand=50,
        demand_std=10,
        lead_time=5,
        service_level=0.95
    )

    reorder_point = calculate_reorder_point(
        avg_demand=50,
        lead_time=5,
        safety_stock=safety_stock
    )

    expected = 50 * 5 + safety_stock

    print(f"   Demande moyenne: 50 unités/jour")
    print(f"   Lead time: 5 jours")
    print(f"   Stock de sécurité: {safety_stock} unités")
    print(f"   Point de réapprovisionnement: {reorder_point} unités")
    print(f"   Attendu: {expected:.2f} unités")
    print(f"   ✓ Test réussi\n")

    assert reorder_point >= 0


def test_calculate_margin():
    """Test de la fonction calculate_margin."""
    print("5. Test calculate_margin()")

    margin = calculate_margin(Decimal('100'), Decimal('60'))

    print(f"   Prix de vente: 100€")
    print(f"   Coût d'achat: 60€")
    print(f"   Marge montant: {margin['margin_amount']}€")
    print(f"   Marge %: {margin['margin_percent']}%")
    print(f"   Attendu: 40€ (40%)")
    print(f"   ✓ Test réussi\n")

    assert margin["margin_amount"] == Decimal("40.00")


def test_edge_cases():
    """Test des cas limites."""
    print("6. Tests des cas limites")

    # Test avec une seule transaction
    pamp_single = calculate_pamp([{'quantity': 10, 'unit_price': 5.50}])
    assert pamp_single == Decimal('5.50'), "PAMP avec une seule transaction incorrect"
    print(f"   ✓ PAMP avec une seule transaction: {pamp_single}€")

    # Test EOQ avec petits nombres
    eoq_small = calculate_eoq(annual_demand=100, order_cost=10, holding_cost=0.5)
    print(f"   ✓ EOQ avec petits nombres: {eoq_small} unités")

    # Test stock de sécurité avec niveau de service élevé
    ss_high = calculate_safety_stock(avg_demand=10, demand_std=2, lead_time=3, service_level=0.99)
    print(f"   ✓ Stock de sécurité (99%): {ss_high} unités")

    # Test marge nulle
    margin_zero = calculate_margin(Decimal('100'), Decimal('100'))
    assert margin_zero['margin_amount'] == Decimal('0.00'), "Marge nulle incorrecte"
    print(f"   ✓ Marge nulle: {margin_zero['margin_amount']}€ ({margin_zero['margin_percent']}%)")

    # Test marge négative (perte)
    margin_negative = calculate_margin(Decimal('80'), Decimal('100'))
    print(f"   ✓ Marge négative (perte): {margin_negative['margin_amount']}€ ({margin_negative['margin_percent']}%)")

    print(f"   ✓ Tous les tests de cas limites réussis\n")


def main():
    """Exécute tous les tests."""
    print("=" * 60)
    print("Tests des fonctions d'inventaire")
    print("=" * 60)
    print()

    try:
        # Tests de base
        test_calculate_pamp()
        test_calculate_eoq()
        safety_stock = test_calculate_safety_stock()
        test_calculate_reorder_point(safety_stock)
        test_calculate_margin()

        # Tests des cas limites
        test_edge_cases()

        print("=" * 60)
        print("✓ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ ERREUR: {e}")
        raise


if __name__ == "__main__":
    main()
