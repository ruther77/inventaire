"""Utilitaires pour inspecter les dossiers de scripts SQL."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScriptGroup:
    """Groupe de scripts SQL."""
    name: str
    files: list[Path]


def find_sql_files(base_dir: Path, *, recursive: bool = False) -> list[Path]:
    """Retourne la liste triée des fichiers SQL sous base_dir."""
    if not base_dir.exists():
        return []
    if recursive:
        files = [p for p in base_dir.rglob('*.sql') if p.is_file()]
    else:
        files = [p for p in base_dir.iterdir() if p.is_file() and p.suffix == '.sql']
    return sorted(files)


def read_sql(path: Path) -> str:
    """Lit un fichier SQL en texte UTF-8."""
    return path.read_text(encoding='utf-8')


def compute_checksum(path: Path) -> str:
    """Retourne un checksum court pour un fichier SQL."""
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()[:16]


def collect_scripts(base_dir: Path) -> dict[str, list[str]]:
    """Collecte les scripts SQL racine et migrations pour la documentation."""
    base_dir = base_dir.resolve()
    root_files = [p.name for p in find_sql_files(base_dir, recursive=False)]
    migrations_dir = base_dir / 'migrations'
    migration_files = [p.name for p in find_sql_files(migrations_dir, recursive=False)]
    return {
        'root': root_files,
        'migrations': migration_files,
    }


__all__ = [
    'ScriptGroup',
    'collect_scripts',
    'compute_checksum',
    'find_sql_files',
    'read_sql',
]
