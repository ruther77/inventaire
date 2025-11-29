"""Utilities to normalise shopping cart rows used by the Streamlit app."""  # Docstring décrivant l'utilitaire de normalisation
from __future__ import annotations  # Active les annotations différées

from typing import Any, Iterable, Mapping  # Import des types pour les annotations

_FIELD_ALIASES: dict[str, str] = {
    "product_id": "id",
    "productId": "id",
    "pid": "id",
    "article_id": "id",
    "code": "id",
    "name": "nom",
    "product_name": "nom",
    "libelle": "nom",
    "designation": "nom",
    "quantity": "qty",
    "quantite": "qty",
    "quantité": "qty",
    "qty": "qty",
    "qte": "qty",
    "nombre": "qty",
    "price": "prix_vente",
    "prix": "prix_vente",
    "unit_price": "prix_vente",
    "prix_unitaire": "prix_vente",
    "sale_price": "prix_vente",
    "montant_unitaire": "prix_vente",
    "vat": "tva",
    "tax": "tva",
    "taux_tva": "tva",
    "taxe": "tva",
    "tva": "tva",
    "prix_total": "prix_total",
    "total": "prix_total",
    "total_price": "prix_total",
    "montant": "prix_total",
    "montant_total": "prix_total",
}  # Table de correspondance des noms de champs entrants vers les noms canoniques

_REQUIRED_DEFAULTS: dict[str, Any] = {
    "id": None,
    "nom": "",
    "qty": 0.0,
    "prix_vente": 0.0,
    "tva": 0.0,
    "prix_total": 0.0,
}  # Valeurs par défaut pour s'assurer que tous les champs requis existent


def _coerce_float(value: Any, *, default: float = 0.0) -> float:
    """Best effort conversion of numeric-like values to float."""  # Docstring décrivant la conversion robuste en float
    if value is None:  # Si aucune valeur fournie
        return default  # On renvoie la valeur par défaut
    if isinstance(value, (int, float)):  # Si déjà numérique
        return float(value)  # Conversion simple en float
    try:
        text = str(value)  # Tente de convertir en chaîne
    except Exception:
        return default  # En cas d'échec retourne par défaut
    text = text.strip()  # Supprime les espaces
    if not text:  # Si la chaîne est vide
        return default  # Retourne la valeur par défaut
    for token in ("€", "\xa0", " "):  # Nettoie les symboles monétaires et espaces insécables
        text = text.replace(token, "")  # Remplace chaque token par rien
    text = text.replace(",", ".")  # Remplace la virgule par un point décimal
    try:
        return float(text)  # Convertit en float si possible
    except ValueError:
        return default  # Retourne la valeur par défaut en cas d'erreur


def _coerce_int(value: Any) -> Any:
    """Convert to int when possible while preserving non-coercible values."""  # Docstring décrivant la conversion en int
    if value is None:  # Si aucune valeur
        return None  # Renvoie None
    if isinstance(value, int):  # Si déjà un entier
        return value  # Renvoie tel quel
    try:
        return int(float(str(value)))  # Tente de convertir via float intermédiaire
    except Exception:
        return value  # Si échec, renvoie la valeur originale


def normalize_cart_rows(cart: Iterable[Mapping[str, Any] | None]) -> list[dict[str, Any]]:
    """Return a normalised list of cart rows ready for persistence.

    Args:
        cart: Iterable of dictionaries coming from Streamlit's session state.

    Returns:
        A list of dictionaries with canonical keys (id, nom, qty, prix_vente,
        tva, prix_total) and cleaned numeric values.
    """  # Docstring décrivant la normalisation des lignes de panier
    normalised: list[dict[str, Any]] = []  # Liste de sortie normalisée

    for raw_row in cart or []:  # Parcourt chaque ligne brute ou itérable vide
        if not isinstance(raw_row, Mapping):  # Ignore les entrées non mappables
            continue  # Passe à l'élément suivant

        canonical: dict[str, Any] = {}  # Dictionnaire pour stocker les valeurs canoniques
        for key, value in raw_row.items():  # Parcourt les clés/valeurs brutes
            canonical_key = _FIELD_ALIASES.get(key, key)  # Traduit la clé si alias connu
            canonical[canonical_key] = value  # Stocke la valeur sous la clé canonique

        # Preserve the original identifier if provided
        if "id" in canonical:  # Si un identifiant est déjà présent
            canonical["id"] = _coerce_int(canonical.get("id"))  # Convertit en entier si possible
        elif "id" in raw_row:  # Si la clé id existe seulement dans la ligne brute
            canonical["id"] = _coerce_int(raw_row.get("id"))  # Convertit et stocke
        else:  # Sinon aucun identifiant fourni
            canonical.setdefault("id", None)  # Définit id à None par défaut

        qty_value = canonical.get("qty", raw_row.get("qty"))  # Récupère la quantité fournie
        qty = max(_coerce_float(qty_value, default=0.0), 0.0)  # Convertit en float et force un minimum à 0
        canonical["qty"] = qty  # Enregistre la quantité normalisée

        price_value = canonical.get("prix_vente", raw_row.get("prix_vente"))  # Récupère le prix de vente
        canonical["prix_vente"] = max(_coerce_float(price_value, default=0.0), 0.0)  # Convertit et borne à 0

        tva_value = canonical.get("tva", raw_row.get("tva"))  # Récupère le taux de TVA
        canonical["tva"] = max(_coerce_float(tva_value, default=0.0), 0.0)  # Convertit et borne à 0

        name_value = (
            canonical.get("nom")
            or raw_row.get("nom")
            or raw_row.get("name")
            or raw_row.get("product_name")
            or raw_row.get("designation")
            or raw_row.get("libelle")
        )  # Tente de trouver un libellé via plusieurs clés
        if name_value is None and canonical.get("id") is not None:  # Si pas de nom mais un id existe
            name_value = f"Produit {canonical['id']}"  # Fabrique un nom générique
        canonical["nom"] = str(name_value) if name_value is not None else ""  # Convertit en chaîne ou vide

        canonical["prix_total"] = round(canonical["prix_vente"] * canonical["qty"], 4)  # Calcule le montant total

        for key, default_value in _REQUIRED_DEFAULTS.items():  # Vérifie tous les champs requis
            canonical.setdefault(key, default_value)  # Ajoute la valeur par défaut si manquante

        normalised.append(canonical)  # Ajoute la ligne normalisée à la liste finale

    return normalised  # Renvoie toutes les lignes normalisées


__all__ = ["normalize_cart_rows"]  # Expose la fonction publique du module
