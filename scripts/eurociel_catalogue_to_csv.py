#!/usr/bin/env python3
"""Extrait une liste de produits depuis le catalogue PDF Eurociel en CSV dédoublonné.

Le CSV généré n'inclut que les libellés. Il sert de base de travail pour créer
des entrées dans les tables `produits`/`produits_barcodes` (prix à compléter).
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
    """Récupère le texte du PDF en privilégiant `pdftotext` (plus fidèle que pypdf)."""

    if shutil.which("pdftotext"):
        result = subprocess.run(
            ["pdftotext", str(pdf_path), "-"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout

    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:  # pragma: no cover - dépendance optionnelle
        raise SystemExit(
            "pypdf requis en fallback lorsque pdftotext est absent. Installez-le via `pip install pypdf`."
        ) from exc

    reader = PdfReader(str(pdf_path))
    return "".join(page.extract_text() or "" for page in reader.pages)


def _dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _extract_candidates(text: str) -> list[str]:
    """Heuristique simple : découpe sur les longues lignes (---) et garde les libellés lisibles."""

    ignored = {"ref.", "taille", "origine", "presentation", "présentation"}
    candidates: list[str] = []

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.isdigit():
            continue

        lowered = line.lower()
        if lowered in ignored or lowered.rstrip(":") in ignored:
            continue

        segments = re.split(r"-{2,}", line) if "-" in line else [line]
        for segment in segments:
            cleaned = re.sub(r"\s{2,}", " ", segment).strip(" -\t")
            if len(cleaned) < 6 or cleaned.isdigit():
                continue
            if cleaned.lower() in ignored or cleaned.lower().rstrip(":") in ignored:
                continue
            if not any(ch.isalpha() for ch in cleaned):
                continue
            candidates.append(cleaned)

    return _dedupe_preserve_order(candidates)


def main() -> None:
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

    text = _extract_text(args.pdf)
    items = _extract_candidates(text)
    if not items:
        raise SystemExit("Aucun libellé détecté dans le catalogue.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"nom": items}).to_csv(args.output, index=False)
    print(f"{len(items)} libellé(s) Eurociel exporté(s) vers {args.output}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
