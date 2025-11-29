"""Reporting aggregations for analytics and CSV exports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from pandas import DataFrame

from core.data_repository import query_df


def _as_records(df: DataFrame) -> list[dict[str, Any]]:
    """Normalize a DataFrame into plain Python dictionaries."""

    if df.empty:
        return []
    return df.to_dict(orient="records")


def fetch_report_kpis(*, tenant_id: int) -> dict[str, float | int]:
    """Récupère les KPI principaux affichés sur le dashboard (totaux, alertes, stock négatif)."""

    sql = """
        SELECT
            COUNT(*) FILTER (WHERE actif) AS total_products,
            COALESCE(SUM(COALESCE(stock_actuel, 0)), 0) AS units_available,
            COALESCE(SUM(COALESCE(stock_actuel, 0) * COALESCE(prix_vente, 0)), 0) AS stock_value,
            COALESCE(SUM(
                CASE
                    WHEN COALESCE(stock_actuel, 0) <= COALESCE(seuil_alerte, 0) THEN 1
                    ELSE 0
                END
            ), 0) AS alert_count,
            COALESCE(SUM(
                CASE
                    WHEN COALESCE(stock_actuel, 0) < 0 THEN 1
                    ELSE 0
                END
            ), 0) AS negative_count
        FROM produits
        WHERE actif = TRUE
          AND tenant_id = :tenant_id
    """
    df = query_df(sql, params={"tenant_id": int(tenant_id)})
    if df.empty:
        return {
            "total_products": 0,
            "units_available": 0.0,
            "stock_value": 0.0,
            "alert_count": 0,
            "negative_count": 0,
        }
    row = df.iloc[0]
    return {
        "total_products": int(row.get("total_products") or 0),
        "units_available": float(row.get("units_available") or 0),
        "stock_value": float(row.get("stock_value") or 0),
        "alert_count": int(row.get("alert_count") or 0),
        "negative_count": int(row.get("negative_count") or 0),
    }


def fetch_category_breakdown(*, tenant_id: int, limit: int = 50) -> list[dict[str, Any]]:
    """Agrège le stock par catégorie pour prioriser les familles les plus valorisées."""

    sql = """
        SELECT
            COALESCE(NULLIF(TRIM(categorie::text), ''), 'Non classé') AS category,
            SUM(COALESCE(stock_actuel, 0)) AS units,
            SUM(COALESCE(stock_actuel, 0) * COALESCE(prix_vente, 0)) AS value
        FROM produits
        WHERE actif = TRUE
          AND tenant_id = :tenant_id
        GROUP BY 1
        ORDER BY value DESC
        LIMIT :limit
    """
    df = query_df(sql, params={"limit": int(limit), "tenant_id": int(tenant_id)})
    return _as_records(df)


def fetch_top_value(*, tenant_id: int, limit: int = 10) -> list[dict[str, Any]]:
    """Retourne les articles les plus coûteux en valeur d'achat immobilisée."""

    sql = """
        SELECT
            p.id,
            p.nom,
            COALESCE(p.stock_actuel, 0) AS stock,
            COALESCE(p.prix_achat, 0) AS prix_achat,
            COALESCE(p.stock_actuel, 0) * COALESCE(p.prix_achat, 0) AS valeur_achat
        FROM produits p
        WHERE p.tenant_id = :tenant_id
        ORDER BY valeur_achat DESC
        LIMIT :limit
    """
    df = query_df(sql, params={"limit": int(limit), "tenant_id": int(tenant_id)})
    return _as_records(df)


def fetch_low_stock(*, tenant_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """Liste les produits passés sous leur seuil d'alerte."""

    sql = """
        SELECT
            p.id,
            p.nom,
            p.categorie,
            COALESCE(p.stock_actuel, 0) AS stock_actuel,
            p.seuil_alerte
        FROM produits p
        WHERE p.tenant_id = :tenant_id
          AND COALESCE(p.stock_actuel, 0) <= COALESCE(p.seuil_alerte, 0)
        ORDER BY stock_actuel ASC
        LIMIT :limit
    """
    df = query_df(sql, params={"limit": int(limit), "tenant_id": int(tenant_id)})
    return _as_records(df)


def fetch_negative_stock(*, tenant_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """Identifie les stocks négatifs, symptôme d'écarts ou de ventes non comptabilisées."""

    sql = """
        SELECT
            p.id,
            p.nom,
            p.categorie,
            COALESCE(p.stock_actuel, 0) AS stock_actuel,
            p.seuil_alerte
        FROM produits p
        WHERE p.tenant_id = :tenant_id
          AND COALESCE(p.stock_actuel, 0) < 0
        ORDER BY stock_actuel ASC
        LIMIT :limit
    """
    df = query_df(sql, params={"limit": int(limit), "tenant_id": int(tenant_id)})
    return _as_records(df)


def fetch_rotation(*, tenant_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """Calcule la rotation sur 30 jours à partir des mouvements d'entrées/sorties."""

    sql = """
        WITH mouvements AS (
            SELECT
                m.produit_id,
                SUM(CASE WHEN m.type = 'ENTREE' THEN m.quantite ELSE 0 END) AS entrees_30j,
                SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END) AS sorties_30j
            FROM mouvements_stock m
            WHERE m.date_mvt >= now() - INTERVAL '30 days'
              AND m.tenant_id = :tenant_id
            GROUP BY m.produit_id
        )
        SELECT
            p.id,
            p.nom,
            COALESCE(m.entrees_30j, 0) AS entrees_30j,
            COALESCE(m.sorties_30j, 0) AS sorties_30j
        FROM produits p
        LEFT JOIN mouvements m ON m.produit_id = p.id
        WHERE p.tenant_id = :tenant_id
        ORDER BY sorties_30j DESC NULLS LAST
        LIMIT :limit
    """
    df = query_df(sql, params={"limit": int(limit), "tenant_id": int(tenant_id)})
    return _as_records(df)


def fetch_supplier_inflows(*, tenant_id: int, days: int = 30, limit: int = 10) -> list[dict[str, Any]]:
    """Classe les fournisseurs ayant injecté le plus de valeur sur la période choisie."""

    sql = """
        SELECT
            COALESCE(NULLIF(TRIM(m.source), ''), 'Non renseigné') AS fournisseur,
            SUM(CASE WHEN m.type = 'ENTREE' THEN m.quantite ELSE 0 END) AS quantite,
            SUM(CASE WHEN m.type = 'ENTREE' THEN m.quantite * COALESCE(p.prix_achat, 0) ELSE 0 END) AS valeur
        FROM mouvements_stock m
        JOIN produits p ON p.id = m.produit_id
        WHERE m.date_mvt >= now() - :interval
          AND m.tenant_id = :tenant_id
          AND p.tenant_id = :tenant_id
        GROUP BY fournisseur
        ORDER BY valeur DESC NULLS LAST
        LIMIT :limit
    """
    interval_literal = f"INTERVAL '{max(1, int(days))} days'"
    df = query_df(
        sql.replace(":interval", interval_literal),
        params={"limit": int(limit), "tenant_id": int(tenant_id)},
    )
    return _as_records(df)


def fetch_latest_capital_snapshot(*, tenant_id: int) -> dict[str, object]:
    """Récupère la dernière photographie des actifs (stock + banques + caisse)."""

    sql = """
        SELECT stock_value, bank_balance, cash_balance, total_assets, snapshot_date
        FROM capital_snapshot
        WHERE tenant_id = :tenant_id
        ORDER BY snapshot_date DESC
        LIMIT 1
    """
    df = query_df(text(sql), params={"tenant_id": int(tenant_id)})
    if df.empty:
        return {"stock_value": 0, "bank_balance": 0, "cash_balance": 0, "total_assets": 0, "snapshot_date": None}
    row = df.iloc[0]
    return {
        "stock_value": float(row.stock_value or 0),
        "bank_balance": float(row.bank_balance or 0),
        "cash_balance": float(row.cash_balance or 0),
        "total_assets": float(row.total_assets or 0),
        "snapshot_date": row.snapshot_date,
    }


def build_overview(*, tenant_id: int) -> dict[str, Any]:
    """Assemble toutes les sections du rapport consolidé consommé par la SPA."""

    return {
        "kpis": fetch_report_kpis(tenant_id=tenant_id),
        "category_breakdown": fetch_category_breakdown(tenant_id=tenant_id),
        "top_value": fetch_top_value(tenant_id=tenant_id),
        "low_stock": fetch_low_stock(tenant_id=tenant_id),
        "negative_stock": fetch_negative_stock(tenant_id=tenant_id),
        "rotation": fetch_rotation(tenant_id=tenant_id),
        "supplier_inflows": fetch_supplier_inflows(tenant_id=tenant_id),
        "capital_snapshot": fetch_latest_capital_snapshot(tenant_id=tenant_id),
    }


@dataclass(frozen=True)
class ReportExport:
    """Describe an exportable dataset."""

    filename: str
    sql: str


EXPORT_DEFINITIONS: Dict[str, ReportExport] = {
    "stock": ReportExport(
        filename="rapport_stock.csv",
        sql="""
            SELECT
                p.id,
                p.nom,
                p.categorie,
                p.prix_vente,
                p.prix_achat,
                p.tva,
                p.seuil_alerte,
                p.stock_actuel AS quantite_stock
            FROM produits p
            WHERE p.tenant_id = :tenant_id
            ORDER BY p.nom ASC
            LIMIT :limit
        """,
    ),
    "alerts": ReportExport(
        filename="rapport_alertes.csv",
        sql="""
            SELECT
                p.id,
                p.nom,
                p.categorie,
                COALESCE(p.stock_actuel, 0) AS stock,
                p.seuil_alerte
            FROM produits p
            WHERE p.tenant_id = :tenant_id
              AND COALESCE(p.stock_actuel, 0) <= COALESCE(p.seuil_alerte, 0)
            ORDER BY stock ASC
            LIMIT :limit
        """,
    ),
    "rotation": ReportExport(
        filename="rapport_rotation_30j.csv",
        sql="""
            WITH mouvements AS (
                SELECT
                    m.produit_id,
                    SUM(CASE WHEN m.type = 'ENTREE' THEN m.quantite ELSE 0 END) AS entrees_30j,
                    SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END) AS sorties_30j
                FROM mouvements_stock m
                WHERE m.date_mvt >= now() - INTERVAL '30 days'
                  AND m.tenant_id = :tenant_id
                GROUP BY m.produit_id
            )
            SELECT
                p.id,
                p.nom,
                COALESCE(m.entrees_30j, 0) AS entrees_30j,
                COALESCE(m.sorties_30j, 0) AS sorties_30j
            FROM produits p
            LEFT JOIN mouvements m ON m.produit_id = p.id
            WHERE p.tenant_id = :tenant_id
            ORDER BY sorties_30j DESC NULLS LAST
            LIMIT :limit
        """,
    ),
    "negative_stock": ReportExport(
        filename="rapport_stock_negatif.csv",
        sql="""
            SELECT
                p.id,
                p.nom,
                p.categorie,
                COALESCE(p.stock_actuel, 0) AS stock,
                p.seuil_alerte
            FROM produits p
            WHERE p.tenant_id = :tenant_id
              AND COALESCE(p.stock_actuel, 0) < 0
            ORDER BY stock ASC
            LIMIT :limit
        """,
    ),
    "capital_snapshot": ReportExport(
        filename="rapport_capital.csv",
        sql="""
            SELECT
                tenant_id,
                snapshot_date,
                stock_value,
                bank_balance,
                cash_balance,
                total_assets
            FROM capital_snapshot
            WHERE tenant_id = :tenant_id
            ORDER BY snapshot_date DESC
            LIMIT :limit
        """,
    ),
}


def export_dataset(report_type: str, limit: int, *, tenant_id: int) -> Tuple[str, bytes]:
    """Return (filename, csv_bytes) for the selected dataset."""

    definition = EXPORT_DEFINITIONS.get(report_type)
    if definition is None:
        raise ValueError(f"Rapport inconnu: {report_type}")

    safe_limit = max(10, min(int(limit), 50_000))
    df = query_df(definition.sql, params={"limit": safe_limit, "tenant_id": int(tenant_id)})
    csv_payload = df.to_csv(index=False).encode("utf-8")
    return definition.filename, csv_payload


__all__ = [
    "build_overview",
    "export_dataset",
]
