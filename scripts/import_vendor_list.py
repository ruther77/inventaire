"""Convertit un tableau brut de fournisseurs en CSV pour le dictionnaire."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Iterable


DEFAULT_OUTPUT = Path("data/vendor_category_mapping.csv")


def _parse_aliases(raw: str) -> tuple[str, ...]:
    tokens = [token.strip() for token in re.split(r"[,\|/]", raw) if token.strip()]
    return tuple(token.upper() for token in tokens)


def _parse_line(line: str) -> tuple[str, str, str | None] | None:
    parts = [part.strip() for part in re.split(r"\t|  {2,}", line) if part.strip()]
    if len(parts) < 2:
        return None
    aliases = "|".join(_parse_aliases(parts[0]))
    category = parts[1]
    types = parts[2] if len(parts) > 2 else ""
    return aliases, category, types


def _detect_domain(line: str) -> str | None:
    stripped = re.sub(r"^[^\wÀ-ÿ]*", "", line).strip()
    if not stripped:
        return None
    if "Fournisseur" in stripped:
        return None
    return stripped


def load_existing(output: Path) -> set[tuple[str, str, str]]:
    if not output.exists():
        return set()
    seen: set[tuple[str, str, str]] = set()
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
    parser = argparse.ArgumentParser(description="Génère un CSV compatible vendor_category_mapping.")
    parser.add_argument("input", type=Path, help="Fichier texte brut à analyser.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Fichier CSV cible.")
    parser.add_argument("--overwrite", action="store_true", help="Réécrit le fichier au lieu d'ajouter.")
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(args.input)

    records: list[tuple[str, str, str, str]] = []
    domain = "Général"
    with args.input.open(encoding="utf-8") as stream:
        for raw in stream:
            text = raw.strip()
            if not text:
                continue
            detected = _detect_domain(text)
            if detected:
                domain = detected
                continue
            parsed = _parse_line(text)
            if not parsed:
                continue
            aliases, category, types = parsed
            records.append((domain, aliases, category, types))

    if not records:
        print("Aucune ligne n'a été trouvée dans le fichier source.")
        return

    write_header = args.overwrite or not args.output.exists()
    existing = set() if args.overwrite else load_existing(args.output)

    mode = "w" if args.overwrite else "a"
    with args.output.open(mode, encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        if write_header:
            writer.writerow(["domain", "aliases", "category", "types"])
        for domain, aliases, category, types in records:
            key = (domain, aliases, category)
            if key in existing:
                continue
            existing.add(key)
            writer.writerow([domain, aliases, category, types])

    print(f"{len(records)} lignes analysées, {len(existing)} entrées présentes.")


if __name__ == "__main__":
    main()
