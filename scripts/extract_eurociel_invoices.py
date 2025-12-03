#!/usr/bin/env python3
"""
Extraction rapide des lignes de facture Eurociel (PDF) via pdftotext -layout.
On parse les colonnes Référence / Désignation / Qté / Poids / Px unitaire / Montant HT.
Objectif : produire un CSV intermédiaire exploitable (nom fichier, facture, date, ligne, désignation, quantité, prix).
"""

from __future__ import annotations

import csv
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "EUROCIEL"
OUTPUT = ROOT / "docs" / "eurociel_factures_extrait.csv"
OUTPUT_FORMATTED = ROOT / "docs" / "eurociel_factures_formatted.csv"


@dataclass
class InvoiceLine:
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
    """Run pdftotext -layout and return the extracted text."""
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def parse_invoice_meta(line: str, last_date: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Extract invoice number (FA...) and date (dd/mm/yy) from current line or fallback to last_date."""
    invoice_match = re.search(r"(FA\d{6,})", line)
    date_match = re.search(r"(\d{2}/\d{2}/\d{2})", line)
    invoice_no = invoice_match.group(1) if invoice_match else None
    invoice_date = date_match.group(1) if date_match else last_date
    return invoice_no, invoice_date


def iter_invoice_lines(text: str) -> Iterable[Tuple[str, Optional[str], Optional[str]]]:
    """
    Iterate over (line, invoice_no, invoice_date) with context of current invoice.
    A PDF peut contenir plusieurs factures ; on bascule quand on rencontre un nouvel invoice_no.
    """
    current_invoice = None
    current_date: Optional[str] = None
    last_date: Optional[str] = None
    in_items = False

    for raw in text.splitlines():
        if not raw.strip():
            continue

        # track latest date seen
        dm = re.search(r"(\d{2}/\d{2}/\d{2})", raw)
        if dm:
            last_date = dm.group(1)

        inv, inv_date = parse_invoice_meta(raw, last_date)
        if inv:
            current_invoice = inv
            current_date = inv_date
            in_items = False
            continue

        if "Référence" in raw and "Désignation" in raw:
            in_items = True
            continue

        if not in_items:
            continue

        # stop conditions for items
        if re.match(r"\s*Code\s+Base", raw) or "Conditions de règlement" in raw:
            in_items = False
            continue

        yield raw.rstrip(), current_invoice, current_date


def parse_line(raw: str) -> Optional[Tuple[str, str, str, str, str, str]]:
    """
    Parse a single item line.
    Expected shape: <ref> <designation...> <qty> <weight> <unit_price> <montant>
    Trailing tokens like '*' ou 'C2' sont optionnels.
    """
    pattern = re.compile(
        r"^\s*(\d+)\s+(.+?)\s+([0-9]+,[0-9]+)\s+([0-9.,]+)\s+([0-9.,]+)\s+([0-9.,]+)(?:\s+\S+)?$"
    )
    m = pattern.match(raw)
    if not m:
        return None
    return m.groups()


def extract_pdf(pdf_path: Path) -> List[InvoiceLine]:
    text = run_pdftotext(pdf_path)
    lines: List[InvoiceLine] = []
    for raw, invoice_no, invoice_date in iter_invoice_lines(text):
        parsed = parse_line(raw)
        if not parsed:
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
    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    all_lines: List[InvoiceLine] = []
    for pdf in pdf_files:
        try:
            lines = extract_pdf(pdf)
        except subprocess.CalledProcessError as exc:
            print(f"[WARN] pdftotext failed on {pdf.name}: {exc}")
            continue
        if not lines:
            print(f"[WARN] aucune ligne détectée dans {pdf.name}")
        all_lines.extend(lines)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
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

    # Fichier au format demandé: Produit, EAN, Qté, Reçue, Prix achat (HT), TVA, Produit ID
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
                    "",  # EAN placeholder à remplir par la suite
                    line.quantity,
                    line.quantity,  # Reçue = Qté
                    f"{prix_achat:.2f}",
                    "",  # TVA à compléter après catégorisation
                    "",  # Produit_ID à compléter après rapprochement
                    line.montant_ht,
                ]
            )

    print(f"Écrit {len(all_lines)} lignes dans {OUTPUT.relative_to(ROOT)} et {OUTPUT_FORMATTED.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
