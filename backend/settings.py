"""
Module de configuration du backend FastAPI.

Ce module étend les settings du core avec des paramètres spécifiques
au backend API:

Paramètres additionnels:
- allow_insecure_jwt_default: Autorise le secret JWT par défaut en dev
- log_level: Niveau de logging (DEBUG, INFO, WARNING, ERROR)

Hérite de:
- AppSettings (core): Configuration base incluant DB, CORS, JWT

Configuration via variables d'environnement:
- ALLOW_INSECURE_JWT_DEFAULT=true: Active le secret par défaut (dev uniquement)
- LOG_LEVEL=DEBUG: Niveau de log détaillé

Note:
    En production, le secret JWT par défaut est toujours rejeté
    même si ALLOW_INSECURE_JWT_DEFAULT=true. Utilisez JWT_SECRET_KEY.
"""

from __future__ import annotations

import os

from core.settings import AppSettings as CoreSettings


class Settings(CoreSettings):
    allow_insecure_jwt_default: bool = False
    log_level: str = "INFO"

    @staticmethod
    def load() -> "Settings":
        core = CoreSettings.load()
        allow_insecure = (
            os.getenv("ALLOW_INSECURE_JWT_DEFAULT", "").strip().lower() in {"1", "true", "yes", "on"}
            or core.app_env in {"development", "dev"}
        )
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        obj = Settings(
            app_env=core.app_env,
            database_url=core.database_url,
            db_pool_size=core.db_pool_size,
            db_pool_max_overflow=core.db_pool_max_overflow,
            cors_allowed_origins=core.cors_allowed_origins,
            jwt_secret_keys=core.jwt_secret_keys,
        )
        object.__setattr__(obj, "allow_insecure_jwt_default", allow_insecure)
        object.__setattr__(obj, "log_level", log_level)
        return obj
