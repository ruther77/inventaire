"""Tests pour le module validation.duplicate_detection."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from validation.duplicate_detection import (
    DuplicateConfig,
    is_duplicate_transaction,
    merge_transactions,
    detect_missing_periods,
    find_duplicates_in_list,
    deduplicate_list,
)


class TestIsDuplicateTransaction:
    """Tests pour is_duplicate_transaction."""

    def test_identical_transactions(self):
        """Teste les transactions identiques."""
        tx1 = {
            "date": date(2025, 1, 15),
            "libelle": "CARREFOUR MARKET",
            "montant": Decimal("50.00"),
        }
        tx2 = tx1.copy()
        assert is_duplicate_transaction(tx1, tx2)

    def test_similar_transactions(self):
        """Teste les transactions similaires (libellé très proche)."""
        tx1 = {
            "date": date(2025, 1, 15),
            "libelle": "CB CARREFOUR MARKET PARIS",
            "montant": Decimal("50.00"),
        }
        tx2 = {
            "date": date(2025, 1, 15),
            "libelle": "CB CARREFOUR MARKET",
            "montant": Decimal("50.00"),
        }
        # Devrait être considéré comme doublon car libellé très similaire (>80%)
        assert is_duplicate_transaction(tx1, tx2)

    def test_different_dates(self):
        """Teste les transactions avec dates trop différentes."""
        tx1 = {
            "date": date(2025, 1, 15),
            "libelle": "CARREFOUR",
            "montant": Decimal("50.00"),
        }
        tx2 = {
            "date": date(2025, 1, 20),  # 5 jours de différence
            "libelle": "CARREFOUR",
            "montant": Decimal("50.00"),
        }
        assert not is_duplicate_transaction(tx1, tx2)

    def test_date_tolerance(self):
        """Teste la tolérance de date."""
        tx1 = {
            "date": date(2025, 1, 15),
            "libelle": "CARREFOUR",
            "montant": Decimal("50.00"),
        }
        tx2 = {
            "date": date(2025, 1, 16),  # 1 jour de différence
            "libelle": "CARREFOUR",
            "montant": Decimal("50.00"),
        }
        # Avec tolérance par défaut de 1 jour
        assert is_duplicate_transaction(tx1, tx2)

    def test_different_amounts(self):
        """Teste les transactions avec montants différents."""
        tx1 = {
            "date": date(2025, 1, 15),
            "libelle": "CARREFOUR",
            "montant": Decimal("50.00"),
        }
        tx2 = {
            "date": date(2025, 1, 15),
            "libelle": "CARREFOUR",
            "montant": Decimal("55.00"),  # Montant différent
        }
        assert not is_duplicate_transaction(tx1, tx2)

    def test_amount_tolerance(self):
        """Teste la tolérance de montant."""
        tx1 = {
            "date": date(2025, 1, 15),
            "libelle": "CARREFOUR",
            "montant": Decimal("50.00"),
        }
        tx2 = {
            "date": date(2025, 1, 15),
            "libelle": "CARREFOUR",
            "montant": Decimal("50.01"),  # 0.01 de différence
        }
        # Avec tolérance par défaut de 0.01
        assert is_duplicate_transaction(tx1, tx2)

    def test_direction_check(self):
        """Teste la vérification de direction."""
        tx1 = {
            "date": date(2025, 1, 15),
            "libelle": "VIREMENT",
            "montant": Decimal("100.00"),
            "direction": "IN",
        }
        tx2 = {
            "date": date(2025, 1, 15),
            "libelle": "VIREMENT",
            "montant": Decimal("100.00"),
            "direction": "OUT",
        }
        assert not is_duplicate_transaction(tx1, tx2)

    def test_different_libelle(self):
        """Teste les libellés complètement différents."""
        tx1 = {
            "date": date(2025, 1, 15),
            "libelle": "CARREFOUR",
            "montant": Decimal("50.00"),
        }
        tx2 = {
            "date": date(2025, 1, 15),
            "libelle": "LIDL",
            "montant": Decimal("50.00"),
        }
        assert not is_duplicate_transaction(tx1, tx2)

    def test_custom_config(self):
        """Teste avec configuration personnalisée."""
        config = DuplicateConfig(
            tolerance_days=3,
            tolerance_amount=Decimal("1.00"),
            fuzzy_threshold=0.5,
        )
        tx1 = {
            "date": date(2025, 1, 15),
            "libelle": "CARREFOUR",
            "montant": Decimal("50.00"),
        }
        tx2 = {
            "date": date(2025, 1, 17),  # 2 jours (< 3)
            "libelle": "CARREFOUR MARKET",  # Similaire
            "montant": Decimal("50.50"),  # 0.50 (< 1.00)
        }
        assert is_duplicate_transaction(tx1, tx2, config=config)


class TestMergeTransactions:
    """Tests pour merge_transactions."""

    def test_priority_wins(self):
        """Teste que la priorité plus basse gagne."""
        tx1 = {"libelle": "TX1", "priority": 1}
        tx2 = {"libelle": "TX2", "priority": 2}
        assert merge_transactions(tx1, tx2) == tx1

    def test_higher_priority_loses(self):
        """Teste que la priorité plus haute perd."""
        tx1 = {"libelle": "TX1", "priority": 3}
        tx2 = {"libelle": "TX2", "priority": 1}
        assert merge_transactions(tx1, tx2) == tx2

    def test_equal_priority_better_libelle(self):
        """Teste que le meilleur libellé gagne à priorité égale."""
        tx1 = {"libelle": "CB CARREFOUR MARKET PARIS", "priority": 1}
        tx2 = {"libelle": "CARREFOUR", "priority": 1}
        result = merge_transactions(tx1, tx2)
        assert result == tx1  # Plus long

    def test_technical_prefix_loses(self):
        """Teste que le préfixe technique perd."""
        tx1 = {"libelle": "stmtline:123456", "priority": 1}
        tx2 = {"libelle": "CB CARREFOUR", "priority": 1}
        result = merge_transactions(tx1, tx2)
        assert result == tx2


class TestDetectMissingPeriods:
    """Tests pour detect_missing_periods."""

    def test_gap_detection(self, sample_periods):
        """Teste la détection de gaps."""
        missing = detect_missing_periods(sample_periods)

        # compte_A a un gap du 16 au 19 janvier
        assert len([m for m in missing if m[0] == "compte_A"]) == 1

        gap = [m for m in missing if m[0] == "compte_A"][0]
        assert gap[1] == date(2025, 1, 16)
        assert gap[2] == date(2025, 1, 19)

    def test_no_gap(self):
        """Teste quand il n'y a pas de gap."""
        coverage = {
            "compte": [
                (date(2025, 1, 1), date(2025, 1, 15)),
                (date(2025, 1, 16), date(2025, 1, 31)),  # Pas de gap
            ]
        }
        missing = detect_missing_periods(coverage)
        assert len(missing) == 0

    def test_empty_coverage(self):
        """Teste avec une couverture vide."""
        coverage = {"compte": []}
        missing = detect_missing_periods(coverage)
        assert len(missing) == 0

    def test_single_period(self):
        """Teste avec une seule période."""
        coverage = {"compte": [(date(2025, 1, 1), date(2025, 1, 31))]}
        missing = detect_missing_periods(coverage)
        assert len(missing) == 0

    def test_custom_gap_threshold(self):
        """Teste avec un seuil de gap personnalisé."""
        coverage = {
            "compte": [
                (date(2025, 1, 1), date(2025, 1, 10)),
                (date(2025, 1, 15), date(2025, 1, 31)),  # Gap de 4 jours
            ]
        }
        # Avec seuil de 5, pas de gap détecté
        missing = detect_missing_periods(coverage, min_gap_days=5)
        assert len(missing) == 0

        # Avec seuil de 1, gap détecté
        missing = detect_missing_periods(coverage, min_gap_days=1)
        assert len(missing) == 1


class TestFindDuplicatesInList:
    """Tests pour find_duplicates_in_list."""

    def test_finds_duplicates(self):
        """Teste la détection de doublons dans une liste."""
        items = [
            {"date": date(2025, 1, 15), "libelle": "CB CARREFOUR MARKET", "montant": Decimal("50.00")},
            {"date": date(2025, 1, 15), "libelle": "CB CARREFOUR MARKET PARIS", "montant": Decimal("50.00")},
            {"date": date(2025, 1, 20), "libelle": "LIDL", "montant": Decimal("35.50")},
        ]
        duplicates = find_duplicates_in_list(items)
        # Les deux premiers sont des doublons (libellés très similaires)
        assert len(duplicates) >= 1
        # Vérifie que le premier doublon concerne les indices 0 et 1
        assert (0, 1) in [(d[0], d[1]) for d in duplicates]

    def test_no_duplicates(self):
        """Teste quand il n'y a pas de doublons."""
        items = [
            {"date": date(2025, 1, 1), "libelle": "A", "montant": Decimal("10")},
            {"date": date(2025, 1, 2), "libelle": "B", "montant": Decimal("20")},
            {"date": date(2025, 1, 3), "libelle": "C", "montant": Decimal("30")},
        ]
        duplicates = find_duplicates_in_list(items)
        assert len(duplicates) == 0

    def test_empty_list(self):
        """Teste avec une liste vide."""
        duplicates = find_duplicates_in_list([])
        assert len(duplicates) == 0


class TestDeduplicateList:
    """Tests pour deduplicate_list."""

    def test_basic_deduplication(self):
        """Teste la déduplication basique."""
        items = [
            {"id": 1, "name": "A"},
            {"id": 2, "name": "A"},  # Doublon
            {"id": 3, "name": "B"},
        ]
        is_dup = lambda x, y: x["name"] == y["name"]
        result = deduplicate_list(items, is_dup)
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 3

    def test_with_merge_function(self):
        """Teste avec fonction de fusion."""
        items = [
            {"id": 1, "name": "A", "value": 10},
            {"id": 2, "name": "A", "value": 20},  # Doublon avec valeur plus haute
        ]
        is_dup = lambda x, y: x["name"] == y["name"]
        merge = lambda x, y: x if x["value"] > y["value"] else y
        result = deduplicate_list(items, is_dup, merge)
        assert len(result) == 1
        assert result[0]["value"] == 20

    def test_empty_list(self):
        """Teste avec une liste vide."""
        result = deduplicate_list([], lambda x, y: True)
        assert result == []

    def test_no_duplicates(self):
        """Teste sans doublons."""
        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        is_dup = lambda x, y: x["id"] == y["id"]
        result = deduplicate_list(items, is_dup)
        assert len(result) == 3
