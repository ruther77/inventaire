"""Détection de doublons et fusion de données.

Ce module fournit des fonctions pour détecter les doublons dans les données
financières et transactionnelles, avec support pour le fuzzy matching.

Fonctions principales:
- is_duplicate_transaction: Vérifie si deux transactions sont des doublons
- merge_transactions: Fusionne deux transactions en gardant la meilleure info
- detect_missing_periods: Détecte les périodes manquantes dans une couverture

Exemples:
    >>> tx1 = {"date": date(2025, 1, 15), "libelle": "CARREFOUR", "montant": 50.00}
    >>> tx2 = {"date": date(2025, 1, 15), "libelle": "CARREFOUR MARKET", "montant": 50.00}
    >>> is_duplicate_transaction(tx1, tx2)
    True
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union

try:
    from utils.text_utils import fuzzy_match
except ImportError:
    # Fallback si import relatif impossible
    from difflib import SequenceMatcher

    def fuzzy_match(str1: str, str2: str, case_sensitive: bool = False) -> float:
        """Calcule la similarité entre deux chaînes."""
        s1 = str1.strip()
        s2 = str2.strip()
        if not case_sensitive:
            s1, s2 = s1.upper(), s2.upper()
        return SequenceMatcher(None, s1, s2).ratio()


# Type générique pour les transactions
T = TypeVar("T")


@dataclass
class DuplicateConfig:
    """Configuration pour la détection de doublons."""
    tolerance_days: int = 1
    tolerance_amount: Decimal = Decimal("0.01")
    fuzzy_threshold: float = 0.80


DEFAULT_CONFIG = DuplicateConfig()


def is_duplicate_transaction(
    tx1: Dict[str, Any],
    tx2: Dict[str, Any],
    config: Optional[DuplicateConfig] = None,
    date_key: str = "date",
    libelle_key: str = "libelle",
    montant_key: str = "montant",
    direction_key: Optional[str] = "direction",
) -> bool:
    """Vérifie si deux transactions sont des doublons.

    Critères de détection:
    - Date à ±tolerance_days
    - Montant identique (±tolerance_amount)
    - Libellé similaire (fuzzy match > threshold)
    - Direction identique (si spécifiée)

    Args:
        tx1: Première transaction (dict avec date, libelle, montant)
        tx2: Deuxième transaction
        config: Configuration de détection (optionnel)
        date_key: Clé pour accéder à la date
        libelle_key: Clé pour accéder au libellé
        montant_key: Clé pour accéder au montant
        direction_key: Clé pour la direction (None pour ignorer)

    Returns:
        True si les transactions sont considérées comme doublons

    Examples:
        >>> tx1 = {"date": date(2025, 1, 15), "libelle": "CARREFOUR", "montant": Decimal("50.00")}
        >>> tx2 = {"date": date(2025, 1, 15), "libelle": "CARREFOUR MARKET", "montant": Decimal("50.00")}
        >>> is_duplicate_transaction(tx1, tx2)
        True

        >>> tx3 = {"date": date(2025, 1, 20), "libelle": "CARREFOUR", "montant": Decimal("50.00")}
        >>> is_duplicate_transaction(tx1, tx3)
        False
    """
    if config is None:
        config = DEFAULT_CONFIG

    # Extraire les valeurs
    date1 = tx1.get(date_key)
    date2 = tx2.get(date_key)
    lib1 = str(tx1.get(libelle_key, ""))
    lib2 = str(tx2.get(libelle_key, ""))
    montant1 = Decimal(str(tx1.get(montant_key, 0)))
    montant2 = Decimal(str(tx2.get(montant_key, 0)))

    # Vérifier la date (± tolérance)
    if date1 and date2:
        if isinstance(date1, str):
            try:
                from formatting.french_parsers import parse_french_datetime
            except ImportError:
                from datetime import datetime
                def parse_french_datetime(v):
                    try:
                        return datetime.strptime(v.strip(), '%Y-%m-%d %H:%M:%S')
                    except:
                        try:
                            return datetime.strptime(v.strip(), '%Y-%m-%d')
                        except:
                            return None
            date1 = parse_french_datetime(date1)
            if date1:
                date1 = date1.date() if hasattr(date1, 'date') else date1
        if isinstance(date2, str):
            try:
                from formatting.french_parsers import parse_french_datetime
            except ImportError:
                from datetime import datetime
                def parse_french_datetime(v):
                    try:
                        return datetime.strptime(v.strip(), '%Y-%m-%d %H:%M:%S')
                    except:
                        try:
                            return datetime.strptime(v.strip(), '%Y-%m-%d')
                        except:
                            return None
            date2 = parse_french_datetime(date2)
            if date2:
                date2 = date2.date() if hasattr(date2, 'date') else date2

        if date1 and date2:
            date_diff = abs((date1 - date2).days)
            if date_diff > config.tolerance_days:
                return False

    # Vérifier le montant (± tolérance)
    amount_diff = abs(montant1 - montant2)
    if amount_diff > config.tolerance_amount:
        return False

    # Vérifier la direction si spécifiée
    if direction_key:
        dir1 = tx1.get(direction_key)
        dir2 = tx2.get(direction_key)
        if dir1 is not None and dir2 is not None and dir1 != dir2:
            return False

    # Vérifier la similarité du libellé
    similarity = fuzzy_match(lib1, lib2)
    if similarity < config.fuzzy_threshold:
        return False

    return True


def merge_transactions(
    existing: T,
    new: T,
    priority_key: str = "priority",
    libelle_key: str = "libelle",
) -> T:
    """Fusionne deux transactions en gardant la meilleure information.

    Stratégie de fusion:
    1. Garde la transaction de priorité la plus haute (valeur la plus basse)
    2. Si même priorité, garde le meilleur libellé (plus long, plus descriptif)

    Args:
        existing: Transaction existante
        new: Nouvelle transaction
        priority_key: Clé pour accéder à la priorité (plus bas = meilleur)
        libelle_key: Clé pour accéder au libellé

    Returns:
        Transaction gagnante (existing ou new)

    Examples:
        >>> tx1 = {"libelle": "CB CARREFOUR", "priority": 1}
        >>> tx2 = {"libelle": "CARREFOUR", "priority": 2}
        >>> merge_transactions(tx1, tx2)
        {'libelle': 'CB CARREFOUR', 'priority': 1}
    """
    # Obtenir les priorités
    if isinstance(existing, dict):
        prio1 = existing.get(priority_key, 999)
        prio2 = new.get(priority_key, 999)
        lib1 = str(existing.get(libelle_key, ""))
        lib2 = str(new.get(libelle_key, ""))
    else:
        prio1 = getattr(existing, priority_key, 999)
        prio2 = getattr(new, priority_key, 999)
        lib1 = str(getattr(existing, libelle_key, ""))
        lib2 = str(getattr(new, libelle_key, ""))

    # Comparer les priorités
    if prio1 < prio2:
        return existing
    elif prio2 < prio1:
        return new

    # Même priorité: choisir le meilleur libellé
    return _choose_best_by_libelle(existing, new, lib1, lib2)


def _choose_best_by_libelle(tx1: T, tx2: T, lib1: str, lib2: str) -> T:
    """Choisit la transaction avec le meilleur libellé.

    Critères:
    - Pas de préfixe technique (stmtline:, etc.)
    - Plus long = plus descriptif
    - Moins de caractères spéciaux
    """
    # Éliminer les préfixes techniques
    if lib1.startswith("stmtline:") and not lib2.startswith("stmtline:"):
        return tx2
    if lib2.startswith("stmtline:") and not lib1.startswith("stmtline:"):
        return tx1

    # Préférer le plus long (avec marge de 20%)
    if len(lib1) > len(lib2) * 1.2:
        return tx1
    if len(lib2) > len(lib1) * 1.2:
        return tx2

    # Si équivalent, garder le premier
    return tx1


def detect_missing_periods(
    period_coverage: Dict[str, List[Tuple[date, date]]],
    min_gap_days: int = 1,
) -> List[Tuple[str, date, date]]:
    """Détecte les périodes manquantes dans une couverture.

    Analyse les périodes couvertes par compte/source et identifie
    les gaps (périodes non couvertes) entre elles.

    Args:
        period_coverage: Dict {account: [(start, end), ...]} des périodes couvertes
        min_gap_days: Nombre minimum de jours pour considérer un gap (défaut: 1)

    Returns:
        Liste de tuples (account, gap_start, gap_end) pour les périodes manquantes

    Examples:
        >>> coverage = {
        ...     "compte_A": [(date(2025, 1, 1), date(2025, 1, 15)),
        ...                  (date(2025, 1, 20), date(2025, 1, 31))]
        ... }
        >>> detect_missing_periods(coverage)
        [("compte_A", date(2025, 1, 16), date(2025, 1, 19))]
    """
    missing: List[Tuple[str, date, date]] = []

    for account, periods in period_coverage.items():
        if not periods:
            continue

        sorted_periods = sorted(periods)

        for i in range(len(sorted_periods) - 1):
            current_end = sorted_periods[i][1]
            next_start = sorted_periods[i + 1][0]

            # Vérifier s'il y a un gap
            gap_days = (next_start - current_end).days
            if gap_days > min_gap_days:
                gap_start = current_end + timedelta(days=1)
                gap_end = next_start - timedelta(days=1)
                missing.append((account, gap_start, gap_end))

    return missing


def find_duplicates_in_list(
    items: List[Dict[str, Any]],
    config: Optional[DuplicateConfig] = None,
    **key_mapping: str,
) -> List[Tuple[int, int, float]]:
    """Trouve tous les doublons potentiels dans une liste.

    Args:
        items: Liste de transactions/items à analyser
        config: Configuration de détection
        **key_mapping: Mapping des clés (date_key, libelle_key, montant_key)

    Returns:
        Liste de tuples (index1, index2, similarity_score)

    Examples:
        >>> items = [
        ...     {"date": date(2025, 1, 15), "libelle": "CARREFOUR", "montant": 50},
        ...     {"date": date(2025, 1, 15), "libelle": "CARREFOUR MARKET", "montant": 50},
        ...     {"date": date(2025, 1, 20), "libelle": "LIDL", "montant": 30},
        ... ]
        >>> find_duplicates_in_list(items)
        [(0, 1, 0.85...)]
    """
    if config is None:
        config = DEFAULT_CONFIG

    duplicates: List[Tuple[int, int, float]] = []

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if is_duplicate_transaction(items[i], items[j], config, **key_mapping):
                lib1 = str(items[i].get(key_mapping.get("libelle_key", "libelle"), ""))
                lib2 = str(items[j].get(key_mapping.get("libelle_key", "libelle"), ""))
                similarity = fuzzy_match(lib1, lib2)
                duplicates.append((i, j, similarity))

    return duplicates


def deduplicate_list(
    items: List[T],
    is_duplicate_fn: Callable[[T, T], bool],
    merge_fn: Optional[Callable[[T, T], T]] = None,
) -> List[T]:
    """Déduplique une liste en utilisant des fonctions personnalisées.

    Args:
        items: Liste d'éléments à dédupliquer
        is_duplicate_fn: Fonction (item1, item2) -> bool
        merge_fn: Fonction de fusion optionnelle (item1, item2) -> merged
                  Si None, garde le premier élément

    Returns:
        Liste dédupliquée

    Examples:
        >>> items = [{"id": 1, "name": "A"}, {"id": 2, "name": "A"}, {"id": 3, "name": "B"}]
        >>> is_dup = lambda x, y: x["name"] == y["name"]
        >>> deduplicate_list(items, is_dup)
        [{"id": 1, "name": "A"}, {"id": 3, "name": "B"}]
    """
    if not items:
        return []

    result: List[T] = []
    seen_indices: set = set()

    for i, item in enumerate(items):
        if i in seen_indices:
            continue

        current = item

        # Chercher les doublons
        for j in range(i + 1, len(items)):
            if j in seen_indices:
                continue

            if is_duplicate_fn(current, items[j]):
                seen_indices.add(j)
                if merge_fn:
                    current = merge_fn(current, items[j])

        result.append(current)

    return result
