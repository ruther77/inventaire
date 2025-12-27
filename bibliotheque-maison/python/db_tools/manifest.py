"""Utilitaires pour inspecter les dossiers de scripts SQL."""

from __future__ import annotations

from pathlib import Path


def find_sql_files(base_dir: Path) -> list[Path]:
    """Retourne la liste triée des fichiers SQL sous base_dir (non récursif)."""
    if not base_dir.exists():
        return []
    return sorted([p for p in base_dir.iterdir() if p.is_file() and p.suffix == ".sql"])


def read_sql(path: Path) -> str:
    """Lit un fichier SQL en texte."""
    return path.read_text(encoding="utf-8")


def collect_db_scripts(base_dir: Path) -> dict[str, list[str]]:
    """Collecte les scripts SQL racine et migrations pour documentation."""
    base_dir = base_dir.resolve()
    root_files = [p.name for p in find_sql_files(base_dir)]
    migrations_dir = base_dir / "migrations"
    migration_files = [p.name for p in find_sql_files(migrations_dir)]
    return {
        "root": root_files,
        "migrations": migration_files,
    }


__all__ = [
    "collect_db_scripts",
    "find_sql_files",
    "read_sql",
]
