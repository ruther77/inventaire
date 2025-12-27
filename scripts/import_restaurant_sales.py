#!/usr/bin/env python3
"""Import restaurant sales from SumUp order CSV files.

Scans the "rapport-de-commandes" folders under the default data directory
and inserts rows into restaurant_sales (no stock movements).
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.restaurant.sales_import import import_sales_csv_bytes

DEFAULT_DATA_DIR = PROJECT_ROOT / "Ventes & Mouvement Stock & Comptabilite Restaurant"


def _find_sales_csvs(base_dir: Path) -> list[Path]:
    return sorted(base_dir.glob("rapport-de-commandes-*/rapport-de-commandes-produits-*.csv"))


def _print_summary(summary: dict) -> None:
    print(
        "  - {filename}: {rows_inserted} inserted, {rows_unmapped} unmapped, {rows_duplicates} duplicates".format(
            filename=summary.get("filename") or "(unknown)",
            rows_inserted=summary.get("rows_inserted", 0),
            rows_unmapped=summary.get("rows_unmapped", 0),
            rows_duplicates=summary.get("rows_duplicates", 0),
        )
    )

    examples = summary.get("unmapped_examples") or []
    if examples:
        preview = ", ".join(item["product"] for item in examples[:5])
        print(f"    unmapped examples: {preview}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import restaurant sales CSV files")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Base data directory (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument("--tenant-id", type=int, default=2, help="Restaurant tenant id")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, no database insert")

    args = parser.parse_args()

    if not args.data_dir.exists():
        print(f"Data directory not found: {args.data_dir}")
        return

    csv_files = _find_sales_csvs(args.data_dir)
    if not csv_files:
        print("No sales CSV files found.")
        return

    totals = {
        "rows_total": 0,
        "rows_valid": 0,
        "rows_mapped": 0,
        "rows_unmapped": 0,
        "rows_inserted": 0,
        "rows_duplicates": 0,
    }

    print(f"Found {len(csv_files)} sales files")
    for csv_path in csv_files:
        content = csv_path.read_bytes()
        summary = import_sales_csv_bytes(
            content,
            tenant_id=args.tenant_id,
            filename=csv_path.name,
            dry_run=args.dry_run,
        )
        _print_summary(summary)

        for key in totals:
            totals[key] += int(summary.get(key, 0) or 0)

    print("\nTotals:")
    for key, value in totals.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
