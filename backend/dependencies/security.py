"""Utilitaires JWT/OAuth2 et dépendances réutilisables."""

from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from core.user_service import ALLOWED_ROLES
from backend.settings import Settings


DEFAULT_SECRET = "change-me-in-prod"
DEFAULT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Configuration des cookies
COOKIE_NAME_ACCESS = "access_token"
COOKIE_NAME_REFRESH = "refresh_token"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")  # lax, strict ou none

logger = logging.getLogger(__name__)


# Schéma OAuth2 - auto_error=False autorise le repli sur l'auth cookie
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


class AuthenticatedUser(BaseModel):
    """Contexte utilisateur extrait d'un access token JWT."""

    id: int
    username: str
    role: str
    tenant_id: int


ROLE_PRIORITY = {"standard": 0, "manager": 1, "admin": 2}

# Mémoire de révocation simple (en RAM) pour invalider les jti encore valides.
_REVOKED_JTIS: dict[str, float] = {}


def _is_production_env() -> bool:
    env = (os.getenv("APP_ENV") or os.getenv("ENV") or "development").lower()
    return env in {"prod", "production", "staging"}


def _load_secrets(settings: Settings | None = None) -> list[str]:
    settings = settings or Settings.load()
    secrets_env = os.getenv("JWT_SECRET_KEYS")
    secrets: list[str] = []
    if secrets_env:
        secrets = [entry.strip() for entry in secrets_env.split(",") if entry.strip()]
    else:
        single = os.getenv("JWT_SECRET_KEY")
        if single:
            secrets = [single.strip()]

    if not secrets:
        if _is_production_env() and not settings.allow_insecure_jwt_default:
            raise RuntimeError("JWT_SECRET_KEY manquant : refuse de démarrer en environnement sensible")
        logger.warning("Using default JWT secret; set JWT_SECRET_KEY/JWT_SECRET_KEYS pour sécuriser la prod")
        secrets = [DEFAULT_SECRET]

    for value in secrets:
        if len(value) < 32:
            raise RuntimeError("JWT secret trop court (<32 caractères). Générez une clé robuste.")
    return secrets


_APP_SETTINGS = Settings.load()
_SECRET_KEYS = _APP_SETTINGS.jwt_secret_keys or _load_secrets(_APP_SETTINGS)


def _get_secret() -> str:
    return _SECRET_KEYS[0]


def _get_verify_secrets() -> list[str]:
    return _SECRET_KEYS


def _get_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", DEFAULT_ALGORITHM)


def create_access_token(claims: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Sérialise les claims fournis dans un JWT signé avec des claims adaptés à la rotation."""

    payload = claims.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload.update({"exp": expire, "jti": uuid.uuid4().hex, "type": "access"})
    return jwt.encode(payload, _get_secret(), algorithm=_get_algorithm())


def create_refresh_token(claims: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Crée un refresh token avec une durée d'expiration plus longue."""

    payload = {
        "sub": claims.get("sub"),
        "username": claims.get("username"),
        "tenant_id": claims.get("tenant_id"),
        "type": "refresh",
    }
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload.update({"exp": expire, "jti": uuid.uuid4().hex})
    return jwt.encode(payload, _get_secret(), algorithm=_get_algorithm())


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_max_age: int | None = None,
    refresh_max_age: int | None = None,
) -> None:
    """Définit les cookies httpOnly pour les tokens d'accès et de rafraîchissement."""

    access_max_age = access_max_age or ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_max_age = refresh_max_age or REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    response.set_cookie(
        key=COOKIE_NAME_ACCESS,
        value=access_token,
        max_age=access_max_age,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        key=COOKIE_NAME_REFRESH,
        value=refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/auth",  # Refresh token accessible uniquement sur les endpoints /auth
    )


def clear_auth_cookies(response: Response) -> None:
    """Supprime les cookies d'authentification (logout)."""

    response.delete_cookie(key=COOKIE_NAME_ACCESS, path="/")
    response.delete_cookie(key=COOKIE_NAME_REFRESH, path="/auth")


def _decode_token(token: str) -> dict[str, Any]:
    last_error: Exception | None = None
    for secret in _get_verify_secrets():
        try:
            payload = jwt.decode(token, secret, algorithms=[_get_algorithm()])
            _enforce_not_revoked(payload)
            return payload
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expiré",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except jwt.InvalidTokenError as exc:  # pragma: no cover - cas defensif
            last_error = exc
            continue

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide",
        headers={"WWW-Authenticate": "Bearer"},
    ) from last_error


def _extract_token_from_request(request: Request) -> str | None:
    """Extrait le token depuis le cookie uniquement (mode HTTP-Only strict).

    Note : Le repli sur l'en-tête Authorization a été supprimé afin de
    forcer l'utilisation exclusive des cookies HTTP-Only.
    """

    # Extraction uniquement depuis le cookie HTTP-Only
    token = request.cookies.get(COOKIE_NAME_ACCESS)
    return token if token else None


def get_current_user_from_request(request: Request) -> AuthenticatedUser:
    """Récupère l'utilisateur courant depuis le cookie HTTP-Only."""

    token = _extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token(token)

    # Vérifie qu'il s'agit d'un access token, pas d'un refresh token
    if payload.get("type") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token non autorise pour cette operation",
        )

    try:
        user_id = int(payload["sub"])
        username = str(payload["username"])
        role = str(payload["role"])
        tenant_id = int(payload["tenant_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant des informations nécessaires",
        ) from exc

    role_lower = role.lower()
    if role_lower not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Rôle inconnu dans le token",
        )

    _gc_revoked()

    return AuthenticatedUser(id=user_id, username=username, role=role_lower, tenant_id=tenant_id)


def get_current_user(token: str | None = Depends(oauth2_scheme)) -> AuthenticatedUser:
    """Héritage : récupère l'utilisateur depuis un token Bearer OAuth2."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token(token)

    # Vérifie qu'il s'agit d'un access token
    if payload.get("type") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token non autorise pour cette operation",
        )

    try:
        user_id = int(payload["sub"])
        username = str(payload["username"])
        role = str(payload["role"])
        tenant_id = int(payload["tenant_id"])
    except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - cas defensif
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant des informations nécessaires",
        ) from exc

    role_lower = role.lower()
    if role_lower not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Rôle inconnu dans le token",
        )

    _gc_revoked()

    return AuthenticatedUser(id=user_id, username=username, role=role_lower, tenant_id=tenant_id)


def decode_refresh_token(token: str) -> dict[str, Any]:
    """Décode et valide un refresh token."""

    payload = _decode_token(token)

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide pour rafraichissement",
        )

    return payload


async def require_user(request: Request) -> AuthenticatedUser:
    """Récupère l'utilisateur courant depuis le cookie HTTP-Only."""
    return get_current_user_from_request(request)


def require_roles(*roles: str) -> Callable:
    """Exige des rôles spécifiques pour accéder à la ressource."""
    allowed = {role.lower() for role in roles} or set(ALLOWED_ROLES)

    async def _checker(request: Request) -> AuthenticatedUser:
        user = get_current_user_from_request(request)
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rôle insuffisant pour accéder à cette ressource",
            )
        return user

    return _checker


async def enforce_default_rbac(request: Request) -> AuthenticatedUser:
    """Autorise toute personne authentifiée à lire ; managers/admins pour modifier.

    Authentification uniquement via cookies HTTP-Only.
    """

    user = get_current_user_from_request(request)

    method = request.method.upper()
    if method in {"POST", "PUT", "PATCH", "DELETE"} and ROLE_PRIORITY[user.role] < ROLE_PRIORITY["manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rôle manager ou admin requis pour modifier les données",
        )
    return user


def revoke_token(token: str) -> None:
    """Ajoute le jti d'un token à la liste de révocation jusqu'à expiration."""

    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        jti = payload.get("jti")
        exp = payload.get("exp")
    except Exception:  # pragma: no cover
        return

    if not jti or not exp:
        return
    _REVOKED_JTIS[str(jti)] = float(exp)


def _enforce_not_revoked(payload: dict[str, Any]) -> None:
    jti = str(payload.get("jti") or "")
    if not jti:
        return
    exp = payload.get("exp")
    cutoff = _REVOKED_JTIS.get(jti)
    if cutoff is None:
        return
    if exp and time.time() > float(cutoff):
        _REVOKED_JTIS.pop(jti, None)
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token révoqué",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _gc_revoked() -> None:
    now = time.time()
    to_delete = [jti for jti, exp_ts in _REVOKED_JTIS.items() if exp_ts <= now]
    for jti in to_delete:
        _REVOKED_JTIS.pop(jti, None)
