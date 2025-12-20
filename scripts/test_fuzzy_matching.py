#!/usr/bin/env python3
"""
Script de test pour le fuzzy matching de produits.

Usage:
    python scripts/test_fuzzy_matching.py

Ce script teste la fonctionnalité de fuzzy matching en recherchant
des produits similaires dans le catalogue.
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
