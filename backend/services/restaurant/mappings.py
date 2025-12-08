"""Epicerie-Restaurant mappings and sync services."""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import text

from core.data_repository import get_engine, query_df, exec_sql, exec_sql_return_id


def list_sales_consumptions(tenant_id: int) -> list[Dict[str, Any]]:
    """Return restaurant consumptions converted to Epicerie quantities."""
    sql = text(
        """
        SELECT *
        FROM restaurant_sales_consumptions
        WHERE tenant_id = :tenant
        ORDER BY epicerie_nom NULLS LAST, last_sale_at DESC NULLS LAST
        """
    )
    df = query_df(sql, {"tenant": tenant_id})
    if df.empty:
        return []
    return df.to_dict("records")


def sync_ingredients_from_mappings(tenant_id: int = 2) -> int:
    """Sync ingredients from epicerie-restaurant SKU mappings."""
    mapping_sql = """
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

    def guess_unit(category: str | None) -> str:
        normalized = (category or '').lower()
        if any(keyword in normalized for keyword in ('champagne', 'whisky', 'spiritueux', 'alcool', 'bouteille')):
            return 'bouteille'
        if any(keyword in normalized for keyword in ('biere', 'biere')):
            return 'bouteille'
        if any(keyword in normalized for keyword in ('softs', 'jus', 'boissons')):
            return 'bouteille'
        return 'unit'

    mappings = query_df(text(mapping_sql), {"tenant": tenant_id}).to_dict("records")
    inserted = 0
    for mapping in mappings:
        ingredient_name = mapping.get("epicerie_nom") or f"{mapping['plat_nom']} ingredient"
        unit = guess_unit(mapping.get("epicerie_categorie"))
        cost = float(mapping.get("prix_achat") or 0)
        existing = query_df(
            text(
                """
                SELECT id
                FROM restaurant_ingredients
                WHERE tenant_id = :tenant
                  AND LOWER(nom) = LOWER(:name)
                LIMIT 1;
                """
            ),
            {"tenant": tenant_id, "name": ingredient_name},
        )
        if not existing.empty:
            ingredient_id = int(existing.iloc[0]["id"])
        else:
            ingredient_id = exec_sql_return_id(
                text(
                    """
                    INSERT INTO restaurant_ingredients (tenant_id, nom, unite_base, cout_unitaire, stock_actuel)
                    VALUES (:tenant, :name, :unit, :cost, 0)
                    RETURNING id;
                    """
                ),
                {"tenant": tenant_id, "name": ingredient_name, "unit": unit, "cost": cost},
            )

        exec_sql(
            text(
                """
                INSERT INTO restaurant_plat_ingredients (tenant_id, plat_id, ingredient_id, quantite, unite)
                VALUES (:tenant, :plat_id, :ingredient_id, :quantite, :unit)
                ON CONFLICT (plat_id, ingredient_id)
                DO UPDATE SET quantite = EXCLUDED.quantite, unite = EXCLUDED.unite;
                """
            ),
            {
                "tenant": tenant_id,
                "plat_id": mapping["plat_id"],
                "ingredient_id": ingredient_id,
                "quantite": float(mapping.get("ratio") or 1),
                "unit": unit,
            },
        )
        inserted += 1
    return inserted


def list_combined_price_history(tenant_id: int) -> list[Dict[str, Any]]:
    """Return restaurant price history with linked Epicerie costs."""
    sql = text(
        """
        SELECT
            ph.plat_id,
            rp.nom AS plat_nom,
            ph.prix_vente_ttc,
            ph.changed_at AS plat_changed_at,
            p.id AS epicerie_id,
            p.nom AS epicerie_nom,
            p.prix_achat AS epicerie_prix_achat,
            NULL::timestamp AS epicerie_changed_at
        FROM restaurant_plat_price_history ph
        JOIN restaurant_plats rp ON rp.id = ph.plat_id AND rp.tenant_id = :tenant
        LEFT JOIN restaurant_epicerie_sku_map map
            ON map.produit_restaurant_id = ph.plat_id
            AND map.tenant_restaurant = rp.tenant_id
        LEFT JOIN produits p ON p.id = map.produit_epicerie_id AND p.tenant_id = map.tenant_epicerie
        ORDER BY ph.changed_at DESC
        """
    )
    df = query_df(sql, {"tenant": tenant_id})
    if df.empty:
        return []
    return df.to_dict("records")


def list_plat_epicerie_links(tenant_id: int) -> list[Dict[str, Any]]:
    """List all plat-epicerie product links."""
    import math
    sql = text(
        """
        SELECT
            rp.id AS plat_id,
            rp.nom AS plat_nom,
            rp.categorie AS plat_categorie,
            map.produit_epicerie_id,
            p.nom AS epicerie_nom,
            p.categorie AS epicerie_categorie,
            p.prix_achat,
            p.prix_vente,
            map.ratio
        FROM restaurant_plats rp
        LEFT JOIN restaurant_epicerie_sku_map map
            ON map.produit_restaurant_id = rp.id
            AND map.tenant_restaurant = rp.tenant_id
        LEFT JOIN produits p
            ON p.id = map.produit_epicerie_id
            AND p.tenant_id = map.tenant_epicerie
        WHERE rp.tenant_id = :tenant
        ORDER BY rp.categorie NULLS LAST, rp.nom
        """
    )
    df = query_df(sql, {"tenant": tenant_id})
    if df.empty:
        return []
    # Convert NaN to None for JSON serialization
    records = df.to_dict("records")
    for record in records:
        for key, value in record.items():
            if isinstance(value, float) and math.isnan(value):
                record[key] = None
    return records


def upsert_plat_epicerie_mapping(
    tenant_restaurant: int,
    plat_id: int,
    produit_epicerie_id: int,
    ratio: float = 1.0,
    tenant_epicerie: int = 1,
) -> Dict[str, Any]:
    """Create or update a plat-epicerie mapping."""
    sql = text(
        """
        INSERT INTO restaurant_epicerie_sku_map
            (tenant_restaurant, tenant_epicerie, produit_restaurant_id, produit_epicerie_id, ratio)
        VALUES (:tenant_restaurant, :tenant_epicerie, :plat_id, :produit_epicerie_id, :ratio)
        ON CONFLICT (tenant_restaurant, produit_restaurant_id)
        DO UPDATE SET
            produit_epicerie_id = EXCLUDED.produit_epicerie_id,
            ratio = EXCLUDED.ratio
        RETURNING id, tenant_restaurant, tenant_epicerie, produit_restaurant_id, produit_epicerie_id, ratio
        """
    )
    df = query_df(
        sql,
        {
            "tenant_restaurant": tenant_restaurant,
            "tenant_epicerie": tenant_epicerie,
            "plat_id": plat_id,
            "produit_epicerie_id": produit_epicerie_id,
            "ratio": ratio,
        },
    )
    if df.empty:
        return {}
    return df.iloc[0].to_dict()


def delete_plat_epicerie_mapping(tenant_restaurant: int, plat_id: int) -> bool:
    """Delete a plat-epicerie mapping."""
    sql = text(
        """
        DELETE FROM restaurant_epicerie_sku_map
        WHERE tenant_restaurant = :tenant_restaurant
          AND produit_restaurant_id = :plat_id
        """
    )
    exec_sql(sql, {"tenant_restaurant": tenant_restaurant, "plat_id": plat_id})
    return True


def list_epicerie_products(tenant_epicerie: int = 1) -> list[Dict[str, Any]]:
    """List all epicerie products available for mapping."""
    sql = text(
        """
        SELECT
            id,
            nom,
            categorie,
            prix_achat,
            prix_vente,
            stock_actuel,
            actif
        FROM produits
        WHERE tenant_id = :tenant
          AND actif = TRUE
        ORDER BY categorie NULLS LAST, nom
        """
    )
    df = query_df(sql, {"tenant": tenant_epicerie})
    if df.empty:
        return []
    return df.to_dict("records")
