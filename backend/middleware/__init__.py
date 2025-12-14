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

__all__ = [
    # Rate limiter
    "RateLimiter",
    "RateLimitConfig",
    "rate_limit",
    "get_rate_limiter",
    # Request context
    "RequestContextMiddleware",
    "get_request_id",
    "get_request_context",
    "set_context_value",
    "get_elapsed_ms",
    # Response wrapper
    "ResponseWrapperMiddleware",
    "ErrorCodes",
    "build_success_response",
    "build_error_response",
    # Performance
    "PerformanceMiddleware",
    "CircuitBreaker",
    "get_performance_stats",
    "create_performance_middleware",
]
