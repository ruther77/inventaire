"""
Tests pour l'API Anomaly Detection.
Coverage des endpoints critiques de détection d'anomalies.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from fastapi import HTTPException
from backend.api.anomaly_detection import (
    scan_for_anomalies,
    detect_transaction_outliers,
    detect_duplicate_invoices,
    detect_invoice_sequence_gaps,
    detect_round_amounts,
    get_anomaly_summary,
    resolve_anomaly,
)
from core.finance.anomaly_detection import (
    AnomalyDetector,
    DetectedAnomaly,
    AnomalyType,
    Severity,
)


@pytest.fixture
def mock_tenant():
    """Mock tenant pour les tests."""
    tenant = MagicMock()
    tenant.id = 1
    return tenant


@pytest.fixture
def mock_anomaly_detector():
    """Mock AnomalyDetector avec anomalies de test."""
    with patch('backend.api.anomaly_detection.AnomalyDetector') as mock:
        detector = MagicMock()

        # Mock detected anomalies
        anomaly1 = DetectedAnomaly(
            anomaly_id="anom_001",
            anomaly_type=AnomalyType.AMOUNT_OUTLIER,
            severity=Severity.HIGH,
            confidence=0.92,
            title="Montant anormal",
            description="Transaction de 5000€ alors que la moyenne est 150€",
            entity_type="transaction",
            entity_id="123",
            details={"amount": 5000, "expected_range": "50-300"},
            suggested_action="Vérifier la transaction",
            detected_at=datetime.now(),
            resolved=False
        )

        anomaly2 = DetectedAnomaly(
            anomaly_id="anom_002",
            anomaly_type=AnomalyType.DUPLICATE_INVOICE,
            severity=Severity.CRITICAL,
            confidence=0.98,
            title="Facture en double",
            description="Facture #123 semble être un doublon",
            entity_type="invoice",
            entity_id="456",
            details={"amount": 1200},
            suggested_action="Annuler la facture en double",
            detected_at=datetime.now(),
            resolved=False
        )

        detector.detect_transaction_anomalies.return_value = [anomaly1]
        detector.detect_invoice_anomalies.return_value = [anomaly2]

        mock.return_value = detector
        yield mock


@pytest.fixture
def mock_transactions():
    """Mock _get_transactions."""
    with patch('backend.api.anomaly_detection._get_transactions') as mock:
        mock.return_value = [
            {
                "id": 1,
                "date": datetime.now(),
                "amount": 150.0,
                "description": "Achat normal",
                "category_id": None
            },
            {
                "id": 2,
                "date": datetime.now(),
                "amount": 5000.0,
                "description": "Achat suspect",
                "category_id": None
            }
        ]
        yield mock


@pytest.fixture
def mock_invoices():
    """Mock _get_invoices."""
    with patch('backend.api.anomaly_detection._get_invoices') as mock:
        mock.return_value = [
            {
                "id": 1,
                "date": datetime.now(),
                "amount": 1200.0,
                "invoice_number": "INV-001",
                "supplier_name": "Fournisseur A",
                "supplier_id": 1
            },
            {
                "id": 2,
                "date": datetime.now(),
                "amount": 1200.0,
                "invoice_number": "INV-002",
                "supplier_name": "Fournisseur A",
                "supplier_id": 1
            }
        ]
        yield mock


@pytest.fixture
def mock_query_df():
    """Mock query_df pour les requêtes SQL."""
    with patch('backend.api.anomaly_detection.query_df') as mock:
        yield mock


class TestScanAnomaliesEndpoint:
    """Tests pour l'endpoint GET /anomaly-detection/scan"""

    def test_scan_all_entities(self, mock_tenant, mock_anomaly_detector, mock_transactions, mock_invoices):
        """Test scan de toutes les anomalies."""
        result = scan_for_anomalies(
            entity_types="transactions,invoices",
            severity_threshold="LOW",
            days_back=30,
            tenant=mock_tenant
        )

        assert len(result) == 2
        assert result[0].anomaly_type == "AMOUNT_OUTLIER"
        assert result[1].anomaly_type == "DUPLICATE_INVOICE"

    def test_scan_transactions_only(self, mock_tenant, mock_anomaly_detector, mock_transactions):
        """Test scan transactions uniquement."""
        result = scan_for_anomalies(
            entity_types="transactions",
            severity_threshold="LOW",
            days_back=30,
            tenant=mock_tenant
        )

        assert len(result) == 1
        assert result[0].entity_type == "transaction"

    def test_scan_with_severity_filter(self, mock_tenant, mock_anomaly_detector, mock_transactions, mock_invoices):
        """Test filtrage par sévérité."""
        result = scan_for_anomalies(
            entity_types="transactions,invoices",
            severity_threshold="CRITICAL",  # Seulement CRITICAL
            days_back=30,
            tenant=mock_tenant
        )

        # Seul anomaly2 (CRITICAL) devrait être retourné
        assert len(result) == 1
        assert result[0].severity == "CRITICAL"

    def test_scan_error_handling(self, mock_tenant, mock_transactions):
        """Test gestion d'erreur du detector."""
        with patch('backend.api.anomaly_detection.AnomalyDetector') as mock:
            mock.return_value.detect_transaction_anomalies.side_effect = Exception("DB error")

            # Ne doit pas crasher, retourne une liste vide
            result = scan_for_anomalies(
                entity_types="transactions",
                tenant=mock_tenant
            )

            assert result == []


class TestTransactionOutliersEndpoint:
    """Tests pour l'endpoint GET /anomaly-detection/transactions/outliers"""

    def test_detect_outliers_success(self, mock_tenant, mock_transactions):
        """Test détection d'outliers avec succès."""
        with patch('backend.api.anomaly_detection.AnomalyDetector') as mock:
            detector = MagicMock()
            outlier = DetectedAnomaly(
                anomaly_id="out_001",
                anomaly_type=AnomalyType.AMOUNT_OUTLIER,
                severity=Severity.HIGH,
                confidence=0.95,
                title="Outlier",
                description="Transaction anormale",
                entity_type="transaction",
                entity_id="2",
                details={"amount": 5000, "expected_range": "50-300"},
                suggested_action="Vérifier",
                detected_at=datetime.now()
            )
            detector.detect_transaction_anomalies.return_value = [outlier]
            mock.return_value = detector

            result = detect_transaction_outliers(
                days_back=30,
                z_score_threshold=2.5,
                tenant=mock_tenant
            )

            assert len(result) == 1
            assert result[0].anomaly_type == "AMOUNT_OUTLIER"

    def test_outliers_custom_threshold(self, mock_tenant, mock_transactions):
        """Test avec seuil Z-score personnalisé."""
        with patch('backend.api.anomaly_detection.AnomalyDetector') as mock:
            detector = MagicMock()
            detector.detect_transaction_anomalies.return_value = []
            mock.return_value = detector

            detect_transaction_outliers(
                z_score_threshold=3.5,
                tenant=mock_tenant
            )

            # Vérifie que le seuil a été appliqué
            assert detector.Z_SCORE_THRESHOLD == 3.5


class TestDuplicateInvoicesEndpoint:
    """Tests pour l'endpoint GET /anomaly-detection/invoices/duplicates"""

    def test_detect_duplicates_same_supplier_amount_date(self, mock_tenant):
        """Test détection de factures en double."""
        with patch('backend.api.anomaly_detection._get_invoices') as mock:
            same_date = datetime.now()
            mock.return_value = [
                {
                    "id": 1,
                    "date": same_date,
                    "amount": 1200.0,
                    "supplier_id": 1,
                    "supplier_name": "Fournisseur A"
                },
                {
                    "id": 2,
                    "date": same_date + timedelta(days=2),
                    "amount": 1200.0,
                    "supplier_id": 1,
                    "supplier_name": "Fournisseur A"
                }
            ]

            result = detect_duplicate_invoices(
                days_back=90,
                similarity_threshold=0.9,
                tenant=mock_tenant
            )

            assert len(result) == 1
            assert result[0].similarity_score >= 0.9
            assert result[0].supplier == "Fournisseur A"

    def test_no_duplicates_different_supplier(self, mock_tenant):
        """Test pas de doublon si fournisseurs différents."""
        with patch('backend.api.anomaly_detection._get_invoices') as mock:
            mock.return_value = [
                {
                    "id": 1,
                    "date": datetime.now(),
                    "amount": 1200.0,
                    "supplier_id": 1,
                    "supplier_name": "Fournisseur A"
                },
                {
                    "id": 2,
                    "date": datetime.now(),
                    "amount": 1200.0,
                    "supplier_id": 2,
                    "supplier_name": "Fournisseur B"
                }
            ]

            result = detect_duplicate_invoices(tenant=mock_tenant)

            assert len(result) == 0

    def test_no_duplicates_different_amount(self, mock_tenant):
        """Test pas de doublon si montants différents."""
        with patch('backend.api.anomaly_detection._get_invoices') as mock:
            same_date = datetime.now()
            mock.return_value = [
                {
                    "id": 1,
                    "date": same_date,
                    "amount": 1200.0,
                    "supplier_id": 1,
                    "supplier_name": "Fournisseur A"
                },
                {
                    "id": 2,
                    "date": same_date,
                    "amount": 500.0,
                    "supplier_id": 1,
                    "supplier_name": "Fournisseur A"
                }
            ]

            result = detect_duplicate_invoices(tenant=mock_tenant)

            assert len(result) == 0

    def test_no_duplicates_dates_too_far(self, mock_tenant):
        """Test pas de doublon si dates trop éloignées."""
        with patch('backend.api.anomaly_detection._get_invoices') as mock:
            mock.return_value = [
                {
                    "id": 1,
                    "date": datetime.now(),
                    "amount": 1200.0,
                    "supplier_id": 1,
                    "supplier_name": "Fournisseur A"
                },
                {
                    "id": 2,
                    "date": datetime.now() + timedelta(days=10),  # > 7 jours
                    "amount": 1200.0,
                    "supplier_id": 1,
                    "supplier_name": "Fournisseur A"
                }
            ]

            result = detect_duplicate_invoices(tenant=mock_tenant)

            assert len(result) == 0


class TestInvoiceSequenceGapsEndpoint:
    """Tests pour l'endpoint GET /anomaly-detection/invoices/sequence-gaps"""

    def test_detect_sequence_gaps(self, mock_tenant, mock_query_df):
        """Test détection de trous dans les séquences."""
        import pandas as pd

        mock_query_df.return_value = pd.DataFrame([
            {
                "supplier_id": 1,
                "supplier_name": "Fournisseur A",
                "invoice_numbers": ["INV-100", "INV-101", "INV-105"],  # Gap: 102, 103, 104
                "dates": [datetime.now(), datetime.now(), datetime.now()]
            }
        ])

        result = detect_invoice_sequence_gaps(days_back=90, tenant=mock_tenant)

        assert len(result) > 0
        assert result[0].gap_size == 3  # 102, 103, 104 manquants
        assert "Fournisseur A" in result[0].sequence_name

    def test_no_gaps_continuous_sequence(self, mock_tenant, mock_query_df):
        """Test pas de gap avec séquence continue."""
        import pandas as pd

        mock_query_df.return_value = pd.DataFrame([
            {
                "supplier_id": 1,
                "supplier_name": "Fournisseur A",
                "invoice_numbers": ["INV-100", "INV-101", "INV-102"],
                "dates": [datetime.now(), datetime.now(), datetime.now()]
            }
        ])

        result = detect_invoice_sequence_gaps(tenant=mock_tenant)

        assert len(result) == 0


class TestRoundAmountsEndpoint:
    """Tests pour l'endpoint GET /anomaly-detection/transactions/round-amounts"""

    def test_detect_round_amounts(self, mock_tenant, mock_query_df):
        """Test détection de montants ronds suspects."""
        import pandas as pd

        mock_query_df.return_value = pd.DataFrame([
            {"id": 1, "date": datetime.now(), "amount": 10000.0, "description": "Paiement"},
            {"id": 2, "date": datetime.now(), "amount": 1000.0, "description": "Autre"},
            {"id": 3, "date": datetime.now(), "amount": 500.0, "description": "Normal"},
        ])

        result = detect_round_amounts(
            days_back=30,
            min_amount=100.0,
            tenant=mock_tenant
        )

        assert len(result) == 3
        # Le montant 10000 doit avoir le score le plus élevé
        assert result[0].amount == 10000.0
        assert result[0].suspicion_score == 0.9

    def test_round_amounts_below_threshold(self, mock_tenant, mock_query_df):
        """Test que les petits montants ne sont pas flaggés."""
        import pandas as pd

        mock_query_df.return_value = pd.DataFrame([
            {"id": 1, "date": datetime.now(), "amount": 50.0, "description": "Petit"},
        ])

        result = detect_round_amounts(min_amount=100.0, tenant=mock_tenant)

        assert len(result) == 0


class TestAnomalySummaryEndpoint:
    """Tests pour l'endpoint GET /anomaly-detection/summary"""

    def test_summary_with_anomalies(self, mock_tenant):
        """Test résumé avec anomalies."""
        with patch('backend.api.anomaly_detection.scan_for_anomalies') as mock_scan:
            from backend.api.anomaly_detection import AnomalyResponse

            anomalies = [
                AnomalyResponse(
                    id="1",
                    anomaly_type="AMOUNT_OUTLIER",
                    severity="HIGH",
                    entity_type="transaction",
                    entity_id=1,
                    description="Anomalie 1",
                    detected_value=5000.0,
                    expected_range="100-500",
                    confidence=0.9,
                    detected_at=datetime.now(),
                    resolved=False
                ),
                AnomalyResponse(
                    id="2",
                    anomaly_type="DUPLICATE_INVOICE",
                    severity="CRITICAL",
                    entity_type="invoice",
                    entity_id=2,
                    description="Anomalie 2",
                    detected_value=1200.0,
                    expected_range=None,
                    confidence=0.95,
                    detected_at=datetime.now(),
                    resolved=False
                )
            ]
            mock_scan.return_value = anomalies

            result = get_anomaly_summary(days_back=30, tenant=mock_tenant)

            assert result.total == 2
            assert result.critical == 1
            assert result.high == 1
            assert result.total_impact == 6200.0  # 5000 + 1200

    def test_summary_with_severity_filter(self, mock_tenant):
        """Test résumé avec filtre de sévérité."""
        with patch('backend.api.anomaly_detection.scan_for_anomalies') as mock_scan:
            from backend.api.anomaly_detection import AnomalyResponse

            anomalies = [
                AnomalyResponse(
                    id="1",
                    anomaly_type="test",
                    severity="HIGH",
                    entity_type="transaction",
                    entity_id=1,
                    description="High",
                    detected_value=100.0,
                    expected_range=None,
                    confidence=0.9,
                    detected_at=datetime.now(),
                    resolved=False
                ),
                AnomalyResponse(
                    id="2",
                    anomaly_type="test",
                    severity="LOW",
                    entity_type="transaction",
                    entity_id=2,
                    description="Low",
                    detected_value=50.0,
                    expected_range=None,
                    confidence=0.7,
                    detected_at=datetime.now(),
                    resolved=False
                )
            ]
            mock_scan.return_value = anomalies

            result = get_anomaly_summary(severity="high", tenant=mock_tenant)

            assert result.total == 1  # Seulement les HIGH
            assert len(result.items) == 1


class TestResolveAnomalyEndpoint:
    """Tests pour l'endpoint POST /anomaly-detection/resolve/{anomaly_id}"""

    def test_resolve_anomaly(self, mock_tenant):
        """Test résolution d'anomalie."""
        result = resolve_anomaly(
            anomaly_id="anom_001",
            resolution_note="Vérifié et correct",
            tenant=mock_tenant
        )

        assert result["status"] == "resolved"
        assert result["anomaly_id"] == "anom_001"
        assert result["resolution_note"] == "Vérifié et correct"
        assert "resolved_at" in result


class TestTenantMapping:
    """Tests pour la conversion tenant_id -> entity_id"""

    def test_intelligence_tenant_mapping(self, mock_query_df):
        """Test que tenant intelligence (4) accède à entity 2."""
        from backend.api.anomaly_detection import _get_transactions
        import pandas as pd

        mock_query_df.return_value = pd.DataFrame()

        _get_transactions(tenant_id=4, days=30)

        call_params = mock_query_df.call_args[1]['params']
        assert call_params['entity_id'] == 2

    def test_normal_tenant_no_mapping(self, mock_query_df):
        """Test que les autres tenants gardent leur ID."""
        from backend.api.anomaly_detection import _get_transactions
        import pandas as pd

        mock_query_df.return_value = pd.DataFrame()

        _get_transactions(tenant_id=3, days=30)

        call_params = mock_query_df.call_args[1]['params']
        assert call_params['entity_id'] == 3
