"""
Request Context Middleware - Traçabilité avancée des requêtes.

Fonctionnalités:
- Request ID unique pour chaque requête (corrélation logs)
- Contexte propagé via contextvars (thread-safe)
- Timing précis des requêtes
- Métriques de performance collectées
"""

from __future__ import annotations

import time
import uuid
import logging
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Context variables thread-safe
_request_id: ContextVar[str] = ContextVar("request_id", default="")
_request_start: ContextVar[float] = ContextVar("request_start", default=0.0)
_request_context: ContextVar[dict[str, Any]] = ContextVar("request_context", default={})


@dataclass
class RequestMetrics:
    """Métriques collectées pour chaque requête."""

    request_id: str
    method: str
    path: str
    status_code: int = 0
    duration_ms: float = 0.0
    user_id: Optional[int] = None
    tenant_id: Optional[int] = None
    error: Optional[str] = None
    db_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


def get_request_id() -> str:
    """Récupère l'ID de requête courant (utilisable partout)."""
    return _request_id.get()


def get_request_context() -> dict[str, Any]:
    """Récupère le contexte complet de la requête courante."""
    return _request_context.get()


def set_context_value(key: str, value: Any) -> None:
    """Ajoute une valeur au contexte de la requête courante."""
    ctx = _request_context.get().copy()
    ctx[key] = value
    _request_context.set(ctx)


def get_elapsed_ms() -> float:
    """Retourne le temps écoulé depuis le début de la requête."""
    start = _request_start.get()
    if start == 0.0:
        return 0.0
    return (time.perf_counter() - start) * 1000


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware de contexte de requête avancé.

    Ajoute:
    - X-Request-ID header (génère si absent)
    - X-Response-Time header
    - Logging structuré
    - Métriques de performance
    """

    def __init__(
        self,
        app,
        *,
        header_name: str = "X-Request-ID",
        log_requests: bool = True,
        slow_request_threshold_ms: float = 1000.0,
        metrics_callback: Optional[Callable[[RequestMetrics], None]] = None,
    ):
        super().__init__(app)
        self.header_name = header_name
        self.log_requests = log_requests
        self.slow_threshold = slow_request_threshold_ms
        self.metrics_callback = metrics_callback

    async def dispatch(self, request: Request, call_next) -> Response:
        # Générer ou récupérer le request ID
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())[:8]
        start_time = time.perf_counter()

        # Initialiser le contexte
        _request_id.set(request_id)
        _request_start.set(start_time)
        _request_context.set({
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
        })

        # Exécuter la requête
        response: Response
        error_msg: Optional[str] = None

        try:
            response = await call_next(request)
        except Exception as exc:
            error_msg = str(exc)
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Construire les métriques
            metrics = RequestMetrics(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=getattr(response, "status_code", 500) if "response" in dir() else 500,
                duration_ms=duration_ms,
                error=error_msg,
                extra=_request_context.get(),
            )

            # Logging structuré
            if self.log_requests:
                self._log_request(metrics)

            # Callback métriques
            if self.metrics_callback:
                try:
                    self.metrics_callback(metrics)
                except Exception:
                    pass

        # Ajouter headers de réponse
        response.headers[self.header_name] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extrait l'IP client en tenant compte des proxies."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _log_request(self, metrics: RequestMetrics) -> None:
        """Log structuré de la requête."""
        level = logging.INFO

        if metrics.error:
            level = logging.ERROR
        elif metrics.status_code >= 500:
            level = logging.ERROR
        elif metrics.status_code >= 400:
            level = logging.WARNING
        elif metrics.duration_ms > self.slow_threshold:
            level = logging.WARNING

        log_data = {
            "request_id": metrics.request_id,
            "method": metrics.method,
            "path": metrics.path,
            "status": metrics.status_code,
            "duration_ms": round(metrics.duration_ms, 2),
        }

        if metrics.error:
            log_data["error"] = metrics.error

        if metrics.duration_ms > self.slow_threshold:
            log_data["slow"] = True

        logger.log(
            level,
            f"[{metrics.request_id}] {metrics.method} {metrics.path} "
            f"→ {metrics.status_code} ({metrics.duration_ms:.0f}ms)",
            extra=log_data,
        )
