import pytest

from backend.schemas.finance import FinanceInvoiceCreate, FinanceInvoiceLineCreate, FinancePaymentCreate
from backend.services import finance_invoices


def test_invoice_line_defaults():
    line = FinanceInvoiceLineCreate(category_id=1, montant_ttc=10.0)
    assert line.position == 1
    invoice = FinanceInvoiceCreate(
        entity_id=1,
        vendor_id=1,
        invoice_number="INV-1",
        montant_ttc=10.0,
        lines=[line],
    )
    assert invoice.status == "EN_ATTENTE"
    assert invoice.currency == "EUR"


def test_payment_positive_amount():
    with pytest.raises(ValueError):
        FinancePaymentCreate(invoice_id=1, transaction_id=None, amount=-5, date_payment="2024-12-01", mode="CB")


def test_vendors_from_processed_invoices(monkeypatch):
    calls = {"created": 0}

    def fake_exec_sql_return_id(*args, **kwargs):
        calls["created"] += 1
        return calls["created"]

    monkeypatch.setattr(finance_invoices, "exec_sql_return_id", fake_exec_sql_return_id)
    payload = finance_invoices.FinanceVendorCreate(entity_id=1, name="TEST_VENDOR")  # type: ignore[attr-defined]
    created = finance_invoices.create_vendor(payload)
    assert created["id"] == 1
