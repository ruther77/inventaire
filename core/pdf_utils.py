from __future__ import annotations  # Active les annotations différées

from io import BytesIO  # Flux mémoire pour manipuler les PDF en bytes
from typing import List  # Typage optionnel (non utilisé mais importé)
import unicodedata
import re
from decimal import Decimal, ROUND_HALF_UP

try:  # Tente d'utiliser pypdf (plus léger) en priorité
    from pypdf import PdfReader, PdfWriter  # type: ignore[import]
except ImportError:  # pragma: no cover - fallback PyPDF2
    from PyPDF2 import PdfReader, PdfWriter  # type: ignore[import]  # Fallback si pypdf indisponible

from .invoice_extractor import DATE_FACTURE_PATTERN, FINAL_INVOICE_PATTERN  # Regex pour détecter dates/fin de facture

# Patterns de détection de factures par fournisseur
# METRO: "date facture : DD-MM-YYYY"
# TAIYAT: "FACTURE N° XXXXXX" avec "Date :DD/MM/YYYY"
# EUROCIEL: "FA2029XXXX" avec "Date DD/MM/YY"

TAIYAT_INVOICE_PATTERN = re.compile(
    r"FACTURE\s+N[°o]\s*(?P<invoice_id>\d{5,8})",
    re.IGNORECASE,
)
TAIYAT_DATE_PATTERN = re.compile(
    r"Date\s*:\s*(?P<facture_date>\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)

EUROCIEL_INVOICE_PATTERN = re.compile(
    r"(?P<invoice_id>FA\d{8})",
    re.IGNORECASE,
)
EUROCIEL_DATE_PATTERN = re.compile(
    r"Date\s*(?P<facture_date>\d{2}/\d{2}/\d{2,4})",
    re.IGNORECASE,
)

# Pattern générique pour "NET A PAYER" qui marque souvent la fin d'une facture
GENERIC_END_PATTERN = re.compile(r"NET\s+[AÀ]\s*PAYER", re.IGNORECASE)


def split_pdf_into_invoices(pdf_bytes: bytes, supplier_hint: str | None = None) -> list[dict[str, object]]:
    """Découpe un PDF en sous-documents par facture.

    Supporte différents fournisseurs via supplier_hint:
    - metro: détecte "date facture : DD-MM-YYYY"
    - taiyat: détecte "FACTURE N° XXXXXX" avec "Date :DD/MM/YYYY"
    - eurociel: détecte "FA2029XXXX" avec "Date DD/MM/YY"
    """

    if not pdf_bytes:  # Si aucun contenu fourni
        return []  # Retourne une liste vide

    stream = BytesIO(pdf_bytes)  # Crée un flux mémoire à partir des bytes
    reader = PdfReader(stream)  # Lit le PDF
    documents: list[dict[str, object]] = []  # Liste des factures extraites

    invoice_counter = 0  # Compteur pour nommer les factures (pour METRO)
    current_pages: list[int] = []  # Pages en cours d'agrégation
    current_invoice_id: str | None = None  # Identifiant de la facture en cours
    current_facture_date: str | None = None  # Date détectée de la facture

    # Normalise le supplier_hint
    supplier = (supplier_hint or "").strip().lower()

    def _finalize_current() -> None:
        nonlocal current_pages, current_invoice_id, current_facture_date  # Utilise les variables extérieures
        if not current_pages or current_invoice_id is None:  # Si aucune page ou pas d'ID
            current_pages = []  # Réinitialise les pages
            current_invoice_id = None  # Réinitialise l'ID
            current_facture_date = None  # Réinitialise la date
            return  # Sort sans créer de document
        writer = PdfWriter()  # Prépare un nouvel écrivain PDF
        for page_idx in current_pages:  # Ajoute chaque page courante
            writer.add_page(reader.pages[page_idx])  # Copie la page
        buffer = BytesIO()  # Buffer pour la sortie PDF
        writer.write(buffer)  # Écrit le PDF dans le buffer
        buffer.seek(0)  # Repositionne au début
        documents.append(
            {
                "invoice_id": current_invoice_id,
                "facture_date": current_facture_date,
                "pdf_bytes": buffer.getvalue(),
            }
        )  # Ajoute le sous-document
        current_pages = []  # Réinitialise les pages
        current_invoice_id = None  # Réinitialise l'ID
        current_facture_date = None  # Réinitialise la date

    def _detect_new_invoice(page_text: str) -> tuple[str | None, str | None]:
        """Détecte une nouvelle facture selon le fournisseur. Retourne (invoice_id, date)."""
        nonlocal invoice_counter

        if supplier == "taiyat":
            # TAIYAT: cherche "FACTURE N° XXXXXX"
            inv_match = TAIYAT_INVOICE_PATTERN.search(page_text)
            if inv_match:
                inv_id = f"TAIYAT-{inv_match.group('invoice_id')}"
                date_match = TAIYAT_DATE_PATTERN.search(page_text)
                inv_date = date_match.group("facture_date") if date_match else None
                return inv_id, inv_date
            return None, None

        elif supplier == "eurociel":
            # EUROCIEL: cherche "FA2029XXXX"
            inv_match = EUROCIEL_INVOICE_PATTERN.search(page_text)
            if inv_match:
                inv_id = inv_match.group("invoice_id").upper()
                date_match = EUROCIEL_DATE_PATTERN.search(page_text)
                inv_date = date_match.group("facture_date") if date_match else None
                return inv_id, inv_date
            return None, None

        else:
            # METRO ou générique: cherche "date facture : DD-MM-YYYY"
            date_match = DATE_FACTURE_PATTERN.search(page_text)
            if date_match:
                invoice_counter += 1
                inv_id = f"INV-{invoice_counter:03d}"
                inv_date = date_match.group("facture_date").strip()
                return inv_id, inv_date
            return None, None

    def _is_end_of_invoice(page_text: str) -> bool:
        """Détecte si la page marque la fin d'une facture."""
        # METRO: "FIN DE LA FACTURE"
        if FINAL_INVOICE_PATTERN.search(page_text):
            return True
        # Tous: "NET A PAYER" marque souvent la fin
        if supplier in ("taiyat", "eurociel") and GENERIC_END_PATTERN.search(page_text):
            return True
        return False

    for page_index, page in enumerate(reader.pages):  # Parcourt toutes les pages
        page_text = page.extract_text() or ""  # Extrait le texte de la page

        # Cherche une nouvelle facture sur cette page
        new_invoice_id, new_invoice_date = _detect_new_invoice(page_text)

        if new_invoice_id:  # Nouvelle facture détectée
            # Finalise la facture précédente
            _finalize_current()
            # Démarre la nouvelle facture
            current_invoice_id = new_invoice_id
            current_facture_date = new_invoice_date
            current_pages = [page_index]
        else:  # Aucune nouvelle facture détectée
            if not current_pages:  # Si aucune facture en cours
                # Pour les cas où le PDF ne commence pas par un header de facture
                invoice_counter += 1
                current_invoice_id = f"INV-{invoice_counter:03d}"
                current_pages = [page_index]
            else:  # Ajoute la page à la facture courante
                current_pages.append(page_index)

        # Vérifie si c'est la fin de la facture
        if _is_end_of_invoice(page_text):
            _finalize_current()

    _finalize_current()  # Finalise la dernière facture après la boucle
    return documents  # Retourne la liste des factures extraites


__all__ = ["split_pdf_into_invoices"]  # Exporte la fonction publique


def sanitize_receipt_text(value: object) -> str:
    """Convertit un contenu en chaîne ASCII sans caractères spéciaux."""

    if value is None:
        return ""

    text = str(value)
    if not text:
        return ""

    text = text.replace("€", " EUR ")
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = " ".join(ascii_text.split())
    return cleaned.strip()


def format_currency_line(label: str, amount: Decimal) -> str:
    safe_amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return sanitize_receipt_text(f"{label}: {safe_amount:.2f} EUR")


def format_quantity(qty: Decimal) -> str:
    normalized = qty.normalize() if isinstance(qty, Decimal) else Decimal(str(qty or "0")).normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def render_receipt_pdf(lines: list[str]) -> bytes:
    """Encode les lignes du ticket dans un PDF minimaliste."""

    def _escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    text_commands = [
        "q",
        "1 w",
        "0 0 0 RG",
        "45 420 m",
        "105 420 l",
        "105 370 l",
        "45 370 l",
        "h",
        "S",
        "45 420 m",
        "75 450 l",
        "135 450 l",
        "105 420 l",
        "S",
        "105 420 m",
        "135 450 l",
        "135 400 l",
        "105 370 l",
        "S",
        "Q",
        "BT",
        "/F1 10 Tf",
        "40 340 Td",
    ]
    for line in lines:
        text_commands.append(f"({_escape(line)}) Tj")
        text_commands.append("0 -12 Td")
    text_commands.append("ET")
    content_stream = "\n".join(text_commands)
    content_bytes = content_stream.encode("utf-8")

    objects: list[str] = []
    objects.append("<< /Type /Catalog /Pages 2 0 R >>")
    objects.append("<< /Type /Pages /Count 1 /Kids [3 0 R] >>")
    objects.append(
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 500] "
        "/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
    )
    objects.append(f"<< /Length {len(content_bytes)} >>\nstream\n{content_stream}\nendstream")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    pdf_parts: list[str] = []
    offsets: list[int] = []
    current_length = 0

    def _append(part: str) -> None:
        nonlocal current_length
        pdf_parts.append(part)
        current_length += len(part)

    def _add_object(obj_number: int, body: str) -> None:
        offsets.append(current_length)
        obj_repr = f"{obj_number} 0 obj\n{body}\nendobj\n"
        _append(obj_repr)

    _append("%PDF-1.4\n")
    for index, body in enumerate(objects, start=1):
        _add_object(index, body)

    xref_offset = current_length
    total_objects = len(objects) + 1
    _append(f"xref\n0 {total_objects}\n")
    _append("0000000000 65535 f \n")
    for offset in offsets:
        _append(f"{offset:010d} 00000 n \n")

    _append("trailer\n")
    _append(f"<< /Size {total_objects} /Root 1 0 R >>\n")
    _append("startxref\n")
    _append(f"{xref_offset}\n")
    _append("%%EOF")

    return "".join(pdf_parts).encode("utf-8")


__all__ = [
    "split_pdf_into_invoices",
    "sanitize_receipt_text",
    "format_currency_line",
    "format_quantity",
    "render_receipt_pdf",
]
