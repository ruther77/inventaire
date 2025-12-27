"""
File processing utilities for PDF and CSV files.

This module provides standalone utilities for:
- Extracting text from PDF files with automatic fallback
- Parsing CSV files with encoding and delimiter detection
- Normalizing column names for easier data manipulation

Examples:
    PDF text extraction:
        >>> from pathlib import Path
        >>> from file_processing import extract_text_from_pdf, run_pdftotext
        >>> # Auto-detect best method
        >>> text = extract_text_from_pdf(Path("invoice.pdf"))
        >>> # Force pdftotext with layout
        >>> text = run_pdftotext(Path("invoice.pdf"), layout=True)

    CSV parsing:
        >>> from file_processing import read_csv_robust, normalize_column_names
        >>> # Read CSV with auto-detection
        >>> df = read_csv_robust(Path("data.csv"))
        >>> # Manual parsing with custom encodings
        >>> df = parse_csv_with_encoding(
        ...     Path("data.csv"),
        ...     encodings=['utf-8', 'iso-8859-1']
        ... )
"""

from file_processing.csv_utils import (
    detect_csv_delimiter,
    normalize_column_names,
    parse_csv_with_encoding,
    read_csv_robust,
    write_csv_robust,
)
from file_processing.pdf_utils import (
    extract_text_from_pdf,
    extract_text_from_pdfs,
    run_pdftotext,
)

__all__ = [
    # PDF utilities
    "extract_text_from_pdf",
    "extract_text_from_pdfs",
    "run_pdftotext",
    # CSV utilities
    "parse_csv_with_encoding",
    "detect_csv_delimiter",
    "normalize_column_names",
    "read_csv_robust",
    "write_csv_robust",
]

__version__ = "1.0.0"
