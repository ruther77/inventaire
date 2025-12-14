"""Tests pour le système de jobs async zero-click."""

from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.schemas.invoices import (
    InvoiceImportSummary,
    ZeroClickJobListResponse,
    ZeroClickJobStatus,
)


class TestZeroClickJobSchemas:
    """Tests pour les schémas Pydantic des jobs."""

    def test_zero_click_job_status_minimal(self):
        """Test création minimale d'un job status."""
        job = ZeroClickJobStatus(
            job_id="test-123",
            status="pending",
        )
        assert job.job_id == "test-123"
        assert job.status == "pending"
        assert job.filename is None
        assert job.summary is None
        assert job.error is None

    def test_zero_click_job_status_complete(self):
        """Test création complète d'un job status."""
        now = datetime.now()
        summary = InvoiceImportSummary(
            rows_received=10,
            movements_created=8,
            quantity_total=100.0,
            errors=[],
        )

        job = ZeroClickJobStatus(
            job_id="test-456",
            status="completed",
            filename="facture.pdf",
            supplier_hint="METRO",
            margin_percent=35.0,
            auto_confirm=True,
            summary=summary,
            created_at=now,
            updated_at=now,
            completed_at=now,
        )

        assert job.job_id == "test-456"
        assert job.status == "completed"
        assert job.filename == "facture.pdf"
        assert job.supplier_hint == "METRO"
        assert job.margin_percent == 35.0
        assert job.auto_confirm is True
        assert job.summary == summary
        assert job.created_at == now

    def test_zero_click_job_status_failed(self):
        """Test job en erreur."""
        job = ZeroClickJobStatus(
            job_id="test-789",
            status="failed",
            error="Fichier invalide",
        )

        assert job.status == "failed"
        assert job.error == "Fichier invalide"
        assert job.summary is None

    def test_zero_click_job_list_response(self):
        """Test de la réponse liste."""
        jobs = [
            ZeroClickJobStatus(job_id=f"job-{i}", status="completed")
            for i in range(5)
        ]

        response = ZeroClickJobListResponse(items=jobs, total=50)

        assert len(response.items) == 5
        assert response.total == 50


class TestZeroClickJobService:
    """Tests pour le service de jobs."""

    @patch("backend.services.zero_click_jobs.execute_raw_sql")
    def test_create_job(self, mock_execute):
        """Test création d'un job."""
        from backend.services import zero_click_jobs

        mock_execute.return_value = [
            ("job-123", "pending", datetime.now())
        ]

        result = zero_click_jobs.create_job(
            job_id="job-123",
            tenant_id=1,
            filename="test.pdf",
            supplier_hint="METRO",
        )

        assert result["job_id"] == "job-123"
        assert result["status"] == "pending"
        mock_execute.assert_called_once()

    @patch("backend.services.zero_click_jobs.execute_raw_sql")
    def test_update_job_status(self, mock_execute):
        """Test mise à jour du statut d'un job."""
        from backend.services import zero_click_jobs

        zero_click_jobs.update_job_status(
            job_id="job-123",
            status="completed",
            result={"rows_received": 10},
        )

        mock_execute.assert_called_once()

    @patch("backend.services.zero_click_jobs.execute_raw_sql")
    def test_get_job(self, mock_execute):
        """Test récupération d'un job."""
        from backend.services import zero_click_jobs

        now = datetime.now()
        mock_execute.return_value = [
            (
                "job-123", 1, "completed", "test.pdf", "METRO",
                40.0, True, '{"rows_received": 10}', None,
                now, now, now
            )
        ]

        result = zero_click_jobs.get_job("job-123", tenant_id=1)

        assert result is not None
        assert result["job_id"] == "job-123"
        assert result["status"] == "completed"
        assert result["filename"] == "test.pdf"
        assert result["result"]["rows_received"] == 10

    @patch("backend.services.zero_click_jobs.execute_raw_sql")
    def test_get_job_not_found(self, mock_execute):
        """Test job introuvable."""
        from backend.services import zero_click_jobs

        mock_execute.return_value = []

        result = zero_click_jobs.get_job("job-999", tenant_id=1)

        assert result is None

    @patch("backend.services.zero_click_jobs.execute_raw_sql")
    def test_list_jobs(self, mock_execute):
        """Test liste des jobs."""
        from backend.services import zero_click_jobs

        now = datetime.now()
        # Mock pour le count
        mock_execute.side_effect = [
            [(100,)],  # Count total
            [  # Jobs
                (
                    f"job-{i}", 1, "completed", f"file-{i}.pdf", None,
                    40.0, True, None, None,
                    now, now, now
                )
                for i in range(10)
            ]
        ]

        jobs, total = zero_click_jobs.list_jobs(
            tenant_id=1,
            limit=10,
            offset=0,
        )

        assert len(jobs) == 10
        assert total == 100
        assert jobs[0]["job_id"] == "job-0"


class TestZeroClickJobEndpoints:
    """Tests pour les endpoints API."""

    def test_job_status_serialization(self):
        """Test sérialisation JSON du job status."""
        job = ZeroClickJobStatus(
            job_id="test-123",
            status="pending",
            filename="test.pdf",
            margin_percent=40.0,
        )

        json_data = job.model_dump()

        assert json_data["job_id"] == "test-123"
        assert json_data["status"] == "pending"
        assert json_data["filename"] == "test.pdf"
        assert json_data["margin_percent"] == 40.0

    def test_job_list_response_serialization(self):
        """Test sérialisation de la liste de jobs."""
        jobs = [
            ZeroClickJobStatus(job_id=f"job-{i}", status="completed")
            for i in range(3)
        ]

        response = ZeroClickJobListResponse(items=jobs, total=3)
        json_data = response.model_dump()

        assert len(json_data["items"]) == 3
        assert json_data["total"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
