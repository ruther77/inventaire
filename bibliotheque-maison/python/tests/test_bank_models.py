"""Tests pour bank_import.models."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from bank_import.models import (
    BalanceType,
    ImportResult,
    ImportStatus,
    ParsedStatement,
    ParsedTransaction,
    StatementBalance,
    StatementPeriod,
    TransactionDirection,
)


def test_statement_period_overlap():
    period_a = StatementPeriod(date(2024, 1, 1), date(2024, 1, 31))
    period_b = StatementPeriod(date(2024, 1, 15), date(2024, 2, 1))
    assert period_a.overlaps(period_b) is True


def test_statement_balance_validation():
    balance = StatementBalance(
        opening_balance=Decimal("10"),
        closing_balance=Decimal("15"),
        total_debits=Decimal("5"),
        total_credits=Decimal("10"),
        opening_balance_type=BalanceType.CREDITEUR,
    )
    assert balance.is_valid() is True


def test_parsed_transaction_signed_amount():
    txn = ParsedTransaction(
        date_operation=date(2024, 1, 1),
        date_valeur=date(2024, 1, 1),
        libelle="Test",
        montant=Decimal("12"),
        direction=TransactionDirection.OUT,
    )
    assert txn.montant_signe == Decimal("-12")


def test_parsed_statement_totals():
    tx_in = ParsedTransaction(
        date_operation=date(2024, 1, 1),
        date_valeur=date(2024, 1, 1),
        libelle="In",
        montant=Decimal("10"),
        direction=TransactionDirection.IN,
    )
    tx_out = ParsedTransaction(
        date_operation=date(2024, 1, 2),
        date_valeur=date(2024, 1, 2),
        libelle="Out",
        montant=Decimal("4"),
        direction=TransactionDirection.OUT,
    )
    statement = ParsedStatement(
        period=StatementPeriod(date(2024, 1, 1), date(2024, 1, 31)),
        transactions=[tx_in, tx_out],
    )
    assert statement.total_in == Decimal("10")
    assert statement.total_out == Decimal("4")
    assert statement.transaction_count == 2


def test_import_result_errors():
    result = ImportResult(status=ImportStatus.SUCCESS)
    assert result.has_errors is False
    result.add_error("oops")
    assert result.has_errors is True
