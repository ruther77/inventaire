"""Utilitaires pour assembler un DATABASE_URL.

Basé sur /home/ruuuzer/Documents/monprojet/core/database_url.py.
"""

from __future__ import annotations

import os
from urllib.parse import quote_plus


def _get_env(name: str) -> str | None:
    """Retourne une variable d'environnement si elle est non vide."""
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def get_database_url() -> str:
    """Construit un DATABASE_URL compatible SQLAlchemy.

    Priority order:
    1) DATABASE_URL
    2) POSTGRES_* or DB_* variables
    3) valeurs locales par défaut
    """
    explicit_url = _get_env("DATABASE_URL")
    if explicit_url:
        return explicit_url

    user = _get_env("POSTGRES_USER") or "postgres"
    password = _get_env("POSTGRES_PASSWORD")
    database = _get_env("POSTGRES_DB") or _get_env("DB_NAME") or "epicerie"
    host = _get_env("DB_HOST") or _get_env("POSTGRES_HOST") or "localhost"
    port = _get_env("DB_PORT") or _get_env("POSTGRES_PORT") or "5432"

    user_part = quote_plus(user)
    if password is None:
        auth_part = user_part
    else:
        auth_part = f"{user_part}:{quote_plus(password)}"

    return f"postgresql+psycopg2://{auth_part}@{host}:{port}/{database}"


__all__ = ["get_database_url"]
