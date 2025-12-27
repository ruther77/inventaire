"""Utilitaires pour normaliser les lignes de panier.

Basé sur /home/ruuuzer/Documents/monprojet/core/cart_normalizer.py.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

FIELD_ALIASES: dict[str, str] = {
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
}

REQUIRED_DEFAULTS: dict[str, Any] = {
    "id": None,
    "nom": "",
    "qty": 0.0,
    "prix_vente": 0.0,
    "tva": 0.0,
    "prix_total": 0.0,
}


def _coerce_float(value: Any, *, default: float = 0.0) -> float:
    """Conversion au mieux des valeurs numériques vers un float."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        text = str(value)
    except Exception:
        return default
    text = text.strip()
    if not text:
        return default
    for token in ("EUR", "eur", "\u20ac", " ", " "):
        text = text.replace(token, "")
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return default


def _coerce_int(value: Any) -> Any:
    """Convertit en int quand possible en conservant les valeurs non coercibles."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(float(str(value)))
    except Exception:
        return value


def normalize_cart_rows(
    cart: Iterable[Mapping[str, Any] | None],
    *,
    field_aliases: dict[str, str] | None = None,
    required_defaults: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Retourne une liste normalisée de lignes panier prêtes à être stockées."""
    aliases = field_aliases or FIELD_ALIASES
    defaults = required_defaults or REQUIRED_DEFAULTS
    normalized: list[dict[str, Any]] = []

    for raw_row in cart or []:
        if not isinstance(raw_row, Mapping):
            continue

        canonical: dict[str, Any] = {}
        for key, value in raw_row.items():
            canonical_key = aliases.get(key, key)
            canonical[canonical_key] = value

        if "id" in canonical:
            canonical["id"] = _coerce_int(canonical.get("id"))
        elif "id" in raw_row:
            canonical["id"] = _coerce_int(raw_row.get("id"))
        else:
            canonical.setdefault("id", None)

        qty_value = canonical.get("qty", raw_row.get("qty"))
        qty = max(_coerce_float(qty_value, default=0.0), 0.0)
        canonical["qty"] = qty

        price_value = canonical.get("prix_vente", raw_row.get("prix_vente"))
        canonical["prix_vente"] = max(_coerce_float(price_value, default=0.0), 0.0)

        tva_value = canonical.get("tva", raw_row.get("tva"))
        canonical["tva"] = max(_coerce_float(tva_value, default=0.0), 0.0)

        name_value = (
            canonical.get("nom")
            or raw_row.get("nom")
            or raw_row.get("name")
            or raw_row.get("product_name")
            or raw_row.get("designation")
            or raw_row.get("libelle")
        )
        if name_value is None and canonical.get("id") is not None:
            name_value = f"Produit {canonical['id']}"
        canonical["nom"] = str(name_value) if name_value is not None else ""

        canonical["prix_total"] = round(canonical["prix_vente"] * canonical["qty"], 4)

        for key, default_value in defaults.items():
            canonical.setdefault(key, default_value)

        normalized.append(canonical)

    return normalized


__all__ = ["normalize_cart_rows", "FIELD_ALIASES", "REQUIRED_DEFAULTS"]
