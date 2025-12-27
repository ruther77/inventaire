"""Orchestrateur d'import bancaire avec composants injectables."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol

from .models import BankType, ImportResult, ImportStatus, ParsedStatement, ParsedTransaction, StatementPeriod


@dataclass(frozen=True)
class ExtractionResult:
    """Résultat de l'extraction de texte PDF."""
    full_text: str
    periods: list[StatementPeriod]
    period_line_ranges: list[tuple[int, int]] | None = None


class PDFExtractor(Protocol):
    def extract(self, pdf_path: Path) -> ExtractionResult:
        ...

    def clean_lines(self, lines: Iterable[str], bank_type: BankType) -> list[str]:
        ...

    def get_lines_for_period(
        self,
        lines: list[str],
        period: StatementPeriod,
        line_ranges: list[tuple[int, int]] | None,
    ) -> list[str]:
        ...


class BankDetector(Protocol):
    def detect(self, text: str) -> tuple[BankType, float]:
        ...


class BankParser(Protocol):
    def parse(self, lines: list[str], period: StatementPeriod, bank_type: BankType) -> ParsedStatement:
        ...


class BalanceValidator(Protocol):
    def validate(self, statement: ParsedStatement) -> tuple[bool, list[str]]:
        ...


class TransactionCategorizer(Protocol):
    def categorize(self, transaction: ParsedTransaction, bank_type: BankType | None = None) -> ParsedTransaction:
        ...


class TransactionDeduplicator(Protocol):
    def deduplicate(self, transactions: list[ParsedTransaction]) -> tuple[list[ParsedTransaction], list[ParsedTransaction]]:
        ...


class ImportRepository(Protocol):
    def persist_statement(
        self,
        statement: ParsedStatement,
        *,
        account_id: int,
        source_file: str,
    ) -> tuple[int, list[ParsedTransaction]]:
        ...


class BankImportOrchestrator:
    """Orchestre le workflow d'import de relevés bancaires."""

    def __init__(
        self,
        *,
        extractor: PDFExtractor,
        detector: BankDetector,
        parser: BankParser,
        validator: BalanceValidator,
        categorizer: TransactionCategorizer,
        deduplicator: TransactionDeduplicator,
        repository: ImportRepository | None = None,
    ) -> None:
        self.extractor = extractor
        self.detector = detector
        self.parser = parser
        self.validator = validator
        self.categorizer = categorizer
        self.deduplicator = deduplicator
        self.repository = repository

    def import_pdf(
        self,
        pdf_path: Path,
        *,
        account_id: int,
        source_file: str | None = None,
    ) -> ImportResult:
        if account_id <= 0:
            raise ValueError("account_id must be positive.")

        result = ImportResult(status=ImportStatus.SUCCESS, started_at=datetime.now())
        extraction = self.extractor.extract(pdf_path)

        if not extraction.periods:
            result.status = ImportStatus.FAILED
            result.add_error("No statement periods detected.")
            return result

        bank_type, _confidence = self.detector.detect(extraction.full_text)
        if bank_type == BankType.UNKNOWN:
            bank_type = BankType.LCL
            result.add_warning("Bank type not detected, defaulted to LCL.")

        lines = extraction.full_text.splitlines()
        for period in extraction.periods:
            period_lines = self.extractor.get_lines_for_period(
                lines, period, extraction.period_line_ranges
            )
            clean_lines = self.extractor.clean_lines(period_lines, bank_type)
            statement = self.parser.parse(clean_lines, period, bank_type)

            is_valid, notes = self.validator.validate(statement)
            if not is_valid:
                result.add_warning("; ".join(notes))

            categorized = [self.categorizer.categorize(txn, bank_type) for txn in statement.transactions]
            new_txns, duplicates = self.deduplicator.deduplicate(categorized)

            inserted = 0
            if self.repository is not None:
                inserted, persisted = self.repository.persist_statement(
                    statement,
                    account_id=account_id,
                    source_file=source_file or pdf_path.name,
                )
            else:
                persisted = new_txns
                inserted = len(new_txns)

            result.statements_detected += 1
            if inserted > 0:
                result.statements_imported += 1
            result.transactions_total += len(statement.transactions)
            result.transactions_inserted += inserted
            result.transactions_duplicates += len(duplicates)
            result.transactions_categorized += sum(1 for tx in persisted if tx.category)
            result.transactions_uncategorized += sum(1 for tx in persisted if not tx.category)

        if result.transactions_inserted == 0 and result.transactions_total > 0:
            if result.transactions_duplicates == result.transactions_total:
                result.status = ImportStatus.DUPLICATE
            else:
                result.status = ImportStatus.FAILED
        elif result.errors:
            result.status = ImportStatus.PARTIAL

        result.completed_at = datetime.now()
        return result


__all__ = [
    "BankImportOrchestrator",
    "BankDetector",
    "BankParser",
    "BalanceValidator",
    "ExtractionResult",
    "ImportRepository",
    "PDFExtractor",
    "TransactionCategorizer",
    "TransactionDeduplicator",
]
