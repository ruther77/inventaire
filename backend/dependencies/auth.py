from __future__ import annotations

import os

from fastapi import Depends, Header, HTTPException, status


def _load_api_key() -> str | None:
    key = os.getenv("ADMIN_API_KEY")
    return key.strip() if key else None


def require_api_key(x_api_key: str | None = Header(default=None)) -> str | None:
    """
    Valide l'en-tête `X-API-KEY` si une clé est configurée.

    Lorsqu'aucune clé n'est définie, l'accès est ouvert pour simplifier le dev local.
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
    """Déclenche la vérification mais ne retourne rien."""

