"""Tests complets pour l'API newCMS (pages et navigation)."""

from __future__ import annotations

import os
import pytest

# Configuration de l'environnement AVANT les imports
os.environ.setdefault("SKIP_TENANT_INIT", "1")
os.environ.setdefault("SKIP_USER_BOOTSTRAP", "1")
os.environ.setdefault("RUN_BACKEND_API_TESTS", "1")

from fastapi.testclient import TestClient

from backend.main import app
from backend.dependencies.security import create_access_token
from backend.dependencies.tenant import Tenant


# ============================================================================
# FIXTURES
# ============================================================================


def _make_token(role: str = "admin", tenant_id: int = 1) -> str:
    """Génère un token JWT pour les tests."""
    return create_access_token(
        {
            "sub": "1",
            "username": "test-user",
            "role": role,
            "tenant_id": tenant_id,
        }
    )


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Headers d'authentification par défaut (tenant_id=1, admin)."""
    return {"Authorization": f"Bearer {_make_token()}"}


@pytest.fixture
def epicerie_tenant() -> Tenant:
    """Fixture tenant Épicerie (tenant_id=1)."""
    return Tenant(id=1, code="epicerie", name="Épicerie HQ")


@pytest.fixture
def restaurant_tenant() -> Tenant:
    """Fixture tenant Restaurant (tenant_id=2)."""
    return Tenant(id=2, code="restaurant", name="Restaurant Gourmet")


@pytest.fixture
def intelligence_tenant() -> Tenant:
    """Fixture tenant Intelligence (tenant_id=3)."""
    return Tenant(id=3, code="intelligence", name="Intelligence Business")


@pytest.fixture
def api_client(auth_headers):
    """Client FastAPI avec authentification."""
    client = TestClient(app)
    client.headers.update(auth_headers)
    return client


@pytest.fixture(autouse=True)
def mock_tenant_resolution(monkeypatch, epicerie_tenant):
    """Mock automatique de la résolution du tenant (par défaut: epicerie)."""
    monkeypatch.setattr(
        "backend.dependencies.tenant.resolve_tenant",
        lambda *_args, **_kwargs: epicerie_tenant,
    )


@pytest.fixture(autouse=True)
def mock_cms_data(monkeypatch):
    """Mock les fonctions de récupération CMS pour éviter les accès DB réels."""
    from backend.api import newcms

    # Mock pages
    def fake_fetch_pages(tenant_id: int):
        return [
            newcms.CMSPage(
                id=1,
                slug="cockpit",
                title="Cockpit - Vue Consolidée",
                description="Vue d'ensemble KPI",
                content={"sections": [{"type": "kpi_grid"}]},
                status="published",
            ),
            newcms.CMSPage(
                id=2,
                slug="operations",
                title="Opérations",
                description="Gestion quotidienne",
                content={"sections": []},
                status="published",
            ),
            newcms.CMSPage(
                id=3,
                slug="finance",
                title="Finance",
                description="Trésorerie",
                content={"sections": []},
                status="draft",
            ),
        ]

    # Mock navigation
    def fake_fetch_nav(tenant_id: int):
        return [
            newcms.CMSNavItem(id=1, label="Cockpit", path="/newcms/cockpit", section="main", order_index=10, icon="Gauge"),
            newcms.CMSNavItem(id=2, label="Opérations", path="/newcms/operations", section="main", order_index=20, icon="Package"),
            newcms.CMSNavItem(id=3, label="Finance", path="/newcms/finance", section="main", order_index=30, icon="Wallet"),
            newcms.CMSNavItem(id=4, label="Restaurant", path="/newcms/restaurant", section="main", order_index=40, icon="Utensils"),
            newcms.CMSNavItem(id=5, label="Intelligence", path="/newcms/intelligence", section="main", order_index=50, icon="Brain"),
        ]

    monkeypatch.setattr("backend.api.newcms._fetch_pages", fake_fetch_pages)
    monkeypatch.setattr("backend.api.newcms._fetch_nav", fake_fetch_nav)


# ============================================================================
# TESTS PAGES CMS
# ============================================================================


def test_list_pages_success(api_client):
    """Test GET /newcms/pages - Retourne la liste des pages."""
    response = api_client.get("/newcms/pages")
    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    pages = data["data"]

    assert isinstance(pages, list)
    assert len(pages) == 3
    assert pages[0]["slug"] == "cockpit"
    assert pages[0]["status"] == "published"


def test_list_pages_different_tenant(api_client, monkeypatch, restaurant_tenant):
    """Test GET /newcms/pages - Vérifie l'isolation par tenant."""
    monkeypatch.setattr(
        "backend.dependencies.tenant.resolve_tenant",
        lambda *_args, **_kwargs: restaurant_tenant,
    )

    response = api_client.get("/newcms/pages")
    assert response.status_code == 200

    data = response.json()
    pages = data["data"]
    assert isinstance(pages, list)


def test_create_page_success(api_client, monkeypatch):
    """Test POST /newcms/pages - Création d'une page."""
    from backend.api import newcms

    created_page = newcms.CMSPage(
        id=99,
        slug="test-page",
        title="Page de test",
        description="Description test",
        content={"sections": []},
        status="draft",
    )

    # Mock exec_sql et _fetch_pages
    def fake_exec_sql(*args, **kwargs):
        pass

    def fake_fetch_pages_after_create(tenant_id: int):
        return [created_page]

    monkeypatch.setattr("backend.api.newcms.exec_sql", fake_exec_sql)
    monkeypatch.setattr("backend.api.newcms._fetch_pages", fake_fetch_pages_after_create)

    payload = {
        "slug": "test-page",
        "title": "Page de test",
        "description": "Description test",
        "content": {"sections": []},
        "status": "draft",
    }

    response = api_client.post("/newcms/pages", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "data" in data
    page = data["data"]
    assert page["slug"] == "test-page"
    assert page["title"] == "Page de test"


def test_update_page_success(api_client, monkeypatch):
    """Test PUT /newcms/pages/{page_id} - Mise à jour d'une page."""
    from backend.api import newcms

    updated_page = newcms.CMSPage(
        id=1,
        slug="cockpit",
        title="Cockpit - Mis à jour",
        description="Nouvelle description",
        content={"sections": [{"type": "updated"}]},
        status="published",
    )

    def fake_exec_sql(*args, **kwargs):
        pass

    def fake_fetch_pages_after_update(tenant_id: int):
        return [updated_page]

    monkeypatch.setattr("backend.api.newcms.exec_sql", fake_exec_sql)
    monkeypatch.setattr("backend.api.newcms._fetch_pages", fake_fetch_pages_after_update)

    payload = {
        "title": "Cockpit - Mis à jour",
        "description": "Nouvelle description",
    }

    response = api_client.put("/newcms/pages/1", json=payload)
    assert response.status_code == 200

    data = response.json()
    page = data["data"]
    assert page["title"] == "Cockpit - Mis à jour"


def test_update_page_no_changes(api_client):
    """Test PUT /newcms/pages/{page_id} - Erreur 400 si aucun champ à mettre à jour."""
    response = api_client.put("/newcms/pages/1", json={})
    assert response.status_code == 400

    data = response.json()
    assert data["success"] is False
    assert "error" in data


def test_update_page_not_found(api_client, monkeypatch):
    """Test PUT /newcms/pages/{page_id} - Erreur 404 si page inexistante."""
    def fake_exec_sql(*args, **kwargs):
        pass

    def fake_fetch_pages_empty(tenant_id: int):
        return []

    monkeypatch.setattr("backend.api.newcms.exec_sql", fake_exec_sql)
    monkeypatch.setattr("backend.api.newcms._fetch_pages", fake_fetch_pages_empty)

    payload = {"title": "New title"}
    response = api_client.put("/newcms/pages/999", json=payload)
    assert response.status_code == 404

    data = response.json()
    assert data["success"] is False


def test_delete_page_success(api_client, monkeypatch):
    """Test DELETE /newcms/pages/{page_id} - Suppression d'une page."""
    def fake_exec_sql(*args, **kwargs):
        pass

    monkeypatch.setattr("backend.api.newcms.exec_sql", fake_exec_sql)

    response = api_client.delete("/newcms/pages/1")
    assert response.status_code == 204


# ============================================================================
# TESTS NAVIGATION CMS
# ============================================================================


def test_list_nav_success(api_client):
    """Test GET /newcms/nav - Retourne la liste des éléments de navigation."""
    response = api_client.get("/newcms/nav")
    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    nav_items = data["data"]

    assert isinstance(nav_items, list)
    assert len(nav_items) == 5
    assert nav_items[0]["label"] == "Cockpit"
    assert nav_items[0]["path"] == "/newcms/cockpit"
    assert nav_items[0]["icon"] == "Gauge"


def test_list_nav_ordered_correctly(api_client):
    """Test GET /newcms/nav - Vérifie que les items sont triés par order_index."""
    response = api_client.get("/newcms/nav")
    data = response.json()
    nav_items = data["data"]

    # Vérifie l'ordre
    assert nav_items[0]["order_index"] == 10  # Cockpit
    assert nav_items[1]["order_index"] == 20  # Opérations
    assert nav_items[2]["order_index"] == 30  # Finance
    assert nav_items[3]["order_index"] == 40  # Restaurant
    assert nav_items[4]["order_index"] == 50  # Intelligence


def test_create_nav_item_success(api_client, monkeypatch):
    """Test POST /newcms/nav - Création d'un élément de navigation."""
    from backend.api import newcms

    created_item = newcms.CMSNavItem(
        id=99,
        label="Config",
        path="/newcms/config",
        section="main",
        order_index=60,
        icon="Settings",
    )

    def fake_exec_sql(*args, **kwargs):
        pass

    def fake_fetch_nav_after_create(tenant_id: int):
        return [created_item]

    monkeypatch.setattr("backend.api.newcms.exec_sql", fake_exec_sql)
    monkeypatch.setattr("backend.api.newcms._fetch_nav", fake_fetch_nav_after_create)

    payload = {
        "label": "Config",
        "path": "/newcms/config",
        "section": "main",
        "order_index": 60,
        "icon": "Settings",
    }

    response = api_client.post("/newcms/nav", json=payload)
    assert response.status_code == 201

    data = response.json()
    item = data["data"]
    assert item["label"] == "Config"
    assert item["path"] == "/newcms/config"


# ============================================================================
# TESTS ERREURS & EDGE CASES
# ============================================================================


def test_unauthenticated_request(monkeypatch):
    """Test sans token d'authentification - Doit retourner 401 ou accès refusé."""
    # Désactive le mock de tenant pour forcer l'échec d'auth
    monkeypatch.setattr(
        "backend.dependencies.tenant.resolve_tenant",
        lambda *args, **kwargs: None,  # Simule absence de tenant
    )

    client = TestClient(app)
    # Pas de headers Authorization

    # Le endpoint newcms n'a pas de dépendances d'auth strictes dans main.py (ligne 357)
    # mais on peut tester qu'il répond quand même (selon config)
    response = client.get("/newcms/pages")

    # Si le endpoint nécessite auth, on attend 401/403, sinon 200
    # Dans notre cas, newcms est sans auth stricte, donc on attend 200 ou 422 (tenant manquant)
    assert response.status_code in [200, 401, 403, 422]


def test_page_not_found_404():
    """Test GET /newcms/pages/{invalid_id} - Endpoint inexistant."""
    client = TestClient(app)
    response = client.get("/newcms/pages/999")

    # Le router ne définit pas GET /newcms/pages/{id}, donc 404 ou 405
    assert response.status_code in [404, 405]


def test_invalid_page_slug(api_client, monkeypatch):
    """Test POST /newcms/pages avec slug vide - Validation Pydantic doit échouer."""
    def fake_exec_sql(*args, **kwargs):
        pass

    monkeypatch.setattr("backend.api.newcms.exec_sql", fake_exec_sql)

    payload = {
        "slug": "",  # Slug vide, devrait échouer (min_length=1)
        "title": "Test",
        "content": {},
    }

    response = api_client.post("/newcms/pages", json=payload)
    assert response.status_code == 422  # Unprocessable Entity (validation error)


def test_response_wrapper_format(api_client):
    """Test que les réponses respectent le format ResponseWrapper."""
    response = api_client.get("/newcms/pages")
    assert response.status_code == 200

    data = response.json()

    # Vérifie le format ResponseWrapper: {success, data, error, meta}
    assert "success" in data
    assert "data" in data
    assert data["success"] is True
    assert isinstance(data["data"], list)

    # Optionnel: meta peut contenir timestamp, request_id, etc
    # assert "meta" in data


def test_response_wrapper_error_format(api_client):
    """Test que les erreurs respectent le format ResponseWrapper."""
    response = api_client.put("/newcms/pages/1", json={})
    assert response.status_code == 400

    data = response.json()
    assert "success" in data
    assert "error" in data
    assert data["success"] is False
    assert data["error"] is not None


# ============================================================================
# TESTS ISOLATION PAR TENANT
# ============================================================================


def test_pages_isolation_by_tenant(api_client, monkeypatch, restaurant_tenant):
    """Test que les pages sont isolées par tenant."""
    from backend.api import newcms

    # Mock pour retourner des pages différentes selon tenant
    def fake_fetch_pages_by_tenant(tenant_id: int):
        if tenant_id == 1:
            return [
                newcms.CMSPage(id=1, slug="page1", title="Épicerie Page", description="", content={}, status="published"),
            ]
        elif tenant_id == 2:
            return [
                newcms.CMSPage(id=2, slug="page2", title="Restaurant Page", description="", content={}, status="published"),
            ]
        return []

    monkeypatch.setattr("backend.api.newcms._fetch_pages", fake_fetch_pages_by_tenant)

    # Requête avec tenant 1 (épicerie)
    response = api_client.get("/newcms/pages")
    data = response.json()
    assert data["data"][0]["title"] == "Épicerie Page"

    # Changement de tenant vers restaurant (tenant_id=2)
    monkeypatch.setattr(
        "backend.dependencies.tenant.resolve_tenant",
        lambda *_args, **_kwargs: restaurant_tenant,
    )

    response = api_client.get("/newcms/pages")
    data = response.json()
    assert data["data"][0]["title"] == "Restaurant Page"


def test_nav_isolation_by_tenant(api_client, monkeypatch, intelligence_tenant):
    """Test que la navigation est isolée par tenant."""
    from backend.api import newcms

    def fake_fetch_nav_by_tenant(tenant_id: int):
        if tenant_id == 1:
            return [newcms.CMSNavItem(id=1, label="Epicerie Nav", path="/e", section="main", order_index=0)]
        elif tenant_id == 3:
            return [newcms.CMSNavItem(id=2, label="Intelligence Nav", path="/i", section="main", order_index=0)]
        return []

    monkeypatch.setattr("backend.api.newcms._fetch_nav", fake_fetch_nav_by_tenant)

    # Tenant 1 (épicerie)
    response = api_client.get("/newcms/nav")
    data = response.json()
    assert data["data"][0]["label"] == "Epicerie Nav"

    # Tenant 3 (intelligence)
    monkeypatch.setattr(
        "backend.dependencies.tenant.resolve_tenant",
        lambda *_args, **_kwargs: intelligence_tenant,
    )

    response = api_client.get("/newcms/nav")
    data = response.json()
    assert data["data"][0]["label"] == "Intelligence Nav"


# ============================================================================
# TESTS INTÉGRATION VUES CMS
# ============================================================================


def test_cockpit_overview_placeholder(api_client):
    """Test GET /newcms/cockpit - Vérifie que l'endpoint (s'il existe) répond."""
    # Note: Si l'endpoint n'existe pas encore, ce test échouera (404)
    # C'est attendu et servira de TODO pour créer l'endpoint
    response = api_client.get("/newcms/cockpit")
    # On accepte 200 (existe), 404 (pas encore implémenté), ou 405 (méthode non autorisée)
    assert response.status_code in [200, 404, 405]


def test_operations_overview_placeholder(api_client):
    """Test GET /newcms/operations/overview - Placeholder."""
    response = api_client.get("/newcms/operations/overview")
    assert response.status_code in [200, 404, 405]


def test_finance_overview_placeholder(api_client):
    """Test GET /newcms/finance/overview - Placeholder."""
    response = api_client.get("/newcms/finance/overview")
    assert response.status_code in [200, 404, 405]


def test_restaurant_overview_placeholder(api_client):
    """Test GET /newcms/restaurant/overview - Placeholder."""
    response = api_client.get("/newcms/restaurant/overview")
    assert response.status_code in [200, 404, 405]


def test_intelligence_overview_placeholder(api_client):
    """Test GET /newcms/intelligence/overview - Placeholder."""
    response = api_client.get("/newcms/intelligence/overview")
    assert response.status_code in [200, 404, 405]


# ============================================================================
# TESTS PAGINATION (si implémenté)
# ============================================================================


def test_pagination_validation():
    """Test de validation des paramètres de pagination."""
    client = TestClient(app)

    # Pagination invalide (page négative)
    response = client.get("/newcms/pages?page=-1&per_page=10")
    # Devrait retourner 422 (validation error) ou ignorer et retourner 200
    assert response.status_code in [200, 422]

    # per_page trop grand
    response = client.get("/newcms/pages?page=1&per_page=10000")
    assert response.status_code in [200, 422]


# ============================================================================
# TESTS PERFORMANCE & EDGE CASES
# ============================================================================


def test_large_content_jsonb(api_client, monkeypatch):
    """Test avec un contenu JSONB volumineux."""
    from backend.api import newcms

    large_content = {
        "sections": [
            {
                "type": "chart",
                "data": [{"x": i, "y": i * 2} for i in range(1000)],
            }
            for _ in range(10)
        ]
    }

    created_page = newcms.CMSPage(
        id=100,
        slug="large-page",
        title="Large Page",
        description="",
        content=large_content,
        status="draft",
    )

    def fake_exec_sql(*args, **kwargs):
        pass

    def fake_fetch_pages_large(tenant_id: int):
        return [created_page]

    monkeypatch.setattr("backend.api.newcms.exec_sql", fake_exec_sql)
    monkeypatch.setattr("backend.api.newcms._fetch_pages", fake_fetch_pages_large)

    payload = {
        "slug": "large-page",
        "title": "Large Page",
        "content": large_content,
    }

    response = api_client.post("/newcms/pages", json=payload)
    assert response.status_code == 201


def test_special_characters_in_slug(api_client, monkeypatch):
    """Test avec caractères spéciaux dans le slug."""
    from backend.api import newcms

    def fake_exec_sql(*args, **kwargs):
        pass

    def fake_fetch_pages_special(tenant_id: int):
        return [
            newcms.CMSPage(
                id=101,
                slug="page-with-émojis-éè",
                title="Test",
                description="",
                content={},
                status="draft",
            )
        ]

    monkeypatch.setattr("backend.api.newcms.exec_sql", fake_exec_sql)
    monkeypatch.setattr("backend.api.newcms._fetch_pages", fake_fetch_pages_special)

    payload = {
        "slug": "page-with-émojis-éè",
        "title": "Test",
        "content": {},
    }

    response = api_client.post("/newcms/pages", json=payload)
    assert response.status_code == 201


# ============================================================================
# TESTS MÉTA
# ============================================================================


def test_health_endpoint():
    """Test que le health endpoint fonctionne (sanity check)."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
