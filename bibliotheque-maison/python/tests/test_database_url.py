"""Tests pour database.database_url."""

from __future__ import annotations

from database.database_url import get_database_url


def test_database_url_prefers_explicit(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@host:5432/db")
    assert get_database_url() == "postgresql://user:pass@host:5432/db"


def test_database_url_fallback(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss word")
    monkeypatch.setenv("POSTGRES_DB", "monprojet")
    monkeypatch.setenv("DB_HOST", "db.local")
    monkeypatch.setenv("DB_PORT", "5433")

    url = get_database_url()
    assert url == "postgresql+psycopg2://user:p%40ss+word@db.local:5433/monprojet"


def test_database_url_without_password(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("POSTGRES_USER", "user")
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.setenv("POSTGRES_DB", "db")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")

    url = get_database_url()
    assert url == "postgresql+psycopg2://user@localhost:5432/db"
