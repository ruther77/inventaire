"""Maintenance helpers (backups listing)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

BACKUP_DIR = Path("/backups")


def list_backups(limit: int | None = None) -> list[dict[str, object]]:
    root = BACKUP_DIR if BACKUP_DIR.exists() else Path("backups")
    if not root.exists():
        return []

    files = [path for path in root.iterdir() if path.is_file() and path.suffix in {".gz", ".sql", ".zip"}]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    if limit:
        files = files[:limit]

    entries: list[dict[str, object]] = []
    for path in files:
        stat = path.stat()
        entries.append(
            {
                "name": path.name,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                "path": str(path),
            }
        )
    return entries
