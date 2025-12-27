"""Exemples d'utilisation du module inventory_utils.

Ce script démontre l'utilisation pratique de toutes les fonctions
pour gérer un produit fictif dans un système d'inventaire.
"""

from decimal import Decimal
from calculation.inventory_utils import (
    calculate_pamp,
    calculate_eoq,
    calculate_safety_stock,
    calculate_reorder_point,
    calculate_margin
)


def exemple_complet():
    """Exemple complet de gestion d'inventaire pour un produit."""

    print("=" * 70)
    print("GESTION D'INVENTAIRE - Exemple complet")
    print("Produit: Huile d'olive 1L")
    print("=" * 70)
    print()

    # =========================================================================
    # ÉTAPE 1: Calculer le PAMP (Prix d'Achat Moyen Pondéré)
    # =========================================================================
    print("ÉTAPE 1: Calcul du PAMP")
    print("-" * 70)

    historique_achats = [
        {'quantity': 100, 'unit_price': 8.50},   # 1er achat
        {'quantity': 150, 'unit_price': 8.20},   # 2e achat (promo)
        {'quantity': 200, 'unit_price': 8.40},   # 3e achat
        {'quantity': 120, 'unit_price': 8.60},   # 4e achat
    ]

    print("Historique des achats:")
    for i, achat in enumerate(historique_achats, 1):
        print(f"  Achat {i}: {achat['quantity']} unités à {achat['unit_price']}€")

    pamp = calculate_pamp(historique_achats)
    quantite_totale = sum(a['quantity'] for a in historique_achats)

    print(f"\nQuantité totale achetée: {quantite_totale} unités")
    print(f"PAMP calculé: {pamp}€ par unité")
    print(f"Valeur du stock: {pamp * quantite_totale}€")
    print()

    # =========================================================================
    # ÉTAPE 2: Déterminer la quantité économique de commande (EOQ)
    # =========================================================================
    print("ÉTAPE 2: Quantité Économique de Commande (EOQ)")
    print("-" * 70)

    # Données annuelles
    ventes_quotidiennes = 15  # 15 bouteilles/jour en moyenne
    demande_annuelle = ventes_quotidiennes * 365
    cout_commande = 85  # Coûts fixes par commande (transport, admin)
    taux_possession = 0.25  # 25% du coût unitaire (stockage, assurance)
    cout_possession = float(pamp) * taux_possession

    print(f"Demande annuelle: {demande_annuelle} unités ({ventes_quotidiennes}/jour)")
    print(f"Coût par commande: {cout_commande}€")
    print(f"Coût de possession: {cout_possession:.2f}€/unité/an ({taux_possession*100}% du PAMP)")

    eoq = calculate_eoq(
        annual_demand=demande_annuelle,
        order_cost=cout_commande,
        holding_cost=cout_possession
    )

    nombre_commandes = demande_annuelle / eoq
    intervalle_jours = 365 / nombre_commandes

    print(f"\nEOQ: {eoq} unités")
    print(f"Nombre de commandes par an: {nombre_commandes:.1f}")
    print(f"Fréquence de commande: tous les {intervalle_jours:.0f} jours")
    print()

    # =========================================================================
    # ÉTAPE 3: Calculer le stock de sécurité
    # =========================================================================
    print("ÉTAPE 3: Stock de Sécurité")
    print("-" * 70)

    demande_moyenne = 15  # unités/jour
    ecart_type_demande = 4  # variation de la demande
    delai_livraison = 7  # 1 semaine
    niveau_service = 0.95  # 95% de satisfaction

    print(f"Demande moyenne: {demande_moyenne} unités/jour")
    print(f"Écart-type demande: {ecart_type_demande} unités")
    print(f"Délai de livraison: {delai_livraison} jours")
    print(f"Niveau de service cible: {niveau_service*100}%")

    stock_securite = calculate_safety_stock(
        avg_demand=demande_moyenne,
        demand_std=ecart_type_demande,
        lead_time=delai_livraison,
        service_level=niveau_service
    )

    valeur_stock_securite = stock_securite * float(pamp)
    jours_couverture = stock_securite / demande_moyenne

    print(f"\nStock de sécurité: {stock_securite} unités")
    print(f"Valeur immobilisée: {valeur_stock_securite:.2f}€")
    print(f"Couverture: {jours_couverture:.1f} jours de vente")
    print()

    # =========================================================================
    # ÉTAPE 4: Définir le point de réapprovisionnement
    # =========================================================================
    print("ÉTAPE 4: Point de Réapprovisionnement")
    print("-" * 70)

    point_reappro = calculate_reorder_point(
        avg_demand=demande_moyenne,
        lead_time=delai_livraison,
        safety_stock=stock_securite
    )

    demande_durant_livraison = demande_moyenne * delai_livraison

    print(f"Demande pendant lead time: {demande_durant_livraison} unités")
    print(f"Stock de sécurité: {stock_securite} unités")
    print(f"\nPoint de réapprovisionnement: {point_reappro} unités")
    print(f"\n⚠️  ALERTE: Commander {eoq} unités quand stock ≤ {point_reappro}")
    print()

    # =========================================================================
    # ÉTAPE 5: Analyser la marge
    # =========================================================================
    print("ÉTAPE 5: Analyse de Marge")
    print("-" * 70)

    prix_vente = Decimal('12.90')  # Prix de vente HT

    print(f"Prix de vente HT: {prix_vente}€")
    print(f"Coût d'achat (PAMP): {pamp}€")

    marge = calculate_margin(revenue=prix_vente, cost=pamp)

    print(f"\nMarge brute: {marge['margin_amount']}€ par unité")
    print(f"Taux de marge: {marge['margin_percent']}%")

    # Calculs additionnels
    marge_commande_eoq = float(marge['margin_amount']) * eoq
    marge_annuelle = float(marge['margin_amount']) * demande_annuelle

    print(f"\nMarge par commande EOQ: {marge_commande_eoq:.2f}€")
    print(f"Marge annuelle estimée: {marge_annuelle:.2f}€")
    print()

    # =========================================================================
    # RÉCAPITULATIF
    # =========================================================================
    print("=" * 70)
    print("RÉCAPITULATIF DES PARAMÈTRES OPTIMAUX")
    print("=" * 70)
    print(f"Coût unitaire (PAMP):           {pamp}€")
    print(f"Prix de vente:                  {prix_vente}€")
    print(f"Marge unitaire:                 {marge['margin_amount']}€ ({marge['margin_percent']}%)")
    print()
    print(f"Quantité à commander (EOQ):     {eoq} unités")
    print(f"Fréquence de commande:          Tous les {intervalle_jours:.0f} jours")
    print(f"Point de réapprovisionnement:   {point_reappro} unités")
    print(f"Stock de sécurité:              {stock_securite} unités")
    print()
    print(f"Valeur stock de sécurité:       {valeur_stock_securite:.2f}€")
    print(f"Marge annuelle estimée:         {marge_annuelle:.2f}€")
    print("=" * 70)


def exemple_scenarios():
    """Exemples de différents scénarios d'inventaire."""

    print("\n\n")
    print("=" * 70)
    print("COMPARAISON DE SCÉNARIOS")
    print("=" * 70)
    print()

    scenarios = [
        {
            "nom": "Produit à rotation rapide",
            "avg_demand": 100,
            "demand_std": 15,
            "lead_time": 3,
            "service_level": 0.99
        },
        {
            "nom": "Produit standard",
            "avg_demand": 20,
            "demand_std": 5,
            "lead_time": 7,
            "service_level": 0.95
        },
        {
            "nom": "Produit à rotation lente",
            "avg_demand": 5,
            "demand_std": 2,
            "lead_time": 14,
            "service_level": 0.90
        }
    ]

    print(f"{'Scénario':<30} {'Stock Sécurité':<20} {'Point Reappro':<20}")
    print("-" * 70)

    for scenario in scenarios:
        ss = calculate_safety_stock(
            avg_demand=scenario['avg_demand'],
            demand_std=scenario['demand_std'],
            lead_time=scenario['lead_time'],
            service_level=scenario['service_level']
        )

        rop = calculate_reorder_point(
            avg_demand=scenario['avg_demand'],
            lead_time=scenario['lead_time'],
            safety_stock=ss
        )

        print(f"{scenario['nom']:<30} {ss:<20.0f} {rop:<20.0f}")

    print()


def exemple_marges_multiples():
    """Calcul de marges pour plusieurs produits."""

    print("\n\n")
    print("=" * 70)
    print("ANALYSE DE MARGES - PLUSIEURS PRODUITS")
    print("=" * 70)
    print()

    produits = [
        {"nom": "Huile d'olive", "vente": 12.90, "achat": 8.40},
        {"nom": "Pâtes", "vente": 2.50, "achat": 1.20},
        {"nom": "Sauce tomate", "vente": 3.80, "achat": 2.10},
        {"nom": "Fromage", "vente": 15.50, "achat": 11.00},
    ]

    print(f"{'Produit':<20} {'Prix Vente':<15} {'Coût':<15} {'Marge €':<15} {'Marge %':<15}")
    print("-" * 70)

    for produit in produits:
        marge = calculate_margin(
            revenue=Decimal(str(produit['vente'])),
            cost=Decimal(str(produit['achat']))
        )

        print(f"{produit['nom']:<20} "
              f"{produit['vente']:<15.2f} "
              f"{produit['achat']:<15.2f} "
              f"{float(marge['margin_amount']):<15.2f} "
              f"{float(marge['margin_percent']):<15.2f}")

    print()


if __name__ == "__main__":
    # Exécuter tous les exemples
    exemple_complet()
    exemple_scenarios()
    exemple_marges_multiples()

    print("\n✓ Tous les exemples ont été exécutés avec succès!")
