from __future__ import annotations  # Active les annotations différées

"""Chargement des produits à partir de factures/extracteurs.

Le service scrute les lignes extraites (nom, code, quantités, prix, TVA) et :
1. Découvre si un produit existe déjà (code-barres, nom).
2. Met à jour les champs financiers (prix d'achat, prix de vente, marges).
3. Maintient la table produits_barcodes (insert/update).
4. Optionnellement, crée un mouvement d’init stock.
Les erreurs sont collectées dans un résumé renvoyé à l’API invoices."""

from typing import Any, Dict, List, Mapping, Sequence  # Types utilitaires

import io  # Buffers en mémoire pour CSV rejeté
import math  # Utilitaires math (NaN)
import re  # Expressions régulières pour nettoyage
import unicodedata  # Normalisation Unicode
from pathlib import Path  # Gestion de chemins

import pandas as pd  # DataFrame pour les imports
from sqlalchemy import exc as sa_exc, text  # Exceptions SQLAlchemy et SQL textuel
from sqlalchemy.engine import Connection  # Type de connexion SQLAlchemy

from .invoice_extractor import DEFAULT_TVA_CODE_MAP  # Mapping codes TVA par défaut
from .data_repository import get_engine  # Récupération du moteur SQL

ALCOHOL_KEYWORDS = [
    "biere",
    "bière",
    "beer",
    "vin",
    "whisky",
    "rhum",
    "vodka",
    "liqueur",
    "champagne",
    "cidre",
    "tequila",
    "gin",
    "pastis",
    "cognac",
    "armagnac",
    "porto",
]  # Mots clés pour détecter l'alcool

DEFAULT_MARGIN_RATE = 0.40  # Marge par défaut 40 %
PRICE_DELTA_THRESHOLD = 0.10  # Seuil de variation prix significative


def _empty_summary(rows_received: int = 0) -> Dict[str, Any]:
    return {
        "rows_received": rows_received,  # Lignes reçues
        "rows_processed": 0,  # Lignes traitées
        "created": 0,  # Produits créés
        "updated": 0,  # Produits mis à jour
        "stock_initialized": 0,  # Stocks initialisés
        "barcode": {"added": 0, "conflicts": 0, "skipped": 0},  # Statistiques codes-barres
        "errors": [],  # Erreurs rencontrées
        "rejected_rows": [],  # Lignes rejetées
        "rejected_csv": None,  # CSV des rejets
    }


def _normalize_barcode(value: str | None) -> str:
    if value is None:  # Valeur absente
        return ""  # Retourne chaîne vide
    text_value = str(value)  # Convertit en chaîne
    digits = re.sub(r"\D", "", text_value)  # Garde uniquement les chiffres
    if 8 <= len(digits) <= 15:  # Longueur standard EAN/UPC
        return digits  # Retourne la version digits-only
    return re.sub(r"\s+", "", text_value).upper()  # Nettoie espaces et majuscules


def _normalize_name(value: str | None) -> str:
    if value is None:  # Aucun nom
        return ""  # Retourne vide
    normalized = unicodedata.normalize("NFKC", str(value))  # Normalise Unicode
    normalized = normalized.replace("’", "'")  # Remplace apostrophe typographique
    normalized = re.sub(r"\s+", " ", normalized)  # Compacte les espaces
    return normalized.strip()  # Supprime bords


def _to_float(value: Any, default: float | None = 0.0) -> float | None:
    if value is None:  # Absence de valeur
        return default  # Retourne défaut

    if isinstance(value, (int, float)):  # Si déjà numérique
        numeric = float(value)  # Conversion en float
        if math.isnan(numeric):  # Si NaN
            return default  # Retourne défaut
        return numeric  # Retourne la valeur

    if isinstance(value, str):  # Si chaîne
        cleaned = (
            value.replace("\xa0", " ")  # Remplace espace insécable
            .replace("€", "")  # Supprime symbole euro
            .replace("EUR", "")  # Supprime devise
            .replace("%", "")  # Supprime pourcentage
            .replace(",", ".")  # Remplace virgule
            .strip()  # Trim
        )
        cleaned = re.sub(r"[^\d\.\-]", "", cleaned)  # Retire tout caractère non numérique
        if not cleaned:  # Si vide
            return default  # Retourne défaut
        try:
            return float(cleaned)  # Conversion en float
        except ValueError:
            return default  # Défaut en cas d'erreur

    try:
        return float(value)  # type: ignore[arg-type]  # Essaye de caster en float
    except (TypeError, ValueError):
        return default  # Défaut en cas d'échec


def insert_or_update_barcode(
    conn: Connection,
    produit_id: int,
    barcode: str,
    tenant_id: float | int | None = None,
) -> str:
    """Insère un code-barres et renvoie *added*, *skipped* ou *conflict*."""  # Docstring action code-barres

    # On vérifie d’abord si le code existe déjà pour un produit différent.
    # Cela protège contre l'écrasement d'un code partagé par deux produits.

    normalized = _normalize_barcode(barcode)  # Code nettoyé
    if not normalized:  # Si vide
        return "skipped"  # On ignore

    existing = conn.execute(
        text(
            """
            SELECT produit_id
            FROM produits_barcodes
            WHERE lower(code) = lower(:code)
            LIMIT 1
            """
        ),
        {"code": normalized},
    ).fetchone()  # Cherche un code existant

    if existing:  # Si un code existe
        return "skipped" if int(existing.produit_id) == int(produit_id) else "conflict"  # Conflit ou ignoré

    if tenant_id is None:  # Si tenant non fourni
        tenant_row = conn.execute(
            text("SELECT tenant_id FROM produits WHERE id = :pid"),
            {"pid": produit_id},
        ).fetchone()  # Récupère le tenant du produit
        tenant_id = tenant_row.tenant_id if tenant_row else 1  # Par défaut 1

    conn.execute(
        text(
            """
            INSERT INTO produits_barcodes (produit_id, tenant_id, code)
            VALUES (:pid, :tenant_id, :code)
            """
        ),
        {"pid": produit_id, "tenant_id": tenant_id, "code": normalized},
    )  # Insert le nouveau code-barres
    return "added"  # Indique l'ajout


def exec_sql_return_id_with_conn(conn: Connection, sql: str, params=None):
    """Exécute une requête SQL et retourne l'ID (colonne 0) en utilisant une connexion ouverte."""  # Docstring helper SQL

    result = conn.execute(text(sql), params)  # Exécute la requête
    row = result.fetchone()  # Récupère la première ligne
    return row[0] if row else None  # Retourne la première colonne


def determine_categorie(nom_produit: Any) -> str:
    """Détermine la catégorie à partir du nom du produit."""  # Docstring catégorisation simple

    nom = str(nom_produit).upper()  # Nom en majuscules
    if any(k.upper() in nom for k in ALCOHOL_KEYWORDS):  # Si mot-clé alcool
        return "Alcool"  # Catégorie alcool
    if any(keyword in nom for keyword in ["JUS", "BOISSON", "EAU", "SODA"]):  # Mots boisson
        return "Boissons"  # Catégorie boissons
    if any(keyword in nom for keyword in ["HYGIENE", "SAVON", "SHAMPOOING"]):  # Hygiène
        return "Hygiene"  # Catégorie hygiène
    if any(keyword in nom for keyword in ["AFRIQUE", "YASSA", "TIÈB", "TIEB"]):  # Spécifique Afrique
        return "Afrique"  # Catégorie Afrique
    return "Autre"  # Catégorie par défaut


def create_initial_stock(
    conn: Connection,
    produit_id: int,
    quantite: float,
    *,
    source: str = "Inventaire Initial",
    tenant_id: int = 1,
) -> bool:
    """Insère un mouvement de stock positif et renvoie ``True`` s'il est créé."""  # Docstring stock initial

    try:
        qty = float(quantite)  # Convertit en float
    except (TypeError, ValueError):
        return False  # Échec de conversion

    if qty <= 0:  # Quantité non positive
        return False  # N'insère rien

    sql = text(
        """
        INSERT INTO mouvements_stock (produit_id, type, quantite, source, tenant_id)
        VALUES (:produit_id, 'ENTREE', :quantite, :source, :tenant_id)
        """
    )  # Requête d'insertion mouvement d'entrée
    conn.execute(
        sql,
        {"produit_id": produit_id, "quantite": qty, "source": source, "tenant_id": int(tenant_id)},
    )  # Exécute l'insertion
    return True  # Indique succès


def _find_existing_product_by_barcode(
    conn: Connection,
    codes: List[str],
    *,
    tenant_id: int = 1,
) -> tuple[int | None, str | None]:
    """Recherche un produit par ses codes-barres et renvoie l'ID et le code associé."""  # Docstring recherche code

    # Utilisée avant de créer un produit pour éviter les doublons de référence.

    for code in codes:  # Parcourt les codes candidats
        normalized = (code or "").strip()  # Nettoie
        if not normalized:  # Si vide
            continue  # Ignore

        row = conn.execute(
            text(
                """
                SELECT produit_id
                FROM produits_barcodes
                WHERE lower(code) = lower(:code)
                  AND tenant_id = :tenant_id
                LIMIT 1
                """
            ),
            {"code": normalized, "tenant_id": int(tenant_id)},
        ).fetchone()  # Cherche un produit via code

        if row:  # Si trouvé
            if hasattr(row, "produit_id"):  # Selon type de ligne
                produit_id = getattr(row, "produit_id")  # Accès attr
            elif isinstance(row, dict):  # Dict
                produit_id = row.get("produit_id")  # Accès clé
            else:
                produit_id = row[0]  # Tuple/list
            if produit_id is not None:  # Si ID valide
                return int(produit_id), normalized  # Retourne l'ID et le code

    return None, None  # Aucun produit trouvé


def _clean_codes(raw_codes: Any) -> List[str]:
    if raw_codes is None:  # Si pas de codes
        return []  # Retourne liste vide

    if isinstance(raw_codes, list):  # Si déjà liste
        iterator = raw_codes  # Utilise tel quel
    else:
        iterator = str(raw_codes).replace("\n", " ").split(";")  # Transforme la chaîne en liste

    cleaned: List[str] = []  # Liste des codes nettoyés
    for chunk in iterator:  # Parcourt chaque segment
        raw = str(chunk).replace(",", " ")  # Remplace virgule par espace
        for item in raw.split():  # Découpe par espace
            code = _normalize_barcode(item.strip())  # Normalise
            if code:  # Si code valide
                cleaned.append(code)  # Ajoute à la liste
    return cleaned  # Retourne les codes nettoyés


def _row_as_dict(row: Any, columns: Sequence[str]) -> Dict[str, Any]:
    if row is None:  # Ligne vide
        return {}  # Retourne dict vide
    if hasattr(row, "_mapping"):  # RowMapping SQLAlchemy
        return dict(row._mapping)  # Convertit en dict
    if isinstance(row, Mapping):  # Déjà un mapping
        return dict(row)  # Retourne dict

    result: Dict[str, Any] = {}  # Dictionnaire résultat
    for index, column in enumerate(columns):  # Parcourt les colonnes attendues
        if hasattr(row, column):  # Si attribut présent
            result[column] = getattr(row, column)  # Ajoute au dict
        else:
            try:
                result[column] = row[index]  # Essaye via index
            except (IndexError, TypeError):
                continue  # Ignore si pas accessible
    return result  # Retourne le dict final


def _fetch_product_snapshot(conn: Connection, produit_id: int | None, *, tenant_id: int = 1) -> Dict[str, Any]:
    if produit_id in (None, ""):  # Si identifiant invalide
        return {}  # Retourne dict vide
    row = conn.execute(
        text(
            """
            SELECT id, prix_achat, prix_vente, categorie
            FROM produits
            WHERE id = :pid AND tenant_id = :tenant_id
            LIMIT 1
            """
        ),
        {"pid": int(produit_id), "tenant_id": int(tenant_id)},
    ).fetchone()  # Récupère un snapshot produit
    return _row_as_dict(row, ["id", "prix_achat", "prix_vente", "categorie"])  # Convertit en dict


def _fetch_product_by_name(conn: Connection, nom: str, *, tenant_id: int = 1) -> Dict[str, Any]:
    cleaned = _normalize_name(nom)  # Nom normalisé
    if not cleaned:  # Si vide
        return {}  # Retourne dict vide
    row = conn.execute(
        text(
            """
            SELECT id, prix_achat, prix_vente, categorie
            FROM produits
            WHERE lower(nom) = lower(:nom)
              AND tenant_id = :tenant_id
            LIMIT 1
            """
        ),
        {"nom": cleaned, "tenant_id": int(tenant_id)},
    ).fetchone()  # Cherche par nom exact
    return _row_as_dict(row, ["id", "prix_achat", "prix_vente", "categorie"])  # Retourne snapshot


def _apply_margin(purchase: float | None, sale_candidate: float | None, *, margin: float) -> float | None:
    if purchase is None:  # Pas de prix d'achat
        return sale_candidate  # Retourne le candidat
    baseline = round(float(purchase) * (1.0 + margin), 2)  # Calcule prix avec marge
    if sale_candidate is None:  # Aucun prix de vente proposé
        return baseline  # Utilise baseline
    return round(sale_candidate if sale_candidate >= baseline else baseline, 2)  # Choisit le max


def _has_significant_delta(old: Any, new: Any, *, threshold: float) -> bool:
    new_value = _to_float(new, default=None)  # Nouveau en float
    if new_value is None:  # Si nouveau absent
        return False  # Pas de delta significatif
    old_value = _to_float(old, default=None)  # Ancien en float
    if old_value is None or abs(old_value) < 1e-9:  # Ancien absent ou quasi nul
        return True  # Considéré comme delta
    diff = abs(new_value - old_value)  # Différence absolue
    if diff < 0.01:  # Variation minime
        return False  # Pas significatif
    return diff / abs(old_value) >= threshold  # Compare au seuil relatif


def _resolve_purchase_price(candidate: float | None, existing: Any) -> float:
    """Détermine le prix d'achat à persister en tenant compte de l'inflation."""  # Docstring prix achat

    # En priorité on prend le nouveau prix d'achat si significativement plus élevé.
    candidate_value = _to_float(candidate, default=None)  # Nouveau prix
    existing_value = _to_float(existing, default=None)  # Ancien prix

    if candidate_value is None or candidate_value <= 0:  # Candidat invalide
        return existing_value or 0.0  # Retourne ancien ou 0
    if existing_value is None or existing_value <= 0:  # Ancien invalide
        return candidate_value  # Retourne candidat

    # Les prix augmentent régulièrement dans les factures METRO : même une hausse
    # minime doit être retenue pour refléter l'inflation.
    if candidate_value > existing_value:  # Hausse
        return candidate_value  # Prend le nouveau prix

    if _has_significant_delta(existing_value, candidate_value, threshold=PRICE_DELTA_THRESHOLD):  # Delta notable
        return candidate_value  # Prend le nouveau prix
    return existing_value  # Sinon conserve l'ancien


def _resolve_sale_price(
    candidate_sale: float | None,
    existing_sale: Any,
    *,
    purchase_price: float,
    tva_rate: float,
    margin: float,
    threshold: float,
    force_when_purchase_increases: bool = False,
) -> float:
    safe_purchase = max(purchase_price, 0.0)  # Prix achat >= 0
    safe_margin = max(margin, 0.0)  # Marge >= 0
    tva_multiplier = 1 + max(tva_rate, 0.0) / 100.0  # Multiplicateur TVA
    baseline_ttc = round(safe_purchase * (1 + safe_margin) * tva_multiplier, 4)  # Prix TTC avec marge minimale
    target_sale = baseline_ttc  # Cible initiale
    candidate_value = _to_float(candidate_sale, default=None)  # Prix vente proposé
    # Pour éviter de baisser les prix, on n’accepte un candidate supérieur au minimum qu’en cas d’augmentation claire.
    if candidate_value is not None and candidate_value > target_sale:  # Si candidat supérieur
        target_sale = candidate_value  # Ajuste la cible
    existing_value = _to_float(existing_sale, default=None)  # Prix vente existant

    if existing_value is None or existing_value <= 0:  # Aucun prix existant
        return target_sale  # Utilise la cible

    if existing_value < baseline_ttc:  # Prix existant sous le minimum
        return max(target_sale, baseline_ttc)  # Remonte au minimum

    if force_when_purchase_increases and target_sale > existing_value:  # Si hausse achat, on force la hausse
        return target_sale  # Utilise la cible

    if _has_significant_delta(existing_value, target_sale, threshold=threshold):  # Variation notable
        return target_sale  # Adopte la nouvelle valeur

    return existing_value  # Sinon conserve l'existant


def _resolve_category(row: Mapping[str, Any], existing: Mapping[str, Any] | None, nom: str) -> str:
    for key in ("categorie", "category", "Categorie", "CAT", "TYPE"):  # Recherche dans plusieurs colonnes
        value = row.get(key) if isinstance(row, Mapping) else None  # Lit la valeur
        if isinstance(value, str) and value.strip():  # Si texte non vide
            return value.strip()  # Retourne la valeur nettoyée

    if existing and existing.get("categorie"):  # Si catégorie existante
        existing_value = existing.get("categorie")  # Récupère la valeur
        if isinstance(existing_value, str) and existing_value.strip():  # Non vide
            return existing_value.strip()  # Retourne

    return determine_categorie(nom)  # Fallback sur détermination par nom


def _resolve_tva_value(row: Mapping[str, Any]) -> float | None:
    raw_value = row.get("tva")  # Tente la colonne tva
    numeric = _to_float(raw_value, default=None)  # Convertit
    if numeric is not None:  # Si conversion ok
        return numeric  # Retourne la valeur

    candidate = row.get("tva_code") or row.get("code_tva") or raw_value  # Fallback code TVA
    if isinstance(candidate, str):  # Si texte
        code = candidate.strip().upper()  # Normalise
        if len(code) == 1 and code in DEFAULT_TVA_CODE_MAP:  # Code court
            return float(DEFAULT_TVA_CODE_MAP[code])  # Retourne le mapping
    return None  # Aucun taux trouvé


def load_products_from_df(
    df: pd.DataFrame,
    *,
    initialize_stock: bool = True,
    tenant_id: int = 1,
) -> Dict[str, Any]:
    """Charge les produits à partir d'un DataFrame et retourne un résumé détaillé."""  # Docstring import produits

    # Étapes :
    # 1. Normalisation (nom, codes, prix, TVA, seuil, quantités).
    # 2. Détection : soit par code-barres existants, soit par nom exact.
    # 3. Application des règles de marge et catégories.
    # 4. Insertion/MAJ produits + codes.
    # 5. Optionnel : création d’un mouvement de stock initial (`initialize_stock`).

    summary = _empty_summary(rows_received=int(len(df)))  # Initialisation du résumé

    if df.empty:  # Si DataFrame vide
        return summary  # Retourne le résumé

    engine = get_engine()  # Récupère le moteur SQL
    with engine.begin() as conn:  # Démarre une transaction
        for idx, row in df.iterrows():  # Parcourt chaque ligne
            summary["rows_processed"] += 1  # Incrémente le compteur
            nom = _normalize_name(row.get("nom", ""))  # Nom normalisé

            try:
                # --- Normalisation des entrées minimales (nom, prix, TVA, seuils, quantités) ---
                if not nom:  # Nom manquant
                    raise ValueError("Nom du produit manquant")  # Erreur

                raw_purchase = _to_float(row.get("prix_achat"), default=None)  # Prix achat candidat
                raw_sale = _to_float(row.get("prix_vente"), default=None)  # Prix vente candidat

                tva = _resolve_tva_value(row)  # Taux de TVA
                if tva is None:  # TVA absente
                    raise ValueError("TVA manquante ou invalide")  # Erreur

                seuil_alerte = _to_float(
                    row.get("seuil_alerte_defaut", row.get("seuil_alerte")),
                    default=0.0,
                ) or 0.0  # Seuil d'alerte
                qte_init = _to_float(
                    row.get("quantite_initiale", row.get("qte_init")),
                    default=0.0,
                ) or 0.0  # Quantité initiale
                code_candidates = (
                    row.get("codes")
                    or row.get("codes_barres")
                    or row.get("EAN")
                    or row.get("ean")
                    or row.get("ean13")
                    or row.get("EAN13")
                    or row.get("code_ean")
                    or row.get("CodeEAN")
                )  # Recherche des colonnes de codes
                codes_list = _clean_codes(code_candidates)  # Normalise les codes

                # --- Identification du produit : barcodes en priorité, puis fallback sur le nom exact ---
                produit_id: int | None = None  # ID produit éventuel
                matched_code: str | None = None  # Code ayant servi à matcher
                existing_snapshot: Dict[str, Any] | None = None  # Snapshot existant
                if codes_list:  # Si des codes sont fournis
                    produit_id, matched_code = _find_existing_product_by_barcode(
                        conn,
                        codes_list,
                        tenant_id=tenant_id,
                    )  # Recherche par code
                    existing_snapshot = _fetch_product_snapshot(conn, produit_id, tenant_id=tenant_id)  # Snapshot actuel

                if produit_id is None:  # Si aucun produit via code
                    snapshot_by_name = _fetch_product_by_name(conn, nom, tenant_id=tenant_id)  # Cherche par nom
                    if snapshot_by_name.get("id") is not None:  # Si trouvé
                        produit_id = int(snapshot_by_name.get("id"))  # Récupère l'ID
                        existing_snapshot = snapshot_by_name  # Utilise ce snapshot

                # --- Construction/ajustement des attributs métier (catégorie, prix achat/vente, marge, seuils) ---
                categorie = _resolve_category(row, existing_snapshot, nom)  # Catégorie retenue

                existing_purchase = (existing_snapshot or {}).get("prix_achat")  # Prix achat existant
                purchase_price = _resolve_purchase_price(
                    raw_purchase, existing_purchase
                )  # Prix achat final
                existing_purchase_value = _to_float(existing_purchase, default=None)  # Ancien prix achat en float
                purchase_increased = (
                    existing_purchase_value is not None
                    and purchase_price is not None
                    and purchase_price > existing_purchase_value
                )  # Indique une hausse

                sale_price = _resolve_sale_price(
                    raw_sale,
                    (existing_snapshot or {}).get("prix_vente"),
                    purchase_price=purchase_price,
                    tva_rate=tva,
                    margin=DEFAULT_MARGIN_RATE,
                    threshold=PRICE_DELTA_THRESHOLD,
                    force_when_purchase_increases=purchase_increased,
                )  # Prix vente final

                purchase_price = round(float(purchase_price), 2) if purchase_price is not None else 0.0  # Arrondi achat
                sale_price = round(float(sale_price), 2) if sale_price is not None else 0.0  # Arrondi vente

                params_common = {
                    "prix_achat": purchase_price,
                    "prix_vente": sale_price,
                    "tva": tva,
                    "seuil_alerte": seuil_alerte,
                    "categorie": categorie,
                }  # Paramètres communs d'update/insert

                created_new = False  # Flag création

                if produit_id is not None:  # Si produit existant
                    conn.execute(
                        text(
                            """
                            UPDATE produits
                            SET prix_achat = :prix_achat,
                                prix_vente = :prix_vente,
                                tva = :tva,
                                seuil_alerte = :seuil_alerte,
                                categorie = :categorie,
                                updated_at = now()
                            WHERE id = :pid AND tenant_id = :tenant_id
                            """
                        ),
                        {**params_common, "pid": produit_id, "tenant_id": int(tenant_id)},
                    )  # Met à jour le produit
                    summary["updated"] += 1  # Incrémente compteur mise à jour
                else:  # Sinon créer le produit
                    params_with_name = {"nom": nom, **params_common}  # Paramètres avec nom
                    insert_result = conn.execute(
                        text(
                            """
                            INSERT INTO produits (
                                nom,
                                prix_achat,
                                prix_vente,
                                tva,
                                seuil_alerte,
                                categorie,
                                tenant_id
                            )
                            VALUES (:nom, :prix_achat, :prix_vente, :tva, :seuil_alerte, :categorie, :tenant_id)
                            RETURNING id
                            """
                        ),
                        {**params_with_name, "tenant_id": int(tenant_id)},
                    )  # Insertion

                    inserted_row = insert_result.fetchone()  # Récupère la ligne insérée
                    if inserted_row is None:  # Sécurité ID absent
                        raise RuntimeError("Insertion du produit sans ID retourné")  # Erreur
                    inserted_data = _row_as_dict(inserted_row, ["id"])  # Convertit la ligne
                    inserted_id = inserted_data.get("id")  # ID extrait
                    if inserted_id is None:  # Si ID absent
                        raise RuntimeError("Insertion du produit sans identifiant valide")  # Erreur
                    produit_id = int(inserted_id)  # ID final
                    summary["created"] += 1  # Compte les créations
                    created_new = True  # Marque création

                movement_source = "Import facture"  # Source de mouvement par défaut
                if created_new:  # Si création
                    movement_source = "Import facture - création"  # Label adapté
                elif matched_code:  # Si match par code
                    movement_source = f"Import facture - code {matched_code}"  # Label contextualisé

                if initialize_stock and produit_id is not None and create_initial_stock(
                    conn,
                    produit_id,
                    qte_init,
                    source=movement_source,
                    tenant_id=tenant_id,
                ):  # Crée éventuellement le stock initial
                    summary["stock_initialized"] += 1  # Incrémente le compteur

                for code in codes_list:  # Parcourt les codes normalisés
                    try:
                        status = insert_or_update_barcode(
                            conn,
                            produit_id,
                            code,
                            tenant_id=tenant_id,
                        )  # Insère ou met à jour le code-barres
                    except sa_exc.IntegrityError:  # Conflit DB
                        summary["barcode"]["conflicts"] += 1  # Note le conflit
                    except Exception:  # Autres erreurs
                        summary["barcode"]["skipped"] += 1  # Note le skip
                        raise  # Propagation
                    else:
                        if status == "added":  # Code ajouté
                            summary["barcode"]["added"] += 1  # Incrémente ajout
                        elif status == "conflict":  # Conflit détecté
                            summary["barcode"]["conflicts"] += 1  # Incrémente conflits
                        else:  # Sinon skip
                            summary["barcode"]["skipped"] += 1  # Incrémente skip

            except Exception as exc:  # Gestion des erreurs par ligne
                summary["errors"].append(
                    {
                        "ligne": int(idx) + 2,  # 1-based index + header
                        "nom": nom or "<inconnu>",
                        "erreur": str(exc),
                    }
                )  # Enregistre l'erreur
                try:
                    summary["rejected_rows"].append(row.to_dict())  # Ajoute la ligne rejetée
                except Exception:
                    summary["rejected_rows"].append({"nom": nom or "<inconnu>"})  # Fallback simple
    if summary["rejected_rows"]:  # Si des rejets existent
        try:
            rejected_df = pd.DataFrame(summary["rejected_rows"])  # DataFrame des rejets
            buffer = io.StringIO()  # Buffer CSV
            rejected_df.to_csv(buffer, index=False)  # Écrit le CSV
            summary["rejected_csv"] = buffer.getvalue()  # Stocke le contenu
        except Exception:
            summary["rejected_csv"] = None  # En cas d'échec

    return summary  # Retourne le résumé global


def process_products_file(csv_path: str) -> Dict[str, Any]:
    """Lit un fichier CSV puis délègue le traitement à :func:`load_products_from_df`."""  # Docstring traitement fichier

    try:
        df = pd.read_csv(csv_path)  # Lit le CSV
    except FileNotFoundError:
        summary = _empty_summary()  # Résumé vide
        summary["errors"].append(
            {"ligne": 0, "nom": "", "erreur": f"Fichier introuvable: {csv_path}"}
        )  # Ajoute erreur
        return summary  # Retourne
    except Exception as exc:
        summary = _empty_summary()  # Résumé vide
        summary["errors"].append(
            {"ligne": 0, "nom": "", "erreur": str(exc)}
        )  # Ajoute erreur
        return summary  # Retourne

    return load_products_from_df(df)  # Délègue au chargement DataFrame


if __name__ == "__main__":  # Exécution directe
    import sys  # Accès aux arguments CLI

    default_csv = Path("docs/invoices/Produit.csv")  # Chemin par défaut
    csv_source = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else default_csv  # Source choisie
    results = process_products_file(str(csv_source))  # Lance le traitement

    print("--- RÉSULTATS DE L'IMPORTATION ---")  # Affiche l'en-tête
    print(
        f"Total de lignes reçues : {results['rows_received']} | "
        f"Traitées : {results['rows_processed']}"
    )  # Statistiques de base
    print(
        f"Produits créés : {results['created']} | "
        f"Mis à jour : {results['updated']}"
    )  # Statistiques produits

    if results["errors"]:  # S'il y a des erreurs
        print(f"\n🚨 {len(results['errors'])} erreur(s) rencontrée(s) lors de l'import.")  # Avertissement
        for error in results["errors"][:5]:  # Affiche les premières erreurs
            print(f"  Ligne {error['ligne']} ({error['nom']}): {error['erreur']}")  # Détail
    else:
        print("✅ Importation terminée sans erreur bloquante.")  # Succès
