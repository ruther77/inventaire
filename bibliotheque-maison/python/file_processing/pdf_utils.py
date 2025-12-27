"""
PDF text extraction utilities.

Provides functions to extract text from PDF files using either pypdf (PyPDF2)
or pdftotext command-line tool with automatic fallback.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


def extract_text_from_pdf(pdf_path: Path, use_layout: bool = False) -> str:
    """
    Extract text content from a PDF file with automatic fallback.

    First tries pypdf (or PyPDF2), then falls back to pdftotext if available.

    Args:
        pdf_path: Path to the PDF file
        use_layout: If True and pdftotext is used, preserve layout (-layout flag)

    Returns:
        Extracted text content as a string

    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        RuntimeError: If text extraction fails with all methods

    Examples:
        >>> from pathlib import Path
        >>> text = extract_text_from_pdf(Path("invoice.pdf"))
        >>> text = extract_text_from_pdf(Path("invoice.pdf"), use_layout=True)
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Try pypdf first (pure Python, no external dependencies)
    try:
        return _extract_with_pypdf(pdf_path)
    except (ImportError, Exception) as pypdf_error:
        # Fallback to pdftotext if pypdf fails
        try:
            return run_pdftotext(pdf_path, layout=use_layout)
        except (FileNotFoundError, subprocess.CalledProcessError) as pdftotext_error:
            raise RuntimeError(
                f"Failed to extract text from {pdf_path}. "
                f"pypdf error: {pypdf_error}. "
                f"pdftotext error: {pdftotext_error}"
            ) from pdftotext_error


def _extract_with_pypdf(pdf_path: Path) -> str:
    """
    Extract text using pypdf library (or PyPDF2 as fallback).

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Extracted text content

    Raises:
        ImportError: If neither pypdf nor PyPDF2 is installed
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except ImportError:
            raise ImportError(
                "Neither pypdf nor PyPDF2 is installed. "
                "Install one with: pip install pypdf"
            )

    with open(pdf_path, "rb") as f:
        reader = PdfReader(f)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
        return "\n".join(text_parts)


def run_pdftotext(pdf_path: Path, layout: bool = True) -> str:
    """
    Run pdftotext command-line tool to extract text from PDF.

    This is a wrapper around the pdftotext command from poppler-utils.
    Requires pdftotext to be installed on the system.

    Args:
        pdf_path: Path to the PDF file
        layout: If True, preserve original physical layout with -layout flag.
                This is useful for parsing structured invoices with columns.

    Returns:
        Extracted text content as a string

    Raises:
        FileNotFoundError: If pdftotext command is not found
        subprocess.CalledProcessError: If pdftotext execution fails

    Examples:
        >>> from pathlib import Path
        >>> # Extract with layout preservation (good for invoices)
        >>> text = run_pdftotext(Path("invoice.pdf"), layout=True)
        >>> # Extract without layout (good for flowing text)
        >>> text = run_pdftotext(Path("document.pdf"), layout=False)

    Notes:
        Install pdftotext on Debian/Ubuntu with:
            sudo apt-get install poppler-utils
        On macOS with Homebrew:
            brew install poppler
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    cmd = ["pdftotext"]
    if layout:
        cmd.append("-layout")
    cmd.extend([str(pdf_path), "-"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except FileNotFoundError:
        raise FileNotFoundError(
            "pdftotext command not found. Install poppler-utils:\n"
            "  Debian/Ubuntu: sudo apt-get install poppler-utils\n"
            "  macOS: brew install poppler"
        )


def extract_text_from_pdfs(
    pdf_paths: list[Path],
    use_layout: bool = False,
    skip_errors: bool = True,
) -> dict[Path, str]:
    """
    Extract text from multiple PDF files.

    Args:
        pdf_paths: List of paths to PDF files
        use_layout: If True, preserve layout when using pdftotext
        skip_errors: If True, skip files that fail to extract and continue.
                     If False, raise on first error.

    Returns:
        Dictionary mapping PDF paths to their extracted text.
        Failed extractions are omitted if skip_errors=True.

    Examples:
        >>> from pathlib import Path
        >>> pdfs = [Path("invoice1.pdf"), Path("invoice2.pdf")]
        >>> results = extract_text_from_pdfs(pdfs, use_layout=True)
        >>> for pdf_path, text in results.items():
        ...     print(f"{pdf_path.name}: {len(text)} characters")
    """
    results = {}
    for pdf_path in pdf_paths:
        try:
            text = extract_text_from_pdf(pdf_path, use_layout=use_layout)
            results[pdf_path] = text
        except Exception as e:
            if skip_errors:
                continue
            raise
    return results
