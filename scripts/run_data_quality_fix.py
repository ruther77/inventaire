#!/usr/bin/env python3
"""Applique le script de correction data-quality (prix manquants, stocks élevés, doublons, labels vides)."""
from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    fix_sql = root / "scripts" / "data_quality_fix.sql"
    cmd = ["docker", "compose", "--env-file", str(root / ".env"), "exec", "-T", "db", "psql", "-U", "postgres", "-d", "epicerie", "-f", str(fix_sql)]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
