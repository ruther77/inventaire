"""Schemas for maintenance endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel


class BackupEntry(BaseModel):
    name: str
    size_bytes: int
    created_at: datetime


class BackupListResponse(BaseModel):
    backups: List[BackupEntry]


__all__ = ["BackupEntry", "BackupListResponse"]
