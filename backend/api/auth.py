"""Endpoints d'authentification (flux OAuth2 password avec JWT).

Prend en charge :
- Les tokens bearer OAuth2 traditionnels (pour les clients API)
- Les cookies httpOnly avec refresh tokens (pour les clients navigateur)
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
from backend.middleware.rate_limiter import rate_limit
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
@rate_limit(requests=5, window=60, burst=2)  # Sécurité : limite à 5 tentatives/minute contre brute force
def issue_token(request: Request, form_data: OAuth2TenantRequestForm = Depends()) -> TokenResponse:
    """Émet un token bearer OAuth2 (pour les clients API)."""
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
@rate_limit(requests=5, window=60, burst=2)  # Sécurité : limite à 5 tentatives/minute contre brute force
def login_with_cookies(
    request: Request,
    response: Response,
    form_data: OAuth2TenantRequestForm = Depends(),
) -> CookieTokenResponse:
    """Connexion et pose des cookies httpOnly (recommandé pour les clients navigateur).

    Cet endpoint :
    1. Valide les identifiants
    2. Crée l'access token (court, 15 min)
    3. Crée le refresh token (long, 7 jours)
    4. Place les deux en cookies httpOnly

    Le cookie d'access token est disponible sur tous les chemins.
    Le cookie de refresh n'est disponible que sur les endpoints /auth.
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
    """Rafraîchit le token d'accès en utilisant le cookie de refresh.

    Cet endpoint :
    1. Lit le refresh token depuis le cookie httpOnly
    2. Valide le refresh token
    3. Charge les données utilisateur fraîches depuis la base
    4. Émet un nouvel access + refresh token (rotation)
    5. Révoque l'ancien refresh token
    """
    refresh_token = request.cookies.get(COOKIE_NAME_REFRESH)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token manquant",
        )

    # Décoder et valider le refresh token
    payload = decode_refresh_token(refresh_token)

    user_id = int(payload["sub"])
    tenant_id = int(payload["tenant_id"])

    # Charger les données utilisateur fraîches depuis la base
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
        )

    tenant = _resolve_tenant(tenant_id)

    # Créer de nouveaux tokens
    claims = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "tenant_id": tenant.id,
        "tenant_code": tenant.code,
    }

    new_access_token = create_access_token(claims)
    new_refresh_token = create_refresh_token(claims)

    # Révoquer l'ancien refresh token
    revoke_token(refresh_token)

    # Poser les nouveaux cookies
    set_auth_cookies(response, new_access_token, new_refresh_token)

    return RefreshResponse(
        message="Token rafraichi",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, str]:
    """Déconnecte et supprime les cookies d'authentification.

    Cet endpoint :
    1. Révoque le refresh token courant
    2. Supprime les cookies access et refresh
    """
    refresh_token = request.cookies.get(COOKIE_NAME_REFRESH)
    if refresh_token:
        revoke_token(refresh_token)

    clear_auth_cookies(response)

    return {"message": "Deconnexion reussie"}
