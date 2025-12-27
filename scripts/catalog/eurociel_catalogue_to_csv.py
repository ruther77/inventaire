#!/usr/bin/env python3
"""
Script d'extraction des produits du catalogue PDF Eurociel vers CSV.

Ce script parse le catalogue PDF Eurociel pour en extraire une liste de produits
(libellés uniquement, sans prix). Le CSV généré sert de base pour créer ou enrichir
les entrées dans les tables `produits` et `produits_barcodes`.

L'extraction utilise des heuristiques pour filtrer le contenu pertinent
(noms de produits) et ignore les en-têtes, séparateurs, numéros de page, etc.

Usage:
    python scripts/catalog/eurociel_catalogue_to_csv.py

    Avec options:
    python scripts/catalog/eurociel_catalogue_to_csv.py --pdf chemin/vers/catalogue.pdf --output sortie.csv

Arguments CLI:
    --pdf : Chemin vers le PDF catalogue (défaut: EUROCIEL/CATALOGUE EURO CIEL.pdf)
    --output : Chemin du CSV de sortie (défaut: data/eurociel_catalogue_candidates.csv)

Fichiers d'entrée:
    - EUROCIEL/CATALOGUE EURO CIEL.pdf : Catalogue produits fournisseur

Fichier de sortie:
    - data/eurociel_catalogue_candidates.csv : Liste dédoublonnée des libellés
      Colonnes: nom

Variables d'environnement:
    Aucune

Prérequis:
    - pdftotext installé (paquet poppler-utils) OU bibliothèque pypdf
    - pandas
    - Catalogue PDF Eurociel

Notes:
    - Les libellés sont extraits puis dédoublonnés en préservant l'ordre
    - Les prix ne sont pas dans ce fichier (à compléter ultérieurement)
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List

import pandas as pd


def _extract_text(pdf_path: Path) -> str:
    """
    Extrait le texte d'un PDF en utilisant pdftotext ou pypdf en fallback.

    Args:
        pdf_path (Path): Chemin vers le fichier PDF

    Returns:
        str: Texte complet extrait du PDF

    Raises:
        SystemExit: Si pypdf n'est pas installé et pdftotext absent
    """
    # Privilégie pdftotext (plus fidèle que pypdf pour les catalogues)
    if shutil.which("pdftotext"):
        result = subprocess.run(
            ["pdftotext", str(pdf_path), "-"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout

    # Fallback vers pypdf si pdftotext absent
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:  # pragma: no cover - dépendance optionnelle
        raise SystemExit(
            "pypdf requis en fallback lorsque pdftotext est absent. Installez-le via `pip install pypdf`."
        ) from exc

    reader = PdfReader(str(pdf_path))
    return "".join(page.extract_text() or "" for page in reader.pages)


def _dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    """
    Dédoublonne une liste en préservant l'ordre de première apparition.

    Args:
        items (Iterable[str]): Liste avec possibles doublons

    Returns:
        List[str]: Liste dédoublonnée dans l'ordre original
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _extract_candidates(text: str) -> list[str]:
    """
    Extrait les libellés de produits candidats du texte brut du catalogue.

    Utilise des heuristiques pour filtrer le contenu pertinent:
    - Ignore les lignes vides, numéros seuls, mots-clés génériques
    - Découpe sur les lignes de séparation (---)
    - Normalise les espaces multiples
    - Filtre les segments trop courts ou sans lettres

    Args:
        text (str): Texte complet extrait du PDF

    Returns:
        list[str]: Liste dédoublonnée des libellés détectés
    """
    # Mots-clés à ignorer (en-têtes de colonnes, métadonnées, etc.)
    ignored = {"ref.", "taille", "origine", "presentation", "présentation"}
    candidates: list[str] = []

    for raw in text.splitlines():
        line = raw.strip()
        # Ignore lignes vides et numéros seuls
        if not line or line.isdigit():
            continue

        lowered = line.lower()
        if lowered in ignored or lowered.rstrip(":") in ignored:
            continue

        # Découpe sur les lignes de séparation (----)
        segments = re.split(r"-{2,}", line) if "-" in line else [line]
        for segment in segments:
            # Nettoie les espaces multiples
            cleaned = re.sub(r"\s{2,}", " ", segment).strip(" -\t")

            # Filtre les segments trop courts ou invalides
            if len(cleaned) < 6 or cleaned.isdigit():
                continue
            if cleaned.lower() in ignored or cleaned.lower().rstrip(":") in ignored:
                continue
            # Doit contenir au moins une lettre (pas que des chiffres/symboles)
            if not any(ch.isalpha() for ch in cleaned):
                continue

            candidates.append(cleaned)

    return _dedupe_preserve_order(candidates)


def main() -> None:
    """
    Fonction principale : parse le PDF catalogue et génère le CSV de libellés.

    Processus:
    1. Parse les arguments CLI (chemins PDF et CSV)
    2. Extrait le texte du PDF
    3. Filtre et extrait les libellés de produits
    4. Génère un CSV dédoublonné avec une colonne 'nom'
    """
    parser = argparse.ArgumentParser(description="Génère un CSV de produits à partir du catalogue Eurociel.")
    parser.add_argument(
        "--pdf",
        type=Path,
        default=Path("EUROCIEL") / "CATALOGUE  EURO CIEL.pdf",
        help="Chemin vers le PDF catalogue Eurociel (défaut: dossier EUROCIEL).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data") / "eurociel_catalogue_candidates.csv",
        help="Chemin du CSV de sortie (défaut: data/eurociel_catalogue_candidates.csv).",
    )
    args = parser.parse_args()

    if not args.pdf.exists():
        raise SystemExit(f"PDF introuvable: {args.pdf}")

    # Extraction et parsing
    text = _extract_text(args.pdf)
    items = _extract_candidates(text)
    if not items:
        raise SystemExit("Aucun libellé détecté dans le catalogue.")

    # Génère le CSV
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"nom": items}).to_csv(args.output, index=False)
    print(f"{len(items)} libellé(s) Eurociel exporté(s) vers {args.output}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
