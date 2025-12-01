#!/usr/bin/env bash
set -euo pipefail

# Automates parsing PDFs and loading into Postgres.
# Requires:
#   - pdftotext in PATH
#   - psycopg2 installed (for load step)
#   - PG env vars or --dsn passed through args
#
# Usage:
#   scripts/run_bank_pipeline.sh [--input-dir DIR] [--output FILE] [--dsn DSN]
#
# Defaults:
#   --input-dir pdfs
#   --output pdfs/parsed_bank_entries_by_period.json

# Activate local venv if present and not already in a venv
if [ -z "$VIRTUAL_ENV" ] && [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate
fi

INPUT_DIR="pdfs"
OUTPUT="pdfs/parsed_bank_entries_by_period.json"
DSN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input-dir) INPUT_DIR="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --dsn) DSN="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

echo "Running auto_parse_lcl.py ..."
python3 scripts/auto_parse_lcl.py --input-dir "${INPUT_DIR}" --output "${OUTPUT}"

echo "Running load_bank_entries.py ..."
if [[ -n "${DSN}" ]]; then
  python3 scripts/load_bank_entries.py --json "${OUTPUT}" --dsn "${DSN}"
else
  python3 scripts/load_bank_entries.py --json "${OUTPUT}"
fi

# Post-load normalization (Entrée/Sortie + catégories + charges + centres de coûts) for tenant 1 (Epicerie HQ)
echo "Normalizing types (Entrée/Sortie), recategorizing, creating charges, applying cost centers ..."
if [[ -n "${DSN}" ]]; then
  python3 scripts/normalize_bank_types.py --tenant 1 || true
  python3 scripts/reclassify_bank_statements.py --tenant 1 || true
  python3 scripts/auto_create_charges.py --tenant 1 || true
  python3 scripts/apply_cost_centers.py --tenant 1 || true
else
  python3 scripts/normalize_bank_types.py --tenant 1 || true
  python3 scripts/reclassify_bank_statements.py --tenant 1 || true
  python3 scripts/auto_create_charges.py --tenant 1 || true
  python3 scripts/apply_cost_centers.py --tenant 1 || true
fi

echo "Bank pipeline completed."
