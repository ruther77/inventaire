#!/usr/bin/env python3
"""Script de vérification de l'infrastructure CMS.

Vérifie que:
1. Les tables existent
2. Les données de seed sont présentes
3. Le router est enregistré
4. Les tests passent (optionnel)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ajouter le projet au path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def check_tables() -> bool:
    """Vérifie que les tables CMS existent."""
    from core.data_repository import query_df

    logger.info("=== Vérification des tables ===")

    try:
        # Vérifier cms_pages
        df = query_df("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('cms_pages', 'cms_nav_items')
            ORDER BY table_name
        """)

        if df.empty:
            logger.error("❌ Tables CMS non trouvées")
            logger.info("💡 Exécutez: alembic upgrade head")
            return False

        tables = df['table_name'].tolist()
        logger.info(f"✅ Tables trouvées: {tables}")

        if 'cms_pages' not in tables:
            logger.error("❌ Table cms_pages manquante")
            return False
        if 'cms_nav_items' not in tables:
            logger.error("❌ Table cms_nav_items manquante")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification des tables: {e}")
        return False


def check_seed_data() -> bool:
    """Vérifie que les données de seed sont présentes."""
    from core.data_repository import query_df

    logger.info("\n=== Vérification des données de seed ===")

    try:
        # Vérifier pages
        df_pages = query_df("SELECT COUNT(*) as count FROM cms_pages")
        page_count = int(df_pages.iloc[0]['count']) if not df_pages.empty else 0

        if page_count == 0:
            logger.warning("⚠️  Aucune page CMS trouvée")
            logger.info("💡 Exécutez: python scripts/seed_cms_navigation.py")
            return False

        logger.info(f"✅ Pages CMS: {page_count}")

        # Vérifier navigation
        df_nav = query_df("SELECT COUNT(*) as count FROM cms_nav_items")
        nav_count = int(df_nav.iloc[0]['count']) if not df_nav.empty else 0

        if nav_count == 0:
            logger.warning("⚠️  Aucun item de navigation trouvé")
            logger.info("💡 Exécutez: python scripts/seed_cms_navigation.py")
            return False

        logger.info(f"✅ Items de navigation: {nav_count}")

        # Afficher les pages par tenant
        df_by_tenant = query_df("""
            SELECT tenant_id, COUNT(*) as count
            FROM cms_pages
            GROUP BY tenant_id
            ORDER BY tenant_id
        """)

        if not df_by_tenant.empty:
            logger.info("Pages par tenant:")
            for _, row in df_by_tenant.iterrows():
                logger.info(f"  - Tenant {row['tenant_id']}: {row['count']} pages")

        return True

    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification des données: {e}")
        return False


def check_router_registration() -> bool:
    """Vérifie que le router newcms est enregistré."""
    logger.info("\n=== Vérification du router ===")

    try:
        main_file = project_root / "backend" / "main.py"

        if not main_file.exists():
            logger.error("❌ Fichier backend/main.py non trouvé")
            return False

        content = main_file.read_text()

        # Vérifier l'import
        if "from backend.api import newcms as newcms_router" not in content:
            logger.error("❌ Import newcms_router manquant dans main.py")
            return False

        logger.info("✅ Import newcms_router trouvé")

        # Vérifier l'enregistrement du router
        if "app.include_router(newcms_router.router" not in content:
            logger.error("❌ Router newcms non enregistré dans main.py")
            return False

        logger.info("✅ Router newcms enregistré")

        return True

    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification du router: {e}")
        return False


def check_files_exist() -> bool:
    """Vérifie que tous les fichiers nécessaires existent."""
    logger.info("\n=== Vérification des fichiers ===")

    files_to_check = [
        ("Migration", "migrations/versions/20251211_cms_tables.py"),
        ("Script seed", "scripts/seed_cms_navigation.py"),
        ("Tests", "tests/test_newcms_api.py"),
        ("API Router", "backend/api/newcms.py"),
        ("Guide", "docs/CMS_INFRASTRUCTURE_GUIDE.md"),
        ("Quickstart", "CMS_QUICKSTART.md"),
    ]

    all_exist = True

    for name, rel_path in files_to_check:
        file_path = project_root / rel_path
        if file_path.exists():
            logger.info(f"✅ {name}: {rel_path}")
        else:
            logger.error(f"❌ {name} manquant: {rel_path}")
            all_exist = False

    return all_exist


def show_summary(results: dict[str, bool]) -> None:
    """Affiche le résumé des vérifications."""
    logger.info("\n" + "=" * 60)
    logger.info("RÉSUMÉ DES VÉRIFICATIONS")
    logger.info("=" * 60)

    for check_name, passed in results.items():
        status = "✅ OK" if passed else "❌ ÉCHEC"
        logger.info(f"{status:10} - {check_name}")

    logger.info("=" * 60)

    all_passed = all(results.values())

    if all_passed:
        logger.info("🎉 Toutes les vérifications sont passées!")
        logger.info("\nProchaines étapes:")
        logger.info("1. Lancer les tests: pytest tests/test_newcms_api.py -v")
        logger.info("2. Démarrer l'API: uvicorn backend.main:app --reload")
        logger.info("3. Tester: curl http://localhost:8000/newcms/pages")
    else:
        logger.error("\n⚠️  Certaines vérifications ont échoué")
        logger.info("\nConsultez les messages ci-dessus pour les actions à effectuer")
        return False

    return True


def main() -> None:
    """Point d'entrée principal."""
    logger.info("🔍 Vérification de l'infrastructure CMS\n")

    results = {
        "Fichiers": check_files_exist(),
        "Tables BDD": check_tables(),
        "Données seed": check_seed_data(),
        "Router": check_router_registration(),
    }

    success = show_summary(results)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
