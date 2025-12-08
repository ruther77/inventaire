#!/usr/bin/env python3
"""
Complète le fichier eurociel_factures_extrait.csv avec:
- EAN (placeholder 5 chiffres par catégorie si produit non trouvé)
- TVA (selon catégorie)
- Produit_ID (si match exact sur nom, sinon vide/NEW)
Le tout en conservant le format demandé : Produit, EAN, Qté, Reçue, Prix achat HT, TVA, Produit ID.

Entrées attendues :
- docs/eurociel_factures_extrait.csv (issu de extract_eurociel_invoices.py)
- docs/db_products_dump.csv (export des produits existants : nom,id,categorie,tva,barcode)
- docs/db_placeholder_max.csv (max code 5 chiffres par catégorie)

Sortie :
- docs/eurociel_factures_enriched.csv
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from scripts.reclassify_products import RULES, normalize_label  # type: ignore

SRC = ROOT / "docs" / "eurociel_factures_extrait.csv"
DB_PRODUCTS = ROOT / "docs" / "db_products_dump.csv"
DB_PLACEHOLDER_MAX = ROOT / "docs" / "db_placeholder_max.csv"
OUT = ROOT / "docs" / "eurociel_factures_enriched.csv"

# TVA à 20% pour ces catégories
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

# Catégories absentes des placeholders existants : on alloue des préfixes libres à partir de 25
MISSING_PREFIX_START = 25


def load_db_products() -> Dict[str, Tuple[int, str, float, str | None]]:
    """
    Retourne un mapping nom_normalisé -> (id, categorie, tva, barcode_principal).
    """
    mapping: Dict[str, Tuple[int, str, float, str | None]] = {}
    with DB_PRODUCTS.open() as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 5:
                continue
            nom, pid, cat, tva, barcode = row
            key = normalize_label(nom)
            try:
                pid_int = int(pid)
                tva_f = float(tva)
            except ValueError:
                continue
            mapping[key] = (pid_int, cat, tva_f, barcode or None)
    return mapping


def load_placeholder_max():
    """
    Charge le max de chaque catégorie pour les codes 5 chiffres et construit
    un mapping categorie -> (prefix, next_counter).
    """
    mapping: Dict[str, Tuple[str, int]] = {}
    used_prefixes: set[str] = set()
    with DB_PLACEHOLDER_MAX.open() as f:
        reader = csv.reader(f)
        for cat, max_code in reader:
            prefix = max_code[:2]
            used_prefixes.add(prefix)
            try:
                counter = int(max_code[2:])
            except ValueError:
                counter = 0
            mapping[cat] = (prefix, counter)
    return mapping, used_prefixes


def categorize(label: str) -> str:
    for rule in RULES:
        if rule.matches(label):
            cat = rule.category
            break
    else:
        cat = "Épicerie sucrée"

    # Anti faux positifs sur les catégories alcool/boissons quand on voit des poids/pcs
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

        has_weight = bool(re.search(r"\d+\s*(KG|G|PCS?)", label)) or "X" in label
        is_drink = any(token in label for token in ["CL", " L", "LITRE", "VIN", "BIERE", "BEER", "BOITE", "CAN", "BOUT", "BOUTEILLE"])
        if has_weight and not is_drink:
            meat_words = ["POULE", "POULET", "VIANDE", "BOEUF", "BEEF", "AGNEAU", "MOUTON", "PORC", "PORK", "SAUMON", "FUMEE", "FUME", "DARNE", "FILET", "TILAPIA", "MAQUEREAU", "CREVETTE", "POISSON"]
            packaging_words = ["SACHET", "SAC", "BOITE", "BOX", "PAQUET", "PAQUETS", "PAIRE", "PLATEAU", "BARQUETTE"]
            if any(word in label for word in meat_words):
                cat = "Mer / Viandes base"
            elif any(word in label for word in packaging_words):
                cat = "Emballages / Jetables"
            else:
                cat = "Épicerie sucrée"

    return cat


def infer_tva(cat: str) -> float:
    return 20.0 if cat in TVA20 else 5.5


def main() -> None:
    db_products = load_db_products()
    placeholder_map, used_prefixes = load_placeholder_max()

    # Allouer des préfixes pour les catégories absentes
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
        while f"{available_prefix:02d}" in used_prefixes:
            available_prefix += 1
        placeholder_map[cat] = (f"{available_prefix:02d}", 0)
        used_prefixes.add(f"{available_prefix:02d}")
        available_prefix += 1

    # Mémoire pour les nouveaux produits (nom normalisé -> placeholder)
    new_products: Dict[str, Tuple[str, str, float]] = {}  # norm -> (code, cat, tva)
    counters = {cat: counter for cat, (pref, counter) in placeholder_map.items()}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with SRC.open() as f_in, OUT.open("w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in, delimiter=";")
        fieldnames = [
            "file",
            "invoice",
            "invoice_date",
            "Produit",
            "EAN",
            "Qté",
            "Reçue",
            "Prix_achat_HT",
            "TVA",
            "Produit_ID",
            "Montant_HT_calc",
            "Categorie",
        ]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for row in reader:
            produit = row["designation"]
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

            norm = normalize_label(produit)
            match = db_products.get(norm)
            if match:
                pid, cat, tva, barcode = match
                code = barcode or ""
                prod_id = str(pid)
            else:
                if norm in new_products:
                    code, cat, tva = new_products[norm]
                else:
                    cat = categorize(norm)
                    tva = infer_tva(cat)
                    pref, _ = placeholder_map[cat]
                    counters[cat] = counters.get(cat, 0) + 1
                    code = f"{pref}{counters[cat]:03d}"
                    new_products[norm] = (code, cat, tva)
                prod_id = "NEW"

            montant_calc = unit_price * qty
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

    print(f"Fichier enrichi écrit : {OUT.relative_to(ROOT)}")
    print(f"Nouveaux produits détectés : {len(new_products)}")


if __name__ == "__main__":
    main()
