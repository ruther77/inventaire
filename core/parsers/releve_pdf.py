from __future__ import annotations

from typing import List, Dict, Any
from pathlib import Path

try:
    import pdfplumber  # type: ignore
except ImportError:  # pragma: no cover
    pdfplumber = None


def parse_bank_pdf(path: str | Path) -> List[Dict[str, Any]]:
    """Parse un relevé PDF en lignes structurées (best effort).

    Retourne une liste de dicts :
      - date_operation (date ou str YYYY-MM-DD)
      - label (label brut)
      - amount (float)
      - balance (float|None)
      - ref_banque (str|None)
    """
    if pdfplumber is None:
        raise ImportError("pdfplumber non installé. pip install pdfplumber")

    rows: List[Dict[str, Any]] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                parts = line.strip().split()
                if len(parts) < 3:
                    continue
                # Heuristique : première colonne = date, dernière = montant
                date_token = parts[0]
                amount_token = parts[-1].replace("€", "").replace(",", ".")
                label = " ".join(parts[1:-1]).strip()
                try:
                    amount = float(amount_token)
                except ValueError:
                    continue
                rows.append(
                    {
                        "date_operation": date_token,
                        "label": label or None,
                        "amount": amount,
                        "balance": None,
                        "ref_banque": None,
                    }
                )
    return rows
