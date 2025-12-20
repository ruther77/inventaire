from __future__ import annotations

from pydantic import BaseModel, Field


class AuthenticatedUserPayload(BaseModel):
    id: int
    username: str
    role: str = Field(description="admin | manager | standard")
    tenant_id: int
    tenant_code: str
    tenant_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthenticatedUserPayload


class CookieTokenResponse(BaseModel):
    """Réponse pour l'authentification basée sur cookie (pas de token dans le corps)."""
    message: str = "Authentification reussie"
    expires_in: int
    user: AuthenticatedUserPayload


class RefreshResponse(BaseModel):
    """Réponse pour le rafraîchissement de token."""
    message: str = "Token rafraichi"
    expires_in: int


__all__ = [
    "AuthenticatedUserPayload",
    "TokenResponse",
    "CookieTokenResponse",
    "RefreshResponse",
]
