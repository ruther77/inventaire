"""Authentication endpoints (OAuth2 password flow with JWT)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, status

from backend.dependencies.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from backend.dependencies.tenant import DEFAULT_TENANT, Tenant, resolve_tenant
from backend.schemas.auth import AuthenticatedUserPayload, TokenResponse
from core.user_service import authenticate_user


router = APIRouter(prefix="/auth", tags=["auth"])


class OAuth2TenantRequestForm:
    """Extension du formulaire OAuth2 standard avec la notion de tenant."""

    def __init__(
        self,
        grant_type: str | None = Form(default=None, regex="password"),
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

