"""
Couche de cache Redis pour optimiser les performances de l'API

Fonctionnalités :
- Mise en cache automatique avec TTL
- Invalidation de cache par motifs
- Mise en cache tenant-aware
- Décorateur de cache pour une intégration facile
"""
import os
import json
import hashlib
import functools
from typing import Optional, Callable, Any
from datetime import timedelta

import redis
from fastapi import Request

# Pool de connexions Redis (singleton)
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Obtient ou crée un client Redis avec pool de connexions."""
    global _redis_pool, _redis_client

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    if _redis_client is None:
        try:
            _redis_pool = redis.ConnectionPool.from_url(
                redis_url,
                max_connections=20,
                decode_responses=True,
            )
            _redis_client = redis.Redis(connection_pool=_redis_pool)
            # Tester la connexion
            _redis_client.ping()
        except redis.ConnectionError:
            print("Warning: Redis not available, caching disabled")
            return None

    return _redis_client


def cache_key(*args, tenant_id: Optional[int] = None, prefix: str = "cache") -> str:
    """Génère une clé de cache cohérente à partir des arguments."""
    key_data = json.dumps(args, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]

    if tenant_id:
        return f"{prefix}:tenant:{tenant_id}:{key_hash}"
    return f"{prefix}:{key_hash}"


def cached(
    ttl: int = 300,  # 5 minutes default
    prefix: str = "api",
    tenant_aware: bool = True,
):
    """
    Décorateur pour mettre en cache les résultats d'une fonction dans Redis.

    Args:
        ttl: Durée de vie en secondes
        prefix: Préfixe de la clé de cache
        tenant_aware: Inclure le tenant_id dans la clé de cache

    Usage:
        @cached(ttl=60, prefix="dashboard")
        async def get_dashboard_data(tenant_id: int):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            client = get_redis_client()
            if client is None:
                # Redis non disponible, exécuter la fonction directement
                return await func(*args, **kwargs)

            # Construire la clé de cache
            tenant_id = kwargs.get("tenant_id") if tenant_aware else None
            key = cache_key(
                func.__name__,
                args,
                {k: v for k, v in kwargs.items() if k != "db"},
                tenant_id=tenant_id,
                prefix=prefix,
            )

            try:
                # Tenter de récupérer depuis le cache
                cached_data = client.get(key)
                if cached_data:
                    return json.loads(cached_data)

                # Exécuter la fonction et mettre en cache le résultat
                result = await func(*args, **kwargs)

                # Ne mettre en cache que les résultats sérialisables
                try:
                    client.setex(key, ttl, json.dumps(result, default=str))
                except (TypeError, ValueError):
                    pass  # Résultat non sérialisable, pas de cache

                return result

            except redis.RedisError:
                # Erreur Redis, exécuter la fonction directement
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
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

            except redis.RedisError:
                return func(*args, **kwargs)

        # Retourner le wrapper approprié selon le type de fonction
        if asyncio_available(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def asyncio_available(func: Callable) -> bool:
    """Vérifie si la fonction est asynchrone."""
    import asyncio
    return asyncio.iscoroutinefunction(func)


class CacheManager:
    """
    Gestionnaire de cache pour les opérations manuelles.

    Usage :
        cache = CacheManager()
        cache.set("my_key", {"data": "value"}, ttl=300)
        data = cache.get("my_key")
        cache.delete("my_key")
        cache.invalidate_pattern("dashboard:*")
    """

    def __init__(self, prefix: str = "app"):
        self.prefix = prefix
        self._client = get_redis_client()

    @property
    def client(self) -> Optional[redis.Redis]:
        if self._client is None:
            self._client = get_redis_client()
        return self._client

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur depuis le cache."""
        if self.client is None:
            return None
        try:
            data = self.client.get(self._key(key))
            return json.loads(data) if data else None
        except (redis.RedisError, json.JSONDecodeError):
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Enregistre une valeur dans le cache avec TTL."""
        if self.client is None:
            return False
        try:
            return self.client.setex(
                self._key(key),
                ttl,
                json.dumps(value, default=str)
            )
        except (redis.RedisError, TypeError, ValueError):
            return False

    def delete(self, key: str) -> bool:
        """Supprime une clé du cache."""
        if self.client is None:
            return False
        try:
            return bool(self.client.delete(self._key(key)))
        except redis.RedisError:
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalide toutes les clés correspondant au motif.

        Attention : utilise SCAN pour rester sûr en production, mais cela reste coûteux.
        À utiliser avec parcimonie.
        """
        if self.client is None:
            return 0

        try:
            count = 0
            full_pattern = self._key(pattern)
            cursor = 0

            while True:
                cursor, keys = self.client.scan(
                    cursor=cursor,
                    match=full_pattern,
                    count=100
                )
                if keys:
                    count += self.client.delete(*keys)
                if cursor == 0:
                    break

            return count
        except redis.RedisError:
            return 0

    def invalidate_tenant(self, tenant_id: int) -> int:
        """Invalide tout le cache pour un tenant donné."""
        return self.invalidate_pattern(f"*:tenant:{tenant_id}:*")


# Instances de cache préconfigurées pour les cas courants
dashboard_cache = CacheManager(prefix="dashboard")
catalog_cache = CacheManager(prefix="catalog")
finance_cache = CacheManager(prefix="finance")
restaurant_cache = CacheManager(prefix="restaurant")


# Constantes de TTL de cache (en secondes)
class CacheTTL:
    VERY_SHORT = 30      # 30 secondes - données temps réel
    SHORT = 60           # 1 minute - changements fréquents
    MEDIUM = 300         # 5 minutes - cache standard
    LONG = 900           # 15 minutes - données qui évoluent lentement
    VERY_LONG = 3600     # 1 heure - données statiques
    DAY = 86400          # 24 heures - changements rares


# Fonctions utilitaires pour des schémas fréquents
def invalidate_on_mutation(cache_prefixes: list[str], tenant_id: Optional[int] = None):
    """
    Décorateur pour invalider le cache après une mutation.

    Usage:
        @invalidate_on_mutation(["catalog", "dashboard"])
        async def create_product(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Invalider les caches concernés
            tid = tenant_id or kwargs.get("tenant_id")
            for prefix in cache_prefixes:
                manager = CacheManager(prefix=prefix)
                if tid:
                    manager.invalidate_tenant(tid)
                else:
                    manager.invalidate_pattern("*")

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            tid = tenant_id or kwargs.get("tenant_id")
            for prefix in cache_prefixes:
                manager = CacheManager(prefix=prefix)
                if tid:
                    manager.invalidate_tenant(tid)
                else:
                    manager.invalidate_pattern("*")

            return result

        if asyncio_available(func):
            return async_wrapper
        return sync_wrapper

    return decorator
