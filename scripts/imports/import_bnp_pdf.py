"""Importe un relevé BNP (PDF) dans les tables finance_bank_statements / finance_bank_statement_lines.

Hypothèses :
- PDF en français au format BNP Paribas (colonnes Date / Nature / Valeur / Débit / Crédit).
- Les colonnes sont détectées via la ligne d'en-tête "Date   Nature des opérations   ... Débit Crédit".
- La période est lue via "du <date> au <date>" sur la première page.

Usage :
  DATABASE_URL=postgresql+psycopg2://... .venv/bin/python scripts/import_bnp_pdf.py \
    --pdf releve/releve\\ 23\\ 24\\ 25\\ BNP\\ angele.pdf \
    --entity EPICERIE \
    --account-label \"BNP - ANGELE\"
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text

from core.data_repository import get_engine


MONTHS = {
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    "decembre": 12,
}


@dataclass
class Operation:
    date_operation: date
    date_valeur: date
    libelle: str
    montant: float
    direction: str  # IN / OUT


PERIOD_RE = re.compile(
    r"du\s+(\d{1,2})\s+([a-zéûêîôäëïöüàç]+)\s+(\d{4})\s+au\s+(\d{1,2})\s+([a-zéûêîôäëïöüàç]+)\s+(\d{4})",
    re.IGNORECASE,
)


def _parse_period_line(line: str) -> Optional[Tuple[date, date]]:
    m = PERIOD_RE.search(line)
    if not m:
        return None
    d1, m1, y1, d2, m2, y2 = m.groups()

    def _mk(d: str, mo: str, y: str) -> date:
        return date(int(y), MONTHS[mo.lower()], int(d))

    return _mk(d1, m1, y1), _mk(d2, m2, y2)


def _run_pdftotext(pdf: Path) -> List[str]:
    try:
        out = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
    except FileNotFoundError:
        print("pdftotext non trouvé. Installez poppler-utils.", file=sys.stderr)
        sys.exit(1)
    return out.splitlines()


def _find_columns(header_line: str) -> Dict[str, int]:
    cols = {}
    for key in ["Date", "Nature des opérations", "Valeur", "Débit", "Crédit"]:
        idx = header_line.find(key)
        if idx < 0:
            raise ValueError(f"Colonne {key} introuvable dans l'en-tête.")
        cols[key] = idx
    return cols


def _parse_amount(raw: str) -> Optional[float]:
    raw = raw.strip().replace(" ", "").replace("\u00a0", "")
    if not raw:
        return None
    raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def parse_bnp_operations(lines: List[str]) -> List[Tuple[date, date, List[Operation]]]:
    """Retourne une liste de périodes avec leurs opérations."""
    if not lines:
        raise ValueError("PDF vide.")

    periods_ops: List[Tuple[date, date, List[Operation]]] = []

    current_period: Optional[Tuple[date, date]] = None
    current_ops: List[Operation] = []
    current_op: Optional[Operation] = None
    cols: Dict[str, int] = {}
    date_re = re.compile(r"\d{2}\.\d{2}")

    def flush_period():
        nonlocal current_period, current_ops, current_op
        if current_period:
            if current_op:
                current_ops.append(current_op)
                current_op = None
            if current_ops:
                periods_ops.append((current_period[0], current_period[1], current_ops))
        current_period = None
        current_ops = []
        current_op = None

    for idx, line in enumerate(lines):
        # Détecter changement de période
        per = _parse_period_line(line)
        if per:
            # On change de période -> flush précédente
            if current_period and current_period != per:
                flush_period()
            current_period = per
            cols = {}
            continue

        if "Nature des opérations" in line and "Débit" in line and "Crédit" in line:
            cols = _find_columns(line)
            continue

        if not current_period or not cols:
            continue

        if not line.strip():
            continue
        if "RELEVE DE COMPTE" in line or "BNP PARIBAS" in line or "RIB :" in line:
            continue

        date_raw = line[cols["Date"] : cols["Date"] + 5].strip()
        looks_like_date = bool(date_re.fullmatch(date_raw))
        if looks_like_date:
            # Finalise l'opération précédente
            if current_op:
                current_ops.append(current_op)
                current_op = None

            nature = line[cols["Nature des opérations"] : cols["Valeur"]].strip()
            val_date_raw = line[cols["Valeur"] : cols["Valeur"] + 5].strip()
            debit_str = line[cols["Débit"] : cols["Crédit"]].strip()
            credit_str = line[cols["Crédit"] :].strip()

            credit_amt = _parse_amount(credit_str)
            debit_amt = _parse_amount(debit_str)
            if credit_amt is not None and credit_amt > 0:
                amount = credit_amt
                direction = "IN"
            elif debit_amt is not None and debit_amt > 0:
                amount = debit_amt
                direction = "OUT"
            else:
                continue

            day, month = int(date_raw.split(".")[0]), int(date_raw.split(".")[1])
            year = current_period[0].year
            # Heuristique : si le mois est avant le mois de début, basculer sur l'année de fin
            if month < current_period[0].month:
                year = current_period[1].year
            op_date = date(year, month, day)

            try:
                val_day = int(val_date_raw.split(".")[0])
                val_month = int(val_date_raw.split(".")[1])
                val_year = year if val_month >= current_period[0].month else current_period[1].year
                val_date = date(val_year, val_month, val_day)
            except Exception:
                val_date = op_date

            current_op = Operation(
                date_operation=op_date,
                date_valeur=val_date,
                libelle=nature,
                montant=amount,
                direction=direction,
            )
        else:
            if current_op:
                current_op.libelle = (current_op.libelle + " " + line.strip()).strip()

    # Flush fin de fichier
    flush_period()
    return periods_ops


def _get_entity_id(conn, code_or_id: str) -> int:
    if code_or_id.isdigit():
        return int(code_or_id)
    row = conn.execute(
        text("SELECT id FROM finance_entities WHERE lower(code) = lower(:code)"),
        {"code": code_or_id},
    ).fetchone()
    if not row:
        raise ValueError(f"Entity introuvable pour code '{code_or_id}'")
    return int(row.id)


def _ensure_account(conn, entity_id: int, label: str) -> int:
    row = conn.execute(
        text("SELECT id FROM finance_accounts WHERE entity_id = :e AND label = :l"),
        {"e": entity_id, "l": label},
    ).fetchone()
    if row:
        return int(row.id)
    return int(
        conn.execute(
            text(
                "INSERT INTO finance_accounts (entity_id, type, label, currency, is_active) "
                "VALUES (:e, 'BANQUE', :l, 'EUR', TRUE) RETURNING id"
            ),
            {"e": entity_id, "l": label},
        ).scalar_one()
    )


def import_bnp(pdf: Path, entity: str, account_label: str, *, dry_run: bool = False) -> None:
    lines = _run_pdftotext(pdf)
    periods_ops = parse_bnp_operations(lines)
    if not periods_ops:
        raise ValueError("Aucune période détectée dans le PDF.")
    print(f"PDF: {pdf} | {len(periods_ops)} période(s) détectée(s)")

    total_lines = 0
    total_in = 0.0
    total_out = 0.0

    if dry_run:
        for period_start, period_end, ops in periods_ops:
            for op in ops:
                if op.direction == "IN":
                    total_in += op.montant
                else:
                    total_out += op.montant
            total_lines += len(ops)
            print(f" - [DRY] Période {period_start} → {period_end} : {len(ops)} lignes")
        print(f"[DRY] {pdf.name} : {len(periods_ops)} relevés, {total_lines} lignes, IN={total_in:.2f} / OUT={total_out:.2f}")
        return

    eng = get_engine()
    with eng.begin() as conn:
        entity_id = _get_entity_id(conn, entity)
        account_id = _ensure_account(conn, entity_id, account_label)

        for period_start, period_end, ops in periods_ops:
            stmt_row = conn.execute(
                text(
                    """
                    SELECT id FROM finance_bank_statements
                    WHERE account_id = :acc AND period_start = :ps AND period_end = :pe
                    LIMIT 1
                    """
                ),
                {"acc": account_id, "ps": period_start, "pe": period_end},
            ).fetchone()
            if stmt_row:
                stmt = int(stmt_row.id)
                conn.execute(
                    text("UPDATE finance_bank_statements SET source = :src WHERE id = :id"),
                    {"src": pdf.name, "id": stmt},
                )
                conn.execute(text("DELETE FROM finance_bank_statement_lines WHERE statement_id = :sid"), {"sid": stmt})
            else:
                stmt = conn.execute(
                    text(
                        """
                        INSERT INTO finance_bank_statements (account_id, period_start, period_end, source, imported_at)
                        VALUES (:acc, :ps, :pe, :src, now())
                        RETURNING id
                        """
                    ),
                    {"acc": account_id, "ps": period_start, "pe": period_end, "src": pdf.name},
                ).scalar_one()

            for op in ops:
                amt = op.montant if op.direction == "IN" else -op.montant
                conn.execute(
                    text(
                        """
                        INSERT INTO finance_bank_statement_lines (
                            statement_id, date_operation, date_valeur, libelle_banque, montant
                        ) VALUES (:sid, :do, :dv, :lib, :amt)
                        """
                    ),
                    {
                        "sid": stmt,
                        "do": op.date_operation,
                        "dv": op.date_valeur,
                        "lib": op.libelle,
                        "amt": amt,
                    },
                )
                if amt >= 0:
                    total_in += amt
                else:
                    total_out += -amt
            total_lines += len(ops)
            print(f" - Période {period_start} → {period_end} : {len(ops)} lignes (statement_id={stmt})")

    print(f"Insertion terminée : {len(periods_ops)} relevés, {total_lines} lignes, IN={total_in:.2f} / OUT={total_out:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import BNP PDF into finance_bank_statements/lines.")
    parser.add_argument("--pdf", required=True, type=Path, help="Chemin du PDF BNP.")
    parser.add_argument("--entity", required=True, help="Code ou ID finance_entities (ex: EPICERIE, RESTO).")
    parser.add_argument("--account-label", default="BNP - ANGELE", help="Label du compte finance_accounts à utiliser/créer.")
    parser.add_argument("--dry-run", action="store_true", help="Ne rien insérer, juste compter et afficher un résumé.")
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"PDF introuvable : {args.pdf}", file=sys.stderr)
        sys.exit(1)

    import_bnp(args.pdf, args.entity, args.account_label, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
