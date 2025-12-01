#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SQL_FILE="$ROOT/scripts/update_epicerie_costs.sql"

if [ ! -f "$SQL_FILE" ]; then
  echo "SQL file missing: $SQL_FILE" >&2
  exit 1
fi

docker compose exec -T db psql -U postgres -d epicerie < "$SQL_FILE"
