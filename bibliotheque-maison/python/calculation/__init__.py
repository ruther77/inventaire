"""Module de calculs.

Ce module contient des fonctions pour les calculs financiers,
fiscaux et autres calculs métier.

Modules:
- tax_utils: Utilitaires de calcul de taxes (TVA)
- inventory_utils: Utilitaires de gestion d'inventaire (PAMP, EOQ, stock de sécurité)
"""

from .tax_utils import (
    infer_tva,
    calculate_ht_from_ttc,
    calculate_ttc_from_ht,
    calculate_tva_amount,
    infer_category,
    categorize_product,
)

from .inventory_utils import (
    calculate_pamp,
    calculate_eoq,
    calculate_safety_stock,
    calculate_reorder_point,
    calculate_margin,
)

__all__ = [
    # Tax utilities
    "infer_tva",
    "calculate_ht_from_ttc",
    "calculate_ttc_from_ht",
    "calculate_tva_amount",
    "infer_category",
    "categorize_product",
    # Inventory utilities
    "calculate_pamp",
    "calculate_eoq",
    "calculate_safety_stock",
    "calculate_reorder_point",
    "calculate_margin",
]
