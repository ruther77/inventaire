"""Exemples d'utilisation du module analysis.classification.

Ce fichier démontre comment utiliser les différentes fonctions de
classification ABC/XYZ pour l'analyse d'inventaire.
"""

from analysis.classification import (
    calculate_coefficient_variation,
    classify_abc,
    classify_abc_xyz,
    classify_xyz,
)


def example_coefficient_variation():
    """Exemple de calcul du coefficient de variation."""
    print("=" * 60)
    print("EXEMPLE 1: Calcul du Coefficient de Variation")
    print("=" * 60)

    # Demande stable
    demande_stable = [100, 105, 98, 102, 100, 103, 99]
    cv_stable = calculate_coefficient_variation(demande_stable)
    print(f"\nDemande stable: {demande_stable}")
    print(f"CV = {cv_stable:.4f} (faible variabilité)")

    # Demande variable
    demande_variable = [50, 120, 80, 200, 60, 150, 90]
    cv_variable = calculate_coefficient_variation(demande_variable)
    print(f"\nDemande variable: {demande_variable}")
    print(f"CV = {cv_variable:.4f} (haute variabilité)")

    # Demande nulle
    demande_nulle = [0, 0, 0, 0]
    cv_nulle = calculate_coefficient_variation(demande_nulle)
    print(f"\nDemande nulle: {demande_nulle}")
    print(f"CV = {cv_nulle} (indéfini)")


def example_abc_classification():
    """Exemple de classification ABC."""
    print("\n" + "=" * 60)
    print("EXEMPLE 2: Classification ABC (Pareto)")
    print("=" * 60)

    # Catalogue de produits avec leur valeur de consommation annuelle
    produits = [
        {'sku': 'PROD-001', 'nom': 'Vis M8x40', 'value': 15000},
        {'sku': 'PROD-002', 'nom': 'Boulon M10', 'value': 12000},
        {'sku': 'PROD-003', 'nom': 'Rondelle M8', 'value': 8000},
        {'sku': 'PROD-004', 'nom': 'Ecrou M10', 'value': 5000},
        {'sku': 'PROD-005', 'nom': 'Vis M6x30', 'value': 3000},
        {'sku': 'PROD-006', 'nom': 'Rondelle M6', 'value': 2000},
        {'sku': 'PROD-007', 'nom': 'Goupille 5mm', 'value': 1500},
        {'sku': 'PROD-008', 'nom': 'Circlips 8mm', 'value': 800},
        {'sku': 'PROD-009', 'nom': 'Rivet 4mm', 'value': 500},
        {'sku': 'PROD-010', 'nom': 'Cavalier 6mm', 'value': 200},
    ]

    result = classify_abc(produits, value_key='value')

    print("\nClassification ABC des produits:")
    print(f"Total de produits: {len(produits)}")

    for classe in ['A', 'B', 'C']:
        items = result[classe]
        total_value = sum(item['value'] for item in items)
        print(f"\nClasse {classe}: {len(items)} produits")
        print(f"  Valeur totale: {total_value:,.0f} EUR")

        if items:
            cumul_pct = items[-1]['cumul'] * 100
            print(f"  Contribution cumulative: {cumul_pct:.1f}%")
            print(f"  Produits:")
            for item in items:
                print(f"    - {item['sku']}: {item['nom']} "
                      f"({item['value']:,.0f} EUR, {item['share']*100:.1f}%)")


def example_xyz_classification():
    """Exemple de classification XYZ."""
    print("\n" + "=" * 60)
    print("EXEMPLE 3: Classification XYZ (Variabilité)")
    print("=" * 60)

    # Produits avec leur coefficient de variation
    produits = [
        {'sku': 'PROD-001', 'nom': 'Vis M8x40', 'cv': 0.15},      # Stable
        {'sku': 'PROD-002', 'nom': 'Boulon M10', 'cv': 0.25},     # Stable
        {'sku': 'PROD-003', 'nom': 'Rondelle M8', 'cv': 0.60},    # Variable
        {'sku': 'PROD-004', 'nom': 'Ecrou M10', 'cv': 0.80},      # Variable
        {'sku': 'PROD-005', 'nom': 'Vis M6x30', 'cv': 1.20},      # Très variable
        {'sku': 'PROD-006', 'nom': 'Rondelle M6', 'cv': 1.50},    # Très variable
        {'sku': 'PROD-007', 'nom': 'Goupille 5mm', 'cv': None},   # Pas de demande
    ]

    result = classify_xyz(produits, cv_key='cv')

    print("\nClassification XYZ des produits:")

    for classe in ['X', 'Y', 'Z']:
        items = result[classe]
        print(f"\nClasse {classe}: {len(items)} produits")

        if classe == 'X':
            print("  (Demande stable, CV < 0.5)")
        elif classe == 'Y':
            print("  (Demande variable, 0.5 <= CV < 1.0)")
        else:
            print("  (Demande très variable, CV >= 1.0)")

        for item in items:
            cv_str = f"{item['cv']:.2f}" if item['cv'] is not None else "N/A"
            print(f"    - {item['sku']}: {item['nom']} (CV={cv_str})")


def example_abc_xyz_classification():
    """Exemple de classification ABC-XYZ combinée."""
    print("\n" + "=" * 60)
    print("EXEMPLE 4: Classification ABC-XYZ Combinée")
    print("=" * 60)

    # Produits avec valeur et coefficient de variation
    produits = [
        # Produits de haute valeur
        {'sku': 'PROD-001', 'nom': 'Vis M8x40', 'value': 15000, 'cv': 0.15},
        {'sku': 'PROD-002', 'nom': 'Boulon M10', 'value': 12000, 'cv': 0.60},
        {'sku': 'PROD-003', 'nom': 'Rondelle M8', 'value': 8000, 'cv': 1.20},
        # Produits de valeur moyenne
        {'sku': 'PROD-004', 'nom': 'Ecrou M10', 'value': 5000, 'cv': 0.25},
        {'sku': 'PROD-005', 'nom': 'Vis M6x30', 'value': 3000, 'cv': 0.70},
        {'sku': 'PROD-006', 'nom': 'Rondelle M6', 'value': 2000, 'cv': 1.30},
        # Produits de faible valeur
        {'sku': 'PROD-007', 'nom': 'Goupille 5mm', 'value': 1500, 'cv': 0.30},
        {'sku': 'PROD-008', 'nom': 'Circlips 8mm', 'value': 800, 'cv': 0.80},
        {'sku': 'PROD-009', 'nom': 'Rivet 4mm', 'value': 500, 'cv': 1.50},
    ]

    result = classify_abc_xyz(produits, value_key='value', cv_key='cv')

    print("\nMatrice ABC-XYZ:")
    print("\nRecommandations de gestion par catégorie:")

    # Matrice de recommandations
    recommandations = {
        'AX': 'CRITIQUE-STABLE: Gestion simple, stock de sécurité important',
        'AY': 'CRITIQUE-VARIABLE: Surveillance régulière, prévisions',
        'AZ': 'CRITIQUE-ERRATIQUE: Analyse détaillée, gestion au cas par cas',
        'BX': 'MOYEN-STABLE: Gestion standard, réapprovisionnement régulier',
        'BY': 'MOYEN-VARIABLE: Revue périodique, ajustements fréquents',
        'BZ': 'MOYEN-ERRATIQUE: Gestion réactive, stock minimal',
        'CX': 'FAIBLE-STABLE: Stock minimum, commandes espacées',
        'CY': 'FAIBLE-VARIABLE: Approvisionnement sur demande',
        'CZ': 'FAIBLE-ERRATIQUE: Stock minimal ou sur commande uniquement',
    }

    for abc in ['A', 'B', 'C']:
        print(f"\n--- Catégorie {abc} ---")
        for xyz in ['X', 'Y', 'Z']:
            classe = f"{abc}{xyz}"
            items = result[classe]

            if items:
                print(f"\n  {classe}: {len(items)} produit(s)")
                print(f"  {recommandations[classe]}")
                for item in items:
                    print(f"    - {item['sku']}: {item['nom']}")
                    print(f"      Valeur: {item['value']:,.0f} EUR, "
                          f"CV: {item['cv']:.2f}, "
                          f"Part: {item['share']*100:.1f}%")


def example_complete_workflow():
    """Exemple de workflow complet d'analyse."""
    print("\n" + "=" * 60)
    print("EXEMPLE 5: Workflow Complet d'Analyse")
    print("=" * 60)

    # 1. Données brutes de demande
    print("\nÉtape 1: Calculer les CV à partir des demandes historiques")

    demandes_historiques = {
        'PROD-001': [100, 105, 98, 102, 100],
        'PROD-002': [50, 150, 80, 120, 100],
        'PROD-003': [200, 250, 180, 220, 210],
    }

    produits = []
    for sku, demandes in demandes_historiques.items():
        cv = calculate_coefficient_variation(demandes)
        valeur = sum(demandes) * 10  # Prix unitaire fictif de 10 EUR
        produits.append({
            'sku': sku,
            'value': valeur,
            'cv': cv,
            'demande_moyenne': sum(demandes) / len(demandes)
        })
        print(f"  {sku}: CV = {cv:.3f}, Valeur = {valeur} EUR")

    # 2. Classification combinée
    print("\nÉtape 2: Classification ABC-XYZ")
    result = classify_abc_xyz(produits, value_key='value', cv_key='cv')

    # 3. Analyse et recommandations
    print("\nÉtape 3: Recommandations d'action")
    for classe, items in result.items():
        if items:
            print(f"\n  Catégorie {classe}:")
            for item in items:
                print(f"    {item['sku']}: "
                      f"Demande moy. = {item['demande_moyenne']:.0f}, "
                      f"CV = {item['cv']:.3f}")


if __name__ == '__main__':
    # Exécuter tous les exemples
    example_coefficient_variation()
    example_abc_classification()
    example_xyz_classification()
    example_abc_xyz_classification()
    example_complete_workflow()

    print("\n" + "=" * 60)
    print("Fin des exemples")
    print("=" * 60)
