"""
CLI to parse LCL statements from PDFs, classify operations, and emit a consolidated JSON.

Usage:
  python3 scripts/auto_parse_lcl.py --input-dir pdfs --output pdfs/parsed_bank_entries_by_period.json

Dependencies:
  - pdftotext CLI available in PATH (no Python deps).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, List, Tuple

import pdfplumber

# Regular expressions for period headers and operation lines
PERIOD_RE = re.compile(r"du\s+(\d{2}\.\d{2}\.\d{4})\s+au\s+(\d{2}\.\d{2}\.\d{4})", re.IGNORECASE)
OP_RE = re.compile(
    r"^\s*(\d{2}\.\d{2})\s+(.+?)\s+(\d{2}\.\d{2}\.\d{2})\s+([0-9 ]+,\d{2})?\s*([0-9 ]+,\d{2})?\s*$"
)
# SumUp table lines (Montant débité / Montant crédité / Frais facturé / Solde dispo)
SUMUP_LINE_RE = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s+(\S+)\s+(.+?)\s+(Approuvé|Entrant|Remboursé|Envoyé par)\s+([0-9]+\.[0-9]{2})\s+([0-9]+\.[0-9]{2})\s+([0-9]+\.[0-9]{2})\s+([0-9]+\.[0-9]{2})"
)


# Classification rules: ordered; first match wins
KEYWORDS: List[Tuple[str, List[str], str]] = [
    ("avis_tiers", ["frais avis a tiers detenteur"], "charges_bancaires_avis_tiers"),
    ("salaire", ["salaire"], "revenu_salaire"),
    ("loyer", ["loyer", "loyers"], "loyer"),
    ("charges_locatives", ["residence st an"], "charges_locatives"),
    ("versement_als", ["versement als"], "depot_especes"),
    ("urssaf", ["urssaf"], "cotisations_sociales"),
    ("klesia", ["klesia"], "prevoyance_retraite"),
    ("avem", ["avem"], "location_tpe"),
    ("metrofourn", ["metro france"], "achat_fournisseur"),
    ("engie", ["engie", "gazelenergie"], "energie"),
    ("assurance", ["assurance lcl", "allianz", "pacifica"], "assurance"),
    ("prefiloc", ["prefiloc"], "financement"),
    ("canal", ["canal+"], "abonnement_media"),
    ("abon_lcl", ["abon lcl access"], "abonnement_bancaire"),
    ("cotis_carte", ["cotisation mensuelle carte", "option pro"], "frais_bancaires"),
    ("lcl_carte_pro", ["lcl a la carte pro"], "remise_fidelite"),
    ("remise_cb", ["remise cb"], "remise_cb"),
    # fournisseurs restauration / alimentation repérés
    ("resto_gnanam", ["gnanam exoti"], "fournisseur_restauration"),
    ("resto_taiyat", ["tai yat"], "fournisseur_restauration"),
    ("resto_bouch", ["bouch.sarl b"], "fournisseur_restauration"),
    ("resto_eurociel", ["eurociel"], "fournisseur_restauration"),
    ("resto_ethan", ["ethan"], "fournisseur_restauration"),
    ("resto_leclerc", ["leclerc blan"], "fournisseur_restauration"),
]


@dataclass
class Entry:
    statement_id: str
    account: str
    period_start: str
    period_end: str
    operation_date: str
    value_date: str
    label_raw: str
    label_normalized: str
    label_canonical: str
    amount: float
    currency: str
    direction: str
    type: str
    hash: str


def parse_iso(date_str: str) -> str:
    fmt = "%d.%m.%y" if len(date_str.split(".")[-1]) == 2 else "%d.%m.%Y"
    return datetime.strptime(date_str, fmt).date().isoformat()


STOPWORDS_CANON = {
    "remise",
    "cb",
    "no",
    "du",
    "prlv",
    "sepa",
    "vir",
    "inst",
    "versement",
    "als",
    "abon",
    "abonnement",
    "carte",
    "commissions",
    "commission",
    "sur",
    "cotisation",
    "mensuelle",
    "access",
    "lcl",
    "assurance",
    "resultat",
    "arrete",
    "compte",
    "option",
    "pro",
    "trt",
    "trait",
    "irreg",
    "fonct",
}


def normalize_label(label: str) -> Tuple[str, str]:
    base = " ".join(label.split())
    canonical = re.sub(r"\d+", " ", base.lower())
    canonical = re.sub(r"[^a-z]+", " ", canonical)
    tokens = [tok for tok in canonical.split() if tok and tok not in STOPWORDS_CANON]
    canonical = " ".join(tokens)
    return base, canonical


def classify(label: str) -> str:
    l = label.lower()
    for _, needles, typ in KEYWORDS:
        if any(n in l for n in needles):
            return typ
    if l.startswith("cb") or " cb" in l:
        return "paiement_cb"
    if l.startswith("vir"):
        return "virement"
    if "versement" in l:
        return "versement"
    if "prlv" in l:
        return "prelevement"
    if "cotisation" in l or "frais" in l:
        return "frais_bancaires"
    if "reg " in l or l.startswith("reg"):
        return "reglement"
    return "autre"


def clean_amount(s: str) -> float:
    return float(s.replace(" ", "").replace(",", "."))


def _parse_sumup(pdf_path: Path, account: str) -> Iterable[Entry]:
    """Parse SumUp account statements using pdfplumber and SUMUP_LINE_RE."""
    with pdfplumber.open(pdf_path) as pdf:
        lines = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            for raw in text.splitlines():
                raw = raw.strip()
                m = SUMUP_LINE_RE.match(raw)
                if m:
                    lines.append(m.groups())
        if not lines:
            return
        dates = [datetime.strptime(g[0], "%d/%m/%Y").date() for g in lines]
        period_start = min(dates).isoformat()
        period_end = max(dates).isoformat()
        statement_id = f"{account}_{period_start}_{period_end}"
        for g in lines:
            date_str, code, desc, status, debit_str, credit_str, fee_str, balance_str = g
            operation_date = datetime.strptime(date_str, "%d/%m/%Y").date().isoformat()
            value_date = operation_date
            debit = float(debit_str)
            credit = float(credit_str)
            fee = float(fee_str)
            if credit > 0:
                amount = credit
                direction = "credit"
            elif debit > 0:
                amount = debit
                direction = "debit"
            else:
                amount = fee
                direction = "debit"
            label_raw = f"{code} {desc} {status}"
            label_base, label_canon = normalize_label(label_raw)
            hkey = f"{statement_id}|{value_date}|{label_canon}|{amount:.2f}|{direction}"
            yield Entry(
                statement_id=statement_id,
                account=account,
                period_start=period_start,
                period_end=period_end,
                operation_date=operation_date,
                value_date=value_date,
                label_raw=label_raw,
                label_normalized=label_base,
                label_canonical=label_canon,
                amount=amount,
                currency="EUR",
                direction=direction,
                type=classify(label_raw),
                hash=hashlib.sha1(hkey.encode()).hexdigest()[:16],
            )


def run_pdftotext(pdf_path: Path) -> str:
    """Call pdftotext and return text with layout preserved."""
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        print("pdftotext not found in PATH. Please install poppler-utils.", file=sys.stderr)
        sys.exit(1)
    return result.stdout.decode(errors="replace")


def parse_pdf(pdf_path: Path, account: str) -> Iterable[Entry]:
    first_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if pdf.pages:
                first_text = (pdf.pages[0].extract_text() or "").upper()
    except Exception:
        first_text = ""
    if "RELEVÉ DE COMPTE SUMUP" in first_text or "RELEVE DE COMPTE SUMUP" in first_text:
        yield from _parse_sumup(pdf_path, account)
        return

    text = run_pdftotext(pdf_path)
    period_start = period_end = None
    for line in text.splitlines():
        pm = PERIOD_RE.search(line)
        if pm:
            period_start = parse_iso(pm.group(1))
            period_end = parse_iso(pm.group(2))
            continue
        m = OP_RE.match(line)
        if not m or not (period_start and period_end):
            continue
        op_date_raw, label_raw, value_date_raw, debit_raw, credit_raw = m.groups()
        if not (debit_raw or credit_raw):
            continue
        amount = clean_amount(debit_raw or credit_raw)
        direction = "debit" if debit_raw else "credit"
        value_date = parse_iso(value_date_raw)

        # Inférer l'année de l'opération depuis la période (pas depuis la date de valeur)
        # Car une opération de décembre peut avoir une date de valeur en janvier
        period_start_date = datetime.strptime(period_start, "%Y-%m-%d").date()
        period_end_date = datetime.strptime(period_end, "%Y-%m-%d").date()
        op_day, op_month = map(int, op_date_raw.split("."))

        # Utiliser l'année de fin de période par défaut
        op_year = period_end_date.year
        # Si le mois d'opération est plus grand que le mois de fin de période,
        # l'opération était probablement en début de période (année précédente)
        if op_month > period_end_date.month:
            op_year = period_start_date.year

        operation_date = date(op_year, op_month, op_day).isoformat()
        label_base, label_canon = normalize_label(label_raw)
        statement_id = f"{account}_{period_start}_{period_end}"
        hkey = f"{statement_id}|{value_date}|{label_canon}|{amount:.2f}|{direction}"
        yield Entry(
            statement_id=statement_id,
            account=account,
            period_start=period_start,
            period_end=period_end,
            operation_date=operation_date,
            value_date=value_date,
            label_raw=label_raw.strip(),
            label_normalized=label_base,
            label_canonical=label_canon,
            amount=amount,
            currency="EUR",
            direction=direction,
            type=classify(label_raw),
            hash=hashlib.sha1(hkey.encode()).hexdigest()[:16],
        )


def derive_account_name(path: Path) -> str:
    # Use filename stem as account identifier, sanitized
    stem = path.stem.lower().replace(" ", "_").replace("(", "").replace(")", "")
    stem = stem.replace("'", "")
    return stem


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse LCL statements PDFs to structured JSON.")
    parser.add_argument("--input-dir", default="pdfs", type=Path, help="Directory containing PDF statements.")
    parser.add_argument("--output", default="pdfs/parsed_bank_entries_by_period.json", type=Path)
    args = parser.parse_args()

    pdf_files = sorted(p for p in args.input_dir.glob("*.pdf") if p.is_file())
    if not pdf_files:
        print(f"No PDF files found in {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    all_entries: List[Entry] = []
    for pdf in pdf_files:
        account = derive_account_name(pdf)
        print(f"Parsing {pdf.name} as account '{account}'...", file=sys.stderr)
        all_entries.extend(parse_pdf(pdf, account=account))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps([asdict(e) for e in all_entries], ensure_ascii=False, indent=2))
    print(f"Wrote {len(all_entries)} entries to {args.output}")


if __name__ == "__main__":
    main()
