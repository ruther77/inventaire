"""Module d'utilitaires généraux.

Ce module contient des fonctions utilitaires réutilisables
pour le traitement de texte, la manipulation de données, etc.

Modules :
- text_utils : utilitaires de traitement de texte
- cart_normalizer : normalisation de paniers
"""

from .text_utils import (
    fuzzy_match,
    normalize_text,
    normalize_product_name,
    split_paragraphs,
    chunk_with_overlap,
    extract_keywords,
    levenshtein_distance,
)
from .cart_normalizer import normalize_cart_rows

__all__ = [
    "fuzzy_match",
    "normalize_text",
    "normalize_product_name",
    "split_paragraphs",
    "chunk_with_overlap",
    "extract_keywords",
    "levenshtein_distance",
    "normalize_cart_rows",
]
