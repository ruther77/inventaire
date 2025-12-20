"""Services de mapping et de synchronisation Épicerie-Restaurant."""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import text

from core.data_repository import get_engine, query_df, exec_sql, exec_sql_return_id


def list_sales_consumptions(tenant_id: int, period: str = "all") -> list[Dict[str, Any]]:
    """Retourne tous les ingrédients liés aux produits Épicerie avec leurs données de consommation.

    Affiche TOUS les ingrédients liés, même ceux présents dans des plats sans ventes (qty=0).
    Utilise le nouveau système d'ingrédients (restaurant_plat_ingredients + restaurant_ingredients).

    Args:
        tenant_id: ID du tenant restaurant
        period: Filtre temporel - 7d, 30d, 90d, 1y ou all
    """
    # Construire un filtre de dates selon la période
    period_filter = ""
    if period == "7d":
        period_filter = "AND s.sold_at >= CURRENT_DATE - INTERVAL '7 days'"
    elif period == "30d":
        period_filter = "AND s.sold_at >= CURRENT_DATE - INTERVAL '30 days'"
    elif period == "90d":
        period_filter = "AND s.sold_at >= CURRENT_DATE - INTERVAL '90 days'"
    elif period == "1y":
        period_filter = "AND s.sold_at >= CURRENT_DATE - INTERVAL '1 year'"
    # 'all' means no filter

    # Partir des ingrédients (pour inclure tous les ingrédients liés)
    # LEFT JOIN vers les ventes pour inclure les ingrédients sans ventes
    sql = text(
        f"""
        SELECT
            ri.tenant_id,
            rp.id AS produit_restaurant_id,
            rp.nom AS restaurant_plat,
            ri.id AS ingredient_id,
            ri.produit_epicerie_id,
            COALESCE(p.nom, ri.nom) AS epicerie_nom,
            COALESCE(p.categorie, ri.categorie, '') AS epicerie_categorie,
            COALESCE(p.prix_achat, ri.cout_unitaire, 0) AS prix_achat,
            COALESCE(p.prix_vente, 0) AS prix_vente,
            COALESCE(p.stock_actuel, ri.stock_actuel, 0) AS stock_actuel,
            COALESCE(SUM(
                CASE WHEN s.id IS NOT NULL THEN s.quantity * COALESCE(rpi.quantite, 1) * COALESCE(ri.ratio_epicerie, 1) ELSE 0 END
            ), 0) AS quantity_consumed,
            CEIL(COALESCE(SUM(
                CASE WHEN s.id IS NOT NULL THEN s.quantity * COALESCE(rpi.quantite, 1) * COALESCE(ri.ratio_epicerie, 1) ELSE 0 END
            ), 0)) AS bottles_required,
            COALESCE(SUM(
                CASE WHEN s.id IS NOT NULL THEN s.quantity * COALESCE(rpi.quantite, 1) * COALESCE(p.prix_achat, ri.cout_unitaire, 0) ELSE 0 END
            ), 0) AS cost_spent,
            COALESCE(p.stock_actuel, ri.stock_actuel, 0) - COALESCE(SUM(
                CASE WHEN s.id IS NOT NULL THEN s.quantity * COALESCE(rpi.quantite, 1) * COALESCE(ri.ratio_epicerie, 1) ELSE 0 END
            ), 0) AS stock_after_sales,
            MAX(s.sold_at) AS last_sale_at
        FROM restaurant_ingredients ri
        JOIN restaurant_plat_ingredients rpi ON rpi.ingredient_id = ri.id AND rpi.tenant_id = ri.tenant_id
        JOIN restaurant_plats rp ON rp.id = rpi.plat_id AND rp.tenant_id = rpi.tenant_id
        LEFT JOIN produits p ON p.id = ri.produit_epicerie_id AND p.tenant_id = 1
        LEFT JOIN restaurant_sales s ON s.plat_id = rp.id AND s.tenant_id = rp.tenant_id
            {period_filter}
        WHERE ri.tenant_id = :tenant
        GROUP BY ri.tenant_id, rp.id, rp.nom, ri.id, ri.nom, ri.produit_epicerie_id,
                 p.nom, p.categorie, p.prix_achat, p.prix_vente, p.stock_actuel,
                 ri.cout_unitaire, ri.categorie, ri.stock_actuel
        ORDER BY epicerie_nom NULLS LAST, quantity_consumed DESC NULLS LAST
        """
    )
    df = query_df(sql, {"tenant": tenant_id})
    if df.empty:
        return []

    # Utiliser la sérialisation JSON pour convertir tous les types en natifs Python
    import json
    import pandas as pd

    # Remplacer NaN par None
    df = df.where(pd.notnull(df), None)

    # Convertir les colonnes entières qui peuvent contenir None
    int_cols = ['tenant_id', 'produit_restaurant_id', 'ingredient_id', 'produit_epicerie_id']
    for col in int_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: int(x) if x is not None and not pd.isna(x) else None)

    # Convertir via JSON pour garantir des types natifs Python
    records = json.loads(df.to_json(orient='records', date_format='iso'))

    return records


def sync_ingredients_from_mappings(tenant_id: int = 2) -> int:
    """Synchronise les ingrédients à partir des mappings SKU épicerie-restaurant."""
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
    """Retourne l'historique des prix restaurant avec les coûts Épicerie associés."""
    import math
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
    # Convertir NaN en None pour la sérialisation JSON
    records = df.to_dict("records")
    for record in records:
        for key, value in record.items():
            if isinstance(value, float) and math.isnan(value):
                record[key] = None
    return records


def list_plat_epicerie_links(tenant_id: int) -> list[Dict[str, Any]]:
    """Liste tous les liens plat-produit épicerie."""
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
    # Convertir NaN en None pour la sérialisation JSON
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
    """Crée ou met à jour un mapping plat-épicerie et synchronise les coûts des ingrédients."""
    # 1. Upsert du mapping
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

    # 2. Récupérer les informations produit épicerie
    prod_df = query_df(
        text("SELECT nom, categorie, prix_achat FROM produits WHERE id = :id AND tenant_id = :tenant"),
        {"id": produit_epicerie_id, "tenant": tenant_epicerie},
    )
    if not prod_df.empty:
        epicerie_nom = prod_df.iloc[0]["nom"]
        epicerie_categorie = prod_df.iloc[0]["categorie"]
        prix_achat = float(prod_df.iloc[0]["prix_achat"] or 0)

        # Deviner l'unité depuis la catégorie
        normalized = (epicerie_categorie or '').lower()
        if any(kw in normalized for kw in ('champagne', 'whisky', 'spiritueux', 'alcool', 'bouteille', 'biere', 'softs', 'jus', 'boissons')):
            unit = 'bouteille'
        else:
            unit = 'unit'

        # 3. Créer ou mettre à jour l'ingrédient
        existing = query_df(
            text("SELECT id FROM restaurant_ingredients WHERE tenant_id = :tenant AND LOWER(nom) = LOWER(:name) LIMIT 1"),
            {"tenant": tenant_restaurant, "name": epicerie_nom},
        )
        if not existing.empty:
            ingredient_id = int(existing.iloc[0]["id"])
            # Mettre à jour le prix
            exec_sql(
                text("UPDATE restaurant_ingredients SET cout_unitaire = :cost WHERE id = :id"),
                {"id": ingredient_id, "cost": prix_achat},
            )
        else:
            ingredient_id = exec_sql_return_id(
                text("""
                    INSERT INTO restaurant_ingredients (tenant_id, nom, unite_base, cout_unitaire, stock_actuel)
                    VALUES (:tenant, :name, :unit, :cost, 0)
                    RETURNING id
                """),
                {"tenant": tenant_restaurant, "name": epicerie_nom, "unit": unit, "cost": prix_achat},
            )

        # 4. Attacher l'ingrédient au plat
        exec_sql(
            text("""
                INSERT INTO restaurant_plat_ingredients (tenant_id, plat_id, ingredient_id, quantite, unite)
                VALUES (:tenant, :plat_id, :ingredient_id, :quantite, :unit)
                ON CONFLICT (plat_id, ingredient_id)
                DO UPDATE SET quantite = EXCLUDED.quantite, unite = EXCLUDED.unite
            """),
            {"tenant": tenant_restaurant, "plat_id": plat_id, "ingredient_id": ingredient_id, "quantite": ratio, "unit": unit},
        )

        # Note: refresh_plat_costs retiré pour performance
        # Les coûts seront recalculés lors de l'accès aux pages overview/food-cost

    return df.iloc[0].to_dict()


def delete_plat_epicerie_mapping(tenant_restaurant: int, plat_id: int) -> bool:
    """Supprime un mapping plat-épicerie."""
    sql = text(
        """
        DELETE FROM restaurant_epicerie_sku_map
        WHERE tenant_restaurant = :tenant_restaurant
          AND produit_restaurant_id = :plat_id
        """
    )
    exec_sql(sql, {"tenant_restaurant": tenant_restaurant, "plat_id": plat_id})

    # Note: refresh_plat_costs retiré pour performance
    # Les coûts seront recalculés lors de l'accès aux pages overview/food-cost

    return True


def list_epicerie_products(tenant_epicerie: int = 1) -> list[Dict[str, Any]]:
    """Liste tous les produits épicerie disponibles pour le mapping."""
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


def search_epicerie_products(
    tenant_epicerie: int = 1,
    query: str = "",
    limit: int = 20,
    suggest_for: str | None = None,
) -> list[Dict[str, Any]]:
    """
    Fast search for epicerie products with optional fuzzy suggestions.

    Args:
        tenant_epicerie: Tenant ID for epicerie
        query: Search term (searches in product name)
        suggest_for: If provided, uses fuzzy matching to find best matches for this ingredient
        limit: Max results to return
    """
    from rapidfuzz import fuzz

    # Requête de base avec filtre de recherche
    if query:
        sql = text(
            """
            SELECT
                id,
                nom,
                categorie,
                prix_achat,
                prix_vente
            FROM produits
            WHERE tenant_id = :tenant
              AND actif = TRUE
              AND LOWER(nom) LIKE :search
            ORDER BY
                CASE WHEN LOWER(nom) LIKE :exact THEN 0 ELSE 1 END,
                nom
            LIMIT :limit
            """
        )
        df = query_df(sql, {
            "tenant": tenant_epicerie,
            "search": f"%{query.lower()}%",
            "exact": f"{query.lower()}%",
            "limit": limit,
        })
    elif suggest_for:
        # Récupérer davantage de produits pour la correspondance floue
        sql = text(
            """
            SELECT
                id,
                nom,
                categorie,
                prix_achat,
                prix_vente
            FROM produits
            WHERE tenant_id = :tenant
              AND actif = TRUE
            """
        )
        df = query_df(sql, {"tenant": tenant_epicerie})
    else:
        # Sans requête, retourner les produits récents/populaires
        sql = text(
            """
            SELECT
                id,
                nom,
                categorie,
                prix_achat,
                prix_vente
            FROM produits
            WHERE tenant_id = :tenant
              AND actif = TRUE
            ORDER BY updated_at DESC NULLS LAST, nom
            LIMIT :limit
            """
        )
        df = query_df(sql, {"tenant": tenant_epicerie, "limit": limit})

    if df.empty:
        return []

    results = df.to_dict("records")

    # Appliquer le fuzzy matching si suggest_for est fourni
    if suggest_for:
        suggest_lower = suggest_for.lower().strip()
        words = suggest_lower.split()

        for product in results:
            product_name = product["nom"].lower()
            # Calculer le score flou
            score = fuzz.token_sort_ratio(suggest_lower, product_name)
            # Booster les correspondances de mots exacts
            if suggest_lower in product_name:
                score = max(score, 90)
            elif all(w in product_name for w in words):
                score = max(score, 80)
            elif words and words[0] in product_name:
                score = max(score, 60)
            product["match_score"] = score

        # Trier par score et conserver les meilleurs résultats
        results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        results = [r for r in results[:limit] if r.get("match_score", 0) >= 30]

    return results
