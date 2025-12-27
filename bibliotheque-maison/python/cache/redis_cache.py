"""Helpers de cache Redis.

Helpers indépendants pour Redis avec décorateurs sync/async.
Basés sur /home/ruuuzer/Documents/monprojet/backend/cache.py.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
from typing import Any, Callable, Optional

try:
    import redis
except ImportError:  # pragma: no cover - optional dependency
    redis = None  # type: ignore[assignment]

if redis is not None:
    RedisError = redis.RedisError
    RedisConnectionError = redis.ConnectionError
else:
    class RedisError(Exception):
        """Erreur Redis de repli quand redis n'est pas installé."""

    class RedisConnectionError(Exception):
        """Erreur de connexion Redis de repli quand redis n'est pas installé."""


_redis_pool: Optional["redis.ConnectionPool"] = None
_redis_client: Optional["redis.Redis"] = None


def get_redis_client(
    redis_url: Optional[str] = None,
    *,
    max_connections: int = 20,
    decode_responses: bool = True,
) -> Optional["redis.Redis"]:
    """Retourne un client Redis ou None si indisponible."""
    if redis is None:
        return None

    global _redis_pool, _redis_client

    if _redis_client is not None:
        return _redis_client

    url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")

    try:
        _redis_pool = redis.ConnectionPool.from_url(
            url,
            max_connections=max_connections,
            decode_responses=decode_responses,
        )
        _redis_client = redis.Redis(connection_pool=_redis_pool)
        _redis_client.ping()
    except RedisConnectionError:
        return None

    return _redis_client


def cache_key(*args: Any, tenant_id: Optional[int] = None, prefix: str = "cache") -> str:
    """Génère une clé de cache stable à partir des arguments."""
    payload = json.dumps(args, sort_keys=True, default=str)
    key_hash = hashlib.md5(payload.encode("utf-8")).hexdigest()[:12]

    if tenant_id is not None:
        return f"{prefix}:tenant:{tenant_id}:{key_hash}"
    return f"{prefix}:{key_hash}"


def asyncio_available(func: Callable) -> bool:
    """Retourne True si la fonction est asynchrone."""
    import asyncio

    return asyncio.iscoroutinefunction(func)


def cached(
    ttl: int = 300,
    prefix: str = "api",
    tenant_aware: bool = True,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Met en cache le résultat d'une fonction dans Redis si disponible."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            client = get_redis_client()
            if client is None:
                return await func(*args, **kwargs)

            tenant_id = kwargs.get("tenant_id") if tenant_aware else None
            key = cache_key(
                func.__name__,
                args,
                {k: v for k, v in kwargs.items() if k != "db"},
                tenant_id=tenant_id,
                prefix=prefix,
            )

            try:
                cached_data = client.get(key)
                if cached_data:
                    return json.loads(cached_data)

                result = await func(*args, **kwargs)
                try:
                    client.setex(key, ttl, json.dumps(result, default=str))
                except (TypeError, ValueError):
                    pass

                return result
            except RedisError:
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            client = get_redis_client()
            if client is None:
                return func(*args, **kwargs)

            tenant_id = kwargs.get("tenant_id") if tenant_aware else None
            key = cache_key(
                func.__name__,
                args,
                {k: v for k, v in kwargs.items() if k != "db"},
                tenant_id=tenant_id,
                prefix=prefix,
            )

            try:
                cached_data = client.get(key)
                if cached_data:
                    return json.loads(cached_data)

                result = func(*args, **kwargs)
                try:
                    client.setex(key, ttl, json.dumps(result, default=str))
                except (TypeError, ValueError):
                    pass

                return result
            except RedisError:
                return func(*args, **kwargs)

        if asyncio_available(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class CacheManager:
    """Gestionnaire de cache simple pour opérations Redis manuelles."""

    def __init__(self, prefix: str = "app") -> None:
        self.prefix = prefix
        self._client = get_redis_client()

    @property
    def client(self) -> Optional["redis.Redis"]:
        if self._client is None:
            self._client = get_redis_client()
        return self._client

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur depuis Redis."""
        if self.client is None:
            return None
        try:
            data = self.client.get(self._key(key))
            return json.loads(data) if data else None
        except (RedisError, json.JSONDecodeError):
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Stocke une valeur sérialisable en JSON avec TTL."""
        if self.client is None:
            return False
        try:
            return bool(self.client.setex(self._key(key), ttl, json.dumps(value, default=str)))
        except (RedisError, TypeError, ValueError):
            return False

    def delete(self, key: str) -> bool:
        """Supprime une entrée de cache."""
        if self.client is None:
            return False
        try:
            return bool(self.client.delete(self._key(key)))
        except RedisError:
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Supprime toutes les clés correspondant à un motif via SCAN."""
        if self.client is None:
            return 0

        try:
            count = 0
            cursor = 0
            full_pattern = self._key(pattern)

            while True:
                cursor, keys = self.client.scan(cursor=cursor, match=full_pattern, count=100)
                if keys:
                    count += self.client.delete(*keys)
                if cursor == 0:
                    break

            return count
        except RedisError:
            return 0

    def invalidate_tenant(self, tenant_id: int) -> int:
        """Invalide les entrées de cache pour un tenant donné."""
        return self.invalidate_pattern(f"*:tenant:{tenant_id}:*")


class CacheTTL:
    """Constantes de TTL courantes (en secondes)."""

    VERY_SHORT = 30
    SHORT = 60
    MEDIUM = 300
    LONG = 900
    VERY_LONG = 3600
    DAY = 86400


def invalidate_on_mutation(
    cache_prefixes: list[str],
    tenant_id: Optional[int] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Invalide des préfixes de cache après une mutation."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)

            tid = tenant_id or kwargs.get("tenant_id")
            for prefix in cache_prefixes:
                manager = CacheManager(prefix=prefix)
                if tid is not None:
                    manager.invalidate_tenant(int(tid))
                else:
                    manager.invalidate_pattern("*")

            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            tid = tenant_id or kwargs.get("tenant_id")
            for prefix in cache_prefixes:
                manager = CacheManager(prefix=prefix)
                if tid is not None:
                    manager.invalidate_tenant(int(tid))
                else:
                    manager.invalidate_pattern("*")

            return result

        if asyncio_available(func):
            return async_wrapper
        return sync_wrapper

    return decorator


__all__ = [
    "CacheManager",
    "CacheTTL",
    "cache_key",
    "cached",
    "get_redis_client",
    "invalidate_on_mutation",
]
