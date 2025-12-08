"""CLI pour recalculer la classification ABC-XYZ."""

from __future__ import annotations

import argparse
import json
from pathlib import Path as _PathHelper
import sys

sys.path.append(str(_PathHelper(__file__).resolve().parents[1]))

from core.tenant_service import ensure_tenants_table
from core.data_repository import get_engine
from sqlalchemy import text
from core.inventory_classification import classify_inventory


def _resolve_tenant_id(code: str) -> int:
    ensure_tenants_table()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(text("SELECT id FROM tenants WHERE code = :code"), {"code": code}).fetchone()
    if not row:
        raise SystemExit(f"Tenant '{code}' introuvable.")
    return int(row.id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Recalcule la classification ABC/XYZ.")
    parser.add_argument("--tenant", default="epicerie", help="Code tenant.")
    args = parser.parse_args()

    tenant_id = _resolve_tenant_id(args.tenant)
    summary = classify_inventory(tenant_id=tenant_id)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
