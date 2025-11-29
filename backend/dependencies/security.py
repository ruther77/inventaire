"""JWT/OAuth2 utilities and reusable dependencies."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from core.user_service import ALLOWED_ROLES


DEFAULT_SECRET = "change-me-in-prod"
DEFAULT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "120"))


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class AuthenticatedUser(BaseModel):
    """User context extracted from a JWT access token."""

    id: int
    username: str
    role: str
    tenant_id: int


ROLE_PRIORITY = {"standard": 0, "manager": 1, "admin": 2}


def _get_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY")
    if secret:
        return secret
    # Provide a deterministic default to simplify local usage.
    return DEFAULT_SECRET


def _get_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", DEFAULT_ALGORITHM)


def create_access_token(claims: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Serialize the provided claims into a signed JWT."""

    payload = claims.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload.update({"exp": expire})
    return jwt.encode(payload, _get_secret(), algorithm=_get_algorithm())


def _decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _get_secret(), algorithms=[_get_algorithm()])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


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
