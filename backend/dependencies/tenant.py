"""Reusable dependency to resolve the current tenant from request headers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy import text

from core.data_repository import get_engine
from core.tenant_service import ensure_tenants_table
from backend.dependencies.security import AuthenticatedUser, get_current_user


@dataclass(frozen=True)
class Tenant:
    id: int
    code: str
    name: str


DEFAULT_TENANT = Tenant(id=1, code="epicerie", name="Épicerie HQ")


ensure_tenants_table()


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


async def get_current_tenant(user: AuthenticatedUser = Depends(get_current_user)) -> Tenant:
    tenant = resolve_tenant(user.tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant introuvable",
        )
    return tenant
