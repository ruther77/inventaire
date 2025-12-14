"""
Tests pour les endpoints corrigés (P0 roadmap décembre 2025)
============================================================

Endpoints testés:
- /finance/categories/suggestions/complete (fix 422 - paramètre q optionnel)
- /audit-trail/report (fix 422 - dates optionnelles avec défauts)
- /restaurant/plats (connexion nouvelles tables plats/ingredients)
- /restaurant/ingredients (connexion nouvelles tables)
"""

import pytest
import requests
import os
import jwt
from datetime import datetime, timedelta

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "superlongdevsecretkey_please_change_me_123456789")


def _generate_test_token(tenant_id: int = 1, tenant_code: str = "epicerie") -> str:
    """Génère un token JWT de test."""
    payload = {
        "sub": "1",
        "username": "admin",
        "role": "admin",
        "tenant_id": tenant_id,
        "tenant_code": tenant_code,
        "exp": datetime.now() + timedelta(hours=1),
        "jti": f"test-{tenant_code}-{datetime.now().timestamp()}"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@pytest.fixture(scope="module")
def auth_token():
    """Token pour tenant epicerie."""
    return _generate_test_token(tenant_id=1, tenant_code="epicerie")


@pytest.fixture(scope="module")
def restaurant_token():
    """Token pour tenant restaurant."""
    return _generate_test_token(tenant_id=2, tenant_code="restaurant")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Headers avec authentification epicerie."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="module")
def restaurant_headers(restaurant_token):
    """Headers avec authentification restaurant."""
    return {"Authorization": f"Bearer {restaurant_token}"}


def extract_data(response_json):
    """Extrait les données depuis une réponse wrappée ou non."""
    if isinstance(response_json, dict) and "success" in response_json:
        # Format wrappé: {"success": true, "data": [...], ...}
        return response_json.get("data")
    return response_json


# =============================================================================
# Tests /finance/categories/suggestions/complete (fix 422)
# =============================================================================
class TestFinanceCategorySuggestions:
    """Tests pour l'endpoint autocomplete catégories corrigé."""

    def test_suggestions_without_query_param(self, headers):
        """Appel sans paramètre q - doit retourner liste vide (pas 422)."""
        response = requests.get(
            f"{BASE_URL}/finance/categories/suggestions/complete",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = extract_data(response.json())
        assert isinstance(data, list)
        assert len(data) == 0  # Sans query, retourne []

    def test_suggestions_with_empty_query(self, headers):
        """Appel avec q="" - doit retourner liste vide."""
        response = requests.get(
            f"{BASE_URL}/finance/categories/suggestions/complete",
            headers=headers,
            params={"q": ""},
            timeout=10
        )
        assert response.status_code == 200
        data = extract_data(response.json())
        assert isinstance(data, list)
        assert len(data) == 0

    def test_suggestions_with_valid_query(self, headers):
        """Appel avec une recherche valide."""
        response = requests.get(
            f"{BASE_URL}/finance/categories/suggestions/complete",
            headers=headers,
            params={"q": "ali"},  # Recherche partielle
            timeout=10
        )
        assert response.status_code == 200
        data = extract_data(response.json())
        assert isinstance(data, list)

    def test_suggestions_with_limit(self, headers):
        """Appel avec limite personnalisée."""
        response = requests.get(
            f"{BASE_URL}/finance/categories/suggestions/complete",
            headers=headers,
            params={"q": "a", "limit": 5},
            timeout=10
        )
        assert response.status_code == 200
        data = extract_data(response.json())
        assert isinstance(data, list)
        assert len(data) <= 5


# =============================================================================
# Tests /audit-trail/report (fix 422)
# =============================================================================
class TestAuditTrailReport:
    """Tests pour l'endpoint audit report corrigé."""

    def test_report_without_dates(self, headers):
        """Appel sans dates - doit utiliser défauts (30 jours)."""
        response = requests.get(
            f"{BASE_URL}/audit-trail/report",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = extract_data(response.json())
        assert "period_start" in data
        assert "period_end" in data
        assert "total_entries" in data

    def test_report_with_dates(self, headers):
        """Appel avec dates explicites."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        response = requests.get(
            f"{BASE_URL}/audit-trail/report",
            headers=headers,
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            timeout=10
        )
        assert response.status_code == 200
        data = extract_data(response.json())
        assert "total_entries" in data
        assert isinstance(data["total_entries"], int)

    def test_report_structure(self, headers):
        """Vérifie la structure complète du rapport."""
        response = requests.get(
            f"{BASE_URL}/audit-trail/report",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 200
        data = extract_data(response.json())

        expected_fields = [
            "period_start", "period_end", "total_entries",
            "actions_count", "entities_count", "users_activity",
            "severity_count", "security_events", "failed_logins",
            "suspicious_activities"
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


# =============================================================================
# Tests /restaurant/plats (connexion nouvelles tables)
# =============================================================================
class TestRestaurantPlats:
    """Tests pour l'API plats connectée aux nouvelles tables."""

    def test_list_plats(self, restaurant_headers):
        """Liste des plats depuis la table plats."""
        response = requests.get(
            f"{BASE_URL}/restaurant/plats",
            headers=restaurant_headers,
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = extract_data(response.json())
        assert isinstance(data, list)
        assert len(data) > 0, "Au moins un plat devrait exister"

    def test_plat_structure(self, restaurant_headers):
        """Vérifie la structure d'un plat."""
        response = requests.get(
            f"{BASE_URL}/restaurant/plats",
            headers=restaurant_headers,
            timeout=10
        )
        assert response.status_code == 200
        data = extract_data(response.json())

        if len(data) > 0:
            plat = data[0]
            assert "id" in plat
            assert "nom" in plat
            assert "cout_matiere" in plat
            assert "marge_brute" in plat
            assert "marge_pct" in plat
            assert isinstance(plat["cout_matiere"], (int, float, type(None)))

    def test_plats_with_pagination_params(self, restaurant_headers):
        """Test que l'endpoint accepte les paramètres de pagination (même si non implémenté)."""
        response = requests.get(
            f"{BASE_URL}/restaurant/plats",
            headers=restaurant_headers,
            params={"limit": 10, "offset": 0},
            timeout=10
        )
        # L'endpoint doit retourner 200 même avec des params de pagination
        assert response.status_code == 200
        data = extract_data(response.json())
        assert isinstance(data, list)
        # Note: la pagination n'est pas encore implémentée, donc on vérifie juste que ça ne plante pas


# =============================================================================
# Tests /restaurant/ingredients (connexion nouvelles tables)
# =============================================================================
class TestRestaurantIngredients:
    """Tests pour l'API ingredients connectée aux nouvelles tables."""

    def test_list_ingredients(self, restaurant_headers):
        """Liste des ingrédients depuis la table ingredients."""
        response = requests.get(
            f"{BASE_URL}/restaurant/ingredients",
            headers=restaurant_headers,
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = extract_data(response.json())
        assert isinstance(data, list)
        assert len(data) > 0, "Au moins un ingrédient devrait exister"

    def test_ingredient_structure(self, restaurant_headers):
        """Vérifie la structure d'un ingrédient."""
        response = requests.get(
            f"{BASE_URL}/restaurant/ingredients",
            headers=restaurant_headers,
            timeout=10
        )
        assert response.status_code == 200
        data = extract_data(response.json())

        if len(data) > 0:
            ingredient = data[0]
            assert "id" in ingredient
            assert "nom" in ingredient
            assert "unite_base" in ingredient
            assert "cout_unitaire" in ingredient
            assert "stock_actuel" in ingredient
            assert isinstance(ingredient["cout_unitaire"], (int, float, type(None)))
            assert isinstance(ingredient["stock_actuel"], (int, float, type(None)))

    def test_ingredients_count(self, restaurant_headers):
        """Vérifie qu'il y a des ingrédients (stock initialisé)."""
        response = requests.get(
            f"{BASE_URL}/restaurant/ingredients",
            headers=restaurant_headers,
            timeout=10
        )
        assert response.status_code == 200
        data = extract_data(response.json())
        assert isinstance(data, list)
        assert len(data) >= 39, f"Expected at least 39 ingredients, got {len(data)}"


# =============================================================================
# Tests intégration plats/ingredients
# =============================================================================
class TestRestaurantIntegration:
    """Tests d'intégration entre plats et ingrédients."""

    def test_plat_cost_calculation(self, restaurant_headers):
        """Vérifie que le coût matière est calculé."""
        response = requests.get(
            f"{BASE_URL}/restaurant/plats",
            headers=restaurant_headers,
            timeout=10
        )
        assert response.status_code == 200
        data = extract_data(response.json())

        # Vérifie que les champs marge sont présents
        for plat in data[:5]:
            assert "cout_matiere" in plat
            assert "marge_brute" in plat
            assert "marge_pct" in plat

    def test_margin_alerts_endpoint(self, restaurant_headers):
        """Test endpoint alertes marges."""
        response = requests.get(
            f"{BASE_URL}/restaurant/alerts/margins",
            headers=restaurant_headers,
            timeout=10
        )
        # Peut être 200 ou 404 selon si l'endpoint existe
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = extract_data(response.json())
            assert isinstance(data, list)


# =============================================================================
# Tests format réponse standardisé (ResponseWrapper)
# =============================================================================
class TestResponseWrapper:
    """Tests pour le format de réponse unifié."""

    def test_success_response_format(self, restaurant_headers):
        """Vérifie le format de réponse de succès."""
        response = requests.get(
            f"{BASE_URL}/restaurant/plats",
            headers=restaurant_headers,
            timeout=10
        )
        assert response.status_code == 200
        json_data = response.json()

        # Vérifie le format wrappé
        assert "success" in json_data
        assert json_data["success"] is True
        assert "data" in json_data
        assert "error" in json_data
        assert json_data["error"] is None
        assert "meta" in json_data
        assert "request_id" in json_data["meta"]
        assert "duration_ms" in json_data["meta"]

    def test_error_response_format(self):
        """Vérifie le format de réponse d'erreur (sans auth)."""
        response = requests.get(
            f"{BASE_URL}/restaurant/plats",
            timeout=10
        )
        assert response.status_code == 401
        json_data = response.json()

        # Vérifie le format wrappé pour les erreurs
        assert "success" in json_data
        assert json_data["success"] is False
        assert "data" in json_data
        assert json_data["data"] is None
        assert "error" in json_data
        assert "code" in json_data["error"]
        assert "message" in json_data["error"]
        assert "suggestion" in json_data["error"]
        assert "meta" in json_data
        assert json_data["meta"] is not None

    def test_health_excluded_from_wrapper(self):
        """Vérifie que /health n'est pas wrappé."""
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        assert response.status_code == 200
        json_data = response.json()

        # /health ne doit pas être wrappé
        assert json_data == {"status": "ok"}
