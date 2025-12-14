"""Reusable dependency to resolve the current tenant from request headers."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import text

from core.data_repository import get_engine
from core.tenant_service import ensure_tenants_table
from backend.dependencies.security import (
    AuthenticatedUser,
    get_current_user_from_request,
    _extract_token_from_request,
)


@dataclass(frozen=True)
class Tenant:
    id: int
    code: str
    name: str


DEFAULT_TENANT = Tenant(id=1, code="epicerie", name="Épicerie HQ")


logger = logging.getLogger(__name__)
DEFAULT_TENANT_ID_ENV = "NEWCMS_DEFAULT_TENANT_ID"
ALLOW_ANON_ENV = "NEWCMS_ALLOW_ANON"


def bootstrap_tenants_if_enabled() -> None:
    """Initialise la table des tenants seulement si l'environnement l'autorise."""

    if os.getenv("SKIP_TENANT_INIT"):
        return
    try:
        ensure_tenants_table()
    except Exception as exc:  # pragma: no cover - mise en garde démarrage
        logger.warning("Impossible d'initialiser la table tenants au démarrage: %s", exc)


@lru_cache(maxsize=32)
def _load_tenant(identifier: str) -> Tenant | None:
    engine = get_engine()
    query = text(
        """
        SELECT id, name, code
        FROM tenants
        WHERE code = :code OR CAST(id AS TEXT) = :code
        LIMIT 1
        """
    )
    with engine.begin() as conn:
        row = conn.execute(query, {"code": identifier}).fetchone()
        if not row:
            return None
        return Tenant(id=int(row.id), code=str(row.code), name=str(row.name))


def resolve_tenant(identifier: Optional[str | int]) -> Tenant | None:
    if identifier is None:
        return None
    text_id = str(identifier).strip()
    if not text_id:
        return None
    return _load_tenant(text_id)


async def get_current_tenant(request: Request) -> Tenant:
    """Get current tenant from authenticated user (supports cookies and bearer).

    This dependency extracts the user from either:
    - httpOnly cookie (preferred for browsers)
    - Authorization: Bearer header (for API clients)
    """
    user = get_current_user_from_request(request)
    tenant = resolve_tenant(user.tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant introuvable",
    )
    return tenant


async def get_current_tenant_or_default(request: Request) -> Tenant:
    """
    Variante permissive pour le newCMS : accepte l'absence de token en mode démo.

    - Si un token est présent, on l'utilise (même logique que get_current_tenant).
    - Sinon, si NEWCMS_ALLOW_ANON est défini (truthy), on retourne le tenant par défaut
      ou celui fourni via l'en-tête X-Tenant ou la variable d'environnement NEWCMS_DEFAULT_TENANT_ID.
    """
    token = _extract_token_from_request(request)
    if token:
        return await get_current_tenant(request)

    if os.getenv(ALLOW_ANON_ENV, "1").lower() not in {"1", "true", "yes"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tenant_identifier = (
        request.headers.get("X-Tenant")
        or os.getenv(DEFAULT_TENANT_ID_ENV)
        or str(DEFAULT_TENANT.id)
    )
    tenant = resolve_tenant(tenant_identifier)
    return tenant or DEFAULT_TENANT
