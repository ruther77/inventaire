"""Tests pour le module analysis.classification."""

import pytest
from analysis.classification import (
    calculate_coefficient_variation,
    classify_abc,
    classify_abc_xyz,
    classify_xyz,
)


class TestCoefficientVariation:
    """Tests pour calculate_coefficient_variation."""

    def test_uniform_values(self):
        """CV devrait être 0 pour des valeurs identiques."""
        values = [10.0, 10.0, 10.0, 10.0]
        cv = calculate_coefficient_variation(values)
        assert cv == 0.0

    def test_variable_values(self):
        """CV devrait être > 0 pour des valeurs variables."""
        values = [10.0, 20.0, 30.0, 40.0]
        cv = calculate_coefficient_variation(values)
        assert cv > 0
        assert 0.4 < cv < 0.6  # Approximativement 0.5

    def test_zero_mean(self):
        """CV devrait être inf si la moyenne est 0."""
        values = [0.0, 0.0, 0.0]
        cv = calculate_coefficient_variation(values)
        assert cv == float('inf')

    def test_empty_list(self):
        """Devrait lever ValueError pour liste vide."""
        with pytest.raises(ValueError, match="ne peut pas être vide"):
            calculate_coefficient_variation([])

    def test_single_value(self):
        """CV devrait être 0 pour une seule valeur."""
        cv = calculate_coefficient_variation([42.0])
        assert cv == 0.0

    def test_negative_mean(self):
        """CV devrait être inf si la moyenne est négative."""
        values = [-5.0, -10.0, -15.0]
        cv = calculate_coefficient_variation(values)
        assert cv == float('inf')


class TestClassifyABC:
    """Tests pour classify_abc."""

    def test_basic_classification(self):
        """Test classification ABC basique."""
        items = [
            {'id': 1, 'value': 1000},
            {'id': 2, 'value': 500},
            {'id': 3, 'value': 300},
            {'id': 4, 'value': 100},
            {'id': 5, 'value': 50},
        ]
        result = classify_abc(items)

        # Vérifier que toutes les clés existent
        assert set(result.keys()) == {'A', 'B', 'C'}

        # Vérifier que tous les items sont classés
        total_items = len(result['A']) + len(result['B']) + len(result['C'])
        assert total_items == 5

        # Le plus gros item devrait être en A
        assert result['A'][0]['id'] == 1
        assert result['A'][0]['abc_class'] == 'A'

        # Vérifier que share et cumul sont ajoutés
        for item in result['A']:
            assert 'share' in item
            assert 'cumul' in item
            assert 0 <= item['share'] <= 1
            assert 0 <= item['cumul'] <= 1

    def test_custom_thresholds(self):
        """Test avec seuils personnalisés."""
        items = [
            {'id': 1, 'value': 100},
            {'id': 2, 'value': 50},
            {'id': 3, 'value': 25},
        ]
        result = classify_abc(items, thresholds=(0.6, 0.9))

        # Avec ces seuils, la répartition devrait être différente
        assert len(result['A']) >= 1

    def test_empty_list(self):
        """Test avec liste vide."""
        result = classify_abc([])
        assert result == {'A': [], 'B': [], 'C': []}

    def test_zero_values(self):
        """Test avec valeurs nulles."""
        items = [
            {'id': 1, 'value': 0},
            {'id': 2, 'value': 0},
        ]
        result = classify_abc(items)

        # Tous devraient être en C
        assert len(result['C']) == 2
        assert len(result['A']) == 0
        assert len(result['B']) == 0

    def test_custom_value_key(self):
        """Test avec clé de valeur personnalisée."""
        items = [
            {'id': 1, 'price': 100},
            {'id': 2, 'price': 50},
        ]
        result = classify_abc(items, value_key='price')
        assert len(result['A']) >= 1

    def test_invalid_thresholds(self):
        """Test avec seuils invalides."""
        items = [{'id': 1, 'value': 100}]

        with pytest.raises(ValueError, match="Seuils invalides"):
            classify_abc(items, thresholds=(0.9, 0.5))  # Inversés

        with pytest.raises(ValueError, match="Seuils invalides"):
            classify_abc(items, thresholds=(0.0, 0.5))  # Premier = 0

        with pytest.raises(ValueError, match="Seuils invalides"):
            classify_abc(items, thresholds=(0.5, 1.5))  # Deuxième > 1

    def test_missing_value_key(self):
        """Test avec clé manquante."""
        items = [{'id': 1, 'price': 100}]

        with pytest.raises(ValueError, match="doivent contenir la clé"):
            classify_abc(items, value_key='value')

    def test_negative_values(self):
        """Test que les valeurs négatives sont traitées comme 0."""
        items = [
            {'id': 1, 'value': 100},
            {'id': 2, 'value': -50},
        ]
        result = classify_abc(items)

        # L'item avec valeur négative devrait avoir value = 0
        for cat in ['A', 'B', 'C']:
            for item in result[cat]:
                if item['id'] == 2:
                    assert item['value'] == 0


class TestClassifyXYZ:
    """Tests pour classify_xyz."""

    def test_basic_classification(self):
        """Test classification XYZ basique."""
        items = [
            {'id': 1, 'cv': 0.3},   # X
            {'id': 2, 'cv': 0.7},   # Y
            {'id': 3, 'cv': 1.5},   # Z
        ]
        result = classify_xyz(items)

        assert len(result['X']) == 1
        assert len(result['Y']) == 1
        assert len(result['Z']) == 1
        assert result['X'][0]['xyz_class'] == 'X'
        assert result['Y'][0]['xyz_class'] == 'Y'
        assert result['Z'][0]['xyz_class'] == 'Z'

    def test_custom_thresholds(self):
        """Test avec seuils personnalisés."""
        items = [
            {'id': 1, 'cv': 0.3},
            {'id': 2, 'cv': 0.7},
            {'id': 3, 'cv': 1.5},
        ]
        result = classify_xyz(items, thresholds=(0.4, 1.0))

        # Avec ces seuils: cv=0.3 -> X, cv=0.7 -> Y, cv=1.5 -> Z
        assert len(result['X']) == 1
        assert len(result['Y']) == 1
        assert len(result['Z']) == 1

    def test_special_values(self):
        """Test avec valeurs spéciales (None, inf)."""
        items = [
            {'id': 1, 'cv': None},
            {'id': 2, 'cv': float('inf')},
            {'id': 3, 'cv': -1},
        ]
        result = classify_xyz(items)

        # Tous devraient être en Z
        assert len(result['Z']) == 3

    def test_empty_list(self):
        """Test avec liste vide."""
        result = classify_xyz([])
        assert result == {'X': [], 'Y': [], 'Z': []}

    def test_custom_cv_key(self):
        """Test avec clé CV personnalisée."""
        items = [
            {'id': 1, 'variability': 0.3},
            {'id': 2, 'variability': 0.7},
        ]
        result = classify_xyz(items, cv_key='variability')
        assert len(result['X']) == 1
        assert len(result['Y']) == 1

    def test_invalid_thresholds(self):
        """Test avec seuils invalides."""
        items = [{'id': 1, 'cv': 0.5}]

        with pytest.raises(ValueError, match="Seuils invalides"):
            classify_xyz(items, thresholds=(1.0, 0.5))  # Inversés

        with pytest.raises(ValueError, match="Seuils invalides"):
            classify_xyz(items, thresholds=(0.0, 0.5))  # Premier = 0


class TestClassifyABCXYZ:
    """Tests pour classify_abc_xyz."""

    def test_basic_combined_classification(self):
        """Test classification combinée basique."""
        items = [
            {'id': 1, 'value': 1000, 'cv': 0.3},  # Devrait être AX
            {'id': 2, 'value': 500, 'cv': 0.7},   # Devrait être AY ou BX/BY
            {'id': 3, 'value': 100, 'cv': 1.5},   # Devrait être BZ ou CZ
        ]
        result = classify_abc_xyz(items)

        # Vérifier que les 9 catégories existent
        expected_keys = {
            'AX', 'AY', 'AZ',
            'BX', 'BY', 'BZ',
            'CX', 'CY', 'CZ'
        }
        assert set(result.keys()) == expected_keys

        # Vérifier que tous les items sont classés
        total_items = sum(len(result[key]) for key in result)
        assert total_items == 3

        # Vérifier que les items ont les bonnes métadonnées
        for category in result.values():
            for item in category:
                assert 'abc_class' in item
                assert 'xyz_class' in item
                assert 'abc_xyz_class' in item
                assert item['abc_xyz_class'] in expected_keys

    def test_empty_list(self):
        """Test avec liste vide."""
        result = classify_abc_xyz([])

        # Devrait retourner 9 catégories vides
        assert len(result) == 9
        for category in result.values():
            assert category == []

    def test_custom_keys_and_thresholds(self):
        """Test avec clés et seuils personnalisés."""
        items = [
            {'id': 1, 'price': 1000, 'variability': 0.3},
            {'id': 2, 'price': 500, 'variability': 0.7},
        ]
        result = classify_abc_xyz(
            items,
            value_key='price',
            cv_key='variability',
            abc_thresholds=(0.7, 0.9),
            xyz_thresholds=(0.4, 0.8)
        )

        # Vérifier que la classification fonctionne
        total_items = sum(len(result[key]) for key in result)
        assert total_items == 2

    def test_category_consistency(self):
        """Test que la catégorie combinée correspond aux classes individuelles."""
        items = [
            {'id': 1, 'value': 1000, 'cv': 0.3},
        ]
        result = classify_abc_xyz(items)

        # Trouver l'item classé
        for category_name, category_items in result.items():
            for item in category_items:
                # Vérifier que abc_xyz_class = abc_class + xyz_class
                expected = item['abc_class'] + item['xyz_class']
                assert item['abc_xyz_class'] == expected
                assert item['abc_xyz_class'] == category_name

    def test_distribution(self):
        """Test avec un ensemble plus large pour vérifier la distribution."""
        items = [
            # Groupe A (haute valeur)
            {'id': 1, 'value': 1000, 'cv': 0.2},   # AX
            {'id': 2, 'value': 900, 'cv': 0.6},    # AY
            {'id': 3, 'value': 800, 'cv': 1.5},    # AZ
            # Groupe B (valeur moyenne)
            {'id': 4, 'value': 200, 'cv': 0.3},    # BX
            {'id': 5, 'value': 150, 'cv': 0.7},    # BY
            {'id': 6, 'value': 100, 'cv': 1.2},    # BZ
            # Groupe C (faible valeur)
            {'id': 7, 'value': 30, 'cv': 0.4},     # CX
            {'id': 8, 'value': 20, 'cv': 0.8},     # CY
            {'id': 9, 'value': 10, 'cv': 2.0},     # CZ
        ]
        result = classify_abc_xyz(items)

        # Vérifier qu'on a des items dans plusieurs catégories
        non_empty_categories = sum(1 for cat in result.values() if len(cat) > 0)
        assert non_empty_categories >= 3  # Au moins 3 catégories différentes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
