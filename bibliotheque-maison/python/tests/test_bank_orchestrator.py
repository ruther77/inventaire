"""Tests pour bank_import.orchestrator."""

from __future__ import annotations

from pathlib import Path
from datetime import date

from bank_import.models import BankType, ImportStatus, ParsedStatement, ParsedTransaction, StatementPeriod, TransactionDirection
from bank_import.orchestrator import BankImportOrchestrator, ExtractionResult


class FakeExtractor:
    def extract(self, pdf_path: Path):
        return ExtractionResult(full_text="line1\nline2", periods=[StatementPeriod(pdf_path.name, pdf_path.name)])

    def clean_lines(self, lines, bank_type):
        return list(lines)

    def get_lines_for_period(self, lines, period, line_ranges):
        return lines


class FakeDetector:
    def detect(self, text):
        return BankType.LCL, 0.9


class FakeParser:
    def parse(self, lines, period, bank_type):
        tx = ParsedTransaction(
            date_operation=period.start_date,
            date_valeur=period.end_date,
            libelle="Test",
            montant=10,
            direction=TransactionDirection.OUT,
        )
        return ParsedStatement(period=period, transactions=[tx])


class FakeValidator:
    def validate(self, statement):
        return True, []


class FakeCategorizer:
    def categorize(self, transaction, bank_type=None):
        transaction.category = "cat"
        return transaction


class FakeDeduplicator:
    def deduplicate(self, transactions):
        return transactions, []


def test_orchestrator_import_pdf(tmp_path):
    pdf_path = tmp_path / "bank.pdf"
    pdf_path.write_text("dummy", encoding="utf-8")

    orchestrator = BankImportOrchestrator(
        extractor=FakeExtractor(),
        detector=FakeDetector(),
        parser=FakeParser(),
        validator=FakeValidator(),
        categorizer=FakeCategorizer(),
        deduplicator=FakeDeduplicator(),
        repository=None,
    )

    result = orchestrator.import_pdf(pdf_path, account_id=1)
    assert result.status == ImportStatus.SUCCESS
    assert result.transactions_total == 1
