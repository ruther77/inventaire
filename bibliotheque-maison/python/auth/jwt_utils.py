"""Utilitaires JWT standalone pour la création et validation de tokens.

Ce module fournit des fonctions standalone pour la gestion de tokens JWT,
sans dépendances sur des configurations globales. Toutes les fonctions
requièrent la clé secrète en paramètre.

Exemples d'utilisation:
    >>> from datetime import timedelta
    >>> secret = "votre-secret-super-secure-de-32-chars-minimum"
    >>>
    >>> # Créer un access token
    >>> claims = {"sub": "123", "username": "john", "role": "admin"}
    >>> token = create_access_token(claims, secret_key=secret)
    >>>
    >>> # Décoder le token
    >>> payload = decode_token(token, secret_key=secret)
    >>> print(payload["username"])  # "john"
    >>>
    >>> # Vérifier l'expiration
    >>> if is_token_expired(token, secret_key=secret):
    >>>     print("Token expiré!")
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt


DEFAULT_ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(
    claims: dict[str, Any],
    expires_delta: timedelta | None = None,
    secret_key: str = None,
    algorithm: str = DEFAULT_ALGORITHM,
) -> str:
    """Crée un access token JWT avec les claims fournis.

    Cette fonction génère un token JWT signé contenant les claims fournis,
    avec ajout automatique de l'expiration, d'un identifiant unique (jti)
    et d'un type de token.

    Args:
        claims: Dictionnaire contenant les claims à inclure dans le token.
            Typiquement: {"sub": user_id, "username": username, "role": role, "tenant_id": tenant_id}
        expires_delta: Durée de validité du token. Si None, utilise 15 minutes par défaut.
        secret_key: Clé secrète pour signer le token (minimum 32 caractères recommandé).
        algorithm: Algorithme de signature (défaut: HS256).

    Returns:
        str: Token JWT signé encodé en string.

    Raises:
        ValueError: Si secret_key est None ou vide.
        TypeError: Si claims n'est pas un dictionnaire.

    Examples:
        >>> from datetime import timedelta
        >>> secret = "ma-cle-secrete-super-longue-et-securisee-32-chars"
        >>>
        >>> # Token avec expiration par défaut (15 min)
        >>> claims = {
        ...     "sub": "42",
        ...     "username": "alice",
        ...     "role": "admin",
        ...     "tenant_id": "1"
        ... }
        >>> token = create_access_token(claims, secret_key=secret)
        >>>
        >>> # Token avec expiration personnalisée (1 heure)
        >>> token = create_access_token(
        ...     claims,
        ...     expires_delta=timedelta(hours=1),
        ...     secret_key=secret
        ... )
        >>>
        >>> # Le token contient automatiquement:
        >>> # - "exp": timestamp d'expiration
        >>> # - "jti": identifiant unique pour la révocation
        >>> # - "type": "access" pour distinguer des refresh tokens

    Note:
        Le token généré inclut automatiquement:
        - exp: timestamp d'expiration (datetime UTC)
        - jti: identifiant unique (UUID hex) pour la révocation/rotation
        - type: "access" pour identifier le type de token
    """
    if not secret_key:
        raise ValueError("secret_key ne peut pas être None ou vide")

    if not isinstance(claims, dict):
        raise TypeError("claims doit être un dictionnaire")

    payload = claims.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload.update({
        "exp": expire,
        "jti": uuid.uuid4().hex,
        "type": "access"
    })

    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_refresh_token(
    claims: dict[str, Any],
    expires_delta: timedelta | None = None,
    secret_key: str = None,
    algorithm: str = DEFAULT_ALGORITHM,
) -> str:
    """Crée un refresh token JWT avec une durée d'expiration longue.

    Les refresh tokens sont utilisés pour obtenir de nouveaux access tokens
    sans redemander les credentials. Ils contiennent un sous-ensemble minimal
    des claims (sub, username, tenant_id) pour des raisons de sécurité.

    Args:
        claims: Dictionnaire contenant les claims source. Seuls "sub", "username"
            et "tenant_id" seront extraits et inclus dans le refresh token.
        expires_delta: Durée de validité du token. Si None, utilise 7 jours par défaut.
        secret_key: Clé secrète pour signer le token (minimum 32 caractères recommandé).
        algorithm: Algorithme de signature (défaut: HS256).

    Returns:
        str: Refresh token JWT signé encodé en string.

    Raises:
        ValueError: Si secret_key est None ou vide.
        TypeError: Si claims n'est pas un dictionnaire.

    Examples:
        >>> secret = "ma-cle-secrete-super-longue-et-securisee-32-chars"
        >>>
        >>> # Refresh token avec expiration par défaut (7 jours)
        >>> claims = {
        ...     "sub": "42",
        ...     "username": "alice",
        ...     "role": "admin",
        ...     "tenant_id": "1"
        ... }
        >>> refresh = create_refresh_token(claims, secret_key=secret)
        >>>
        >>> # Refresh token avec expiration personnalisée (30 jours)
        >>> refresh = create_refresh_token(
        ...     claims,
        ...     expires_delta=timedelta(days=30),
        ...     secret_key=secret
        ... )
        >>>
        >>> # Le refresh token contient uniquement:
        >>> # - sub, username, tenant_id (pas le role)
        >>> # - exp, jti, type: "refresh"

    Note:
        Le refresh token ne contient PAS le role pour des raisons de sécurité.
        Il ne contient que les informations minimales nécessaires pour identifier
        l'utilisateur et générer un nouveau access token.
    """
    if not secret_key:
        raise ValueError("secret_key ne peut pas être None ou vide")

    if not isinstance(claims, dict):
        raise TypeError("claims doit être un dictionnaire")

    # Ne conserver que les claims essentiels pour le refresh token
    payload = {
        "sub": claims.get("sub"),
        "username": claims.get("username"),
        "tenant_id": claims.get("tenant_id"),
        "type": "refresh",
    }

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=DEFAULT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload.update({
        "exp": expire,
        "jti": uuid.uuid4().hex
    })

    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_token(
    token: str,
    secret_key: str = None,
    algorithm: str = DEFAULT_ALGORITHM,
    verify_exp: bool = True,
) -> dict[str, Any]:
    """Décode et valide un JWT (access ou refresh token).

    Cette fonction décode un token JWT, vérifie sa signature et optionnellement
    son expiration. Elle retourne les claims contenus dans le token.

    Args:
        token: Token JWT à décoder (string).
        secret_key: Clé secrète utilisée pour signer le token.
        algorithm: Algorithme de signature (défaut: HS256).
        verify_exp: Si True, vérifie que le token n'est pas expiré (défaut: True).

    Returns:
        dict: Dictionnaire contenant tous les claims du token (sub, username, role,
            tenant_id, exp, jti, type, etc.).

    Raises:
        ValueError: Si secret_key est None ou vide, ou si token est vide.
        jwt.ExpiredSignatureError: Si le token est expiré et verify_exp=True.
        jwt.InvalidTokenError: Si le token est invalide (signature incorrecte,
            format invalide, etc.).

    Examples:
        >>> secret = "ma-cle-secrete-super-longue-et-securisee-32-chars"
        >>>
        >>> # Décoder un token valide
        >>> claims = {"sub": "42", "username": "alice", "role": "admin"}
        >>> token = create_access_token(claims, secret_key=secret)
        >>> payload = decode_token(token, secret_key=secret)
        >>> print(payload["username"])  # "alice"
        >>> print(payload["type"])      # "access"
        >>>
        >>> # Décoder sans vérifier l'expiration (utile pour inspection)
        >>> payload = decode_token(token, secret_key=secret, verify_exp=False)
        >>>
        >>> # Gérer les erreurs
        >>> try:
        ...     payload = decode_token("invalid-token", secret_key=secret)
        ... except jwt.InvalidTokenError as e:
        ...     print(f"Token invalide: {e}")
        >>>
        >>> try:
        ...     payload = decode_token(expired_token, secret_key=secret)
        ... except jwt.ExpiredSignatureError:
        ...     print("Token expiré, rafraîchissement nécessaire")

    Note:
        Cette fonction ne fait aucune distinction entre access et refresh tokens.
        Utilisez decode_refresh_token() pour valider spécifiquement un refresh token.
    """
    if not secret_key:
        raise ValueError("secret_key ne peut pas être None ou vide")

    if not token:
        raise ValueError("token ne peut pas être None ou vide")

    options = {}
    if not verify_exp:
        options["verify_exp"] = False

    payload = jwt.decode(
        token,
        secret_key,
        algorithms=[algorithm],
        options=options
    )

    return payload


def decode_refresh_token(
    token: str,
    secret_key: str = None,
    algorithm: str = DEFAULT_ALGORITHM,
) -> dict[str, Any]:
    """Décode et valide spécifiquement un refresh token.

    Cette fonction décode un token JWT et vérifie qu'il s'agit bien d'un
    refresh token (type="refresh"). Elle lève une exception si le token
    est un access token ou tout autre type.

    Args:
        token: Refresh token JWT à décoder (string).
        secret_key: Clé secrète utilisée pour signer le token.
        algorithm: Algorithme de signature (défaut: HS256).

    Returns:
        dict: Dictionnaire contenant les claims du refresh token (sub, username,
            tenant_id, exp, jti, type).

    Raises:
        ValueError: Si secret_key est None ou vide, si token est vide,
            ou si le token n'est pas de type "refresh".
        jwt.ExpiredSignatureError: Si le token est expiré.
        jwt.InvalidTokenError: Si le token est invalide.

    Examples:
        >>> secret = "ma-cle-secrete-super-longue-et-securisee-32-chars"
        >>>
        >>> # Créer et décoder un refresh token
        >>> claims = {"sub": "42", "username": "alice", "tenant_id": "1"}
        >>> refresh = create_refresh_token(claims, secret_key=secret)
        >>> payload = decode_refresh_token(refresh, secret_key=secret)
        >>> print(payload["username"])  # "alice"
        >>> print(payload["type"])      # "refresh"
        >>>
        >>> # Tenter de décoder un access token (erreur)
        >>> access = create_access_token(claims, secret_key=secret)
        >>> try:
        ...     payload = decode_refresh_token(access, secret_key=secret)
        ... except ValueError as e:
        ...     print(e)  # "Token invalide: type attendu 'refresh', reçu 'access'"
        >>>
        >>> # Cas d'usage typique: rotation de tokens
        >>> try:
        ...     payload = decode_refresh_token(refresh_from_client, secret_key=secret)
        ...     # Générer un nouveau access token
        ...     new_access = create_access_token({
        ...         "sub": payload["sub"],
        ...         "username": payload["username"],
        ...         "role": "admin",  # récupéré depuis la DB
        ...         "tenant_id": payload["tenant_id"]
        ...     }, secret_key=secret)
        ... except (jwt.InvalidTokenError, ValueError) as e:
        ...     print("Refresh invalide, reconnexion requise")

    Note:
        Cette fonction est spécifiquement conçue pour valider les refresh tokens
        dans un flow de rotation de tokens. Elle s'assure que seul un refresh token
        peut être utilisé pour obtenir un nouveau access token.
    """
    if not secret_key:
        raise ValueError("secret_key ne peut pas être None ou vide")

    if not token:
        raise ValueError("token ne peut pas être None ou vide")

    # Décoder le token
    payload = jwt.decode(token, secret_key, algorithms=[algorithm])

    # Vérifier que c'est bien un refresh token
    token_type = payload.get("type")
    if token_type != "refresh":
        raise ValueError(
            f"Token invalide: type attendu 'refresh', reçu '{token_type}'"
        )

    return payload


def is_token_expired(
    token: str,
    secret_key: str = None,
    algorithm: str = DEFAULT_ALGORITHM,
) -> bool:
    """Vérifie si un token JWT est expiré.

    Cette fonction décode le token sans vérifier l'expiration, puis compare
    le timestamp d'expiration avec l'heure actuelle. Elle retourne True si
    le token est expiré, False sinon.

    Args:
        token: Token JWT à vérifier (string).
        secret_key: Clé secrète utilisée pour signer le token.
        algorithm: Algorithme de signature (défaut: HS256).

    Returns:
        bool: True si le token est expiré, False sinon.

    Raises:
        ValueError: Si secret_key est None ou vide, ou si token est vide.
        jwt.InvalidTokenError: Si le token est invalide (signature incorrecte,
            format invalide, etc.).
        KeyError: Si le token ne contient pas de claim "exp".

    Examples:
        >>> from datetime import timedelta
        >>> secret = "ma-cle-secrete-super-longue-et-securisee-32-chars"
        >>>
        >>> # Token valide (expire dans 15 min)
        >>> claims = {"sub": "42", "username": "alice"}
        >>> token = create_access_token(claims, secret_key=secret)
        >>> print(is_token_expired(token, secret_key=secret))  # False
        >>>
        >>> # Token qui expire dans 1 seconde
        >>> short_token = create_access_token(
        ...     claims,
        ...     expires_delta=timedelta(seconds=1),
        ...     secret_key=secret
        ... )
        >>> print(is_token_expired(short_token, secret_key=secret))  # False
        >>>
        >>> # Attendre 2 secondes
        >>> import time
        >>> time.sleep(2)
        >>> print(is_token_expired(short_token, secret_key=secret))  # True
        >>>
        >>> # Cas d'usage: rafraîchissement proactif
        >>> if is_token_expired(token, secret_key=secret):
        ...     # Utiliser le refresh token pour obtenir un nouveau token
        ...     new_token = refresh_access_token(refresh_token)
        ... else:
        ...     # Continuer avec le token actuel
        ...     use_token(token)

    Note:
        Cette fonction est utile pour vérifier l'expiration sans lever d'exception,
        contrairement à decode_token() avec verify_exp=True. Cela permet de gérer
        le rafraîchissement de tokens de manière proactive.
    """
    if not secret_key:
        raise ValueError("secret_key ne peut pas être None ou vide")

    if not token:
        raise ValueError("token ne peut pas être None ou vide")

    # Décoder sans vérifier l'expiration
    payload = jwt.decode(
        token,
        secret_key,
        algorithms=[algorithm],
        options={"verify_exp": False}
    )

    # Vérifier manuellement l'expiration
    exp = payload.get("exp")
    if exp is None:
        raise KeyError("Le token ne contient pas de claim 'exp'")

    now = datetime.now(timezone.utc).timestamp()
    return now >= exp
