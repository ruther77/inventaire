#!/usr/bin/env python3
"""Script pour importer toutes les factures Eurociel dans la base de données."""

from __future__ import annotations

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger(__name__)

from backend.services import invoices as invoices_service
from core.invoice_extractor import extract_text_from_file

EUROCIEL_DIR = ROOT_DIR / "EUROCIEL"
TENANT_ID = 1
MARGIN_PERCENT = 40.0
INITIALIZE_STOCK = True


def import_pdf(pdf_path: Path) -> dict:
    """Importe un fichier PDF Eurociel."""
    LOGGER.info(f"Traitement de: {pdf_path.name}")

    try:
        # Lire le fichier
        content = pdf_path.read_bytes()

        # Extraire le texte
        import io
        buffer = io.BytesIO(content)
        buffer.name = pdf_path.name
        text = extract_text_from_file(buffer)

        if not text.strip():
            LOGGER.warning(f"  Aucun texte extrait de {pdf_path.name}")
            return {"file": pdf_path.name, "status": "empty", "products": 0}

        LOGGER.info(f"  Texte extrait: {len(text)} caractères")

        # Stocker le PDF
        stored_docs = invoices_service.persist_invoice_documents(
            content,
            tenant_id=TENANT_ID,
            supplier="Eurociel",
        )
        LOGGER.info(f"  Documents stockés: {len(stored_docs)}")

        # Extraire les lignes produits
        lines_df = invoices_service.extract_invoice_lines(
            text,
            margin_percent=MARGIN_PERCENT,
            supplier_hint="Eurociel",
        )

        if lines_df.empty:
            LOGGER.warning(f"  Aucun produit détecté dans {pdf_path.name}")
            return {"file": pdf_path.name, "status": "no_products", "products": 0}

        LOGGER.info(f"  Lignes extraites: {len(lines_df)}")

        # Enrichir avec le catalogue existant
        enriched_df = invoices_service.enrich_lines_with_catalog(
            lines_df,
            margin_percent=MARGIN_PERCENT,
            tenant_id=TENANT_ID,
        )

        # Importer dans le catalogue
        summary = invoices_service.import_catalog_from_invoice(
            enriched_df,
            supplier="Eurociel",
            initialize_stock=INITIALIZE_STOCK,
            invoice_date=None,
            tenant_id=TENANT_ID,
        )

        LOGGER.info(f"  Import terminé: {summary.get('created', 0)} créés, {summary.get('updated', 0)} mis à jour")

        return {
            "file": pdf_path.name,
            "status": "success",
            "products": len(lines_df),
            "created": summary.get("created", 0),
            "updated": summary.get("updated", 0),
            "stock_initialized": summary.get("stock_initialized", 0),
            "errors": summary.get("errors", []),
        }

    except Exception as e:
        LOGGER.error(f"  Erreur: {e}")
        return {"file": pdf_path.name, "status": "error", "error": str(e)}


def main():
    """Point d'entrée principal."""
    if not EUROCIEL_DIR.exists():
        LOGGER.error(f"Répertoire non trouvé: {EUROCIEL_DIR}")
        sys.exit(1)

    # Lister les PDFs (exclure le catalogue qui est trop gros)
    pdf_files = [
        f for f in EUROCIEL_DIR.glob("*.pdf")
        if "catalogue" not in f.name.lower()
    ]

    if not pdf_files:
        LOGGER.error("Aucun fichier PDF trouvé")
        sys.exit(1)

    LOGGER.info(f"Trouvé {len(pdf_files)} fichiers PDF à traiter")

    results = []
    total_created = 0
    total_updated = 0

    for pdf_path in sorted(pdf_files):
        result = import_pdf(pdf_path)
        results.append(result)
        total_created += result.get("created", 0)
        total_updated += result.get("updated", 0)

    # Résumé
    LOGGER.info("=" * 60)
    LOGGER.info("RÉSUMÉ DE L'IMPORT")
    LOGGER.info("=" * 60)
    LOGGER.info(f"Fichiers traités: {len(results)}")
    LOGGER.info(f"Total produits créés: {total_created}")
    LOGGER.info(f"Total produits mis à jour: {total_updated}")

    for result in results:
        status = result.get("status", "unknown")
        if status == "success":
            LOGGER.info(f"  ✓ {result['file']}: {result.get('created', 0)} créés, {result.get('updated', 0)} MAJ")
        elif status == "error":
            LOGGER.error(f"  ✗ {result['file']}: {result.get('error', 'Unknown error')}")
        else:
            LOGGER.warning(f"  - {result['file']}: {status}")


if __name__ == "__main__":
    main()
