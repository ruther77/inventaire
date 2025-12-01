"""JWT/OAuth2 utilities and reusable dependencies."""

from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from core.user_service import ALLOWED_ROLES
from backend.settings import Settings


DEFAULT_SECRET = "change-me-in-prod"
DEFAULT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

logger = logging.getLogger(__name__)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class AuthenticatedUser(BaseModel):
    """User context extracted from a JWT access token."""

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
    """Serialize the provided claims into a signed JWT with rotation-friendly claims."""

    payload = claims.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload.update({"exp": expire, "jti": uuid.uuid4().hex})
    return jwt.encode(payload, _get_secret(), algorithm=_get_algorithm())


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
        except jwt.InvalidTokenError as exc:  # pragma: no cover - defensive
            last_error = exc
            continue

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide",
        headers={"WWW-Authenticate": "Bearer"},
    ) from last_error


def get_current_user(token: str = Depends(oauth2_scheme)) -> AuthenticatedUser:
    payload = _decode_token(token)
    try:
        user_id = int(payload["sub"])
        username = str(payload["username"])
        role = str(payload["role"])
        tenant_id = int(payload["tenant_id"])
    except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - defensive
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


def require_user(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
    return user


def require_roles(*roles: str) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    allowed = {role.lower() for role in roles} or set(ALLOWED_ROLES)

    def _checker(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rôle insuffisant pour accéder à cette ressource",
            )
        return user

    return _checker


def enforce_default_rbac(
    request: Request, user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """Allow anyone authenticated to read, managers/admins to mutate."""

    method = request.method.upper()
    if method in {"POST", "PUT", "PATCH", "DELETE"} and ROLE_PRIORITY[user.role] < ROLE_PRIORITY["manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rôle manager ou admin requis pour modifier les données",
        )
    return user


def revoke_token(token: str) -> None:
    """Ajoute le jti d'un token à la liste de révocation jusqu'à son expiration."""

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
