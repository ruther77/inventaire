"""Module de validation de données.

Ce module contient des fonctions pour la validation et la détection
d'anomalies dans les données.

Modules:
- duplicate_detection: Détection de doublons et fusion de données
"""

from .duplicate_detection import (
    DuplicateConfig,
    is_duplicate_transaction,
    merge_transactions,
    detect_missing_periods,
    find_duplicates_in_list,
    deduplicate_list,
)

__all__ = [
    "DuplicateConfig",
    "is_duplicate_transaction",
    "merge_transactions",
    "detect_missing_periods",
    "find_duplicates_in_list",
    "deduplicate_list",
]
