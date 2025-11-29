import importlib

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec('pandas') is None,
    reason='pandas non installé',
)

from backend.services import audit as audit_service
from tests import sample_data


def test_list_diagnostics_with_filters(monkeypatch):
    monkeypatch.setattr(audit_service, "_fetch_stock_diagnostics_df", lambda tenant_id: sample_data.make_audit_diag_df())
    monkeypatch.setattr(
        audit_service,
        "fetch_customer_catalog",
        lambda tenant_id: sample_data.make_catalog_df()[["id", "categorie"]],
    )
    monkeypatch.setattr(audit_service, "_load_actions_df", lambda tenant_id: sample_data.make_audit_actions_df())

    result = audit_service.list_diagnostics(categories=["Boissons"], levels=["Modéré"], min_abs=3, max_abs=20)

    assert result["summary"]["anomalies"] == 1
    assert result["summary"]["assigned"] == 1
    assert result["summary"]["open_tasks"] == 2
    assert result["items"][0]["product_id"] == 1
    assert result["items"][0]["niveau_ecart"] == "Modéré"
    assert result["items"][0]["responsable"] == "Alice"


def test_list_diagnostics_handles_empty(monkeypatch):
    monkeypatch.setattr(
        audit_service,
        "_fetch_stock_diagnostics_df",
        lambda tenant_id: sample_data.make_audit_diag_df().iloc[0:0],
    )
    monkeypatch.setattr(
        audit_service,
        "_load_actions_df",
        lambda tenant_id: sample_data.make_audit_actions_df().iloc[0:0],
    )
    monkeypatch.setattr(
        audit_service,
        "fetch_customer_catalog",
        lambda tenant_id: sample_data.make_catalog_df()[["id", "categorie"]],
    )

    result = audit_service.list_diagnostics(categories=None, levels=None, min_abs=0, max_abs=100)

    assert result["summary"]["anomalies"] == 0
    assert result["items"] == []
