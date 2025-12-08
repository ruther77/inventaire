"""Export restaurant sales consumption view for reconciliation."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from core.data_repository import query_df


SQL = """
SELECT
    s.tenant_id,
    s.produit_restaurant_id,
    rp.nom AS restaurant_plat,
    s.produit_epicerie_id,
    s.epicerie_nom,
    s.epicerie_categorie,
    s.prix_achat,
    s.prix_vente,
    s.stock_actuel,
    s.quantity_consumed,
    s.bottles_required,
    s.cost_spent,
    s.stock_after_sales,
    s.last_sale_at
FROM restaurant_sales_consumptions s
LEFT JOIN restaurant_plats rp ON rp.id = s.produit_restaurant_id
ORDER BY s.epicerie_nom NULLS LAST, rp.nom NULLS LAST;
"""


def build_output_path(base: Path | None) -> Path:
    if base:
        return base
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return Path(f"reports/restaurant_sales_consumptions_{timestamp}.csv")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export restaurant sales consumption data for the dashboard."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional CSV path (default writes under reports/)",
    )
    args = parser.parse_args()

    df = query_df(SQL)
    if df.empty:
        print("Aucune consommation restaurant enregistrée.")
        return

    output_path = build_output_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    total_cost = df["cost_spent"].sum()
    total_bottles = df["bottles_required"].sum()

    print(f"Exported {len(df)} lignes vers {output_path}")
    print(f"Coût total estimé : {total_cost:.2f} €")
    print(f"Bouteilles (équivalent) requises : {total_bottles:.2f}")


if __name__ == "__main__":
    main()
