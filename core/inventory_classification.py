"""Classification ABC/XYZ des produits."""  # Docstring présentant le module de classification

from __future__ import annotations  # Active les annotations différées

from datetime import datetime, timedelta  # Gestion des dates (non utilisées ici mais importées)
from decimal import Decimal  # Type décimal précis
from typing import Any  # Typage générique

import numpy as np  # Bibliothèque numérique pour calculs vectorisés
import pandas as pd  # Manipulation de données tabulaires
from sqlalchemy import text  # Construction de requêtes SQL textuelles

from core.data_repository import get_engine, query_df  # Accès moteur et requêtes vers la base


CATALOG_SQL = """
    WITH ventes_30j AS (
        SELECT
            m.produit_id,
            SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END) AS qte_sorties_30j
        FROM mouvements_stock m
        WHERE m.tenant_id = :tenant_id
          AND m.date_mvt >= now() - INTERVAL '30 days'
        GROUP BY m.produit_id
    )
    SELECT
        p.id,
        COALESCE(p.prix_achat, 0) AS prix_achat,
        COALESCE(p.average_cost, 0) AS average_cost,
        COALESCE(p.stock_actuel, 0) AS stock_actuel,
        COALESCE(tv.qte_sorties_30j, 0) AS ventes_30j
    FROM produits p
    LEFT JOIN ventes_30j tv ON tv.produit_id = p.id
    WHERE p.actif = TRUE
      AND p.tenant_id = :tenant_id
"""  # Requête SQL pour récupérer le catalogue et les ventes sur 30 jours

DEMAND_SQL = """
    SELECT
        m.produit_id,
        DATE(m.date_mvt) AS jour,
        SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END) AS qty_out
    FROM mouvements_stock m
    WHERE m.tenant_id = :tenant_id
      AND m.date_mvt >= now() - INTERVAL '90 days'
    GROUP BY m.produit_id, DATE(m.date_mvt)
"""  # Requête SQL des sorties quotidiennes sur 90 jours


def _safe_decimal(value: Any) -> Decimal:
    try:  # Tente de convertir la valeur en Decimal
        return Decimal(str(value))  # Conversion en utilisant la représentation chaîne
    except Exception:  # Si conversion impossible
        return Decimal("0")  # Renvoie zéro en Decimal


def _compute_abc(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()  # Copie pour éviter de muter l'entrée
    df["valeur"] = df["valeur"].clip(lower=0.0)  # Coupe les valeurs négatives à zéro
    df = df.sort_values("valeur", ascending=False)  # Trie par valeur décroissante
    total_value = df["valeur"].sum()  # Somme totale pour calculer les parts
    if total_value <= 0:  # Cas sans valeur
        df["abc"] = "C"  # Classe par défaut C
        df["share"] = 0.0  # Part de valeur nulle
        return df  # Retourne directement

    df["share"] = df["valeur"] / total_value  # Part relative de chaque article
    df["cumul"] = df["share"].cumsum()  # Cumul des parts pour seuils ABC

    conditions = [
        df["cumul"] <= 0.8,
        df["cumul"] <= 0.95,
    ]  # Seuils pour A (80%) et B (95%)
    choices = ["A", "B"]  # Classes associées aux conditions
    df["abc"] = np.select(conditions, choices, default="C")  # Assigne la classe ABC
    return df  # Renvoie le DataFrame annoté


def _compute_xyz(demand_df: pd.DataFrame, *, catalog: pd.DataFrame) -> dict[int, dict[str, float]]:
    if demand_df.empty:  # Sans historique de demande
        return {}  # Retourne un dictionnaire vide
    stats = (
        demand_df.groupby("produit_id")["qty_out"]
        .agg(["mean", "std"])
        .rename(columns={"mean": "demand_mean", "std": "demand_std"})
        .reset_index()
    )  # Calcule moyenne et écart-type de demande par produit
    denom = stats["demand_mean"].replace(0, np.nan)  # Remplace 0 par NaN pour éviter division
    cv_series = stats["demand_std"] / denom  # Coefficient de variation
    stats["cv"] = np.where(stats["demand_mean"] > 0, cv_series, np.inf)  # CV infini si demande nulle
    result: dict[int, dict[str, float]] = {}  # Dictionnaire résultat par produit
    for row in stats.to_dict("records"):  # Parcourt chaque ligne agrégée
        cv_value = float(row["cv"]) if np.isfinite(row["cv"]) else float("inf")  # CV numérique ou infini
        if not np.isfinite(cv_value):  # Cas CV non défini
            xyz = "Z"  # Classe Z par défaut
        elif cv_value <= 0.10:  # Faible variabilité
            xyz = "X"  # Classe X
        elif cv_value <= 0.25:  # Variabilité modérée
            xyz = "Y"  # Classe Y
        else:  # Variabilité élevée
            xyz = "Z"  # Classe Z
        result[int(row["produit_id"])] = {
            "xyz": xyz,
            "cv": cv_value if np.isfinite(cv_value) else None,
            "demand_mean": float(row["demand_mean"] or 0),
            "demand_std": float(row["demand_std"] or 0),
        }  # Stocke les métriques par produit
    return result  # Renvoie le mapping produit -> stats XYZ


def classify_inventory(*, tenant_id: int = 1) -> dict[str, int]:
    catalog_df = query_df(CATALOG_SQL, params={"tenant_id": int(tenant_id)})  # Récupère le catalogue et ventes récentes
    if catalog_df.empty:  # Aucun produit actif
        return {"classified": 0}  # Indique zéro classification

    catalog_df["prix_base"] = catalog_df.apply(
        lambda row: row.get("prix_achat") if row.get("prix_achat") and row.get("prix_achat") > 0 else row.get("average_cost"),
        axis=1,
    )  # Sélectionne prix d'achat s'il existe sinon average_cost
    catalog_df["prix_base"] = catalog_df["prix_base"].fillna(0.0)  # Remplace les prix manquants par 0
    catalog_df["ventes_30j"] = catalog_df["ventes_30j"].fillna(0.0)  # Remplace les ventes manquantes par 0
    catalog_df["valeur"] = catalog_df["prix_base"] * catalog_df["ventes_30j"]  # Calcule la valeur consommée

    abc_df = _compute_abc(catalog_df[["id", "valeur"]].rename(columns={"id": "produit_id"}))  # Classe ABC sur la valeur

    demand_df = query_df(DEMAND_SQL, params={"tenant_id": int(tenant_id)})  # Charge l'historique de demande
    xyz_mapping = _compute_xyz(demand_df, catalog=catalog_df)  # Calcule les classes XYZ

    rows: list[dict[str, Any]] = []  # Liste des lignes à insérer
    for entry in abc_df.to_dict("records"):  # Parcourt chaque produit classé ABC
        product_id = int(entry["produit_id"])  # Identifiant du produit
        xyz_info = xyz_mapping.get(product_id, {"xyz": "Z", "cv": None, "demand_mean": 0.0, "demand_std": 0.0})  # Infos XYZ
        rows.append(
            {
                "tenant_id": int(tenant_id),
                "product_id": product_id,
                "abc_class": entry["abc"],
                "xyz_class": xyz_info["xyz"],
                "value_share": float(entry.get("share") or 0),
                "annual_consumption_value": float(entry.get("valeur") or 0) * 12.0,
                "cv": xyz_info.get("cv"),
                "demand_mean": xyz_info.get("demand_mean"),
                "demand_std": xyz_info.get("demand_std"),
            }
        )  # Construit le dictionnaire à insérer

    engine = get_engine()  # Récupère le moteur SQLAlchemy
    with engine.begin() as conn:  # Ouvre une transaction
        conn.execute(
            text(
                "DELETE FROM inventory_classifications WHERE tenant_id = :tenant_id"
            ),
            {"tenant_id": int(tenant_id)},
        )  # Nettoie les classifications existantes pour ce tenant
        conn.execute(
            text(
                """
                INSERT INTO inventory_classifications (
                    tenant_id,
                    product_id,
                    abc_class,
                    xyz_class,
                    value_share,
                    annual_consumption_value,
                    cv,
                    demand_mean,
                    demand_std,
                    updated_at
                )
                VALUES (
                    :tenant_id,
                    :product_id,
                    :abc_class,
                    :xyz_class,
                    :value_share,
                    :annual_consumption_value,
                    :cv,
                    :demand_mean,
                    :demand_std,
                    NOW()
                )
                """
            ),
            rows,
        )  # Insère les nouvelles classifications
    return {"classified": len(rows)}  # Retourne le nombre de lignes classées


__all__ = ["classify_inventory"]  # Exporte la fonction publique
