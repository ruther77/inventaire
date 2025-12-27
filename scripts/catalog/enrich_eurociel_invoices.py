#!/usr/bin/env python3
"""
Script d'enrichissement des factures Eurociel extraites.

Ce script complète le fichier eurociel_factures_extrait.csv avec des informations
supplémentaires nécessaires à l'importation dans la base de données :
- Code EAN (code-barres) : récupéré depuis la DB si le produit existe, sinon génère
  un placeholder à 5 chiffres basé sur la catégorie (format: préfixe 2 chiffres + compteur 3 chiffres)
- TVA : 20% pour alcools/boissons/hygiène, 5.5% pour alimentaire
- Produit_ID : ID du produit existant en base, ou "NEW" si produit à créer
- Catégorie : classification automatique du produit
- Montant HT calculé : quantité × prix unitaire

Le script gère aussi la normalisation des noms de produits et évite les faux positifs
de catégorisation (ex: "POULET" classé en "Vins" à cause de "L" dans le nom).

Usage:
    python scripts/catalog/enrich_eurociel_invoices.py

Fichiers d'entrée requis:
    - docs/eurociel_factures_extrait.csv : factures extraites par extract_eurociel_invoices.py
      Colonnes attendues: file, invoice, invoice_date, designation, quantity, unit_price
    - docs/db_products_dump.csv : export des produits existants en base
      Format: nom,id,categorie,tva,barcode (sans en-tête)
    - docs/db_placeholder_max.csv : code placeholder maximum par catégorie
      Format: categorie,max_code (ex: "Épicerie sucrée,01042")

Fichier de sortie:
    - docs/eurociel_factures_enriched.csv : factures enrichies prêtes pour l'import
      Colonnes: file, invoice, invoice_date, Produit, EAN, Qté, Reçue, Prix_achat_HT,
                TVA, Produit_ID, Montant_HT_calc, Categorie

Variables d'environnement:
    Aucune (utilise des chemins relatifs au dossier du script)

Prérequis:
    - Fichier eurociel_factures_extrait.csv généré par extract_eurociel_invoices.py
    - Exports de la base de données (db_products_dump.csv, db_placeholder_max.csv)
    - Module scripts.reclassify_products pour les règles de catégorisation

Notes:
    - Les nouveaux produits se voient attribuer un code placeholder unique
    - Les codes placeholder par catégorie sont incrémentés automatiquement
    - Le script gère les catégories manquantes en leur allouant de nouveaux préfixes (25+)
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

import sys

# Configuration des chemins de fichiers
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from scripts.reclassify_products import RULES, normalize_label  # type: ignore

# Chemins des fichiers d'entrée et de sortie
SRC = ROOT / "docs" / "eurociel_factures_extrait.csv"  # Factures extraites (entrée)
DB_PRODUCTS = ROOT / "docs" / "db_products_dump.csv"  # Produits existants en DB (entrée)
DB_PLACEHOLDER_MAX = ROOT / "docs" / "db_placeholder_max.csv"  # Max codes par catégorie (entrée)
OUT = ROOT / "docs" / "eurociel_factures_enriched.csv"  # Factures enrichies (sortie)

# TVA à 20% pour les catégories suivantes (alcools, boissons et hygiène)
# Toutes les autres catégories sont à 5.5% (taux réduit alimentaire)
TVA20 = {
    "Spiritueux",
    "Effervescents / Champagne",
    "Vins rouges",
    "Vins blancs",
    "Vins rosés",
    "Bières",
    "Apéritifs / Fortifiés",
    "Softs / Énergisants",
    "Hygiène / Entretien",
}

# Préfixe de départ pour allouer de nouveaux codes aux catégories manquantes
# Les préfixes 00-24 sont déjà utilisés par les catégories existantes
MISSING_PREFIX_START = 25


def load_db_products() -> Dict[str, Tuple[int, str, float, str | None]]:
    """
    Charge les produits existants en base de données.

    Lit le fichier db_products_dump.csv et construit un dictionnaire permettant
    de retrouver rapidement un produit à partir de son nom normalisé.

    Returns:
        Dict[str, Tuple[int, str, float, str | None]]: Dictionnaire avec pour clé
            le nom normalisé du produit et pour valeur un tuple contenant:
            - id (int): ID du produit en base
            - categorie (str): Catégorie du produit
            - tva (float): Taux de TVA (5.5 ou 20.0)
            - barcode (str | None): Code EAN/barcode principal (ou None si absent)
    """
    mapping: Dict[str, Tuple[int, str, float, str | None]] = {}
    with DB_PRODUCTS.open() as f:
        reader = csv.reader(f)
        for row in reader:
            # Ignore les lignes incomplètes
            if len(row) < 5:
                continue
            nom, pid, cat, tva, barcode = row
            # Normalise le nom pour faciliter les matchs (majuscules, sans accents, etc.)
            key = normalize_label(nom)
            try:
                pid_int = int(pid)
                tva_f = float(tva)
            except ValueError:
                # Ignore les lignes avec des valeurs invalides
                continue
            mapping[key] = (pid_int, cat, tva_f, barcode or None)
    return mapping


def load_placeholder_max():
    """
    Charge les codes placeholder maximum par catégorie.

    Les codes placeholder sont des codes EAN temporaires à 5 chiffres utilisés pour
    les nouveaux produits. Format: 2 chiffres de préfixe (par catégorie) + 3 chiffres
    de compteur séquentiel. Ex: "01042" = catégorie "01", 42ème produit.

    Cette fonction lit le fichier db_placeholder_max.csv qui contient pour chaque
    catégorie le code maximum déjà utilisé, afin de pouvoir continuer la numérotation.

    Returns:
        Tuple[Dict[str, Tuple[str, int]], set[str]]:
            - mapping: Dictionnaire {categorie: (prefix, dernier_compteur_utilise)}
              Ex: {"Épicerie sucrée": ("01", 42)}
            - used_prefixes: Ensemble des préfixes déjà utilisés (pour éviter les doublons)
              Ex: {"01", "02", "03", ...}
    """
    mapping: Dict[str, Tuple[str, int]] = {}
    used_prefixes: set[str] = set()
    with DB_PLACEHOLDER_MAX.open() as f:
        reader = csv.reader(f)
        for cat, max_code in reader:
            # Extrait le préfixe (2 premiers chiffres) et le compteur (3 derniers)
            prefix = max_code[:2]
            used_prefixes.add(prefix)
            try:
                counter = int(max_code[2:])
            except ValueError:
                counter = 0
            mapping[cat] = (prefix, counter)
    return mapping, used_prefixes


def categorize(label: str) -> str:
    """
    Catégorise automatiquement un produit à partir de son libellé.

    Utilise les règles de catégorisation définies dans scripts.reclassify_products
    et applique des corrections pour éviter les faux positifs.

    Args:
        label (str): Libellé normalisé du produit (ex: "POULET FERMIER 1.5KG")

    Returns:
        str: Nom de la catégorie (ex: "Mer / Viandes base", "Épicerie sucrée", etc.)

    Notes:
        - Si aucune règle ne correspond, retourne "Épicerie sucrée" par défaut
        - Corrige les faux positifs : un produit avec un poids (KG/G) classé en "Vins"
          est probablement de la viande ou de l'emballage, pas de l'alcool
    """
    # Applique les règles de catégorisation dans l'ordre
    for rule in RULES:
        if rule.matches(label):
            cat = rule.category
            break
    else:
        # Catégorie par défaut si aucune règle ne correspond
        cat = "Épicerie sucrée"

    # Correction des faux positifs : évite de classer des produits solides en alcools
    # Exemple: "POULET 1.5 L" pourrait matcher "Vins" à cause du "L" (litres)
    alcohol_cats = {
        "Apéritifs / Fortifiés",
        "Effervescents / Champagne",
        "Vins rouges",
        "Vins blancs",
        "Vins rosés",
        "Bières",
        "Spiritueux",
    }
    if cat in alcohol_cats:
        import re

        # Détecte les indicateurs de poids/quantité (KG, G, PCS, X)
        has_weight = bool(re.search(r"\d+\s*(KG|G|PCS?)", label)) or "X" in label
        # Détecte les indicateurs de boissons (CL, L, BOUTEILLE, etc.)
        is_drink = any(token in label for token in ["CL", " L", "LITRE", "VIN", "BIERE", "BEER", "BOITE", "CAN", "BOUT", "BOUTEILLE"])

        # Si le produit a un poids mais pas d'indicateur de boisson, c'est probablement une erreur
        if has_weight and not is_drink:
            # Détecte les mots clés de viande/poisson
            meat_words = ["POULE", "POULET", "VIANDE", "BOEUF", "BEEF", "AGNEAU", "MOUTON", "PORC", "PORK", "SAUMON", "FUMEE", "FUME", "DARNE", "FILET", "TILAPIA", "MAQUEREAU", "CREVETTE", "POISSON"]
            # Détecte les mots clés d'emballage
            packaging_words = ["SACHET", "SAC", "BOITE", "BOX", "PAQUET", "PAQUETS", "PAIRE", "PLATEAU", "BARQUETTE"]

            if any(word in label for word in meat_words):
                cat = "Mer / Viandes base"
            elif any(word in label for word in packaging_words):
                cat = "Emballages / Jetables"
            else:
                cat = "Épicerie sucrée"

    return cat


def infer_tva(cat: str) -> float:
    """
    Détermine le taux de TVA applicable à une catégorie de produit.

    Args:
        cat (str): Nom de la catégorie du produit

    Returns:
        float: Taux de TVA applicable (20.0 ou 5.5)
            - 20.0% pour les alcools, boissons et produits d'hygiène
            - 5.5% pour tous les autres produits (taux réduit alimentaire)
    """
    return 20.0 if cat in TVA20 else 5.5


def main() -> None:
    """
    Fonction principale du script d'enrichissement.

    Processus:
    1. Charge les produits existants et les codes placeholder max
    2. Alloue des préfixes pour les catégories manquantes
    3. Parcourt chaque ligne du fichier d'extraction
    4. Pour chaque produit:
       - Cherche un match exact en base (nom normalisé)
       - Si trouvé: récupère son ID, catégorie, TVA et EAN
       - Si nouveau: génère un code placeholder, infère catégorie et TVA
    5. Écrit le fichier enrichi avec toutes les colonnes complétées
    """
    # Charge les données de référence
    db_products = load_db_products()
    placeholder_map, used_prefixes = load_placeholder_max()

    # Alloue des préfixes pour les catégories qui n'ont pas encore de code placeholder
    # Ces catégories ont été identifiées manuellement comme manquantes
    missing_cats = {
        "Apéritifs / Fortifiés",
        "Effervescents / Champagne",
        "Frais laitier / Fromages",
        "Sauces sucrées cuisine",
    }
    available_prefix = MISSING_PREFIX_START
    for cat in sorted(missing_cats):
        if cat in placeholder_map:
            continue
        # Trouve un préfixe libre (non déjà utilisé)
        while f"{available_prefix:02d}" in used_prefixes:
            available_prefix += 1
        placeholder_map[cat] = (f"{available_prefix:02d}", 0)
        used_prefixes.add(f"{available_prefix:02d}")
        available_prefix += 1

    # Mémoire des nouveaux produits rencontrés lors du traitement
    # Évite de générer plusieurs codes différents pour le même produit
    new_products: Dict[str, Tuple[str, str, float]] = {}  # nom_normalisé -> (code_ean, categorie, tva)

    # Initialise les compteurs de codes pour chaque catégorie
    counters = {cat: counter for cat, (pref, counter) in placeholder_map.items()}

    # Crée le dossier de sortie si nécessaire
    OUT.parent.mkdir(parents=True, exist_ok=True)

    # Ouvre les fichiers d'entrée et de sortie
    with SRC.open() as f_in, OUT.open("w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in, delimiter=";")

        # Définit les colonnes du fichier enrichi de sortie
        fieldnames = [
            "file",              # Nom du fichier PDF source
            "invoice",           # Numéro de facture
            "invoice_date",      # Date de la facture
            "Produit",          # Nom du produit
            "EAN",              # Code EAN/barcode (ou placeholder)
            "Qté",              # Quantité commandée
            "Reçue",            # Quantité reçue (= Qté pour l'instant)
            "Prix_achat_HT",    # Prix unitaire HT
            "TVA",              # Taux de TVA (%)
            "Produit_ID",       # ID du produit en base ou "NEW"
            "Montant_HT_calc",  # Montant total HT calculé
            "Categorie",        # Catégorie du produit
        ]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        # Traite chaque ligne du fichier d'extraction
        for row in reader:
            produit = row["designation"]

            # Parse les valeurs numériques (gère le format français avec virgules)
            qty_s = row["quantity"].replace(",", ".")
            unit_s = row["unit_price"].replace(",", ".") if row.get("unit_price") else ""
            try:
                qty = float(qty_s)
            except ValueError:
                qty = 0.0
            try:
                unit_price = float(unit_s)
            except ValueError:
                unit_price = 0.0

            # Normalise le nom du produit pour le matching
            norm = normalize_label(produit)

            # Cherche le produit dans la base de données existante
            match = db_products.get(norm)
            if match:
                # Produit existant : récupère ses informations
                pid, cat, tva, barcode = match
                code = barcode or ""  # Utilise le code-barres existant
                prod_id = str(pid)    # ID du produit en base
            else:
                # Produit nouveau : vérifie s'il a déjà été rencontré dans ce traitement
                if norm in new_products:
                    # Déjà vu : réutilise le même code
                    code, cat, tva = new_products[norm]
                else:
                    # Premier passage : catégorise et génère un code placeholder
                    cat = categorize(norm)
                    tva = infer_tva(cat)
                    pref, _ = placeholder_map[cat]
                    counters[cat] = counters.get(cat, 0) + 1
                    code = f"{pref}{counters[cat]:03d}"  # Ex: "01042"
                    new_products[norm] = (code, cat, tva)
                prod_id = "NEW"  # Marqueur pour indiquer qu'il faut créer ce produit

            # Calcule le montant total HT de la ligne
            montant_calc = unit_price * qty

            # Écrit la ligne enrichie
            writer.writerow(
                {
                    "file": row["file"],
                    "invoice": row["invoice"],
                    "invoice_date": row["invoice_date"],
                    "Produit": produit,
                    "EAN": code,
                    "Qté": row["quantity"],
                    "Reçue": row["quantity"],
                    "Prix_achat_HT": f"{unit_price:.2f}",
                    "TVA": f"{tva:.1f}",
                    "Produit_ID": prod_id,
                    "Montant_HT_calc": f"{montant_calc:.2f}",
                    "Categorie": cat,
                }
            )

    # Affiche le résumé du traitement
    print(f"Fichier enrichi écrit : {OUT.relative_to(ROOT)}")
    print(f"Nouveaux produits détectés : {len(new_products)}")


if __name__ == "__main__":
    main()
