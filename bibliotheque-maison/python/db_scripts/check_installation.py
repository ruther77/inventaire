#!/usr/bin/env python3
"""Vérification d'installation pour db_scripts."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_module_import() -> bool:
    try:
        import db_scripts
        print(f"db_scripts module v{db_scripts.__version__}")
        return True
    except ImportError as exc:
        print(f"db_scripts import failed: {exc}")
        return False


def check_assets() -> bool:
    base_dir = Path(__file__).resolve().parent / "sql"
    if not base_dir.exists():
        print("sql directory not found")
        return False
    if not list(base_dir.glob('*.sql')) and not list((base_dir / 'migrations').glob('*.sql')):
        print("no SQL scripts found")
        return False
    print("sql assets present")
    return True


def main() -> None:
    print("DB_SCRIPTS MODULE - INSTALLATION CHECK")
    print("=" * 60)

    module_ok = check_module_import()
    assets_ok = check_assets() if module_ok else False

    if not (module_ok and assets_ok):
        raise SystemExit(1)

    print("db_scripts OK")


if __name__ == "__main__":
    main()
