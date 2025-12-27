#!/usr/bin/env python3
"""Démonstration rapide du module analysis.classification.

Usage:
    python3 demo.py
    ou (depuis le dossier python):
    PYTHONPATH=. python3 analysis/demo.py
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path si nécessaire
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from analysis import (
    calculate_coefficient_variation,
    classify_abc,
    classify_abc_xyz,
    classify_xyz,
)


def main():
    print("\n" + "=" * 70)
    print("DÉMONSTRATION MODULE ANALYSIS - CLASSIFICATION ABC/XYZ")
    print("=" * 70)

    # Données d'exemple: inventaire d'une quincaillerie
    inventaire = [
        # Produits A (haute valeur)
        {'sku': 'VIS-M8-40', 'nom': 'Vis M8x40mm', 'valeur_annuelle': 15000, 'cv': 0.15},
        {'sku': 'BOU-M10', 'nom': 'Boulon M10', 'valeur_annuelle': 12000, 'cv': 0.60},
        {'sku': 'RON-M8', 'nom': 'Rondelle M8', 'valeur_annuelle': 8000, 'cv': 1.20},

        # Produits B (valeur moyenne)
        {'sku': 'ECR-M10', 'nom': 'Ecrou M10', 'valeur_annuelle': 5000, 'cv': 0.25},
        {'sku': 'VIS-M6-30', 'nom': 'Vis M6x30mm', 'valeur_annuelle': 3000, 'cv': 0.70},
        {'sku': 'RON-M6', 'nom': 'Rondelle M6', 'valeur_annuelle': 2000, 'cv': 1.30},

        # Produits C (faible valeur)
        {'sku': 'GOU-5MM', 'nom': 'Goupille 5mm', 'valeur_annuelle': 1500, 'cv': 0.30},
        {'sku': 'CIR-8MM', 'nom': 'Circlips 8mm', 'valeur_annuelle': 800, 'cv': 0.80},
        {'sku': 'RIV-4MM', 'nom': 'Rivet 4mm', 'valeur_annuelle': 500, 'cv': 1.50},
        {'sku': 'CAV-6MM', 'nom': 'Cavalier 6mm', 'valeur_annuelle': 200, 'cv': 2.00},
    ]

    # Classification ABC-XYZ combinée
    print("\n1. CLASSIFICATION ABC-XYZ COMBINÉE")
    print("-" * 70)

    result = classify_abc_xyz(
        inventaire,
        value_key='valeur_annuelle',
        cv_key='cv'
    )

    # Afficher les résultats par catégorie avec recommandations
    categories_prioritaires = ['AX', 'AY', 'AZ', 'BX', 'BY', 'BZ']
    categories_secondaires = ['CX', 'CY', 'CZ']

    print("\nCATÉGORIES PRIORITAIRES (A-B):")
    for cat in categories_prioritaires:
        items = result[cat]
        if items:
            print(f"\n  {cat}:")
            for item in items:
                print(f"    • {item['sku']}: {item['nom']}")
                print(f"      Valeur: {item['valeur_annuelle']:>6,.0f} EUR | "
                      f"CV: {item['cv']:>4.2f} | "
                      f"Part: {item['share']*100:>4.1f}%")

    print("\nCATÉGORIES SECONDAIRES (C):")
    for cat in categories_secondaires:
        items = result[cat]
        if items:
            skus = [item['sku'] for item in items]
            print(f"  {cat}: {', '.join(skus)}")

    # Statistiques globales
    print("\n" + "-" * 70)
    print("2. STATISTIQUES GLOBALES")
    print("-" * 70)

    total_valeur = sum(item['valeur_annuelle'] for item in inventaire)
    print(f"\nValeur totale: {total_valeur:,.0f} EUR")

    # Distribution par classe ABC
    valeur_a = sum(item['valeur_annuelle'] for cat in ['AX', 'AY', 'AZ'] for item in result[cat])
    valeur_b = sum(item['valeur_annuelle'] for cat in ['BX', 'BY', 'BZ'] for item in result[cat])
    valeur_c = sum(item['valeur_annuelle'] for cat in ['CX', 'CY', 'CZ'] for item in result[cat])

    print(f"\nClasse A: {valeur_a:>8,.0f} EUR ({valeur_a/total_valeur*100:>5.1f}%)")
    print(f"Classe B: {valeur_b:>8,.0f} EUR ({valeur_b/total_valeur*100:>5.1f}%)")
    print(f"Classe C: {valeur_c:>8,.0f} EUR ({valeur_c/total_valeur*100:>5.1f}%)")

    # Distribution par classe XYZ
    count_x = sum(len(result[cat]) for cat in ['AX', 'BX', 'CX'])
    count_y = sum(len(result[cat]) for cat in ['AY', 'BY', 'CY'])
    count_z = sum(len(result[cat]) for cat in ['AZ', 'BZ', 'CZ'])

    print(f"\nClasse X (stable):        {count_x:>2} produits")
    print(f"Classe Y (variable):      {count_y:>2} produits")
    print(f"Classe Z (très variable): {count_z:>2} produits")

    # Recommandations
    print("\n" + "-" * 70)
    print("3. RECOMMANDATIONS DE GESTION")
    print("-" * 70)

    recommandations = {
        'AX': '📊 Critique-Stable: Stock sécurisé, réappro. automatique',
        'AY': '⚡ Critique-Variable: Surveillance hebdo, prévisions',
        'AZ': '🔥 Critique-Erratique: Analyse détaillée, relation fournisseur',
        'BX': '✓ Moyen-Stable: Gestion standard',
        'BY': '~ Moyen-Variable: Revue mensuelle',
        'BZ': '! Moyen-Erratique: Gestion réactive',
        'CX': '- Faible-Stable: Stock minimal',
        'CY': '? Faible-Variable: Sur commande',
        'CZ': '× Faible-Erratique: Pas de stock',
    }

    for cat, items in result.items():
        if items:
            print(f"\n{recommandations[cat]}")
            for item in items:
                print(f"  → {item['sku']}: {item['nom']}")

    # Exemple de calcul de CV
    print("\n" + "-" * 70)
    print("4. EXEMPLE DE CALCUL DU COEFFICIENT DE VARIATION")
    print("-" * 70)

    demandes_exemple = {
        'Stable': [100, 102, 98, 101, 99, 100, 103],
        'Variable': [80, 120, 90, 150, 70, 110, 100],
        'Erratique': [50, 200, 30, 180, 60, 150, 40],
    }

    print("\nComparaison de profils de demande:")
    for profil, demandes in demandes_exemple.items():
        cv = calculate_coefficient_variation(demandes)
        moyenne = sum(demandes) / len(demandes)
        print(f"\n  {profil:12s}: {demandes}")
        print(f"  {'':12s}  Moyenne = {moyenne:>6.1f}, CV = {cv:>5.3f}")

        if cv < 0.5:
            classe = 'X (Stable)'
        elif cv < 1.0:
            classe = 'Y (Variable)'
        else:
            classe = 'Z (Erratique)'
        print(f"  {'':12s}  → Classe {classe}")

    print("\n" + "=" * 70)
    print("FIN DE LA DÉMONSTRATION")
    print("=" * 70)
    print("\nPour plus d'exemples, consultez:")
    print("  - analysis/example_usage.py : Exemples détaillés")
    print("  - analysis/README.md        : Documentation complète")
    print("  - analysis/TECHNICAL.md     : Documentation technique")
    print()


if __name__ == '__main__':
    main()
