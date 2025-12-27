"""Utilitaires et assets de scripts SQL."""

from .sql_utils import (
    collect_scripts,
    compute_checksum,
    find_sql_files,
    read_sql,
)

__all__ = [
    "collect_scripts",
    "compute_checksum",
    "find_sql_files",
    "read_sql",
]

__version__ = "1.0.0"
