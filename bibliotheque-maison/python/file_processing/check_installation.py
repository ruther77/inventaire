#!/usr/bin/env python3
"""
Vérificateur d'installation pour le module file_processing.

Vérifie que toutes les dépendances et composants optionnels sont correctement installés.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_pandas():
    """Vérifie si pandas est installé."""
    try:
        import pandas as pd
        print(f"✓ pandas {pd.__version__}")
        return True
    except ImportError:
        print("✗ pandas NOT INSTALLED")
        print("  Install: pip install pandas")
        return False


def check_pypdf():
    """Vérifie si pypdf ou PyPDF2 est installé."""
    try:
        import pypdf
        print(f"✓ pypdf {pypdf.__version__}")
        return True
    except ImportError:
        try:
            import PyPDF2
            print(f"✓ PyPDF2 {PyPDF2.__version__}")
            return True
        except ImportError:
            print("✗ pypdf/PyPDF2 NOT INSTALLED (optional)")
            print("  Install: pip install pypdf")
            return False


def check_pdftotext():
    """Vérifie si pdftotext est disponible."""
    import subprocess

    try:
        result = subprocess.run(
            ["pdftotext", "-v"],
            capture_output=True,
            text=True,
        )
        # pdftotext outputs version to stderr
        version_info = result.stderr.split("\n")[0] if result.stderr else "unknown version"
        print(f"✓ pdftotext ({version_info})")
        return True
    except FileNotFoundError:
        print("✗ pdftotext NOT INSTALLED (optional)")
        print("  Install:")
        print("    Debian/Ubuntu: sudo apt-get install poppler-utils")
        print("    macOS: brew install poppler")
        return False


def check_module_import():
    """Vérifie si le module file_processing peut être importé."""
    try:
        import file_processing
        print(f"✓ file_processing module v{file_processing.__version__}")
        return True
    except ImportError as e:
        print(f"✗ file_processing module IMPORT FAILED: {e}")
        return False


def check_module_functions():
    """Vérifie que toutes les fonctions attendues sont disponibles."""
    try:
        from file_processing import (
            extract_text_from_pdf,
            extract_text_from_pdfs,
            run_pdftotext,
            parse_csv_with_encoding,
            detect_csv_delimiter,
            normalize_column_names,
            read_csv_robust,
            write_csv_robust,
        )
        print("✓ All expected functions are available")
        return True
    except ImportError as e:
        print(f"✗ Function import failed: {e}")
        return False


def main():
    """Exécute toutes les vérifications d'installation."""
    print("FILE PROCESSING MODULE - INSTALLATION CHECK")
    print("=" * 60)
    print()

    print("Required dependencies:")
    print("-" * 60)
    pandas_ok = check_pandas()
    print()

    print("Optional dependencies (at least one PDF library recommended):")
    print("-" * 60)
    pypdf_ok = check_pypdf()
    pdftotext_ok = check_pdftotext()
    print()

    print("Module import:")
    print("-" * 60)
    module_ok = check_module_import()
    if module_ok:
        functions_ok = check_module_functions()
    else:
        functions_ok = False
    print()

    print("=" * 60)
    print("\nSummary:")
    print("-" * 60)

    all_ok = pandas_ok and module_ok and functions_ok
    pdf_ok = pypdf_ok or pdftotext_ok

    if all_ok:
        print("✓ Core installation: OK")
    else:
        print("✗ Core installation: FAILED")

    if pdf_ok:
        print("✓ PDF support: OK")
    else:
        print("⚠ PDF support: LIMITED (install pypdf or pdftotext)")

    print()

    if all_ok and pdf_ok:
        print("✓ All checks passed! Module is ready to use.")
        return 0
    elif all_ok:
        print("⚠ Module works but PDF support is limited.")
        print("  Install pypdf or pdftotext for full functionality.")
        return 0
    else:
        print("✗ Installation incomplete. Fix errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
