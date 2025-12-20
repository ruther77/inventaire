"""
Core Services Module
=====================

Services métier pour le projet.
Compatible avec le plan de restructuration 2025-12.

Services:
- MarginCalculator: Calcul des marges (brute, opérationnelle, PAMP)
- InventoryIntelligence: Gestion intelligente du stock (EOQ, safety stock)
- AnalyticAccountingEngine: Comptabilité analytique multi-axes
"""

# Re-export depuis core/finance
from core.finance.margin_calculator import (
    MarginType,
    PeriodType,
    MarginResult,
    PAMPHistory,
    MarginCalculator,
)

from core.finance.inventory_intelligence import (
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

from core.finance.analytic_accounting import (
    AxisType,
    AnalyticAxis,
    AnalyticAssignment,
    AnalyticReport,
    AnalyticAccountingEngine,
)

# Re-export depuis core/
from core.price_history_service import PriceHistoryService
from core.inventory_service import InventoryService
from core.product_service import ProductService

__all__ = [
    # Margin Calculator
    "MarginType",
    "PeriodType",
    "MarginResult",
    "PAMPHistory",
    "MarginCalculator",

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

    # Analytic Accounting
    "AxisType",
    "AnalyticAxis",
    "AnalyticAssignment",
    "AnalyticReport",
    "AnalyticAccountingEngine",

    # Core Services
    "PriceHistoryService",
    "InventoryService",
    "ProductService",
]
