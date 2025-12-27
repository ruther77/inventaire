"""Tests pour cache.redis_cache."""

from __future__ import annotations

from cache import redis_cache


def test_cache_key_tenant_prefix():
    key = redis_cache.cache_key("fn", (1, 2), {"a": 1}, tenant_id=3, prefix="test")
    assert key.startswith("test:tenant:3:")


def test_cached_fallback_when_no_redis(monkeypatch):
    monkeypatch.setattr(redis_cache, "get_redis_client", lambda *args, **kwargs: None)

    calls = {"count": 0}

    @redis_cache.cached(ttl=1, prefix="demo")
    def compute(value):
        calls["count"] += 1
        return value * 2

    assert compute(3) == 6
    assert calls["count"] == 1
