"""Dépendance réutilisable pour déterminer le tenant courant via les en-têtes."""

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
    """Récupère le tenant courant depuis l'utilisateur authentifié (cookies ou bearer).

    Cette dépendance extrait l'utilisateur depuis :
    - le cookie httpOnly (préféré pour les navigateurs)
    - l'en-tête Authorization: Bearer (pour les clients API)
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


# ============================================================================
# TENANTS FIXES PAR MODULE
# ============================================================================

# Tenants prédéfinis (correspondent aux données en base)
RESTAURANT_TENANT = Tenant(id=2, code="restaurant", name="Restaurant HQ")
TRESORERIE_TENANT = Tenant(id=3, code="tresorerie", name="Trésorerie HQ")
INTELLIGENCE_TENANT = Tenant(id=4, code="intelligence", name="Intelligence")


async def get_restaurant_tenant(request: Request) -> Tenant:
    """
    Dépendance pour le module restaurant.
    Retourne toujours le tenant restaurant (id=2).
    N'exige pas d'authentification pour permettre l'accès aux données restaurant.
    """
    # Toujours retourner le tenant restaurant, sans vérifier l'auth
    return RESTAURANT_TENANT


async def get_restaurant_tenant_strict(request: Request) -> Tenant:
    """
    Dépendance pour le module restaurant avec authentification obligatoire.
    Vérifie l'authentification mais utilise toujours le tenant restaurant (id=2).
    """
    user = get_current_user_from_request(request)
    return RESTAURANT_TENANT


async def get_intelligence_tenant(request: Request) -> Tenant:
    """
    Dépendance pour le module intelligence/scoring.
    Vérifie l'authentification mais utilise toujours le tenant intelligence (id=4).
    """
    user = get_current_user_from_request(request)
    return INTELLIGENCE_TENANT


async def get_epicerie_tenant(request: Request) -> Tenant:
    """
    Dépendance pour le module épicerie (operations, catalogue, etc.).
    Vérifie l'authentification mais utilise toujours le tenant epicerie (id=1).
    """
    user = get_current_user_from_request(request)
    return DEFAULT_TENANT


async def get_tenant_by_route(request: Request) -> Tenant:
    """
    Dépendance intelligente qui détermine le tenant selon la route.
    /restaurant/* -> tenant 2
    /supplier-scoring/* -> tenant 1 (epicerie - pour les fournisseurs)
    /intelligence/* -> tenant 4
    Autres -> tenant du token JWT
    """
    path = request.url.path.lower()

    # Vérifier l'authentification d'abord
    user = get_current_user_from_request(request)

    # Router vers le bon tenant selon le path
    if path.startswith("/restaurant"):
        return RESTAURANT_TENANT
    elif path.startswith("/supplier-scoring"):
        # Les fournisseurs sont dans epicerie
        return DEFAULT_TENANT
    elif path.startswith("/intelligence") or path.startswith("/forecasting") or path.startswith("/anomaly"):
        return INTELLIGENCE_TENANT

    # Par défaut, utiliser le tenant du token
    tenant = resolve_tenant(user.tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant introuvable",
        )
    return tenant
