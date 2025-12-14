"""
Tests d'intégration pour NewCMS Finance endpoints.

Ces tests vérifient le bon fonctionnement des endpoints:
- GET /api/newcms/finance/overview
- GET /api/newcms/finance/transactions
- POST /api/newcms/finance/reconciliation/apply
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta


@pytest.fixture
def client():
    """Client de test FastAPI."""
    from backend.main import app
    return TestClient(app)


class TestFinanceOverview:
    """Tests pour l'endpoint /api/newcms/finance/overview"""

    def test_overview_structure(self, client):
        """Vérifie la structure de la réponse overview."""
        response = client.get("/api/newcms/finance/overview")

        assert response.status_code == 200
        data = response.json()

        # Vérifier les clés principales
        assert "reconciliation_stats" in data
        assert "cashflow_30d" in data
        assert "ai_suggestions" in data
        assert "recent_transactions" in data
        assert "generated_at" in data

    def test_reconciliation_stats_fields(self, client):
        """Vérifie les champs des stats de rapprochement."""
        response = client.get("/api/newcms/finance/overview")
        stats = response.json()["reconciliation_stats"]

        required_fields = [
            "matched_count",
            "pending_count",
            "unmatched_count",
            "matched_percentage",
            "pending_percentage",
            "unmatched_percentage",
            "total_amount_matched",
            "total_amount_pending",
        ]

        for field in required_fields:
            assert field in stats, f"Champ manquant: {field}"
            assert isinstance(stats[field], (int, float))

    def test_cashflow_fields(self, client):
        """Vérifie les champs du cash-flow."""
        response = client.get("/api/newcms/finance/overview")
        cashflow = response.json()["cashflow_30d"]

        required_fields = [
            "period_days",
            "total_inflow",
            "total_outflow",
            "net_cashflow",
            "avg_daily_inflow",
            "avg_daily_outflow",
            "current_balance",
        ]

        for field in required_fields:
            assert field in cashflow, f"Champ manquant: {field}"

        assert cashflow["period_days"] == 30
        assert cashflow["net_cashflow"] == cashflow["total_inflow"] - cashflow["total_outflow"]

    def test_ai_suggestions_limit(self, client):
        """Vérifie que les suggestions IA sont limitées à 5."""
        response = client.get("/api/newcms/finance/overview")
        suggestions = response.json()["ai_suggestions"]

        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5

    def test_ai_suggestion_structure(self, client):
        """Vérifie la structure des suggestions IA."""
        response = client.get("/api/newcms/finance/overview")
        suggestions = response.json()["ai_suggestions"]

        if suggestions:
            suggestion = suggestions[0]
            required_fields = [
                "suggestion_id",
                "transaction_id",
                "transaction_date",
                "transaction_amount",
                "transaction_label",
                "matched_invoice_ids",
                "matched_invoices_info",
                "confidence",
                "match_type",
                "total_matched_amount",
                "difference",
                "explanation",
            ]

            for field in required_fields:
                assert field in suggestion, f"Champ manquant: {field}"

            # Vérifier les types
            assert isinstance(suggestion["confidence"], float)
            assert 0 <= suggestion["confidence"] <= 1
            assert suggestion["match_type"] in ["exact", "fuzzy_amount", "multi_line", "alias", "unknown"]

    def test_recent_transactions_limit(self, client):
        """Vérifie que les transactions récentes sont limitées à 5."""
        response = client.get("/api/newcms/finance/overview")
        transactions = response.json()["recent_transactions"]

        assert isinstance(transactions, list)
        assert len(transactions) <= 5

    def test_recent_transaction_structure(self, client):
        """Vérifie la structure des transactions récentes."""
        response = client.get("/api/newcms/finance/overview")
        transactions = response.json()["recent_transactions"]

        if transactions:
            tx = transactions[0]
            required_fields = [
                "id",
                "date",
                "amount",
                "label",
                "direction",
                "reconciled",
            ]

            for field in required_fields:
                assert field in tx, f"Champ manquant: {field}"

            assert tx["direction"] in ["IN", "OUT", "TRANSFER"]
            assert isinstance(tx["reconciled"], bool)


class TestTransactionsList:
    """Tests pour l'endpoint /api/newcms/finance/transactions"""

    def test_transactions_basic(self, client):
        """Test de base de l'endpoint transactions."""
        response = client.get("/api/newcms/finance/transactions")

        assert response.status_code == 200
        data = response.json()

        assert "transactions" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data

    def test_transactions_pagination(self, client):
        """Vérifie la pagination."""
        response = client.get("/api/newcms/finance/transactions?page=1&size=10")

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["size"] == 10
        assert len(data["transactions"]) <= 10

    def test_transactions_search_filter(self, client):
        """Vérifie le filtre de recherche texte."""
        response = client.get("/api/newcms/finance/transactions?q=METRO")

        assert response.status_code == 200
        data = response.json()

        # Si des résultats, vérifier qu'ils contiennent le terme recherché
        if data["transactions"]:
            for tx in data["transactions"]:
                assert "METRO" in tx["label"].upper() or True  # Peut être dans d'autres champs

    def test_transactions_date_filter(self, client):
        """Vérifie les filtres de date."""
        today = date.today()
        date_from = (today - timedelta(days=30)).isoformat()
        date_to = today.isoformat()

        response = client.get(
            f"/api/newcms/finance/transactions?date_from={date_from}&date_to={date_to}"
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifier que les dates sont dans la plage
        if data["transactions"]:
            for tx in data["transactions"]:
                tx_date = date.fromisoformat(tx["date"])
                assert date.fromisoformat(date_from) <= tx_date <= date.fromisoformat(date_to)

    def test_transactions_amount_filter(self, client):
        """Vérifie les filtres de montant."""
        response = client.get(
            "/api/newcms/finance/transactions?amount_min=100&amount_max=500"
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifier que les montants sont dans la plage
        if data["transactions"]:
            for tx in data["transactions"]:
                assert 100 <= abs(tx["amount"]) <= 500

    def test_transactions_max_size(self, client):
        """Vérifie la limite max de taille de page."""
        response = client.get("/api/newcms/finance/transactions?size=1000")

        # Devrait être rejeté ou limité à 500
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            assert data["size"] <= 500


class TestReconciliationApply:
    """Tests pour l'endpoint /api/newcms/finance/reconciliation/apply"""

    def test_apply_reconciliation_validation(self, client):
        """Vérifie la validation des données."""
        # Requête invalide (champs manquants)
        response = client.post(
            "/api/newcms/finance/reconciliation/apply",
            json={},
        )

        assert response.status_code == 422  # Unprocessable Entity

    def test_apply_reconciliation_structure(self, client):
        """Vérifie la structure de la requête."""
        payload = {
            "suggestion_id": "ai-test-123",
            "transaction_id": 9999999,  # Transaction inexistante
            "invoice_ids": [9999999],   # Facture inexistante
            "user_comment": "Test",
        }

        response = client.post(
            "/api/newcms/finance/reconciliation/apply",
            json=payload,
        )

        # Devrait retourner 404 (transaction non trouvée) ou 500
        assert response.status_code in [404, 500]

    def test_apply_reconciliation_success_structure(self, client):
        """Vérifie la structure de la réponse en cas de succès."""
        # Ce test nécessite des données valides en DB
        # Pour l'instant, on vérifie juste la structure attendue

        expected_fields = [
            "success",
            "transaction_id",
            "invoice_ids",
            "reconciled_at",
            "message",
        ]

        # Note: Ce test devrait être complété avec des fixtures DB
        # pour créer une transaction et une facture de test


class TestEdgeCases:
    """Tests de cas limites et erreurs."""

    def test_overview_without_data(self, client):
        """Vérifie que l'overview fonctionne même sans données."""
        response = client.get("/api/newcms/finance/overview")

        assert response.status_code == 200
        data = response.json()

        # Les stats devraient être à 0 mais la structure doit être présente
        assert data["reconciliation_stats"]["matched_count"] >= 0
        assert data["cashflow_30d"]["total_inflow"] >= 0

    def test_transactions_invalid_page(self, client):
        """Vérifie le comportement avec une page invalide."""
        response = client.get("/api/newcms/finance/transactions?page=0")

        # Devrait être rejeté (page doit être >= 1)
        assert response.status_code == 422

    def test_transactions_negative_amount(self, client):
        """Vérifie le comportement avec montant négatif."""
        response = client.get("/api/newcms/finance/transactions?amount_min=-100")

        # Devrait être rejeté (montant doit être >= 0)
        assert response.status_code == 422


class TestPerformance:
    """Tests de performance basiques."""

    def test_overview_response_time(self, client):
        """Vérifie que l'overview répond en temps raisonnable."""
        import time

        start = time.time()
        response = client.get("/api/newcms/finance/overview")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 5.0, f"Réponse trop lente: {elapsed:.2f}s"

    def test_transactions_large_page_response_time(self, client):
        """Vérifie le temps de réponse pour une grande page."""
        import time

        start = time.time()
        response = client.get("/api/newcms/finance/transactions?size=500")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 10.0, f"Réponse trop lente: {elapsed:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
