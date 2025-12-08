#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

export PGHOST=127.0.0.1
export PGPORT=5432
export PGUSER=postgres
export PGPASSWORD=postgres

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL non défini : export DATABASE_URL=\"postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/epicerie\""
  exit 1
fi

if [[ ! -f /var/log/capital_snapshot.log ]]; then
  echo "Log /var/log/capital_snapshot.log absent"
else
  echo "--- Dernières lignes du log ---"
  tail -n 20 /var/log/capital_snapshot.log || true
fi

echo
echo "--- Derniers snapshots ---"
psql "$DATABASE_URL" -c "SELECT tenant_id, snapshot_date, stock_value, bank_balance, cash_balance, total_assets FROM capital_snapshot ORDER BY snapshot_date DESC LIMIT 5;"
