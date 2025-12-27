"""Modèles de données pour les imports bancaires."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional


class BankType(Enum):
    """Types de banque pris en charge."""
    LCL = "lcl"
    BNP = "bnp"
    SUMUP = "sumup"
    CREDIT_AGRICOLE = "credit_agricole"
    SOCIETE_GENERALE = "societe_generale"
    UNKNOWN = "unknown"


class ImportStatus(Enum):
    """Statut d'un processus d'import."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class TransactionDirection(Enum):
    """Sens de la transaction."""
    IN = "IN"
    OUT = "OUT"


@dataclass
class StatementPeriod:
    """Représente une période de relevé bancaire."""
    start_date: date
    end_date: date
    page_start: int = 0
    page_end: int = 0

    def __str__(self) -> str:
        return f"{self.start_date} -> {self.end_date}"

    def overlaps(self, other: "StatementPeriod") -> bool:
        """Retourne True si deux périodes se chevauchent."""
        return not (self.end_date < other.start_date or self.start_date > other.end_date)


class BalanceType(Enum):
    """Type de solde (créditeur ou débiteur)."""
    CREDITEUR = "crediteur"
    DEBITEUR = "debiteur"


@dataclass
class StatementBalance:
    """Informations de solde extraites d'un relevé."""
    opening_balance: Decimal
    closing_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal
    opening_balance_type: BalanceType = BalanceType.CREDITEUR
    closing_balance_type: BalanceType = BalanceType.CREDITEUR

    def is_valid(self) -> bool:
        """Vérifie l'équation de solde : ouverture + crédits - débits = clôture."""
        calculated = self.opening_balance + self.total_credits - self.total_debits
        return abs(calculated - self.closing_balance) < Decimal("0.01")

    @property
    def net_movement(self) -> Decimal:
        """Mouvement net sur la période."""
        return self.total_credits - self.total_debits

    @property
    def actual_transaction_credits(self) -> Decimal:
        """Crédits hors solde d'ouverture lorsqu'il était créditeur."""
        if self.opening_balance_type == BalanceType.CREDITEUR:
            return self.total_credits - self.opening_balance
        return self.total_credits

    @property
    def actual_transaction_debits(self) -> Decimal:
        """Débits hors solde d'ouverture lorsqu'il était débiteur."""
        if self.opening_balance_type == BalanceType.DEBITEUR:
            return self.total_debits - self.opening_balance
        return self.total_debits


@dataclass
class ParsedTransaction:
    """Une transaction bancaire parsée."""
    date_operation: date
    date_valeur: date
    libelle: str
    montant: Decimal
    direction: TransactionDirection

    category: Optional[str] = None
    category_confidence: float = 0.0
    matched_keyword: Optional[str] = None

    line_number: int = 0
    raw_text: str = ""
    checksum: str = ""

    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    @property
    def montant_signe(self) -> Decimal:
        """Montant signé (positif pour IN, négatif pour OUT)."""
        if self.direction == TransactionDirection.IN:
            return abs(self.montant)
        return -abs(self.montant)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour la persistance."""
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
    """Un relevé bancaire parsé complet."""
    period: StatementPeriod
    transactions: List[ParsedTransaction]
    balance: Optional[StatementBalance] = None
    bank_type: BankType = BankType.UNKNOWN
    account_number: Optional[str] = None

    is_balanced: bool = False
    validation_notes: List[str] = field(default_factory=list)

    @property
    def total_in(self) -> Decimal:
        """Montant total des entrées."""
        return sum(
            t.montant for t in self.transactions
            if t.direction == TransactionDirection.IN
        )

    @property
    def total_out(self) -> Decimal:
        """Montant total des sorties."""
        return sum(
            t.montant for t in self.transactions
            if t.direction == TransactionDirection.OUT
        )

    @property
    def transaction_count(self) -> int:
        """Nombre de transactions."""
        return len(self.transactions)


@dataclass
class ImportResult:
    """Résultat d'une opération d'import."""
    status: ImportStatus
    statements_detected: int = 0
    statements_imported: int = 0
    transactions_total: int = 0
    transactions_inserted: int = 0
    transactions_duplicates: int = 0
    transactions_categorized: int = 0
    transactions_uncategorized: int = 0

    total_credits: Decimal = Decimal("0")
    total_debits: Decimal = Decimal("0")

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    import_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    statement_results: List[Dict[str, Any]] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        """Ajoute un message d'erreur."""
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        """Ajoute un avertissement."""
        self.warnings.append(msg)

    @property
    def has_errors(self) -> bool:
        """Retourne True si des erreurs ont été enregistrées."""
        return len(self.errors) > 0


__all__ = [
    "BankType",
    "ImportStatus",
    "TransactionDirection",
    "StatementPeriod",
    "BalanceType",
    "StatementBalance",
    "ParsedTransaction",
    "ParsedStatement",
    "ImportResult",
]
