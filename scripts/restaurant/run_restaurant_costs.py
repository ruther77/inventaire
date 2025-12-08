"""CLI pour recalculer les coûts/marges des plats restaurant."""

from __future__ import annotations

import argparse
import json
from pathlib import Path as _PathHelper
import sys

sys.path.append(str(_PathHelper(__file__).resolve().parents[1]))

from core.tenant_service import ensure_tenants_table
from core.data_repository import get_engine
from sqlalchemy import text
from core import restaurant_costs


def _resolve_tenant_id(code: str) -> int:
    ensure_tenants_table()
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(text("SELECT id FROM tenants WHERE code = :code"), {"code": code}).fetchone()
    if not row:
        raise SystemExit(f"Tenant '{code}' introuvable.")
    return int(row.id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Recalcule les coûts matière des plats restaurant.")
    parser.add_argument("--tenant", default="restaurant", help="Code tenant.")
    parser.add_argument("--threshold", type=float, default=35.0, help="Seuil de marge (%) pour les alertes.")
    args = parser.parse_args()

    tenant_id = _resolve_tenant_id(args.tenant)
    summary = restaurant_costs.refresh_plat_costs(tenant_id=tenant_id, margin_threshold=args.threshold)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
