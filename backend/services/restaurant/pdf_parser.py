"""PDF parsing for bank statements (LCL, SumUp formats)."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, List

from pypdf import PdfReader

from backend.services.restaurant.constants import (
    TRANSACTION_LINE_RE,
    AMOUNT_RE,
    SUMUP_DATE_RE,
    SUMUP_TIME_RE,
    SUMUP_STATUS_PREFIXES,
)
from backend.services.restaurant.utils import (
    _safe_float,
    _normalize_amount,
    _extract_descriptions,
    _align_descriptions,
    _guess_category,
    _looks_like_credit,
    _should_skip_line,
)


def parse_bank_statement_pdf(pdf_bytes: bytes) -> List[dict[str, Any]]:
    """Detecte le format (LCL vs SumUp) puis extrait les lignes bancaires du PDF."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    first_page_text = ""
    if reader.pages:
        first_page_text = reader.pages[0].extract_text() or ""
    upper_text = first_page_text.upper()
    if "RELEVE DE COMPTE SUMUP" in upper_text or "RELEVE DE COMPTE SUMUP" in upper_text:
        return _parse_sumup_bank_statement(reader)
    return _parse_lcl_bank_statement(reader)


def _parse_lcl_bank_statement(reader: PdfReader) -> List[dict[str, Any]]:
    """Extraction specifique aux releves LCL (PDF texte) en s'appuyant sur les lignes datees."""
    entries: list[dict[str, Any]] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        page_lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
        if not page_lines:
            continue
        first_tx_idx = next(
            (idx for idx, value in enumerate(page_lines) if TRANSACTION_LINE_RE.match(value)),
            len(page_lines),
        )
        header_lines = page_lines[:first_tx_idx]
        data_lines = page_lines[first_tx_idx:]
        descriptions = _extract_descriptions(header_lines)
        tx_lines = [ln for ln in data_lines if TRANSACTION_LINE_RE.match(ln) and not _should_skip_line(ln)]
        descriptions = _align_descriptions(descriptions, len(tx_lines))

        for idx, line in enumerate(tx_lines):
            match = TRANSACTION_LINE_RE.match(line)
            if not match:
                continue
            description = descriptions[idx] if idx < len(descriptions) else ""
            if not description:
                description = "Mouvement"

            val_date = datetime.strptime(match.group("val"), "%d.%m.%y").date()
            op_month = val_date.strftime("%Y-%m")

            body = match.group("body")
            amounts = AMOUNT_RE.findall(body)
            debit = credit = 0.0
            if len(amounts) >= 2:
                debit = _normalize_amount(amounts[0])
                credit = _normalize_amount(amounts[1])
            elif len(amounts) == 1:
                amt = _normalize_amount(amounts[0])
                if _looks_like_credit(description):
                    credit = amt
                else:
                    debit = amt
            else:
                continue

            if credit:
                amount = credit
                entry_type = "Entree"
            else:
                amount = debit
                entry_type = "Sortie"

            entries.append(
                {
                    "date": val_date,
                    "libelle": description,
                    "categorie": _guess_category(description, entry_type),
                    "montant": amount,
                    "type": entry_type,
                    "mois": op_month,
                    "source": "pdf",
                }
            )

    return entries


def _parse_sumup_bank_statement(reader: PdfReader) -> List[dict[str, Any]]:
    """Parser dedie aux releves SumUp : decoupe en blocs par date puis delegue a `_parse_sumup_block`."""
    lines: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if stripped:
                lines.append(stripped)

    blocks: list[list[str]] = []
    current_block: list[str] = []
    for line in lines:
        if SUMUP_DATE_RE.match(line):
            if current_block:
                blocks.append(current_block)
            current_block = [line]
        else:
            if current_block:
                current_block.append(line)
    if current_block:
        blocks.append(current_block)

    entries: list[dict[str, Any]] = []
    for block in blocks:
        entry = _parse_sumup_block(block)
        if entry:
            entries.append(entry)
    return entries


def _parse_sumup_block(block: list[str]) -> dict[str, Any] | None:
    """Transforme un bloc de lignes SumUp en entree normalisee (date, description, montant, type)."""
    if not block:
        return None
    try:
        val_date = datetime.strptime(block[0], "%d/%m/%Y").date()
    except ValueError:
        return None
    idx = 1
    if idx < len(block) and SUMUP_TIME_RE.match(block[idx]):
        idx += 1

    description_lines: list[str] = []
    status_line = None
    while idx < len(block):
        line = block[idx]
        upper = line.upper()
        if any(upper.startswith(prefix) for prefix in SUMUP_STATUS_PREFIXES):
            status_line = line
            break
        description_lines.append(line)
        idx += 1

    if not status_line:
        return None

    parts = status_line.replace(",", ".").split()
    if len(parts) < 5:
        return None
    try:
        debit = _safe_float(parts[1])
        credit = _safe_float(parts[2])
    except ValueError:
        return None

    entry_type = "Entree" if credit > 0 else "Sortie"
    amount = credit if entry_type == "Entree" else debit
    if amount <= 0:
        return None

    description = " ".join(description_lines).strip()
    if not description:
        description = parts[0]

    op_month = val_date.strftime("%Y-%m")
    return {
        "date": val_date,
        "libelle": description,
        "categorie": _guess_category(description, entry_type),
        "montant": amount,
        "type": entry_type,
        "mois": op_month,
        "source": "sumup_pdf",
    }
