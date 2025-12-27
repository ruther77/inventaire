"""Tests pour db_tools.manifest."""

from __future__ import annotations

from pathlib import Path

from db_tools.manifest import collect_db_scripts, find_sql_files, read_sql


def test_find_sql_files(tmp_path: Path):
    (tmp_path / "a.sql").write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "b.txt").write_text("ignore", encoding="utf-8")
    files = find_sql_files(tmp_path)
    assert [p.name for p in files] == ["a.sql"]


def test_collect_db_scripts(tmp_path: Path):
    (tmp_path / "root.sql").write_text("SELECT 2;", encoding="utf-8")
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "001_init.sql").write_text("SELECT 3;", encoding="utf-8")
    manifest = collect_db_scripts(tmp_path)
    assert manifest["root"] == ["root.sql"]
    assert manifest["migrations"] == ["001_init.sql"]


def test_read_sql(tmp_path: Path):
    path = tmp_path / "script.sql"
    path.write_text("SELECT 4;", encoding="utf-8")
    assert read_sql(path) == "SELECT 4;"
