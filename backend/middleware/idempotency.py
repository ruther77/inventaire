"""
Middleware d'idempotence pour des retries sécurisés.

Implémente des clés d'idempotence pour les requêtes POST/PUT/PATCH afin
que les opérations ne soient pas exécutées deux fois en cas de retry.

Usage :
- Le client envoie l'en-tête : X-Idempotency-Key: <clé-unique>
- Le serveur stocke la réponse avec la clé dans Redis
- Les requêtes dupliquées renvoient la réponse en cache

Inspiré du pattern d'idempotence de Stripe.
"""
import json
import hashlib
from typing import Optional, Callable
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.cache import get_redis_client


# Nom de l'en-tête pour la clé d'idempotence
IDEMPOTENCY_KEY_HEADER = "X-Idempotency-Key"

# TTL par défaut pour les clés d'idempotence (24 heures)
IDEMPOTENCY_TTL = 86400

# Méthodes qui supportent l'idempotence
IDEMPOTENT_METHODS = {"POST", "PUT", "PATCH"}

# Chemins à exclure de l'idempotence (ex. auth, healthchecks)
EXCLUDED_PATHS = {
    "/health",
    "/auth/login",
    "/auth/refresh",
    "/docs",
    "/openapi.json",
}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling idempotency keys.

    Flow:
    1. Check if request method supports idempotency
    2. Check for X-Idempotency-Key header
    3. If key exists in Redis, return cached response
    4. Otherwise, process request and cache response
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Ignorer les méthodes non idempotentes
        if request.method not in IDEMPOTENT_METHODS:
            return await call_next(request)

        # Ignorer les chemins exclus
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # Récupérer la clé d'idempotence depuis l'en-tête
        idempotency_key = request.headers.get(IDEMPOTENCY_KEY_HEADER)

        # Sans clé d'idempotence, traiter normalement
        if not idempotency_key:
            return await call_next(request)

        # Construire la clé de cache complète avec isolation par tenant
        tenant_id = getattr(request.state, "tenant_id", None)
        cache_key = self._build_cache_key(
            idempotency_key,
            request.url.path,
            request.method,
            tenant_id
        )

        redis_client = get_redis_client()

        # Si Redis n'est pas disponible, traiter normalement
        if redis_client is None:
            return await call_next(request)

        try:
            # Vérifier si une réponse est déjà en cache
            cached = redis_client.get(cache_key)

            if cached:
                cached_data = json.loads(cached)

                # Vérifier si le traitement est encore en cours (évite les courses)
                if cached_data.get("status") == "processing":
                    return JSONResponse(
                        status_code=409,
                        content={
                            "error": "Request is currently being processed",
                            "idempotency_key": idempotency_key,
                        }
                    )

                # Retourner la réponse en cache
                return JSONResponse(
                    status_code=cached_data["status_code"],
                    content=cached_data["body"],
                    headers={
                        "X-Idempotency-Cached": "true",
                        "X-Idempotency-Key": idempotency_key,
                    }
                )

            # Marquer en cours de traitement pour éviter les courses
            redis_client.setex(
                cache_key,
                60,  # TTL court pour l'état de traitement
                json.dumps({
                    "status": "processing",
                    "started_at": datetime.utcnow().isoformat(),
                })
            )

            # Traiter la requête
            response = await call_next(request)

            # Mettre en cache les réponses réussies
            if 200 <= response.status_code < 500:
                # Lire le corps de la réponse
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                # Tenter de parser en JSON
                try:
                    body_json = json.loads(body.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    body_json = {"raw": body.decode("utf-8", errors="replace")}

                # Stocker dans le cache
                redis_client.setex(
                    cache_key,
                    IDEMPOTENCY_TTL,
                    json.dumps({
                        "status": "completed",
                        "status_code": response.status_code,
                        "body": body_json,
                        "completed_at": datetime.utcnow().isoformat(),
                    })
                )

                # Retourner une nouvelle réponse avec le corps parsé
                return JSONResponse(
                    status_code=response.status_code,
                    content=body_json,
                    headers={
                        "X-Idempotency-Key": idempotency_key,
                    }
                )

            # En cas d'erreur, supprimer le marqueur de traitement
            redis_client.delete(cache_key)
            return response

        except Exception as e:
            # En cas d'erreur, nettoyer et traiter normalement
            if redis_client:
                try:
                    redis_client.delete(cache_key)
                except Exception:
                    pass
            return await call_next(request)

    def _build_cache_key(
        self,
        idempotency_key: str,
        path: str,
        method: str,
        tenant_id: Optional[int]
    ) -> str:
        """Construit une clé de cache unique pour la requête idempotente."""
        key_parts = [
            "idempotency",
            method,
            path,
            idempotency_key,
        ]

        if tenant_id:
            key_parts.insert(1, f"tenant:{tenant_id}")

        # Hasher les chemins trop longs
        key = ":".join(key_parts)
        if len(key) > 200:
            hash_suffix = hashlib.md5(path.encode()).hexdigest()[:8]
            key_parts[2] = hash_suffix
            key = ":".join(key_parts)

        return key


class IdempotencyKeyGenerator:
    """Classe utilitaire pour générer des clés d'idempotence."""

    @staticmethod
    def generate(
        action: str,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        extra: Optional[str] = None,
    ) -> str:
        """
        Génère une clé d'idempotence déterministe.

        Args:
            action: L'action effectuée (ex. "create_invoice")
            entity_id: Identifiant d'entité optionnel
            user_id: Identifiant utilisateur optionnel
            extra: Données additionnelles pour l'unicité

        Returns:
            Une clé d'idempotence unique et déterministe
        """
        import uuid
        from datetime import datetime

        parts = [
            action,
            str(entity_id) if entity_id else "",
            str(user_id) if user_id else "",
            extra or "",
            datetime.utcnow().strftime("%Y%m%d%H"),  # Granularité à l'heure
        ]

        content = ":".join(filter(None, parts))
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    @staticmethod
    def random() -> str:
        """Génère une clé d'idempotence aléatoire (pour les opérations non déterministes)."""
        import uuid
        return str(uuid.uuid4())


# Dépendance pour les routes FastAPI
def require_idempotency_key(request: Request) -> str:
    """
    Dépendance FastAPI imposant une clé d'idempotence pour les opérations critiques.

    Usage:
        @router.post("/invoices")
        async def create_invoice(
            idempotency_key: str = Depends(require_idempotency_key),
            ...
        ):
    """
    key = request.headers.get(IDEMPOTENCY_KEY_HEADER)
    if not key:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Missing required header",
                "header": IDEMPOTENCY_KEY_HEADER,
                "message": "This endpoint requires an idempotency key for safe retries",
            }
        )
    return key


# Helper pour vérifier si la requête possède une clé d'idempotence
def has_idempotency_key(request: Request) -> bool:
    """Vérifie si la requête possède une clé d'idempotence."""
    return IDEMPOTENCY_KEY_HEADER in request.headers


# Obtenir le statut d'une clé d'idempotence
async def get_idempotency_status(idempotency_key: str, tenant_id: Optional[int] = None) -> dict:
    """Récupère le statut d'une clé d'idempotence."""
    redis_client = get_redis_client()
    if redis_client is None:
        return {"status": "unknown", "reason": "Redis not available"}

    # Il faut rechercher la clé, le chemin exact n'étant pas connu
    pattern = f"idempotency:*:{idempotency_key}"
    if tenant_id:
        pattern = f"idempotency:tenant:{tenant_id}:*:{idempotency_key}"

    keys = list(redis_client.scan_iter(match=pattern, count=100))

    if not keys:
        return {"status": "not_found", "idempotency_key": idempotency_key}

    for key in keys:
        data = redis_client.get(key)
        if data:
            cached = json.loads(data)
            return {
                "status": cached.get("status", "unknown"),
                "idempotency_key": idempotency_key,
                "completed_at": cached.get("completed_at"),
            }

    return {"status": "not_found", "idempotency_key": idempotency_key}
