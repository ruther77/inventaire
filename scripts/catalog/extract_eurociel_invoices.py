#!/usr/bin/env python3
"""
Script d'extraction des lignes de factures Eurociel depuis des fichiers PDF.

Ce script utilise l'outil en ligne de commande pdftotext pour extraire le texte
des factures PDF Eurociel, puis parse ce texte pour en extraire les lignes de
produits avec leurs informations (référence, désignation, quantité, prix, etc.).

Un PDF peut contenir plusieurs factures. Le script détecte automatiquement les
changements de numéro de facture et associe chaque ligne à la bonne facture.

Usage:
    python scripts/catalog/extract_eurociel_invoices.py

Fichiers d'entrée:
    - EUROCIEL/*.pdf : Tous les fichiers PDF de factures Eurociel dans ce dossier

Fichiers de sortie:
    - docs/eurociel_factures_extrait.csv : Toutes les colonnes extraites brutes
      Colonnes: file, invoice, invoice_date, reference, designation, quantity,
                weight, unit_price, montant_ht
    - docs/eurociel_factures_formatted.csv : Format préparé pour enrichissement
      Colonnes: file, invoice, invoice_date, Produit, EAN, Qté, Reçue,
                Prix_achat_HT, TVA, Produit_ID, Montant_HT

Variables d'environnement:
    Aucune

Prérequis:
    - Outil pdftotext installé (paquet poppler-utils sur Debian/Ubuntu)
    - Dossier EUROCIEL/ contenant les PDFs de factures Eurociel

Notes:
    - Le format des factures Eurociel doit être cohérent (colonnes alignées)
    - Les colonnes EAN, TVA et Produit_ID sont laissées vides, à remplir par
      enrich_eurociel_invoices.py
"""

from __future__ import annotations

import csv
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

# Configuration des chemins
ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "EUROCIEL"  # Dossier contenant les PDFs de factures
OUTPUT = ROOT / "docs" / "eurociel_factures_extrait.csv"  # Extraction brute
OUTPUT_FORMATTED = ROOT / "docs" / "eurociel_factures_formatted.csv"  # Format préparé


@dataclass
class InvoiceLine:
    """
    Représente une ligne de produit extraite d'une facture Eurociel.

    Attributes:
        file (str): Nom du fichier PDF source
        invoice (str | None): Numéro de facture (ex: "FA123456")
        invoice_date (str | None): Date de la facture (format: dd/mm/yy)
        reference (str): Code référence produit fournisseur
        designation (str): Nom/description du produit
        quantity (str): Quantité commandée (format: "1,50")
        weight (str): Poids ou volume (format: "2,500")
        unit_price (str): Prix unitaire HT (format: "12,50")
        montant_ht (str): Montant total HT de la ligne (format: "18,75")
    """

    file: str
    invoice: Optional[str]
    invoice_date: Optional[str]
    reference: str
    designation: str
    quantity: str
    weight: str
    unit_price: str
    montant_ht: str


def run_pdftotext(pdf_path: Path) -> str:
    """
    Exécute pdftotext pour extraire le texte d'un PDF en préservant la mise en page.

    Args:
        pdf_path (Path): Chemin vers le fichier PDF à traiter

    Returns:
        str: Texte extrait du PDF avec la mise en page préservée (-layout)

    Raises:
        subprocess.CalledProcessError: Si pdftotext échoue
    """
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def parse_invoice_meta(line: str, last_date: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extrait le numéro de facture et la date d'une ligne de texte.

    Args:
        line (str): Ligne de texte extraite du PDF
        last_date (str | None): Dernière date rencontrée (fallback si pas de date sur cette ligne)

    Returns:
        Tuple[str | None, str | None]: (numéro_facture, date_facture)
            - numéro_facture: ex "FA123456" ou None
            - date_facture: ex "15/03/24" ou last_date si non trouvée
    """
    invoice_match = re.search(r"(FA\d{6,})", line)
    date_match = re.search(r"(\d{2}/\d{2}/\d{2})", line)
    invoice_no = invoice_match.group(1) if invoice_match else None
    invoice_date = date_match.group(1) if date_match else last_date
    return invoice_no, invoice_date


def iter_invoice_lines(text: str) -> Iterable[Tuple[str, Optional[str], Optional[str]]]:
    """
    Itère sur les lignes de produits d'un PDF, en trackant la facture courante.

    Un PDF peut contenir plusieurs factures. Cette fonction détecte automatiquement
    les changements de facture (numéro FA...) et associe chaque ligne de produit
    à la bonne facture.

    Le parsing commence après la ligne d'en-tête contenant "Référence" et "Désignation",
    et s'arrête aux marqueurs de fin ("Code Base" ou "Conditions de règlement").

    Args:
        text (str): Texte complet extrait du PDF par pdftotext

    Yields:
        Tuple[str, str | None, str | None]: (ligne_texte, numéro_facture, date_facture)
            pour chaque ligne de produit détectée
    """
    current_invoice = None
    current_date: Optional[str] = None
    last_date: Optional[str] = None
    in_items = False  # Flag: sommes-nous dans la section des lignes de produits ?

    for raw in text.splitlines():
        if not raw.strip():
            continue

        # Track la dernière date vue (utile si facture sans date explicite)
        dm = re.search(r"(\d{2}/\d{2}/\d{2})", raw)
        if dm:
            last_date = dm.group(1)

        # Détecte un nouveau numéro de facture
        inv, inv_date = parse_invoice_meta(raw, last_date)
        if inv:
            current_invoice = inv
            current_date = inv_date
            in_items = False  # Nouvelle facture = on attend le tableau de produits
            continue

        # Détecte le début du tableau de produits (ligne d'en-tête)
        if "Référence" in raw and "Désignation" in raw:
            in_items = True
            continue

        if not in_items:
            continue

        # Détecte la fin du tableau de produits
        if re.match(r"\s*Code\s+Base", raw) or "Conditions de règlement" in raw:
            in_items = False
            continue

        # Yield la ligne brute avec son contexte (facture, date)
        yield raw.rstrip(), current_invoice, current_date


def parse_line(raw: str) -> Optional[Tuple[str, str, str, str, str, str]]:
    """
    Parse une ligne de produit individuelle pour en extraire les colonnes.

    Format attendu (colonnes séparées par espaces):
    <référence> <désignation...> <quantité> <poids> <prix_unitaire> <montant_ht> [*|C2]

    Exemple:
    "12345  HUILE OLIVE 1L              2,00    1,500    12,50    25,00   *"
    => ("12345", "HUILE OLIVE 1L", "2,00", "1,500", "12,50", "25,00")

    Args:
        raw (str): Ligne de texte brute extraite du PDF

    Returns:
        Tuple[str, str, str, str, str, str] | None:
            (référence, désignation, quantité, poids, prix_unitaire, montant_ht)
            ou None si le format ne correspond pas
    """
    # Regex: ref (digits), designation (texte), puis 4 nombres avec virgule
    # Les tokens finaux comme '*' ou 'C2' sont optionnels
    pattern = re.compile(
        r"^\s*(\d+)\s+(.+?)\s+([0-9]+,[0-9]+)\s+([0-9.,]+)\s+([0-9.,]+)\s+([0-9.,]+)(?:\s+\S+)?$"
    )
    m = pattern.match(raw)
    if not m:
        return None
    return m.groups()


def extract_pdf(pdf_path: Path) -> List[InvoiceLine]:
    """
    Extrait toutes les lignes de factures d'un fichier PDF Eurociel.

    Processus:
    1. Exécute pdftotext pour obtenir le texte du PDF
    2. Itère sur les lignes en trackant la facture courante
    3. Parse chaque ligne pour extraire les colonnes structurées
    4. Retourne la liste complète des lignes extraites

    Args:
        pdf_path (Path): Chemin vers le fichier PDF à traiter

    Returns:
        List[InvoiceLine]: Liste de toutes les lignes de produits extraites
    """
    text = run_pdftotext(pdf_path)
    lines: List[InvoiceLine] = []

    for raw, invoice_no, invoice_date in iter_invoice_lines(text):
        parsed = parse_line(raw)
        if not parsed:
            # Ligne qui ne correspond pas au format attendu => ignore
            continue

        ref, designation, qty, weight, unit_price, montant_ht = parsed
        lines.append(
            InvoiceLine(
                file=pdf_path.name,
                invoice=invoice_no,
                invoice_date=invoice_date,
                reference=ref,
                designation=designation.strip(),
                quantity=qty,
                weight=weight,
                unit_price=unit_price,
                montant_ht=montant_ht,
            )
        )
    return lines


def main() -> None:
    """
    Fonction principale : extrait toutes les factures PDF et génère les CSV.

    Processus:
    1. Liste tous les fichiers PDF dans le dossier EUROCIEL/
    2. Extrait les lignes de chaque PDF (gère les erreurs individuellement)
    3. Génère deux fichiers CSV:
       - eurociel_factures_extrait.csv : extraction brute avec toutes les colonnes
       - eurociel_factures_formatted.csv : format préparé pour l'enrichissement
         avec colonnes vides (EAN, TVA, Produit_ID) à remplir ultérieurement
    """
    # Liste tous les PDFs à traiter
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    all_lines: List[InvoiceLine] = []

    # Extrait chaque PDF individuellement
    for pdf in pdf_files:
        try:
            lines = extract_pdf(pdf)
        except subprocess.CalledProcessError as exc:
            print(f"[WARN] pdftotext a échoué sur {pdf.name}: {exc}")
            continue
        if not lines:
            print(f"[WARN] aucune ligne détectée dans {pdf.name}")
        all_lines.extend(lines)

    # Crée le dossier de sortie si nécessaire
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # Génère le fichier d'extraction brute (toutes les colonnes)
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
                "file",
                "invoice",
                "invoice_date",
                "reference",
                "designation",
                "quantity",
                "weight",
                "unit_price",
                "montant_ht",
            ]
        )
        for line in all_lines:
            writer.writerow(
                [
                    line.file,
                    line.invoice or "",
                    line.invoice_date or "",
                    line.reference,
                    line.designation,
                    line.quantity,
                    line.weight,
                    line.unit_price,
                    line.montant_ht,
                ]
            )

    # Génère le fichier formaté pour enrichissement
    # Calcule le prix unitaire à partir du montant total et de la quantité
    with OUTPUT_FORMATTED.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
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
                "Montant_HT",
            ]
        )
        for line in all_lines:
            # Calcule le prix unitaire à partir du montant total
            qty = line.quantity.replace(",", ".")
            try:
                qty_f = float(qty)
            except ValueError:
                qty_f = 0.0
            try:
                mt_f = float(line.montant_ht.replace(",", "."))
            except ValueError:
                mt_f = 0.0
            prix_achat = mt_f / qty_f if qty_f else 0.0

            writer.writerow(
                [
                    line.file,
                    line.invoice or "",
                    line.invoice_date or "",
                    line.designation,
                    "",  # EAN : à remplir par enrich_eurociel_invoices.py
                    line.quantity,
                    line.quantity,  # Reçue = Qté (par défaut)
                    f"{prix_achat:.2f}",
                    "",  # TVA : à remplir par enrich_eurociel_invoices.py
                    "",  # Produit_ID : à remplir par enrich_eurociel_invoices.py
                    line.montant_ht,
                ]
            )

    print(f"Écrit {len(all_lines)} lignes dans {OUTPUT.relative_to(ROOT)} et {OUTPUT_FORMATTED.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
