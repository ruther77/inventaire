"""
Tests pour l'API Supplier Scoring.

Vérifie:
- Les endpoints retournent le bon format ResponseWrapper
- La pagination fonctionne correctement
- Les validations Pydantic sont appliquées
- Le filtrage multi-tenant fonctionne
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date, timedelta


def test_get_overview_returns_wrapper_format(client, auth_headers):
    """Test que /overview retourne le format ResponseWrapper."""
    response = client.get("/supplier-scoring/overview", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Vérifier le format ResponseWrapper
    assert "success" in data
    assert "data" in data
    assert "error" in data
    assert "meta" in data

    # Vérifier que success est True
    assert data["success"] is True
    assert data["error"] is None

    # Vérifier la structure de data
    overview = data["data"]
    assert "total_suppliers" in overview
    assert "average_score" in overview
    assert "score_distribution" in overview
    assert "top_suppliers" in overview
    assert "bottom_suppliers" in overview
    assert "trends" in overview
    assert "alerts_summary" in overview

    # Vérifier meta
    assert "request_id" in data["meta"]
    assert "duration_ms" in data["meta"]


def test_get_suppliers_list_pagination(client, auth_headers):
    """Test que /suppliers retourne une liste paginée."""
    response = client.get(
        "/supplier-scoring/suppliers?page=1&per_page=10&sort_by=score&order=desc",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    # Vérifier la structure de pagination
    suppliers_list = data["data"]
    assert "suppliers" in suppliers_list
    assert "total_count" in suppliers_list
    assert "page" in suppliers_list
    assert "per_page" in suppliers_list
    assert "total_pages" in suppliers_list

    # Vérifier meta pagination
    assert "pagination" in data["meta"]
    pagination = data["meta"]["pagination"]
    assert pagination["page"] == 1
    assert pagination["per_page"] == 10


def test_get_suppliers_list_filtering(client, auth_headers):
    """Test le filtrage par score minimum et grade."""
    # Filtrer par score minimum
    response = client.get(
        "/supplier-scoring/suppliers?min_score=80",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Vérifier que tous les scores sont >= 80
    suppliers = data["data"]["suppliers"]
    for supplier in suppliers:
        assert supplier["score"] >= 80

    # Filtrer par grade
    response = client.get(
        "/supplier-scoring/suppliers?grade_filter=A",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Vérifier que tous les grades sont A
    suppliers = data["data"]["suppliers"]
    for supplier in suppliers:
        assert supplier["grade"] == "A"


def test_get_supplier_details(client, auth_headers):
    """Test que /suppliers/{id} retourne les détails complets."""
    supplier_id = 101

    response = client.get(
        f"/supplier-scoring/suppliers/{supplier_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    # Vérifier la structure
    details = data["data"]
    assert "supplier_id" in details
    assert "supplier_name" in details
    assert "current_score" in details
    assert "history" in details
    assert "recent_deliveries" in details
    assert "recent_issues" in details
    assert "alerts" in details
    assert "statistics" in details
    assert "recommendations" in details

    # Vérifier current_score
    score = details["current_score"]
    assert "overall_score" in score
    assert "grade" in score
    assert "delivery_score" in score
    assert "quality_score" in score
    assert "price_score" in score
    assert "reliability_score" in score
    assert "trend" in score


def test_get_supplier_history(client, auth_headers):
    """Test que /suppliers/{id}/history retourne l'historique."""
    supplier_id = 101

    response = client.get(
        f"/supplier-scoring/suppliers/{supplier_id}/history?limit=20",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    # Vérifier la structure
    history_data = data["data"]
    assert "supplier_id" in history_data
    assert "supplier_name" in history_data
    assert "history" in history_data
    assert "trend_analysis" in history_data

    # Vérifier trend_analysis
    trend = history_data["trend_analysis"]
    assert "direction" in trend


def test_get_scoring_criteria(client, auth_headers):
    """Test que /criteria retourne les critères de scoring."""
    response = client.get("/supplier-scoring/criteria", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    # Vérifier la structure
    criteria_list = data["data"]
    assert "criteria" in criteria_list
    assert "total_weight" in criteria_list

    # Vérifier que le poids total est 1.0
    assert criteria_list["total_weight"] == 1.0

    # Vérifier les critères
    criteria = criteria_list["criteria"]
    assert len(criteria) == 7  # 7 dimensions

    for criterion in criteria:
        assert "criterion_id" in criterion
        assert "name" in criterion
        assert "weight" in criterion
        assert "description" in criterion
        assert "enabled" in criterion


def test_update_scoring_criteria_valid(client, auth_headers):
    """Test la mise à jour des critères avec des poids valides."""
    payload = {
        "weights": {
            "price_stability": 0.30,
            "delivery_reliability": 0.25,
            "invoice_accuracy": 0.15,
            "stock_accuracy": 0.10,
            "payment_terms": 0.10,
            "responsiveness": 0.05,
            "product_quality": 0.05
        }
    }

    response = client.put(
        "/supplier-scoring/criteria",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    # Vérifier que les poids ont été mis à jour
    criteria_list = data["data"]
    assert criteria_list["total_weight"] == 1.0


def test_update_scoring_criteria_invalid_sum(client, auth_headers):
    """Test la validation du poids total."""
    payload = {
        "weights": {
            "price_stability": 0.50,  # Somme > 1.0
            "delivery_reliability": 0.30,
            "invoice_accuracy": 0.20,
            "stock_accuracy": 0.10,
            "payment_terms": 0.10,
            "responsiveness": 0.05,
            "product_quality": 0.05
        }
    }

    response = client.put(
        "/supplier-scoring/criteria",
        json=payload,
        headers=auth_headers
    )

    # Doit retourner une erreur de validation
    assert response.status_code == 422


def test_get_alerts(client, auth_headers):
    """Test que /alerts retourne la liste des alertes."""
    response = client.get("/supplier-scoring/alerts", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    # Vérifier la structure
    alerts_list = data["data"]
    assert "alerts" in alerts_list
    assert "total_count" in alerts_list
    assert "unacknowledged_count" in alerts_list


def test_get_alerts_filtering(client, auth_headers):
    """Test le filtrage des alertes par sévérité."""
    response = client.get(
        "/supplier-scoring/alerts?severity=critical&acknowledged=false",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    # Vérifier que les alertes sont filtrées
    alerts = data["data"]["alerts"]
    for alert in alerts:
        assert alert["severity"] == "critical"
        assert alert["acknowledged"] is False


def test_recalculate_scores(client, auth_headers):
    """Test le recalcul des scores."""
    payload = {
        "supplier_names": None,  # Tous les fournisseurs
        "period_days": 90,
        "force": False
    }

    response = client.post(
        "/supplier-scoring/recalculate",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    # Vérifier la structure de réponse
    result = data["data"]
    assert "success" in result
    assert "suppliers_processed" in result
    assert "suppliers_failed" in result
    assert "duration_seconds" in result
    assert "errors" in result


def test_record_delivery(client, auth_headers):
    """Test l'enregistrement d'une livraison."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    payload = {
        "supplier_name": "Test Supplier",
        "expected_date": yesterday.isoformat(),
        "actual_date": today.isoformat(),
        "invoice_id": 1001
    }

    response = client.post(
        "/supplier-scoring/delivery",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    # Vérifier la réponse
    result = data["data"]
    assert result["status"] == "ok"
    assert "delay_days" in result
    assert "on_time" in result


def test_record_invoice_issue(client, auth_headers):
    """Test l'enregistrement d'un incident."""
    payload = {
        "supplier_name": "Test Supplier",
        "issue_type": "price_error",
        "severity": "medium",
        "invoice_id": 1001,
        "description": "Prix incorrect sur la facture"
    }

    response = client.post(
        "/supplier-scoring/issue",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    # Vérifier la réponse
    result = data["data"]
    assert result["status"] == "ok"


def test_record_invoice_issue_invalid_type(client, auth_headers):
    """Test la validation du type d'incident."""
    payload = {
        "supplier_name": "Test Supplier",
        "issue_type": "invalid_type",  # Type invalide
        "severity": "medium",
        "invoice_id": 1001
    }

    response = client.post(
        "/supplier-scoring/issue",
        json=payload,
        headers=auth_headers
    )

    # Doit retourner une erreur de validation
    assert response.status_code == 422


def test_compare_suppliers(client, auth_headers):
    """Test la comparaison de fournisseurs."""
    payload = {
        "suppliers": ["Supplier_101", "Supplier_102", "Supplier_103"]
    }

    response = client.post(
        "/supplier-scoring/compare",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    # Vérifier la structure
    comparison = data["data"]
    assert "suppliers" in comparison
    assert "best_overall" in comparison
    assert "best_by_dimension" in comparison

    # Vérifier les fournisseurs
    suppliers = comparison["suppliers"]
    assert len(suppliers) == 3

    for supplier in suppliers:
        assert "supplier_name" in supplier
        assert "overall_score" in supplier
        assert "grade" in supplier
        assert "rank_overall" in supplier
        assert "ranks_by_dimension" in supplier


# ============================================================================
# LEGACY ENDPOINTS TESTS
# ============================================================================

def test_legacy_score_endpoint(client, auth_headers):
    """Test l'endpoint legacy /score/{supplier_name}."""
    response = client.get(
        "/supplier-scoring/score/Test%20Supplier?period_days=90",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "supplier_name" in data["data"]
    assert "overall_score" in data["data"]


def test_legacy_ranking_endpoint(client, auth_headers):
    """Test l'endpoint legacy /ranking."""
    response = client.get("/supplier-scoring/ranking", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_legacy_dimensions_endpoint(client, auth_headers):
    """Test l'endpoint legacy /dimensions."""
    response = client.get("/supplier-scoring/dimensions", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "dimensions" in data["data"]


def test_legacy_history_endpoint(client, auth_headers):
    """Test l'endpoint legacy /history/{supplier_name}."""
    response = client.get(
        "/supplier-scoring/history/Test%20Supplier?limit=20",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "supplier_name" in data["data"]
    assert "history" in data["data"]


# ============================================================================
# FIXTURES (à adapter selon votre config de test)
# ============================================================================

@pytest.fixture
def client():
    """Fixture pour le client de test FastAPI."""
    from backend.main import app
    from fastapi.testclient import TestClient

    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Fixture pour les headers d'authentification."""
    # À adapter selon votre système d'auth
    # Exemple: générer un token JWT valide
    return {
        "Authorization": "Bearer test_token"
    }
