"""Tests pour finance.admin_catalog."""

from __future__ import annotations

from finance.admin_catalog import (
    create_category,
    create_cost_center,
    list_categories,
    list_cost_centers,
)


class MemoryCategoryRepo:
    def __init__(self):
        self.items = []

    def create_category(self, payload):
        payload = dict(payload)
        payload["id"] = len(self.items) + 1
        self.items.append(payload)
        return payload

    def list_categories(self, entity_id=None):
        if entity_id is None:
            return list(self.items)
        return [item for item in self.items if item.get("entity_id") in (entity_id, None)]


class MemoryCostCenterRepo:
    def __init__(self):
        self.items = []

    def create_cost_center(self, payload):
        payload = dict(payload)
        payload["id"] = len(self.items) + 1
        self.items.append(payload)
        return payload

    def list_cost_centers(self, entity_id=None, is_active=None):
        items = self.items
        if entity_id is not None:
            items = [item for item in items if item.get("entity_id") in (entity_id, None)]
        if is_active is not None:
            items = [item for item in items if item.get("is_active") == is_active]
        return items


def test_create_and_list_categories():
    repo = MemoryCategoryRepo()
    create_category(repo, entity_id=1, code="FOOD", name="Food")
    results = list_categories(repo, entity_id=1)
    assert results


def test_create_and_list_cost_centers():
    repo = MemoryCostCenterRepo()
    create_cost_center(repo, entity_id=1, code="KITCHEN", name="Kitchen")
    results = list_cost_centers(repo, entity_id=1)
    assert results
