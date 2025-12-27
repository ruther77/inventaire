#!/usr/bin/env python3
"""
Script de préparation et rapprochement de produits pour import en base.

Ce script prend une liste de nouveaux produits (avec prix TTC) et les rapproche
des produits déjà existants en base de données pour éviter les doublons.

Le rapprochement utilise plusieurs niveaux de matching:
1. Match exact sur nom normalisé (ASCII uppercase sans accents)
2. Match exact sur "base_key" (nom sans conditionnements/poids)
3. Match fuzzy sur base_key avec score de similarité
4. Détection des différences de conditionnement (pack 6x1L vs 1L)

Le résultat indique pour chaque produit s'il est nouveau (is_new=True) ou
s'il correspond à un produit existant, avec le score de match et les détails
de conditionnement.

Usage:
    python scripts/catalog/prepare_articles_for_db.py

Fichiers d'entrée:
    - docs/articles_prix_ttc_cond_inclus_clean.csv : Nouveaux produits à importer
      Colonnes attendues: Nom, Prix_TTC
    - db/Produit.csv : Export des produits existants en base
      Colonnes attendues: nom (minimum)

Fichier de sortie:
    - docs/articles_prix_ttc_cond_inclus_prepared.csv : Résultat du rapprochement
      Colonnes: nom_original, nom_clean, prix_ttc, base_key, matched_nom_bdd,
                match_type, match_score, pack_count, pack_size, pack_unit,
                matched_pack_*, packaging_diff, is_new

Variables d'environnement:
    Aucune

Prérequis:
    - pandas
    - Fichiers CSV source et export de la base

Notes:
    - Score < 0.86 ou différence de conditionnement => is_new=True
    - Le matching fuzzy utilise SequenceMatcher de difflib
    - Les conditionnements sont parsés automatiquement (ex: "6X1L", "500G")
"""

import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd


# Configuration des chemins
SOURCE_PATH = Path("docs/articles_prix_ttc_cond_inclus_clean.csv")  # Nouveaux produits
EXISTING_PATH = Path("db/Produit.csv")  # Produits existants en base
OUTPUT_PATH = Path("docs/articles_prix_ttc_cond_inclus_prepared.csv")  # Résultat du rapprochement


def _to_ascii_upper(text: str) -> str:
    """
    Convertit un texte en ASCII uppercase (sans accents).

    Args:
        text (str): Texte source

    Returns:
        str: Texte en majuscules ASCII (ex: "Café" -> "CAFE")
    """
    normalized = unicodedata.normalize("NFKD", str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text.upper()


def clean_label(text: str) -> str:
    """
    Normalise un libellé de produit pour le matching et l'insertion en base.

    Transformations appliquées:
    - Conversion en ASCII uppercase
    - Virgules remplacées par points
    - Suppression des brackets/parenthèses
    - Normalisation des conditionnements (ex: "6 X 1KG" -> "6X1KG")
    - Suppression des caractères non-alphanumériques (sauf points)
    - Normalisation des espaces

    Args:
        text (str): Libellé brut du produit

    Returns:
        str: Libellé normalisé (ex: "Huile d'olive 6x1L" -> "HUILE OLIVE 6X1L")
    """
    label = _to_ascii_upper(text)
    label = label.replace(",", ".")

    # Supprime brackets et parenthèses
    label = re.sub(r"[\[\]{}()]", " ", label)

    # Normalise les conditionnements : "6 X 1.5KG" -> "6X1.5KG"
    label = re.sub(
        r"(\d+)\s*[X]\s*(\d+[.,]?\d*\s*(?:KG|G|CL|L|ML)?)",
        lambda m: f"{m.group(1)}X{m.group(2).replace(' ', '')}",
        label,
    )

    # Ne garde que alphanumériques et points
    label = re.sub(r"[^A-Z0-9.]+", " ", label)

    # Normalise les espaces multiples
    label = re.sub(r"\s+", " ", label).strip()
    return label


def parse_pack(label: str):
    """
    Extrait les informations de conditionnement d'un libellé.

    Détecte les formats:
    - "6X1KG" => (6, 1.0, "KG")
    - "500G" => (1, 500.0, "G")
    - "12X33CL" => (12, 33.0, "CL")

    Args:
        label (str): Libellé normalisé du produit

    Returns:
        Tuple[int | None, float | None, str | None]:
            (nombre_unités, taille_unitaire, unité)
            ou (None, None, None) si pas de conditionnement détecté
    """
    # Format pack: 6X1KG, 12X33CL, etc.
    m = re.search(r"(\d+)[X]\s*(\d+(?:\.\d+)?)(KG|G|L|CL|ML|GR|PCS)", label)
    if m:
        return int(m.group(1)), float(m.group(2)), m.group(3)

    # Format simple: 500G, 1.5L, etc.
    m = re.search(r"(\d+(?:\.\d+)?)(?:\s*)(KG|G|L|CL|ML|GR|PCS)\b", label)
    if m:
        return 1, float(m.group(1)), m.group(2)

    return None, None, None


def base_key(text: str) -> str:
    """
    Génère une clé simplifiée pour le matching (sans conditionnements/tailles).

    Supprime du nom normalisé:
    - Les packs (6X1KG, 12X500G, etc.)
    - Les tailles/poids (1KG, 500G, 33CL, etc.)
    - Les nombres seuls

    Utilisé pour matcher des produits similaires avec conditionnements différents.
    Ex: "HUILE OLIVE 6X1L" et "HUILE OLIVE 1L" ont la même base_key: "HUILE OLIVE"

    Args:
        text (str): Libellé brut du produit

    Returns:
        str: Clé simplifiée pour le matching
    """
    label = clean_label(text)

    # Supprime les packs (6X1KG, 12X500G, etc.)
    label = re.sub(r"\b\d+X\d+[A-Z0-9.]*\b", " ", label)

    # Supprime les tailles/poids (1KG, 500G, 33CL, etc.)
    label = re.sub(r"\b\d+[.,]?\d*(?:KG|G|CL|L|ML)\b", " ", label)

    # Supprime les nombres seuls
    label = re.sub(r"\b\d+[.,]?\d*\b", " ", label)

    # Normalise les espaces
    label = re.sub(r"\s+", " ", label).strip()
    return label


def load_existing() -> pd.DataFrame:
    """
    Charge les produits existants en base et calcule leurs clés de matching.

    Ajoute les colonnes:
    - nom_clean: Nom normalisé
    - base_key: Clé simplifiée (sans conditionnements)
    - pack_count, pack_size, pack_unit: Infos de conditionnement

    Returns:
        pd.DataFrame: Produits existants avec colonnes de matching
    """
    df = pd.read_csv(EXISTING_PATH)
    df["nom_clean"] = df["nom"].map(clean_label)
    df["base_key"] = df["nom"].map(base_key)

    # Parse les conditionnements
    packs = df["nom_clean"].map(parse_pack)
    df[["pack_count", "pack_size", "pack_unit"]] = pd.DataFrame(packs.tolist(), index=df.index)

    return df


def build_token_index(base_series: pd.Series) -> dict[str, set[int]]:
    """
    Construit un index inversé token -> indices de lignes pour accélérer le matching.

    Pour chaque mot dans chaque base_key, crée un mapping vers les indices
    des lignes contenant ce mot. Permet de filtrer rapidement les candidats
    pour le matching fuzzy.

    Args:
        base_series (pd.Series): Série des base_key des produits existants

    Returns:
        dict[str, set[int]]: Index {token: {idx1, idx2, ...}}
    """
    token_index: dict[str, set[int]] = {}
    for idx, value in base_series.items():
        for token in value.split():
            token_index.setdefault(token, set()).add(idx)
    return token_index


def best_fuzzy_match(new_base: str, candidates: set[int], existing_df: pd.DataFrame) -> tuple[int | None, float]:
    """
    Trouve le meilleur match fuzzy parmi les candidats.

    Utilise SequenceMatcher pour calculer un score de similarité entre
    la nouvelle base_key et chaque candidat. Retourne le meilleur match.

    Args:
        new_base (str): base_key du nouveau produit
        candidates (set[int]): Indices des produits candidats pour le match
        existing_df (pd.DataFrame): DataFrame des produits existants

    Returns:
        Tuple[int | None, float]: (index_meilleur_match, score)
            Score entre 0.0 et 1.0 (1.0 = match exact)
    """
    best_idx = None
    best_score = 0.0
    for idx in candidates:
        score = SequenceMatcher(None, new_base, existing_df.at[idx, "base_key"]).ratio()
        if score > best_score:
            best_score = score
            best_idx = idx
    return best_idx, best_score


def prepare():
    """
    Fonction principale : rapproche les nouveaux produits des produits existants.

    Processus:
    1. Charge les nouveaux produits et les produits existants
    2. Construit les index de matching (nom_clean, base_key, tokens)
    3. Pour chaque nouveau produit:
       a. Tente un match exact sur nom_clean
       b. Sinon, tente un match exact sur base_key
       c. Sinon, tente un match fuzzy sur base_key
       d. Compare les conditionnements
       e. Marque comme nouveau si score < 0.86 ou packaging différent
    4. Génère un CSV avec tous les résultats du rapprochement
    """
    # Charge les données
    new_df = pd.read_csv(SOURCE_PATH)
    existing_df = load_existing()

    # Construit les index de lookup pour les matchs exacts
    norm_lookup: dict[str, list[str]] = {}
    base_lookup: dict[str, list[str]] = {}
    for _, row in existing_df.iterrows():
        norm_lookup.setdefault(row["nom_clean"], []).append(row["nom"])
        base_lookup.setdefault(row["base_key"], []).append(row["nom"])

    # Construit l'index de tokens pour le matching fuzzy
    token_index = build_token_index(existing_df["base_key"])

    rows = []
    for _, row in new_df.iterrows():
        raw = row["Nom"]
        price = row["Prix_TTC"]

        # Normalise le nom et extrait la base_key
        nom_clean = clean_label(raw)
        base = base_key(raw)

        # État initial du match
        match_type = "none"
        match_score = 0.0
        matched_nom = ""
        matched_pack = (None, None, None)

        # Niveau 1: Match exact sur nom normalisé
        if nom_clean in norm_lookup:
            match_type = "exact_norm"
            match_score = 1.0
            matched_nom = norm_lookup[nom_clean][0]

        # Niveau 2: Match exact sur base_key (sans conditionnements)
        elif base and base in base_lookup:
            match_type = "exact_base"
            match_score = 1.0
            matched_nom = base_lookup[base][0]

        # Niveau 3: Match fuzzy sur base_key
        elif base:
            # Filtre les candidats par tokens communs
            tokens = base.split()
            candidate_idxs: set[int] = set()
            for token in tokens:
                candidate_idxs.update(token_index.get(token, ()))

            # Si aucun token commun, considère tous les produits (fallback)
            if not candidate_idxs and tokens:
                candidate_idxs = set(range(len(existing_df)))

            if candidate_idxs:
                best_idx, score = best_fuzzy_match(base, candidate_idxs, existing_df)
                if best_idx is not None:
                    match_type = "fuzzy_base"
                    match_score = score
                    matched_nom = existing_df.at[best_idx, "nom"]
                    matched_pack = (
                        existing_df.at[best_idx, "pack_count"],
                        existing_df.at[best_idx, "pack_size"],
                        existing_df.at[best_idx, "pack_unit"],
                    )

        # Parse le conditionnement du nouveau produit
        pack_info = parse_pack(nom_clean)

        # Détecte les différences de conditionnement
        packaging_diff = False
        if match_type != "none" and pack_info != (None, None, None):
            packaging_diff = pack_info != matched_pack

        # Décide si c'est un nouveau produit (seuil de score + packaging)
        is_new = match_score < 0.86 or packaging_diff

        # Enregistre le résultat du rapprochement
        rows.append(
            {
                "nom_original": raw,
                "nom_clean": nom_clean,
                "prix_ttc": price,
                "base_key": base,
                "matched_nom_bdd": matched_nom,
                "match_type": match_type,
                "match_score": round(match_score, 3),
                "pack_count": pack_info[0],
                "pack_size": pack_info[1],
                "pack_unit": pack_info[2],
                "matched_pack_count": matched_pack[0],
                "matched_pack_size": matched_pack[1],
                "matched_pack_unit": matched_pack[2],
                "packaging_diff": packaging_diff,
                "is_new": is_new,
            }
        )

    # Génère le CSV de résultat
    output_df = pd.DataFrame(rows)
    output_df.to_csv(OUTPUT_PATH, index=False)

    # Affiche le résumé
    summary = output_df["is_new"].value_counts()
    print("Fichier genere:", OUTPUT_PATH)
    print("Nouveaux produits potentiels:", int(summary.get(True, 0)))
    print("Correspondances probables:", int(summary.get(False, 0)))


if __name__ == "__main__":
    prepare()
