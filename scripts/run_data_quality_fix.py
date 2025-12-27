#!/usr/bin/env python3
"""
Module d'exécution du script SQL de correction de qualité des données.

Ce script permet de:
- Exécuter le fichier data_quality_fix.sql dans le conteneur Docker PostgreSQL
- Corriger automatiquement les problèmes de qualité de données détectés
- Réparer les prix manquants, stocks élevés, doublons, labels vides
- Utiliser docker compose pour accéder à la base de données

Le script SQL applique des corrections standardisées identifiées par l'audit.

Usage:
    python scripts/run_data_quality_fix.py

Prérequis:
    - Docker et docker-compose installés et en cours d'exécution
    - Conteneur 'db' actif dans docker-compose
    - Fichier scripts/data_quality_fix.sql présent
    - Fichier .env avec configuration PostgreSQL

Variables d'environnement:
    Chargées depuis .env:
    - POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, etc.

Fichiers d'entrée:
    - scripts/data_quality_fix.sql : Fichier SQL avec les corrections

Workflow:
    1. Localise le fichier data_quality_fix.sql
    2. Exécute docker-compose exec db psql avec le fichier SQL
    3. Applique les corrections directement en base

Notes:
    - Le script utilise subprocess pour exécuter docker compose
    - Les erreurs SQL sont propagées et arrêtent l'exécution
    - Recommandé de faire un backup avant exécution
"""
from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    fix_sql = root / "scripts" / "data_quality_fix.sql"
    cmd = ["docker", "compose", "--env-file", str(root / ".env"), "exec", "-T", "db", "psql", "-U", "postgres", "-d", "epicerie", "-f", str(fix_sql)]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
