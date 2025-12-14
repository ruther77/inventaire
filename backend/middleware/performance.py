"""
Performance Middleware - Monitoring et optimisation avancée.

Fonctionnalités:
- Détection des requêtes lentes
- Métriques agrégées par endpoint
- Circuit breaker pour services externes
- Cache-Control automatique
"""

from __future__ import annotations

import time
import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Normal
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class EndpointStats:
    """Statistiques par endpoint."""

    path: str
    total_requests: int = 0
    total_errors: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    slow_requests: int = 0

    @property
    def avg_duration_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_duration_ms / self.total_requests

    @property
    def error_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_errors / self.total_requests

    def record(self, duration_ms: float, is_error: bool, slow_threshold: float) -> None:
        self.total_requests += 1
        self.total_duration_ms += duration_ms
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)

        if is_error:
            self.total_errors += 1

        if duration_ms > slow_threshold:
            self.slow_requests += 1


class CircuitBreaker:
    """
    Circuit Breaker pattern pour protéger contre les cascades d'erreurs.

    États:
    - CLOSED: Normal, requêtes passent
    - OPEN: Trop d'erreurs, requêtes rejetées
    - HALF_OPEN: Test de récupération
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time > self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
            return self._state

    def can_execute(self) -> bool:
        return self.state != CircuitState.OPEN

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    logger.info("Circuit breaker closed - service recovered")

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning("Circuit breaker re-opened - recovery failed")
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker opened after {self._failure_count} failures"
                )


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware de performance avancé.

    - Collecte des métriques par endpoint
    - Alertes sur requêtes lentes
    - Headers de performance (Server-Timing)
    - Cache-Control intelligent
    """

    # Cache policies par pattern de path
    CACHE_POLICIES = {
        "/products": ("public", 60),          # 1 minute
        "/catalog/categories": ("public", 300),  # 5 minutes
        "/dashboard/metrics": ("private", 30),   # 30 secondes
        "/prices/history": ("private", 120),     # 2 minutes
    }

    def __init__(
        self,
        app,
        *,
        slow_threshold_ms: float = 500.0,
        enable_server_timing: bool = True,
        enable_cache_control: bool = True,
        stats_callback: Optional[Callable[[dict[str, EndpointStats]], None]] = None,
    ):
        super().__init__(app)
        self.slow_threshold = slow_threshold_ms
        self.enable_server_timing = enable_server_timing
        self.enable_cache_control = enable_cache_control
        self.stats_callback = stats_callback

        self._stats: dict[str, EndpointStats] = defaultdict(
            lambda: EndpointStats(path="unknown")
        )
        self._lock = Lock()

    def get_stats(self) -> dict[str, EndpointStats]:
        """Retourne les statistiques actuelles."""
        with self._lock:
            return dict(self._stats)

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        path = self._normalize_path(request.url.path)

        response: Response
        is_error = False

        try:
            response = await call_next(request)
            is_error = response.status_code >= 500
        except Exception:
            is_error = True
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000

            # Enregistrer les stats
            with self._lock:
                if path not in self._stats:
                    self._stats[path] = EndpointStats(path=path)
                self._stats[path].record(duration_ms, is_error, self.slow_threshold)

            # Log requête lente
            if duration_ms > self.slow_threshold:
                logger.warning(
                    f"Slow request: {request.method} {path} took {duration_ms:.0f}ms"
                )

        # Headers de performance
        if self.enable_server_timing:
            response.headers["Server-Timing"] = f"total;dur={duration_ms:.2f}"

        # Cache-Control pour GET
        if (
            self.enable_cache_control
            and request.method == "GET"
            and 200 <= response.status_code < 300
        ):
            self._apply_cache_control(response, path)

        return response

    def _normalize_path(self, path: str) -> str:
        """Normalise le path pour le groupement (remplace IDs par :id)."""
        parts = path.strip("/").split("/")
        normalized = []

        for part in parts:
            if part.isdigit():
                normalized.append(":id")
            elif len(part) == 36 and "-" in part:  # UUID
                normalized.append(":uuid")
            else:
                normalized.append(part)

        return "/" + "/".join(normalized)

    def _apply_cache_control(self, response: Response, path: str) -> None:
        """Applique le Cache-Control approprié."""
        for pattern, (visibility, max_age) in self.CACHE_POLICIES.items():
            if path.startswith(pattern):
                response.headers["Cache-Control"] = f"{visibility}, max-age={max_age}"
                return

        # Par défaut: pas de cache
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"


# Instance globale pour accès aux stats
_global_stats: Optional[PerformanceMiddleware] = None


def get_performance_stats() -> dict[str, EndpointStats]:
    """Récupère les statistiques de performance globales."""
    if _global_stats is None:
        return {}
    return _global_stats.get_stats()


def create_performance_middleware(app, **kwargs) -> PerformanceMiddleware:
    """Factory pour créer le middleware avec instance globale."""
    global _global_stats
    middleware = PerformanceMiddleware(app, **kwargs)
    _global_stats = middleware
    return middleware
