from __future__ import annotations  # Active les annotations différées

from io import BytesIO  # Flux mémoire pour manipuler les PDF en bytes
from typing import List  # Typage optionnel (non utilisé mais importé)
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

try:  # Tente d'utiliser pypdf (plus léger) en priorité
    from pypdf import PdfReader, PdfWriter  # type: ignore[import]
except ImportError:  # pragma: no cover - fallback PyPDF2
    from PyPDF2 import PdfReader, PdfWriter  # type: ignore[import]  # Fallback si pypdf indisponible

from .invoice_extractor import DATE_FACTURE_PATTERN, FINAL_INVOICE_PATTERN  # Regex pour détecter dates/fin de facture


def split_pdf_into_invoices(pdf_bytes: bytes) -> list[dict[str, object]]:
    """Découpe un PDF en sous-documents par facture (détectée via Date facture)."""  # Docstring de la fonction

    if not pdf_bytes:  # Si aucun contenu fourni
        return []  # Retourne une liste vide

    stream = BytesIO(pdf_bytes)  # Crée un flux mémoire à partir des bytes
    reader = PdfReader(stream)  # Lit le PDF
    documents: list[dict[str, object]] = []  # Liste des factures extraites

    invoice_counter = 0  # Compteur pour nommer les factures
    current_pages: list[int] = []  # Pages en cours d'agrégation
    current_invoice_id: str | None = None  # Identifiant de la facture en cours
    current_facture_date: str | None = None  # Date détectée de la facture

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

    for page_index, page in enumerate(reader.pages):  # Parcourt toutes les pages
        page_text = page.extract_text() or ""  # Extrait le texte de la page
        date_match = DATE_FACTURE_PATTERN.search(page_text)  # Cherche une date de facture
        if date_match:  # Si une date est détectée
            # nouvelle facture détectée -> finalise la précédente
            _finalize_current()  # Finalise l'éventuelle facture courante
            invoice_counter += 1  # Incrémente le compteur
            current_invoice_id = f"INV-{invoice_counter:03d}"  # Crée un ID formaté
            current_facture_date = date_match.group("facture_date").strip()  # Stocke la date détectée
            current_pages = [page_index]  # Démarre la nouvelle facture avec cette page
        else:  # Aucune date détectée sur la page
            if not current_pages:  # Si aucune facture en cours
                invoice_counter += 1  # Incrémente le compteur
                current_invoice_id = f"INV-{invoice_counter:03d}"  # Crée un nouvel ID
                current_pages = [page_index]  # Commence une nouvelle facture
            else:  # Une facture est déjà en cours
                current_pages.append(page_index)  # Ajoute la page à la facture courante

        if FINAL_INVOICE_PATTERN.search(page_text):  # Si motif de fin de facture détecté
            _finalize_current()  # Finalise immédiatement la facture en cours

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
