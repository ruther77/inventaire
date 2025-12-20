"""Data models for bank import module."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any


class BankType(Enum):
    """Supported bank types.

    Current implementation supports:
    - LCL (Credit Lyonnais)
    - BNP (BNP Paribas)
    - SUMUP (SumUp payment processor)

    Future extensions planned:
    - CREDIT_AGRICOLE (Crédit Agricole)
    - SOCIETE_GENERALE (Société Générale)
    """
    LCL = "lcl"
    BNP = "bnp"
    SUMUP = "sumup"
    CREDIT_AGRICOLE = "credit_agricole"  # Future extension
    SOCIETE_GENERALE = "societe_generale"  # Future extension
    UNKNOWN = "unknown"


class ImportStatus(Enum):
    """Import process status."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class TransactionDirection(Enum):
    """Transaction direction."""
    IN = "IN"
    OUT = "OUT"


@dataclass
class StatementPeriod:
    """Represents a bank statement period."""
    start_date: date
    end_date: date
    page_start: int = 0
    page_end: int = 0

    def __str__(self) -> str:
        return f"{self.start_date} -> {self.end_date}"

    def overlaps(self, other: "StatementPeriod") -> bool:
        """Check if this period overlaps with another."""
        return not (self.end_date < other.start_date or self.start_date > other.end_date)


class BalanceType(Enum):
    """Type of balance (credit or debit)."""
    CREDITEUR = "crediteur"  # Positive balance (account has money)
    DEBITEUR = "debiteur"    # Negative balance (account is overdrawn)


@dataclass
class StatementBalance:
    """Balance information extracted from statement.

    LCL specificity:
    - TOTAUX on LCL statements include ANCIEN SOLDE
    - If ANCIEN SOLDE CREDITEUR: it's added to total_credits column
    - If ANCIEN SOLDE DEBITEUR: it's added to total_debits column

    To get actual transaction totals:
    - actual_credits = total_credits - opening_balance (if crediteur)
    - actual_debits = total_debits - opening_balance (if debiteur)
    """
    opening_balance: Decimal
    closing_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal
    opening_balance_type: BalanceType = BalanceType.CREDITEUR
    closing_balance_type: BalanceType = BalanceType.CREDITEUR

    def is_valid(self) -> bool:
        """Verify balance equation: opening + credits - debits = closing."""
        calculated = self.opening_balance + self.total_credits - self.total_debits
        return abs(calculated - self.closing_balance) < Decimal("0.01")

    @property
    def net_movement(self) -> Decimal:
        """Net movement during the period."""
        return self.total_credits - self.total_debits

    @property
    def actual_transaction_credits(self) -> Decimal:
        """Actual credit transactions (excluding ANCIEN SOLDE if crediteur).

        LCL PDF TOTAUX logic:
        - If ANCIEN SOLDE CREDITEUR: it appears in CREDIT column, included in total_credits
        - If ANCIEN SOLDE DEBITEUR: it appears in DEBIT column, NOT in total_credits
        """
        if self.opening_balance_type == BalanceType.CREDITEUR:
            return self.total_credits - self.opening_balance
        return self.total_credits

    @property
    def actual_transaction_debits(self) -> Decimal:
        """Actual debit transactions (excluding ANCIEN SOLDE if debiteur).

        LCL PDF TOTAUX logic:
        - If ANCIEN SOLDE DEBITEUR: it appears in DEBIT column, included in total_debits
        - If ANCIEN SOLDE CREDITEUR: it appears in CREDIT column, NOT in total_debits
        """
        if self.opening_balance_type == BalanceType.DEBITEUR:
            return self.total_debits - self.opening_balance
        return self.total_debits


@dataclass
class ParsedTransaction:
    """A parsed bank transaction."""
    date_operation: date
    date_valeur: date
    libelle: str
    montant: Decimal
    direction: TransactionDirection

    # Categorization
    category: Optional[str] = None
    category_confidence: float = 0.0
    matched_keyword: Optional[str] = None

    # Metadata
    line_number: int = 0
    raw_text: str = ""
    checksum: str = ""

    # Validation flags
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    @property
    def montant_signe(self) -> Decimal:
        """Signed amount (positive for IN, negative for OUT)."""
        if self.direction == TransactionDirection.IN:
            return abs(self.montant)
        return -abs(self.montant)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            "date_operation": self.date_operation,
            "date_valeur": self.date_valeur,
            "libelle_banque": self.libelle,
            "montant": float(self.montant_signe),
            "category": self.category,
            "category_confidence": self.category_confidence,
            "matched_keyword": self.matched_keyword,
            "checksum": self.checksum,
        }


@dataclass
class ParsedStatement:
    """A complete parsed bank statement."""
    period: StatementPeriod
    transactions: List[ParsedTransaction]
    balance: Optional[StatementBalance] = None
    bank_type: BankType = BankType.UNKNOWN
    account_number: Optional[str] = None

    # Validation
    is_balanced: bool = False
    validation_notes: List[str] = field(default_factory=list)

    @property
    def total_in(self) -> Decimal:
        """Total incoming amount."""
        return sum(
            t.montant for t in self.transactions
            if t.direction == TransactionDirection.IN
        )

    @property
    def total_out(self) -> Decimal:
        """Total outgoing amount."""
        return sum(
            t.montant for t in self.transactions
            if t.direction == TransactionDirection.OUT
        )

    @property
    def transaction_count(self) -> int:
        """Number of transactions."""
        return len(self.transactions)


@dataclass
class ImportResult:
    """Result of an import operation."""
    status: ImportStatus
    statements_detected: int = 0
    statements_imported: int = 0
    transactions_total: int = 0
    transactions_inserted: int = 0
    transactions_duplicates: int = 0
    transactions_categorized: int = 0
    transactions_uncategorized: int = 0

    # Financial totals
    total_credits: Decimal = Decimal("0")
    total_debits: Decimal = Decimal("0")

    # Audit
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    import_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Detailed results per statement
    statement_results: List[Dict[str, Any]] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        """Add an error message."""
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        """Add a warning message."""
        self.warnings.append(msg)

    @property
    def has_errors(self) -> bool:
        """Check if there were any errors."""
        return len(self.errors) > 0

    @property
    def duration_seconds(self) -> Optional[float]:
        """Import duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "statements_detected": self.statements_detected,
            "statements_imported": self.statements_imported,
            "transactions_total": self.transactions_total,
            "transactions_inserted": self.transactions_inserted,
            "transactions_duplicates": self.transactions_duplicates,
            "transactions_categorized": self.transactions_categorized,
            "transactions_uncategorized": self.transactions_uncategorized,
            "total_credits": float(self.total_credits),
            "total_debits": float(self.total_debits),
            "errors": self.errors,
            "warnings": self.warnings,
            "import_id": self.import_id,
            "duration_seconds": self.duration_seconds,
        }


@dataclass
class ColumnPositions:
    """Column positions for parsing fixed-width bank statements."""
    date_start: int = 0
    date_end: int = 6
    libelle_start: int = 10
    libelle_end: int = 87
    valeur_start: int = 87
    valeur_end: int = 105
    debit_start: int = 105
    debit_end: int = 124
    credit_start: int = 124
    credit_end: int = 200

    @classmethod
    def for_lcl(cls) -> "ColumnPositions":
        """LCL bank column positions.

        Based on actual PDF layout:
        - DATE at position 1 (with leading space)
        - LIBELLE at ~10
        - VALEUR at ~87
        - DEBIT at ~105
        - CREDIT at ~124
        """
        return cls(
            date_start=0, date_end=7,  # " 02.01 " -> captures date with spaces
            libelle_start=7, libelle_end=87,
            valeur_start=87, valeur_end=105,
            debit_start=105, debit_end=124,
            credit_start=124, credit_end=200
        )

    @classmethod
    def for_bnp(cls) -> "ColumnPositions":
        """BNP bank column positions."""
        return cls(
            date_start=0, date_end=10,
            libelle_start=12, libelle_end=70,
            valeur_start=70, valeur_end=85,
            debit_start=85, debit_end=105,
            credit_start=105, credit_end=200
        )
