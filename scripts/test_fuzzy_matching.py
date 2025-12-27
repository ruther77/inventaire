#!/usr/bin/env python3
"""
Module de test et démonstration du système de fuzzy matching de produits.

Ce script permet de:
- Tester la fonction de recherche floue (fuzzy matching) du catalogue
- Vérifier la qualité des suggestions de produits similaires
- Évaluer les scores de pertinence
- Tester différents cas d'usage (fautes d'orthographe, ordre des mots, etc.)
- Afficher les résultats de manière formatée avec émojis et couleurs

Le fuzzy matching est crucial pour:
- Associer automatiquement les factures aux produits du catalogue
- Aider les utilisateurs à trouver des produits malgré les variations d'orthographe
- Gérer les différences de nommage entre fournisseurs
- Supporter la recherche intelligente dans l'interface

Usage:
    # Test complet avec exemples prédéfinis
    python scripts/test_fuzzy_matching.py

Prérequis:
    - Base de données avec table produits remplie
    - Module backend.services.product_matching configuré
    - Tenant ID 1 actif avec des produits

Tests effectués:
    1. Recherche simple (mot unique): "Tomate"
    2. Faute d'orthographe: "Lait demi écréme"
    3. Produit avec détails: "Pomme Golden 1kg"
    4. Ordre inversé: "UHT Lait"
    5. Produit inexistant: "Produit inexistant XYZ123"
    6. Meilleur match unique avec seuil élevé

Scoring:
    - Score >= 90%: Excellent match (émoji vert)
    - Score >= 75%: Bon match (émoji jaune)
    - Score >= 60%: Match acceptable (émoji orange)
    - Score < 60%: Match faible (émoji rouge)

Exemple de sortie:
    TEST DU FUZZY MATCHING DE PRODUITS
    ==================================================================

    Test avec un mot simple
    ==================================================================
    Recherche: 'Tomate'
    ==================================================================
    3 suggestion(s) trouvée(s):

    1. TOMATE RONDE
       Score: 95%
       ID: 42
       Catégorie: Légumes
       Prix achat: 2.50€
       Prix vente: 3.50€

    2. TOMATE CERISE 500G
       Score: 78%
       ID: 89
       EAN: 3245678901234

Notes:
    - Le script est autonome et peut être exécuté sans arguments
    - Les scores sont calculés via l'algorithme de Levenshtein
    - Les résultats incluent les métadonnées (catégorie, prix, EAN)
    - Utile pour diagnostiquer les problèmes de matching
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.services import product_matching


def print_suggestions(query: str, suggestions: list):
    """Affiche les suggestions de manière formatée."""
    print(f"\n{'='*80}")
    print(f"Recherche: '{query}'")
    print(f"{'='*80}")

    if not suggestions:
        print("❌ Aucune suggestion trouvée")
        return

    print(f"✅ {len(suggestions)} suggestion(s) trouvée(s):\n")

    for i, suggestion in enumerate(suggestions, 1):
        score = suggestion.get("score", 0)

        # Emoji selon le score
        if score >= 90:
            emoji = "🟢"
        elif score >= 75:
            emoji = "🟡"
        elif score >= 60:
            emoji = "🟠"
        else:
            emoji = "🔴"

        print(f"{emoji} {i}. {suggestion['produit_nom']}")
        print(f"   Score: {score}%")
        print(f"   ID: {suggestion['produit_id']}")

        if suggestion.get('categorie'):
            print(f"   Catégorie: {suggestion['categorie']}")

        if suggestion.get('barcode'):
            print(f"   EAN: {suggestion['barcode']}")

        if suggestion.get('prix_achat', 0) > 0:
            print(f"   Prix achat: {suggestion['prix_achat']:.2f} €")

        if suggestion.get('prix_vente', 0) > 0:
            print(f"   Prix vente: {suggestion['prix_vente']:.2f} €")

        print()


def test_fuzzy_matching():
    """Test la fonctionnalité de fuzzy matching avec différents exemples."""

    print("\n" + "="*80)
    print("TEST DU FUZZY MATCHING DE PRODUITS")
    print("="*80)

    # Exemples de requêtes de test
    test_queries = [
        ("Tomate", "Test avec un mot simple"),
        ("Lait demi écréme", "Test avec faute d'orthographe"),
        ("Pomme Golden 1kg", "Test avec détails"),
        ("UHT Lait", "Test avec ordre des mots inversé"),
        ("Produit inexistant XYZ123", "Test avec produit qui n'existe pas"),
    ]

    tenant_id = 1  # Utiliser le tenant par défaut

    for query, description in test_queries:
        print(f"\n📝 {description}")

        try:
            suggestions = product_matching.get_fuzzy_product_matches(
                query,
                tenant_id=tenant_id,
                max_results=3,
                min_score=50.0,  # Score minimum bas pour voir plus de résultats
            )

            print_suggestions(query, suggestions)

        except Exception as e:
            print(f"❌ Erreur lors de la recherche: {e}")
            import traceback
            traceback.print_exc()

    # Test de meilleur match unique
    print(f"\n{'='*80}")
    print("TEST DU MEILLEUR MATCH UNIQUE")
    print(f"{'='*80}")

    test_query = "Tomate"
    print(f"\nRecherche du meilleur match pour: '{test_query}'")

    try:
        best = product_matching.get_best_product_match(
            test_query,
            tenant_id=tenant_id,
            min_score=75.0,  # Score minimum élevé pour auto-matching
        )

        if best:
            print(f"✅ Meilleur match trouvé:")
            print(f"   Produit: {best['produit_nom']}")
            print(f"   Score: {best['score']}%")
            print(f"   ID: {best['produit_id']}")
        else:
            print(f"❌ Aucun match avec score ≥75% trouvé")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'='*80}")
    print("FIN DES TESTS")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    test_fuzzy_matching()
