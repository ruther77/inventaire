"""PDF text extraction and preprocessing."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

from .models import BankType, StatementPeriod


@dataclass
class ExtractedPage:
    """A single page extracted from PDF."""
    page_number: int
    text: str
    lines: List[str]


@dataclass
class ExtractionResult:
    """Result of PDF extraction."""
    full_text: str
    pages: List[ExtractedPage]
    periods: List[StatementPeriod]
    line_count: int
    # Map period key (start_date, end_date) to list of (start_line, end_line) ranges
    period_line_ranges: Optional[dict] = None


class PDFExtractor:
    """Extracts and preprocesses text from bank statement PDFs."""

    # Month names for French date parsing
    FRENCH_MONTHS = {
        "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12
    }

    # Period detection patterns
    PERIOD_PATTERNS = [
        # LCL format: "du 30.12.2023 au 31.01.2024"
        re.compile(
            r"du\s+(\d{2})[./](\d{2})[./](\d{2,4})\s+au\s+(\d{2})[./](\d{2})[./](\d{2,4})",
            re.IGNORECASE
        ),
        # BNP format: "Période du 01/01/2024 au 31/01/2024"
        re.compile(
            r"[Pp][ée]riode\s+du\s+(\d{2})/(\d{2})/(\d{4})\s+au\s+(\d{2})/(\d{2})/(\d{4})"
        ),
        # Alternative: "RELEVE DU 01.01.2024 AU 31.01.2024"
        re.compile(
            r"RELEVE\s+DU\s+(\d{2})[./](\d{2})[./](\d{4})\s+AU\s+(\d{2})[./](\d{2})[./](\d{4})",
            re.IGNORECASE
        ),
        # SumUp format: "période du rapport: 08/05/2022 - 12/11/2025"
        re.compile(
            r"p[ée]riode\s+du\s+rapport\s*:\s*(\d{2})/(\d{2})/(\d{4})\s*-\s*(\d{2})/(\d{2})/(\d{4})",
            re.IGNORECASE
        ),
    ]

    # BNP French text date pattern: "du 27 décembre 2022 au 27 janvier 2023"
    BNP_FRENCH_DATE_PATTERN = re.compile(
        r"du\s+(\d{1,2})\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(\d{4})\s+au\s+(\d{1,2})\s+(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s+(\d{4})",
        re.IGNORECASE
    )

    # Lines to skip (headers, footers, etc.)
    SKIP_PATTERNS = [
        re.compile(r"^PAGE\s+\d+", re.IGNORECASE),
        re.compile(r"^ECRITURES\s+DE\s+LA\s+PERIODE", re.IGNORECASE),
        re.compile(r"^DATE\s+LIBELLE\s+VALEUR", re.IGNORECASE),
        re.compile(r"^Titulaire\s+du\s+compte", re.IGNORECASE),
        re.compile(r"^Votreconseiller", re.IGNORECASE),
        re.compile(r"^Credit\s+Lyonnais", re.IGNORECASE),
        re.compile(r"^RELEVE\s+D'IDENTITE", re.IGNORECASE),
        re.compile(r"^www\.lcl\.fr", re.IGNORECASE),
        re.compile(r"^DOMICILIATION", re.IGNORECASE),
        re.compile(r"^REFERENCES", re.IGNORECASE),
        re.compile(r"^IBAN\s*:", re.IGNORECASE),
        re.compile(r"^BIC\s*:", re.IGNORECASE),
    ]

    def __init__(self, pdftotext_path: str = "pdftotext"):
        self.pdftotext_path = pdftotext_path

    def extract_text(self, pdf_path: Path) -> str:
        """Extract raw text from PDF using pdftotext.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Raw text content

        Raises:
            FileNotFoundError: If pdftotext is not installed
            RuntimeError: If extraction fails
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            result = subprocess.run(
                [self.pdftotext_path, "-layout", str(pdf_path), "-"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except FileNotFoundError:
            raise FileNotFoundError(
                f"pdftotext not found. Install poppler-utils: "
                f"apt-get install poppler-utils"
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"PDF extraction failed: {e.stderr}")

    def extract(self, pdf_path: Path) -> ExtractionResult:
        """Extract and preprocess PDF content.

        Args:
            pdf_path: Path to PDF file

        Returns:
            ExtractionResult with text, pages, and detected periods
        """
        raw_text = self.extract_text(pdf_path)
        lines = raw_text.splitlines()

        # Normalize lines
        normalized_lines = []
        for line in lines:
            # Replace non-breaking spaces
            line = line.replace("\u00a0", " ")
            normalized_lines.append(line)

        # Detect periods (now returns tuple with line ranges)
        periods, period_line_ranges = self._detect_periods(raw_text, normalized_lines)

        # Split into pages (form feed character)
        pages = self._split_pages(normalized_lines)

        return ExtractionResult(
            full_text=raw_text,
            pages=pages,
            periods=periods,
            line_count=len(normalized_lines),
            period_line_ranges=period_line_ranges
        )

    def _detect_periods(
        self, full_text: str, lines: List[str]
    ) -> Tuple[List[StatementPeriod], dict]:
        """Detect statement periods from text.

        For multi-period PDFs (consolidated statements), each period may appear
        multiple times (once per page). We collect ALL line ranges for each period
        to ensure complete transaction extraction.

        Args:
            full_text: Complete PDF text
            lines: List of text lines

        Returns:
            Tuple of (List of unique StatementPeriod objects, dict of period_key -> line_ranges)
        """
        # First pass: collect ALL occurrences of each period
        period_occurrences: dict = {}  # period_key -> list of line numbers where period header appears

        for line_num, line in enumerate(lines):
            period = None

            # Try numeric patterns first
            for pattern in self.PERIOD_PATTERNS:
                match = pattern.search(line)
                if match:
                    period = self._parse_period_match(match)
                    if period:
                        break

            # Try BNP French text date pattern
            if not period:
                match = self.BNP_FRENCH_DATE_PATTERN.search(line)
                if match:
                    period = self._parse_french_period_match(match)

            if period:
                period_key = (period.start_date, period.end_date)
                if period_key not in period_occurrences:
                    period_occurrences[period_key] = []
                period_occurrences[period_key].append(line_num)

        # Second pass: for each unique period, calculate line ranges
        # Each occurrence defines a "block" that ends when the next period header appears
        # (regardless of which period it is)

        # Get all header line numbers sorted
        all_header_lines = []
        for period_key, line_nums in period_occurrences.items():
            for ln in line_nums:
                all_header_lines.append((ln, period_key))
        all_header_lines.sort(key=lambda x: x[0])

        # Build line ranges for each period
        period_line_ranges: dict = {}  # period_key -> list of (start_line, end_line)

        for i, (header_line, period_key) in enumerate(all_header_lines):
            # Find where this block ends (next header or end of file)
            if i + 1 < len(all_header_lines):
                block_end = all_header_lines[i + 1][0] - 1
            else:
                block_end = len(lines) - 1

            # Add this range to the period
            if period_key not in period_line_ranges:
                period_line_ranges[period_key] = []
            period_line_ranges[period_key].append((header_line, block_end))

        # Build unique period objects
        periods: List[StatementPeriod] = []
        for period_key in period_occurrences.keys():
            start_date, end_date = period_key
            ranges = period_line_ranges.get(period_key, [])

            # page_start = first occurrence, page_end = last line of last occurrence
            first_line = min(r[0] for r in ranges) if ranges else 0
            last_line = max(r[1] for r in ranges) if ranges else len(lines) - 1

            period = StatementPeriod(
                start_date=start_date,
                end_date=end_date,
                page_start=first_line,
                page_end=last_line
            )
            periods.append(period)

        # Sort by start date
        periods.sort(key=lambda p: p.start_date)

        return periods, period_line_ranges

    def _parse_french_period_match(self, match: re.Match) -> Optional[StatementPeriod]:
        """Parse French text date match (BNP format).

        Args:
            match: Regex match with groups (day1, month1, year1, day2, month2, year2)

        Returns:
            StatementPeriod or None
        """
        try:
            d1, m1_name, y1, d2, m2_name, y2 = match.groups()
            m1 = self.FRENCH_MONTHS.get(m1_name.lower())
            m2 = self.FRENCH_MONTHS.get(m2_name.lower())

            if m1 is None or m2 is None:
                return None

            return StatementPeriod(
                start_date=date(int(y1), m1, int(d1)),
                end_date=date(int(y2), m2, int(d2))
            )
        except (ValueError, IndexError):
            return None

    def _parse_period_match(self, match: re.Match) -> Optional[StatementPeriod]:
        """Parse regex match into StatementPeriod.

        Args:
            match: Regex match object with 6 groups (d1,m1,y1,d2,m2,y2)

        Returns:
            StatementPeriod or None if parsing fails
        """
        try:
            groups = match.groups()
            d1, m1, y1, d2, m2, y2 = groups

            def _make_date(d: str, m: str, y: str) -> date:
                year = int(y)
                if year < 100:
                    year += 2000
                return date(year, int(m), int(d))

            return StatementPeriod(
                start_date=_make_date(d1, m1, y1),
                end_date=_make_date(d2, m2, y2)
            )
        except (ValueError, IndexError):
            return None

    def _split_pages(self, lines: List[str]) -> List[ExtractedPage]:
        """Split text into pages based on form feed characters.

        Args:
            lines: List of text lines

        Returns:
            List of ExtractedPage objects
        """
        pages: List[ExtractedPage] = []
        current_page_lines: List[str] = []
        page_num = 1

        for line in lines:
            if "\f" in line:
                # Form feed - new page
                if current_page_lines:
                    pages.append(ExtractedPage(
                        page_number=page_num,
                        text="\n".join(current_page_lines),
                        lines=current_page_lines
                    ))
                    page_num += 1
                current_page_lines = []
                # Handle text after form feed on same line
                remaining = line.split("\f")[-1].strip()
                if remaining:
                    current_page_lines.append(remaining)
            else:
                current_page_lines.append(line)

        # Last page
        if current_page_lines:
            pages.append(ExtractedPage(
                page_number=page_num,
                text="\n".join(current_page_lines),
                lines=current_page_lines
            ))

        return pages

    def clean_lines(
        self,
        lines: List[str],
        bank_type: BankType = BankType.UNKNOWN
    ) -> List[str]:
        """Remove header/footer lines and noise.

        Args:
            lines: Raw text lines
            bank_type: Detected bank type for specific cleaning

        Returns:
            Cleaned lines
        """
        cleaned: List[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Skip matching patterns
            skip = False
            for pattern in self.SKIP_PATTERNS:
                if pattern.match(stripped):
                    skip = True
                    break

            if not skip:
                cleaned.append(line)

        return cleaned

    def get_lines_for_period(
        self,
        lines: List[str],
        period: StatementPeriod,
        period_line_ranges: Optional[dict] = None
    ) -> List[str]:
        """Get lines belonging to a specific period.

        For multi-period PDFs, the same period may appear on multiple pages.
        If period_line_ranges is provided, it collects lines from ALL occurrences
        of this period.

        Args:
            lines: All text lines
            period: Target period
            period_line_ranges: Optional dict mapping period_key to list of (start, end) ranges

        Returns:
            Lines within the period's range(s)
        """
        period_key = (period.start_date, period.end_date)

        # If we have detailed line ranges, use them to collect ALL lines for this period
        if period_line_ranges and period_key in period_line_ranges:
            collected_lines: List[str] = []
            for start_line, end_line in period_line_ranges[period_key]:
                start = max(0, start_line)
                end = min(len(lines), end_line + 1)
                collected_lines.extend(lines[start:end])
            return collected_lines

        # Fallback to original behavior using page_start/page_end
        if period.page_end == 0:
            period.page_end = len(lines) - 1

        start = max(0, period.page_start)
        end = min(len(lines), period.page_end + 1)

        return lines[start:end]


def extract_pdf_text(pdf_path: Path) -> str:
    """Convenience function to extract PDF text.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text
    """
    extractor = PDFExtractor()
    return extractor.extract_text(pdf_path)
