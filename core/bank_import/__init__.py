"""Unified bank statement import module.

This module provides a complete workflow for importing bank statements from PDF files:
- Multi-bank support (LCL, BNP, SumUp)
- Multi-statement PDF handling
- Balance validation
- Automatic categorization
- Duplicate detection
- Audit trail

Usage:
    from core.bank_import import BankImportOrchestrator

    orchestrator = BankImportOrchestrator()
    result = orchestrator.import_pdf(
        pdf_path="/path/to/statement.pdf",
        entity_code="RESTO",
        account_label="LCL - Principal"
    )
"""

from .orchestrator import BankImportOrchestrator
from .models import (
    BalanceType,
    BankType,
    StatementPeriod,
    ParsedTransaction,
    StatementBalance,
    ImportResult,
    ImportStatus,
)
from .detector import (
    BankDetector,
    DetectionResult,
    detect_bank_type,
    detect_bank_type_simple,
    detect_bank_full,
)
from .extractor import PDFExtractor
from .parser import (
    UnifiedBankParser,
    BaseBankParser,
    BankParser,
    get_parser,
    parse_statement,
)
from .categorizer import TransactionCategorizer
from .validator import BalanceValidator
from .deduplicator import TransactionDeduplicator

__all__ = [
    # Core orchestrator
    "BankImportOrchestrator",

    # Models
    "BalanceType",
    "BankType",
    "StatementPeriod",
    "ParsedTransaction",
    "StatementBalance",
    "ImportResult",
    "ImportStatus",

    # Detection
    "BankDetector",
    "DetectionResult",
    "detect_bank_type",
    "detect_bank_type_simple",
    "detect_bank_full",

    # Extraction and parsing
    "PDFExtractor",
    "UnifiedBankParser",
    "BaseBankParser",
    "BankParser",
    "get_parser",
    "parse_statement",

    # Processing
    "TransactionCategorizer",
    "BalanceValidator",
    "TransactionDeduplicator",
]
