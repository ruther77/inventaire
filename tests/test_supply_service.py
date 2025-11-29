import importlib

import pytest

from backend.services import supply
from tests import sample_data

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec('pandas') is None,
    reason='pandas non installé',
)


def test_compute_supply_plan_with_recommendations(monkeypatch):
    monkeypatch.setattr(supply, "fetch_customer_catalog", lambda tenant_id: sample_data.make_catalog_df())
    monkeypatch.setattr(supply, "fetch_recent_suppliers", lambda tenant_id: sample_data.make_suppliers_df())

    result = supply.compute_supply_plan(target_coverage=10, alert_threshold=5, min_daily_sales=0.0)

    assert result["summary"]["analyzed"] == 4
    assert result["summary"]["recommended_count"] == 3
    assert result["summary"]["units_to_order"] == 14
    assert result["summary"]["value_total"] > 0

    critical_items = [item for item in result["items"] if item["niveau_priorite"] == "Critique"]
    assert critical_items, "au moins un article critique est attendu"
    assert all(item["quantite_a_commander"] > 0 for item in critical_items)

    supplier_summary = {row["fournisseur"]: row for row in result["supplier_breakdown"]}
    assert "Metro" in supplier_summary
    assert supplier_summary["Metro"]["quantite"] > 0

    assert "Boissons" in result["available_categories"]


def test_supply_plan_filters_and_search(monkeypatch):
    monkeypatch.setattr(supply, "fetch_customer_catalog", lambda tenant_id: sample_data.make_catalog_df())
    monkeypatch.setattr(supply, "fetch_recent_suppliers", lambda tenant_id: sample_data.make_suppliers_df())

    result = supply.compute_supply_plan(
        target_coverage=7,
        alert_threshold=3,
        min_daily_sales=0.1,
        categories=["Boissons"],
        search="mangue",
    )

    assert result["summary"]["analyzed"] == 1
    assert result["items"][0]["nom"] == "Jus mangue"
    assert result["items"][0]["fournisseur"] == "Metro"
