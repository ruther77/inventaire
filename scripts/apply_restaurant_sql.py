"""Applique les fichiers SQL/DDL fournis dans docs/restaurant/*.txt."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as fp:
        for raw in fp:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

_load_dotenv(PROJECT_ROOT / ".env")

from core.data_repository import get_engine

DEFAULT_FILES = [
    Path("docs/restaurant/RESTAURANT_DEBUT_MODELISATION.txt"),
    Path("docs/restaurant/PLATS_EN_SAUCE_MODELISATION.txt"),
    Path("docs/restaurant/BOM_MENU.txt"),
    Path("docs/restaurant/CHARGE_RESTO.txt"),
    Path("docs/restaurant/PARTIE_3_MENU.txt"),
]


def apply_sql_file(conn, path: Path) -> None:
    sql_content = path.read_text(encoding="utf-8")
    try:
        conn.exec_driver_sql(sql_content)
    except TypeError:
        # Certains fichiers SQL déclenchent un bug de SQLAlchemy ; utiliser
        # directement le curseur DBAPI permet d’éviter cette exception.
        cursor = conn.connection.cursor()
        try:
            cursor.execute(sql_content)
        finally:
            cursor.close()


def main(files: list[Path]) -> None:
    engine = get_engine()
    applied = 0
    with engine.begin() as conn:
        for file_path in files:
            resolved = file_path if file_path.is_absolute() else Path.cwd() / file_path
            if not resolved.exists():
                raise FileNotFoundError(f"Fichier SQL introuvable: {resolved}")
            print(f"[restaurant-seed] Application de {resolved} …")
            apply_sql_file(conn, resolved)
            applied += 1
    print(f"[restaurant-seed] {applied} fichier(s) SQL appliqués avec succès.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Applique les scripts SQL Restaurant HQ.")
    parser.add_argument(
        "--files",
        nargs="*",
        type=Path,
        default=DEFAULT_FILES,
        help="Liste des fichiers SQL à appliquer (ordre respecté).",
    )
    args = parser.parse_args()
    main(args.files)
