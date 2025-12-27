"""
CSV parsing and normalization utilities.

Provides robust CSV reading with encoding detection, delimiter detection,
and column name normalization.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path
from typing import Optional

import pandas as pd


def parse_csv_with_encoding(
    file_path: Path,
    encodings: list[str] | None = None,
    delimiter: str | None = None,
    **kwargs,
) -> pd.DataFrame:
    """
    Parse CSV file with automatic encoding detection and fallback.

    Tries multiple encodings in order until one succeeds. Common encodings
    for European files are tried by default.

    Args:
        file_path: Path to CSV file
        encodings: List of encodings to try. Defaults to ['utf-8', 'latin-1', 'cp1252']
        delimiter: CSV delimiter. If None, will auto-detect using detect_csv_delimiter()
        **kwargs: Additional arguments passed to pandas.read_csv()

    Returns:
        DataFrame with parsed CSV data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file cannot be parsed with any encoding

    Examples:
        >>> from pathlib import Path
        >>> # Auto-detect encoding and delimiter
        >>> df = parse_csv_with_encoding(Path("data.csv"))
        >>> # Specify custom encodings
        >>> df = parse_csv_with_encoding(
        ...     Path("data.csv"),
        ...     encodings=['utf-8', 'iso-8859-1']
        ... )
        >>> # Pass additional pandas options
        >>> df = parse_csv_with_encoding(
        ...     Path("data.csv"),
        ...     skiprows=1,
        ...     na_values=['N/A', 'NULL']
        ... )
    """
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    if encodings is None:
        encodings = ["utf-8", "latin-1", "cp1252"]

    errors = []
    for encoding in encodings:
        try:
            # Read a small sample to detect delimiter if needed
            if delimiter is None:
                with open(file_path, "r", encoding=encoding) as f:
                    sample = f.read(4096)
                detected_delimiter = detect_csv_delimiter(sample)
            else:
                detected_delimiter = delimiter

            # Read the full CSV
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                delimiter=detected_delimiter,
                **kwargs,
            )
            return df

        except (UnicodeDecodeError, pd.errors.ParserError) as e:
            errors.append(f"{encoding}: {e}")
            continue

    raise ValueError(
        f"Failed to parse CSV with any encoding. Tried: {encodings}. "
        f"Errors: {'; '.join(errors)}"
    )


def detect_csv_delimiter(content: str, candidates: list[str] | None = None) -> str:
    """
    Detect the most likely CSV delimiter from file content.

    Analyzes the first few lines and counts delimiter occurrences to find
    the most consistent one.

    Args:
        content: Sample of CSV file content (first few KB is usually enough)
        candidates: List of delimiters to consider. Defaults to [';', ',', '\t', '|']

    Returns:
        The detected delimiter character

    Examples:
        >>> content = "Name;Age;City\\nAlice;30;Paris\\nBob;25;Lyon"
        >>> detect_csv_delimiter(content)
        ';'
        >>> content = "Name,Age,City\\nAlice,30,Paris\\nBob,25,Lyon"
        >>> detect_csv_delimiter(content)
        ','

    Notes:
        - The detection is based on consistency across lines
        - Returns ',' as fallback if detection is ambiguous
    """
    if candidates is None:
        candidates = [";", ",", "\t", "|"]

    lines = content.split("\n")[:10]  # Analyze first 10 lines
    if not lines:
        return ","

    # Count occurrences of each candidate in each line
    delimiter_scores = {}
    for delimiter in candidates:
        counts = [line.count(delimiter) for line in lines if line.strip()]
        if not counts:
            delimiter_scores[delimiter] = 0
            continue

        # Good delimiter should appear consistently across lines
        # Score = average count * consistency (inverse of std deviation)
        avg_count = sum(counts) / len(counts)
        if avg_count == 0:
            delimiter_scores[delimiter] = 0
        else:
            # Calculate variance
            variance = sum((c - avg_count) ** 2 for c in counts) / len(counts)
            std_dev = variance**0.5
            consistency = 1 / (1 + std_dev)  # Higher is better
            delimiter_scores[delimiter] = avg_count * consistency

    if not delimiter_scores:
        return ","

    # Return delimiter with highest score
    best_delimiter = max(delimiter_scores.items(), key=lambda x: x[1])
    return best_delimiter[0] if best_delimiter[1] > 0 else ","


def normalize_column_names(
    df: pd.DataFrame,
    lowercase: bool = True,
    remove_accents: bool = True,
    replace_spaces: str = "_",
    remove_special: bool = True,
) -> pd.DataFrame:
    """
    Normalize DataFrame column names for easier programmatic access.

    Converts column names to a consistent format by:
    - Converting to lowercase (optional)
    - Removing accents/diacritics (optional)
    - Replacing spaces with underscores (optional)
    - Removing special characters (optional)

    Args:
        df: Input DataFrame
        lowercase: Convert to lowercase
        remove_accents: Remove accents and diacritics
        replace_spaces: Character to replace spaces with (None to keep spaces)
        remove_special: Remove special characters (keep only alphanumeric and _)

    Returns:
        DataFrame with normalized column names (modifies a copy)

    Examples:
        >>> df = pd.DataFrame({"Nom Prénom": [1], "Âge (années)": [2]})
        >>> normalized = normalize_column_names(df)
        >>> list(normalized.columns)
        ['nom_prenom', 'age_annees']
        >>> # Keep original case
        >>> normalized = normalize_column_names(df, lowercase=False)
        >>> list(normalized.columns)
        ['Nom_Prenom', 'Age_annees']
        >>> # Keep accents
        >>> normalized = normalize_column_names(df, remove_accents=False)
        >>> list(normalized.columns)
        ['nom_prénom', 'âge_années']
    """
    df = df.copy()

    normalized_columns = []
    for col in df.columns:
        new_col = str(col).strip()

        # Remove accents
        if remove_accents:
            new_col = unicodedata.normalize("NFKD", new_col)
            new_col = "".join(c for c in new_col if not unicodedata.combining(c))

        # Convert to lowercase
        if lowercase:
            new_col = new_col.lower()

        # Replace spaces
        if replace_spaces is not None:
            new_col = new_col.replace(" ", replace_spaces)

        # Remove special characters
        if remove_special:
            new_col = re.sub(r"[^a-zA-Z0-9_]", "", new_col)

        # Remove leading/trailing underscores and collapse multiple underscores
        new_col = re.sub(r"_+", "_", new_col).strip("_")

        # Handle empty column names
        if not new_col:
            new_col = f"column_{df.columns.get_loc(col)}"

        normalized_columns.append(new_col)

    df.columns = normalized_columns
    return df


def read_csv_robust(
    file_path: Path,
    normalize_columns: bool = True,
    encodings: list[str] | None = None,
    delimiter: str | None = None,
    **kwargs,
) -> pd.DataFrame:
    """
    Robust CSV reader combining encoding detection, delimiter detection, and normalization.

    This is a convenience function that combines parse_csv_with_encoding()
    and normalize_column_names().

    Args:
        file_path: Path to CSV file
        normalize_columns: If True, normalize column names
        encodings: List of encodings to try
        delimiter: CSV delimiter (auto-detected if None)
        **kwargs: Additional arguments for pandas.read_csv()

    Returns:
        DataFrame with parsed and optionally normalized data

    Examples:
        >>> from pathlib import Path
        >>> # Read with all automatic features
        >>> df = read_csv_robust(Path("messy_data.csv"))
        >>> # Read without column normalization
        >>> df = read_csv_robust(Path("data.csv"), normalize_columns=False)
        >>> # Custom pandas options
        >>> df = read_csv_robust(
        ...     Path("data.csv"),
        ...     skiprows=2,
        ...     na_values=['', 'NA', 'N/A']
        ... )
    """
    df = parse_csv_with_encoding(
        file_path, encodings=encodings, delimiter=delimiter, **kwargs
    )

    if normalize_columns:
        df = normalize_column_names(df)

    return df


def write_csv_robust(
    df: pd.DataFrame,
    file_path: Path,
    encoding: str = "utf-8",
    delimiter: str = ";",
    **kwargs,
) -> None:
    """
    Write DataFrame to CSV with sensible defaults for European data.

    Args:
        df: DataFrame to write
        file_path: Output file path
        encoding: Output encoding (default: utf-8)
        delimiter: CSV delimiter (default: semicolon for European Excel)
        **kwargs: Additional arguments for pandas.to_csv()

    Examples:
        >>> import pandas as pd
        >>> from pathlib import Path
        >>> df = pd.DataFrame({"nom": ["Alice", "Bob"], "age": [30, 25]})
        >>> write_csv_robust(df, Path("output.csv"))
        >>> # Use comma delimiter
        >>> write_csv_robust(df, Path("output.csv"), delimiter=",")
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Set defaults for European CSV format
    defaults = {
        "index": False,
        "encoding": encoding,
        "sep": delimiter,
    }
    defaults.update(kwargs)

    df.to_csv(file_path, **defaults)
