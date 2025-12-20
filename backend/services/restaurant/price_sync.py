"""Service de synchronisation des prix des ingrédients restaurant depuis les produits épicerie."""

from __future__ import annotations

import logging
import unicodedata
from typing import Any

from sqlalchemy import text

from core.data_repository import get_engine, query_df
from backend.services.restaurant.ingredients import refresh_plat_costs

LOGGER = logging.getLogger(__name__)

_ALCOHOL_KEYWORDS = {
    "whisky", "whiskey", "vodka", "rhum", "rum", "gin", "cognac", "armagnac",
    "calvados", "tequila", "liqueur", "liqueurs", "martini", "pastis",
    "champagne", "moet", "ruinart", "veuveclicquot", "veuve", "chandon",
    "bordeaux", "bourgogne", "vin", "wine", "rose", "rouge", "blanc",
    "biere", "bieres", "beer", "guinness", "desperados", "campari", "aperol",
    "chivas", "jack", "j.daniel", "jdaniel", "jwalker", "johnnie",
    "baileys", "kir", "porto",
}

_NON_ALCOHOL_BEVERAGE_KEYWORDS = {
    "coca", "cola", "soda", "limonade", "jus", "juice", "eau", "water",
    "ice tea", "iced tea", "ginger beer", "schweppes", "perrier", "orangina",
    "red bull", "malta",
}


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower().replace("’", "'").strip()


def _has_any_keyword(text: str, keywords: set[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def audit_epicerie_links(tenant_id: int, *, dry_run: bool = True) -> dict[str, Any]:
    """Détecte et éventuellement délier les correspondances incohérentes ingrédient ↔ épicerie."""
    df = query_df(
        text(
            """
            SELECT
                ri.id AS ingredient_id,
                ri.nom AS ingredient_nom,
                ri.produit_epicerie_id,
                p.nom AS epicerie_nom,
                p.categorie AS epicerie_categorie
            FROM restaurant_ingredients ri
            JOIN produits p ON p.id = ri.produit_epicerie_id
            WHERE ri.tenant_id = :tenant
              AND ri.produit_epicerie_id IS NOT NULL
            ORDER BY ri.nom
            """
        ),
        {"tenant": tenant_id},
    )

    if df.empty:
        return {"checked": 0, "flagged": 0, "unlinked": 0, "items": []}

    items = []
    for _, row in df.iterrows():
        ing_name = _normalize_text(row["ingredient_nom"])
        epi_name = _normalize_text(row["epicerie_nom"])
        epi_cat = _normalize_text(row.get("epicerie_categorie") or "")

        ingredient_is_alcohol = _has_any_keyword(ing_name, _ALCOHOL_KEYWORDS)
        ingredient_is_non_alcohol_bev = _has_any_keyword(ing_name, _NON_ALCOHOL_BEVERAGE_KEYWORDS)
        epicerie_is_alcohol = _has_any_keyword(epi_name, _ALCOHOL_KEYWORDS) or _has_any_keyword(epi_cat, _ALCOHOL_KEYWORDS)

        if epicerie_is_alcohol and not ingredient_is_alcohol:
            reason = "ingredient_non_alcohol_linked_to_alcohol"
            if ingredient_is_non_alcohol_bev:
                reason = "non_alcohol_beverage_linked_to_alcohol"
            items.append(
                {
                    "ingredient_id": int(row["ingredient_id"]),
                    "ingredient_nom": row["ingredient_nom"],
                    "produit_epicerie_id": int(row["produit_epicerie_id"]),
                    "epicerie_nom": row["epicerie_nom"],
                    "epicerie_categorie": row.get("epicerie_categorie"),
                    "reason": reason,
                }
            )

    unlinked = 0
    if items and not dry_run:
        ingredient_ids = [item["ingredient_id"] for item in items]
        with get_engine().begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE restaurant_ingredients
                    SET produit_epicerie_id = NULL,
                        ratio_epicerie = 1.0
                    WHERE tenant_id = :tenant
                      AND id = ANY(:ingredient_ids)
                    """
                ),
                {"tenant": tenant_id, "ingredient_ids": ingredient_ids},
            )
        unlinked = len(ingredient_ids)

    return {
        "checked": int(len(df)),
        "flagged": len(items),
        "unlinked": unlinked,
        "items": items,
        "dry_run": dry_run,
    }


def sync_ingredient_prices_from_epicerie(tenant_id: int, force_update: bool = False) -> dict[str, Any]:
    """Synchronise les prix des ingrédients à partir des produits épicerie liés.

    Met à jour restaurant_ingredients.cout_unitaire depuis produits.prix_achat
    pour tous les ingrédients possédant un produit_epicerie_id.

    La synchronisation respecte le champ ratio_epicerie pour gérer les conversions d'unité
    (ex. : l'épicerie vend au kg mais l'ingrédient doit être au 100g avec ratio=0.1).

    Args:
        tenant_id: ID du tenant pour lequel synchroniser les prix
        force_update: Si True, met à jour tous les ingrédients liés. Si False, seulement lorsque
                     le prix épicerie diffère du prix actuel de l'ingrédient.

    Returns:
        Dictionnaire de statistiques :
        - updated : nombre d'ingrédients mis à jour
        - skipped : nombre d'ingrédients ignorés (pas de changement)
        - errors : liste des erreurs rencontrées
        - price_changes : liste détaillée des changements de prix
    """
    summary = {
        "updated": 0,
        "skipped": 0,
        "errors": [],
        "price_changes": [],
    }

    with get_engine().begin() as conn:
        # Trouver tous les ingrédients liés à des produits épicerie
        if force_update:
            # Mettre à jour tous les ingrédients liés quelle que soit la différence de prix
            query = text("""
                SELECT
                    ri.id,
                    ri.nom,
                    ri.cout_unitaire AS current_price,
                    p.prix_achat AS epicerie_price,
                    ri.ratio_epicerie,
                    p.nom AS produit_nom
                FROM restaurant_ingredients ri
                INNER JOIN produits p ON p.id = ri.produit_epicerie_id
                WHERE ri.tenant_id = :tenant
                  AND ri.produit_epicerie_id IS NOT NULL
                  AND p.prix_achat IS NOT NULL
                  AND p.prix_achat > 0
            """)
        else:
            # Mettre à jour uniquement si le prix a changé (seuil de 0,01€)
            query = text("""
                SELECT
                    ri.id,
                    ri.nom,
                    ri.cout_unitaire AS current_price,
                    p.prix_achat AS epicerie_price,
                    ri.ratio_epicerie,
                    p.nom AS produit_nom
                FROM restaurant_ingredients ri
                INNER JOIN produits p ON p.id = ri.produit_epicerie_id
                WHERE ri.tenant_id = :tenant
                  AND ri.produit_epicerie_id IS NOT NULL
                  AND p.prix_achat IS NOT NULL
                  AND p.prix_achat > 0
                  AND (
                    ri.cout_unitaire IS NULL
                    OR ri.cout_unitaire = 0
                    OR ABS(ri.cout_unitaire - (p.prix_achat * COALESCE(ri.ratio_epicerie, 1.0))) > 0.01
                  )
            """)

        df = query_df(query, {"tenant": tenant_id})

        if df.empty:
            LOGGER.info(f"No ingredient price updates needed for tenant {tenant_id}")
            return summary

        LOGGER.info(f"Found {len(df)} ingredients to sync for tenant {tenant_id}")

        # Mettre à jour chaque ingrédient
        for _, row in df.iterrows():
            ingredient_id = row["id"]
            ingredient_nom = row["nom"]
            current_price = float(row["current_price"] or 0)
            epicerie_price = float(row["epicerie_price"])
            ratio = float(row.get("ratio_epicerie") or 1.0)
            produit_nom = row.get("produit_nom")

            # Appliquer le ratio pour la conversion d'unité
            # Exemple : prix épicerie 10€/kg, ratio 0.1 → prix ingrédient 1€/100g
            new_price = epicerie_price * ratio

            try:
                # Mettre à jour le prix de l'ingrédient
                # Note : le trigger trg_restaurant_ingredient_price_history va automatiquement
                # enregistrer ce changement dans la table restaurant_ingredient_price_history
                conn.execute(
                    text("""
                        UPDATE restaurant_ingredients
                        SET cout_unitaire = :new_price
                        WHERE id = :ingredient_id AND tenant_id = :tenant
                    """),
                    {
                        "ingredient_id": ingredient_id,
                        "tenant": tenant_id,
                        "new_price": new_price,
                    },
                )

                change_pct = ((new_price - current_price) / current_price * 100) if current_price > 0 else 0

                summary["updated"] += 1
                summary["price_changes"].append({
                    "ingredient_id": ingredient_id,
                    "ingredient_nom": ingredient_nom,
                    "produit_epicerie_nom": produit_nom,
                    "old_price": round(current_price, 4),
                    "new_price": round(new_price, 4),
                    "change_pct": round(change_pct, 2),
                    "ratio": ratio,
                })

                LOGGER.info(
                    f"Updated ingredient {ingredient_id} '{ingredient_nom}': "
                    f"{current_price:.4f}€ → {new_price:.4f}€ ({change_pct:+.1f}%)"
                )

            except Exception as e:
                error_msg = f"Failed to update ingredient {ingredient_id}: {str(e)}"
                LOGGER.error(error_msg)
                summary["errors"].append({
                    "ingredient_id": ingredient_id,
                    "nom": ingredient_nom,
                    "error": str(e),
                })

        # Après la mise à jour des prix, recalculer les coûts des plats pour mettre à jour les marges
        if summary["updated"] > 0:
            try:
                LOGGER.info(f"Refreshing plat costs for tenant {tenant_id}")
                refresh_plat_costs(tenant_id)
            except Exception as e:
                LOGGER.error(f"Failed to refresh plat costs: {e}")
                summary["errors"].append({
                    "context": "refresh_plat_costs",
                    "error": str(e),
                })

    return summary


def get_ingredients_with_price_source(tenant_id: int) -> list[dict[str, Any]]:
    """Retourne les ingrédients avec indication explicite de la source de prix (manuel vs épicerie).

    Utile pour le frontend afin d'afficher quels prix sont synchronisés depuis l'épicerie
    et lesquels sont maintenus manuellement.

    Returns:
        Liste d'ingrédients avec des champs additionnels :
        - price_source : 'epicerie' ou 'manual'
        - is_price_synced : True si lié à l'épicerie et prix aligné (tolérance 0,01€)
        - price_diff : écart entre le prix ingrédient et le prix épicerie (si lié)
    """
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
                ri.categorie,
                ri.fournisseur,
                ri.produit_epicerie_id,
                ri.ratio_epicerie,
                p.nom AS produit_epicerie_nom,
                p.prix_achat AS produit_epicerie_prix,
                CASE
                    WHEN ri.produit_epicerie_id IS NOT NULL THEN 'epicerie'
                    ELSE 'manual'
                END AS price_source,
                CASE
                    WHEN ri.produit_epicerie_id IS NOT NULL AND p.prix_achat IS NOT NULL
                        THEN ABS(ri.cout_unitaire - (p.prix_achat * COALESCE(ri.ratio_epicerie, 1.0))) < 0.01
                    ELSE TRUE
                END AS is_price_synced,
                CASE
                    WHEN ri.produit_epicerie_id IS NOT NULL AND p.prix_achat IS NOT NULL
                        THEN ri.cout_unitaire - (p.prix_achat * COALESCE(ri.ratio_epicerie, 1.0))
                    ELSE NULL
                END AS price_diff
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

    results = df.to_dict("records")

    # Nettoyer les types pour la sérialisation JSON
    for ing in results:
        # S'assurer que produit_epicerie_id est un int ou None
        epicerie_id = ing.get("produit_epicerie_id")
        if epicerie_id is not None and not (isinstance(epicerie_id, float) and epicerie_id != epicerie_id):
            ing["produit_epicerie_id"] = int(epicerie_id)
        else:
            ing["produit_epicerie_id"] = None

        # S'assurer que ratio_epicerie est un float (par défaut 1.0)
        ratio = ing.get("ratio_epicerie")
        if ratio is None or (isinstance(ratio, float) and ratio != ratio):
            ing["ratio_epicerie"] = 1.0
        else:
            ing["ratio_epicerie"] = float(ratio)

        # Arrondir price_diff pour plus de lisibilité
        if ing.get("price_diff") is not None:
            ing["price_diff"] = round(float(ing["price_diff"]), 4)

    return results


def get_price_sync_summary(tenant_id: int) -> dict[str, Any]:
    """Fournit un récapitulatif du statut de synchronisation des prix pour tous les ingrédients.

    Returns:
        Dictionnaire contenant :
        - total_ingredients : nombre total d'ingrédients
        - linked_to_epicerie : nombre liés à des produits épicerie
        - synced : nombre synchronisé depuis l'épicerie
        - out_of_sync : nombre dont le prix diffère de l'épicerie
        - manual : nombre en tarification manuelle (sans lien épicerie)
        - needs_attention : liste des ingrédients à resynchroniser
    """
    ingredients = get_ingredients_with_price_source(tenant_id)

    total = len(ingredients)
    linked = sum(1 for i in ingredients if i["price_source"] == "epicerie")
    synced = sum(1 for i in ingredients if i["price_source"] == "epicerie" and i["is_price_synced"])
    out_of_sync = sum(1 for i in ingredients if i["price_source"] == "epicerie" and not i["is_price_synced"])
    manual = sum(1 for i in ingredients if i["price_source"] == "manual")

    needs_attention = [
        {
            "id": i["id"],
            "nom": i["nom"],
            "current_price": i["cout_unitaire"],
            "epicerie_price": i["produit_epicerie_prix"],
            "price_diff": i["price_diff"],
            "produit_epicerie_nom": i["produit_epicerie_nom"],
        }
        for i in ingredients
        if i["price_source"] == "epicerie" and not i["is_price_synced"]
    ]

    return {
        "total_ingredients": total,
        "linked_to_epicerie": linked,
        "synced": synced,
        "out_of_sync": out_of_sync,
        "manual": manual,
        "sync_rate_pct": round((synced / linked * 100) if linked > 0 else 0, 1),
        "needs_attention": needs_attention,
    }
