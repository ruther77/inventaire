"""Importe des relevés LCL (PDF) en mode période par période dans finance_bank_statements / finance_bank_statement_lines.

Hypothèses :
- PDF au format LCL avec en-têtes "RELEVE DE COMPTE" et blocs "du <date> au <date>".
- Colonnes repérables via une ligne qui contient "DATE LIBELLE VALEUR" ou similaire.
- Les montants débit/crédit sont sur la même ligne que la date/libellé.

Usage :
  DATABASE_URL=postgresql+psycopg2://... .venv/bin/python scripts/import_lcl_pdf.py \
    --pdf "releve/l'incontournable 0723 a 1025.pdf" \
    --entity RESTO \
    --account-label "LCL - INCONTOURNABLE"
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
    r"du\s+(\d{2})[./](\d{2})[./](\d{2,4})\s+au\s+(\d{2})[./](\d{2})[./](\d{2,4})",
    re.IGNORECASE,
)


def _parse_period_line(line: str) -> Optional[Tuple[date, date]]:
    m = PERIOD_RE.search(line)
    if not m:
        return None
    d1, m1, y1, d2, m2, y2 = m.groups()

    def _mk(d: str, mo: str, y: str) -> date:
        year = int(y)
        if year < 100:
            year += 2000
        return date(year, int(mo), int(d))

    return _mk(d1, m1, y1), _mk(d2, m2, y2)


def _run_pdftotext(pdf: Path) -> List[str]:
    try:
        out = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
    except FileNotFoundError:
        print("pdftotext non trouvé. Installez poppler-utils.", file=sys.stderr)
        sys.exit(1)
    return out.splitlines()


def _parse_amount(raw: str) -> Optional[float]:
    raw = raw.strip().replace("\u00a0", " ").replace(" ", "")
    if not raw:
        return None
    raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def _guess_libelle(parts: List[str]) -> str:
    return " ".join(p.strip() for p in parts if p.strip())


def parse_lcl_operations(lines: List[str]) -> List[Tuple[date, date, List[Operation]]]:
    """Parse les relevés LCL multi-périodes en blocs (période -> opérations).

    Heuristique tolérante :
    - Détecte les en-têtes de période "du xx.xx.xxxx au yy.yy.yyyy".
    - Tente de lire les colonnes si "DATE LIBELLE" est présent ; sinon fallback : date en début de ligne + dernier token = montant.
    - Agrège les lignes de détail dans le libellé courant.
    """

    periods_ops: List[Tuple[date, date, List[Operation]]] = []
    current_period: Optional[Tuple[date, date]] = None
    current_ops: List[Operation] = []
    current_op: Optional[Operation] = None

    date_col = 0
    value_col = None
    debit_col = None
    credit_col = None

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

    header_seen = False
    date_re = re.compile(r"\d{2}[./]\d{2}")

    for raw_line in lines:
        line = (raw_line or "").replace("\u00a0", " ").strip()
        if not line:
            continue

        per = _parse_period_line(line)
        if per:
            # Changement de période : flush la précédente
            if current_period and current_period != per:
                flush_period()
            current_period = per
            header_seen = False
            current_op = None
            continue

        if "DATE LIBELLE" in line.upper():
            date_col = line.upper().find("DATE")
            value_col = line.upper().find("VALEUR")
            debit_col = line.upper().find("DEBIT") if "DEBIT" in line.upper() else None
            credit_col = line.upper().find("CREDIT") if "CREDIT" in line.upper() else None
            header_seen = True
            continue

        if not current_period:
            continue
        if "RELEVE DE COMPTE" in line.upper():
            continue

        # Repère une date au début de ligne (format dd.mm ou dd/mm)
        tokens = line.split()
        first_token = tokens[0] if tokens else ""
        is_date = bool(date_re.fullmatch(first_token))
        if is_date:
            if current_op:
                current_ops.append(current_op)
                current_op = None

            if header_seen and value_col is not None and (debit_col is not None or credit_col is not None):
                lib_end = debit_col or credit_col or len(line)
                lib_part = line[value_col:lib_end].strip()
                debit_part = line[debit_col:credit_col].strip() if debit_col is not None else ""
                credit_part = line[credit_col:].strip() if credit_col is not None else ""
            else:
                chunks = line.split()
                if len(chunks) >= 2:
                    lib_part = " ".join(chunks[1:-1])
                    amt_raw = chunks[-1]
                    debit_part = ""
                    credit_part = amt_raw
                else:
                    continue

            debit_amt = _parse_amount(debit_part)
            credit_amt = _parse_amount(credit_part)
            if credit_amt is not None and credit_amt > 0:
                amount = credit_amt
                direction = "IN"
            elif debit_amt is not None and debit_amt > 0:
                amount = debit_amt
                direction = "OUT"
            else:
                continue

            parts = first_token.replace(".", "/").split("/")
            if len(parts) < 2:
                continue
            day = int(parts[0])
            month = int(parts[1])
            year = current_period[0].year
            if month < current_period[0].month:
                year = current_period[1].year
            op_date = date(year, month, day)
            val_date = op_date

            current_op = Operation(
                date_operation=op_date,
                date_valeur=val_date,
                libelle=lib_part,
                montant=amount,
                direction=direction,
            )
        else:
            if current_op:
                current_op.libelle = _guess_libelle([current_op.libelle, line])

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


def import_lcl(pdf: Path, entity: str, account_label: str, *, dry_run: bool = False, account_id_override: int | None = None) -> None:
    lines = _run_pdftotext(pdf)
    periods_ops = parse_lcl_operations(lines)
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
        account_id = account_id_override or _ensure_account(conn, entity_id, account_label)

        for period_start, period_end, ops in periods_ops:
            stmt_row = conn.execute(
                text(
                    "SELECT id FROM finance_bank_statements WHERE account_id = :acc AND period_start = :ps AND period_end = :pe LIMIT 1"
                ),
                {"acc": account_id, "ps": period_start, "pe": period_end},
            ).fetchone()
            if stmt_row:
                stmt = int(stmt_row.id)
                conn.execute(text("UPDATE finance_bank_statements SET source = :src WHERE id = :id"), {"src": pdf.name, "id": stmt})
                conn.execute(text("DELETE FROM finance_bank_statement_lines WHERE statement_id = :sid"), {"sid": stmt})
            else:
                stmt = conn.execute(
                    text(
                        "INSERT INTO finance_bank_statements (account_id, period_start, period_end, source, imported_at) "
                        "VALUES (:acc, :ps, :pe, :src, now()) RETURNING id"
                    ),
                    {"acc": account_id, "ps": period_start, "pe": period_end, "src": pdf.name},
                ).scalar_one()

            for op in ops:
                amt = op.montant if op.direction == "IN" else -op.montant
                conn.execute(
                    text(
                        "INSERT INTO finance_bank_statement_lines (statement_id, account_id, date_operation, date_valeur, libelle_banque, montant) "
                        "VALUES (:sid, :acc, :do, :dv, :lib, :amt)"
                    ),
                    {
                        "sid": stmt,
                        "acc": account_id,
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
    parser = argparse.ArgumentParser(description="Import LCL PDF into finance_bank_statements/lines.")
    parser.add_argument("--pdf", required=True, type=Path, help="Chemin du PDF LCL.")
    parser.add_argument("--entity", required=True, help="Code ou ID finance_entities (ex: EPICERIE, RESTO).")
    parser.add_argument("--account-label", required=True, help="Label du compte finance_accounts à utiliser/créer.")
    parser.add_argument("--dry-run", action="store_true", help="Ne rien insérer, juste compter et afficher un résumé.")
    parser.add_argument("--account-id", type=int, help="Forcer l'account_id au lieu de le chercher par label.")
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"PDF introuvable : {args.pdf}", file=sys.stderr)
        sys.exit(1)

    import_lcl(args.pdf, args.entity, args.account_label, dry_run=args.dry_run, account_id_override=args.account_id)


if __name__ == "__main__":
    main()
