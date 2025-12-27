"""Module d'authentification JWT standalone.

Ce module fournit des utilitaires pour la création et validation de tokens JWT,
sans dépendances sur des configurations globales.

Fonctions principales:
    - create_access_token: Crée un access token JWT
    - create_refresh_token: Crée un refresh token JWT
    - decode_token: Décode et valide un token JWT
    - decode_refresh_token: Décode et valide spécifiquement un refresh token
    - is_token_expired: Vérifie si un token est expiré

Exemple d'utilisation:
    >>> from auth import create_access_token, decode_token, is_token_expired
    >>> from datetime import timedelta
    >>>
    >>> secret = "votre-secret-super-secure-de-32-chars-minimum"
    >>> claims = {"sub": "123", "username": "john", "role": "admin"}
    >>>
    >>> # Créer un token
    >>> token = create_access_token(claims, secret_key=secret)
    >>>
    >>> # Décoder le token
    >>> payload = decode_token(token, secret_key=secret)
    >>>
    >>> # Vérifier l'expiration
    >>> if is_token_expired(token, secret_key=secret):
    ...     print("Token expiré!")
"""

from .jwt_utils import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    decode_token,
    is_token_expired,
)

from .user_service import (
    ALLOWED_ROLES,
    DEFAULT_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    PASSWORD_ITERATIONS,
    PasswordPolicy,
    UserRepository,
    authenticate_user,
    create_user,
    generate_secure_password,
    get_user_by_id,
    get_user_by_login,
    hash_password,
    normalize_identifier,
    reset_user_password,
    update_user_role,
    verify_password,
)


__all__ = [
    "ALLOWED_ROLES",
    "DEFAULT_PASSWORD_LENGTH",
    "MIN_PASSWORD_LENGTH",
    "PASSWORD_ITERATIONS",
    "PasswordPolicy",
    "UserRepository",
    "authenticate_user",
    "create_user",
    "generate_secure_password",
    "get_user_by_id",
    "get_user_by_login",
    "hash_password",
    "normalize_identifier",
    "reset_user_password",
    "update_user_role",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "decode_refresh_token",
    "is_token_expired",
]