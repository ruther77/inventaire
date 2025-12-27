#!/usr/bin/env python3
"""Script pour importer toutes les factures des fournisseurs METRO, TAIYAT et EUROCIEL.

Ce script :
1. Parcourt les dossiers /METRO, /TAIYAT, /EUROCIEL
2. Utilise le nom du dossier comme supplier_hint pour le parseur approprié
3. Découpe les PDFs multi-factures automatiquement
4. Crée les produits, enregistre l'historique des prix et les mouvements de stock
5. Génère un rapport détaillé

Usage:
    python scripts/import_all_suppliers.py
    python scripts/import_all_suppliers.py --supplier METRO
    python scripts/import_all_suppliers.py --dry-run
"""

from __future__ import annotations

import argparse
import io
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(ROOT_DIR / "import_suppliers.log", mode="w", encoding="utf-8"),
    ],
)
LOGGER = logging.getLogger(__name__)

from backend.services import invoices as invoices_service
from core.invoice_extractor import extract_text_from_file
from core.pdf_utils import split_pdf_into_invoices

# Configuration des fournisseurs
SUPPLIERS_CONFIG = {
    "METRO": {
        "folder": ROOT_DIR / "METRO",
        "supplier_hint": "metro",
        "exclude_patterns": [],  # Pas d'exclusion pour METRO
    },
    "TAIYAT": {
        "folder": ROOT_DIR / "TAIYAT",
        "supplier_hint": "taiyat",
        "exclude_patterns": ["tarif", "liste articles"],  # Exclure les fichiers de tarifs
    },
    "EUROCIEL": {
        "folder": ROOT_DIR / "EUROCIEL",
        "supplier_hint": "eurociel",
        "exclude_patterns": ["catalogue"],  # Exclure le catalogue (trop gros)
    },
}

TENANT_ID = 1  # Epicerie
MARGIN_PERCENT = 40.0
INITIALIZE_STOCK = True


class ImportStats:
    """Statistiques d'import par fournisseur."""

    def __init__(self, supplier: str):
        self.supplier = supplier
        self.files_processed = 0
        self.files_success = 0
        self.files_error = 0
        self.files_empty = 0
        self.invoices_found = 0
        self.products_created = 0
        self.products_updated = 0
        self.stock_initialized = 0
        self.errors: list[dict] = []

    def add_file_result(self, result: dict):
        self.files_processed += 1
        status = result.get("status", "unknown")

        if status == "success":
            self.files_success += 1
            self.products_created += result.get("created", 0)
            self.products_updated += result.get("updated", 0)
            self.stock_initialized += result.get("stock_initialized", 0)
            self.invoices_found += result.get("invoices", 0)
        elif status == "error":
            self.files_error += 1
            self.errors.append({
                "file": result.get("file", "unknown"),
                "error": result.get("error", "Unknown error"),
            })
        elif status in ("empty", "no_products"):
            self.files_empty += 1

    def summary(self) -> str:
        lines = [
            f"=== {self.supplier} ===",
            f"  Fichiers traités: {self.files_processed}",
            f"  - Succès: {self.files_success}",
            f"  - Vides: {self.files_empty}",
            f"  - Erreurs: {self.files_error}",
            f"  Factures détectées: {self.invoices_found}",
            f"  Produits créés: {self.products_created}",
            f"  Produits mis à jour: {self.products_updated}",
            f"  Stock initialisé: {self.stock_initialized}",
        ]
        if self.errors:
            lines.append("  Erreurs détaillées:")
            for err in self.errors[:5]:  # Limite à 5 erreurs
                lines.append(f"    - {err['file']}: {err['error'][:100]}")
            if len(self.errors) > 5:
                lines.append(f"    ... et {len(self.errors) - 5} autres erreurs")
        return "\n".join(lines)


def should_exclude_file(filename: str, exclude_patterns: list[str]) -> bool:
    """Vérifie si un fichier doit être exclu selon les patterns."""
    lowered = filename.lower()
    return any(pattern.lower() in lowered for pattern in exclude_patterns)


def import_single_pdf(
    pdf_path: Path,
    supplier: str,
    supplier_hint: str,
    *,
    dry_run: bool = False,
) -> dict:
    """Importe un fichier PDF pour un fournisseur donné."""
    LOGGER.info(f"  [{supplier}] Traitement: {pdf_path.name}")

    try:
        # 1. Lire le fichier PDF
        content = pdf_path.read_bytes()
        if not content:
            return {"file": pdf_path.name, "status": "empty", "reason": "Fichier vide"}

        # 2. Découper en factures individuelles (pour les PDFs multi-factures)
        invoices = split_pdf_into_invoices(content)
        invoice_count = len(invoices) if invoices else 1

        LOGGER.info(f"    → {invoice_count} facture(s) détectée(s)")

        if dry_run:
            return {
                "file": pdf_path.name,
                "status": "dry_run",
                "invoices": invoice_count,
            }

        # 3. Extraire le texte
        buffer = io.BytesIO(content)
        buffer.name = pdf_path.name
        text = extract_text_from_file(buffer)

        if not text.strip():
            LOGGER.warning(f"    → Aucun texte extrait")
            return {"file": pdf_path.name, "status": "empty", "reason": "Aucun texte extrait"}

        LOGGER.info(f"    → {len(text)} caractères extraits")

        # 4. Stocker les documents PDF (découpe par facture)
        stored_docs = invoices_service.persist_invoice_documents(
            content,
            tenant_id=TENANT_ID,
            supplier=supplier,
        )
        LOGGER.info(f"    → {len(stored_docs)} document(s) stocké(s)")

        # 5. Extraire les lignes produits avec le parseur approprié
        lines_df = invoices_service.extract_invoice_lines(
            text,
            margin_percent=MARGIN_PERCENT,
            supplier_hint=supplier_hint,
            tenant_id=TENANT_ID,
        )

        if lines_df.empty:
            LOGGER.warning(f"    → Aucun produit détecté")
            return {
                "file": pdf_path.name,
                "status": "no_products",
                "invoices": invoice_count,
            }

        LOGGER.info(f"    → {len(lines_df)} ligne(s) produit extraite(s)")

        # 6. Enrichir avec le catalogue existant
        enriched_df = invoices_service.enrich_lines_with_catalog(
            lines_df,
            margin_percent=MARGIN_PERCENT,
            tenant_id=TENANT_ID,
        )

        # 7. Importer dans le catalogue
        summary = invoices_service.import_catalog_from_invoice(
            enriched_df,
            supplier=supplier,
            initialize_stock=INITIALIZE_STOCK,
            invoice_date=None,  # Date extraite du PDF
            tenant_id=TENANT_ID,
        )

        created = summary.get("created", 0)
        updated = summary.get("updated", 0)
        stock_init = summary.get("stock_initialized", 0)

        LOGGER.info(f"    → Import terminé: {created} créés, {updated} MAJ, {stock_init} stock")

        return {
            "file": pdf_path.name,
            "status": "success",
            "invoices": invoice_count,
            "products": len(lines_df),
            "created": created,
            "updated": updated,
            "stock_initialized": stock_init,
        }

    except Exception as e:
        LOGGER.error(f"    → Erreur: {e}")
        return {
            "file": pdf_path.name,
            "status": "error",
            "error": str(e),
        }


def import_supplier(
    supplier_name: str,
    config: dict,
    *,
    dry_run: bool = False,
) -> ImportStats:
    """Importe tous les PDFs d'un fournisseur."""
    folder = config["folder"]
    supplier_hint = config["supplier_hint"]
    exclude_patterns = config.get("exclude_patterns", [])

    stats = ImportStats(supplier_name)

    if not folder.exists():
        LOGGER.error(f"Dossier non trouvé: {folder}")
        return stats

    # Lister les PDFs (excluant les patterns configurés)
    pdf_files = [
        f for f in folder.glob("*.pdf")
        if not should_exclude_file(f.name, exclude_patterns)
    ]

    if not pdf_files:
        LOGGER.warning(f"Aucun PDF trouvé dans {folder}")
        return stats

    LOGGER.info(f"\n{'='*60}")
    LOGGER.info(f"FOURNISSEUR: {supplier_name}")
    LOGGER.info(f"Dossier: {folder}")
    LOGGER.info(f"Fichiers à traiter: {len(pdf_files)}")
    LOGGER.info(f"{'='*60}")

    for pdf_path in sorted(pdf_files):
        result = import_single_pdf(
            pdf_path,
            supplier_name,
            supplier_hint,
            dry_run=dry_run,
        )
        stats.add_file_result(result)

    return stats


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Import des factures fournisseurs METRO, TAIYAT, EUROCIEL"
    )
    parser.add_argument(
        "--supplier",
        choices=["METRO", "TAIYAT", "EUROCIEL"],
        help="Importer uniquement un fournisseur spécifique",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode simulation (pas d'import réel)",
    )
    args = parser.parse_args()

    start_time = datetime.now(timezone.utc)
    LOGGER.info(f"Démarrage de l'import: {start_time.isoformat()}")

    if args.dry_run:
        LOGGER.info(">>> MODE DRY-RUN: Aucune modification ne sera effectuée <<<")

    # Déterminer les fournisseurs à traiter
    if args.supplier:
        suppliers_to_process = {args.supplier: SUPPLIERS_CONFIG[args.supplier]}
    else:
        suppliers_to_process = SUPPLIERS_CONFIG

    all_stats: list[ImportStats] = []

    for supplier_name, config in suppliers_to_process.items():
        stats = import_supplier(supplier_name, config, dry_run=args.dry_run)
        all_stats.append(stats)

    # Afficher le rapport final
    end_time = datetime.now(timezone.utc)
    duration = (end_time - start_time).total_seconds()

    LOGGER.info("\n" + "=" * 60)
    LOGGER.info("RAPPORT FINAL D'IMPORT")
    LOGGER.info("=" * 60)
    LOGGER.info(f"Durée totale: {duration:.1f} secondes")
    LOGGER.info("")

    total_files = 0
    total_created = 0
    total_updated = 0
    total_invoices = 0

    for stats in all_stats:
        LOGGER.info(stats.summary())
        LOGGER.info("")
        total_files += stats.files_processed
        total_created += stats.products_created
        total_updated += stats.products_updated
        total_invoices += stats.invoices_found

    LOGGER.info("-" * 60)
    LOGGER.info("TOTAUX:")
    LOGGER.info(f"  Fichiers traités: {total_files}")
    LOGGER.info(f"  Factures détectées: {total_invoices}")
    LOGGER.info(f"  Produits créés: {total_created}")
    LOGGER.info(f"  Produits mis à jour: {total_updated}")
    LOGGER.info("=" * 60)


if __name__ == "__main__":
    main()
