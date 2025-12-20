"""Tests pour le système de feedback de catégorisation."""

import pytest
from datetime import date
from decimal import Decimal

from core.bank_import.categorizer import (
    TransactionCategorizer,
    record_categorization_feedback,
    get_feedback_stats,
    get_common_corrections,
)
from core.bank_import.models import ParsedTransaction, TransactionDirection


class TestTransactionCategorizer:
    """Tests pour le categorizer de base."""

    def test_categorize_restaurant_keyword(self):
        """Test catégorisation avec keyword 'restaurant'."""
        txn = ParsedTransaction(
            date_operation=date(2025, 1, 15),
            date_valeur=date(2025, 1, 15),
            libelle="RESTAURANT LE PARIS",
            montant=Decimal("45.80"),
            direction=TransactionDirection.OUT,
        )

        categorizer = TransactionCategorizer()
        result = categorizer.categorize(txn)

        # Devrait être catégorisé comme "repas" ou "alimentation"
        assert result.category_code in ["repas", "alimentation", "restaurant"]
        assert result.confidence > 0.7
        assert result.matched_keyword is not None

    def test_categorize_virement_keyword(self):
        """Test catégorisation avec keyword 'virement'."""
        txn = ParsedTransaction(
            date_operation=date(2025, 1, 15),
            date_valeur=date(2025, 1, 15),
            libelle="VIREMENT SALAIRE",
            montant=Decimal("2500.00"),
            direction=TransactionDirection.IN,
        )

        categorizer = TransactionCategorizer()
        result = categorizer.categorize(txn)

        # Devrait être catégorisé comme "virement" ou "salaire"
        assert result.category_code in ["virement", "salaire", "revenu"]
        assert result.confidence > 0.7

    def test_categorize_unknown_fallback(self):
        """Test fallback pour transaction inconnue."""
        txn = ParsedTransaction(
            date_operation=date(2025, 1, 15),
            date_valeur=date(2025, 1, 15),
            libelle="XYZABC123456",
            montant=Decimal("100.00"),
            direction=TransactionDirection.OUT,
        )

        categorizer = TransactionCategorizer()
        result = categorizer.categorize(txn)

        # Devrait tomber dans "à_categoriser"
        assert result.category_code == "a_categoriser"
        assert result.confidence == 0.0
        assert result.matched_keyword is None

    def test_categorize_with_confidence_levels(self):
        """Test que la confiance varie selon le type de match."""
        categorizer = TransactionCategorizer()

        # Exact match (devrait avoir confiance maximale)
        txn_exact = ParsedTransaction(
            date_operation=date(2025, 1, 15),
            date_valeur=date(2025, 1, 15),
            libelle="RESTAURANT",
            montant=Decimal("50.00"),
            direction=TransactionDirection.OUT,
        )
        result_exact = categorizer.categorize(txn_exact)

        # Substring match (devrait avoir confiance moyenne)
        txn_substring = ParsedTransaction(
            date_operation=date(2025, 1, 15),
            date_valeur=date(2025, 1, 15),
            libelle="PAIEMENT RESTAURANTS PARIS",
            montant=Decimal("50.00"),
            direction=TransactionDirection.OUT,
        )
        result_substring = categorizer.categorize(txn_substring)

        # Le match exact devrait avoir une confiance >= au substring
        assert result_exact.confidence >= result_substring.confidence


class TestCategorizationFeedback:
    """Tests pour le système de feedback."""

    @pytest.mark.skip(reason="Requires database connection")
    def test_record_feedback(self):
        """Test enregistrement d'un feedback."""
        # Note: Ce test nécessite une connexion DB
        # Il est skippé par défaut mais sert d'exemple

        feedback_id = record_categorization_feedback(
            transaction_id=12345,
            predicted_category_id=5,  # Alimentation
            actual_category_id=8,     # Fournitures
            confidence_score=0.75,
            user_id=1,
            correction_source="manual"
        )

        assert feedback_id > 0

    @pytest.mark.skip(reason="Requires database connection")
    def test_get_feedback_stats(self):
        """Test récupération des stats de feedback."""
        stats = get_feedback_stats()

        # Vérifier la structure
        assert "total_corrections" in stats
        assert "unique_transactions" in stats
        assert "avg_wrong_confidence" in stats
        assert "manual_corrections" in stats

        # Les valeurs doivent être >= 0
        assert stats["total_corrections"] >= 0
        assert stats["unique_transactions"] >= 0

    @pytest.mark.skip(reason="Requires database connection")
    def test_get_common_corrections(self):
        """Test récupération des corrections communes."""
        corrections = get_common_corrections(limit=10)

        # Devrait retourner une liste
        assert isinstance(corrections, list)

        # Si des corrections existent, vérifier la structure
        if len(corrections) > 0:
            correction = corrections[0]
            assert "predicted_code" in correction
            assert "actual_code" in correction
            assert "correction_count" in correction
            assert "avg_confidence" in correction


class TestCategorizerWithDBRules:
    """Tests pour le categorizer avec règles DB."""

    @pytest.mark.skip(reason="Requires database connection")
    def test_db_rules_have_priority(self):
        """Test que les règles DB ont la priorité sur les keywords."""
        # Créer un categorizer qui charge les règles DB
        categorizer = TransactionCategorizer(load_db_rules=True)

        # Transaction qui pourrait matcher plusieurs keywords
        txn = ParsedTransaction(
            date_operation=date(2025, 1, 15),
            date_valeur=date(2025, 1, 15),
            libelle="RESTAURANT LIVRAISON UBER EATS",
            montant=Decimal("35.00"),
            direction=TransactionDirection.OUT,
        )

        result = categorizer.categorize(txn)

        # Si une règle DB matche, elle devrait avoir confiance 0.98
        if result.rule_id is not None:
            assert result.confidence == 0.98


class TestBatchCategorization:
    """Tests pour la catégorisation en batch."""

    def test_categorize_batch(self):
        """Test catégorisation de plusieurs transactions."""
        transactions = [
            ParsedTransaction(
                date_operation=date(2025, 1, 15),
                date_valeur=date(2025, 1, 15),
                libelle="RESTAURANT LE PARIS",
                montant=Decimal("45.80"),
                direction=TransactionDirection.OUT,
            ),
            ParsedTransaction(
                date_operation=date(2025, 1, 16),
                date_valeur=date(2025, 1, 16),
                libelle="VIREMENT SALAIRE",
                montant=Decimal("2500.00"),
                direction=TransactionDirection.IN,
            ),
            ParsedTransaction(
                date_operation=date(2025, 1, 17),
                date_valeur=date(2025, 1, 17),
                libelle="UNKNOWN XYZABC",
                montant=Decimal("100.00"),
                direction=TransactionDirection.OUT,
            ),
        ]

        categorizer = TransactionCategorizer()
        results = categorizer.categorize_batch(transactions)

        # Vérifier qu'on a le bon nombre de résultats
        assert len(results) == len(transactions)

        # Vérifier que les résultats sont cohérents
        assert results[0].category_code != "a_categoriser"  # Restaurant
        assert results[1].category_code != "a_categoriser"  # Virement
        assert results[2].category_code == "a_categoriser"  # Unknown

    def test_apply_categories(self):
        """Test application des catégories sur les transactions."""
        transactions = [
            ParsedTransaction(
                date_operation=date(2025, 1, 15),
                date_valeur=date(2025, 1, 15),
                libelle="RESTAURANT LE PARIS",
                montant=Decimal("45.80"),
                direction=TransactionDirection.OUT,
            ),
            ParsedTransaction(
                date_operation=date(2025, 1, 17),
                date_valeur=date(2025, 1, 17),
                libelle="UNKNOWN XYZABC",
                montant=Decimal("100.00"),
                direction=TransactionDirection.OUT,
            ),
        ]

        categorizer = TransactionCategorizer()
        categorized, uncategorized = categorizer.apply_categories(transactions)

        # Vérifier les compteurs
        assert categorized >= 1  # Au moins le restaurant
        assert uncategorized >= 1  # Au moins l'unknown
        assert categorized + uncategorized == len(transactions)

        # Vérifier que les catégories ont été appliquées
        assert transactions[0].category is not None
        assert transactions[1].category == "a_categoriser"


# Exemple d'utilisation du système (documentation)
def example_usage():
    """
    Exemple d'utilisation complète du système de catégorisation avec feedback.

    Ce n'est pas un test mais une documentation d'usage.
    """
    from datetime import date
    from decimal import Decimal

    # 1. Créer une transaction
    transaction = ParsedTransaction(
        date_operation=date(2025, 1, 15),
        date_valeur=date(2025, 1, 15),
        libelle="RESTAURANT LE BISTROT PARIS",
        montant=Decimal("45.80"),
        direction=TransactionDirection.OUT,
    )

    # 2. Catégoriser automatiquement
    categorizer = TransactionCategorizer(load_db_rules=True)
    result = categorizer.categorize(transaction)

    print(f"Catégorie prédite: {result.category_code}")
    print(f"Confiance: {result.confidence}")
    print(f"Mot-clé matché: {result.matched_keyword}")

    # 3. Appliquer la catégorie à la transaction
    transaction.category = result.category_code
    transaction.category_confidence = result.confidence

    # 4. Si l'utilisateur corrige la catégorie plus tard
    # (ex: il change "restaurant" en "repas_equipe")
    # Enregistrer le feedback pour l'apprentissage
    """
    feedback_id = record_categorization_feedback(
        transaction_id=transaction.id,  # Après insertion en DB
        predicted_category_id=5,        # ID de "restaurant"
        actual_category_id=12,          # ID de "repas_equipe"
        confidence_score=result.confidence,
        user_id=1,
        correction_source="manual"
    )
    print(f"Feedback enregistré: {feedback_id}")
    """

    # 5. Analyser les patterns de correction
    """
    stats = get_feedback_stats()
    print(f"Total corrections: {stats['total_corrections']}")
    print(f"Confiance moyenne des erreurs: {stats['avg_wrong_confidence']}")

    common = get_common_corrections(limit=10)
    for correction in common:
        print(f"{correction['predicted_name']} -> {correction['actual_name']}: "
              f"{correction['correction_count']} fois")
    """


if __name__ == "__main__":
    # Afficher l'exemple d'utilisation
    print("=== Exemple d'utilisation du système ===")
    print()
    example_usage()
