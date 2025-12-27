"""Module d'analyse pour la bibliothèque maison.

Ce module fournit des outils d'analyse pour la gestion d'inventaire,
notamment les classifications ABC/XYZ basées sur la méthode Pareto
et l'analyse de la variabilité de la demande.

Modules disponibles:
    - classification: Classifications ABC, XYZ et ABC-XYZ
"""

from .classification import (
    calculate_coefficient_variation,
    classify_abc,
    classify_abc_xyz,
    classify_xyz,
)

__all__ = [
    'calculate_coefficient_variation',
    'classify_abc',
    'classify_xyz',
    'classify_abc_xyz',
]

__version__ = '1.0.0'
