"""CLI utilitaire pour lancer un rapprochement finance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path as _PathHelper

import sys
from sqlalchemy import text

sys.path.append(str(_PathHelper(__file__).resolve().parents[1]))

from core.data_repository import get_engine
from core.tenant_service import ensure_tenants_table
from core.finance import reconciliation as reconciliation_core


def _resolve_tenant_id(code: str) -> int:
    ensure_tenants_table()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(text("SELECT id FROM tenants WHERE code = :code"), {"code": code}).fetchone()
    if not row:
        raise SystemExit(f"Tenant '{code}' introuvable.")
    return int(row.id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rapprochement banque ⇄ factures.")
    parser.add_argument("--tenant", default="epicerie", help="Code tenant.")
    parser.add_argument("--amount-tolerance", type=float, default=2.0, help="Tolérance montant (€).")
    parser.add_argument("--max-days", type=int, default=10, help="Écart max (jours).")
    parser.add_argument("--auto-threshold", type=float, default=0.9, help="Score auto.")
    args = parser.parse_args()

    tenant_id = _resolve_tenant_id(args.tenant)
    summary = reconciliation_core.run_reconciliation_job(
        tenant_id,
        amount_tolerance=args.amount_tolerance,
        max_days_difference=args.max_days,
        auto_threshold=args.auto_threshold,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
