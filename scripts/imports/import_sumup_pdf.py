"""Importe des relevés SumUp (PDF) dans finance_bank_statements/lines, avec mode dry-run.

Hypothèses :
- PDF export SumUp avec tableau contenant les colonnes : Date / ID / Description / Statut / Montant débité / Montant crédité / Frais facturé / Solde disponible.
- pdftotext disponible.

Usage :
  DATABASE_URL=postgresql+psycopg2://... python3 scripts/import_sumup_pdf.py \
    --pdf releve/sumup\ releve.pdf \
    --entity RESTO \
    --account-label \"SUMUP - RESTAURANT\" \
    --dry-run
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.data_repository import get_engine


SUMUP_LINE_RE = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s+(\S+)\s+(.+?)\s+(Approuvé|Entrant|Remboursé|Envoyé par)\s+([0-9]+\.[0-9]{2})\s+([0-9]+\.[0-9]{2})\s+([0-9]+\.[0-9]{2})\s+([0-9]+\.[0-9]{2})"
)


@dataclass
class Operation:
    date_operation: date
    date_valeur: date
    libelle: str
    montant: float
    direction: str  # IN / OUT


def _run_pdftotext(pdf: Path) -> List[str]:
    try:
        out = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
    except FileNotFoundError:
        print("pdftotext non trouvé. Installez poppler-utils.", file=sys.stderr)
        sys.exit(1)
    return out.splitlines()


def _get_entity_id(conn, entity: str) -> int:
    try:
        return int(entity)
    except ValueError:
        row = conn.execute(text("SELECT id FROM finance_entities WHERE code = :c"), {"c": entity}).fetchone()
        if not row:
            raise RuntimeError(f"Entity '{entity}' introuvable.")
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


def parse_sumup_operations(lines: List[str]) -> Tuple[date, date, List[Operation]]:
    ops: List[Operation] = []
    min_d: Optional[date] = None
    max_d: Optional[date] = None
    for line in lines:
        m = SUMUP_LINE_RE.match(line.strip())
        if not m:
            continue
        raw_date, tx_id, desc, status, debit_raw, credit_raw, fee_raw, balance_raw = m.groups()
        d = datetime.strptime(raw_date, "%d/%m/%Y").date()
        min_d = d if min_d is None else min(min_d, d)
        max_d = d if max_d is None else max(max_d, d)
        debit = float(debit_raw)
        credit = float(credit_raw)
        fee = float(fee_raw)
        net = credit - debit - fee
        direction = "IN" if net >= 0 else "OUT"
        ops.append(
            Operation(
                date_operation=d,
                date_valeur=d,
                libelle=f"{desc} ({tx_id}, {status})",
                montant=abs(net),
                direction=direction,
            )
        )
    if not ops or min_d is None or max_d is None:
        raise ValueError("Aucune opération SumUp détectée dans le PDF.")
    return min_d, max_d, ops


def import_sumup(pdf: Path, entity: str, account_label: str, *, dry_run: bool = False, account_id_override: int | None = None) -> None:
    lines = _run_pdftotext(pdf)
    period_start, period_end, ops = parse_sumup_operations(lines)
    print(f"PDF: {pdf} | période {period_start} → {period_end} | {len(ops)} opérations")

    total_in = 0.0
    total_out = 0.0
    if dry_run:
        for op in ops:
            if op.direction == "IN":
                total_in += op.montant
            else:
                total_out += op.montant
        print(f"[DRY] {pdf.name} : lignes={len(ops)} IN={total_in:.2f} / OUT={total_out:.2f}")
        return

    eng = get_engine()
    with eng.begin() as conn:
        entity_id = _get_entity_id(conn, entity)
        account_id = account_id_override or _ensure_account(conn, entity_id, account_label)
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
                    "INSERT INTO finance_bank_statement_lines (statement_id, date_operation, date_valeur, libelle_banque, montant) "
                    "VALUES (:sid, :do, :dv, :lib, :amt)"
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

    print(f"Insertion terminée : {len(ops)} lignes (IN={total_in:.2f} / OUT={total_out:.2f})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import SumUp PDF into finance_bank_statements/lines.")
    parser.add_argument("--pdf", required=True, type=Path, help="Chemin du PDF SumUp.")
    parser.add_argument("--entity", required=True, help="Code ou ID finance_entities (ex: EPICERIE, RESTO).")
    parser.add_argument("--account-label", default="SUMUP", help="Label du compte finance_accounts à utiliser/créer.")
    parser.add_argument("--dry-run", action="store_true", help="Ne rien insérer, juste compter et afficher un résumé.")
    parser.add_argument("--account-id", type=int, help="Forcer l'account_id au lieu de le chercher par label.")
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"PDF introuvable : {args.pdf}", file=sys.stderr)
        sys.exit(1)

    import_sumup(args.pdf, args.entity, args.account_label, dry_run=args.dry_run, account_id_override=args.account_id)


if __name__ == "__main__":
    main()
