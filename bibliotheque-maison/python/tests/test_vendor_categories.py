"""Tests pour catalog.vendor_categories."""

from __future__ import annotations

from pathlib import Path

from catalog.vendor_categories import load_vendor_category_rules


def test_load_vendor_category_rules(tmp_path: Path):
    csv_content = "aliases,category,types\nACME|ACME SA,Groceries,Food|Retail\n"
    csv_path = tmp_path / "vendor.csv"
    csv_path.write_text(csv_content, encoding="utf-8")

    rules = load_vendor_category_rules(csv_path)
    assert rules
    aliases, category, types = rules[0]
    assert aliases == ("ACME", "ACME SA")
    assert category == "Groceries"
    assert types == ("Food", "Retail")


def test_load_vendor_category_rules_missing():
    rules = load_vendor_category_rules(None)
    assert rules == ()
