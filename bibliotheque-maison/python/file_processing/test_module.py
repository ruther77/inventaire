#!/usr/bin/env python3
"""
Tests rapides pour le module file_processing.

À exécuter avec : python test_module.py
"""

import sys
from pathlib import Path
import tempfile
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_csv_delimiter_detection():
    """Teste la détection du délimiteur CSV."""
    from file_processing import detect_csv_delimiter

    # Test semicolon
    content_semicolon = "Name;Age;City\nAlice;30;Paris\nBob;25;Lyon"
    assert detect_csv_delimiter(content_semicolon) == ";"

    # Test comma
    content_comma = "Name,Age,City\nAlice,30,Paris\nBob,25,Lyon"
    assert detect_csv_delimiter(content_comma) == ","

    # Test tab
    content_tab = "Name\tAge\tCity\nAlice\t30\tParis\nBob\t25\tLyon"
    assert detect_csv_delimiter(content_tab) == "\t"

    print("✓ CSV delimiter detection works")


def test_column_normalization():
    """Teste la normalisation des noms de colonnes."""
    from file_processing import normalize_column_names

    df = pd.DataFrame({
        "Nom Prénom": [1, 2],
        "Âge (années)": [30, 25],
        "Ville / Région": ["Paris", "Lyon"]
    })

    normalized = normalize_column_names(df)
    expected_columns = ["nom_prenom", "age_annees", "ville_region"]

    assert list(normalized.columns) == expected_columns
    print("✓ Column normalization works")


def test_csv_write_read():
    """Teste l'écriture puis lecture CSV (aller-retour)."""
    from file_processing import write_csv_robust, read_csv_robust

    # Create test data
    df = pd.DataFrame({
        "nom": ["Alice", "Bob", "Charlie"],
        "age": [30, 25, 35],
        "ville": ["Paris", "Lyon", "Marseille"]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test.csv"

        # Write
        write_csv_robust(df, csv_path, delimiter=";")

        # Read back
        df_read = read_csv_robust(csv_path, normalize_columns=False)

        # Compare
        pd.testing.assert_frame_equal(df, df_read)

    print("✓ CSV write/read roundtrip works")


def test_csv_encoding_detection():
    """Teste la détection d'encodage CSV."""
    from file_processing import parse_csv_with_encoding

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test.csv"

        # Write UTF-8
        df = pd.DataFrame({"nom": ["Éléonore", "François"], "prénom": ["Müller", "Château"]})
        df.to_csv(csv_path, index=False, encoding="utf-8", sep=";")

        # Read with auto-detection
        df_read = parse_csv_with_encoding(csv_path)
        assert len(df_read) == 2
        assert "nom" in df_read.columns

        # Write Latin-1
        csv_path_latin = Path(tmpdir) / "test_latin.csv"
        df.to_csv(csv_path_latin, index=False, encoding="latin-1", sep=";")

        # Read with auto-detection (should fallback to latin-1)
        df_read_latin = parse_csv_with_encoding(csv_path_latin)
        assert len(df_read_latin) == 2

    print("✓ CSV encoding detection works")


def test_pdf_imports():
    """Teste que les utilitaires PDF peuvent être importés."""
    try:
        from file_processing import extract_text_from_pdf, run_pdftotext, extract_text_from_pdfs
        print("✓ PDF utilities can be imported")
    except ImportError as e:
        print(f"✗ Failed to import PDF utilities: {e}")


def main():
    """Exécute tous les tests."""
    print("Testing file_processing module...\n")

    try:
        test_csv_delimiter_detection()
        test_column_normalization()
        test_csv_write_read()
        test_csv_encoding_detection()
        test_pdf_imports()

        print("\n✓ All tests passed!")
        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
