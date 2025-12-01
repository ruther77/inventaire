"""Crée automatiquement les ingrédients restaurant à partir des produits Epicerie associés."""

from __future__ import annotations

from sqlalchemy import text

from core.data_repository import exec_sql, exec_sql_return_id, query_df


MAPPING_SQL = """
SELECT
    rp.id AS plat_id,
    rp.nom AS plat_nom,
    rp.categorie AS plat_categorie,
    map.ratio,
    p.id AS produit_epicerie_id,
    p.nom AS epicerie_nom,
    p.categorie AS epicerie_categorie,
    COALESCE(p.prix_achat, 0) AS prix_achat
FROM restaurant_epicerie_sku_map map
JOIN restaurant_plats rp ON rp.id = map.produit_restaurant_id AND rp.tenant_id = map.tenant_restaurant
LEFT JOIN produits p ON p.id = map.produit_epicerie_id AND p.tenant_id = map.tenant_epicerie
WHERE map.tenant_restaurant = :tenant
ORDER BY rp.nom;
"""


def _guess_unit(category: str | None) -> str:
    normalized = (category or '').lower()
    if 'champagne' in normalized or 'whisky' in normalized or 'spiritueux' in normalized or 'alcool' in normalized or 'bouteille' in normalized:
        return 'bouteille'
    if 'bière' in normalized or 'biere' in normalized:
        return 'bouteille'
    if 'softs' in normalized or 'jus' in normalized or 'boissons' in normalized:
        return 'bouteille'
    return 'unit'


def ensure_ingredient(name: str, unit: str, cost: float) -> int:
    existing = query_df(
        text(
            """
            SELECT id
            FROM restaurant_ingredients
            WHERE tenant_id = 2
              AND LOWER(nom) = LOWER(:name)
            LIMIT 1;
            """
        ),
        {"name": name},
    )
    if not existing.empty:
        return int(existing.iloc[0]['id'])

    return exec_sql_return_id(
        text(
            """
            INSERT INTO restaurant_ingredients (tenant_id, nom, unite_base, cout_unitaire, stock_actuel)
            VALUES (2, :name, :unit, :cost, 0)
            RETURNING id;
            """
        ),
        {"name": name, "unit": unit, "cost": cost},
    )


def ensure_plat_ingredient(plat_id: int, ingredient_id: int, quantite: float, unit: str) -> None:
    exec_sql(
        text(
            """
            INSERT INTO restaurant_plat_ingredients (tenant_id, plat_id, ingredient_id, quantite, unite)
            VALUES (2, :plat_id, :ingredient_id, :quantite, :unit)
            ON CONFLICT (plat_id, ingredient_id)
            DO UPDATE SET quantite = EXCLUDED.quantite, unite = EXCLUDED.unite;
            """
        ),
        {
            "plat_id": plat_id,
            "ingredient_id": ingredient_id,
            "quantite": quantite,
            "unit": unit,
        },
    )


def gather_mappings(tenant_id: int = 2):
    df = query_df(text(MAPPING_SQL), {"tenant": tenant_id})
    return df.to_dict("records")


def main() -> None:
    insertions = 0
    for mapping in gather_mappings():
        ingredient_name = mapping.get('epicerie_nom') or f"{mapping['plat_nom']} ingredient"
        unit = _guess_unit(mapping.get('epicerie_categorie'))
        cost = float(mapping.get('prix_achat') or 0)
        ingredient_id = ensure_ingredient(ingredient_name, unit, cost)
        quantity = float(mapping.get('ratio') or 1)
        ensure_plat_ingredient(mapping['plat_id'], ingredient_id, quantity, unit)
        insertions += 1
    print(f"{insertions} fiches techniques synchronisées.")


if __name__ == "__main__":
    main()
