"""Shared pytest fixtures for backend tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def client() -> TestClient:
    """Create a TestClient instance for the FastAPI app."""
    from backend.main import app

    return TestClient(app)


@pytest.fixture
def mock_tenant():
    """Mock tenant for testing."""
    from backend.dependencies.tenant import Tenant

    return Tenant(id=1, code="test", name="Test Tenant")


@pytest.fixture
def mock_user():
    """Mock user for testing."""
    from backend.dependencies.security import AuthenticatedUser

    return AuthenticatedUser(
        id=1,
        username="test_user",
        role="admin",
        tenant_id=1,
    )


@pytest.fixture
def authenticated_client(client, mock_tenant, mock_user):
    """Client with mocked authentication."""
    from backend.main import app
    from backend.dependencies.tenant import get_current_tenant
    from backend.dependencies.security import get_current_user

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_tenant] = lambda: mock_tenant
    yield client
    app.dependency_overrides.clear()
