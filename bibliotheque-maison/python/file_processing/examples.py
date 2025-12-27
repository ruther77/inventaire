#!/usr/bin/env python3
"""
Examples of using the file_processing module.

These examples demonstrate common use cases for PDF and CSV processing.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_processing import (
    extract_text_from_pdf,
    run_pdftotext,
    extract_text_from_pdfs,
    read_csv_robust,
    parse_csv_with_encoding,
    detect_csv_delimiter,
    normalize_column_names,
    write_csv_robust,
)
import pandas as pd


def example_pdf_single():
    """Exemple : extraire le texte d'un seul PDF."""
    print("=== Example: Single PDF extraction ===")

    pdf_path = Path("invoice.pdf")

    # Method 1: Auto-detect best extraction method
    try:
        text = extract_text_from_pdf(pdf_path)
        print(f"Extracted {len(text)} characters from {pdf_path.name}")
        print(f"First 200 chars: {text[:200]}...")
    except FileNotFoundError:
        print(f"PDF not found: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")

    # Method 2: Force pdftotext with layout (good for structured invoices)
    try:
        text = run_pdftotext(pdf_path, layout=True)
        print(f"Extracted {len(text)} characters with layout preservation")
    except FileNotFoundError:
        print(f"PDF or pdftotext not found")
    except Exception as e:
        print(f"Error: {e}")

    print()


def example_pdf_batch():
    """Exemple : extraire le texte de plusieurs PDF."""
    print("=== Example: Batch PDF extraction ===")

    invoice_dir = Path("invoices/")
    if not invoice_dir.exists():
        print(f"Directory not found: {invoice_dir}")
        print()
        return

    pdf_files = list(invoice_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files")

    # Extract all with error handling
    results = extract_text_from_pdfs(pdf_files, use_layout=True, skip_errors=True)

    print(f"Successfully extracted {len(results)}/{len(pdf_files)} PDFs")
    for pdf_path, text in results.items():
        print(f"  - {pdf_path.name}: {len(text)} characters")

    print()


def example_csv_robust_read():
    """Exemple : lecture CSV robuste avec auto-détection."""
    print("=== Example: Robust CSV reading ===")

    csv_path = Path("data.csv")

    # Method 1: Full auto-detection (encoding + delimiter + normalization)
    try:
        df = read_csv_robust(csv_path)
        print(f"Read {len(df)} rows, {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
        print(df.head())
    except FileNotFoundError:
        print(f"CSV not found: {csv_path}")

    print()


def example_csv_custom_encoding():
    """Exemple : lecture CSV avec encodages personnalisés."""
    print("=== Example: Custom encoding CSV read ===")

    csv_path = Path("data_latin.csv")

    try:
        # Try specific encodings
        df = parse_csv_with_encoding(
            csv_path,
            encodings=["utf-8", "iso-8859-1", "cp1252"],
            delimiter=";",
        )
        print(f"Read {len(df)} rows with custom encoding detection")
    except FileNotFoundError:
        print(f"CSV not found: {csv_path}")
    except Exception as e:
        print(f"Error: {e}")

    print()


def example_delimiter_detection():
    """Exemple : détecter le délimiteur CSV."""
    print("=== Example: Delimiter detection ===")

    samples = [
        ("Name;Age;City\nAlice;30;Paris\nBob;25;Lyon", "Semicolon"),
        ("Name,Age,City\nAlice,30,Paris\nBob,25,Lyon", "Comma"),
        ("Name\tAge\tCity\nAlice\t30\tParis\nBob\t25\tLyon", "Tab"),
        ("Name|Age|City\nAlice|30|Paris\nBob|25|Lyon", "Pipe"),
    ]

    for content, description in samples:
        delimiter = detect_csv_delimiter(content)
        delimiter_name = {";": "semicolon", ",": "comma", "\t": "tab", "|": "pipe"}.get(
            delimiter, repr(delimiter)
        )
        print(f"{description}: detected {delimiter_name}")

    print()


def example_normalize_columns():
    """Exemple : normaliser les noms de colonnes."""
    print("=== Example: Column normalization ===")

    # Create DataFrame with messy column names
    df = pd.DataFrame(
        {
            "Nom Prénom": ["Alice Dupont", "Bob Martin"],
            "Âge (années)": [30, 25],
            "Ville / Région": ["Paris - IDF", "Lyon - AURA"],
            "Prix d'achat HT": [100.50, 200.75],
        }
    )

    print("Original columns:")
    print(list(df.columns))

    # Normalize
    df_normalized = normalize_column_names(df)

    print("\nNormalized columns:")
    print(list(df_normalized.columns))

    # Custom normalization
    df_custom = normalize_column_names(
        df, lowercase=False, remove_accents=True, replace_spaces="_"
    )

    print("\nCustom normalization (keep case):")
    print(list(df_custom.columns))

    print()


def example_csv_write():
    """Exemple : écrire un CSV au format européen."""
    print("=== Example: CSV writing ===")

    # Create sample data
    df = pd.DataFrame(
        {
            "nom": ["Alice", "Bob", "Charlie"],
            "prenom": ["Dupont", "Martin", "Bernard"],
            "age": [30, 25, 35],
            "ville": ["Paris", "Lyon", "Marseille"],
        }
    )

    output_path = Path("/tmp/output_example.csv")

    # Write with European defaults (UTF-8, semicolon)
    write_csv_robust(df, output_path)
    print(f"Written to: {output_path}")

    # Verify by reading back
    df_read = read_csv_robust(output_path, normalize_columns=False)
    print(f"Read back {len(df_read)} rows")

    # Write with comma delimiter
    output_path_comma = Path("/tmp/output_comma.csv")
    write_csv_robust(df, output_path_comma, delimiter=",")
    print(f"Written with comma delimiter to: {output_path_comma}")

    print()


def example_complete_workflow():
    """Exemple : workflow complet combinant PDF et CSV."""
    print("=== Example: Complete workflow ===")

    # 1. Extract text from PDF invoices
    print("Step 1: Extract PDF invoices")
    invoice_dir = Path("invoices/")
    if invoice_dir.exists():
        pdf_files = list(invoice_dir.glob("*.pdf"))[:3]  # Limit to 3 for demo
        pdf_texts = extract_text_from_pdfs(pdf_files, use_layout=True, skip_errors=True)
        print(f"  Extracted {len(pdf_texts)} PDFs")
    else:
        print(f"  Invoice directory not found: {invoice_dir}")

    # 2. Read CSV with product catalog
    print("\nStep 2: Read product catalog")
    catalog_path = Path("catalog.csv")
    if catalog_path.exists():
        df_catalog = read_csv_robust(catalog_path)
        print(f"  Loaded {len(df_catalog)} products")
        print(f"  Columns: {list(df_catalog.columns)}")
    else:
        print(f"  Catalog not found: {catalog_path}")
        # Create dummy data for demo
        df_catalog = pd.DataFrame(
            {
                "nom": ["Product A", "Product B", "Product C"],
                "prix": [10.50, 20.75, 30.00],
            }
        )

    # 3. Process and normalize
    print("\nStep 3: Process data")
    df_normalized = normalize_column_names(df_catalog)
    print(f"  Normalized column names: {list(df_normalized.columns)}")

    # 4. Export results
    print("\nStep 4: Export results")
    output_path = Path("/tmp/processed_catalog.csv")
    write_csv_robust(df_normalized, output_path)
    print(f"  Exported to: {output_path}")

    print()


def main():
    """Exécute tous les exemples."""
    print("FILE PROCESSING MODULE - EXAMPLES\n")
    print("=" * 60)
    print()

    # Run examples
    example_delimiter_detection()
    example_normalize_columns()
    example_csv_write()

    # These require actual files, so they may not work
    # Uncomment to test with your own files
    # example_pdf_single()
    # example_pdf_batch()
    # example_csv_robust_read()
    # example_csv_custom_encoding()
    # example_complete_workflow()

    print("=" * 60)
    print("\nDone! Check the code in examples.py to see how it works.")


if __name__ == "__main__":
    main()
