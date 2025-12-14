"""Authentication endpoints (OAuth2 password flow with JWT).

Supports both:
- Traditional OAuth2 bearer tokens (for API clients)
- httpOnly cookies with refresh tokens (for browser clients)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status

from backend.dependencies.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    COOKIE_NAME_REFRESH,
    create_access_token,
    create_refresh_token,
    set_auth_cookies,
    clear_auth_cookies,
    decode_refresh_token,
    revoke_token,
)
from backend.dependencies.tenant import DEFAULT_TENANT, Tenant, resolve_tenant
from backend.schemas.auth import (
    AuthenticatedUserPayload,
    TokenResponse,
    CookieTokenResponse,
    RefreshResponse,
)
from core.user_service import authenticate_user, get_user_by_id


router = APIRouter(prefix="/auth", tags=["auth"])


class OAuth2TenantRequestForm:
    """Extension du formulaire OAuth2 standard avec la notion de tenant."""

    def __init__(
        self,
        grant_type: str | None = Form(default=None, pattern="password"),
        username: str = Form(...),
        password: str = Form(...),
        scope: str = Form(default=""),
        client_id: str | None = Form(default=None),
        client_secret: str | None = Form(default=None),
        tenant: str = Form(default=DEFAULT_TENANT.code),
    ) -> None:
        self.grant_type = grant_type
        self.username = username
        self.password = password
        self.scopes = scope.split()
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant = tenant


def _resolve_tenant(tenant_identifier: str | int | None) -> Tenant:
    tenant = resolve_tenant(tenant_identifier)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant introuvable",
        )
    return tenant


@router.post("/token", response_model=TokenResponse)
def issue_token(form_data: OAuth2TenantRequestForm = Depends()) -> TokenResponse:
    """Issue OAuth2 bearer token (for API clients)."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tenant = _resolve_tenant(form_data.tenant)
    claims = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "tenant_id": tenant.id,
        "tenant_code": tenant.code,
    }
    token = create_access_token(claims)
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=AuthenticatedUserPayload(
            id=user["id"],
            username=user["username"],
            role=user["role"],
            tenant_id=tenant.id,
            tenant_code=tenant.code,
            tenant_name=tenant.name,
        ),
    )


@router.post("/login", response_model=CookieTokenResponse)
def login_with_cookies(
    response: Response,
    form_data: OAuth2TenantRequestForm = Depends(),
) -> CookieTokenResponse:
    """Login and set httpOnly cookies (recommended for browser clients).

    This endpoint:
    1. Validates credentials
    2. Creates access token (short-lived, 15 min)
    3. Creates refresh token (long-lived, 7 days)
    4. Sets both as httpOnly cookies

    The access token cookie is available on all paths.
    The refresh token cookie is only available on /auth endpoints.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
        )

    tenant = _resolve_tenant(form_data.tenant)
    claims = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "tenant_id": tenant.id,
        "tenant_code": tenant.code,
    }

    access_token = create_access_token(claims)
    refresh_token = create_refresh_token(claims)

    set_auth_cookies(response, access_token, refresh_token)

    return CookieTokenResponse(
        message="Authentification reussie",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=AuthenticatedUserPayload(
            id=user["id"],
            username=user["username"],
            role=user["role"],
            tenant_id=tenant.id,
            tenant_code=tenant.code,
            tenant_name=tenant.name,
        ),
    )


@router.post("/refresh", response_model=RefreshResponse)
def refresh_access_token(request: Request, response: Response) -> RefreshResponse:
    """Refresh the access token using the refresh token cookie.

    This endpoint:
    1. Reads the refresh token from httpOnly cookie
    2. Validates the refresh token
    3. Loads fresh user data from database
    4. Issues new access + refresh tokens (rotation)
    5. Revokes the old refresh token
    """
    refresh_token = request.cookies.get(COOKIE_NAME_REFRESH)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token manquant",
        )

    # Decode and validate refresh token
    payload = decode_refresh_token(refresh_token)

    user_id = int(payload["sub"])
    tenant_id = int(payload["tenant_id"])

    # Load fresh user data from database
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
        )

    tenant = _resolve_tenant(tenant_id)

    # Create new tokens
    claims = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "tenant_id": tenant.id,
        "tenant_code": tenant.code,
    }

    new_access_token = create_access_token(claims)
    new_refresh_token = create_refresh_token(claims)

    # Revoke old refresh token
    revoke_token(refresh_token)

    # Set new cookies
    set_auth_cookies(response, new_access_token, new_refresh_token)

    return RefreshResponse(
        message="Token rafraichi",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, str]:
    """Logout and clear authentication cookies.

    This endpoint:
    1. Revokes the current refresh token
    2. Clears both access and refresh cookies
    """
    refresh_token = request.cookies.get(COOKIE_NAME_REFRESH)
    if refresh_token:
        revoke_token(refresh_token)

    clear_auth_cookies(response)

    return {"message": "Deconnexion reussie"}
