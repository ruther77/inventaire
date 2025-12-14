#!/usr/bin/env python3
"""Script de seed pour initialiser les pages et navigation CMS par défaut.

Ce script crée:
- 6 pages de section (Cockpit, Opérations, Finance, Restaurant, Intelligence, Config)
- Navigation par défaut avec icônes et ordre
- Contenu JSONB minimal pour chaque page

Idempotent: utilise INSERT ... ON CONFLICT DO UPDATE pour éviter les doublons.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Ajouter le projet au path pour les imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.data_repository import exec_sql, query_df

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


# Configuration des pages par défaut
DEFAULT_PAGES = [
    {
        "slug": "cockpit",
        "title": "Cockpit - Vue Consolidée",
        "description": "Vue d'ensemble consolidée avec KPIs et alertes en temps réel",
        "content": {
            "sections": [
                {
                    "type": "kpi_grid",
                    "title": "Métriques Clés",
                    "widgets": [
                        {"metric": "revenue", "label": "CA du jour", "icon": "TrendingUp"},
                        {"metric": "stock_value", "label": "Valorisation stock", "icon": "Package"},
                        {"metric": "alerts", "label": "Alertes actives", "icon": "AlertTriangle"},
                    ],
                },
                {
                    "type": "chart",
                    "title": "Tendances",
                    "chartType": "line",
                    "dataSource": "daily_revenue",
                },
            ]
        },
        "status": "published",
    },
    {
        "slug": "operations",
        "title": "Opérations - Gestion Quotidienne",
        "description": "Catalogue, stock, factures et approvisionnement",
        "content": {
            "sections": [
                {
                    "type": "quick_actions",
                    "actions": [
                        {"label": "Ajouter produit", "path": "/catalog/new", "icon": "Plus"},
                        {"label": "Scanner facture", "path": "/invoices/import", "icon": "Upload"},
                        {"label": "Mouvement stock", "path": "/stock/movement", "icon": "ArrowRightLeft"},
                    ],
                },
                {
                    "type": "data_table",
                    "title": "Produits récents",
                    "dataSource": "recent_products",
                },
            ]
        },
        "status": "published",
    },
    {
        "slug": "finance",
        "title": "Finance - Trésorerie & Comptabilité",
        "description": "Gestion financière, relevés bancaires et rapprochement",
        "content": {
            "sections": [
                {
                    "type": "kpi_grid",
                    "title": "Indicateurs Financiers",
                    "widgets": [
                        {"metric": "cash_balance", "label": "Solde trésorerie", "icon": "Wallet"},
                        {"metric": "pending_reconciliation", "label": "À rapprocher", "icon": "GitCompare"},
                        {"metric": "monthly_revenue", "label": "CA mensuel", "icon": "BarChart3"},
                    ],
                },
                {
                    "type": "recent_transactions",
                    "title": "Dernières transactions",
                    "limit": 10,
                },
            ]
        },
        "status": "published",
    },
    {
        "slug": "restaurant",
        "title": "Restaurant - Plats & Ingrédients",
        "description": "Gestion des plats, ingrédients et marges restauration",
        "content": {
            "sections": [
                {
                    "type": "quick_actions",
                    "actions": [
                        {"label": "Nouveau plat", "path": "/restaurant/dishes/new", "icon": "Utensils"},
                        {"label": "Gérer ingrédients", "path": "/restaurant/ingredients", "icon": "Carrot"},
                        {"label": "Calculer coûts", "path": "/restaurant/costs", "icon": "Calculator"},
                    ],
                },
                {
                    "type": "margin_analysis",
                    "title": "Analyse des marges",
                    "dataSource": "dish_margins",
                },
            ]
        },
        "status": "published",
    },
    {
        "slug": "intelligence",
        "title": "Intelligence - Prévisions & Optimisation",
        "description": "IA, prévisions, détection d'anomalies et scoring fournisseurs",
        "content": {
            "sections": [
                {
                    "type": "ai_insights",
                    "title": "Insights IA",
                    "features": [
                        {"name": "forecast", "label": "Prévisions demande"},
                        {"name": "anomalies", "label": "Anomalies détectées"},
                        {"name": "supplier_scoring", "label": "Scoring fournisseurs"},
                    ],
                },
                {
                    "type": "chart",
                    "title": "Prévisions vs Réalisé",
                    "chartType": "combo",
                    "dataSource": "forecast_accuracy",
                },
            ]
        },
        "status": "published",
    },
    {
        "slug": "config",
        "title": "Configuration - Admin & Paramètres",
        "description": "Administration système, utilisateurs et paramètres",
        "content": {
            "sections": [
                {
                    "type": "settings_grid",
                    "categories": [
                        {"name": "users", "label": "Utilisateurs", "icon": "Users"},
                        {"name": "tenants", "label": "Tenants", "icon": "Building2"},
                        {"name": "system", "label": "Système", "icon": "Settings"},
                        {"name": "integrations", "label": "Intégrations", "icon": "Plug"},
                    ],
                },
            ]
        },
        "status": "published",
    },
]


# Configuration de la navigation par défaut
DEFAULT_NAV_ITEMS = [
    {"label": "Cockpit", "path": "/newcms/cockpit", "section": "main", "order_index": 10, "icon": "Gauge", "badge": None},
    {"label": "Opérations", "path": "/newcms/operations", "section": "main", "order_index": 20, "icon": "Package", "badge": None},
    {"label": "Catalogue", "path": "/newcms/operations/catalog", "section": "operations", "order_index": 21, "icon": "BookOpen", "badge": None},
    {"label": "Stock", "path": "/newcms/operations/stock", "section": "operations", "order_index": 22, "icon": "Archive", "badge": None},
    {"label": "Factures", "path": "/newcms/operations/invoices", "section": "operations", "order_index": 23, "icon": "FileText", "badge": None},
    {"label": "Finance", "path": "/newcms/finance", "section": "main", "order_index": 30, "icon": "Wallet", "badge": None},
    {"label": "Trésorerie", "path": "/newcms/finance/treasury", "section": "finance", "order_index": 31, "icon": "Coins", "badge": None},
    {"label": "Rapprochement", "path": "/newcms/finance/reconciliation", "section": "finance", "order_index": 32, "icon": "GitCompare", "badge": None},
    {"label": "Restaurant", "path": "/newcms/restaurant", "section": "main", "order_index": 40, "icon": "Utensils", "badge": None},
    {"label": "Plats", "path": "/newcms/restaurant/dishes", "section": "restaurant", "order_index": 41, "icon": "ChefHat", "badge": None},
    {"label": "Ingrédients", "path": "/newcms/restaurant/ingredients", "section": "restaurant", "order_index": 42, "icon": "Carrot", "badge": None},
    {"label": "Intelligence", "path": "/newcms/intelligence", "section": "main", "order_index": 50, "icon": "Brain", "badge": "AI"},
    {"label": "Prévisions", "path": "/newcms/intelligence/forecasting", "section": "intelligence", "order_index": 51, "icon": "TrendingUp", "badge": None},
    {"label": "Anomalies", "path": "/newcms/intelligence/anomalies", "section": "intelligence", "order_index": 52, "icon": "AlertTriangle", "badge": None},
    {"label": "Config", "path": "/newcms/config", "section": "main", "order_index": 60, "icon": "Settings", "badge": None},
]


def get_all_tenant_ids() -> list[int]:
    """Récupère tous les tenant_ids de la base."""
    df = query_df("SELECT id FROM tenants ORDER BY id")
    if df.empty:
        logger.warning("Aucun tenant trouvé, utilisation tenant_id=1 par défaut")
        return [1]
    return df["id"].tolist()


def seed_pages(tenant_id: int) -> None:
    """Seed les pages CMS pour un tenant donné."""
    logger.info(f"Seeding pages CMS pour tenant_id={tenant_id}")
    for page_data in DEFAULT_PAGES:
        exec_sql(
            """
            INSERT INTO cms_pages (tenant_id, slug, title, description, content, status, created_at, updated_at)
            VALUES (:tenant_id, :slug, :title, :description, :content, :status, NOW(), NOW())
            ON CONFLICT (tenant_id, slug)
            DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                content = EXCLUDED.content,
                status = EXCLUDED.status,
                updated_at = NOW()
            """,
            {
                "tenant_id": tenant_id,
                "slug": page_data["slug"],
                "title": page_data["title"],
                "description": page_data["description"],
                "content": json.dumps(page_data["content"]),
                "status": page_data["status"],
            },
        )
        logger.info(f"  ✓ Page '{page_data['slug']}' créée/mise à jour")


def seed_navigation(tenant_id: int) -> None:
    """Seed les éléments de navigation pour un tenant donné."""
    logger.info(f"Seeding navigation CMS pour tenant_id={tenant_id}")

    # Supprime toutes les entrées existantes pour ce tenant (pour éviter les doublons)
    exec_sql("DELETE FROM cms_nav_items WHERE tenant_id = :tenant_id", {"tenant_id": tenant_id})

    for nav_item in DEFAULT_NAV_ITEMS:
        exec_sql(
            """
            INSERT INTO cms_nav_items (tenant_id, label, path, section, order_index, icon, badge, created_at, updated_at)
            VALUES (:tenant_id, :label, :path, :section, :order_index, :icon, :badge, NOW(), NOW())
            """,
            {
                "tenant_id": tenant_id,
                "label": nav_item["label"],
                "path": nav_item["path"],
                "section": nav_item["section"],
                "order_index": nav_item["order_index"],
                "icon": nav_item["icon"],
                "badge": nav_item.get("badge"),
            },
        )
        logger.info(f"  ✓ Nav item '{nav_item['label']}' créé")


def main() -> None:
    """Point d'entrée principal du script de seed."""
    logger.info("=== Début du seed CMS ===")

    try:
        # Récupère tous les tenants
        tenant_ids = get_all_tenant_ids()
        logger.info(f"Tenants trouvés: {tenant_ids}")

        for tenant_id in tenant_ids:
            seed_pages(tenant_id)
            seed_navigation(tenant_id)

        logger.info("=== Seed CMS terminé avec succès ===")

    except Exception as e:
        logger.error(f"Erreur lors du seed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
