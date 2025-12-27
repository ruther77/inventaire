"""Charge les correspondances de catégories fournisseurs depuis un CSV."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Iterable, Sequence


def _parse_aliases(raw: str) -> tuple[str, ...]:
    return tuple(alias.strip().upper() for alias in raw.split("|") if alias.strip())


def _parse_types(raw: str | None) -> tuple[str, ...] | None:
    if not raw:
        return None
    items = tuple(item.strip() for item in raw.split("|") if item.strip())
    return items or None


def load_vendor_category_rules(
    mapping_path: str | os.PathLike[str] | None = None,
) -> tuple[tuple[tuple[str, ...], str, Sequence[str] | None], ...]:
    """Charge les règles de catégories fournisseurs depuis un fichier CSV.

    The CSV file must include at least these columns:
    - aliases (pipe-separated vendor aliases)
    - category (category name)
    - types (optional pipe-separated sub-types)

    Si mapping_path n'est pas fourni, le loader consulte la variable
    d'environnement VENDOR_CATEGORY_FILE. Si aucun fichier n'est trouvé,
    un tuple vide est retourné.
    """
    resolved_path: Path | None = None
    if mapping_path is not None:
        resolved_path = Path(mapping_path)
    else:
        env_path = os.getenv("VENDOR_CATEGORY_FILE")
        if env_path:
            resolved_path = Path(env_path)

    if resolved_path is None or not resolved_path.exists():
        return ()

    rules: list[tuple[tuple[str, ...], str, Sequence[str] | None]] = []
    with resolved_path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            aliases = _parse_aliases(row.get("aliases", ""))
            category = (row.get("category") or "").strip()
            types = _parse_types(row.get("types"))
            if not aliases or not category:
                continue
            rules.append((aliases, category, types))

    return tuple(rules)


__all__ = ["load_vendor_category_rules"]
