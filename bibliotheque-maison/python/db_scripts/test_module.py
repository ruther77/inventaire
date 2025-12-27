#!/usr/bin/env python3
"""Tests pour db_scripts."""

import sys
from pathlib import Path
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from db_scripts import collect_scripts, compute_checksum, find_sql_files, read_sql


def test_find_sql_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "a.sql").write_text("SELECT 1;", encoding="utf-8")
        (tmp_path / "b.txt").write_text("ignore", encoding="utf-8")
        files = find_sql_files(tmp_path)
        assert [p.name for p in files] == ["a.sql"]
    print("✓ find_sql_files")


def test_collect_scripts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "root.sql").write_text("SELECT 2;", encoding="utf-8")
        migrations = tmp_path / "migrations"
        migrations.mkdir()
        (migrations / "001.sql").write_text("SELECT 3;", encoding="utf-8")
        manifest = collect_scripts(tmp_path)
        assert manifest["root"] == ["root.sql"]
        assert manifest["migrations"] == ["001.sql"]
    print("✓ collect_scripts")


def test_compute_checksum() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        path = tmp_path / "script.sql"
        path.write_text("SELECT 4;", encoding="utf-8")
        assert len(compute_checksum(path)) == 16
    print("✓ compute_checksum")


def test_read_sql() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        path = tmp_path / "script.sql"
        path.write_text("SELECT 5;", encoding="utf-8")
        assert read_sql(path) == "SELECT 5;"
    print("✓ read_sql")


def main() -> None:
    test_find_sql_files()
    test_collect_scripts()
    test_compute_checksum()
    test_read_sql()
    print("db_scripts tests OK")


if __name__ == "__main__":
    main()
