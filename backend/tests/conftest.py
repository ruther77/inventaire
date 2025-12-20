"""Fixtures pytest partagées pour les tests backend."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ajouter la racine du projet au path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def client() -> TestClient:
    """Crée une instance TestClient pour l'app FastAPI."""
    from backend.main import app

    return TestClient(app)


@pytest.fixture
def mock_tenant():
    """Tenant fictif pour les tests."""
    from backend.dependencies.tenant import Tenant

    return Tenant(id=1, code="test", name="Test Tenant")


@pytest.fixture
def mock_user():
    """Utilisateur fictif pour les tests."""
    from backend.dependencies.security import AuthenticatedUser

    return AuthenticatedUser(
        id=1,
        username="test_user",
        role="admin",
        tenant_id=1,
    )


@pytest.fixture
def authenticated_client(client, mock_tenant, mock_user):
    """Client avec authentification simulée."""
    from backend.main import app
    from backend.dependencies.tenant import get_current_tenant
    from backend.dependencies.security import get_current_user

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_tenant] = lambda: mock_tenant
    yield client
    app.dependency_overrides.clear()
