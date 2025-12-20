"""Services de gestion des ingrédients et des plats pour le module restaurant."""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import text

from core.data_repository import get_engine, query_df
from core import restaurant_costs
from backend.services.restaurant.utils import _safe_float


def list_ingredients(tenant_id: int) -> List[dict[str, Any]]:
    """Retourne les ingrédients disponibles pour composer les plats avec infos catégorie/fournisseur."""
    df = query_df(
        text(
            """
            SELECT
                ri.id,
                ri.nom,
                ri.unite_base,
                ri.cout_unitaire,
                ri.stock_actuel,
                ri.stock_min,
                COALESCE(ri.categorie, 'Non classé') AS categorie,
                COALESCE(
                    ri.fournisseur,
                    (
                        SELECT m.fournisseur
                        FROM restaurant_stock_movements m
                        WHERE m.ingredient_id = ri.id
                          AND m.fournisseur IS NOT NULL
                        ORDER BY m.date_mouvement DESC
                        LIMIT 1
                    ),
                    'Non renseigné'
                ) AS fournisseur,
                ri.produit_epicerie_id,
                ri.ratio_epicerie,
                p.nom AS produit_epicerie_nom,
                p.prix_achat AS produit_epicerie_prix
            FROM restaurant_ingredients ri
            LEFT JOIN produits p ON p.id = ri.produit_epicerie_id
            WHERE ri.tenant_id = :tenant
            ORDER BY ri.nom
            """
        ),
        {"tenant": tenant_id},
    )
    if df.empty:
        return []

    # Remplacer NaN par None pour la sérialisation JSON
    df = df.where(df.notna(), None)

    # Calculer la tendance de prix depuis l'historique récent si disponible
    results = df.to_dict("records")
    for ing in results:
        epicerie_price = ing.get("produit_epicerie_prix")
        ratio = ing.get("ratio_epicerie")
        ratio_value = 1.0
        if ratio is None or (isinstance(ratio, float) and ratio != ratio):
            ratio_value = 1.0
        else:
            ratio_value = float(ratio)
        ing["price_trend"] = None
        ing["price_evolution"] = None
        ing["price_history"] = []
        # S'assurer que produit_epicerie_id est un int ou None (gérer correctement les NaN)
        epicerie_id = ing.get("produit_epicerie_id")
        if epicerie_id is not None and not (isinstance(epicerie_id, float) and epicerie_id != epicerie_id):
            ing["produit_epicerie_id"] = int(epicerie_id)
        else:
            ing["produit_epicerie_id"] = None
        ing["ratio_epicerie"] = ratio_value
        if epicerie_price is not None:
            ing["cout_unitaire"] = float(epicerie_price or 0) * ratio_value

    return results


def create_ingredient(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Crée un ingrédient avec prix unitaire et stock initial."""
    produit_epicerie_id = payload.get("produit_epicerie_id")
    ratio = float(payload.get("ratio_epicerie") or 1.0)
    categorie = payload.get("categorie")
    fournisseur = payload.get("fournisseur")
    cout_unitaire = payload.get("cout_unitaire", 0)
    if produit_epicerie_id:
        prod_df = query_df(
            text(
                """
                SELECT p.nom, p.categorie, p.prix_achat,
                       (SELECT m.source FROM mouvements_stock m
                        WHERE m.produit_id = p.id AND m.source IS NOT NULL
                        ORDER BY m.date_mvt DESC LIMIT 1) AS fournisseur
                FROM produits p
                WHERE p.id = :produit_id
                """
            ),
            {"produit_id": produit_epicerie_id},
        )
        if prod_df.empty:
            raise RuntimeError(f"Produit épicerie {produit_epicerie_id} introuvable")
        prod = prod_df.iloc[0]
        categorie = categorie or prod["categorie"]
        fournisseur = fournisseur or prod["fournisseur"]
        cout_unitaire = float(prod["prix_achat"] or 0) * ratio

    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_ingredients (
                    tenant_id, nom, unite_base, cout_unitaire, stock_actuel,
                    stock_min, categorie, fournisseur, produit_epicerie_id, ratio_epicerie
                )
                VALUES (
                    :tenant, :nom, :unite_base, :cout_unitaire, :stock_actuel,
                    :stock_min, :categorie, :fournisseur, :produit_epicerie_id, :ratio_epicerie
                )
                RETURNING id, nom, unite_base, cout_unitaire, stock_actuel, stock_min, categorie, fournisseur, produit_epicerie_id, ratio_epicerie
                """
            ),
            {
                "tenant": tenant_id,
                "nom": payload.get("nom"),
                "unite_base": payload.get("unite_base", "kg"),
                "cout_unitaire": cout_unitaire,
                "stock_actuel": payload.get("stock_actuel", 0),
                "stock_min": payload.get("stock_min"),
                "categorie": categorie,
                "fournisseur": fournisseur,
                "produit_epicerie_id": produit_epicerie_id,
                "ratio_epicerie": ratio,
            },
        ).fetchone()
    result = dict(row._mapping)
    result["price_trend"] = None
    result["price_evolution"] = None
    result["price_history"] = []
    return result


def link_ingredient_to_epicerie(tenant_id: int, ingredient_id: int, produit_epicerie_id: int, ratio: float = 1.0) -> dict[str, Any]:
    """Lie un ingrédient à un produit épicerie et synchronise catégorie/fournisseur."""
    # Récupérer les infos produit épicerie
    prod_df = query_df(
        text("""
            SELECT p.nom, p.categorie, p.prix_achat,
                   (SELECT m.source FROM mouvements_stock m
                    WHERE m.produit_id = p.id AND m.source IS NOT NULL
                    ORDER BY m.date_mvt DESC LIMIT 1) AS fournisseur
            FROM produits p
            WHERE p.id = :produit_id
        """),
        {"produit_id": produit_epicerie_id},
    )

    if prod_df.empty:
        raise RuntimeError(f"Produit épicerie {produit_epicerie_id} introuvable")

    prod = prod_df.iloc[0]
    categorie = prod["categorie"]
    fournisseur = prod["fournisseur"]
    prix_achat = float(prod["prix_achat"] or 0)
    ratio_value = float(ratio or 1.0)

    # Mettre à jour l'ingrédient avec le lien
    with get_engine().begin() as conn:
        row = conn.execute(
            text("""
                UPDATE restaurant_ingredients
                SET produit_epicerie_id = :produit_epicerie_id,
                    ratio_epicerie = :ratio,
                    -- On impose la catégorie épicerie pour rester aligné
                    categorie = :categorie,
                    fournisseur = COALESCE(fournisseur, :fournisseur),
                    cout_unitaire = :prix_achat
                WHERE tenant_id = :tenant AND id = :ingredient_id
                RETURNING id, nom, unite_base, cout_unitaire, stock_actuel, stock_min, categorie, fournisseur, produit_epicerie_id, ratio_epicerie
            """),
            {
                "tenant": tenant_id,
                "ingredient_id": ingredient_id,
                "produit_epicerie_id": produit_epicerie_id,
                "ratio": ratio_value,
                "categorie": categorie,
                "fournisseur": fournisseur,
                "prix_achat": prix_achat * ratio_value,
            },
        ).fetchone()

        if not row:
            raise RuntimeError(f"Ingrédient {ingredient_id} introuvable")

    result = dict(row._mapping)
    result["price_trend"] = None
    result["price_evolution"] = None
    result["price_history"] = []
    return result


def unlink_ingredient_from_epicerie(tenant_id: int, ingredient_id: int) -> dict[str, Any]:
    """Retire le lien entre un ingrédient et un produit épicerie."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text("""
                UPDATE restaurant_ingredients
                SET produit_epicerie_id = NULL, ratio_epicerie = 1.0
                WHERE tenant_id = :tenant AND id = :ingredient_id
                RETURNING id, nom, unite_base, cout_unitaire, stock_actuel, stock_min, categorie, fournisseur, produit_epicerie_id, ratio_epicerie
            """),
            {"tenant": tenant_id, "ingredient_id": ingredient_id},
        ).fetchone()

        if not row:
            raise RuntimeError(f"Ingrédient {ingredient_id} introuvable")

    result = dict(row._mapping)
    result["price_trend"] = None
    result["price_evolution"] = None
    result["price_history"] = []
    result["ratio_epicerie"] = float(result.get("ratio_epicerie") or 1.0)
    return result


def update_ingredient_ratio(tenant_id: int, ingredient_id: int, ratio: float) -> dict[str, Any]:
    """Met à jour le ratio de conversion ingrédient/épicerie."""
    ratio_value = float(ratio or 1.0)
    with get_engine().begin() as conn:
        row = conn.execute(
            text("""
                UPDATE restaurant_ingredients
                SET ratio_epicerie = :ratio,
                    cout_unitaire = CASE
                        WHEN produit_epicerie_id IS NOT NULL THEN (
                            COALESCE(
                                (SELECT prix_achat FROM produits WHERE id = produit_epicerie_id),
                                cout_unitaire
                            ) * :ratio
                        )
                        ELSE cout_unitaire
                    END
                WHERE tenant_id = :tenant AND id = :ingredient_id
                RETURNING id, nom, unite_base, cout_unitaire, stock_actuel, stock_min, categorie, fournisseur, produit_epicerie_id, ratio_epicerie
            """),
            {"tenant": tenant_id, "ingredient_id": ingredient_id, "ratio": ratio_value},
        ).fetchone()

        if not row:
            raise RuntimeError(f"Ingrédient {ingredient_id} introuvable")

    result = dict(row._mapping)
    result["price_trend"] = None
    result["price_evolution"] = None
    result["price_history"] = []
    result["ratio_epicerie"] = float(result.get("ratio_epicerie") or 1.0)
    return result


def update_ingredient_price(tenant_id: int, ingredient_id: int, new_price: float) -> dict[str, Any]:
    """Met à jour le coût de l'ingrédient et recalcule les marges des plats."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                UPDATE restaurant_ingredients
                SET cout_unitaire = :price
                WHERE tenant_id = :tenant AND id = :ingredient_id
                RETURNING id, nom, unite_base, cout_unitaire, stock_actuel
                """
            ),
            {"tenant": tenant_id, "ingredient_id": ingredient_id, "price": new_price},
        ).fetchone()
        if not row:
            raise RuntimeError("Ingredient introuvable")
    refresh_plat_costs(tenant_id)
    return dict(row._mapping)


def list_plats(tenant_id: int) -> List[dict[str, Any]]:
    """Charge les plats avec marge brute calculée depuis les ingrédients.

    Le coût matière est calculé depuis:
    - quantite_batch * cout_unitaire de chaque ingrédient
    - Si l'ingrédient est lié à un produit épicerie, on utilise le prix_achat épicerie
    """
    plats_df = query_df(
        text(
            """
            WITH couts_ingredients AS (
                SELECT
                    pi.plat_id,
                    SUM(
                        pi.quantite *
                        COALESCE(
                            -- Priorité au prix épicerie si l'ingrédient est lié
                            (SELECT prix_achat FROM produits WHERE id = ri.produit_epicerie_id)
                              * COALESCE(ri.ratio_epicerie, 1.0),
                            -- Sinon prix ingrédient
                            ri.cout_unitaire,
                            0
                        )
                    ) AS cout_matiere
                FROM restaurant_plat_ingredients pi
                JOIN restaurant_ingredients ri ON ri.id = pi.ingredient_id
                WHERE pi.tenant_id = :tenant
                GROUP BY pi.plat_id
            )
            SELECT
                p.id,
                p.nom,
                p.categorie,
                p.prix_vente_ttc,
                p.actif,
                COALESCE(ci.cout_matiere, 0) AS cout_matiere
            FROM restaurant_plats p
            LEFT JOIN couts_ingredients ci ON ci.plat_id = p.id
            WHERE p.tenant_id = :tenant
            ORDER BY p.categorie, p.nom
            """
        ),
        {"tenant": tenant_id},
    )
    if plats_df.empty:
        return []

    plats_df["cout_matiere"] = plats_df["cout_matiere"].fillna(0.0)
    plats_df["marge_brute"] = plats_df["prix_vente_ttc"].fillna(0.0) - plats_df["cout_matiere"]
    plats_df["marge_pct"] = plats_df.apply(
        lambda row: (row["marge_brute"] / row["prix_vente_ttc"] * 100) if row["prix_vente_ttc"] else 0.0,
        axis=1,
    )
    # Food cost % = coût_matière / prix_vente * 100
    plats_df["food_cost_pct"] = plats_df.apply(
        lambda row: (row["cout_matiere"] / row["prix_vente_ttc"] * 100) if row["prix_vente_ttc"] else 0.0,
        axis=1,
    )

    plat_ids = plats_df["id"].tolist()
    ing_df = None
    if plat_ids:
        placeholder_tokens = []
        params: Dict[str, Any] = {"tenant": tenant_id}
        for idx, pid in enumerate(plat_ids):
            token = f"pid_{idx}"
            placeholder_tokens.append(f":{token}")
            params[token] = pid

        sql = text(
            f"""
            SELECT pi.id,
                   pi.plat_id,
                   pi.ingredient_id,
                   ri.nom,
                   pi.quantite AS quantite,
                   ri.unite_base AS unite,
                   COALESCE(
                       (SELECT prix_achat FROM produits WHERE id = ri.produit_epicerie_id)
                         * COALESCE(ri.ratio_epicerie, 1.0),
                       ri.cout_unitaire,
                       0
                   ) AS unit_price,
                   pi.quantite * COALESCE(
                       (SELECT prix_achat FROM produits WHERE id = ri.produit_epicerie_id)
                         * COALESCE(ri.ratio_epicerie, 1.0),
                       ri.cout_unitaire,
                       0
                   ) AS total_cost
            FROM restaurant_plat_ingredients pi
            JOIN restaurant_ingredients ri ON ri.id = pi.ingredient_id
            WHERE pi.tenant_id = :tenant
              AND pi.plat_id IN ({", ".join(placeholder_tokens)})
            """
        )
        ing_df = query_df(sql, params=params)

    grouped = {}
    if ing_df is not None and not ing_df.empty:
        for row in ing_df.to_dict("records"):
            grouped.setdefault(row["plat_id"], []).append(row)

    # Récupérer l'historique de prix pour tous les plats
    price_history_df = query_df(
        text("""
            SELECT plat_id, prix_vente_ttc as prix, changed_at::date as date
            FROM restaurant_plat_price_history
            WHERE tenant_id = :tenant
            ORDER BY plat_id, changed_at
        """),
        {"tenant": tenant_id},
    )

    price_history_grouped = {}
    if not price_history_df.empty:
        for row in price_history_df.to_dict("records"):
            price_history_grouped.setdefault(row["plat_id"], []).append({
                "prix": _safe_float(row["prix"]),
                "date": str(row["date"]),
            })

    results = []
    for plat in plats_df.to_dict("records"):
        plat["ingredients"] = grouped.get(plat["id"], [])
        plat["price_history"] = price_history_grouped.get(plat["id"], [])
        plat["cout_matiere"] = _safe_float(plat.get("cout_matiere"))
        plat["marge_brute"] = _safe_float(plat.get("marge_brute"))
        plat["marge_pct"] = _safe_float(plat.get("marge_pct"))
        plat["food_cost_pct"] = _safe_float(plat.get("food_cost_pct"))
        results.append(plat)
    return results


def refresh_plat_costs(tenant_id: int, margin_threshold: float = 35.0) -> dict[str, Any]:
    """Délègue le recalcul des coûts/marges aux utilitaires partagés."""
    return restaurant_costs.refresh_plat_costs(tenant_id=tenant_id, margin_threshold=margin_threshold)


def list_plat_alerts(tenant_id: int) -> List[dict[str, Any]]:
    """Retourne les alertes de marge générées par le recalcul précédent."""
    return restaurant_costs.list_margin_alerts(tenant_id=tenant_id)


def create_plat(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Crée un plat et initialise totaux/marges depuis les ingrédients liés."""
    # Mapper 'categorie' vers 'type' pour le nouveau schéma
    plat_type = payload.pop("categorie", "plat")
    with get_engine().begin() as conn:
        # Récupérer le restaurant_id pour ce tenant
        rest_row = conn.execute(
            text("SELECT id FROM restaurants WHERE tenant_id = :tenant LIMIT 1"),
            {"tenant": tenant_id},
        ).fetchone()
        restaurant_id = rest_row[0] if rest_row else 1

        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_plats (tenant_id, restaurant_id, nom, categorie, prix_vente_ttc, actif)
                VALUES (:tenant, :restaurant_id, :nom, :type, :prix_vente_ttc, :actif)
                RETURNING id, nom, categorie, prix_vente_ttc, actif
                """
            ),
            {**payload, "tenant": tenant_id, "restaurant_id": restaurant_id, "type": plat_type},
        ).fetchone()
    base = dict(row._mapping)
    price = _safe_float(base.get("prix_vente_ttc"))
    base.update(
        {
            "cout_matiere": 0.0,
            "marge_brute": price,
            "marge_pct": 100.0 if price else 0.0,
            "ingredients": [],
        }
    )
    refresh_plat_costs(tenant_id)
    return base


def attach_ingredient_to_plat(tenant_id: int, plat_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Associe un ingrédient à un plat avec recalcul des coûts."""
    # Mapper 'quantite' vers 'quantite_batch' pour le nouveau schéma
    quantite = payload.get("quantite", payload.get("quantite_batch", 0))
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO restaurant_plat_ingredients (tenant_id, plat_id, ingredient_id, quantite, unite)
                VALUES (:tenant, :plat_id, :ingredient_id, :quantite, :unite)
                ON CONFLICT (plat_id, ingredient_id)
                DO UPDATE SET quantite = EXCLUDED.quantite,
                              unite = COALESCE(EXCLUDED.unite, restaurant_plat_ingredients.unite)
                """
            ),
            {
                "tenant": tenant_id,
                "plat_id": plat_id,
                "ingredient_id": payload["ingredient_id"],
                "quantite": quantite,
                "unite": payload.get("unite"),
            },
        )
    refresh_plat_costs(tenant_id)
    plats = list_plats(tenant_id)
    updated = next((plat for plat in plats if plat["id"] == plat_id), None)
    return updated or {"status": "ok"}


def remove_ingredient_from_plat(tenant_id: int, plat_id: int, ingredient_id: int) -> dict[str, Any]:
    """Retire un ingrédient d'un plat et rafraîchit les coûts."""
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                DELETE FROM restaurant_plat_ingredients
                WHERE tenant_id = :tenant AND plat_id = :plat_id AND ingredient_id = :ingredient_id
                """
            ),
            {"tenant": tenant_id, "plat_id": plat_id, "ingredient_id": ingredient_id},
        )
    refresh_plat_costs(tenant_id)
    plats = list_plats(tenant_id)
    updated = next((plat for plat in plats if plat["id"] == plat_id), None)
    return updated or {"deleted": True, "plat_id": plat_id, "ingredient_id": ingredient_id}


def update_plat_ingredient(
    tenant_id: int,
    plat_id: int,
    ingredient_id: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Met à jour la quantité/unité d'un ingrédient du plat et rafraîchit les coûts."""
    fields = {}
    if "quantite" in payload and payload["quantite"] is not None:
        fields["quantite"] = float(payload["quantite"])
    if "unite" in payload and payload["unite"] is not None:
        fields["unite"] = payload["unite"]

    if not fields:
        raise ValueError("Aucun champ à mettre à jour pour l'ingrédient du plat")

    set_clause = ", ".join(f"{k} = :{k}" for k in fields.keys())
    params = {"tenant": tenant_id, "plat_id": plat_id, "ingredient_id": ingredient_id, **fields}

    with get_engine().begin() as conn:
        res = conn.execute(
            text(
                f"""
                UPDATE restaurant_plat_ingredients
                SET {set_clause}
                WHERE tenant_id = :tenant AND plat_id = :plat_id AND ingredient_id = :ingredient_id
                RETURNING id
                """
            ),
            params,
        ).fetchone()
        if not res:
            raise RuntimeError("Ingrédient non trouvé sur ce plat")

    refresh_plat_costs(tenant_id)
    plats = list_plats(tenant_id)
    updated = next((plat for plat in plats if plat["id"] == plat_id), None)
    return updated or {"status": "updated"}


def update_plat_price(tenant_id: int, plat_id: int, new_price: float) -> dict[str, Any]:
    """Met à jour le prix TTC du plat et recalcule les marges liées."""
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                UPDATE restaurant_plats
                SET prix_vente_ttc = :price
                WHERE tenant_id = :tenant AND id = :plat_id
                RETURNING id, nom, categorie, prix_vente_ttc, actif
                """
            ),
            {"tenant": tenant_id, "plat_id": plat_id, "price": new_price},
        ).fetchone()
        if not row:
            raise RuntimeError("Plat introuvable")
    refresh_plat_costs(tenant_id)
    plats = list_plats(tenant_id)
    updated = next((plat for plat in plats if plat["id"] == plat_id), None)
    return updated or dict(row._mapping)


def list_ingredient_price_history(tenant_id: int, ingredient_id: int) -> List[dict[str, Any]]:
    """Affiche l'historique des prix pour un ingrédient donné."""
    ingredient_df = query_df(
        text(
            """
            SELECT id, nom, produit_epicerie_id, ratio_epicerie
            FROM restaurant_ingredients
            WHERE tenant_id = :tenant AND id = :ingredient
            """
        ),
        {"tenant": tenant_id, "ingredient": ingredient_id},
    )
    if ingredient_df.empty:
        return []

    ingredient_row = ingredient_df.iloc[0]
    ingredient_nom = ingredient_row["nom"]
    produit_epicerie_id = ingredient_row["produit_epicerie_id"]
    ratio = ingredient_row.get("ratio_epicerie")
    ratio_value = 1.0 if ratio is None else float(ratio)

    if produit_epicerie_id:
        codes_df = query_df(
            text(
                """
                SELECT code
                FROM produits_barcodes
                WHERE produit_id = :produit_id AND tenant_id = :tenant_epicerie
                """
            ),
            {"produit_id": int(produit_epicerie_id), "tenant_epicerie": 1},
        )
        codes = [row["code"] for _, row in codes_df.iterrows()] if not codes_df.empty else []
        if codes:
            placeholders = []
            params: Dict[str, Any] = {"tenant_epicerie": 1, "limit": 60}
            for idx, code in enumerate(codes):
                token = f"code_{idx}"
                placeholders.append(f":{token}")
                params[token] = code
            history_df = query_df(
                text(
                    f"""
                    SELECT ph.id, ph.prix_achat, ph.facture_date, ph.created_at
                    FROM produits_price_history ph
                    WHERE ph.tenant_id = :tenant_epicerie
                      AND ph.code IN ({", ".join(placeholders)})
                    ORDER BY ph.facture_date DESC NULLS LAST, ph.created_at DESC
                    LIMIT :limit
                    """
                ),
                params,
            )
            if not history_df.empty:
                return [
                    {
                        "id": int(row["id"]),
                        "ingredient_id": ingredient_id,
                        "ingredient_nom": ingredient_nom,
                        "cout_unitaire": float(row["prix_achat"] or 0) * ratio_value,
                        "changed_at": row["facture_date"] or row["created_at"],
                    }
                    for _, row in history_df.iterrows()
                ]

    df = query_df(
        text(
            """
            SELECT h.id, h.ingredient_id, ri.nom AS ingredient_nom, h.cout_unitaire, h.changed_at
            FROM restaurant_ingredient_price_history h
            JOIN restaurant_ingredients ri ON ri.id = h.ingredient_id
            WHERE h.tenant_id = :tenant AND h.ingredient_id = :ingredient
            ORDER BY h.changed_at DESC
            """
        ),
        {"tenant": tenant_id, "ingredient": ingredient_id},
    )
    return df.to_dict("records") if not df.empty else []


def list_plat_price_history(tenant_id: int, plat_id: int) -> List[dict[str, Any]]:
    """Affiche l'historique des prix pour un plat donné."""
    df = query_df(
        text(
            """
            SELECT h.id, h.plat_id, p.nom AS plat_nom, h.prix_vente_ttc, h.changed_at
            FROM restaurant_plat_price_history h
            JOIN restaurant_plats p ON p.id = h.plat_id
            WHERE h.tenant_id = :tenant AND h.plat_id = :plat
            ORDER BY h.changed_at DESC
            """
        ),
        {"tenant": tenant_id, "plat": plat_id},
    )
    return df.to_dict("records") if not df.empty else []


def list_recent_price_changes(tenant_id: int, limit: int = 12) -> dict[str, list[dict[str, Any]]]:
    """Retourne les dernières modifications de prix pour ingrédients et plats."""
    safe_limit = max(1, min(limit, 200))
    ingredient_sql = text(
        f"""
        SELECT h.id, h.ingredient_id, ri.nom AS ingredient_nom, h.cout_unitaire, h.changed_at
        FROM restaurant_ingredient_price_history h
        JOIN restaurant_ingredients ri ON ri.id = h.ingredient_id
        WHERE h.tenant_id = :tenant
        ORDER BY h.changed_at DESC
        LIMIT {safe_limit}
        """
    )
    plat_sql = text(
        f"""
        SELECT h.id, h.plat_id, p.nom AS plat_nom, h.prix_vente_ttc, h.changed_at
        FROM restaurant_plat_price_history h
        JOIN restaurant_plats p ON p.id = h.plat_id
        WHERE h.tenant_id = :tenant
        ORDER BY h.changed_at DESC
        LIMIT {safe_limit}
        """
    )
    ingredient_df = query_df(ingredient_sql, {"tenant": tenant_id})
    plat_df = query_df(plat_sql, {"tenant": tenant_id})
    return {
        "ingredients": ingredient_df.to_dict("records") if not ingredient_df.empty else [],
        "plats": plat_df.to_dict("records") if not plat_df.empty else [],
    }


def update_ingredient(tenant_id: int, ingredient_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Met à jour les détails d'un ingrédient (nom, unité, coût, stock, catégorie, fournisseur)."""
    # Construire dynamiquement la clause SET à partir des champs fournis
    allowed_fields = ["nom", "unite_base", "cout_unitaire", "stock_actuel", "stock_min", "categorie", "fournisseur"]
    updates = {k: v for k, v in payload.items() if k in allowed_fields and v is not None}

    if not updates:
        raise ValueError("Aucun champ à mettre à jour")

    set_clauses = ", ".join(f"{field} = :{field}" for field in updates.keys())

    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                f"""
                UPDATE restaurant_ingredients
                SET {set_clauses}
                WHERE tenant_id = :tenant AND id = :ingredient_id
                RETURNING id, nom, unite_base, cout_unitaire, stock_actuel, stock_min, categorie, fournisseur, produit_epicerie_id, ratio_epicerie
                """
            ),
            {"tenant": tenant_id, "ingredient_id": ingredient_id, **updates},
        ).fetchone()

        if not row:
            raise RuntimeError(f"Ingrédient {ingredient_id} introuvable")

    # Recalculer les coûts du plat si le prix a changé
    if "cout_unitaire" in updates:
        refresh_plat_costs(tenant_id)

    result = dict(row._mapping)
    result["price_trend"] = None
    result["price_evolution"] = None
    result["price_history"] = []
    # S'assurer que ratio_epicerie est un float
    result["ratio_epicerie"] = float(result.get("ratio_epicerie") or 1.0)
    return result


def delete_ingredient(tenant_id: int, ingredient_id: int) -> dict[str, Any]:
    """Supprime un ingrédient. Échoue si l'ingrédient est utilisé dans un plat."""
    with get_engine().begin() as conn:
        # Vérifier si l'ingrédient est utilisé dans un plat
        usage = conn.execute(
            text(
                """
                SELECT COUNT(*) as cnt FROM restaurant_plat_ingredients
                WHERE tenant_id = :tenant AND ingredient_id = :ingredient_id
                """
            ),
            {"tenant": tenant_id, "ingredient_id": ingredient_id},
        ).fetchone()

        if usage and usage.cnt > 0:
            raise RuntimeError(
                f"Impossible de supprimer : cet ingrédient est utilisé dans {usage.cnt} plat(s). "
                "Retirez-le d'abord des plats concernés."
            )

        # Supprimer l'ingrédient
        result = conn.execute(
            text(
                """
                DELETE FROM restaurant_ingredients
                WHERE tenant_id = :tenant AND id = :ingredient_id
                RETURNING id, nom
                """
            ),
            {"tenant": tenant_id, "ingredient_id": ingredient_id},
        ).fetchone()

        if not result:
            raise RuntimeError(f"Ingrédient {ingredient_id} introuvable")

    return {"deleted": True, "id": result.id, "nom": result.nom}


def delete_plat(tenant_id: int, plat_id: int) -> dict[str, Any]:
    """Supprime un plat et cascade sur restaurant_plat_ingredients."""
    with get_engine().begin() as conn:
        # Supprimer d'abord tous les liens d'ingrédients (cascade)
        conn.execute(
            text(
                """
                DELETE FROM restaurant_plat_ingredients
                WHERE tenant_id = :tenant AND plat_id = :plat_id
                """
            ),
            {"tenant": tenant_id, "plat_id": plat_id},
        )

        # Puis supprimer le plat lui-même
        result = conn.execute(
            text(
                """
                DELETE FROM restaurant_plats
                WHERE tenant_id = :tenant AND id = :plat_id
                RETURNING id, nom
                """
            ),
            {"tenant": tenant_id, "plat_id": plat_id},
        ).fetchone()

        if not result:
            raise RuntimeError(f"Plat {plat_id} introuvable")

    return {"deleted": True, "id": result.id, "nom": result.nom}
