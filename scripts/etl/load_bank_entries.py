"""
Ingest parsed LCL entries into Postgres with idempotent upsert.

Prereqs:
  - Run `python3 scripts/auto_parse_lcl.py` to produce pdfs/parsed_bank_entries_by_period.json
  - Set env vars: PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE (or a DSN via --dsn)

Usage:
  python3 scripts/load_bank_entries.py --json pdfs/parsed_bank_entries_by_period.json [--dsn postgres://...]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import psycopg2
from psycopg2.extras import execute_values


SCHEMA_STATEMENTS = """
CREATE TABLE IF NOT EXISTS bank_statements (
    statement_id TEXT PRIMARY KEY,
    account TEXT NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS bank_entries (
    hash TEXT PRIMARY KEY,
    statement_id TEXT NOT NULL REFERENCES bank_statements(statement_id) ON DELETE CASCADE,
    account TEXT NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    operation_date DATE NOT NULL,
    value_date DATE NOT NULL,
    label_raw TEXT NOT NULL,
    label_normalized TEXT NOT NULL,
    label_canonical TEXT NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    currency TEXT NOT NULL,
    direction TEXT NOT NULL,
    type TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bank_entries_value_date ON bank_entries(value_date);
CREATE INDEX IF NOT EXISTS idx_bank_entries_account ON bank_entries(account);
CREATE INDEX IF NOT EXISTS idx_bank_entries_type ON bank_entries(type);
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load parsed LCL entries JSON into Postgres.")
    parser.add_argument("--json", type=Path, default=Path("pdfs/parsed_bank_entries_by_period.json"))
    parser.add_argument("--dsn", type=str, default=None, help="Postgres DSN. If not set, use env PG*.")
    return parser.parse_args()


def connect(dsn: str | None):
    if dsn:
        return psycopg2.connect(dsn)
    # fallback to env PG* vars
    params = {
        "host": os.getenv("PGHOST", "localhost"),
        "port": os.getenv("PGPORT", "5432"),
        "user": os.getenv("PGUSER"),
        "password": os.getenv("PGPASSWORD"),
        "dbname": os.getenv("PGDATABASE"),
    }
    return psycopg2.connect(**params)


def load_json(path: Path) -> List[Dict[str, Any]]:
    return json.loads(path.read_text())


def upsert_statements(cur, rows: List[Tuple[str, str, str, str]]) -> None:
    sql = """
    INSERT INTO bank_statements (statement_id, account, period_start, period_end)
    VALUES %s
    ON CONFLICT (statement_id) DO UPDATE
      SET account = EXCLUDED.account,
          period_start = EXCLUDED.period_start,
          period_end = EXCLUDED.period_end;
    """
    execute_values(cur, sql, rows, template="(%s,%s,%s,%s)")


def upsert_entries(cur, rows: List[Tuple]) -> None:
    sql = """
    INSERT INTO bank_entries (
      hash, statement_id, account, period_start, period_end,
      operation_date, value_date, label_raw, label_normalized, label_canonical,
      amount, currency, direction, type
    )
    VALUES %s
    ON CONFLICT (hash) DO UPDATE
      SET statement_id = EXCLUDED.statement_id,
          account = EXCLUDED.account,
          period_start = EXCLUDED.period_start,
          period_end = EXCLUDED.period_end,
          operation_date = EXCLUDED.operation_date,
          value_date = EXCLUDED.value_date,
          label_raw = EXCLUDED.label_raw,
          label_normalized = EXCLUDED.label_normalized,
          label_canonical = EXCLUDED.label_canonical,
          amount = EXCLUDED.amount,
          currency = EXCLUDED.currency,
          direction = EXCLUDED.direction,
          type = EXCLUDED.type;
    """
    execute_values(cur, sql, rows)


def main() -> None:
    args = parse_args()
    if not args.json.exists():
        print(f"JSON not found: {args.json}", file=sys.stderr)
        sys.exit(1)

    data = load_json(args.json)
    statements = {}
    entry_rows = []

    for e in data:
        sid = e["statement_id"]
        statements[sid] = (
            sid,
            e["account"],
            e["period_start"],
            e["period_end"],
        )
        entry_rows.append(
            (
                e["hash"],
                sid,
                e["account"],
                e["period_start"],
                e["period_end"],
                e["operation_date"],
                e["value_date"],
                e["label_raw"],
                e["label_normalized"],
                e["label_canonical"],
                e["amount"],
                e["currency"],
                e["direction"],
                e["type"],
            )
        )

    conn = connect(args.dsn)
    conn.autocommit = False
    with conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_STATEMENTS)
            upsert_statements(cur, list(statements.values()))
            upsert_entries(cur, entry_rows)
    conn.close()
    print(f"Loaded {len(entry_rows)} entries and {len(statements)} statements into Postgres.")


if __name__ == "__main__":
    main()
