"""Services d'agrégation pour le tableau de bord."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import text

from core.data_repository import query_df


def fetch_kpis(tenant_id: int) -> dict[str, float | int]:
    # Compte des produits et alertes depuis la table produits
    sql_produits = """
        SELECT
            COUNT(id) AS total_produits,
            COALESCE(SUM(CASE WHEN stock_actuel <= 5 AND stock_actuel > 0 THEN 1 ELSE 0 END), 0) AS alerte_stock_bas,
            COALESCE(SUM(CASE WHEN stock_actuel = 0 THEN 1 ELSE 0 END), 0) AS stock_epuise,
            COUNT(DISTINCT NULLIF(TRIM(categorie), '')) AS categories_count,
            COALESCE(AVG(NULLIF(prix_achat, 0)), 0) AS avg_purchase_price
        FROM produits
        WHERE tenant_id = :tenant_id
    """
    df_produits = query_df(sql_produits, params={"tenant_id": int(tenant_id)})

    # Valeur du stock depuis latest_price_history (plus fiable)
    sql_stock = """
        SELECT
            COALESCE(SUM(prix_achat * COALESCE(quantite, 1)), 0) AS valeur_stock_ht,
            COALESCE(SUM(COALESCE(quantite, 1)), 0) AS quantite_stock_total
        FROM latest_price_history
        WHERE tenant_id = :tenant_id
    """
    df_stock = query_df(sql_stock, params={"tenant_id": int(tenant_id)})

    # Factures récentes (30 derniers jours) - pas de colonne status, on compte les récentes
    sql_pending = """
        SELECT
            COUNT(*) AS pending_invoices,
            COALESCE(SUM(total_ttc), 0) AS pending_amount
        FROM processed_invoices
        WHERE tenant_id = :tenant_id
          AND created_at >= NOW() - INTERVAL '30 days'
    """
    df_pending = query_df(sql_pending, params={"tenant_id": int(tenant_id)})

    # Rotation de stock moyenne (jours de couverture basée sur les sorties des 90 derniers jours)
    sql_rotation = """
        WITH sorties_90j AS (
            SELECT
                produit_id,
                SUM(quantite) AS total_sorti
            FROM mouvements_stock
            WHERE type = 'SORTIE'
              AND tenant_id = :tenant_id
              AND date_mvt >= NOW() - INTERVAL '90 days'
            GROUP BY produit_id
        ),
        stock_actuel AS (
            SELECT id, stock_actuel
            FROM produits
            WHERE tenant_id = :tenant_id
              AND stock_actuel > 0
        )
        SELECT
            COALESCE(AVG(
                CASE WHEN s.total_sorti > 0
                     THEN (p.stock_actuel / (s.total_sorti / 90.0))
                     ELSE NULL
                END
            ), 0) AS avg_rotation
        FROM stock_actuel p
        LEFT JOIN sorties_90j s ON s.produit_id = p.id
    """
    df_rotation = query_df(sql_rotation, params={"tenant_id": int(tenant_id)})

    if df_produits.empty:
        return {
            'total_produits': 0,
            'valeur_stock_ht': 0.0,
            'quantite_stock_total': 0.0,
            'alerte_stock_bas': 0,
            'stock_epuise': 0,
            'categories_count': 0,
            'avg_purchase_price': 0.0,
            'pending_invoices': 0,
            'pending_amount': 0.0,
            'avg_rotation': 0.0,
        }

    row_produits = df_produits.iloc[0]
    row_stock = df_stock.iloc[0] if not df_stock.empty else {}
    row_pending = df_pending.iloc[0] if not df_pending.empty else {}
    row_rotation = df_rotation.iloc[0] if not df_rotation.empty else {}

    return {
        'total_produits': int(row_produits.get('total_produits', 0) or 0),
        'valeur_stock_ht': float(row_stock.get('valeur_stock_ht', 0) or 0),
        'quantite_stock_total': float(row_stock.get('quantite_stock_total', 0) or 0),
        'alerte_stock_bas': int(row_produits.get('alerte_stock_bas', 0) or 0),
        'stock_epuise': int(row_produits.get('stock_epuise', 0) or 0),
        'categories_count': int(row_produits.get('categories_count', 0) or 0),
        'avg_purchase_price': round(float(row_produits.get('avg_purchase_price', 0) or 0), 2),
        'pending_invoices': int(row_pending.get('pending_invoices', 0) or 0),
        'pending_amount': round(float(row_pending.get('pending_amount', 0) or 0), 2),
        'avg_rotation': round(float(row_rotation.get('avg_rotation', 0) or 0), 1),
    }


def fetch_top_stock_value(*, tenant_id: int, limit: int = 5) -> List[dict[str, Any]]:
    """Top produits par valeur de stock (prix_achat * stock_actuel)."""
    sql = """
        SELECT
            p.nom,
            (COALESCE(p.prix_achat, 0) * COALESCE(p.stock_actuel, 0)) AS valeur_stock
        FROM produits p
        WHERE p.tenant_id = :tenant_id
          AND p.stock_actuel > 0
        ORDER BY valeur_stock DESC NULLS LAST
        LIMIT :limit
    """
    df = query_df(sql, params={'limit': limit, 'tenant_id': int(tenant_id)})
    return df.to_dict(orient='records') if not df.empty else []


def fetch_top_sales(*, tenant_id: int, limit: int = 5) -> List[dict[str, Any]]:
    sql = """
        SELECT p.nom, COALESCE(SUM(m.quantite), 0) AS quantite_vendue
        FROM mouvements_stock m
        JOIN produits p ON m.produit_id = p.id
        WHERE m.type = 'SORTIE'
          AND m.tenant_id = :tenant_id
          AND p.tenant_id = :tenant_id
        GROUP BY p.nom
        ORDER BY quantite_vendue DESC
        LIMIT :limit
    """
    df = query_df(sql, params={'limit': limit, 'tenant_id': int(tenant_id)})
    return df.to_dict(orient='records') if not df.empty else []


def fetch_status_distribution(*, tenant_id: int) -> List[dict[str, Any]]:
    sql = """
        SELECT
            CASE
                WHEN stock_actuel <= 0 THEN 'Épuisé'
                WHEN stock_actuel < 5 THEN 'Alerte Basse'
                ELSE 'Stock OK'
            END AS statut_stock,
            COUNT(*) AS nombre
        FROM produits
        WHERE tenant_id = :tenant_id
        GROUP BY 1
        ORDER BY nombre DESC
    """
    df = query_df(sql, params={'tenant_id': int(tenant_id)})
    return df.to_dict(orient='records') if not df.empty else []


def fetch_supplier_breakdown(*, tenant_id: int, limit: int = 5) -> List[dict[str, Any]]:
    sql = """
        SELECT
            COALESCE(NULLIF(TRIM(m.source), ''), 'Non renseigné') AS fournisseur,
            COUNT(*) AS mouvements,
            SUM(CASE WHEN m.type = 'ENTREE' THEN m.quantite ELSE 0 END) AS quantite,
            SUM(CASE WHEN m.type = 'ENTREE' THEN m.quantite * COALESCE(p.prix_achat, 0) ELSE 0 END) AS valeur
        FROM mouvements_stock m
        JOIN produits p ON p.id = m.produit_id
        WHERE m.type = 'ENTREE'
          AND m.tenant_id = :tenant_id
          AND p.tenant_id = :tenant_id
        GROUP BY fournisseur
        ORDER BY valeur DESC
        LIMIT :limit
    """
    df = query_df(sql, params={'limit': limit, 'tenant_id': int(tenant_id)})
    return df.to_dict(orient='records') if not df.empty else []


def fetch_weekly_variation(*, tenant_id: int, weeks: int = 8) -> List[dict[str, Any]]:
    sql = """
        SELECT
            DATE_TRUNC('week', m.date_mvt) AS semaine,
            SUM(CASE WHEN m.type = 'ENTREE' THEN m.quantite ELSE 0 END) AS entrees,
            SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END) AS sorties
        FROM mouvements_stock m
        WHERE m.date_mvt >= now() - INTERVAL ':weeks weeks'
          AND m.tenant_id = :tenant_id
        GROUP BY semaine
        ORDER BY semaine ASC
    """
    df = query_df(text(sql.replace(':weeks', str(max(1, weeks)))), params={'tenant_id': int(tenant_id)})
    if df.empty:
        return []
    df['semaine'] = pd.to_datetime(df['semaine'])
    return df.to_dict(orient='records')


def fetch_margin_alerts(*, tenant_id: int, limit: int = 5) -> List[dict[str, Any]]:
    sql = """
        SELECT
            p.id, p.nom, p.categorie,
            COALESCE(p.prix_vente, 0) AS prix_vente,
            COALESCE(p.prix_achat, 0) AS prix_achat,
            CASE WHEN COALESCE(p.prix_vente, 0) = 0 THEN 0
                 ELSE ((p.prix_vente - p.prix_achat) / NULLIF(p.prix_vente, 0)) * 100
            END AS marge_pct
        FROM produits p
        WHERE p.actif = TRUE
          AND p.tenant_id = :tenant_id
        ORDER BY marge_pct ASC
        LIMIT :limit
    """
    df = query_df(sql, params={'limit': limit, 'tenant_id': int(tenant_id)})
    return df.to_dict(orient='records') if not df.empty else []


def fetch_dashboard_metrics(*, tenant_id: int) -> dict[str, Any]:
    return {
        'kpis': fetch_kpis(tenant_id=tenant_id),
        'top_stock_value': fetch_top_stock_value(tenant_id=tenant_id),
        'top_sales': fetch_top_sales(tenant_id=tenant_id),
        'status_distribution': fetch_status_distribution(tenant_id=tenant_id),
        'supplier_breakdown': fetch_supplier_breakdown(tenant_id=tenant_id),
        'weekly_variation': fetch_weekly_variation(tenant_id=tenant_id),
        'margin_alerts': fetch_margin_alerts(tenant_id=tenant_id),
    }


__all__ = ['fetch_dashboard_metrics']
