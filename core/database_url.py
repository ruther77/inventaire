"""Utilities to assemble the DATABASE_URL used by Python services."""  # Docstring décrivant l'utilitaire d'URL de base de données

from __future__ import annotations  # Active les annotations reportées pour compatibilité

import os  # Fournit l'accès aux variables d'environnement
from urllib.parse import quote_plus  # Permet d'échapper les parties sensibles de l'URL


def _get_env(name: str) -> str | None:
    """Return the environment variable when it is a non-empty string."""  # Docstring : récupère une variable d'environnement non vide

    value = os.getenv(name)  # Lit la valeur brute dans l'environnement
    if value is None:  # Si la variable n'existe pas
        return None  # On renvoie None explicitement
    value = value.strip()  # Supprime les espaces superflus éventuels
    return value if value else None  # Renvoie la chaîne si non vide sinon None


def get_database_url() -> str:
    """Build a SQLAlchemy compatible DATABASE_URL.

    Priority order:

    1. ``DATABASE_URL`` (already complete connection string).
    2. Individual ``POSTGRES_*`` / ``DB_*`` environment variables.
    3. Sensible local defaults.
    """  # Docstring expliquant l'ordre de priorité pour construire l'URL

    explicit_url = _get_env("DATABASE_URL")  # Tente de lire l'URL directement fournie
    if explicit_url:  # Si une URL complète est déjà définie
        return explicit_url  # On la renvoie sans modification

    user = _get_env("POSTGRES_USER") or "postgres"  # Nom d'utilisateur ou valeur par défaut
    password = _get_env("POSTGRES_PASSWORD")  # Mot de passe éventuel
    database = _get_env("POSTGRES_DB") or _get_env("DB_NAME") or "epicerie"  # Nom de base avec fallback
    host = _get_env("DB_HOST") or _get_env("POSTGRES_HOST") or "localhost"  # Hôte cible ou localhost
    port = _get_env("DB_PORT") or _get_env("POSTGRES_PORT") or "5432"  # Port PostgreSQL par défaut

    user_part = quote_plus(user)  # Échappe l'utilisateur pour l'URL
    if password is None:  # Si aucun mot de passe n'est fourni
        auth_part = user_part  # Seul l'utilisateur est utilisé
    else:  # Sinon on combine utilisateur et mot de passe
        auth_part = f"{user_part}:{quote_plus(password)}"  # Échappe aussi le mot de passe

    return f"postgresql+psycopg2://{auth_part}@{host}:{port}/{database}"  # Construit l'URL SQLAlchemy


__all__ = ["get_database_url"]  # Exporte la fonction publique du module
