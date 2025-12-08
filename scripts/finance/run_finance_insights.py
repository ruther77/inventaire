"""CLI pour rafraîchir les récurrences et anomalies finance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path as _PathHelper
import sys

sys.path.append(str(_PathHelper(__file__).resolve().parents[1]))

from core.tenant_service import ensure_tenants_table
from core.data_repository import get_engine
from sqlalchemy import text
from core.finance import insights as insights_core


def _resolve_tenant_id(code: str) -> int:
    ensure_tenants_table()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(text("SELECT id FROM tenants WHERE code = :code"), {"code": code}).fetchone()
    if not row:
        raise SystemExit(f"Tenant '{code}' introuvable.")
    return int(row.id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rafraîchir récurrences/anomalies financières.")
    parser.add_argument("--tenant", default="epicerie", help="Code tenant.")
    parser.add_argument(
        "--mode",
        choices=["recurring", "anomalies", "all"],
        default="all",
        help="Type de traitement à lancer.",
    )
    parser.add_argument("--min-occ", type=int, default=3, help="Occurrences mini pour les stats.")
    parser.add_argument("--zscore", type=float, default=2.5, help="Seuil z-score anomalies.")
    args = parser.parse_args()

    tenant_id = _resolve_tenant_id(args.tenant)
    summary: dict[str, int] = {}
    if args.mode in {"recurring", "all"}:
        summary.update(
            insights_core.refresh_recurring_expenses(tenant_id, min_occurrences=args.min_occ)
        )
    if args.mode in {"anomalies", "all"}:
        summary.update(
            insights_core.refresh_anomaly_flags(
                tenant_id,
                zscore_threshold=args.zscore,
                min_occurrences=args.min_occ,
            )
        )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
