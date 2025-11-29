from __future__ import annotations  # Active les annotations différées

from io import BytesIO  # Flux mémoire pour manipuler les PDF en bytes
from typing import List  # Typage optionnel (non utilisé mais importé)

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
