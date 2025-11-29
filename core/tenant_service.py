from __future__ import annotations  # Active l'évaluation différée des annotations

import os  # Accès aux variables d'environnement

from sqlalchemy import text  # Permet de construire des requêtes SQL textuelles

from .data_repository import exec_sql, get_engine  # Fonctions utilitaires d'accès à la base


_TENANT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""  # Requête SQL pour créer la table tenants si elle n'existe pas

_DEFAULT_TENANTS: tuple[dict[str, object], ...] = (
    {"id": 1, "name": "Épicerie HQ", "code": "epicerie"},
    {"id": 2, "name": "Restaurant HQ", "code": "restaurant"},
)  # Locaux par défaut insérés au démarrage


def ensure_tenants_table() -> None:
    """Crée la table tenants et insère les lignes de base si nécessaire."""  # Docstring en français

    # Cette table est consultée par `backend.dependencies.tenant` pour
    # résoudre `X-Tenant-Id` et appliquer l'isolation multitenant.

    if os.getenv("SKIP_TENANT_INIT"):  # Permet de sauter l'initialisation via variable d'environnement
        return  # Sort si on demande de ne pas initialiser

    exec_sql(text(_TENANT_TABLE_SQL))  # Exécute la création de table idempotente
    engine = get_engine()  # Récupère l'engine SQLAlchemy partagé
    with engine.begin() as conn:  # Ouvre une transaction
        for tenant in _DEFAULT_TENANTS:  # Parcourt les locataires par défaut
            conn.execute(
                text(
                    """
                    INSERT INTO tenants (id, name, code)
                    VALUES (:id, :name, :code)
                    ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
                    """
                ),
                tenant,
            )  # Insert ou met à jour le nom si le code existe
        conn.execute(
            text(
                """
                SELECT setval(
                    pg_get_serial_sequence('tenants', 'id'),
                    COALESCE((SELECT MAX(id) FROM tenants), 1),
                    TRUE
                )
                """
            )
        )  # Recalibre la séquence pour éviter les collisions d'ID
