"""
Core Finance Module
====================

Module financier avancé comprenant:
- Event Sourcing pour traçabilité complète
- Moteur de règles avec apprentissage semi-supervisé
- Scoring fournisseurs multi-dimensionnel
- Détection d'anomalies (Z-score, IQR)
- Rapprochement bancaire intelligent
- Calcul marges (brute, opérationnelle, nette, PAMP)
- Comptabilité analytique multi-axes
- Forecasting (Holt-Winters, régression)
- Inventaire intelligent (EOQ, safety stock)
- Audit trail ultra complet
"""

from .event_sourcing import (
    EventType,
    Event,
    EventStore,
    EventDispatcher,
    emit_invoice_imported,
    emit_price_updated,
    emit_stock_movement,
)

from .rules_engine import (
    RuleType,
    Rule,
    ClassificationResult,
    Anomaly as RulesAnomaly,
    FinancialRulesEngine,
)

from .supplier_scoring import (
    ScoreDimension,
    SupplierScore,
    PriceVolatilityMetrics,
    SupplierScoreCalculator,
)

from .anomaly_detection import (
    AnomalyType,
    Severity as AnomalySeverity,
    DetectedAnomaly,
    AnomalyDetector,
)

from .bank_reconciliation import (
    MatchStatus,
    MatchType,
    MatchCandidate,
    ReconciliationResult,
    BankReconciliationEngine,
)

from .margin_calculator import (
    MarginType,
    PeriodType,
    MarginResult,
    PAMPHistory,
    MarginCalculator,
)

from .analytic_accounting import (
    AxisType,
    AnalyticAxis,
    AnalyticAssignment,
    AnalyticReport,
    AnalyticAccountingEngine,
)

from .forecasting import (
    ForecastType,
    ForecastMethod,
    ForecastResult,
    CashFlowForecast,
    ForecastingEngine,
)

from .inventory_intelligence import (
    StockClassification,
    ServiceLevel,
    DemandAnalysis,
    EOQResult,
    SafetyStockResult,
    ReorderPoint,
    DeadStockItem,
    StockoutPrediction,
    ReorderSuggestion,
    ABCXYZClassification,
    InventoryIntelligence,
    create_inventory_intelligence,
)

from .audit_trail import (
    AuditAction,
    AuditEntity,
    AuditSeverity,
    AuditContext,
    AuditDiff,
    AuditEntry,
    AuditSearchCriteria,
    AuditReport,
    AuditTrail,
    audit_action,
    create_audit_trail,
    AUDIT_LOG_SCHEMA,
)

__all__ = [
    # Event Sourcing
    "EventType",
    "Event",
    "EventStore",
    "EventDispatcher",
    "emit_invoice_imported",
    "emit_price_updated",
    "emit_stock_movement",

    # Rules Engine
    "RuleType",
    "Rule",
    "ClassificationResult",
    "RulesAnomaly",
    "FinancialRulesEngine",

    # Supplier Scoring
    "ScoreDimension",
    "SupplierScore",
    "PriceVolatilityMetrics",
    "SupplierScoreCalculator",

    # Anomaly Detection
    "AnomalyType",
    "AnomalySeverity",
    "DetectedAnomaly",
    "AnomalyDetector",

    # Bank Reconciliation
    "MatchStatus",
    "MatchType",
    "MatchCandidate",
    "ReconciliationResult",
    "BankReconciliationEngine",

    # Margin Calculator
    "MarginType",
    "PeriodType",
    "MarginResult",
    "PAMPHistory",
    "MarginCalculator",

    # Analytic Accounting
    "AxisType",
    "AnalyticAxis",
    "AnalyticAssignment",
    "AnalyticReport",
    "AnalyticAccountingEngine",

    # Forecasting
    "ForecastType",
    "ForecastMethod",
    "ForecastResult",
    "CashFlowForecast",
    "ForecastingEngine",

    # Inventory Intelligence
    "StockClassification",
    "ServiceLevel",
    "DemandAnalysis",
    "EOQResult",
    "SafetyStockResult",
    "ReorderPoint",
    "DeadStockItem",
    "StockoutPrediction",
    "ReorderSuggestion",
    "ABCXYZClassification",
    "InventoryIntelligence",
    "create_inventory_intelligence",

    # Audit Trail
    "AuditAction",
    "AuditEntity",
    "AuditSeverity",
    "AuditContext",
    "AuditDiff",
    "AuditEntry",
    "AuditSearchCriteria",
    "AuditReport",
    "AuditTrail",
    "audit_action",
    "create_audit_trail",
    "AUDIT_LOG_SCHEMA",
]
