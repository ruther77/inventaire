"""Helpers de catalogue admin finance avec stockage injectable."""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class CategoryRepository(Protocol):
    def create_category(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        ...

    def list_categories(self, entity_id: int | None = None) -> list[Mapping[str, Any]]:
        ...


class CostCenterRepository(Protocol):
    def create_cost_center(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        ...

    def list_cost_centers(self, entity_id: int | None = None, is_active: bool | None = None) -> list[Mapping[str, Any]]:
        ...


def create_category(
    repo: CategoryRepository,
    *,
    entity_id: int,
    code: str,
    name: str,
    type_: str = "EXPENSE",
) -> dict[str, Any]:
    if entity_id is None or int(entity_id) <= 0:
        raise ValueError("entity_id must be a positive integer.")
    clean_code = (code or "").strip()
    clean_name = (name or "").strip()
    if not clean_code:
        raise ValueError("code must be provided.")
    if not clean_name:
        raise ValueError("name must be provided.")

    payload = {
        "entity_id": int(entity_id),
        "code": clean_code,
        "name": clean_name,
        "type": (type_ or "EXPENSE").strip().upper(),
    }
    created = repo.create_category(payload)
    return dict(created)


def list_categories(
    repo: CategoryRepository,
    *,
    entity_id: int | None = None,
) -> list[dict[str, Any]]:
    if entity_id is not None and int(entity_id) <= 0:
        raise ValueError("entity_id must be a positive integer.")
    rows = repo.list_categories(int(entity_id) if entity_id is not None else None)
    return [dict(row) for row in rows]


def create_cost_center(
    repo: CostCenterRepository,
    *,
    entity_id: int,
    code: str,
    name: str,
) -> dict[str, Any]:
    if entity_id is None or int(entity_id) <= 0:
        raise ValueError("entity_id must be a positive integer.")
    clean_code = (code or "").strip()
    clean_name = (name or "").strip()
    if not clean_code:
        raise ValueError("code must be provided.")
    if not clean_name:
        raise ValueError("name must be provided.")

    payload = {
        "entity_id": int(entity_id),
        "code": clean_code,
        "name": clean_name,
        "is_active": True,
    }
    created = repo.create_cost_center(payload)
    return dict(created)


def list_cost_centers(
    repo: CostCenterRepository,
    *,
    entity_id: int | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    if entity_id is not None and int(entity_id) <= 0:
        raise ValueError("entity_id must be a positive integer.")
    rows = repo.list_cost_centers(
        int(entity_id) if entity_id is not None else None,
        is_active,
    )
    return [dict(row) for row in rows]


__all__ = [
    "CategoryRepository",
    "CostCenterRepository",
    "create_category",
    "create_cost_center",
    "list_categories",
    "list_cost_centers",
]
