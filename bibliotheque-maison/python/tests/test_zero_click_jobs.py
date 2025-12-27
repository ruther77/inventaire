"""Tests pour jobs.zero_click."""

from __future__ import annotations

from datetime import datetime, timezone

from jobs.zero_click import ALLOWED_STATUSES, create_job, get_job, update_job_status


class MemoryJobRepo:
    def __init__(self):
        self.jobs = {}

    def create_job(self, payload):
        self.jobs[payload["job_id"]] = dict(payload)
        return dict(payload)

    def update_job(self, job_id, payload):
        if job_id not in self.jobs:
            return
        self.jobs[job_id].update(payload)

    def get_job(self, job_id, tenant_id=None):
        job = self.jobs.get(job_id)
        if not job:
            return None
        if tenant_id is not None and job.get("tenant_id") != tenant_id:
            return None
        return dict(job)


def test_create_job_and_get():
    repo = MemoryJobRepo()
    created = create_job(repo, "job-1", 1, margin_percent=35.0)
    assert created["job_id"] == "job-1"
    fetched = get_job(repo, "job-1", tenant_id=1)
    assert fetched["status"] == "pending"


def test_update_job_status_sets_completed_at():
    repo = MemoryJobRepo()
    create_job(repo, "job-2", 2)
    status = update_job_status(repo, "job-2", "completed", result={"ok": True})
    assert status.completed_at is not None
    stored = get_job(repo, "job-2")
    assert stored["status"] == "completed"
    assert stored["result"]["ok"] is True


def test_update_job_status_rejects_invalid():
    repo = MemoryJobRepo()
    create_job(repo, "job-3", 3)
    try:
        update_job_status(repo, "job-3", "unknown")
    except ValueError as exc:
        assert "Invalid status" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid status")
