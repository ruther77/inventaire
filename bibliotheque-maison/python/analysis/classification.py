"""Classification ABC/XYZ pour l'analyse d'inventaire.

Ce module fournit des fonctions pour classifier des items selon:
- ABC: Basé sur la valeur cumulative (Pareto)
- XYZ: Basé sur la variabilité de la demande (coefficient de variation)
- ABC-XYZ: Classification combinée

Inspiré de la méthode classique de gestion d'inventaire.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def calculate_coefficient_variation(values: List[float]) -> float:
    """Calcule le coefficient de variation (CV = écart-type / moyenne).

    Le coefficient de variation mesure la dispersion relative d'un ensemble
    de valeurs. Plus le CV est élevé, plus la demande est variable.

    Args:
        values: Liste de valeurs numériques (ex: demandes quotidiennes)

    Returns:
        Le coefficient de variation. Retourne float('inf') si la moyenne
        est nulle ou négative.

    Raises:
        ValueError: Si la liste est vide

    Examples:
        >>> calculate_coefficient_variation([10, 12, 11, 9, 10])
        0.111...
        >>> calculate_coefficient_variation([10, 10, 10, 10])
        0.0
        >>> calculate_coefficient_variation([0, 0, 0])
        inf
    """
    if not values:
        raise ValueError("La liste de valeurs ne peut pas être vide")

    if HAS_NUMPY:
        arr = np.array(values, dtype=float)
        mean = arr.mean()
        std = arr.std(ddof=0)  # Population std
    else:
        # Calcul manuel sans numpy
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std = variance ** 0.5

    if mean <= 0:
        return float('inf')

    return std / mean


def classify_abc(
    items: List[dict],
    value_key: str = 'value',
    thresholds: Tuple[float, float] = (0.8, 0.95)
) -> Dict[str, List[dict]]:
    """Classifie des items selon la méthode ABC (Pareto).

    La classification ABC divise les items en trois catégories selon leur
    contribution à la valeur totale:
    - A: Items contribuant aux premiers X% de la valeur (défaut: 80%)
    - B: Items contribuant jusqu'à Y% de la valeur (défaut: 95%)
    - C: Items restants (derniers 5%)

    Args:
        items: Liste de dictionnaires contenant au minimum la clé de valeur
        value_key: Nom de la clé contenant la valeur numérique
        thresholds: Tuple (seuil_A, seuil_B) en pourcentage décimal
                   Défaut: (0.8, 0.95) pour 80% et 95%

    Returns:
        Dictionnaire avec clés 'A', 'B', 'C' contenant les listes d'items.
        Chaque item est enrichi avec:
        - 'abc_class': La classe assignée ('A', 'B', ou 'C')
        - 'share': Part de la valeur totale (0.0 à 1.0)
        - 'cumul': Valeur cumulative (0.0 à 1.0)

    Raises:
        ValueError: Si les seuils sont invalides ou si value_key est absent

    Examples:
        >>> items = [
        ...     {'id': 1, 'value': 1000},
        ...     {'id': 2, 'value': 500},
        ...     {'id': 3, 'value': 100}
        ... ]
        >>> result = classify_abc(items)
        >>> len(result['A'])
        1
        >>> result['A'][0]['id']
        1
    """
    if not items:
        return {'A': [], 'B': [], 'C': []}

    if thresholds[0] <= 0 or thresholds[1] <= thresholds[0] or thresholds[1] > 1.0:
        raise ValueError(
            f"Seuils invalides: {thresholds}. "
            "Attendu: 0 < seuil_A < seuil_B <= 1.0"
        )

    # Vérifier que la clé existe
    if not all(value_key in item for item in items):
        raise ValueError(f"Tous les items doivent contenir la clé '{value_key}'")

    # Copier les items pour ne pas modifier l'original
    items_copy = [item.copy() for item in items]

    # Assurer que les valeurs sont positives
    for item in items_copy:
        item[value_key] = max(0.0, float(item.get(value_key, 0)))

    # Trier par valeur décroissante
    items_copy.sort(key=lambda x: x[value_key], reverse=True)

    # Calculer la valeur totale
    total_value = sum(item[value_key] for item in items_copy)

    if total_value <= 0:
        # Tous les items en classe C si aucune valeur
        for item in items_copy:
            item['abc_class'] = 'C'
            item['share'] = 0.0
            item['cumul'] = 0.0
        return {'A': [], 'B': [], 'C': items_copy}

    # Calculer parts et cumulatifs
    cumul = 0.0
    result: Dict[str, List[dict]] = {'A': [], 'B': [], 'C': []}

    for item in items_copy:
        share = item[value_key] / total_value
        cumul += share

        item['share'] = share
        item['cumul'] = cumul

        # Assigner la classe
        if cumul <= thresholds[0]:
            item['abc_class'] = 'A'
            result['A'].append(item)
        elif cumul <= thresholds[1]:
            item['abc_class'] = 'B'
            result['B'].append(item)
        else:
            item['abc_class'] = 'C'
            result['C'].append(item)

    return result


def classify_xyz(
    items: List[dict],
    cv_key: str = 'cv',
    thresholds: Tuple[float, float] = (0.5, 1.0)
) -> Dict[str, List[dict]]:
    """Classifie des items selon la méthode XYZ (variabilité).

    La classification XYZ divise les items selon la variabilité de leur demande:
    - X: Demande stable (CV < seuil_X, défaut: 0.5)
    - Y: Demande variable (seuil_X <= CV < seuil_Y, défaut: 1.0)
    - Z: Demande très variable (CV >= seuil_Y ou demande nulle)

    Args:
        items: Liste de dictionnaires contenant le coefficient de variation
        cv_key: Nom de la clé contenant le CV (ou None/inf pour demande nulle)
        thresholds: Tuple (seuil_X, seuil_Y) pour les limites CV
                   Défaut: (0.5, 1.0)

    Returns:
        Dictionnaire avec clés 'X', 'Y', 'Z' contenant les listes d'items.
        Chaque item est enrichi avec 'xyz_class'.

    Raises:
        ValueError: Si les seuils sont invalides

    Examples:
        >>> items = [
        ...     {'id': 1, 'cv': 0.3},
        ...     {'id': 2, 'cv': 0.7},
        ...     {'id': 3, 'cv': 1.5}
        ... ]
        >>> result = classify_xyz(items)
        >>> len(result['X'])
        1
        >>> len(result['Y'])
        1
        >>> len(result['Z'])
        1
    """
    if not items:
        return {'X': [], 'Y': [], 'Z': []}

    if thresholds[0] <= 0 or thresholds[1] <= thresholds[0]:
        raise ValueError(
            f"Seuils invalides: {thresholds}. "
            "Attendu: 0 < seuil_X < seuil_Y"
        )

    result: Dict[str, List[dict]] = {'X': [], 'Y': [], 'Z': []}

    for item in items:
        item_copy = item.copy()
        cv = item_copy.get(cv_key)

        # Gérer les cas spéciaux (None, inf, valeurs négatives)
        if cv is None or not isinstance(cv, (int, float)):
            xyz_class = 'Z'
        elif cv == float('inf') or cv < 0:
            xyz_class = 'Z'
        elif cv < thresholds[0]:
            xyz_class = 'X'
        elif cv < thresholds[1]:
            xyz_class = 'Y'
        else:
            xyz_class = 'Z'

        item_copy['xyz_class'] = xyz_class
        result[xyz_class].append(item_copy)

    return result


def classify_abc_xyz(
    items: List[dict],
    value_key: str = 'value',
    cv_key: str = 'cv',
    abc_thresholds: Tuple[float, float] = (0.8, 0.95),
    xyz_thresholds: Tuple[float, float] = (0.5, 1.0)
) -> Dict[str, List[dict]]:
    """Classification combinée ABC-XYZ.

    Combine les classifications ABC (valeur) et XYZ (variabilité) pour
    obtenir une matrice de 9 catégories: AX, AY, AZ, BX, BY, BZ, CX, CY, CZ.

    Recommandations de gestion:
    - AX: Items critiques, demande stable -> Gestion simple, stock sécurisé
    - AY: Items critiques, demande variable -> Surveillance régulière
    - AZ: Items critiques, demande erratique -> Analyse détaillée nécessaire
    - BX: Items moyens, demande stable -> Gestion standard
    - BY: Items moyens, demande variable -> Revue périodique
    - BZ: Items moyens, demande erratique -> Gestion réactive
    - CX: Items faibles, demande stable -> Stock minimum
    - CY: Items faibles, demande variable -> Sur commande
    - CZ: Items faibles, demande erratique -> Stock de sécurité minimal

    Args:
        items: Liste d'items avec value_key et cv_key
        value_key: Clé de la valeur pour classification ABC
        cv_key: Clé du coefficient de variation pour classification XYZ
        abc_thresholds: Seuils pour ABC (défaut: 80%, 95%)
        xyz_thresholds: Seuils pour XYZ (défaut: 0.5, 1.0)

    Returns:
        Dictionnaire avec 9 clés (AX, AY, AZ, BX, BY, BZ, CX, CY, CZ).
        Chaque item contient 'abc_class', 'xyz_class', et 'abc_xyz_class'.

    Examples:
        >>> items = [
        ...     {'id': 1, 'value': 1000, 'cv': 0.3},
        ...     {'id': 2, 'value': 500, 'cv': 0.7},
        ...     {'id': 3, 'value': 100, 'cv': 1.5}
        ... ]
        >>> result = classify_abc_xyz(items, value_key='value', cv_key='cv')
        >>> 'AX' in result
        True
    """
    if not items:
        return {
            f"{abc}{xyz}": []
            for abc in ['A', 'B', 'C']
            for xyz in ['X', 'Y', 'Z']
        }

    # D'abord classifier ABC
    abc_result = classify_abc(items, value_key=value_key, thresholds=abc_thresholds)

    # Recombiner tous les items avec leur classe ABC
    all_items_abc = []
    for abc_class in ['A', 'B', 'C']:
        all_items_abc.extend(abc_result[abc_class])

    # Ensuite classifier XYZ
    xyz_result = classify_xyz(all_items_abc, cv_key=cv_key, thresholds=xyz_thresholds)

    # Créer la classification combinée
    result: Dict[str, List[dict]] = {
        f"{abc}{xyz}": []
        for abc in ['A', 'B', 'C']
        for xyz in ['X', 'Y', 'Z']
    }

    # Distribuer les items dans les bonnes catégories
    for xyz_class in ['X', 'Y', 'Z']:
        for item in xyz_result[xyz_class]:
            abc_class = item['abc_class']
            combined_class = f"{abc_class}{xyz_class}"
            item['abc_xyz_class'] = combined_class
            result[combined_class].append(item)

    return result


__all__ = [
    'calculate_coefficient_variation',
    'classify_abc',
    'classify_xyz',
    'classify_abc_xyz',
]
