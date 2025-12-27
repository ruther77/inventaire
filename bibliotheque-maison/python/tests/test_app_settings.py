"""Tests pour config.app_settings."""

from __future__ import annotations

from config.app_settings import AppSettings, bool_env


def test_bool_env_default(monkeypatch):
    monkeypatch.delenv("FLAG", raising=False)
    assert bool_env("FLAG", default=True) is True


def test_bool_env_parsing(monkeypatch):
    monkeypatch.setenv("FLAG", "true")
    assert bool_env("FLAG") is True
    monkeypatch.setenv("FLAG", "0")
    assert bool_env("FLAG") is False


def test_app_settings_load(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://a.com, https://b.com")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")
    settings = AppSettings.load()
    assert settings.cors_allowed_origins == ["https://a.com", "https://b.com"]
    assert settings.jwt_secret_keys == ["secret"]
