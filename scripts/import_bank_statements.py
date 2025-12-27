#!/usr/bin/env python3
"""
Module d'import unifié des relevés bancaires PDF multi-banques.

Ce script permet de:
- Importer des relevés bancaires PDF de différentes banques (LCL, BNP, SumUp)
- Détecter automatiquement le type de banque à partir du contenu
- Parser les transactions avec dates, libellés et montants
- Gérer les relevés multi-périodes (plusieurs mois dans un seul PDF)
- Détecter et ignorer automatiquement les doublons
- Configurer automatiquement l'entité et le compte selon le nom du fichier
- Supporter le mode dry-run pour simulation sans insertion

Banques supportées:
    - LCL: Format standard et multi-périodes
    - BNP: Format avec dates en français (ex: "01 janv. 2024")
    - SumUp: Relevés de transactions de paiement

Usage:
    # Import d'un répertoire complet
    python scripts/import_bank_statements.py --dir /path/to/pdfs

    # Import d'un fichier unique avec configuration manuelle
    python scripts/import_bank_statements.py --file /path/to/file.pdf --entity RESTO --account "LCL Principal"

    # Mode dry-run pour tester sans insérer
    python scripts/import_bank_statements.py --dir /path/to/pdfs --dry-run

    # Avec URL de base de données personnalisée
    python scripts/import_bank_statements.py --dir /path/to/pdfs --database-url postgresql://...

Arguments CLI:
    --dir, -d        : Répertoire contenant les fichiers PDF
    --file, -f       : Fichier PDF unique à importer
    --entity, -e     : Code de l'entité (RESTO, EPICERIE) - optionnel, auto-détecté
    --account, -a    : Libellé du compte bancaire - optionnel, auto-détecté
    --dry-run        : Mode simulation sans insertion en base
    --database-url   : URL de connexion PostgreSQL (sinon variable DATABASE_URL)

Configuration automatique:
    Le script détecte automatiquement l'entité et le compte à partir du nom du fichier:
    - "l'incontournable" ou "incontournable" -> RESTO / LCL Principal
    - "noutam" ou "comptecourant_00459448258" -> EPICERIE / LCL Noutam
    - "bnp" ou "angele" -> RESTO / BNP Angele
    - "sumup" -> RESTO / SumUp
    - Défaut: EPICERIE / LCL Default

Variables d'environnement:
    DATABASE_URL: URL de connexion PostgreSQL (requis sauf en mode dry-run)
        Format: postgresql://user:password@host:port/database

Prérequis:
    - PostgreSQL avec les tables finance_bank_statements et finance_bank_statement_lines
    - Module core.bank_import avec BankImportOrchestrator
    - PDFs de relevés bancaires
    - pdftotext ou outil équivalent pour extraction

Fichiers d'entrée:
    - PDFs de relevés bancaires au format LCL, BNP ou SumUp
    - Un PDF peut contenir une ou plusieurs périodes

Fichiers de sortie:
    - Logs détaillés dans la console
    - Transactions insérées dans finance_bank_statement_lines
    - Statements créés dans finance_bank_statements

Workflow:
    1. Scanner les fichiers PDF (--dir) ou traiter un fichier unique (--file)
    2. Pour chaque PDF:
       a. Détecter automatiquement le compte cible (via nom de fichier)
       b. Extraire le texte du PDF
       c. Détecter le type de banque (LCL, BNP, SumUp)
       d. Parser les transactions
       e. Vérifier les doublons (par checksum)
       f. Insérer les nouvelles transactions
    3. Afficher un résumé récapitulatif

Notes:
    - Les doublons sont détectés via un checksum (date + libellé + montant)
    - Les relevés multi-périodes sont supportés (détection automatique)
    - Le mode dry-run permet de tester sans modifier la base
    - Les erreurs sont loggées mais n'arrêtent pas le traitement des autres fichiers

Exemple de sortie:
    IMPORT DES RELEVÉS BANCAIRES
    ====================================================================

    releve_lcl_noutam_2024.pdf
      EPICERIE / LCL Noutam
      2 périodes | 145/145 transactions

    releve_bnp_angele_2024.pdf
      RESTO / BNP Angele
      1 périodes | 67/72 transactions
      5 doublons ignorés

    ====================================================================
    TOTAL: 212 transactions insérées, 5 doublons, 0 erreurs
    ====================================================================
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine

from core.bank_import import BankImportOrchestrator


# Configuration par défaut des fichiers
DEFAULT_FILE_CONFIG = {
    # L'Incontournable (Restaurant)
    "l'incontournable": {"entity": "RESTO", "account": "LCL Principal"},
    "incontournable": {"entity": "RESTO", "account": "LCL Principal"},
    # Noutam (Épicerie)
    "noutam": {"entity": "EPICERIE", "account": "LCL Noutam"},
    "comptecourant_00459448258": {"entity": "EPICERIE", "account": "LCL Noutam"},
    # BNP Angele
    "bnp": {"entity": "RESTO", "account": "BNP Angele"},
    "angele": {"entity": "RESTO", "account": "BNP Angele"},
    # SumUp
    "sumup": {"entity": "RESTO", "account": "SumUp"},
}


def guess_config(filename: str) -> dict:
    """
    Devine la configuration (entité/compte) à partir du nom de fichier.

    Utilise un dictionnaire de patterns pour identifier automatiquement
    le compte bancaire et l'entité associée en fonction du nom du fichier.

    Args:
        filename (str): Nom du fichier PDF (avec ou sans extension)

    Returns:
        dict: Configuration contenant:
            - entity (str): Code de l'entité (RESTO, EPICERIE)
            - account (str): Libellé du compte bancaire

    Example:
        >>> guess_config("releve_noutam_2024.pdf")
        {'entity': 'EPICERIE', 'account': 'LCL Noutam'}
        >>> guess_config("bnp_angele.pdf")
        {'entity': 'RESTO', 'account': 'BNP Angele'}
    """
    filename_lower = filename.lower()

    for pattern, config in DEFAULT_FILE_CONFIG.items():
        if pattern in filename_lower:
            return config

    # Défaut
    return {"entity": "EPICERIE", "account": "LCL Default"}


def import_file(
    orchestrator: BankImportOrchestrator,
    pdf_path: Path,
    entity: str = None,
    account: str = None,
) -> dict:
    """
    Importe un fichier PDF de relevé bancaire.

    Cette fonction coordonne le processus d'import:
    1. Détecte la configuration (entité/compte) si non fournie
    2. Utilise l'orchestrateur pour importer le PDF
    3. Retourne un dictionnaire de statistiques

    Args:
        orchestrator (BankImportOrchestrator): Orchestrateur d'import configuré
        pdf_path (Path): Chemin vers le PDF à importer
        entity (str, optional): Code de l'entité (RESTO, EPICERIE). Auto-détecté si None
        account (str, optional): Libellé du compte. Auto-détecté si None

    Returns:
        dict: Statistiques d'import contenant:
            - file (str): Nom du fichier
            - entity (str): Code de l'entité
            - account (str): Libellé du compte
            - status (str): Statut (success, partial, failed)
            - periods (int): Nombre de périodes détectées
            - total (int): Nombre total de transactions
            - inserted (int): Nombre de transactions insérées
            - duplicates (int): Nombre de doublons ignorés
            - errors (list): Liste des 3 premières erreurs

    Example:
        >>> from core.bank_import import BankImportOrchestrator
        >>> orch = BankImportOrchestrator(engine=engine)
        >>> result = import_file(orch, Path("releve.pdf"))
        >>> print(result)
        {'file': 'releve.pdf', 'entity': 'EPICERIE', 'account': 'LCL Noutam',
         'status': 'success', 'periods': 2, 'total': 145, 'inserted': 145,
         'duplicates': 0, 'errors': []}
    """
    config = guess_config(pdf_path.name)
    entity = entity or config["entity"]
    account = account or config["account"]

    result = orchestrator.import_pdf(
        pdf_path=pdf_path,
        entity_code=entity,
        account_label=account,
    )

    return {
        "file": pdf_path.name,
        "entity": entity,
        "account": account,
        "status": result.status.value,
        "periods": result.statements_detected,
        "total": result.transactions_total,
        "inserted": result.transactions_inserted,
        "duplicates": result.transactions_duplicates,
        "errors": result.errors[:3] if result.errors else [],
    }


def main():
    """
    Point d'entrée principal du script.

    Cette fonction:
    1. Parse les arguments de ligne de commande
    2. Configure la connexion à la base de données
    3. Crée l'orchestrateur d'import
    4. Collecte les fichiers PDF à traiter
    5. Importe chaque fichier
    6. Affiche un résumé récapitulatif

    Returns:
        int: Code de sortie (0 si succès, 1 si erreurs)

    Raises:
        SystemExit: En cas d'arguments invalides ou d'erreur de configuration
    """
    parser = argparse.ArgumentParser(description="Import bank statement PDFs")
    parser.add_argument("--dir", "-d", help="Directory containing PDF files")
    parser.add_argument("--file", "-f", help="Single PDF file to import")
    parser.add_argument("--entity", "-e", help="Entity code (RESTO, EPICERIE)")
    parser.add_argument("--account", "-a", help="Account label")
    parser.add_argument("--dry-run", action="store_true", help="Parse without inserting")
    parser.add_argument("--database-url", help="Database URL (or use DATABASE_URL env var)")

    args = parser.parse_args()

    if not args.dir and not args.file:
        parser.error("Either --dir or --file is required")

    # Database connection
    db_url = args.database_url or os.environ.get("DATABASE_URL")
    if not db_url and not args.dry_run:
        parser.error("DATABASE_URL required (use --database-url or set env var)")

    engine = None if args.dry_run else create_engine(db_url)
    orchestrator = BankImportOrchestrator(engine=engine, dry_run=args.dry_run)

    # Collect files
    pdf_files = []
    if args.file:
        pdf_files.append(Path(args.file))
    if args.dir:
        pdf_files.extend(sorted(Path(args.dir).glob("*.pdf")))

    if not pdf_files:
        print("No PDF files found")
        return 1

    # Import
    print("=" * 70)
    print("IMPORT DES RELEVÉS BANCAIRES")
    if args.dry_run:
        print("(MODE DRY-RUN - pas d'insertion en base)")
    print("=" * 70)

    total_inserted = 0
    total_duplicates = 0
    total_errors = 0

    for pdf_path in pdf_files:
        if not pdf_path.exists():
            print(f"File not found: {pdf_path}")
            continue

        result = import_file(
            orchestrator,
            pdf_path,
            entity=args.entity,
            account=args.account,
        )

        status_icon = "✓" if result["status"] == "success" else "⚠" if result["status"] == "partial" else "✗"
        print(f"\n{status_icon} {result['file']}")
        print(f"  {result['entity']} / {result['account']}")
        print(f"  {result['periods']} périodes | {result['inserted']}/{result['total']} transactions")

        if result["duplicates"]:
            print(f"  {result['duplicates']} doublons ignorés")

        for err in result["errors"]:
            print(f"  ❌ {err}")

        total_inserted += result["inserted"]
        total_duplicates += result["duplicates"]
        if result["status"] == "failed":
            total_errors += 1

    print("\n" + "=" * 70)
    print(f"TOTAL: {total_inserted} transactions insérées, {total_duplicates} doublons, {total_errors} erreurs")
    print("=" * 70)

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
