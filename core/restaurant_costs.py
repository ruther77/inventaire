"""Recalcule les coûts matière des plats restaurant."""  # Docstring du module de coûts restaurant

from __future__ import annotations  # Active les annotations différées

import logging
from dataclasses import dataclass  # Import non utilisé ici mais disponible pour structures
from typing import Any  # Typage générique

from sqlalchemy import text  # Construction de requêtes SQL textuelles

from core.data_repository import get_engine, query_df  # Utilitaires d'accès base
from core.events import PriceChangedEvent, get_event_dispatcher

LOGGER = logging.getLogger(__name__)


COST_SQL = """
    WITH ingredient_costs AS (
        SELECT
            pi.plat_id,
            SUM(
                pi.quantite * COALESCE(
                    p.prix_achat * COALESCE(i.ratio_epicerie, 1.0),
                    i.cout_unitaire,
                    0
                )
            ) AS cout_matiere
        FROM restaurant_plat_ingredients pi
        JOIN restaurant_ingredients i ON i.id = pi.ingredient_id AND i.tenant_id = pi.tenant_id
        LEFT JOIN produits p ON p.id = i.produit_epicerie_id
        WHERE pi.tenant_id = :tenant_id
        GROUP BY pi.plat_id
    )
    SELECT
        p.id AS plat_id,
        p.prix_vente_ttc,
        COALESCE(ic.cout_matiere, 0) AS cout_matiere,
        p.categorie,
        COALESCE(pc.target_food_cost_percent, 30.0) AS category_threshold
    FROM restaurant_plats p
    LEFT JOIN ingredient_costs ic ON ic.plat_id = p.id
    LEFT JOIN plat_categories pc ON pc.nom = p.categorie AND pc.tenant_id = p.tenant_id
    WHERE p.tenant_id = :tenant_id
"""  # Requête SQL pour calculer le coût matière par plat avec seuil par catégorie


def _safe_float(value: Any) -> float:
    try:  # Tente conversion en float
        return float(value)  # Retourne la valeur numérique
    except (TypeError, ValueError):  # Si la conversion échoue
        return 0.0  # Renvoie zéro par défaut


def refresh_plat_costs(*, tenant_id: int, margin_threshold: float = 35.0) -> dict[str, Any]:
    """Recalcule les coûts matière et marges des plats avec seuils par catégorie.

    Args:
        tenant_id: ID du tenant
        margin_threshold: Seuil global par défaut (obsolète, remplacé par les seuils par catégorie)

    Returns:
        dict avec nombre de plats mis à jour et alertes créées
    """
    plats_df = query_df(text(COST_SQL), params={"tenant_id": int(tenant_id)})  # Charge les coûts matière calculés
    if plats_df.empty:  # Aucun plat
        with get_engine().begin() as conn:  # Ouvre une transaction
            conn.execute(
                text("DELETE FROM restaurant_plat_costs WHERE tenant_id = :tenant_id"),
                {"tenant_id": int(tenant_id)},
            )  # Purge les coûts existants
            conn.execute(
                text("DELETE FROM restaurant_alerts WHERE tenant_id = :tenant_id AND alert_type = 'plat_margin'"),
                {"tenant_id": int(tenant_id)},
            )  # Purge les alertes liées
        return {"updated": 0, "alerts": 0}  # Retourne un bilan vide

    records = []  # Liste des enregistrements de coûts à écrire
    alerts = []  # Liste des alertes à écrire
    for row in plats_df.to_dict("records"):  # Parcourt chaque plat
        price = _safe_float(row.get("prix_vente_ttc"))  # Prix de vente TTC
        cost = _safe_float(row.get("cout_matiere"))  # Coût matière calculé
        category_threshold = _safe_float(row.get("category_threshold", 30.0))  # Seuil par catégorie

        # Calcul du food cost (ratio coût/prix en %)
        food_cost_pct = (cost / price * 100) if price > 0 else 0.0

        # Calcul de la marge
        margin = max(0.0, price - cost)  # Marge brute absolue
        margin_pct = (margin / price * 100) if price else 0.0  # Marge en pourcentage

        records.append(
            {
                "tenant_id": int(tenant_id),
                "plat_id": int(row["plat_id"]),
                "cout_matiere": cost,
                "prix_vente_ttc": price,
                "marge_brute": margin,
                "marge_pct": margin_pct,
            }
        )  # Ajoute la ligne de coût pour upsert

        # Alerte si le food cost dépasse le seuil de la catégorie
        if price > 0 and food_cost_pct > category_threshold:  # Détecte un food cost au-dessus du seuil
            severity = "critical" if food_cost_pct > category_threshold * 1.2 else "warning"
            alerts.append(
                {
                    "tenant_id": int(tenant_id),
                    "plat_id": int(row["plat_id"]),
                    "alert_type": "plat_margin",
                    "severity": severity,
                    "message": f"Food cost {food_cost_pct:.1f}% dépasse le seuil {category_threshold:.1f}% ({row.get('categorie', 'N/A')})",
                    "current_value": food_cost_pct,
                    "threshold": category_threshold,
                }
            )  # Empile l'alerte correspondante

    engine = get_engine()  # Récupère l'engine SQLAlchemy
    with engine.begin() as conn:  # Ouvre une transaction
        conn.execute(
            text(
                """
                INSERT INTO restaurant_plat_costs (
                    tenant_id,
                    plat_id,
                    cout_matiere,
                    prix_vente_ttc,
                    marge_brute,
                    marge_pct,
                    updated_at
                )
                VALUES (
                    :tenant_id,
                    :plat_id,
                    :cout_matiere,
                    :prix_vente_ttc,
                    :marge_brute,
                    :marge_pct,
                    NOW()
                )
                ON CONFLICT (tenant_id, plat_id) DO UPDATE
                SET cout_matiere = EXCLUDED.cout_matiere,
                    prix_vente_ttc = EXCLUDED.prix_vente_ttc,
                    marge_brute = EXCLUDED.marge_brute,
                    marge_pct = EXCLUDED.marge_pct,
                    updated_at = NOW()
                """
            ),
            records,
        )  # Upsert des coûts matière et marges
        conn.execute(
            text("DELETE FROM restaurant_alerts WHERE tenant_id = :tenant_id AND alert_type = 'plat_margin'"),
            {"tenant_id": int(tenant_id)},
        )  # Supprime les alertes existantes de ce type
        if alerts:  # S'il y a des alertes à insérer
            conn.execute(
                text(
                    """
                    INSERT INTO restaurant_alerts (
                        tenant_id,
                        plat_id,
                        alert_type,
                        severity,
                        message,
                        current_value,
                        threshold,
                        created_at
                    )
                    VALUES (
                        :tenant_id,
                        :plat_id,
                        :alert_type,
                        :severity,
                        :message,
                        :current_value,
                        :threshold,
                        NOW()
                    )
                    """
                ),
                alerts,
            )  # Insère les nouvelles alertes

    return {"updated": len(records), "alerts": len(alerts)}  # Retourne un résumé des mises à jour


def list_margin_alerts(*, tenant_id: int) -> list[dict[str, Any]]:
    sql = text(
        """
        SELECT a.id,
               a.plat_id,
               p.nom AS plat_nom,
               p.categorie,
               a.severity,
               a.message,
               a.current_value,
               a.threshold,
               a.created_at
        FROM restaurant_alerts a
        LEFT JOIN restaurant_plats p ON p.id = a.plat_id AND p.tenant_id = a.tenant_id
        WHERE a.tenant_id = :tenant_id
          AND a.alert_type = 'plat_margin'
        ORDER BY a.created_at DESC
        """
    )  # Requête listant les alertes de marge
    df = query_df(sql, params={"tenant_id": int(tenant_id)})  # Exécute la requête
    return df.to_dict("records") if not df.empty else []  # Retourne la liste ou vide


def list_plat_categories(*, tenant_id: int) -> list[dict[str, Any]]:
    """Liste toutes les catégories de plats avec leurs seuils de food cost.

    Args:
        tenant_id: ID du tenant

    Returns:
        Liste des catégories avec nom et target_food_cost_percent
    """
    sql = text(
        """
        SELECT id,
               tenant_id,
               nom,
               target_food_cost_percent,
               created_at,
               updated_at
        FROM plat_categories
        WHERE tenant_id = :tenant_id
        ORDER BY nom
        """
    )
    df = query_df(sql, params={"tenant_id": int(tenant_id)})
    return df.to_dict("records") if not df.empty else []


def get_category_threshold(*, tenant_id: int, category_name: str) -> float:
    """Récupère le seuil de food cost pour une catégorie donnée.

    Args:
        tenant_id: ID du tenant
        category_name: Nom de la catégorie

    Returns:
        Seuil de food cost en pourcentage (par défaut 30.0)
    """
    sql = text(
        """
        SELECT target_food_cost_percent
        FROM plat_categories
        WHERE tenant_id = :tenant_id AND nom = :category_name
        """
    )
    df = query_df(sql, params={"tenant_id": int(tenant_id), "category_name": category_name})
    if not df.empty:
        return float(df.iloc[0]["target_food_cost_percent"])
    return 30.0  # Valeur par défaut


def update_category_threshold(*, tenant_id: int, category_name: str, threshold: float) -> dict[str, Any]:
    """Met à jour le seuil de food cost pour une catégorie.

    Args:
        tenant_id: ID du tenant
        category_name: Nom de la catégorie
        threshold: Nouveau seuil en pourcentage

    Returns:
        dict de confirmation
    """
    with get_engine().begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO plat_categories (tenant_id, nom, target_food_cost_percent)
                VALUES (:tenant_id, :category_name, :threshold)
                ON CONFLICT (tenant_id, nom) DO UPDATE
                SET target_food_cost_percent = EXCLUDED.target_food_cost_percent,
                    updated_at = NOW()
                RETURNING id, nom, target_food_cost_percent
                """
            ),
            {"tenant_id": int(tenant_id), "category_name": category_name, "threshold": float(threshold)},
        )
        row = result.fetchone()
        return {"id": row[0], "nom": row[1], "target_food_cost_percent": float(row[2])}


__all__ = [
    "refresh_plat_costs",
    "list_margin_alerts",
    "list_plat_categories",
    "get_category_threshold",
    "update_category_threshold",
]  # Exporte les fonctions publiques
