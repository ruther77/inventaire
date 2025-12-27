"""Helpers de jobs zero-click avec stockage injectable."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol
import json


ALLOWED_STATUSES = {"pending", "processing", "completed", "failed"}


@dataclass(frozen=True)
class JobStatus:
    """Payload de statut de job normalisé."""
    status: str
    updated_at: datetime
    completed_at: datetime | None
    result: dict[str, Any] | None
    error: str | None


class JobRepository(Protocol):
    """Interface de stockage pour les jobs zero-click."""

    def create_job(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        ...

    def update_job(self, job_id: str, payload: Mapping[str, Any]) -> None:
        ...

    def get_job(self, job_id: str, tenant_id: int | None = None) -> Mapping[str, Any] | None:
        ...


def _normalize_job_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Normalise les payloads de jobs issus du dépôt."""
    result_raw = record.get("result")
    if isinstance(result_raw, str):
        try:
            result_parsed = json.loads(result_raw)
        except json.JSONDecodeError:
            result_parsed = None
    else:
        result_parsed = result_raw

    return {
        "job_id": record.get("job_id"),
        "tenant_id": record.get("tenant_id"),
        "session_id": record.get("session_id"),
        "status": record.get("status"),
        "filename": record.get("filename"),
        "supplier_hint": record.get("supplier_hint"),
        "margin_percent": record.get("margin_percent"),
        "auto_confirm": record.get("auto_confirm"),
        "result": result_parsed,
        "error": record.get("error"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
        "completed_at": record.get("completed_at"),
    }


def create_job(
    repo: JobRepository,
    job_id: str,
    tenant_id: int,
    *,
    filename: str | None = None,
    supplier_hint: str | None = None,
    margin_percent: float = 40.0,
    auto_confirm: bool = True,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Crée une nouvelle entrée de job zero-click."""
    if not job_id or not job_id.strip():
        raise ValueError("job_id must be provided.")
    if tenant_id is None or int(tenant_id) <= 0:
        raise ValueError("tenant_id must be a positive integer.")
    if margin_percent < 0 or margin_percent > 100:
        raise ValueError("margin_percent must be between 0 and 100.")

    payload = {
        "job_id": job_id.strip(),
        "tenant_id": int(tenant_id),
        "session_id": session_id,
        "status": "pending",
        "filename": filename,
        "supplier_hint": supplier_hint,
        "margin_percent": float(margin_percent),
        "auto_confirm": bool(auto_confirm),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    created = repo.create_job(payload)
    if not created:
        raise RuntimeError("Job creation failed.")

    return _normalize_job_record(created)


def update_job_status(
    repo: JobRepository,
    job_id: str,
    status: str,
    *,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> JobStatus:
    """Met à jour le statut du job et ses timestamps."""
    if not job_id or not job_id.strip():
        raise ValueError("job_id must be provided.")
    status_clean = (status or "").strip().lower()
    if status_clean not in ALLOWED_STATUSES:
        raise ValueError(f"Invalid status. Choose from {', '.join(sorted(ALLOWED_STATUSES))}.")

    now = datetime.now(timezone.utc)
    completed_at = now if status_clean in {"completed", "failed"} else None
    payload = {
        "status": status_clean,
        "updated_at": now,
        "completed_at": completed_at,
        "result": result,
        "error": error,
    }

    repo.update_job(job_id.strip(), payload)

    return JobStatus(
        status=status_clean,
        updated_at=now,
        completed_at=completed_at,
        result=result,
        error=error,
    )


def get_job(
    repo: JobRepository,
    job_id: str,
    *,
    tenant_id: int | None = None,
) -> dict[str, Any] | None:
    """Récupère un job et normalise le payload."""
    if not job_id or not job_id.strip():
        raise ValueError("job_id must be provided.")

    record = repo.get_job(job_id.strip(), tenant_id=tenant_id)
    if not record:
        return None
    return _normalize_job_record(record)


__all__ = [
    "ALLOWED_STATUSES",
    "JobRepository",
    "JobStatus",
    "create_job",
    "get_job",
    "update_job_status",
]
