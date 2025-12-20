"""
Backend middleware package - Middleware avancés pour l'API.
"""

from .rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    rate_limit,
    get_rate_limiter,
)
from .request_context import (
    RequestContextMiddleware,
    get_request_id,
    get_request_context,
    set_context_value,
    get_elapsed_ms,
)
from .response_wrapper import (
    ResponseWrapperMiddleware,
    ErrorCodes,
    build_success_response,
    build_error_response,
)
from .performance import (
    PerformanceMiddleware,
    CircuitBreaker,
    get_performance_stats,
    create_performance_middleware,
)
from .idempotency import (
    IdempotencyMiddleware,
    IdempotencyKeyGenerator,
    require_idempotency_key,
    has_idempotency_key,
    get_idempotency_status,
    IDEMPOTENCY_KEY_HEADER,
)

__all__ = [
    # Limiteur de débit
    "RateLimiter",
    "RateLimitConfig",
    "rate_limit",
    "get_rate_limiter",
    # Contexte requête
    "RequestContextMiddleware",
    "get_request_id",
    "get_request_context",
    "set_context_value",
    "get_elapsed_ms",
    # Wrapper de réponse
    "ResponseWrapperMiddleware",
    "ErrorCodes",
    "build_success_response",
    "build_error_response",
    # Performance
    "PerformanceMiddleware",
    "CircuitBreaker",
    "get_performance_stats",
    "create_performance_middleware",
    # Idempotency
    "IdempotencyMiddleware",
    "IdempotencyKeyGenerator",
    "require_idempotency_key",
    "has_idempotency_key",
    "get_idempotency_status",
    "IDEMPOTENCY_KEY_HEADER",
]
