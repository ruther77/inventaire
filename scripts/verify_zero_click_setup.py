#!/usr/bin/env python
"""Script de vérification de l'installation du système zero-click jobs."""

from __future__ import annotations

import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Vérifie qu'un fichier existe."""
    path = Path(filepath)
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {filepath}")
    return exists


def check_import(module_path: str, description: str) -> bool:
    """Vérifie qu'un module peut être importé."""
    try:
        parts = module_path.split(".")
        module = __import__(module_path)
        for part in parts[1:]:
            module = getattr(module, part)
        print(f"✅ {description}: {module_path}")
        return True
    except Exception as exc:
        print(f"❌ {description}: {module_path} - {exc}")
        return False


def main():
    """Vérifie l'installation complète."""
    print("=" * 70)
    print("Vérification du système Zero-Click Jobs Async")
    print("=" * 70)
    print()

    checks = []

    # 1. Fichiers de migration
    print("📁 FICHIERS DE MIGRATION")
    print("-" * 70)
    checks.append(check_file_exists(
        "migrations/versions/20251211_zero_click_jobs.py",
        "Migration zero_click_jobs"
    ))
    print()

    # 2. Services
    print("🔧 SERVICES")
    print("-" * 70)
    checks.append(check_file_exists(
        "backend/services/zero_click_jobs.py",
        "Service zero_click_jobs"
    ))
    print()

    # 3. Schémas
    print("📋 SCHÉMAS")
    print("-" * 70)
    checks.append(check_file_exists(
        "backend/schemas/invoices.py",
        "Schémas invoices (modifié)"
    ))
    print()

    # 4. API
    print("🌐 API ENDPOINTS")
    print("-" * 70)
    checks.append(check_file_exists(
        "backend/api/invoices.py",
        "API invoices (modifié)"
    ))
    print()

    # 5. Tests
    print("🧪 TESTS")
    print("-" * 70)
    checks.append(check_file_exists(
        "tests/test_zero_click_jobs.py",
        "Tests unitaires"
    ))
    print()

    # 6. Documentation
    print("📚 DOCUMENTATION")
    print("-" * 70)
    checks.append(check_file_exists(
        "docs/ZERO_CLICK_JOBS_ASYNC.md",
        "Documentation complète"
    ))
    checks.append(check_file_exists(
        "docs/ZERO_CLICK_ARCHITECTURE.md",
        "Architecture détaillée"
    ))
    checks.append(check_file_exists(
        "ZERO_CLICK_ASYNC_SUMMARY.md",
        "Résumé d'implémentation"
    ))
    print()

    # 7. Scripts
    print("🛠️  SCRIPTS UTILITAIRES")
    print("-" * 70)
    checks.append(check_file_exists(
        "scripts/apply_zero_click_migration.sh",
        "Script de migration"
    ))
    checks.append(check_file_exists(
        "scripts/test_zero_click_client.py",
        "Client de test"
    ))
    checks.append(check_file_exists(
        "scripts/verify_zero_click_setup.py",
        "Script de vérification"
    ))
    print()

    # 8. Imports Python
    print("🐍 IMPORTS PYTHON")
    print("-" * 70)
    checks.append(check_import(
        "backend.schemas.invoices",
        "Schémas invoices"
    ))
    checks.append(check_import(
        "backend.services.zero_click_jobs",
        "Service zero_click_jobs"
    ))
    print()

    # Résumé
    print("=" * 70)
    total = len(checks)
    passed = sum(checks)
    failed = total - passed

    print(f"RÉSULTAT: {passed}/{total} vérifications passées")

    if failed > 0:
        print(f"⚠️  {failed} vérification(s) échouée(s)")
        print()
        print("Actions recommandées:")
        print("1. Vérifier que tous les fichiers sont bien créés")
        print("2. Vérifier les imports Python")
        print("3. Relancer le script après correction")
        return 1
    else:
        print("✅ Tous les composants sont en place!")
        print()
        print("Prochaines étapes:")
        print("1. Appliquer la migration:")
        print("   bash scripts/apply_zero_click_migration.sh")
        print()
        print("2. Lancer les tests:")
        print("   pytest tests/test_zero_click_jobs.py -v")
        print()
        print("3. Tester avec le client:")
        print("   python scripts/test_zero_click_client.py facture.pdf")
        return 0

    print("=" * 70)


if __name__ == "__main__":
    sys.exit(main())
