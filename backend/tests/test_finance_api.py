"""Comprehensive tests for finance API endpoints."""

from __future__ import annotations

import io
from datetime import date
from unittest.mock import patch

import pytest


# ============================================================================
# Tests pagination
# ============================================================================


def test_transactions_search_pagination(authenticated_client):
    """Test que la pagination fonctionne correctement."""
    with patch("backend.services.finance_transactions.search_transactions") as mock_search:
        mock_search.return_value = {
            "items": [
                {
                    "id": 1,
                    "entity_id": 1,
                    "account_id": 1,
                    "date_operation": "2025-01-01",
                    "amount": 100.0,
                    "direction": "OUT",
                },
                {
                    "id": 2,
                    "entity_id": 1,
                    "account_id": 1,
                    "date_operation": "2025-01-02",
                    "amount": 200.0,
                    "direction": "OUT",
                },
            ],
            "page": 1,
            "size": 10,
            "total": 25,
            "sort": "-date_operation",
            "filters_applied": {},
        }

        response = authenticated_client.get("/finance/transactions/search?page=1&size=10")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "page" in data
        assert "size" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["size"] == 10
        assert data["total"] == 25
        assert len(data["items"]) == 2
        assert data["items"][0]["id"] == 1


def test_transactions_search_pagination_bounds(authenticated_client):
    """Test les limites de pagination (page négative, size > 500)."""
    with patch("backend.services.finance_transactions.search_transactions") as mock_search:
        # Test page négative
        response = authenticated_client.get("/finance/transactions/search?page=0&size=10")
        assert response.status_code == 422  # Validation error

        # Test size > 500
        response = authenticated_client.get("/finance/transactions/search?page=1&size=1000")
        assert response.status_code == 422  # Validation error

        # Test size = 500 (should work)
        mock_search.return_value = {
            "items": [],
            "page": 1,
            "size": 500,
            "total": 0,
            "sort": "-date_operation",
            "filters_applied": {},
        }
        response = authenticated_client.get("/finance/transactions/search?page=1&size=500")
        assert response.status_code == 200


def test_bank_statements_search_pagination(authenticated_client):
    """Test pagination des relevés bancaires."""
    with patch("backend.services.finance_bank_statements.search_bank_statements") as mock_search:
        mock_search.return_value = {
            "items": [
                {
                    "id": 1,
                    "account_id": 1,
                    "period_start": "2025-01-01",
                    "period_end": "2025-01-31",
                    "status": "IMPORTED",
                }
            ],
            "page": 2,
            "size": 20,
            "total": 50,
            "sort": "-imported_at",
            "filters_applied": {},
        }

        response = authenticated_client.get("/finance/bank-statements/search?page=2&size=20")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["size"] == 20
        assert data["total"] == 50
        assert len(data["items"]) == 1


def test_invoices_search_pagination(authenticated_client):
    """Test pagination des factures."""
    with patch("backend.services.finance_invoices.search_invoices") as mock_search:
        mock_search.return_value = {
            "items": [
                {
                    "id": 1,
                    "entity_id": 1,
                    "vendor_id": 1,
                    "invoice_number": "INV-001",
                    "date_invoice": "2025-01-15",
                    "montant_ttc": 500.0,
                    "status": "EN_ATTENTE",
                }
            ],
            "page": 1,
            "size": 50,
            "total": 100,
            "sort": "-date_invoice",
            "filters_applied": {},
        }

        response = authenticated_client.get("/finance/invoices/search?page=1&size=50")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 50
        assert data["total"] == 100


# ============================================================================
# Tests filtres
# ============================================================================


def test_transactions_search_filters(authenticated_client):
    """Test les filtres de recherche transactions."""
    with patch("backend.services.finance_transactions.search_transactions") as mock_search:
        mock_search.return_value = {
            "items": [
                {
                    "id": 3,
                    "entity_id": 1,
                    "account_id": 2,
                    "category_id": 5,
                    "date_operation": "2025-01-10",
                    "amount": 150.0,
                    "direction": "OUT",
                    "note": "Payment ACME",
                }
            ],
            "page": 1,
            "size": 50,
            "total": 1,
            "sort": "-date_operation",
            "filters_applied": {
                "entity_id": 1,
                "account_id": 2,
                "category_id": 5,
                "date_from": "2025-01-01",
                "date_to": "2025-01-31",
                "q": "ACME",
            },
        }

        response = authenticated_client.get(
            "/finance/transactions/search"
            "?entity_id=1"
            "&account_id=2"
            "&category_id=5"
            "&date_from=2025-01-01"
            "&date_to=2025-01-31"
            "&q=ACME"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["account_id"] == 2
        assert data["items"][0]["category_id"] == 5

        # Verify filters were passed to service
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs["entity_id"] == 1
        assert call_kwargs["account_id"] == 2
        assert call_kwargs["category_id"] == 5
        assert call_kwargs["date_from"] == "2025-01-01"
        assert call_kwargs["date_to"] == "2025-01-31"
        assert call_kwargs["q"] == "ACME"


def test_transactions_search_amount_filters(authenticated_client):
    """Test les filtres de montant min/max."""
    with patch("backend.services.finance_transactions.search_transactions") as mock_search:
        mock_search.return_value = {
            "items": [],
            "page": 1,
            "size": 50,
            "total": 0,
            "sort": "-date_operation",
            "filters_applied": {"amount_min": 100.0, "amount_max": 500.0},
        }

        response = authenticated_client.get("/finance/transactions/search?amount_min=100&amount_max=500")

        assert response.status_code == 200
        mock_search.assert_called_once()
        call_kwargs = mock_search.call_args.kwargs
        assert call_kwargs["amount_min"] == 100.0
        assert call_kwargs["amount_max"] == 500.0


def test_transactions_search_sorting(authenticated_client):
    """Test le tri des transactions."""
    with patch("backend.services.finance_transactions.search_transactions") as mock_search:
        # Test tri descendant par date
        mock_search.return_value = {
            "items": [
                {"id": 2, "date_operation": "2025-01-02", "amount": 200.0},
                {"id": 1, "date_operation": "2025-01-01", "amount": 100.0},
            ],
            "page": 1,
            "size": 50,
            "total": 2,
            "sort": "-date_operation",
            "filters_applied": {},
        }

        response = authenticated_client.get("/finance/transactions/search?sort=-date_operation")
        assert response.status_code == 200
        data = response.json()
        assert data["sort"] == "-date_operation"
        assert data["items"][0]["id"] == 2
        assert data["items"][1]["id"] == 1

        # Test tri ascendant par montant
        mock_search.return_value["sort"] = "amount"
        mock_search.return_value["items"] = [
            {"id": 1, "date_operation": "2025-01-01", "amount": 100.0},
            {"id": 2, "date_operation": "2025-01-02", "amount": 200.0},
        ]

        response = authenticated_client.get("/finance/transactions/search?sort=amount")
        assert response.status_code == 200
        data = response.json()
        assert data["sort"] == "amount"


# ============================================================================
# Tests batch categorize
# ============================================================================


def test_batch_categorize_by_ids(authenticated_client):
    """Test recatégorisation par IDs."""
    with patch("backend.services.finance_transactions.batch_categorize") as mock_batch:
        mock_batch.return_value = {
            "updated": 3,
            "transaction_ids": [10, 11, 12],
            "category_id": 5,
        }

        payload = {"transaction_ids": [10, 11, 12], "category_id": 5}

        response = authenticated_client.post("/finance/transactions/batch-categorize", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["updated"] == 3
        assert data["category_id"] == 5
        assert len(data["transaction_ids"]) == 3


def test_batch_categorize_by_rule(authenticated_client):
    """Test recatégorisation par règle."""
    with patch("backend.services.finance_transactions.batch_categorize") as mock_batch:
        mock_batch.return_value = {
            "updated": 15,
            "category_id": 7,
            "rule_applied": {"keywords": ["AMAZON", "AWS"], "apply_to_autre_only": True},
        }

        payload = {
            "category_id": 7,
            "rule": {"keywords": ["AMAZON", "AWS"], "apply_to_autre_only": True},
        }

        response = authenticated_client.post("/finance/transactions/batch-categorize", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["updated"] == 15
        assert data["category_id"] == 7
        assert "rule_applied" in data


def test_batch_categorize_validation_error(authenticated_client):
    """Test erreur de validation (ni IDs ni règle)."""
    with patch("backend.services.finance_transactions.batch_categorize") as mock_batch:
        mock_batch.side_effect = ValueError("Either transaction_ids or rule must be provided")

        payload = {"category_id": 5}  # Missing both transaction_ids and rule

        response = authenticated_client.post("/finance/transactions/batch-categorize", json=payload)

        assert response.status_code == 400
        assert "Either transaction_ids or rule must be provided" in response.json()["detail"]


# ============================================================================
# Tests suggestions
# ============================================================================


def test_suggestions_autre_top(authenticated_client):
    """Test suggestions des libellés fréquents non catégorisés."""
    with patch("backend.services.finance_transactions.suggest_autre_top") as mock_suggest:
        mock_suggest.return_value = [
            {"key": "AMAZON MARKETPLACE", "count": 25, "examples": ["AMAZON MARKETPLACE EUR", "AMAZON MKTP"]},
            {"key": "EDF FACTURE", "count": 12, "examples": ["EDF FACTURE 123", "EDF FACTURE 456"]},
            {"key": "GOOGLE CLOUD", "count": 8, "examples": ["GOOGLE CLOUD PLATFORM"]},
        ]

        response = authenticated_client.get("/finance/categories/suggestions/autre-top")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["key"] == "AMAZON MARKETPLACE"
        assert data[0]["count"] == 25
        assert len(data[0]["examples"]) >= 1
        assert data[1]["count"] == 12


def test_suggestions_autre_top_with_limit(authenticated_client):
    """Test suggestions avec limite personnalisée."""
    with patch("backend.services.finance_transactions.suggest_autre_top") as mock_suggest:
        mock_suggest.return_value = [
            {"key": "TEST1", "count": 100, "examples": ["TEST1"]},
            {"key": "TEST2", "count": 50, "examples": ["TEST2"]},
        ]

        response = authenticated_client.get("/finance/categories/suggestions/autre-top?limit=2")

        assert response.status_code == 200
        mock_suggest.assert_called_once()
        call_kwargs = mock_suggest.call_args.kwargs
        assert call_kwargs["limit"] == 2


def test_categories_autocomplete(authenticated_client):
    """Test autocomplete catégories."""
    with patch("backend.services.finance_transactions.autocomplete_categories") as mock_autocomplete:
        mock_autocomplete.return_value = [
            {"id": 1, "label": "Alimentation", "parent_id": None},
            {"id": 2, "label": "Alimentation Bio", "parent_id": 1},
        ]

        response = authenticated_client.get("/finance/categories/suggestions/complete?q=ali")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["label"] == "Alimentation"
        assert data[1]["parent_id"] == 1


def test_categories_autocomplete_missing_query(authenticated_client):
    """Test autocomplete sans paramètre de recherche."""
    response = authenticated_client.get("/finance/categories/suggestions/complete")

    assert response.status_code == 422  # Validation error - q is required


def test_categories_list(authenticated_client):
    """Test liste complète des catégories."""
    with patch("backend.services.finance_categories.list_categories") as mock_list:
        mock_list.return_value = [
            {"id": 1, "label": "Alimentation", "is_active": True},
            {"id": 2, "label": "Transport", "is_active": True},
            {"id": 3, "label": "Autre", "is_active": True},
        ]

        response = authenticated_client.get("/finance/categories")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(cat["is_active"] for cat in data)


# ============================================================================
# Tests import CSV
# ============================================================================


def _make_multipart_body(filename: str, content: bytes, content_type: str = "text/csv") -> tuple[bytes, str]:
    """Helper to create multipart body for file uploads.

    Works around httpx 0.28+ TestClient file upload issues.
    Returns (body_bytes, content_type_header).
    """
    import uuid
    boundary = f"----pytest{uuid.uuid4().hex}"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n"
        f"\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def test_import_csv_format(authenticated_client):
    """Test import avec format CSV valide."""
    with patch("backend.api.finance.bank_statement_csv.import_csv") as mock_import:
        with patch("backend.api.finance.finance_rules.record_import"):
            with patch("backend.api.finance.finance_metrics.record_import_metrics"):
                mock_import.return_value = {
                    "inserted": 10,
                    "total": 12,
                    "skipped": 2,
                    "errors": 0,
                }

                csv_content = b"date,label,amount\n2025-01-01,Payment ACME,-100.50\n2025-01-02,Salary,2500.00\n"
                body, content_type = _make_multipart_body("statement.csv", csv_content)

                response = authenticated_client.post(
                    "/finance/bank-statements/import?account_id=1",
                    content=body,
                    headers={"Content-Type": content_type},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["inserted"] == 10
                assert data["total"] == 12
                assert data["skipped"] == 2


def test_import_csv_invalid(authenticated_client):
    """Test import avec format invalide."""
    with patch("backend.api.finance.bank_statement_csv.import_csv") as mock_import:
        with patch("backend.api.finance.finance_rules.record_import"):
            with patch("backend.api.finance.finance_metrics.record_import_metrics"):
                mock_import.side_effect = ValueError("Invalid CSV format: missing required columns")

                csv_content = b"invalid,header\ndata,here\n"
                body, content_type = _make_multipart_body("invalid.csv", csv_content)

                response = authenticated_client.post(
                    "/finance/bank-statements/import?account_id=1",
                    content=body,
                    headers={"Content-Type": content_type},
                )

                assert response.status_code == 400
                assert "Invalid CSV format" in response.json()["detail"]


def test_import_csv_missing_account_id(authenticated_client):
    """Test import sans account_id."""
    csv_content = b"date,label,amount\n"
    body, content_type = _make_multipart_body("statement.csv", csv_content)

    response = authenticated_client.post(
        "/finance/bank-statements/import",
        content=body,
        headers={"Content-Type": content_type},
    )

    assert response.status_code == 422  # Validation error - account_id is required


# ============================================================================
# Tests reconciliation
# ============================================================================


def test_reconciliation_run(authenticated_client):
    """Test lancement réconciliation."""
    with patch("backend.services.finance.run_reconciliation") as mock_run:
        with patch("backend.services.finance_metrics.record_reco_run"):
            mock_run.return_value = {
                "run_id": 42,
                "statements_scanned": 100,
                "documents_available": 80,
                "matches_created": 35,
                "auto_matches": 20,
            }

            payload = {
                "amount_tolerance": 5.0,
                "max_days_difference": 15,
                "auto_threshold": 0.95,
            }

            response = authenticated_client.post("/finance/reconciliation/run", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["run_id"] == 42
            assert data["statements_scanned"] == 100
            assert data["matches_created"] == 35
            assert data["auto_matches"] == 20


def test_reconciliation_run_default_params(authenticated_client):
    """Test réconciliation avec paramètres par défaut."""
    with patch("backend.services.finance.run_reconciliation") as mock_run:
        with patch("backend.services.finance_metrics.record_reco_run"):
            mock_run.return_value = {
                "run_id": 1,
                "statements_scanned": 50,
                "documents_available": 40,
                "matches_created": 15,
                "auto_matches": 10,
            }

            response = authenticated_client.post("/finance/reconciliation/run", json={})

            assert response.status_code == 200
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args.kwargs
            assert call_kwargs["amount_tolerance"] == 2.0  # Default
            assert call_kwargs["max_days_difference"] == 10  # Default
            assert call_kwargs["auto_threshold"] == 0.9  # Default


def test_reconciliation_matches(authenticated_client):
    """Test liste des matches."""
    with patch("backend.services.finance.list_matches") as mock_list:
        mock_list.return_value = [
            {
                "id": 1,
                "status": "pending",
                "match_type": "exact",
                "score": 0.95,
                "amount_diff": 0.0,
                "days_diff": 1,
                "explanation": "Exact match",
                "bank_id": 100,
                "bank_date": date(2025, 1, 15),
                "bank_label": "Payment ACME",
                "bank_amount": 100.0,
                "bank_raw_amount": 100.0,
                "bank_account": "Main Account",
                "bank_category": None,
                "document_id": 50,
                "invoice_reference": "INV-2025-001",
                "invoice_number": "INV001",
                "supplier_name": "ACME Corp",
                "invoice_date": date(2025, 1, 14),
                "total_incl_tax": 100.0,
                "total_excl_tax": 83.33,
            }
        ]

        response = authenticated_client.get("/finance/reconciliation/matches?status=pending")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["status"] == "pending"
        assert data[0]["score"] == 0.95
        assert data[0]["bank"]["label"] == "Payment ACME"
        assert data[0]["invoice"]["supplier_name"] == "ACME Corp"


def test_reconciliation_matches_all_statuses(authenticated_client):
    """Test matches sans filtre de statut."""
    with patch("backend.services.finance.list_matches") as mock_list:
        mock_list.return_value = []

        response = authenticated_client.get("/finance/reconciliation/matches?status=all")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


def test_reconciliation_update_match_status(authenticated_client):
    """Test mise à jour du statut d'un match."""
    with patch("backend.services.finance.update_match_status") as mock_update:
        mock_update.return_value = {
            "id": 1,
            "status": "confirmed",
            "match_type": "exact",
            "score": 0.95,
            "amount_diff": 0.0,
            "days_diff": 1,
            "explanation": "Manually confirmed",
            "bank_id": 100,
            "bank_date": date(2025, 1, 15),
            "bank_label": "Payment ACME",
            "bank_amount": 100.0,
            "bank_raw_amount": 100.0,
            "bank_account": "Main Account",
            "bank_category": None,
            "document_id": 50,
            "invoice_reference": "INV-2025-001",
            "invoice_number": "INV001",
            "supplier_name": "ACME Corp",
            "invoice_date": date(2025, 1, 14),
            "total_incl_tax": 100.0,
            "total_excl_tax": 83.33,
        }

        payload = {"status": "confirmed", "note": "Verified manually"}

        response = authenticated_client.post("/finance/reconciliation/1/status", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"


def test_reconciliation_update_match_not_found(authenticated_client):
    """Test mise à jour d'un match inexistant."""
    with patch("backend.services.finance.update_match_status") as mock_update:
        mock_update.side_effect = ValueError("Match not found")

        payload = {"status": "confirmed"}

        response = authenticated_client.post("/finance/reconciliation/9999/status", json=payload)

        assert response.status_code == 404
        assert "Match not found" in response.json()["detail"]


# ============================================================================
# Tests CRUD de base
# ============================================================================


def test_create_account(authenticated_client):
    """Test création d'un compte."""
    with patch("backend.services.finance_accounts.create_account") as mock_create:
        mock_create.return_value = {
            "id": 1,
            "entity_id": 1,
            "type": "BANK",
            "label": "Main Account",
            "iban": "FR1234567890",
            "currency": "EUR",
            "is_active": True,
        }

        payload = {
            "entity_id": 1,
            "type": "BANK",
            "label": "Main Account",
            "iban": "FR1234567890",
            "currency": "EUR",
        }

        response = authenticated_client.post("/finance/accounts", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["label"] == "Main Account"


def test_list_accounts(authenticated_client):
    """Test liste des comptes."""
    with patch("backend.services.finance_accounts.list_accounts") as mock_list:
        mock_list.return_value = [
            {"id": 1, "label": "Main Account", "type": "BANK", "is_active": True},
            {"id": 2, "label": "Savings", "type": "BANK", "is_active": True},
        ]

        response = authenticated_client.get("/finance/accounts")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


def test_create_transaction(authenticated_client):
    """Test création d'une transaction."""
    with patch("backend.services.finance_transactions.create_transaction") as mock_create:
        mock_create.return_value = {
            "id": 1,
            "entity_id": 1,
            "account_id": 1,
            "direction": "OUT",
            "amount": 100.0,
            "date_operation": "2025-01-15",
        }

        payload = {
            "entity_id": 1,
            "account_id": 1,
            "direction": "OUT",
            "source": "MANUAL",
            "date_operation": "2025-01-15",
            "amount": 100.0,
        }

        response = authenticated_client.post("/finance/transactions", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1


def test_update_transaction(authenticated_client):
    """Test mise à jour d'une transaction."""
    with patch("backend.services.finance_transactions.update_transaction") as mock_update:
        mock_update.return_value = {
            "id": 1,
            "note": "Updated note",
            "status": "CONFIRMED",
        }

        payload = {"note": "Updated note", "status": "CONFIRMED"}

        response = authenticated_client.patch("/finance/transactions/1", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["note"] == "Updated note"


def test_lock_transaction(authenticated_client):
    """Test verrouillage d'une transaction."""
    with patch("backend.services.finance_transactions.lock_transaction") as mock_lock:
        mock_lock.return_value = {"id": 1, "locked": True}

        response = authenticated_client.post("/finance/transactions/1/lock")

        assert response.status_code == 200
        data = response.json()
        assert data["locked"] is True


# ============================================================================
# Tests récurrences et anomalies
# ============================================================================


def test_refresh_recurring(authenticated_client):
    """Test rafraîchissement des dépenses récurrentes."""
    with patch("backend.services.finance.refresh_recurring") as mock_refresh:
        mock_refresh.return_value = {"recurring_expenses": 15}

        payload = {"min_occurrences": 3}

        response = authenticated_client.post("/finance/recurring/refresh", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["recurring_expenses"] == 15


def test_list_recurring(authenticated_client):
    """Test liste des dépenses récurrentes."""
    with patch("backend.services.finance.list_recurring") as mock_list:
        mock_list.return_value = [
            {
                "id": 1,
                "normalized_label": "EDF",
                "sample_label": "EDF FACTURE 123",
                "account": "Main",
                "category": "Utilities",
                "periodicity": "MONTHLY",
                "occurrences": 12,
                "avg_amount": 85.5,
                "std_amount": 5.2,
                "first_date": date(2024, 1, 15),
                "last_date": date(2025, 1, 15),
            }
        ]

        response = authenticated_client.get("/finance/recurring")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["normalized_label"] == "EDF"
        assert data[0]["occurrences"] == 12


def test_refresh_anomalies(authenticated_client):
    """Test détection d'anomalies."""
    with patch("backend.services.finance.refresh_anomalies") as mock_refresh:
        mock_refresh.return_value = {"anomalies": 5}

        payload = {"zscore_threshold": 2.5, "min_occurrences": 3}

        response = authenticated_client.post("/finance/anomalies/refresh", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["anomalies"] == 5


def test_list_anomalies(authenticated_client):
    """Test liste des anomalies."""
    with patch("backend.services.finance.list_anomalies") as mock_list:
        mock_list.return_value = [
            {
                "id": 1,
                "rule": "amount_deviation",
                "severity": "HIGH",
                "message": "Amount significantly higher than usual",
                "score": 3.5,
                "amount": 500.0,
                "expected_amount": 85.0,
                "statement_id": 100,
                "statement_date": date(2025, 1, 15),
                "statement_label": "EDF FACTURE 999",
                "statement_account": "Main",
                "statement_category": "Utilities",
            }
        ]

        response = authenticated_client.get("/finance/anomalies?severity=HIGH")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["severity"] == "HIGH"
        assert data[0]["amount"] == 500.0


# ============================================================================
# Tests edge cases
# ============================================================================


def test_transactions_search_no_results(authenticated_client):
    """Test recherche sans résultats."""
    with patch("backend.services.finance_transactions.search_transactions") as mock_search:
        mock_search.return_value = {
            "items": [],
            "page": 1,
            "size": 50,
            "total": 0,
            "sort": "-date_operation",
            "filters_applied": {},
        }

        response = authenticated_client.get("/finance/transactions/search?q=NONEXISTENT")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 0


def test_reconciliation_matches_empty(authenticated_client):
    """Test matches vide quand la table n'existe pas."""
    with patch("backend.services.finance.list_matches") as mock_list:
        mock_list.side_effect = Exception("Table does not exist")

        response = authenticated_client.get("/finance/reconciliation/matches")

        assert response.status_code == 200
        data = response.json()
        assert data == []  # Should return empty list on error


def test_anomalies_optional_table_missing(authenticated_client):
    """Test anomalies quand la table optionnelle est absente."""
    with patch("backend.services.finance.list_anomalies") as mock_list:
        mock_list.side_effect = Exception("Anomalies table does not exist")

        response = authenticated_client.get("/finance/anomalies")

        assert response.status_code == 200
        data = response.json()
        assert data == []  # Should return empty list on error
