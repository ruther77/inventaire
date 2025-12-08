"""
Rate Limiter Middleware - Token bucket algorithm with sliding window.

Provides configurable rate limiting for API endpoints using in-memory
or Redis-backed storage.

Usage:
    @router.get("/api/data")
    @rate_limit(requests=100, window=60)  # 100 requests per minute
    async def get_data(request: Request):
        ...
"""

from __future__ import annotations

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
    """Configuration for rate limiting."""

    requests: int = 100  # Maximum requests
    window: int = 60  # Time window in seconds
    burst: int = 10  # Burst allowance above limit
    key_prefix: str = "rl"  # Prefix for rate limit keys

    @property
    def key(self) -> str:
        return f"{self.key_prefix}:{self.requests}:{self.window}"


@dataclass
class RateLimitEntry:
    """Tracks rate limit state for a single client."""

    tokens: float
    last_update: float
    request_count: int = 0


class RateLimiter:
    """
    In-memory rate limiter using token bucket algorithm.

    For production with multiple workers, consider using Redis.
    """

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._buckets: dict[str, RateLimitEntry] = defaultdict(
            lambda: RateLimitEntry(
                tokens=float(self.config.requests + self.config.burst),
                last_update=time.time(),
            )
        )
        self._cleanup_interval = 300  # Clean up every 5 minutes
        self._last_cleanup = time.time()

    def _get_client_key(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Priority: X-Forwarded-For > X-Real-IP > client host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.headers.get("X-Real-IP") or (
                request.client.host if request.client else "unknown"
            )

        # Include path for per-endpoint limiting
        path = request.url.path
        return f"{self.config.key}:{client_ip}:{path}"

    def _refill_tokens(self, entry: RateLimitEntry, now: float) -> None:
        """Refill tokens based on time elapsed."""
        elapsed = now - entry.last_update
        # Refill rate: requests per window
        refill_rate = self.config.requests / self.config.window
        new_tokens = elapsed * refill_rate
        entry.tokens = min(
            self.config.requests + self.config.burst,
            entry.tokens + new_tokens,
        )
        entry.last_update = now

    def _cleanup_expired(self, now: float) -> None:
        """Remove expired entries to prevent memory bloat."""
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

        # Refill tokens
        self._refill_tokens(entry, now)

        # Periodic cleanup
        self._cleanup_expired(now)

        # Check if request is allowed
        is_allowed = entry.tokens >= 1.0
        if is_allowed:
            entry.tokens -= 1.0
            entry.request_count += 1

        # Calculate remaining and reset time
        remaining = max(0, int(entry.tokens))
        reset_time = int(now + self.config.window)

        headers = {
            "X-RateLimit-Limit": str(self.config.requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

        if not is_allowed:
            # Calculate retry-after
            tokens_needed = 1.0 - entry.tokens
            refill_rate = self.config.requests / self.config.window
            retry_after = int(tokens_needed / refill_rate) + 1
            headers["Retry-After"] = str(retry_after)

        return is_allowed, headers


# Global rate limiter instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter(config: RateLimitConfig | None = None) -> RateLimiter:
    """Get or create global rate limiter instance."""
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

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find Request in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                request = kwargs.get("request")

            if request is None:
                # Can't rate limit without request, proceed
                return await func(*args, **kwargs)

            is_allowed, headers = await limiter.check(request)

            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please retry later.",
                    headers=headers,
                )

            response = await func(*args, **kwargs)

            # Note: Headers would need to be added via middleware for full support
            return response

        return wrapper

    return decorator


class RateLimitMiddleware:
    """
    ASGI middleware for global rate limiting.

    Usage in main.py:
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

        # Skip excluded paths
        if any(path.startswith(p) for p in self.exclude_paths):
            await self.app(scope, receive, send)
            return

        # Create fake request for rate limiter
        from starlette.requests import Request

        request = Request(scope, receive)

        is_allowed, headers = await self.limiter.check(request)

        if not is_allowed:
            # Return 429 response
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
