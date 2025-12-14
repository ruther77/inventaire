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
    """Response for cookie-based authentication (no token in body)."""
    message: str = "Authentification reussie"
    expires_in: int
    user: AuthenticatedUserPayload


class RefreshResponse(BaseModel):
    """Response for token refresh."""
    message: str = "Token rafraichi"
    expires_in: int


__all__ = [
    "AuthenticatedUserPayload",
    "TokenResponse",
    "CookieTokenResponse",
    "RefreshResponse",
]

