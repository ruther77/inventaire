"""
Module d'authentification par clé API.

Ce module fournit une authentification alternative par clé API pour les
endpoints administratifs ou les intégrations externes. Complète le système
JWT/OAuth2 pour des cas d'usage spécifiques.

Configuration:
- Variable d'environnement: ADMIN_API_KEY
- Si non configurée, l'accès est ouvert (mode développement)
- En production, toujours configurer une clé robuste

Usage:
- Header HTTP: X-API-Key: <votre-clé>
- Utilisé principalement pour les webhooks et scripts automation
"""

from __future__ import annotations

import os

from fastapi import Depends, Header, HTTPException, status


def _load_api_key() -> str | None:
    """
    Charge la clé API depuis les variables d'environnement.

    Returns:
        Clé API si configurée, None sinon
    """
    key = os.getenv("ADMIN_API_KEY")
    return key.strip() if key else None


def require_api_key(x_api_key: str | None = Header(default=None)) -> str | None:
    """
    Dépendance FastAPI pour valider la clé API.

    Valide l'en-tête `X-API-KEY` contre la clé configurée.
    En mode développement (pas de clé configurée), autorise tous les accès.

    Args:
        x_api_key: Valeur de l'en-tête X-API-Key (injecté par FastAPI)

    Returns:
        La clé validée ou None si pas de validation requise

    Raises:
        HTTPException 401: Si la clé est invalide ou manquante

    Example:
        >>> @router.get("/webhook", dependencies=[Depends(require_api_key)])
        >>> def webhook_endpoint():
        ...     return {"status": "received"}
    """
    secret = _load_api_key()
    if secret is None:
        return None

    if x_api_key is None or x_api_key != secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide",
            headers={"WWW-Authenticate": "Api-Key"},
        )
    return x_api_key


def optional_api_key(api_key: str | None = Depends(require_api_key)) -> None:
    """
    Déclenche la vérification de clé API sans retourner de valeur.

    Utile pour les routes qui nécessitent juste la validation sans
    utiliser la clé dans la logique métier.

    Args:
        api_key: Clé validée (injecté automatiquement)
    """

