from datetime import datetime
from decimal import Decimal

import pandas as pd
import pytest

import os

os.environ.setdefault("SKIP_TENANT_INIT", "1")
os.environ.setdefault("SKIP_USER_BOOTSTRAP", "1")

from backend.services import capital as capital_service  # noqa: E402


@pytest.fixture(autouse=True)
def patch_db(monkeypatch):
    def fake_fetch_tenants():
        return pd.DataFrame([{"id": 1, "code": "epicerie", "name": "Épicerie HQ"}])

    def fake_price_history(*, tenant_id):
        return Decimal("10.5")

    def fake_bank_balance(*, tenant_id):
        return Decimal("5")

    monkeypatch.setattr(capital_service, "_fetch_tenants", fake_fetch_tenants)
    monkeypatch.setattr(capital_service, "_latest_price_total", fake_price_history)
    monkeypatch.setattr(capital_service, "_bank_balance", fake_bank_balance)
    monkeypatch.setattr(capital_service, "_cash_balance", lambda *args, **kwargs: Decimal("2"))
    yield


def test_build_capital_overview(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "code": "EAN1",
                "fournisseur": "F1",
                "prix_achat": 4.5,
                "quantite": 2,
                "facture_date": datetime.utcnow(),
                "source_context": "invoice",
                "created_at": datetime.utcnow(),
                "tenant_id": 1,
            }
        ]
    )

    def fake_latest_price(*args, **kwargs):
        return df

    monkeypatch.setattr(capital_service, "fetch_latest_price_per_code", fake_latest_price)
    overview = capital_service.build_capital_overview(limit_latest_prices=5)
    assert overview["global"]["stock_value"] >= 0
    assert overview["entities"][0]["code"] == "epicerie"
