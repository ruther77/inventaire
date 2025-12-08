"""Ajoute un tableau fournisseur→catégorie depuis un CSV simple."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable


BASE_OUTPUT = Path("data/vendor_category_mapping.csv")


def _normalize_aliases(raw: str) -> tuple[str, ...]:
    return tuple(alias.strip().upper() for alias in raw.split(",") if alias.strip())


def _type_from_category(category: str) -> str:
    lower = category.lower()
    if "revenu" in lower or "encaissement" in lower:
        return "Entrée"
    return "Sortie"


def _iter_lines(path: Path) -> Iterable[str]:
    with path.open(encoding="utf-8") as stream:
        for raw in stream:
            line = raw.strip()
            if not line:
                continue
            yield line


def load_existing(output: Path) -> set[tuple[str, str, str]]:
    seen: set[tuple[str, str, str]] = set()
    if not output.exists():
        return seen
    with output.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            seen.add(
                (
                    row.get("domain", "").strip(),
                    row.get("aliases", "").strip(),
                    row.get("category", "").strip(),
                )
            )
    return seen


def main() -> None:
    parser = argparse.ArgumentParser(description="Convertit un CSV fournisseur/catégorie en dictionnaire.")
    parser.add_argument("input", type=Path, help="Fichier avec des lignes Domain ou Fournisseur,Categorie.")
    parser.add_argument("--output", type=Path, default=BASE_OUTPUT, help="CSV cible.")
    parser.add_argument("--overwrite", action="store_true", help="Réécrit le fichier cible.")
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(args.input)

    domain = "Général"
    records: list[tuple[str, str, str, str]] = []
    lines = list(_iter_lines(args.input))
    i = 0
    while i < len(lines):
        line = lines[i]
        if "," not in line:
            domain = line
            i += 1
            continue
        vendor, category = [col.strip() for col in line.split(",", 1)]
        if not vendor or not category:
            i += 1
            continue
        aliases = "|".join(_normalize_aliases(vendor))
        types = _type_from_category(category)
        records.append((domain, aliases, category, types))
        i += 1

    if not records:
        print("Aucune ligne exploitable.")
        return

    existing = set() if args.overwrite else load_existing(args.output)
    mode = "w" if args.overwrite else "a"
    with args.output.open(mode, encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        if args.overwrite:
            writer.writerow(["domain", "aliases", "category", "types"])
        for domain, aliases, category, types in records:
            key = (domain, aliases, category)
            if key in existing:
                continue
            existing.add(key)
            writer.writerow([domain, aliases, category, types])

    print(f"{len(records)} lignes analysées, {len(existing)} totales (après fusion).")


if __name__ == "__main__":
    main()
