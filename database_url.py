"""Utilities to assemble the DATABASE_URL used by Python services."""

from __future__ import annotations

import os
from urllib.parse import quote_plus


def _get_env(name: str) -> str | None:
    """Return the environment variable when it is a non-empty string."""

    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def get_database_url() -> str:
    """Build a SQLAlchemy compatible DATABASE_URL.

    Priority order:

    1. ``DATABASE_URL`` (already complete connection string).
    2. Individual ``POSTGRES_*`` / ``DB_*`` environment variables.
    3. Sensible local defaults.
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
