#!/usr/bin/env python3
"""
Script d'import des relevés bancaires PDF.

Utilise le workflow unifié core.bank_import qui supporte:
- LCL (format standard et multi-périodes)
- BNP (format avec dates en français)

Usage:
    python scripts/import_bank_statements.py --dir /path/to/pdfs
    python scripts/import_bank_statements.py --file /path/to/file.pdf --entity RESTO --account "LCL Principal"
    python scripts/import_bank_statements.py --dir /path/to/pdfs --dry-run
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine

from core.bank_import import BankImportOrchestrator


# Configuration par défaut des fichiers
DEFAULT_FILE_CONFIG = {
    # L'Incontournable (Restaurant)
    "l'incontournable": {"entity": "RESTO", "account": "LCL Principal"},
    "incontournable": {"entity": "RESTO", "account": "LCL Principal"},
    # Noutam (Épicerie)
    "noutam": {"entity": "EPICERIE", "account": "LCL Noutam"},
    "comptecourant_00459448258": {"entity": "EPICERIE", "account": "LCL Noutam"},
    # BNP Angele
    "bnp": {"entity": "RESTO", "account": "BNP Angele"},
    "angele": {"entity": "RESTO", "account": "BNP Angele"},
    # SumUp
    "sumup": {"entity": "RESTO", "account": "SumUp"},
}


def guess_config(filename: str) -> dict:
    """Devine la configuration (entité/compte) à partir du nom de fichier."""
    filename_lower = filename.lower()

    for pattern, config in DEFAULT_FILE_CONFIG.items():
        if pattern in filename_lower:
            return config

    # Défaut
    return {"entity": "EPICERIE", "account": "LCL Default"}


def import_file(
    orchestrator: BankImportOrchestrator,
    pdf_path: Path,
    entity: str = None,
    account: str = None,
) -> dict:
    """Importe un fichier PDF."""
    config = guess_config(pdf_path.name)
    entity = entity or config["entity"]
    account = account or config["account"]

    result = orchestrator.import_pdf(
        pdf_path=pdf_path,
        entity_code=entity,
        account_label=account,
    )

    return {
        "file": pdf_path.name,
        "entity": entity,
        "account": account,
        "status": result.status.value,
        "periods": result.statements_detected,
        "total": result.transactions_total,
        "inserted": result.transactions_inserted,
        "duplicates": result.transactions_duplicates,
        "errors": result.errors[:3] if result.errors else [],
    }


def main():
    parser = argparse.ArgumentParser(description="Import bank statement PDFs")
    parser.add_argument("--dir", "-d", help="Directory containing PDF files")
    parser.add_argument("--file", "-f", help="Single PDF file to import")
    parser.add_argument("--entity", "-e", help="Entity code (RESTO, EPICERIE)")
    parser.add_argument("--account", "-a", help="Account label")
    parser.add_argument("--dry-run", action="store_true", help="Parse without inserting")
    parser.add_argument("--database-url", help="Database URL (or use DATABASE_URL env var)")

    args = parser.parse_args()

    if not args.dir and not args.file:
        parser.error("Either --dir or --file is required")

    # Database connection
    db_url = args.database_url or os.environ.get("DATABASE_URL")
    if not db_url and not args.dry_run:
        parser.error("DATABASE_URL required (use --database-url or set env var)")

    engine = None if args.dry_run else create_engine(db_url)
    orchestrator = BankImportOrchestrator(engine=engine, dry_run=args.dry_run)

    # Collect files
    pdf_files = []
    if args.file:
        pdf_files.append(Path(args.file))
    if args.dir:
        pdf_files.extend(sorted(Path(args.dir).glob("*.pdf")))

    if not pdf_files:
        print("No PDF files found")
        return 1

    # Import
    print("=" * 70)
    print("IMPORT DES RELEVÉS BANCAIRES")
    if args.dry_run:
        print("(MODE DRY-RUN - pas d'insertion en base)")
    print("=" * 70)

    total_inserted = 0
    total_duplicates = 0
    total_errors = 0

    for pdf_path in pdf_files:
        if not pdf_path.exists():
            print(f"File not found: {pdf_path}")
            continue

        result = import_file(
            orchestrator,
            pdf_path,
            entity=args.entity,
            account=args.account,
        )

        status_icon = "✓" if result["status"] == "success" else "⚠" if result["status"] == "partial" else "✗"
        print(f"\n{status_icon} {result['file']}")
        print(f"  {result['entity']} / {result['account']}")
        print(f"  {result['periods']} périodes | {result['inserted']}/{result['total']} transactions")

        if result["duplicates"]:
            print(f"  {result['duplicates']} doublons ignorés")

        for err in result["errors"]:
            print(f"  ❌ {err}")

        total_inserted += result["inserted"]
        total_duplicates += result["duplicates"]
        if result["status"] == "failed":
            total_errors += 1

    print("\n" + "=" * 70)
    print(f"TOTAL: {total_inserted} transactions insérées, {total_duplicates} doublons, {total_errors} erreurs")
    print("=" * 70)

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
