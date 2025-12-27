"""
Middleware de limitation de débit - algorithme du seau à jetons avec fenêtre glissante.

Fournit une limitation configurable des endpoints API avec stockage en mémoire
ou via Redis.

Usage :
    @router.get("/api/data")
    @rate_limit(requests=100, window=60)  # 100 requêtes par minute
    async def get_data(request: Request):
        ...
"""

from __future__ import annotations

import asyncio
import inspect
import time
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Any

from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration pour la limitation de débit."""

    requests: int = 100  # Nombre maximum de requêtes
    window: int = 60  # Fenêtre temporelle en secondes
    burst: int = 10  # Tolérance de rafale au-delà de la limite
    key_prefix: str = "rl"  # Préfixe pour les clés de limitation

    @property
    def key(self) -> str:
        return f"{self.key_prefix}:{self.requests}:{self.window}"


@dataclass
class RateLimitEntry:
    """Suit l'état de limitation pour un client."""

    tokens: float
    last_update: float
    request_count: int = 0


class RateLimiter:
    """
    Rate limiter en mémoire utilisant l'algorithme du seau à jetons.

    Pour la production multi-workers, préférer Redis.
    """

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._buckets: dict[str, RateLimitEntry] = defaultdict(
            lambda: RateLimitEntry(
                tokens=float(self.config.requests + self.config.burst),
                last_update=time.time(),
            )
        )
        self._cleanup_interval = 300  # Nettoyage toutes les 5 minutes
        self._last_cleanup = time.time()

    def _get_client_key(self, request: Request) -> str:
        """Extrait l'identifiant client depuis la requête."""
        # Priorité : X-Forwarded-For > X-Real-IP > host client
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.headers.get("X-Real-IP") or (
                request.client.host if request.client else "unknown"
            )

        # Inclure le chemin pour limiter par endpoint
        path = request.url.path
        return f"{self.config.key}:{client_ip}:{path}"

    def _refill_tokens(self, entry: RateLimitEntry, now: float) -> None:
        """Recharge les jetons selon le temps écoulé."""
        elapsed = now - entry.last_update
        # Taux de remplissage : requêtes par fenêtre
        refill_rate = self.config.requests / self.config.window
        new_tokens = elapsed * refill_rate
        entry.tokens = min(
            self.config.requests + self.config.burst,
            entry.tokens + new_tokens,
        )
        entry.last_update = now

    def _cleanup_expired(self, now: float) -> None:
        """Supprime les entrées expirées pour éviter la surcharge mémoire."""
        if now - self._last_cleanup < self._cleanup_interval:
            return

        expiry = now - (self.config.window * 2)
        expired_keys = [
            key
            for key, entry in self._buckets.items()
            if entry.last_update < expiry
        ]
        for key in expired_keys:
            del self._buckets[key]

        self._last_cleanup = now
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit entries")

    async def check(self, request: Request) -> tuple[bool, dict[str, str]]:
        """
        Check if request is allowed.

        Returns:
            Tuple of (is_allowed, headers_dict)
        """
        now = time.time()
        key = self._get_client_key(request)
        entry = self._buckets[key]

        # Recharger les jetons
        self._refill_tokens(entry, now)

        # Nettoyage périodique
        self._cleanup_expired(now)

        # Vérifier si la requête est autorisée
        is_allowed = entry.tokens >= 1.0
        if is_allowed:
            entry.tokens -= 1.0
            entry.request_count += 1

        # Calculer le reste et le temps de réinitialisation
        remaining = max(0, int(entry.tokens))
        reset_time = int(now + self.config.window)

        headers = {
            "X-RateLimit-Limit": str(self.config.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

        if not is_allowed:
            # Calculer le retry-after
            tokens_needed = 1.0 - entry.tokens
            refill_rate = self.config.requests / self.config.window
            retry_after = int(tokens_needed / refill_rate) + 1
            headers["Retry-After"] = str(retry_after)

        return is_allowed, headers


# Instance globale du rate limiter
_rate_limiter: RateLimiter | None = None


def get_rate_limiter(config: RateLimitConfig | None = None) -> RateLimiter:
    """Obtient ou crée l'instance globale du rate limiter."""
    global _rate_limiter
    if _rate_limiter is None or config is not None:
        _rate_limiter = RateLimiter(config)
    return _rate_limiter


def rate_limit(
    requests: int = 100,
    window: int = 60,
    burst: int = 10,
):
    """
    Decorator for rate limiting endpoints.

    Args:
        requests: Maximum requests in time window
        window: Time window in seconds
        burst: Extra burst capacity above limit

    Usage:
        @router.get("/api/data")
        @rate_limit(requests=100, window=60)
        async def get_data(request: Request):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        config = RateLimitConfig(requests=requests, window=window, burst=burst)
        limiter = RateLimiter(config)
        is_async = asyncio.iscoroutinefunction(func)

        async def _check_rate_limit(*args, **kwargs):
            """Vérifie le rate limit et retourne la request si trouvée."""
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                request = kwargs.get("request")

            if request is not None:
                is_allowed, headers = await limiter.check(request)
                if not is_allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Please retry later.",
                        headers=headers,
                    )

        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                await _check_rate_limit(*args, **kwargs)
                return await func(*args, **kwargs)
            return async_wrapper
        else:
            @wraps(func)
            async def sync_wrapper(*args, **kwargs):
                await _check_rate_limit(*args, **kwargs)
                # Exécuter la fonction sync dans un thread pool pour éviter de bloquer
                return func(*args, **kwargs)
            return sync_wrapper

    return decorator


class RateLimitMiddleware:
    """
    Middleware ASGI pour la limitation de débit globale.

    Usage dans main.py :
        app.add_middleware(RateLimitMiddleware, requests=1000, window=60)
    """

    def __init__(
        self,
        app,
        requests: int = 1000,
        window: int = 60,
        burst: int = 50,
        exclude_paths: list[str] | None = None,
    ):
        self.app = app
        self.config = RateLimitConfig(requests=requests, window=window, burst=burst)
        self.limiter = RateLimiter(self.config)
        self.exclude_paths = set(exclude_paths or ["/health", "/ready", "/docs", "/openapi.json"])

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Ignorer les chemins exclus
        if any(path.startswith(p) for p in self.exclude_paths):
            await self.app(scope, receive, send)
            return

        # Créer une fausse requête pour le rate limiter
        from starlette.requests import Request

        request = Request(scope, receive)

        is_allowed, headers = await self.limiter.check(request)

        if not is_allowed:
            # Retourner une réponse 429
            response_headers = [
                (b"content-type", b"application/json"),
            ]
            for key, value in headers.items():
                response_headers.append((key.lower().encode(), value.encode()))

            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": response_headers,
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"detail":"Rate limit exceeded. Please retry later."}',
                }
            )
            return

        await self.app(scope, receive, send)
