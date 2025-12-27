#!/usr/bin/env python3
"""
Module d'import automatique des factures fournisseur Eurociel.

Ce script permet de:
- Scanner un répertoire contenant des factures PDF Eurociel
- Extraire automatiquement le texte de chaque facture
- Parser les lignes de produits avec prix et quantités
- Enrichir les données avec le catalogue existant
- Importer ou mettre à jour les produits dans la base de données
- Initialiser le stock pour les nouveaux produits
- Générer un rapport détaillé de l'import

Le script traite tous les PDFs du répertoire EUROCIEL/ (à l'exception du catalogue
principal qui est trop volumineux).

Usage:
    python scripts/import_eurociel.py

Configuration:
    Les paramètres suivants sont définis dans le script:
    - EUROCIEL_DIR: Répertoire contenant les factures PDF
    - TENANT_ID: Identifiant du tenant (par défaut: 1)
    - MARGIN_PERCENT: Marge appliquée pour calculer le prix de vente (40%)
    - INITIALIZE_STOCK: Active l'initialisation du stock (True)

Prérequis:
    - Les PDFs doivent être dans le répertoire EUROCIEL/ à la racine du projet
    - La base de données doit être accessible via DATABASE_URL
    - Les services backend.services.invoices doivent être configurés
    - pdftotext ou un outil équivalent pour l'extraction PDF

Fichiers d'entrée:
    - EUROCIEL/*.pdf : Factures Eurociel au format PDF
      (exclut automatiquement les fichiers contenant "catalogue" dans le nom)

Fichiers de sortie:
    - Logs détaillés dans la console (niveau INFO)
    - Produits créés/mis à jour dans la table `produits`
    - Stock initialisé dans la table `mouvements_stock`
    - Documents stockés dans `processed_invoices`

Workflow:
    1. Scanner le répertoire EUROCIEL/
    2. Pour chaque PDF:
       a. Extraire le texte avec pdftotext
       b. Stocker le document dans processed_invoices
       c. Parser les lignes de produits
       d. Enrichir avec le catalogue existant
       e. Importer dans la base de données
    3. Générer un rapport récapitulatif

Notes:
    - Le catalogue Eurociel principal est exclu automatiquement (trop volumineux)
    - Les doublons sont gérés automatiquement (mise à jour au lieu de création)
    - La marge de 40% est appliquée pour calculer le prix de vente
    - Le stock est initialisé uniquement pour les nouveaux produits si INITIALIZE_STOCK=True

Exemple de sortie:
    Traitement de: facture_2024_01.pdf
      Texte extrait: 15420 caractères
      Documents stockés: 1
      Lignes extraites: 45
      Import terminé: 12 créés, 33 mis à jour

    RÉSUMÉ DE L'IMPORT
    Fichiers traités: 10
    Total produits créés: 120
    Total produits mis à jour: 340
"""

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
    """
    Importe un fichier PDF de facture Eurociel dans le catalogue.

    Cette fonction effectue toutes les étapes nécessaires pour traiter une facture:
    1. Lecture du fichier PDF
    2. Extraction du texte brut
    3. Stockage du document dans processed_invoices
    4. Parsing des lignes de produits
    5. Enrichissement avec le catalogue existant
    6. Import/mise à jour dans la base de données

    Args:
        pdf_path (Path): Chemin vers le fichier PDF à importer

    Returns:
        dict: Dictionnaire avec les statistiques d'import contenant:
            - file: Nom du fichier traité
            - status: Statut (success, empty, no_products, error)
            - products: Nombre de produits détectés
            - created: Nombre de produits créés
            - updated: Nombre de produits mis à jour
            - stock_initialized: Nombre de stocks initialisés
            - errors: Liste des erreurs rencontrées

    Raises:
        Exception: En cas d'erreur lors du traitement (capturée et loggée)

    Example:
        >>> result = import_pdf(Path("EUROCIEL/facture_2024_01.pdf"))
        >>> print(result)
        {'file': 'facture_2024_01.pdf', 'status': 'success', 'products': 45,
         'created': 12, 'updated': 33, 'stock_initialized': 12, 'errors': []}
    """
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
    """
    Point d'entrée principal du script.

    Cette fonction:
    1. Vérifie l'existence du répertoire EUROCIEL
    2. Liste tous les fichiers PDF (sauf le catalogue)
    3. Traite chaque fichier séquentiellement
    4. Accumule les statistiques d'import
    5. Affiche un résumé récapitulatif

    Returns:
        None: Le script affiche les résultats et se termine

    Raises:
        SystemExit: En cas d'erreur (répertoire inexistant, aucun fichier)
    """
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
