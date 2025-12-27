#!/usr/bin/env python3
"""Exemples d'utilisation du module tax_utils.py"""

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


def example_basic_calculations():
    """Exemples de calculs de base"""
    print("=" * 60)
    print("EXEMPLES DE CALCULS DE BASE")
    print("=" * 60)
    print()

    # 1. Déduire le taux de TVA depuis des montants
    print("1. Déduire le taux de TVA depuis des montants TTC et HT")
    print("-" * 60)
    ttc = Decimal("120.00")
    ht = Decimal("100.00")
    taux = infer_tva(ttc, ht)
    print(f"   TTC: {ttc} EUR")
    print(f"   HT:  {ht} EUR")
    print(f"   → Taux TVA: {taux}%")
    print()

    # 2. Calculer HT depuis TTC
    print("2. Calculer le montant HT depuis le TTC")
    print("-" * 60)
    ttc = Decimal("120.00")
    taux_tva = 20.0
    ht = calculate_ht_from_ttc(ttc, taux_tva)
    print(f"   TTC:       {ttc} EUR")
    print(f"   Taux TVA:  {taux_tva}%")
    print(f"   → HT:      {ht} EUR")
    print()

    # 3. Calculer TTC depuis HT
    print("3. Calculer le montant TTC depuis le HT")
    print("-" * 60)
    ht = Decimal("100.00")
    taux_tva = 20.0
    ttc = calculate_ttc_from_ht(ht, taux_tva)
    print(f"   HT:        {ht} EUR")
    print(f"   Taux TVA:  {taux_tva}%")
    print(f"   → TTC:     {ttc} EUR")
    print()

    # 4. Calculer le montant de TVA
    print("4. Calculer le montant de TVA")
    print("-" * 60)

    # Depuis TTC
    ttc = Decimal("120.00")
    taux_tva = 20.0
    montant_tva = calculate_tva_amount(ttc, taux_tva, is_ttc=True)
    print(f"   a) Depuis TTC:")
    print(f"      TTC:        {ttc} EUR")
    print(f"      Taux TVA:   {taux_tva}%")
    print(f"      → Montant TVA: {montant_tva} EUR")
    print()

    # Depuis HT
    ht = Decimal("100.00")
    montant_tva = calculate_tva_amount(ht, taux_tva, is_ttc=False)
    print(f"   b) Depuis HT:")
    print(f"      HT:         {ht} EUR")
    print(f"      Taux TVA:   {taux_tva}%")
    print(f"      → Montant TVA: {montant_tva} EUR")
    print()


def example_product_categorization():
    """Exemples de catégorisation de produits"""
    print("=" * 60)
    print("EXEMPLES DE CATÉGORISATION DE PRODUITS")
    print("=" * 60)
    print()

    products = [
        "WHISKY JACK DANIELS 70CL",
        "CHAMPAGNE MOËT & CHANDON BRUT",
        "VIN ROUGE BORDEAUX 75CL",
        "BIERE HEINEKEN 33CL",
        "COCA COLA 1.5L",
        "EAU EVIAN 1L",
        "RIZ BASMATI 1KG",
        "PAIN DE MIE",
        "CHOCOLAT NOIR 100G",
        "ARTICLE INCONNU",
    ]

    for product in products:
        category = infer_category(product)
        tva = infer_tva_from_category(category)
        print(f"Produit:   {product:<40}")
        print(f"Catégorie: {category:<30} TVA: {tva}%")
        print()


def example_complete_workflow():
    """Exemple de workflow complet"""
    print("=" * 60)
    print("WORKFLOW COMPLET: ANALYSE D'UNE FACTURE")
    print("=" * 60)
    print()

    facture = [
        ("WHISKY JACK DANIELS 70CL", Decimal("35.90")),
        ("CHAMPAGNE BRUT", Decimal("28.50")),
        ("RIZ BASMATI 1KG", Decimal("3.50")),
        ("PAIN DE MIE", Decimal("2.10")),
        ("COCA COLA 2L", Decimal("2.80")),
    ]

    print(f"{'Produit':<35} {'Prix TTC':<12} {'Catégorie':<20} {'TVA%':<8} {'HT':<12} {'TVA':<12}")
    print("-" * 110)

    total_ttc = Decimal("0")
    total_ht = Decimal("0")
    total_tva = Decimal("0")

    for product_name, prix_ttc in facture:
        # Catégoriser le produit et obtenir le taux de TVA
        category, taux_tva = categorize_product(product_name)

        # Calculer HT et montant TVA
        prix_ht = calculate_ht_from_ttc(prix_ttc, taux_tva)
        montant_tva = calculate_tva_amount(prix_ttc, taux_tva, is_ttc=True)

        # Afficher la ligne
        print(
            f"{product_name:<35} {prix_ttc:>10.2f} € {category:<20} {taux_tva:>6.1f}% "
            f"{prix_ht:>10.2f} € {montant_tva:>10.2f} €"
        )

        # Accumuler les totaux
        total_ttc += prix_ttc
        total_ht += prix_ht
        total_tva += montant_tva

    print("-" * 110)
    print(
        f"{'TOTAL':<35} {total_ttc:>10.2f} € {'':<20} {'':<8} "
        f"{total_ht:>10.2f} € {total_tva:>10.2f} €"
    )
    print()


def example_tva_rates():
    """Exemples de taux de TVA français"""
    print("=" * 60)
    print("TAUX DE TVA FRANÇAIS STANDARDS")
    print("=" * 60)
    print()

    taux_examples = [
        (20.0, "Taux normal", ["Alcool", "Boissons alcoolisées", "Produits manufacturés"]),
        (10.0, "Taux intermédiaire", ["Restauration", "Transport", "Hébergement"]),
        (5.5, "Taux réduit", ["Alimentation", "Livres", "Produits de première nécessité"]),
        (2.1, "Taux super-réduit", ["Médicaments remboursables", "Presse"]),
    ]

    for taux, nom, categories in taux_examples:
        print(f"{taux:>5.1f}% - {nom:<25} : {', '.join(categories)}")

    print()
    print("Exemples de calculs pour 100 EUR HT:")
    print("-" * 60)

    ht = Decimal("100.00")
    for taux, nom, _ in taux_examples:
        ttc = calculate_ttc_from_ht(ht, taux)
        montant_tva = calculate_tva_amount(ht, taux, is_ttc=False)
        print(f"  {nom:<25} ({taux:>5.1f}%): TTC = {ttc:>7.2f} EUR  (TVA: {montant_tva:>6.2f} EUR)")

    print()


def example_edge_cases():
    """Exemples de cas limites"""
    print("=" * 60)
    print("CAS LIMITES ET PROTECTION")
    print("=" * 60)
    print()

    # Division par zéro
    print("1. Protection division par zéro")
    print("-" * 60)
    result = infer_tva(Decimal("100.00"), Decimal("0.00"))
    print(f"   infer_tva(100.00, 0.00) = {result}% (protection activée)")
    print()

    # Très petits montants
    print("2. Très petits montants")
    print("-" * 60)
    result = infer_tva(Decimal("100.00"), Decimal("0.0001"))
    print(f"   infer_tva(100.00, 0.0001) = {result}% (protection activée)")
    print()

    # Précision des calculs
    print("3. Précision des calculs (arrondi à 2 décimales)")
    print("-" * 60)
    ttc = Decimal("33.33")
    taux = 20.0
    ht = calculate_ht_from_ttc(ttc, taux)
    recalc_ttc = calculate_ttc_from_ht(ht, taux)
    print(f"   TTC original:  {ttc} EUR")
    print(f"   HT calculé:    {ht} EUR")
    print(f"   TTC recalculé: {recalc_ttc} EUR")
    print(f"   Différence:    {abs(ttc - recalc_ttc)} EUR (arrondi)")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" " * 15 + "MODULE TAX_UTILS.PY")
    print(" " * 10 + "Exemples d'utilisation pratique")
    print("=" * 60)
    print()

    example_basic_calculations()
    example_product_categorization()
    example_complete_workflow()
    example_tva_rates()
    example_edge_cases()

    print("=" * 60)
    print("Fin des exemples")
    print("=" * 60)
