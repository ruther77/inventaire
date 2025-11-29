"""Recalcule les coûts matière des plats restaurant."""  # Docstring du module de coûts restaurant

from __future__ import annotations  # Active les annotations différées

from dataclasses import dataclass  # Import non utilisé ici mais disponible pour structures
from typing import Any  # Typage générique

from sqlalchemy import text  # Construction de requêtes SQL textuelles

from core.data_repository import get_engine, query_df  # Utilitaires d'accès base


COST_SQL = """
    WITH ingredient_costs AS (
        SELECT
            rpi.plat_id,
            SUM(rpi.quantite * COALESCE(ri.cout_unitaire, 0)) AS cout_matiere
        FROM restaurant_plat_ingredients rpi
        JOIN restaurant_ingredients ri ON ri.id = rpi.ingredient_id
        WHERE rpi.tenant_id = :tenant_id
        GROUP BY rpi.plat_id
    )
    SELECT
        p.id AS plat_id,
        p.prix_vente_ttc,
        COALESCE(ic.cout_matiere, 0) AS cout_matiere
    FROM restaurant_plats p
    LEFT JOIN ingredient_costs ic ON ic.plat_id = p.id
    WHERE p.tenant_id = :tenant_id
"""  # Requête SQL pour calculer le coût matière par plat


def _safe_float(value: Any) -> float:
    try:  # Tente conversion en float
        return float(value)  # Retourne la valeur numérique
    except (TypeError, ValueError):  # Si la conversion échoue
        return 0.0  # Renvoie zéro par défaut


def refresh_plat_costs(*, tenant_id: int, margin_threshold: float = 35.0) -> dict[str, Any]:
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
    threshold = float(max(0.0, margin_threshold))  # Seuil minimal de marge en pourcentage
    for row in plats_df.to_dict("records"):  # Parcourt chaque plat
        price = _safe_float(row.get("prix_vente_ttc"))  # Prix de vente TTC
        cost = _safe_float(row.get("cout_matiere"))  # Coût matière calculé
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
        if price > 0 and margin_pct < threshold:  # Détecte une marge sous le seuil
            alerts.append(
                {
                    "tenant_id": int(tenant_id),
                    "plat_id": int(row["plat_id"]),
                    "alert_type": "plat_margin",
                    "severity": "critical" if margin_pct < threshold * 0.8 else "warning",
                    "message": f"Marge {margin_pct:.1f}% sous le seuil {threshold:.1f}%",
                    "current_value": margin_pct,
                    "threshold": threshold,
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
               a.severity,
               a.message,
               a.current_value,
               a.threshold,
               a.created_at
        FROM restaurant_alerts a
        LEFT JOIN restaurant_plats p ON p.id = a.plat_id
        WHERE a.tenant_id = :tenant_id
          AND a.alert_type = 'plat_margin'
        ORDER BY a.created_at DESC
        """
    )  # Requête listant les alertes de marge
    df = query_df(sql, params={"tenant_id": int(tenant_id)})  # Exécute la requête
    return df.to_dict("records") if not df.empty else []  # Retourne la liste ou vide


__all__ = ["refresh_plat_costs", "list_margin_alerts"]  # Exporte les fonctions publiques
