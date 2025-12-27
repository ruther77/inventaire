"""
Module des schémas Pydantic pour l'authentification.

Ce module définit les modèles de données pour:
- Authentification OAuth2 Password Bearer
- Authentification par cookies httpOnly
- Rafraîchissement de tokens
- Payload utilisateur authentifié

Schémas principaux:
1. AuthenticatedUserPayload: Informations utilisateur extraites du JWT
2. TokenResponse: Réponse standard OAuth2 avec access_token
3. CookieTokenResponse: Réponse pour auth basée cookies (sans token exposé)
4. RefreshResponse: Réponse de rafraîchissement de token

Notes de sécurité:
- Les tokens ne sont jamais stockés côté serveur (stateless)
- Les cookies utilisent httpOnly + secure + SameSite
- Le payload JWT est minimal (id, username, role, tenant)
- Les rôles sont validés via enum strict (admin/manager/standard)
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AuthenticatedUserPayload(BaseModel):
    """
    Payload utilisateur extrait d'un token JWT validé.

    Contient les informations essentielles de l'utilisateur pour
    l'autorisation et le contexte de requête.

    Attributes:
        id: ID unique de l'utilisateur en base
        username: Nom d'utilisateur (login)
        role: Rôle RBAC (admin, manager, ou standard)
        tenant_id: ID du tenant associé (isolation multi-tenant)
        tenant_code: Code court du tenant (ex: 'epicerie', 'restaurant')
        tenant_name: Nom complet du tenant pour affichage
    """
    id: int
    username: str
    role: str = Field(description="admin | manager | standard")
    tenant_id: int
    tenant_code: str
    tenant_name: str


class TokenResponse(BaseModel):
    """
    Réponse standard OAuth2 Password Bearer.

    Utilisée pour les clients API qui gèrent les tokens manuellement
    (ex: applications mobiles, scripts automation).

    Attributes:
        access_token: JWT signé à inclure dans Authorization header
        token_type: Toujours "bearer" pour OAuth2
        expires_in: Durée de validité en secondes (typiquement 900s = 15min)
        user: Informations de l'utilisateur authentifié
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthenticatedUserPayload


class CookieTokenResponse(BaseModel):
    """
    Réponse pour authentification basée cookies (recommandé web).

    Le token n'est PAS inclus dans le corps de réponse mais dans un cookie
    httpOnly sécurisé. Plus sûr que le stockage localStorage côté client.

    Attributes:
        message: Message de confirmation
        expires_in: Durée de validité du token en secondes
        user: Informations de l'utilisateur authentifié
    """
    message: str = "Authentification reussie"
    expires_in: int
    user: AuthenticatedUserPayload


class RefreshResponse(BaseModel):
    """
    Réponse de rafraîchissement de token.

    Permet d'obtenir un nouveau access token sans re-saisir les credentials
    en utilisant le refresh token (durée de vie longue, 7 jours).

    Attributes:
        message: Message de confirmation
        expires_in: Durée de validité du nouveau token en secondes
    """
    message: str = "Token rafraichi"
    expires_in: int


__all__ = [
    "AuthenticatedUserPayload",
    "TokenResponse",
    "CookieTokenResponse",
    "RefreshResponse",
]
