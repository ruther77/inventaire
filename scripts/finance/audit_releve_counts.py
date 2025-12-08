"""Audit des PDF dans /releve : comptage des opérations détectées par banque (dry-run).

Produit un tableau par fichier (nb d'opérations, période, totaux IN/OUT) et une comparaison
avec la BDD (finance_transactions) par compte si souhaité.

Usage :
  python3 scripts/audit_releve_counts.py --folder releve
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.data_repository import get_engine  # type: ignore  # noqa: E402
from scripts.import_lcl_pdf import parse_lcl_operations, _run_pdftotext as lcl_pdftotext  # type: ignore  # noqa: E402
from scripts.import_bnp_pdf import parse_bnp_operations, _run_pdftotext as bnp_pdftotext  # type: ignore  # noqa: E402
from scripts.import_sumup_pdf import parse_sumup_operations, _run_pdftotext as sumup_pdftotext  # type: ignore  # noqa: E402


def summarize_ops(ops: List[Dict]) -> Tuple[int, float, float]:
    total_in = 0.0
    total_out = 0.0
    for op in ops:
        if op["direction"] == "IN":
            total_in += op["amount"]
        else:
            total_out += op["amount"]
    return len(ops), total_in, total_out


def audit_file(pdf: Path) -> Dict:
    name_lower = pdf.name.lower()
    if "sumup" in name_lower:
        lines = sumup_pdftotext(pdf)
        ps, pe, ops_raw = parse_sumup_operations(lines)
        ops = [
            {"date": op.date_operation, "label": op.libelle, "direction": op.direction, "amount": op.montant}
            for op in ops_raw
        ]
        count, tin, tout = summarize_ops(ops)
        return {"file": pdf.name, "parser": "sumup", "period_start": ps, "period_end": pe, "count": count, "in": tin, "out": tout}

    # Certains PDFs nommés COMPTECOURANT_* sont au format LCL; on force LCL avant BNP
    if name_lower.startswith("comptecourant_"):
        lines = lcl_pdftotext(pdf)
        periods = parse_lcl_operations(lines)
        count = 0
        tin = 0.0
        tout = 0.0
        ps = min(p[0] for p in periods)
        pe = max(p[1] for p in periods)
        for _, _, ops_raw in periods:
            for op in ops_raw:
                if op.direction == "IN":
                    tin += op.montant
                else:
                    tout += op.montant
            count += len(ops_raw)
        return {"file": pdf.name, "parser": "lcl", "period_start": ps, "period_end": pe, "count": count, "in": tin, "out": tout}

    if "bnp" in name_lower:
        lines = bnp_pdftotext(pdf)
        periods = parse_bnp_operations(lines)
        count = 0
        tin = 0.0
        tout = 0.0
        ps = min(p[0] for p in periods)
        pe = max(p[1] for p in periods)
        for _, _, ops_raw in periods:
            for op in ops_raw:
                if op.direction == "IN":
                    tin += op.montant
                else:
                    tout += op.montant
            count += len(ops_raw)
        return {"file": pdf.name, "parser": "bnp", "period_start": ps, "period_end": pe, "count": count, "in": tin, "out": tout}

    # défaut : LCL
    lines = lcl_pdftotext(pdf)
    periods = parse_lcl_operations(lines)
    count = 0
    tin = 0.0
    tout = 0.0
    ps = min(p[0] for p in periods)
    pe = max(p[1] for p in periods)
    for _, _, ops_raw in periods:
        for op in ops_raw:
            if op.direction == "IN":
                tin += op.montant
            else:
                tout += op.montant
        count += len(ops_raw)
    return {"file": pdf.name, "parser": "lcl", "period_start": ps, "period_end": pe, "count": count, "in": tin, "out": tout}


def db_counts() -> Dict[int, int]:
    eng = get_engine()
    with eng.begin() as conn:
        rows = conn.execute(
            text("SELECT account_id, COUNT(*) AS cnt FROM finance_transactions GROUP BY account_id ORDER BY account_id")
        ).fetchall()
    return {int(r.account_id): int(r.cnt) for r in rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compte les lignes détectées dans les PDF de relevés (sans insertion).")
    parser.add_argument("--folder", type=Path, default=Path("releve"), help="Dossier contenant les PDF.")
    parser.add_argument("--include-db", action="store_true", help="Affiche aussi les counts finance_transactions par account_id.")
    args = parser.parse_args()

    if not args.folder.exists():
        sys.exit(f"Dossier introuvable: {args.folder}")

    pdfs = sorted(p for p in args.folder.glob("*.pdf") if p.is_file())
    if not pdfs:
        sys.exit("Aucun PDF trouvé.")

    print("=== Comptage dry-run des PDF ===")
    for pdf in pdfs:
        try:
            summary = audit_file(pdf)
            print(
                f"{summary['file']:<40} parser={summary['parser']:<5} "
                f"période={summary['period_start']}→{summary['period_end']} "
                f"lignes={summary['count']} IN={summary['in']:.2f} OUT={summary['out']:.2f}"
            )
        except Exception as exc:
            print(f"{pdf.name:<40} ERROR: {exc}")

    if args.include_db:
        counts = db_counts()
        print("\\n=== finance_transactions par account_id ===")
        for acc, cnt in counts.items():
            print(f"account_id={acc}: {cnt} lignes")


if __name__ == "__main__":
    main()
