"""Helpers de rapprochement avec stockage injectable."""

from __future__ import annotations

from typing import Any, Mapping, Protocol


ALLOWED_MATCH_STATUSES = {"pending", "auto", "confirmed", "rejected"}


class ReconciliationRepository(Protocol):
    """Interface de stockage pour les rapprochements."""

    def fetch_matches(self, tenant_id: int, status: str | None = None) -> list[Mapping[str, Any]]:
        ...


def fetch_matches(
    repo: ReconciliationRepository,
    *,
    tenant_id: int,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Retourne les rapprochements à valider manuellement."""
    if tenant_id is None or int(tenant_id) <= 0:
        raise ValueError("tenant_id must be a positive integer.")

    status_clean = status.strip().lower() if status else None
    if status_clean and status_clean not in ALLOWED_MATCH_STATUSES:
        raise ValueError(
            f"Invalid status. Choose from {', '.join(sorted(ALLOWED_MATCH_STATUSES))}."
        )

    records = repo.fetch_matches(int(tenant_id), status_clean)
    return [dict(record) for record in records]


__all__ = ["ALLOWED_MATCH_STATUSES", "ReconciliationRepository", "fetch_matches"]
