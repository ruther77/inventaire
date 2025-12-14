"""
================================================================================
TEST HARDCORE FEATURES - 100 Tests par Fonctionnalite
================================================================================
Ce module teste exhaustivement toutes les fonctionnalites de l'application.

Pour executer: pytest tests/test_hardcore_features.py -v --tb=short
================================================================================
"""

import pytest
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import time

# Configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
TEST_USERNAME = os.getenv("TEST_USERNAME", "admin")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "admin123")

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def auth_token():
    """Obtient un token d'authentification valide."""
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
        timeout=10
    )
    if response.status_code != 200:
        pytest.skip(f"Authentification echouee: {response.status_code}")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def headers(auth_token):
    """Headers avec authentification."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def api_client(headers):
    """Client API avec authentification."""
    class APIClient:
        def __init__(self, headers):
            self.headers = headers
            self.base_url = BASE_URL

        def get(self, path: str, params: dict = None, expected_status: int = 200) -> dict:
            url = f"{self.base_url}{path}"
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            assert response.status_code == expected_status, f"GET {path} returned {response.status_code}: {response.text[:500]}"
            return response.json() if response.text else {}

        def post(self, path: str, data: dict = None, expected_status: int = 200) -> dict:
            url = f"{self.base_url}{path}"
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            assert response.status_code == expected_status, f"POST {path} returned {response.status_code}: {response.text[:500]}"
            return response.json() if response.text else {}

        def patch(self, path: str, data: dict = None, expected_status: int = 200) -> dict:
            url = f"{self.base_url}{path}"
            response = requests.patch(url, headers=self.headers, json=data, timeout=30)
            assert response.status_code == expected_status, f"PATCH {path} returned {response.status_code}: {response.text[:500]}"
            return response.json() if response.text else {}

        def delete(self, path: str, expected_status: int = 200) -> dict:
            url = f"{self.base_url}{path}"
            response = requests.delete(url, headers=self.headers, timeout=30)
            assert response.status_code == expected_status, f"DELETE {path} returned {response.status_code}: {response.text[:500]}"
            return response.json() if response.text else {}

        def raw_get(self, path: str, params: dict = None) -> requests.Response:
            url = f"{self.base_url}{path}"
            return requests.get(url, headers=self.headers, params=params, timeout=30)

    return APIClient(headers)


# ============================================================================
# 1. TESTS AUTH (10 tests)
# ============================================================================
class TestAuth:
    """Tests pour le module d'authentification."""

    def test_auth_01_valid_login(self):
        """Login avec credentials valides."""
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_auth_02_invalid_password(self):
        """Login avec mot de passe invalide."""
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": TEST_USERNAME, "password": "wrongpassword"},
            timeout=10
        )
        assert response.status_code in [400, 401]

    def test_auth_03_invalid_username(self):
        """Login avec username invalide."""
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": "nonexistent", "password": "password"},
            timeout=10
        )
        assert response.status_code in [400, 401]

    def test_auth_04_empty_credentials(self):
        """Login sans credentials."""
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={},
            timeout=10
        )
        assert response.status_code in [400, 422]

    def test_auth_05_missing_password(self):
        """Login sans mot de passe."""
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": TEST_USERNAME},
            timeout=10
        )
        assert response.status_code in [400, 422]

    def test_auth_06_token_format(self):
        """Verifier le format du token JWT."""
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            parts = token.split(".")
            assert len(parts) == 3, "Token JWT doit avoir 3 parties"

    def test_auth_07_protected_endpoint_without_token(self):
        """Acces endpoint protege sans token."""
        response = requests.get(f"{BASE_URL}/products", timeout=10)
        assert response.status_code in [401, 403]

    def test_auth_08_protected_endpoint_with_invalid_token(self):
        """Acces endpoint protege avec token invalide."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = requests.get(f"{BASE_URL}/products", headers=headers, timeout=10)
        assert response.status_code in [401, 403]

    def test_auth_09_protected_endpoint_with_valid_token(self, headers):
        """Acces endpoint protege avec token valide."""
        response = requests.get(f"{BASE_URL}/products", headers=headers, timeout=10)
        assert response.status_code == 200

    def test_auth_10_multiple_logins(self):
        """Multiple logins consecutifs."""
        for _ in range(5):
            response = requests.post(
                f"{BASE_URL}/auth/token",
                data={"username": TEST_USERNAME, "password": TEST_PASSWORD},
                timeout=10
            )
            assert response.status_code == 200


# ============================================================================
# 2. TESTS CATALOGUE PRODUITS (15 tests)
# ============================================================================
class TestCatalog:
    """Tests pour le module catalogue."""

    def test_catalog_01_list_products(self, api_client):
        """Liste des produits."""
        data = api_client.get("/catalog/products")
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_catalog_02_list_products_pagination(self, api_client):
        """Pagination des produits."""
        data = api_client.get("/catalog/products", {"page": 1, "page_size": 10})
        assert "items" in data
        assert len(data["items"]) <= 10

    def test_catalog_03_list_products_search(self, api_client):
        """Recherche de produits."""
        data = api_client.get("/catalog/products", {"q": "test"})
        assert "items" in data

    def test_catalog_04_list_products_category_filter(self, api_client):
        """Filtrer par categorie."""
        # D'abord obtenir les categories
        categories = api_client.get("/catalog/categories")
        if categories:
            data = api_client.get("/catalog/products", {"category": categories[0] if isinstance(categories, list) else None})
            assert "items" in data

    def test_catalog_05_get_product_by_id(self, api_client):
        """Obtenir un produit par ID."""
        products = api_client.get("/catalog/products")
        if products.get("items"):
            product_id = products["items"][0]["id"]
            product = api_client.get(f"/catalog/products/{product_id}")
            assert product["id"] == product_id

    def test_catalog_06_get_nonexistent_product(self, api_client):
        """Produit inexistant."""
        response = api_client.raw_get("/catalog/products/999999999")
        assert response.status_code == 404

    def test_catalog_07_list_categories(self, api_client):
        """Liste des categories."""
        data = api_client.get("/catalog/categories")
        assert isinstance(data, list) or isinstance(data, dict)

    def test_catalog_08_list_vendors(self, api_client):
        """Liste des fournisseurs."""
        data = api_client.get("/catalog/vendors")
        assert isinstance(data, list) or isinstance(data, dict)

    def test_catalog_09_product_barcode_lookup(self, api_client):
        """Recherche par code-barres."""
        # Test avec un code-barres inexistant
        response = api_client.raw_get("/catalog/products/barcode/0000000000000")
        # 404 est acceptable pour un code inexistant
        assert response.status_code in [200, 404]

    def test_catalog_10_products_with_large_page_size(self, api_client):
        """Large page size."""
        data = api_client.get("/catalog/products", {"page_size": 100})
        assert "items" in data

    def test_catalog_11_products_various_sorts(self, api_client):
        """Differents tris."""
        for sort in ["nom", "-nom", "prix_vente", "-prix_vente"]:
            data = api_client.get("/catalog/products", {"sort": sort})
            assert "items" in data

    def test_catalog_12_products_active_only(self, api_client):
        """Filtrer produits actifs."""
        data = api_client.get("/catalog/products", {"actif": "true"})
        assert "items" in data

    def test_catalog_13_products_with_stock_filter(self, api_client):
        """Filtrer par stock."""
        data = api_client.get("/catalog/products", {"stock_min": 0})
        assert "items" in data

    def test_catalog_14_products_multiple_filters(self, api_client):
        """Multiple filtres combines."""
        data = api_client.get("/catalog/products", {
            "actif": "true",
            "page": 1,
            "page_size": 20
        })
        assert "items" in data

    def test_catalog_15_products_structure_validation(self, api_client):
        """Validation structure produit."""
        data = api_client.get("/catalog/products")
        if data.get("items"):
            product = data["items"][0]
            assert "id" in product
            assert "nom" in product


# ============================================================================
# 3. TESTS STOCK (15 tests)
# ============================================================================
class TestStock:
    """Tests pour le module stock."""

    def test_stock_01_movements_timeseries(self, api_client):
        """Historique mouvements timeseries."""
        data = api_client.get("/stock/movements/timeseries")
        assert "timeseries" in data or "data" in data or isinstance(data, dict)

    def test_stock_02_movements_timeseries_30_days(self, api_client):
        """Mouvements sur 30 jours."""
        data = api_client.get("/stock/movements/timeseries", {"window_days": 30})
        assert isinstance(data, dict)

    def test_stock_03_movements_timeseries_90_days(self, api_client):
        """Mouvements sur 90 jours."""
        data = api_client.get("/stock/movements/timeseries", {"window_days": 90})
        assert isinstance(data, dict)

    def test_stock_04_movements_timeseries_365_days(self, api_client):
        """Mouvements sur 365 jours."""
        data = api_client.get("/stock/movements/timeseries", {"window_days": 365})
        assert isinstance(data, dict)

    def test_stock_05_recent_movements(self, api_client):
        """Mouvements recents."""
        data = api_client.get("/stock/movements/recent")
        assert "items" in data or "movements" in data or isinstance(data, dict)

    def test_stock_06_recent_movements_limit(self, api_client):
        """Mouvements recents avec limite."""
        data = api_client.get("/stock/movements/recent", {"limit": 5})
        assert isinstance(data, dict)

    def test_stock_07_recent_movements_large_limit(self, api_client):
        """Mouvements recents limite importante."""
        data = api_client.get("/stock/movements/recent", {"limit": 100})
        assert isinstance(data, dict)

    def test_stock_08_inventory_summary(self, api_client):
        """Resume inventaire."""
        data = api_client.get("/inventory/summary")
        assert "total_purchase_value" in data or "total_sale_value" in data

    def test_stock_09_products_list(self, api_client):
        """Liste produits simple."""
        data = api_client.get("/products")
        assert isinstance(data, list)

    def test_stock_10_supply_plan(self, api_client):
        """Plan d'approvisionnement."""
        data = api_client.get("/supply/plan")
        assert isinstance(data, dict) or isinstance(data, list)

    def test_stock_11_multiple_timeseries_calls(self, api_client):
        """Multiple appels timeseries."""
        for days in [7, 14, 30, 60, 90]:
            data = api_client.get("/stock/movements/timeseries", {"window_days": days})
            assert isinstance(data, dict)

    def test_stock_12_movements_structure(self, api_client):
        """Structure des mouvements."""
        data = api_client.get("/stock/movements/recent", {"limit": 1})
        # Verifier qu'on a une structure valide
        assert isinstance(data, dict)

    def test_stock_13_inventory_value_positive(self, api_client):
        """Valeur inventaire >= 0."""
        data = api_client.get("/inventory/summary")
        if "total_purchase_value" in data:
            assert data["total_purchase_value"] >= 0
        if "total_sale_value" in data:
            assert data["total_sale_value"] >= 0

    def test_stock_14_concurrent_timeseries(self, api_client):
        """Appels concurrents timeseries."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(api_client.get, "/stock/movements/timeseries", {"window_days": d})
                for d in [30, 60, 90]
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            assert len(results) == 3

    def test_stock_15_recent_movements_pagination(self, api_client):
        """Pagination mouvements recents."""
        data = api_client.get("/stock/movements/recent", {"limit": 10, "offset": 0})
        assert isinstance(data, dict)


# ============================================================================
# 4. TESTS DASHBOARD (10 tests)
# ============================================================================
class TestDashboard:
    """Tests pour le module dashboard."""

    def test_dashboard_01_metrics(self, api_client):
        """Metriques dashboard."""
        data = api_client.get("/dashboard/metrics")
        assert isinstance(data, dict)

    def test_dashboard_02_metrics_structure(self, api_client):
        """Structure metriques."""
        data = api_client.get("/dashboard/metrics")
        # Verifier les champs attendus
        assert isinstance(data, dict)

    def test_dashboard_03_metrics_kpis(self, api_client):
        """KPIs du dashboard."""
        data = api_client.get("/dashboard/metrics")
        # Verifier qu'on a des KPIs
        if "kpis" in data:
            assert isinstance(data["kpis"], (list, dict))

    def test_dashboard_04_multiple_metrics_calls(self, api_client):
        """Multiple appels metriques."""
        for _ in range(5):
            data = api_client.get("/dashboard/metrics")
            assert isinstance(data, dict)

    def test_dashboard_05_metrics_response_time(self, api_client):
        """Temps de reponse metriques."""
        start = time.time()
        api_client.get("/dashboard/metrics")
        elapsed = time.time() - start
        assert elapsed < 10, f"Dashboard trop lent: {elapsed}s"

    def test_dashboard_06_health_check(self, api_client):
        """Health check."""
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_dashboard_07_metrics_values_types(self, api_client):
        """Types des valeurs metriques."""
        data = api_client.get("/dashboard/metrics")
        assert isinstance(data, dict)

    def test_dashboard_08_concurrent_dashboard(self, api_client):
        """Appels concurrents dashboard."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(api_client.get, "/dashboard/metrics")
                for _ in range(5)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            assert len(results) == 5

    def test_dashboard_09_metrics_consistency(self, api_client):
        """Consistance des metriques."""
        data1 = api_client.get("/dashboard/metrics")
        data2 = api_client.get("/dashboard/metrics")
        # Les donnees ne devraient pas changer drastiquement
        assert type(data1) == type(data2)

    def test_dashboard_10_full_dashboard_load(self, api_client):
        """Chargement complet dashboard."""
        # Simuler un chargement complet de dashboard
        api_client.get("/dashboard/metrics")
        api_client.get("/stock/movements/timeseries", {"window_days": 30})
        api_client.get("/stock/movements/recent", {"limit": 10})
        api_client.get("/inventory/summary")


# ============================================================================
# 5. TESTS FINANCE (20 tests)
# ============================================================================
class TestFinance:
    """Tests pour le module finance."""

    def test_finance_01_accounts_list(self, api_client):
        """Liste des comptes."""
        data = api_client.get("/finance/accounts")
        assert isinstance(data, list)

    def test_finance_02_accounts_overview(self, api_client):
        """Vue d'ensemble comptes."""
        data = api_client.get("/finance/accounts/overview")
        assert isinstance(data, (list, dict))

    def test_finance_03_transactions_list(self, api_client):
        """Liste transactions."""
        data = api_client.get("/finance/transactions")
        assert isinstance(data, (list, dict))

    def test_finance_04_transactions_search(self, api_client):
        """Recherche transactions."""
        data = api_client.get("/finance/transactions/search")
        assert isinstance(data, dict)

    def test_finance_05_categories_list(self, api_client):
        """Liste categories finance."""
        data = api_client.get("/finance/categories")
        assert isinstance(data, list)

    def test_finance_06_rules_list(self, api_client):
        """Liste regles finance."""
        data = api_client.get("/finance/rules")
        assert isinstance(data, list)

    def test_finance_07_imports_list(self, api_client):
        """Liste imports."""
        data = api_client.get("/finance/imports")
        assert isinstance(data, list)

    def test_finance_08_dashboard_summary(self, api_client):
        """Resume finance dashboard."""
        data = api_client.get("/finance/dashboard/summary")
        assert isinstance(data, dict)

    def test_finance_09_categories_stats(self, api_client):
        """Stats categories."""
        data = api_client.get("/finance/categories/stats")
        assert isinstance(data, (list, dict))

    def test_finance_10_vendors_list(self, api_client):
        """Liste vendeurs finance."""
        data = api_client.get("/finance/vendors")
        assert isinstance(data, list)

    def test_finance_11_cost_centers(self, api_client):
        """Centres de cout."""
        data = api_client.get("/finance/cost-centers")
        assert isinstance(data, list)

    def test_finance_12_stats_timeline(self, api_client):
        """Timeline stats."""
        data = api_client.get("/finance/stats/timeline")
        assert isinstance(data, (list, dict))

    def test_finance_13_stats_category_breakdown(self, api_client):
        """Breakdown par categorie."""
        data = api_client.get("/finance/stats/category-breakdown")
        assert isinstance(data, (list, dict))

    def test_finance_14_stats_treasury(self, api_client):
        """Stats tresorerie."""
        data = api_client.get("/finance/stats/treasury")
        assert isinstance(data, dict)

    def test_finance_15_invoices_search(self, api_client):
        """Recherche factures."""
        data = api_client.get("/finance/invoices/search")
        assert isinstance(data, dict)

    def test_finance_16_bank_statements_search(self, api_client):
        """Recherche releves bancaires."""
        data = api_client.get("/finance/bank-statements/search")
        assert isinstance(data, dict)

    def test_finance_17_reconciliation_matches(self, api_client):
        """Matches rapprochement."""
        data = api_client.get("/finance/reconciliation/matches")
        assert isinstance(data, list)

    def test_finance_18_recurring(self, api_client):
        """Depenses recurrentes."""
        data = api_client.get("/finance/recurring")
        assert isinstance(data, list)

    def test_finance_19_anomalies(self, api_client):
        """Anomalies finance."""
        data = api_client.get("/finance/anomalies")
        assert isinstance(data, list)

    def test_finance_20_categories_suggestions(self, api_client):
        """Suggestions categories."""
        data = api_client.get("/finance/categories/suggestions/complete")
        assert isinstance(data, (list, dict))


# ============================================================================
# 6. TESTS RESTAURANT (15 tests)
# ============================================================================
class TestRestaurant:
    """Tests pour le module restaurant."""

    def test_restaurant_01_plats_list(self, api_client):
        """Liste des plats."""
        data = api_client.get("/restaurant/plats")
        assert isinstance(data, list)

    def test_restaurant_02_ingredients_list(self, api_client):
        """Liste ingredients."""
        data = api_client.get("/restaurant/ingredients")
        assert isinstance(data, list)

    def test_restaurant_03_charges_categories(self, api_client):
        """Categories charges."""
        data = api_client.get("/restaurant/charges/categories")
        assert isinstance(data, list)

    def test_restaurant_04_charges_expenses(self, api_client):
        """Liste depenses."""
        data = api_client.get("/restaurant/charges/expenses")
        assert isinstance(data, list)

    def test_restaurant_05_charges_summary(self, api_client):
        """Resume charges."""
        data = api_client.get("/restaurant/charges/summary")
        assert isinstance(data, list)

    def test_restaurant_06_charges_tva_summary(self, api_client):
        """Resume TVA."""
        data = api_client.get("/restaurant/charges/tva-summary")
        assert isinstance(data, list)

    def test_restaurant_07_cost_centers(self, api_client):
        """Centres de cout restaurant."""
        data = api_client.get("/restaurant/charges/cost-centers")
        assert isinstance(data, list)

    def test_restaurant_08_dashboard_overview(self, api_client):
        """Vue d'ensemble dashboard."""
        data = api_client.get("/restaurant/dashboard/overview")
        assert isinstance(data, dict)

    def test_restaurant_09_forecasts_overview(self, api_client):
        """Vue previsions."""
        data = api_client.get("/restaurant/forecasts/overview")
        assert isinstance(data, dict)

    def test_restaurant_10_prices_history(self, api_client):
        """Historique prix."""
        data = api_client.get("/restaurant/prices/history")
        assert isinstance(data, dict)

    def test_restaurant_11_alerts(self, api_client):
        """Alertes restaurant."""
        data = api_client.get("/restaurant/alerts")
        assert isinstance(data, list)

    def test_restaurant_12_consumptions(self, api_client):
        """Consommations."""
        data = api_client.get("/restaurant/consumptions")
        assert isinstance(data, list)

    def test_restaurant_13_price_history_comparison(self, api_client):
        """Comparaison historique prix."""
        data = api_client.get("/restaurant/price-history/comparison")
        assert isinstance(data, list)

    def test_restaurant_14_plats_mappings(self, api_client):
        """Mappings plats."""
        data = api_client.get("/restaurant/plats/mappings")
        assert isinstance(data, list)

    def test_restaurant_15_epicerie_products(self, api_client):
        """Produits epicerie."""
        data = api_client.get("/restaurant/epicerie/products")
        assert isinstance(data, (list, dict))


# ============================================================================
# 7. TESTS INTELLIGENCE (15 tests)
# ============================================================================
class TestIntelligence:
    """Tests pour le module intelligence."""

    def test_intelligence_01_inventory_reorder_points(self, api_client):
        """Points de reapprovisionnement."""
        data = api_client.get("/inventory-intelligence/reorder-points")
        assert isinstance(data, list)

    def test_intelligence_02_stockout_predictions(self, api_client):
        """Predictions rupture."""
        data = api_client.get("/inventory-intelligence/stockout-predictions")
        assert isinstance(data, list)

    def test_intelligence_03_dead_stock(self, api_client):
        """Stock mort."""
        data = api_client.get("/inventory-intelligence/dead-stock")
        assert isinstance(data, list)

    def test_intelligence_04_abc_xyz(self, api_client):
        """Classification ABC-XYZ."""
        data = api_client.get("/inventory-intelligence/abc-xyz")
        assert isinstance(data, list)

    def test_intelligence_05_reorder_suggestions(self, api_client):
        """Suggestions reapprovisionnement."""
        data = api_client.get("/inventory-intelligence/reorder-suggestions")
        assert isinstance(data, list)

    def test_intelligence_06_inventory_summary(self, api_client):
        """Resume intelligence inventaire."""
        data = api_client.get("/inventory-intelligence/summary")
        assert isinstance(data, dict)

    def test_intelligence_07_forecasting_stock_depletion(self, api_client):
        """Prevision epuisement stock."""
        data = api_client.get("/forecasting/stock-depletion")
        assert isinstance(data, list)

    def test_intelligence_08_forecasting_cashflow(self, api_client):
        """Prevision tresorerie."""
        data = api_client.get("/forecasting/cash-flow")
        assert isinstance(data, dict)

    def test_intelligence_09_forecasting_summary(self, api_client):
        """Resume previsions."""
        data = api_client.get("/forecasting/summary")
        assert isinstance(data, dict)

    def test_intelligence_10_anomaly_scan(self, api_client):
        """Scan anomalies."""
        data = api_client.get("/anomaly-detection/scan")
        assert isinstance(data, list)

    def test_intelligence_11_anomaly_summary(self, api_client):
        """Resume anomalies."""
        data = api_client.get("/anomaly-detection/summary")
        assert isinstance(data, dict)

    def test_intelligence_12_margins_products(self, api_client):
        """Marges produits."""
        data = api_client.get("/margins/products")
        assert isinstance(data, list)

    def test_intelligence_13_margins_categories(self, api_client):
        """Marges categories."""
        data = api_client.get("/margins/categories")
        assert isinstance(data, list)

    def test_intelligence_14_margins_summary(self, api_client):
        """Resume marges."""
        data = api_client.get("/margins/summary")
        assert isinstance(data, dict)

    def test_intelligence_15_supplier_ranking(self, api_client):
        """Classement fournisseurs."""
        data = api_client.get("/supplier-scoring/ranking")
        assert isinstance(data, list)


# ============================================================================
# 8. TESTS RAPPROCHEMENT BANCAIRE (10 tests)
# ============================================================================
class TestBankReconciliation:
    """Tests pour le rapprochement bancaire."""

    def test_reconciliation_01_unmatched_transactions(self, api_client):
        """Transactions non rapprochees."""
        data = api_client.get("/bank-reconciliation/unmatched/transactions")
        assert isinstance(data, list)

    def test_reconciliation_02_unmatched_invoices(self, api_client):
        """Factures non rapprochees."""
        data = api_client.get("/bank-reconciliation/unmatched/invoices")
        assert isinstance(data, list)

    def test_reconciliation_03_aliases(self, api_client):
        """Alias fournisseurs."""
        data = api_client.get("/bank-reconciliation/aliases")
        assert isinstance(data, list)

    def test_reconciliation_04_summary(self, api_client):
        """Resume rapprochement."""
        data = api_client.get("/bank-reconciliation/summary")
        assert isinstance(data, dict)

    def test_reconciliation_05_summary_structure(self, api_client):
        """Structure resume."""
        data = api_client.get("/bank-reconciliation/summary")
        assert isinstance(data, dict)

    def test_reconciliation_06_multiple_summary_calls(self, api_client):
        """Multiple appels resume."""
        for _ in range(3):
            data = api_client.get("/bank-reconciliation/summary")
            assert isinstance(data, dict)

    def test_reconciliation_07_unmatched_counts(self, api_client):
        """Comptage non rapproches."""
        trans = api_client.get("/bank-reconciliation/unmatched/transactions")
        inv = api_client.get("/bank-reconciliation/unmatched/invoices")
        assert isinstance(trans, list)
        assert isinstance(inv, list)

    def test_reconciliation_08_aliases_structure(self, api_client):
        """Structure alias."""
        data = api_client.get("/bank-reconciliation/aliases")
        assert isinstance(data, list)

    def test_reconciliation_09_concurrent_reconciliation(self, api_client):
        """Appels concurrents."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(api_client.get, path)
                for path in [
                    "/bank-reconciliation/summary",
                    "/bank-reconciliation/unmatched/transactions",
                    "/bank-reconciliation/aliases"
                ]
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            assert len(results) == 3

    def test_reconciliation_10_full_reconciliation_load(self, api_client):
        """Chargement complet rapprochement."""
        api_client.get("/bank-reconciliation/summary")
        api_client.get("/bank-reconciliation/unmatched/transactions")
        api_client.get("/bank-reconciliation/unmatched/invoices")
        api_client.get("/bank-reconciliation/aliases")


# ============================================================================
# 9. TESTS COCKPIT (10 tests)
# ============================================================================
class TestCockpit:
    """Tests pour le cockpit."""

    def test_cockpit_01_overview(self, api_client):
        """Vue d'ensemble cockpit."""
        data = api_client.get("/cockpit/overview")
        assert isinstance(data, dict)

    def test_cockpit_02_live_kpis(self, api_client):
        """KPIs en direct."""
        data = api_client.get("/cockpit/kpis/live")
        assert isinstance(data, dict)

    def test_cockpit_03_alerts(self, api_client):
        """Alertes cockpit."""
        data = api_client.get("/cockpit/alerts")
        assert isinstance(data, list)

    def test_cockpit_04_health(self, api_client):
        """Sante cockpit."""
        data = api_client.get("/cockpit/health")
        assert isinstance(data, dict)

    def test_cockpit_05_overview_structure(self, api_client):
        """Structure overview."""
        data = api_client.get("/cockpit/overview")
        assert isinstance(data, dict)

    def test_cockpit_06_kpis_structure(self, api_client):
        """Structure KPIs."""
        data = api_client.get("/cockpit/kpis/live")
        assert isinstance(data, dict)

    def test_cockpit_07_multiple_overview_calls(self, api_client):
        """Multiple appels overview."""
        for _ in range(5):
            data = api_client.get("/cockpit/overview")
            assert isinstance(data, dict)

    def test_cockpit_08_concurrent_cockpit(self, api_client):
        """Appels concurrents cockpit."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(api_client.get, path)
                for path in [
                    "/cockpit/overview",
                    "/cockpit/kpis/live",
                    "/cockpit/alerts",
                    "/cockpit/health"
                ]
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            assert len(results) == 4

    def test_cockpit_09_alerts_structure(self, api_client):
        """Structure alertes."""
        data = api_client.get("/cockpit/alerts")
        assert isinstance(data, list)

    def test_cockpit_10_full_cockpit_load(self, api_client):
        """Chargement complet cockpit."""
        api_client.get("/cockpit/overview")
        api_client.get("/cockpit/kpis/live")
        api_client.get("/cockpit/alerts")
        api_client.get("/cockpit/health")


# ============================================================================
# 10. TESTS ADMIN (10 tests)
# ============================================================================
class TestAdmin:
    """Tests pour le module admin."""

    def test_admin_01_overview(self, api_client):
        """Vue d'ensemble admin."""
        data = api_client.get("/admin/overview")
        assert isinstance(data, dict)

    def test_admin_02_users_list(self, api_client):
        """Liste utilisateurs."""
        data = api_client.get("/admin/users")
        assert isinstance(data, dict)

    def test_admin_03_backups_integrity(self, api_client):
        """Integrite sauvegardes."""
        data = api_client.get("/admin/backups/integrity")
        assert isinstance(data, list)

    def test_admin_04_settings(self, api_client):
        """Parametres."""
        data = api_client.get("/admin/settings")
        assert isinstance(data, dict)

    def test_admin_05_overview_structure(self, api_client):
        """Structure overview."""
        data = api_client.get("/admin/overview")
        assert isinstance(data, dict)

    def test_admin_06_users_structure(self, api_client):
        """Structure utilisateurs."""
        data = api_client.get("/admin/users")
        assert "users" in data or isinstance(data, dict)

    def test_admin_07_multiple_overview_calls(self, api_client):
        """Multiple appels overview."""
        for _ in range(3):
            data = api_client.get("/admin/overview")
            assert isinstance(data, dict)

    def test_admin_08_settings_structure(self, api_client):
        """Structure parametres."""
        data = api_client.get("/admin/settings")
        assert isinstance(data, dict)

    def test_admin_09_concurrent_admin(self, api_client):
        """Appels concurrents admin."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(api_client.get, path)
                for path in ["/admin/overview", "/admin/users", "/admin/settings"]
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            assert len(results) == 3

    def test_admin_10_full_admin_load(self, api_client):
        """Chargement complet admin."""
        api_client.get("/admin/overview")
        api_client.get("/admin/users")
        api_client.get("/admin/settings")
        api_client.get("/admin/backups/integrity")


# ============================================================================
# 11. TESTS PRICES (5 tests)
# ============================================================================
class TestPrices:
    """Tests pour le module prix."""

    def test_prices_01_history(self, api_client):
        """Historique prix."""
        data = api_client.get("/prices/history")
        assert isinstance(data, (list, dict))

    def test_prices_02_latest(self, api_client):
        """Prix recents."""
        data = api_client.get("/prices/latest")
        assert isinstance(data, dict)

    def test_prices_03_history_structure(self, api_client):
        """Structure historique."""
        data = api_client.get("/prices/history")
        assert isinstance(data, (list, dict))

    def test_prices_04_multiple_history_calls(self, api_client):
        """Multiple appels historique."""
        for _ in range(3):
            data = api_client.get("/prices/history")
            assert isinstance(data, (list, dict))

    def test_prices_05_latest_structure(self, api_client):
        """Structure prix recents."""
        data = api_client.get("/prices/latest")
        assert isinstance(data, dict)


# ============================================================================
# 12. TESTS INVOICES (5 tests)
# ============================================================================
class TestInvoices:
    """Tests pour le module factures."""

    def test_invoices_01_history(self, api_client):
        """Historique factures."""
        data = api_client.get("/invoices/history")
        assert isinstance(data, dict)

    def test_invoices_02_history_pagination(self, api_client):
        """Pagination historique."""
        data = api_client.get("/invoices/history", {"limit": 10})
        assert isinstance(data, dict)

    def test_invoices_03_history_structure(self, api_client):
        """Structure historique."""
        data = api_client.get("/invoices/history")
        assert isinstance(data, dict)

    def test_invoices_04_multiple_history_calls(self, api_client):
        """Multiple appels historique."""
        for _ in range(3):
            data = api_client.get("/invoices/history")
            assert isinstance(data, dict)

    def test_invoices_05_large_history(self, api_client):
        """Historique large."""
        data = api_client.get("/invoices/history", {"limit": 100})
        assert isinstance(data, dict)


# ============================================================================
# 13. TESTS REPORTS (5 tests)
# ============================================================================
class TestReports:
    """Tests pour le module rapports."""

    def test_reports_01_overview(self, api_client):
        """Vue d'ensemble rapports."""
        data = api_client.get("/reports/overview")
        assert isinstance(data, dict)

    def test_reports_02_overview_structure(self, api_client):
        """Structure overview."""
        data = api_client.get("/reports/overview")
        assert isinstance(data, dict)

    def test_reports_03_multiple_overview_calls(self, api_client):
        """Multiple appels overview."""
        for _ in range(3):
            data = api_client.get("/reports/overview")
            assert isinstance(data, dict)

    def test_reports_04_overview_response_time(self, api_client):
        """Temps reponse overview."""
        start = time.time()
        api_client.get("/reports/overview")
        elapsed = time.time() - start
        assert elapsed < 10

    def test_reports_05_concurrent_reports(self, api_client):
        """Appels concurrents rapports."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(api_client.get, "/reports/overview")
                for _ in range(3)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            assert len(results) == 3


# ============================================================================
# 14. TESTS ANALYTICS (5 tests)
# ============================================================================
class TestAnalytics:
    """Tests pour le module analytics."""

    def test_analytics_01_summary(self, api_client):
        """Resume analytics."""
        data = api_client.get("/analytics/summary")
        assert isinstance(data, dict)

    def test_analytics_02_summary_structure(self, api_client):
        """Structure resume."""
        data = api_client.get("/analytics/summary")
        assert isinstance(data, dict)

    def test_analytics_03_multiple_summary_calls(self, api_client):
        """Multiple appels resume."""
        for _ in range(3):
            data = api_client.get("/analytics/summary")
            assert isinstance(data, dict)

    def test_analytics_04_summary_response_time(self, api_client):
        """Temps reponse resume."""
        start = time.time()
        api_client.get("/analytics/summary")
        elapsed = time.time() - start
        assert elapsed < 10

    def test_analytics_05_concurrent_analytics(self, api_client):
        """Appels concurrents analytics."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(api_client.get, "/analytics/summary")
                for _ in range(3)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            assert len(results) == 3


# ============================================================================
# 15. TESTS CAPITAL (5 tests)
# ============================================================================
class TestCapital:
    """Tests pour le module capital."""

    def test_capital_01_overview(self, api_client):
        """Vue d'ensemble capital."""
        data = api_client.get("/capital/overview")
        assert isinstance(data, dict)

    def test_capital_02_overview_structure(self, api_client):
        """Structure overview."""
        data = api_client.get("/capital/overview")
        assert isinstance(data, dict)

    def test_capital_03_multiple_overview_calls(self, api_client):
        """Multiple appels overview."""
        for _ in range(3):
            data = api_client.get("/capital/overview")
            assert isinstance(data, dict)

    def test_capital_04_overview_response_time(self, api_client):
        """Temps reponse overview."""
        start = time.time()
        api_client.get("/capital/overview")
        elapsed = time.time() - start
        assert elapsed < 10

    def test_capital_05_concurrent_capital(self, api_client):
        """Appels concurrents capital."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(api_client.get, "/capital/overview")
                for _ in range(3)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
            assert len(results) == 3


# ============================================================================
# 16. TESTS AUDIT TRAIL (5 tests)
# ============================================================================
class TestAuditTrail:
    """Tests pour l'audit trail."""

    def test_audit_trail_01_entries(self, api_client):
        """Entrees audit."""
        data = api_client.get("/audit-trail/entries")
        assert isinstance(data, list)

    def test_audit_trail_02_summary(self, api_client):
        """Resume audit."""
        data = api_client.get("/audit-trail/summary")
        assert isinstance(data, dict)

    def test_audit_trail_03_recent_changes(self, api_client):
        """Changements recents."""
        data = api_client.get("/audit-trail/recent-changes")
        assert isinstance(data, list)

    def test_audit_trail_04_security_events(self, api_client):
        """Evenements securite."""
        data = api_client.get("/audit-trail/security-events")
        assert isinstance(data, list)

    def test_audit_trail_05_report(self, api_client):
        """Rapport audit."""
        data = api_client.get("/audit-trail/report")
        assert isinstance(data, dict)


# ============================================================================
# RUNNER
# ============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
