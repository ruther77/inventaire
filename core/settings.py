"""Configuration centralisée (backend core) avec validation minimale."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AppSettings:
    app_env: str = os.getenv("APP_ENV", os.getenv("ENV", "development")).lower()
    database_url: str = os.getenv("DATABASE_URL", "")
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_pool_max_overflow: int = int(os.getenv("DB_POOL_MAX_OVERFLOW", "20"))
    cors_allowed_origins: list[str] = None
    jwt_secret_keys: list[str] = None

    @staticmethod
    def load() -> "AppSettings":
        cors_raw = os.getenv("CORS_ALLOWED_ORIGINS")
        cors = [entry.strip() for entry in cors_raw.split(",")] if cors_raw else []
        jwt_raw = os.getenv("JWT_SECRET_KEYS") or os.getenv("JWT_SECRET_KEY") or ""
        jwt_keys = [entry.strip() for entry in jwt_raw.split(",") if entry.strip()]
        return AppSettings(
            cors_allowed_origins=cors,
            jwt_secret_keys=jwt_keys,
        )

