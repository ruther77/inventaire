"""
Core Engines Module
====================

Re-exports des moteurs depuis core/finance/ pour la nouvelle architecture.
Compatible avec le plan de restructuration 2025-12.

Moteurs disponibles:
- FinancialRulesEngine: Catégorisation automatique des transactions
- ForecastingEngine: Prévisions ventes/cash-flow/stock
- SupplierScoreCalculator: Scoring multi-dimensionnel fournisseurs
- BankReconciliationEngine: Rapprochement bancaire intelligent
"""

# Re-export depuis core/finance
from core.finance.rules_engine import (
    RuleType,
    Rule,
    ClassificationResult,
    Anomaly as RulesAnomaly,
    FinancialRulesEngine,
)

from core.finance.forecasting import (
    ForecastType,
    ForecastMethod,
    ForecastResult,
    CashFlowForecast,
    ForecastingEngine,
)

from core.finance.supplier_scoring import (
    ScoreDimension,
    SupplierScore,
    PriceVolatilityMetrics,
    SupplierScoreCalculator,
)

from core.finance.bank_reconciliation import (
    MatchStatus,
    MatchType,
    MatchCandidate,
    ReconciliationResult,
    BankReconciliationEngine,
)

from core.finance.anomaly_detection import (
    AnomalyType,
    Severity as AnomalySeverity,
    DetectedAnomaly,
    AnomalyDetector,
)

__all__ = [
    # Rules Engine
    "RuleType",
    "Rule",
    "ClassificationResult",
    "RulesAnomaly",
    "FinancialRulesEngine",

    # Forecasting
    "ForecastType",
    "ForecastMethod",
    "ForecastResult",
    "CashFlowForecast",
    "ForecastingEngine",

    # Supplier Scoring
    "ScoreDimension",
    "SupplierScore",
    "PriceVolatilityMetrics",
    "SupplierScoreCalculator",

    # Bank Reconciliation
    "MatchStatus",
    "MatchType",
    "MatchCandidate",
    "ReconciliationResult",
    "BankReconciliationEngine",

    # Anomaly Detection
    "AnomalyType",
    "AnomalySeverity",
    "DetectedAnomaly",
    "AnomalyDetector",
]
