"""Dashboard aggregation services."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
from sqlalchemy import text

from core.data_repository import query_df


def fetch_kpis(tenant_id: int) -> dict[str, float | int]:
    sql = """
        SELECT
            COUNT(id) AS total_produits,
            COALESCE(SUM(stock_actuel * prix_vente), 0) AS valeur_stock_ht,
            COALESCE(SUM(stock_actuel), 0) AS quantite_stock_total,
            COALESCE(SUM(CASE WHEN stock_actuel <= 5 AND stock_actuel > 0 THEN 1 ELSE 0 END), 0) AS alerte_stock_bas,
            COALESCE(SUM(CASE WHEN stock_actuel = 0 THEN 1 ELSE 0 END), 0) AS stock_epuise
        FROM produits
        WHERE tenant_id = :tenant_id
    """
    df = query_df(sql, params={"tenant_id": int(tenant_id)})
    if df.empty:
        return {
            'total_produits': 0,
            'valeur_stock_ht': 0.0,
            'quantite_stock_total': 0.0,
            'alerte_stock_bas': 0,
            'stock_epuise': 0,
        }
    row = df.iloc[0]
    return {
        'total_produits': int(row.get('total_produits', 0) or 0),
        'valeur_stock_ht': float(row.get('valeur_stock_ht', 0) or 0),
        'quantite_stock_total': float(row.get('quantite_stock_total', 0) or 0),
        'alerte_stock_bas': int(row.get('alerte_stock_bas', 0) or 0),
        'stock_epuise': int(row.get('stock_epuise', 0) or 0),
    }


def fetch_top_stock_value(*, tenant_id: int, limit: int = 5) -> List[dict[str, Any]]:
    sql = """
        SELECT nom, (stock_actuel * prix_vente) AS valeur_stock
        FROM produits
        WHERE tenant_id = :tenant_id
        ORDER BY valeur_stock DESC
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
