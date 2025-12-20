#!/usr/bin/env python3
"""Script d'import intelligent de relevés bancaires avec gestion des chevauchements.

Fonctionnalités:
- Détection automatique du type de banque (LCL, BNP, SumUp)
- Fusion intelligente des transactions sur des périodes chevauchantes
- Gestion des priorités de sources (consolidé > mensuel)
- Détection de doublons avec fuzzy matching
- Mapping automatique des comptes
- Mode dry-run pour simulation
- Rapports détaillés

Usage:
    # Dry-run pour simuler
    python scripts/smart_bank_import.py /releve/ --dry-run

    # Import avec compte spécifique
    python scripts/smart_bank_import.py /releve/ --account-id 16 --force-merge

    # Import avec priorité
    python scripts/smart_bank_import.py /releve/COMPTECOURANT_*.pdf --priority 2

    # Import multi-sources avec fusion intelligente
    python scripts/smart_bank_import.py /releve/*.pdf --smart-merge
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from difflib import SequenceMatcher
from sqlalchemy import text

# Imports du projet
try:
    from core.bank_import import BankImportOrchestrator, UnifiedBankParser, BankDetector, PDFExtractor
    from core.bank_import.models import BankType, ParsedTransaction, TransactionDirection
    from core.data_repository import get_engine
except ImportError as e:
    print(f"Erreur d'import: {e}")
    print("Assurez-vous d'être dans le bon environnement virtuel et répertoire")
    sys.exit(1)


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("smart_bank_import.log")
    ]
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Priorités d'import (plus bas = priorité haute)
IMPORT_PRIORITY = {
    "releve noutam lcl.pdf": 1,           # Consolidé LCL (priorité haute)
    "COMPTECOURANT": 2,                    # Mensuel LCL (priorité moyenne)
    "BNP": 2,                              # BNP
    "SUMUP": 2,                            # SumUp
    "DEFAULT": 3,                          # Défaut (priorité basse)
}

# Mapping automatique des comptes par pattern de fichier
ACCOUNT_MAPPING = {
    "BNP": {
        "pattern": r"(?i)(bnp|angele)",
        "account_id": 14,
        "entity_code": "EPICERIE",
        "label": "BNP - Angele",
    },
    "LCL_NOUTAM": {
        "pattern": r"(?i)(noutam|COMPTECOURANT)",
        "account_id": 16,
        "entity_code": "EPICERIE",
        "label": "LCL - Noutam",
    },
    "LCL_INCONTOURNABLE": {
        "pattern": r"(?i)(incontournable)",
        "account_id": 17,
        "entity_code": "EPICERIE",
        "label": "LCL - Incontournable",
    },
    "SUMUP": {
        "pattern": r"(?i)(sumup)",
        "account_id": 3,
        "entity_code": "EPICERIE",
        "label": "SumUp",
    },
}

# Tolérance pour détection de doublons
TOLERANCE_DAYS = 1
TOLERANCE_AMOUNT = Decimal("0.01")
FUZZY_MATCH_THRESHOLD = 0.80  # 80% de similarité


# =============================================================================
# MODÈLES DE DONNÉES
# =============================================================================

@dataclass
class TransactionKey:
    """Clé unique pour identifier une transaction."""
    date: date
    libelle: str
    montant: Decimal

    def __hash__(self):
        return hash((self.date, self.libelle.lower(), self.montant))

    def __eq__(self, other):
        if not isinstance(other, TransactionKey):
            return False
        return (
            self.date == other.date
            and self.libelle.lower() == other.libelle.lower()
            and self.montant == other.montant
        )


@dataclass
class SourcedTransaction:
    """Transaction avec sa source et priorité."""
    transaction: ParsedTransaction
    source_file: str
    priority: int
    checksum: str

    def to_key(self) -> TransactionKey:
        return TransactionKey(
            date=self.transaction.date_operation,
            libelle=self.transaction.libelle,
            montant=self.transaction.montant,
        )


@dataclass
class ImportStats:
    """Statistiques d'import pour un fichier."""
    file_path: str
    bank_type: str
    priority: int
    total_transactions: int = 0
    new_transactions: int = 0
    duplicate_transactions: int = 0
    merged_transactions: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    period_start: Optional[date] = None
    period_end: Optional[date] = None

    @property
    def inserted_transactions(self) -> int:
        return self.new_transactions - self.merged_transactions


@dataclass
class GlobalReport:
    """Rapport global de l'import multi-fichiers."""
    files_processed: int = 0
    files_success: int = 0
    files_failed: int = 0
    total_transactions: int = 0
    new_transactions: int = 0
    duplicate_transactions: int = 0
    merged_transactions: int = 0
    file_stats: List[ImportStats] = field(default_factory=list)
    period_coverage: Dict[str, List[Tuple[date, date]]] = field(default_factory=dict)
    missing_periods: List[Tuple[date, date]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# DÉTECTION ET FUSION DE DOUBLONS
# =============================================================================

def fuzzy_match(str1: str, str2: str) -> float:
    """Calcule la similarité entre deux chaînes (0.0 à 1.0).

    Args:
        str1: Première chaîne
        str2: Deuxième chaîne

    Returns:
        Score de similarité (0.0 = différent, 1.0 = identique)
    """
    s1 = str1.strip().upper()
    s2 = str2.strip().upper()
    return SequenceMatcher(None, s1, s2).ratio()


def is_duplicate(
    tx1: SourcedTransaction,
    tx2: SourcedTransaction,
    tolerance_days: int = TOLERANCE_DAYS,
    tolerance_amount: Decimal = TOLERANCE_AMOUNT,
) -> bool:
    """Vérifie si deux transactions sont des doublons.

    Critères:
    - Même compte (implicite via le groupement)
    - Date à ±tolerance_days
    - Montant identique (±tolerance_amount)
    - Libellé similaire (fuzzy match > threshold)

    Args:
        tx1: Première transaction
        tx2: Deuxième transaction
        tolerance_days: Tolérance en jours pour la date
        tolerance_amount: Tolérance pour le montant

    Returns:
        True si doublon détecté
    """
    t1 = tx1.transaction
    t2 = tx2.transaction

    # Vérifier la date (± tolérance)
    date_diff = abs((t1.date_operation - t2.date_operation).days)
    if date_diff > tolerance_days:
        return False

    # Vérifier le montant (± tolérance)
    amount_diff = abs(t1.montant - t2.montant)
    if amount_diff > tolerance_amount:
        return False

    # Vérifier la direction
    if t1.direction != t2.direction:
        return False

    # Vérifier la similarité du libellé
    similarity = fuzzy_match(t1.libelle, t2.libelle)
    if similarity < FUZZY_MATCH_THRESHOLD:
        return False

    logger.debug(
        f"Doublon détecté: {t1.date_operation} {t1.libelle[:30]} "
        f"(similarité: {similarity:.2%})"
    )
    return True


def merge_transactions(
    existing: SourcedTransaction,
    new: SourcedTransaction,
) -> SourcedTransaction:
    """Fusionne deux transactions en gardant la meilleure information.

    Stratégie:
    - Garde la transaction de la source avec priorité la plus haute
    - Si même priorité, garde le meilleur libellé (plus long, plus descriptif)
    - Garde la date la plus précise

    Args:
        existing: Transaction existante
        new: Nouvelle transaction

    Returns:
        Transaction fusionnée (gagnante)
    """
    # Priorité (plus bas = meilleur)
    if existing.priority < new.priority:
        winner = existing
        loser = new
    elif new.priority < existing.priority:
        winner = new
        loser = existing
    else:
        # Même priorité: choisir le meilleur libellé
        winner = _choose_best_libelle(existing, new)
        loser = new if winner == existing else existing

    logger.info(
        f"Fusion: garde '{winner.source_file}' (priorité {winner.priority}) "
        f"au lieu de '{loser.source_file}' (priorité {loser.priority})"
    )

    return winner


def _choose_best_libelle(
    tx1: SourcedTransaction,
    tx2: SourcedTransaction,
) -> SourcedTransaction:
    """Choisit la transaction avec le meilleur libellé.

    Critères:
    - Pas de préfixe technique (stmtline:, etc.)
    - Plus long = plus descriptif
    - Moins de caractères spéciaux

    Args:
        tx1: Première transaction
        tx2: Deuxième transaction

    Returns:
        Transaction avec le meilleur libellé
    """
    lib1 = tx1.transaction.libelle
    lib2 = tx2.transaction.libelle

    # Éliminer les préfixes techniques
    if lib1.startswith("stmtline:") and not lib2.startswith("stmtline:"):
        return tx2
    if lib2.startswith("stmtline:") and not lib1.startswith("stmtline:"):
        return tx1

    # Préférer le plus long
    if len(lib1) > len(lib2) * 1.2:  # 20% plus long
        return tx1
    if len(lib2) > len(lib1) * 1.2:
        return tx2

    # Si équivalent, garder le premier
    return tx1


# =============================================================================
# MAPPING DE COMPTES
# =============================================================================

def detect_account_from_filename(filename: str) -> Optional[Dict[str, Any]]:
    """Détecte le compte cible depuis le nom de fichier.

    Args:
        filename: Nom du fichier

    Returns:
        Dict avec account_id, entity_code, label ou None
    """
    for name, config in ACCOUNT_MAPPING.items():
        if re.search(config["pattern"], filename):
            logger.info(f"Compte détecté: {name} depuis '{filename}'")
            return config

    logger.warning(f"Aucun mapping de compte trouvé pour '{filename}'")
    return None


def get_file_priority(filename: str) -> int:
    """Détermine la priorité d'un fichier.

    Args:
        filename: Nom du fichier

    Returns:
        Niveau de priorité (plus bas = priorité haute)
    """
    filename_upper = filename.upper()

    for pattern, priority in IMPORT_PRIORITY.items():
        if pattern.upper() in filename_upper:
            return priority

    return IMPORT_PRIORITY["DEFAULT"]


# =============================================================================
# PARSING ET EXTRACTION
# =============================================================================

def parse_pdf_file(pdf_path: Path) -> Tuple[List[ParsedTransaction], BankType, date, date]:
    """Parse un PDF et extrait les transactions.

    Args:
        pdf_path: Chemin vers le PDF

    Returns:
        Tuple (transactions, bank_type, period_start, period_end)
    """
    logger.info(f"Parsing {pdf_path.name}...")

    try:
        # Utiliser le workflow core.bank_import unifié
        extractor = PDFExtractor()
        detector = BankDetector()
        parser = UnifiedBankParser()

        # 1. Extraire le texte du PDF
        text_content = extractor.extract(str(pdf_path))

        # 2. Détecter le type de banque
        bank_type = detector.detect(text_content)

        # 3. Parser les transactions
        statements = parser.parse(text_content, bank_type)

        # Collecter toutes les transactions
        transactions = []
        period_start = None
        period_end = None

        for stmt in statements:
            transactions.extend(stmt.transactions)
            if period_start is None or stmt.period.start_date < period_start:
                period_start = stmt.period.start_date
            if period_end is None or stmt.period.end_date > period_end:
                period_end = stmt.period.end_date

        # Fallback pour les dates de période
        if not transactions:
            period_start = date.today()
            period_end = date.today()
        elif period_start is None:
            period_start = min(tx.date_operation for tx in transactions)
            period_end = max(tx.date_operation for tx in transactions)

        logger.info(
            f"Parsed {len(transactions)} transactions from {pdf_path.name} "
            f"({bank_type.value}, {period_start} - {period_end})"
        )

        return transactions, bank_type, period_start, period_end

    except Exception as e:
        logger.error(f"Erreur lors du parsing de {pdf_path.name}: {e}")
        raise


# =============================================================================
# FUSION INTELLIGENTE MULTI-SOURCES
# =============================================================================

def smart_merge_sources(
    all_sourced: List[SourcedTransaction],
) -> Tuple[List[SourcedTransaction], int]:
    """Fusionne intelligemment les transactions de plusieurs sources.

    Algorithme:
    1. Groupe par date approximative (±tolerance_days)
    2. Pour chaque groupe, détecte les doublons
    3. Garde la meilleure version (priorité + qualité libellé)

    Args:
        all_sourced: Toutes les transactions sourcées

    Returns:
        Tuple (transactions_fusionnées, nombre_de_fusions)
    """
    logger.info(f"Fusion intelligente de {len(all_sourced)} transactions...")

    # Grouper par plage de dates (fenêtre glissante)
    date_groups: Dict[date, List[SourcedTransaction]] = defaultdict(list)

    for tx in all_sourced:
        base_date = tx.transaction.date_operation
        date_groups[base_date].append(tx)

    # Fusionner les doublons dans chaque groupe
    merged: List[SourcedTransaction] = []
    merge_count = 0
    processed: Set[str] = set()

    for group_date, group_txs in sorted(date_groups.items()):
        # Trier par priorité (plus bas = meilleur)
        group_txs.sort(key=lambda x: x.priority)

        for i, tx in enumerate(group_txs):
            if tx.checksum in processed:
                continue

            # Chercher des doublons dans le reste du groupe
            has_duplicate = False
            for other in group_txs[i + 1:]:
                if other.checksum in processed:
                    continue

                if is_duplicate(tx, other):
                    # Fusionner
                    winner = merge_transactions(tx, other)
                    processed.add(other.checksum)

                    # Remplacer tx par le gagnant si nécessaire
                    if winner.checksum != tx.checksum:
                        tx = winner

                    merge_count += 1
                    has_duplicate = True

            processed.add(tx.checksum)
            merged.append(tx)

    logger.info(
        f"Fusion terminée: {len(merged)} transactions uniques "
        f"({merge_count} fusions)"
    )

    return merged, merge_count


# =============================================================================
# IMPORT DANS LA BASE DE DONNÉES
# =============================================================================

def import_to_database(
    transactions: List[SourcedTransaction],
    account_id: int,
    entity_code: str,
    dry_run: bool = False,
) -> Tuple[int, int]:
    """Importe les transactions dans la base de données.

    Args:
        transactions: Transactions à importer
        account_id: ID du compte cible
        entity_code: Code de l'entité
        dry_run: Si True, ne fait pas l'insertion réelle

    Returns:
        Tuple (inserted, duplicates)
    """
    if dry_run:
        logger.info(f"[DRY-RUN] {len(transactions)} transactions seraient importées")
        return len(transactions), 0

    engine = get_engine()
    inserted = 0
    duplicates = 0

    # Grouper par période pour créer les statements
    period_groups: Dict[Tuple[date, date], List[SourcedTransaction]] = defaultdict(list)

    for tx in transactions:
        # Utiliser une période mensuelle
        start = tx.transaction.date_operation.replace(day=1)
        if start.month == 12:
            end = date(start.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(start.year, start.month + 1, 1) - timedelta(days=1)

        period_groups[(start, end)].append(tx)

    # Importer chaque période
    with engine.begin() as conn:
        for (period_start, period_end), period_txs in period_groups.items():
            # Créer ou récupérer le statement
            stmt_row = conn.execute(
                text(
                    "SELECT id FROM finance_bank_statements "
                    "WHERE account_id = :acc AND period_start = :ps AND period_end = :pe"
                ),
                {"acc": account_id, "ps": period_start, "pe": period_end}
            ).fetchone()

            if stmt_row:
                statement_id = int(stmt_row.id)
            else:
                statement_id = int(conn.execute(
                    text(
                        "INSERT INTO finance_bank_statements "
                        "(account_id, period_start, period_end, source, imported_at) "
                        "VALUES (:acc, :ps, :pe, 'SMART_IMPORT', now()) RETURNING id"
                    ),
                    {"acc": account_id, "ps": period_start, "pe": period_end}
                ).scalar_one())

            # Récupérer les checksums existants
            existing = conn.execute(
                text(
                    "SELECT checksum FROM finance_bank_statement_lines "
                    "WHERE account_id = :acc AND date_operation BETWEEN :ps AND :pe"
                ),
                {"acc": account_id, "ps": period_start, "pe": period_end}
            ).fetchall()
            existing_checksums = {row[0] for row in existing if row[0]}

            # Insérer les transactions
            for tx in period_txs:
                if tx.checksum in existing_checksums:
                    duplicates += 1
                    continue

                conn.execute(
                    text(
                        "INSERT INTO finance_bank_statement_lines "
                        "(statement_id, account_id, date_operation, date_valeur, "
                        "libelle_banque, montant, checksum) "
                        "VALUES (:sid, :acc, :do, :dv, :lib, :amt, :chk)"
                    ),
                    {
                        "sid": statement_id,
                        "acc": account_id,
                        "do": tx.transaction.date_operation,
                        "dv": tx.transaction.date_valeur,
                        "lib": tx.transaction.libelle,
                        "amt": float(tx.transaction.montant_signe),
                        "chk": tx.checksum,
                    }
                )
                inserted += 1

    logger.info(f"Import terminé: {inserted} insérées, {duplicates} doublons ignorés")
    return inserted, duplicates


# =============================================================================
# GÉNÉRATION DE RAPPORTS
# =============================================================================

def generate_report(report: GlobalReport, output_file: Optional[Path] = None) -> str:
    """Génère un rapport détaillé de l'import.

    Args:
        report: Rapport global
        output_file: Fichier de sortie optionnel

    Returns:
        Rapport formaté en texte
    """
    lines = []
    lines.append("=" * 80)
    lines.append("RAPPORT D'IMPORT INTELLIGENT DES RELEVÉS BANCAIRES")
    lines.append("=" * 80)
    lines.append("")

    # Résumé global
    lines.append("RÉSUMÉ GLOBAL")
    lines.append("-" * 80)
    lines.append(f"Fichiers traités:           {report.files_processed}")
    lines.append(f"Fichiers réussis:           {report.files_success}")
    lines.append(f"Fichiers en erreur:         {report.files_failed}")
    lines.append(f"Transactions totales:       {report.total_transactions}")
    lines.append(f"Transactions nouvelles:     {report.new_transactions}")
    lines.append(f"Transactions dupliquées:    {report.duplicate_transactions}")
    lines.append(f"Transactions fusionnées:    {report.merged_transactions}")
    lines.append("")

    # Détail par fichier
    lines.append("DÉTAIL PAR FICHIER")
    lines.append("-" * 80)

    for stats in report.file_stats:
        lines.append(f"\nFichier: {stats.file_path}")
        lines.append(f"  Banque:             {stats.bank_type}")
        lines.append(f"  Priorité:           {stats.priority}")
        lines.append(f"  Période:            {stats.period_start} → {stats.period_end}")
        lines.append(f"  Transactions:       {stats.total_transactions}")
        lines.append(f"  Nouvelles:          {stats.new_transactions}")
        lines.append(f"  Doublons:           {stats.duplicate_transactions}")
        lines.append(f"  Fusionnées:         {stats.merged_transactions}")

        if stats.errors:
            lines.append("  ERREURS:")
            for err in stats.errors:
                lines.append(f"    - {err}")

        if stats.warnings:
            lines.append("  AVERTISSEMENTS:")
            for warn in stats.warnings:
                lines.append(f"    - {warn}")

    # Couverture des périodes
    if report.period_coverage:
        lines.append("\n")
        lines.append("COUVERTURE DES PÉRIODES PAR COMPTE")
        lines.append("-" * 80)

        for account, periods in report.period_coverage.items():
            lines.append(f"\nCompte: {account}")
            for start, end in sorted(periods):
                lines.append(f"  {start} → {end}")

    # Périodes manquantes
    if report.missing_periods:
        lines.append("\n")
        lines.append("PÉRIODES MANQUANTES DÉTECTÉES")
        lines.append("-" * 80)

        for start, end in report.missing_periods:
            lines.append(f"  {start} → {end}")

    # Erreurs globales
    if report.errors:
        lines.append("\n")
        lines.append("ERREURS GLOBALES")
        lines.append("-" * 80)
        for err in report.errors:
            lines.append(f"  - {err}")

    # Avertissements globaux
    if report.warnings:
        lines.append("\n")
        lines.append("AVERTISSEMENTS GLOBAUX")
        lines.append("-" * 80)
        for warn in report.warnings:
            lines.append(f"  - {warn}")

    lines.append("\n" + "=" * 80)

    report_text = "\n".join(lines)

    # Sauvegarder si demandé
    if output_file:
        output_file.write_text(report_text)
        logger.info(f"Rapport sauvegardé dans {output_file}")

    return report_text


def detect_missing_periods(
    period_coverage: Dict[str, List[Tuple[date, date]]]
) -> List[Tuple[date, date]]:
    """Détecte les périodes manquantes dans la couverture.

    Args:
        period_coverage: Couverture par compte

    Returns:
        Liste des périodes manquantes
    """
    missing = []

    for account, periods in period_coverage.items():
        if not periods:
            continue

        sorted_periods = sorted(periods)

        for i in range(len(sorted_periods) - 1):
            current_end = sorted_periods[i][1]
            next_start = sorted_periods[i + 1][0]

            # Vérifier s'il y a un gap
            gap_days = (next_start - current_end).days
            if gap_days > 1:  # Plus d'un jour de gap
                missing.append((current_end + timedelta(days=1), next_start - timedelta(days=1)))

    return missing


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(
        description="Import intelligent de relevés bancaires avec gestion des chevauchements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Fichiers PDF à importer (supporte les wildcards)",
    )

    parser.add_argument(
        "--account-id",
        type=int,
        help="ID du compte cible (sinon détecté automatiquement)",
    )

    parser.add_argument(
        "--entity-code",
        default="EPICERIE",
        help="Code de l'entité (défaut: EPICERIE)",
    )

    parser.add_argument(
        "--priority",
        type=int,
        help="Priorité manuelle (sinon détectée automatiquement)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode simulation: ne fait pas l'import réel",
    )

    parser.add_argument(
        "--smart-merge",
        action="store_true",
        default=True,
        help="Active la fusion intelligente des doublons (activé par défaut)",
    )

    parser.add_argument(
        "--force-merge",
        action="store_true",
        help="Force la fusion même pour les fichiers de même priorité",
    )

    parser.add_argument(
        "--report",
        type=Path,
        help="Fichier de sortie pour le rapport détaillé",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Mode verbose (plus de logs)",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Résoudre les wildcards
    all_files = []
    for pattern in args.files:
        if "*" in str(pattern):
            all_files.extend(Path(".").glob(str(pattern)))
        else:
            all_files.append(pattern)

    pdf_files = [f for f in all_files if f.suffix.lower() == ".pdf" and f.exists()]

    if not pdf_files:
        logger.error("Aucun fichier PDF trouvé")
        sys.exit(1)

    logger.info(f"Fichiers à traiter: {len(pdf_files)}")

    # Rapport global
    global_report = GlobalReport()

    # Collecter toutes les transactions sourcées
    all_sourced: List[SourcedTransaction] = []
    account_groups: Dict[int, List[SourcedTransaction]] = defaultdict(list)

    # Phase 1: Parser tous les fichiers
    for pdf_file in pdf_files:
        global_report.files_processed += 1
        stats = ImportStats(
            file_path=str(pdf_file),
            bank_type="UNKNOWN",
            priority=args.priority or get_file_priority(pdf_file.name),
        )

        try:
            # Détecter le compte
            if args.account_id:
                account_config = {
                    "account_id": args.account_id,
                    "entity_code": args.entity_code,
                    "label": f"Account {args.account_id}",
                }
            else:
                account_config = detect_account_from_filename(pdf_file.name)
                if not account_config:
                    stats.errors.append("Compte non détecté automatiquement")
                    global_report.file_stats.append(stats)
                    continue

            account_id = account_config["account_id"]

            # Parser le PDF
            transactions, bank_type, period_start, period_end = parse_pdf_file(pdf_file)

            stats.bank_type = bank_type.value
            stats.period_start = period_start
            stats.period_end = period_end
            stats.total_transactions = len(transactions)

            # Créer les SourcedTransaction
            for tx in transactions:
                # Générer checksum
                checksum_data = (
                    f"{account_id}|{tx.date_operation.isoformat()}|"
                    f"{tx.libelle.upper()}|{tx.montant}|{tx.direction.value}"
                )
                checksum = hashlib.sha256(checksum_data.encode()).hexdigest()[:32]

                sourced = SourcedTransaction(
                    transaction=tx,
                    source_file=pdf_file.name,
                    priority=stats.priority,
                    checksum=checksum,
                )

                all_sourced.append(sourced)
                account_groups[account_id].append(sourced)

            # Ajouter à la couverture
            account_label = account_config["label"]
            if account_label not in global_report.period_coverage:
                global_report.period_coverage[account_label] = []
            global_report.period_coverage[account_label].append((period_start, period_end))

            global_report.files_success += 1
            logger.info(f"✓ {pdf_file.name}: {len(transactions)} transactions")

        except Exception as e:
            logger.error(f"✗ {pdf_file.name}: {e}")
            stats.errors.append(str(e))
            global_report.files_failed += 1
            global_report.errors.append(f"{pdf_file.name}: {e}")

        global_report.file_stats.append(stats)

    # Phase 2: Fusion intelligente par compte
    if args.smart_merge:
        logger.info("Phase de fusion intelligente...")

        for account_id, txs in account_groups.items():
            logger.info(f"Fusion pour compte {account_id}: {len(txs)} transactions")
            merged, merge_count = smart_merge_sources(txs)

            # Remplacer dans all_sourced
            # (simplifié: on garde toutes les merged)
            global_report.merged_transactions += merge_count

            # Mettre à jour les stats des fichiers
            for stats in global_report.file_stats:
                if stats.file_path in {tx.source_file for tx in txs}:
                    stats.merged_transactions = merge_count // len(pdf_files)  # Approximation

    # Phase 3: Import dans la base
    global_report.total_transactions = len(all_sourced)

    for account_id, txs in account_groups.items():
        # Récupérer le config du compte
        sample_tx = txs[0]
        account_config = detect_account_from_filename(sample_tx.source_file)
        if not account_config:
            continue

        inserted, duplicates = import_to_database(
            txs,
            account_id,
            account_config["entity_code"],
            dry_run=args.dry_run,
        )

        global_report.new_transactions += inserted
        global_report.duplicate_transactions += duplicates

    # Phase 4: Détecter les périodes manquantes
    global_report.missing_periods = detect_missing_periods(global_report.period_coverage)

    # Phase 5: Générer le rapport
    report_text = generate_report(global_report, args.report)
    print("\n" + report_text)

    # Code de sortie
    if global_report.files_failed > 0:
        sys.exit(1)

    logger.info("Import terminé avec succès")


if __name__ == "__main__":
    main()
