"""Loader for vendor category mappings maintained in CSV format."""  # Docstring décrivant le chargeur de correspondances de vendeurs

from __future__ import annotations  # Active les annotations différées pour la compatibilité

import csv  # Permet de lire les fichiers CSV
from pathlib import Path  # Manipule les chemins de fichiers de façon portable
from typing import Iterable, Sequence  # Types utilitaires pour les annotations


ROOT_DIR = Path(__file__).resolve().parent.parent  # Répertoire racine du projet
VENDOR_CATEGORY_FILE = ROOT_DIR / "data" / "vendor_category_mapping.csv"  # Chemin du CSV de mapping


def _parse_aliases(raw: str) -> tuple[str, ...]:
    return tuple(alias.strip().upper() for alias in raw.split("|") if alias.strip())  # Normalise et sépare les alias


def _parse_types(raw: str | None) -> tuple[str, ...] | None:
    if not raw:  # Si aucune valeur fournie
        return None  # On renvoie None pour signaler l'absence
    items = tuple(item.strip() for item in raw.split("|") if item.strip())  # Nettoie et sépare les types
    return items or None  # Renvoie la liste ou None si vide


def load_vendor_category_rules() -> tuple[tuple[tuple[str, ...], str, Sequence[str] | None], ...]:
    """Charge la table `data/vendor_category_mapping.csv` pour étendre les règles.

    Chaque tuple (alias, catégorie, types) est fusionné dans `CATEGORY_RULES`
    du module restaurant afin de classer les relevés bancaires."""  # Docstring expliquant l'usage du chargeur
    if not VENDOR_CATEGORY_FILE.exists():  # Si le fichier CSV est absent
        return ()  # Retourne un tuple vide pour éviter les erreurs
    rules: list[tuple[tuple[str, ...], str, Sequence[str] | None]] = []  # Liste mutable pour accumuler les règles
    with VENDOR_CATEGORY_FILE.open(newline="", encoding="utf-8") as csvfile:  # Ouvre le fichier CSV en UTF-8
        reader = csv.DictReader(csvfile)  # Crée un lecteur dict pour accéder aux colonnes par nom
        for row in reader:  # Parcourt chaque ligne du CSV
            aliases = _parse_aliases(row.get("aliases", ""))  # Récupère et normalise les alias
            category = (row.get("category") or "").strip()  # Lit la catégorie en supprimant les espaces
            types = _parse_types(row.get("types"))  # Optionnellement récupère les types supplémentaires
            if not aliases or not category:  # Ignore les lignes incomplètes
                continue  # Passe à l'itération suivante
            rules.append((aliases, category, types))  # Ajoute la règle formatée
    return tuple(rules)  # Transforme la liste en tuple immuable pour l'export
