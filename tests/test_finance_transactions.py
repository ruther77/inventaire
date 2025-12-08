import pytest

from backend.schemas.finance import FinanceTransactionCreate, FinanceTransactionLineCreate
from backend.services import finance_transactions


def test_validate_direction_ok():
    payload = FinanceTransactionCreate(
        entity_id=1,
        account_id=1,
        direction="in",
        source="TEST",
        date_operation="2024-12-01",
        amount=100,
    )
    assert payload.direction == "IN"


def test_validate_direction_error():
    with pytest.raises(ValueError):
        FinanceTransactionCreate(
            entity_id=1,
            account_id=1,
            direction="WRONG",
            source="TEST",
            date_operation="2024-12-01",
            amount=10,
        )


def test_currency_validation():
    payload = FinanceTransactionCreate(
        entity_id=1,
        account_id=1,
        direction="IN",
        source="TEST",
        date_operation="2024-12-01",
        amount=50,
        currency="usd",
    )
    assert payload.currency == "USD"
    with pytest.raises(ValueError):
        FinanceTransactionCreate(
            entity_id=1,
            account_id=1,
            direction="IN",
            source="TEST",
            date_operation="2024-12-01",
            amount=50,
            currency="EURO",
        )


def test_lines_amount_mismatch():
    payload = FinanceTransactionCreate(
        entity_id=1,
        account_id=1,
        direction="OUT",
        source="TEST",
        date_operation="2024-12-01",
        amount=100.0,
        lines=[
            FinanceTransactionLineCreate(category_id=1, montant_ttc=40),
            FinanceTransactionLineCreate(category_id=2, montant_ttc=30),
        ],
    )
    with pytest.raises(ValueError):
        finance_transactions._validate_lines_amount(payload)  # noqa: SLF001
