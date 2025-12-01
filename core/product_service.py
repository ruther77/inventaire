"""Services utilitaires pour la gestion des produits et codes-barres."""  # Docstring du module produit

from __future__ import annotations  # Active les annotations différées

import re  # Expressions régulières pour nettoyer les codes-barres
from typing import Any, Iterable, Mapping  # Types génériques pour annotations

from sqlalchemy import text  # Construction de requêtes SQL textuelles

from .data_repository import get_engine  # Accès au moteur SQL
from . import products_loader  # Utilitaire pour gérer les codes-barres


class ProductServiceError(Exception):
    """Exception de base pour les opérations sur les produits."""  # Docstring décrivant l'exception base


class InvalidBarcodeError(ProductServiceError):
    """Levée lorsqu'un code-barres est absent ou mal formé."""  # Docstring de l'exception code-barres


class ProductNotFoundError(ProductServiceError):
    """Levée lorsqu'un produit n'est pas trouvé en base."""  # Docstring produit introuvable


_ALLOWED_NUMERIC_COLUMNS = {"prix_vente", "prix_achat", "tva", "seuil_alerte"}  # Colonnes numériques autorisées
_ALLOWED_TEXT_COLUMNS = {"nom", "categorie"}  # Colonnes textuelles autorisées
_ALLOWED_BOOL_COLUMNS = {"actif"}  # Colonnes booléennes autorisées
_BARCODE_STATUS_MAP = {"added": "added", "skipped": "skipped", "conflict": "conflicts"}  # Traduction des statuts de loader
_MIN_GTIN_LENGTH = 3  # Longueur minimale des codes acceptés
_MAX_GTIN_LENGTH = 14  # Longueur maximale des codes acceptés


def _canonicalize_barcode(code: str | None) -> str | None:
    if code is None:  # Si aucun code fourni
        return None  # Retourne None

    raw_text = str(code).strip()  # Convertit en chaîne et nettoie les espaces
    if not raw_text:  # Chaîne vide
        return None  # Retourne None

    digits_only = re.sub(r"\D", "", raw_text)  # Retire tous les caractères non numériques
    if not digits_only:  # Si aucun chiffre restant
        return None  # Retourne None

    length = len(digits_only)  # Calcule la longueur du code numérique
    if length < _MIN_GTIN_LENGTH or length > _MAX_GTIN_LENGTH:  # Vérifie la plage autorisée
        return None  # Retourne None si hors plage

    return digits_only  # Retourne le code canonique


def parse_barcode_input(raw_codes: str | Iterable[str] | None) -> list[str]:
    """Normalise une entrée utilisateur en liste de codes-barres uniques."""  # Docstring de la fonction de parsing

    if raw_codes is None:  # Aucun code fourni
        return []  # Renvoie une liste vide

    if isinstance(raw_codes, str):  # Entrée sous forme de chaîne
        parts = re.split(r"[;,\n]+", raw_codes)  # Sépare par ; , ou saut de ligne
    else:  # Entrée itérable
        parts = list(raw_codes)  # Convertit en liste

    results: list[str] = []  # Liste des codes uniques
    seen: set[str] = set()  # Ensemble pour dédoublonnage insensible à la casse

    for part in parts:  # Parcourt chaque fragment
        canonical = _canonicalize_barcode(part)  # Canonise le code
        if not canonical:  # Ignore les codes invalides
            continue  # Passe au suivant
        key = canonical.lower()  # Clé normalisée pour dédoublonnage
        if key in seen:  # Déjà rencontré
            continue  # Passe au suivant
        seen.add(key)  # Marque le code comme vu
        results.append(canonical)  # Ajoute le code canonique

    return results  # Renvoie la liste unique


def _coerce_numeric(value: Any) -> float | None:
    if value in (None, ""):  # Valeurs vides
        return None  # Retourne None
    try:
        return float(value)  # Convertit en float
    except (TypeError, ValueError) as exc:  # pragma: no cover - message enrichi pour l'appelant
        raise ValueError(f"Valeur numérique invalide: {value!r}") from exc  # Propage avec message explicite


def _coerce_text(value: Any, *, field: str) -> str:
    cleaned = str(value or "").strip()  # Convertit en chaîne et enlève les espaces
    if not cleaned:  # Si vide après nettoyage
        raise ValueError(f"La colonne '{field}' ne peut pas être vide.")  # Erreur explicite
    return cleaned  # Renvoie la chaîne nettoyée


def _coerce_bool(value: Any) -> bool | None:
    if value in (None, ""):  # Valeurs vides
        return None  # Renvoie None
    if isinstance(value, bool):  # Déjà booléen
        return value  # Renvoie tel quel
    if isinstance(value, (int, float)):  # Numérique
        return bool(value)  # Convertit en booléen
    if isinstance(value, str):  # Chaîne à interpréter
        lowered = value.strip().lower()  # Nettoie et met en minuscule
        if lowered in {"true", "1", "oui", "on", "actif", "yes"}:  # Valeurs positives
            return True  # Renvoie True
        if lowered in {"false", "0", "non", "off", "inactif", "no"}:  # Valeurs négatives
            return False  # Renvoie False
    raise ValueError(f"Valeur booléenne invalide: {value!r}")  # Erreur si non convertible


def update_catalog_entry(
    product_id: int,
    field_changes: Mapping[str, Any] | None,
    barcode_field: str | Iterable[str] | None = None,
    *,
    tenant_id: int = 1,
) -> dict[str, Any]:
    """Applique les modifications du tableau catalogue à un produit donné."""  # Docstring de mise à jour catalogue

    # Flux : validation -> update champs numériques/textuels -> synchronisation codes-barres.

    try:
        pid = int(product_id)  # Convertit l'identifiant en entier
    except (TypeError, ValueError) as exc:  # Capture les conversions invalides
        raise ValueError("Identifiant de produit invalide.") from exc  # Renvoie une erreur claire

    sanitized_updates: dict[str, Any] = {}  # Dictionnaire des champs à mettre à jour
    if field_changes:  # Si des changements sont fournis
        for column, value in field_changes.items():  # Parcourt chaque champ modifié
            if column in _ALLOWED_NUMERIC_COLUMNS:  # Colonne numérique autorisée
                sanitized_updates[column] = _coerce_numeric(value)  # Convertit en float ou None
            elif column in _ALLOWED_TEXT_COLUMNS:  # Colonne texte autorisée
                sanitized_updates[column] = _coerce_text(value, field=column)  # Nettoie la chaîne
            elif column in _ALLOWED_BOOL_COLUMNS:  # Colonne booléenne autorisée
                sanitized_updates[column] = _coerce_bool(value)  # Convertit en booléen

    engine = get_engine()  # Récupère l'engine SQLAlchemy
    with engine.begin() as conn:  # Ouvre une transaction
        exists = conn.execute(
            text("SELECT 1 FROM produits WHERE id = :pid AND tenant_id = :tenant_id"),
            {"pid": pid, "tenant_id": tenant_id},
        ).scalar()  # Vérifie l'existence du produit
        if not exists:  # Si le produit est absent
            raise ProductNotFoundError(f"Produit ID {pid} introuvable.")  # Erreur explicite

        fields_updated = 0  # Compteur de champs mis à jour
        if sanitized_updates:  # S'il y a des changements
            set_clause = ", ".join(f"{col} = :{col}" for col in sanitized_updates)  # Construit la clause SET
            params = dict(sanitized_updates)  # Copie des paramètres
            params["pid"] = pid  # Ajoute l'identifiant
            params["tenant_id"] = tenant_id  # Ajoute le tenant
            conn.execute(
                text(f"UPDATE produits SET {set_clause} WHERE id = :pid AND tenant_id = :tenant_id"),
                params,
            )  # Applique la mise à jour
            fields_updated = len(sanitized_updates)  # Met à jour le compteur

        barcode_summary = {"added": 0, "removed": 0, "skipped": 0, "conflicts": 0}  # Statistiques sur les codes-barres

        if barcode_field is not None:  # Si une colonne code-barres est fournie
            desired_codes = parse_barcode_input(barcode_field)  # Normalise la liste souhaitée
            existing_rows = conn.execute(
                text(
                    "SELECT code FROM produits_barcodes WHERE produit_id = :pid AND tenant_id = :tenant_id"
                ),
                {"pid": pid, "tenant_id": tenant_id},
            ).fetchall()  # Récupère les codes existants
            existing_map = {
                _canonicalize_barcode(row[0] if isinstance(row, tuple) else row.code): (
                    row[0] if isinstance(row, tuple) else row.code
                )
                for row in existing_rows
            }  # Mappe codes canoniques vers version stockée
            existing_keys = {code for code in existing_map.keys() if code}  # Ensemble des codes existants
            desired_keys = {code for code in desired_codes if code}  # Ensemble des codes souhaités

            to_remove = existing_keys - desired_keys  # Codes à supprimer
            to_add = desired_keys - existing_keys  # Codes à ajouter

            for canonical in to_remove:  # Parcourt les codes à retirer
                stored_code = existing_map.get(canonical)  # Récupère la version stockée
                if not stored_code:  # Si absent
                    continue  # Passe au suivant
                conn.execute(
                    text(
                        "DELETE FROM produits_barcodes "
                        "WHERE produit_id = :pid AND tenant_id = :tenant_id AND lower(code) = lower(:code)"
                    ),
                    {"pid": pid, "tenant_id": tenant_id, "code": stored_code},
                )  # Supprime le code-barres
                barcode_summary["removed"] += 1  # Incrémente le compteur de suppressions

            for code in desired_codes:  # Parcourt les codes souhaités
                if code not in to_add:  # Ignore ceux déjà présents
                    continue  # Passe au suivant
                status = products_loader.insert_or_update_barcode(
                    conn, pid, code, tenant_id=tenant_id
                )  # Ajoute ou met à jour le code via loader partagé
                summary_key = _BARCODE_STATUS_MAP.get(status)  # Convertit le statut en clé de résumé
                if summary_key:  # Si le statut est reconnu
                    barcode_summary[summary_key] += 1  # Incrémente la statistique

        return {
            "fields_updated": fields_updated,
            "barcodes": barcode_summary,
        }  # Retourne le résumé des mises à jour


def delete_product_by_barcode(raw_code: str | None, *, tenant_id: int = 1) -> dict[str, Any]:
    """Supprime un code-barres (ou le produit entier s'il est unique) pour un tenant donné."""  # Docstring de suppression par code-barres

    # Cette fonction est utile pour les menues opérations “nettoyage” parcourues par l’admin.

    canonical = _canonicalize_barcode(raw_code)  # Canonise le code fourni
    if not canonical:  # Si code invalide
        raise InvalidBarcodeError("Code-barres manquant ou trop court.")  # Erreur explicite

    engine = get_engine()  # Récupère l'engine
    with engine.begin() as conn:  # Ouvre une transaction
        row = conn.execute(
            text(
                """
                SELECT pb.produit_id, p.nom,
                       (
                           SELECT COUNT(*)
                           FROM produits_barcodes
                           WHERE produit_id = pb.produit_id AND tenant_id = :tenant_id
                       ) AS code_count
                FROM produits_barcodes pb
                JOIN produits p ON p.id = pb.produit_id AND p.tenant_id = pb.tenant_id
                WHERE lower(pb.code) = lower(:code) AND pb.tenant_id = :tenant_id
                LIMIT 1
                """
            ),
            {"code": canonical, "tenant_id": int(tenant_id)},
        ).fetchone()  # Cherche le produit associé au code

        if row is None:  # Aucun produit trouvé
            raise ProductNotFoundError(
                f"Aucun produit associé au code-barres {canonical}."
            )  # Erreur explicite

        product_id = int(row.produit_id if hasattr(row, "produit_id") else row[0])  # ID du produit
        product_name = row.nom if hasattr(row, "nom") else row[1]  # Nom du produit
        code_count = int(row.code_count if hasattr(row, "code_count") else row[2])  # Nombre de codes associés

        if code_count > 1:  # Si plusieurs codes liés
            conn.execute(
                text(
                    "DELETE FROM produits_barcodes "
                    "WHERE produit_id = :pid AND tenant_id = :tenant_id AND lower(code) = lower(:code)"
                ),
                {"pid": product_id, "code": canonical, "tenant_id": int(tenant_id)},
            )  # Supprime uniquement ce code-barres
            return {
                "action": "barcode_removed",
                "product_id": product_id,
                "product_name": product_name,
                "removed_code": canonical,
                "remaining_barcodes": code_count - 1,
            }  # Retourne le résumé de suppression de code-barres

        conn.execute(
            text("DELETE FROM produits WHERE id = :pid AND tenant_id = :tenant_id"),
            {"pid": product_id, "tenant_id": int(tenant_id)},
        )  # Supprime le produit complet si un seul code existait
        return {
            "action": "product_deleted",
            "product_id": product_id,
            "product_name": product_name,
            "removed_code": canonical,
            "remaining_barcodes": 0,
        }  # Retourne le résumé de suppression de produit
