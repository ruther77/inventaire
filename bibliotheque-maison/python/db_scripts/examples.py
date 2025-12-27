#!/usr/bin/env python3
"""Exemples pour db_scripts."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db_scripts import collect_scripts, read_sql


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent / "sql"
    manifest = collect_scripts(base_dir)
    print("Scripts:", manifest)

    if manifest["root"]:
        first = base_dir / manifest["root"][0]
        print("First script path:", first)
        print("First script preview:")
        print(read_sql(first)[:200])
