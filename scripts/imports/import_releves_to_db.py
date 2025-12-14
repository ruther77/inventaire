#!/usr/bin/env python3
"""
Script d'import des relevés bancaires dans la base de données.

Utilise les parseurs de analyze_releves.py et insère les données
dans les tables finance_bank_statements, finance_bank_statement_lines,
finance_transactions et finance_transaction_lines.

Usage:
    python scripts/import_releves_to_db.py
"""

from __future__ import annotations

import hashlib
import os
import re
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

# Importer les parseurs depuis analyze_releves (dans scripts/etl/)
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir / "etl"))
sys.path.insert(0, str(scripts_dir.parent))  # Pour core/

from analyze_releves import (
    CATEGORIES,
    KeywordAnalyzer,
    LCLParser,
    BNPParser,
    SUMUPParser,
    detect_bank_type,
    parse_statement,
)

# Configuration BDD
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "db"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "epicerie"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "postgres"),
}

# Mapping fichiers -> (account_id, entity_id)
# IDs pour base epicerie:
#   1 = LCL - INCONTOURNABLE (entity 3)
#   2 = LCL - NOUTAM (entity 2)
#   3 = SUMUP - INCONTOURNABLE (entity 3)
#  14 = BNP - ANGELE (entity 2)
FILE_TO_ACCOUNT = {
    # LCL - NOUTAM / Epicerie (account 2, entity 2)
    "COMPTECOURANT_00459448258": (2, 2),
    "releve noutam lcl": (2, 2),
    # LCL - L'INCONTOURNABLE / Restaurant (account 1, entity 3)
    "l'incontournable": (1, 3),
    # BNP - ANGELE (account 14, entity 2)
    "releve 23 24 25 BNP angele": (14, 2),
    # SUMUP - L'INCONTOURNABLE (account 3, entity 3)
    "sumup releve": (3, 3),
}


def get_account_info(filename: str) -> tuple[int, int]:
    """Détermine l'ID du compte et de l'entité à partir du nom de fichier."""
    for pattern, (account_id, entity_id) in FILE_TO_ACCOUNT.items():
        if pattern.lower() in filename.lower():
            return account_id, entity_id
    raise ValueError(f"Compte non trouvé pour: {filename}")


def parse_date(date_str: str, bank_type: str, ref_year: int = None) -> datetime:
    """Parse une date selon le format de la banque.

    Args:
        date_str: La date à parser
        bank_type: Type de banque (LCL, BNP, SUMUP)
        ref_year: Année de référence pour les formats sans année (DD.MM)
    """
    if not date_str:
        return None

    # Nettoyer
    date_str = date_str.strip()

    # Format DD.MM (LCL/BNP) - utiliser l'année de référence
    if re.match(r"^\d{2}\.\d{2}$", date_str):
        day, month = date_str.split(".")
        if ref_year is None:
            # Fallback: utiliser l'année courante
            ref_year = datetime.now().year
        return datetime(ref_year, int(month), int(day))

    # Format DD.MM.YY (date valeur LCL)
    if re.match(r"^\d{2}\.\d{2}\.\d{2}$", date_str):
        day, month, year = date_str.split(".")
        year = 2000 + int(year)
        return datetime(year, int(month), int(day))

    # Format DD.MM.YYYY
    if re.match(r"^\d{2}\.\d{2}\.\d{4}$", date_str):
        day, month, year = date_str.split(".")
        return datetime(int(year), int(month), int(day))

    # Format DD/MM/YYYY (SumUp)
    if re.match(r"^\d{2}/\d{2}/\d{4}", date_str):
        parts = date_str.split()[0]  # Enlever l'heure si présente
        day, month, year = parts.split("/")
        return datetime(int(year), int(month), int(day))

    return None


def compute_checksum(date_op, libelle, montant, account_id, position: int = 0) -> str:
    """Calcule un checksum unique pour éviter les doublons.

    Args:
        position: Index de la transaction dans le relevé pour différencier
                  les transactions identiques (même date/libellé/montant)
    """
    data = f"{date_op}|{libelle}|{montant}|{account_id}|{position}"
    return hashlib.md5(data.encode()).hexdigest()


def get_month_bounds(year: int, month: int):
    """Retourne le premier et dernier jour du mois."""
    import calendar
    first_day = datetime(year, month, 1)
    last_day_num = calendar.monthrange(year, month)[1]
    last_day = datetime(year, month, last_day_num)
    return first_day, last_day


def import_to_db(folder: str = "/app/releve", split_by_month: bool = True):
    """Import les relevés dans la base de données.

    Args:
        folder: Dossier contenant les PDF
        split_by_month: Si True, crée un relevé par mois au lieu d'un par fichier
    """
    from collections import defaultdict

    folder_path = Path(folder)
    pdf_files = list(folder_path.glob("*.pdf"))

    print(f"📂 Import depuis: {folder}")
    print(f"   {len(pdf_files)} fichiers PDF trouvés")
    print(f"   Mode: {'Découpage par mois' if split_by_month else 'Un relevé par fichier'}")

    # Connexion BDD
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Récupérer les catégories
    cur.execute("SELECT id, code FROM finance_categories")
    categories_map = {row[1]: row[0] for row in cur.fetchall()}
    print(f"   {len(categories_map)} catégories en BDD")

    # Catégorie par défaut pour les non-catégorisées
    default_category_id = categories_map.get('frais_generaux', categories_map.get('achats_fournisseurs'))
    if not default_category_id and categories_map:
        default_category_id = list(categories_map.values())[0]
    print(f"   Catégorie par défaut: {default_category_id}")

    # Initialiser l'analyseur de mots-clés
    analyzer = KeywordAnalyzer()

    total_statements = 0
    total_lines = 0
    total_transactions = 0

    for pdf_file in sorted(pdf_files):
        try:
            # Parser le fichier
            stmt = parse_statement(pdf_file)
            account_id, entity_id = get_account_info(pdf_file.name)

            if not stmt.transactions:
                print(f"   ⚠ {pdf_file.name}: Aucune transaction")
                continue

            # Parser toutes les transactions avec leurs dates
            parsed_transactions = []

            # Pour BNP/SUMUP: construire un mapping mois -> années disponibles depuis opening_balances
            # Cela permet de distribuer les transactions aux bonnes années
            month_to_years = defaultdict(list)
            if stmt.opening_balances:
                for (year, month) in stmt.opening_balances.keys():
                    month_to_years[month].append(year)
                for m in month_to_years:
                    month_to_years[m].sort()  # Trier les années par ordre croissant

            for tx in stmt.transactions:
                # Déterminer l'année de référence pour cette transaction
                # Priorité: date de valeur (DD.MM.YY) > opening_balances > année courante
                ref_year = None

                # 1. Essayer d'extraire l'année depuis la date de valeur (format DD.MM.YY)
                if tx.valeur and re.match(r"^\d{2}\.\d{2}\.\d{2}$", tx.valeur):
                    year_part = tx.valeur.split(".")[2]
                    ref_year = 2000 + int(year_part)

                # 2. Fallback sur opening_balances si disponible
                if ref_year is None and tx.date and re.match(r"^\d{2}\.\d{2}$", tx.date):
                    month = int(tx.date.split(".")[1])
                    if month in month_to_years and month_to_years[month]:
                        ref_year = month_to_years[month][0]
                        if len(month_to_years[month]) > 1:
                            month_to_years[month] = month_to_years[month][1:]

                date_op = parse_date(tx.date, stmt.bank_type, ref_year)
                date_val = parse_date(tx.valeur, stmt.bank_type, ref_year) if tx.valeur else date_op

                if not date_op:
                    continue

                # Calculer le montant
                montant = Decimal("0")
                if tx.credit:
                    montant = tx.credit
                elif tx.debit:
                    montant = -tx.debit

                # Utiliser la période du relevé d'origine si disponible (LCL)
                # Sinon fallback sur le mois calendaire
                if tx.statement_period:
                    period_key = tx.statement_period  # (period_start, period_end) DD.MM.YYYY
                else:
                    # Fallback: construire une clé basée sur le mois calendaire
                    period_key = (date_op.year, date_op.month)

                parsed_transactions.append({
                    'date_op': date_op,
                    'date_val': date_val,
                    'libelle': tx.libelle,
                    'montant': montant,
                    'period_key': period_key,
                    'statement_period': tx.statement_period,
                })

            if not parsed_transactions:
                print(f"   ⚠ {pdf_file.name}: Aucune transaction valide")
                continue

            # Grouper par période de relevé
            if split_by_month:
                by_period = defaultdict(list)
                for ptx in parsed_transactions:
                    by_period[ptx['period_key']].append(ptx)

                print(f"   📄 {pdf_file.name}: {len(parsed_transactions)} tx → {len(by_period)} périodes")

                for period_key, period_txs in sorted(by_period.items(), key=lambda x: str(x[0])):
                    # Déterminer les dates de période
                    if isinstance(period_key, tuple) and len(period_key) == 2 and isinstance(period_key[0], str):
                        # C'est une vraie période de relevé (period_start, period_end) DD.MM.YYYY
                        period_start = parse_date(period_key[0], stmt.bank_type)
                        period_end = parse_date(period_key[1], stmt.bank_type)
                        period_label = f"{period_key[0]}-{period_key[1]}"
                        # Extraire year/month de la fin de période pour lookup solde
                        year = period_end.year
                        month = period_end.month
                    else:
                        # Fallback: (year, month) tuple
                        year, month = period_key
                        period_start, period_end = get_month_bounds(year, month)
                        period_label = f"{year}-{month:02d}"

                    period_hash = hashlib.md5(f"{pdf_file.name}:{period_label}".encode()).hexdigest()

                    # Récupérer le solde d'ouverture pour cette période
                    opening_balance = stmt.opening_balances.get((year, month))

                    # Vérifier si cette période est déjà importée
                    cur.execute("""
                        SELECT id, opening_balance FROM finance_bank_statements
                        WHERE account_id = %s AND period_start = %s AND period_end = %s
                    """, (account_id, period_start.date(), period_end.date()))
                    existing = cur.fetchone()
                    if existing:
                        # Mettre à jour le solde d'ouverture si manquant
                        if opening_balance is not None and existing[1] is None:
                            cur.execute("""
                                UPDATE finance_bank_statements
                                SET opening_balance = %s
                                WHERE id = %s
                            """, (float(opening_balance), existing[0]))
                            conn.commit()
                            print(f"      🔄 {period_label}: Solde ouverture mis à jour ({opening_balance:.2f}€)")
                        else:
                            print(f"      ⏭ {period_label}: Déjà importé")
                        continue

                    # Créer le statement pour cette période avec solde d'ouverture
                    cur.execute("""
                        INSERT INTO finance_bank_statements
                        (account_id, period_start, period_end, source, file_name, hash, opening_balance)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (account_id, period_start.date(), period_end.date(), 'PDF_IMPORT',
                          f"{pdf_file.name}:{period_label}", period_hash,
                          float(opening_balance) if opening_balance else None))
                    statement_id = cur.fetchone()[0]
                    total_statements += 1

                    # Insérer les lignes de cette période
                    period_lines = 0
                    period_tx_count = 0
                    for tx_idx, ptx in enumerate(period_txs):
                        checksum = compute_checksum(ptx['date_op'], ptx['libelle'], ptx['montant'], account_id, tx_idx)

                        # Vérifier doublon ligne
                        cur.execute("SELECT id FROM finance_bank_statement_lines WHERE checksum = %s", (checksum,))
                        if cur.fetchone():
                            continue

                        # Insérer ligne de relevé
                        cur.execute("""
                            INSERT INTO finance_bank_statement_lines
                            (statement_id, date_operation, date_valeur, libelle_banque, montant, checksum)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (statement_id, ptx['date_op'].date(),
                              ptx['date_val'].date() if ptx['date_val'] else None,
                              ptx['libelle'], float(ptx['montant']), checksum))
                        period_lines += 1
                        total_lines += 1

                        # Créer la transaction
                        direction = 'IN' if ptx['montant'] > 0 else 'OUT'
                        amount_abs = abs(float(ptx['montant']))

                        # Catégoriser
                        cat_code, _ = analyzer.categorize(ptx['libelle'])
                        category_id = categories_map.get(cat_code) if cat_code else default_category_id
                        if not category_id:
                            category_id = default_category_id

                        cur.execute("""
                            INSERT INTO finance_transactions
                            (entity_id, account_id, direction, source, date_operation, amount,
                             ref_externe, status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (entity_id, account_id, direction, 'IMPORT_PDF',
                              ptx['date_op'].date(), amount_abs, f"stmtline:{checksum}", 'CONFIRMED'))
                        tx_id = cur.fetchone()[0]

                        cur.execute("""
                            INSERT INTO finance_transaction_lines
                            (transaction_id, category_id, montant_ttc, description, position)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (tx_id, category_id, amount_abs, ptx['libelle'], 1))
                        period_tx_count += 1
                        total_transactions += 1

                    conn.commit()
                    print(f"      ✓ {period_label}: {period_lines} lignes, {period_tx_count} tx")

            else:
                # Mode original: un relevé par fichier
                period_start = min(ptx['date_op'] for ptx in parsed_transactions)
                period_end = max(ptx['date_op'] for ptx in parsed_transactions)
                file_hash = hashlib.md5(pdf_file.read_bytes()).hexdigest()

                cur.execute("SELECT id FROM finance_bank_statements WHERE hash = %s", (file_hash,))
                if cur.fetchone():
                    print(f"   ⏭ {pdf_file.name}: Déjà importé")
                    continue

                cur.execute("""
                    INSERT INTO finance_bank_statements
                    (account_id, period_start, period_end, source, file_name, hash)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (account_id, period_start.date(), period_end.date(), 'PDF_IMPORT', pdf_file.name, file_hash))
                statement_id = cur.fetchone()[0]
                total_statements += 1

                for tx_idx, ptx in enumerate(parsed_transactions):
                    checksum = compute_checksum(ptx['date_op'], ptx['libelle'], ptx['montant'], account_id, tx_idx)

                    # Vérifier doublon ligne
                    cur.execute("SELECT id FROM finance_bank_statement_lines WHERE checksum = %s", (checksum,))
                    if cur.fetchone():
                        continue

                    # Insérer ligne de relevé
                    cur.execute("""
                        INSERT INTO finance_bank_statement_lines
                        (statement_id, date_operation, date_valeur, libelle_banque, montant, checksum)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (statement_id, ptx['date_op'].date(),
                          ptx['date_val'].date() if ptx['date_val'] else None,
                          ptx['libelle'], float(ptx['montant']), checksum))
                    total_lines += 1

                    # Créer la transaction
                    direction = 'IN' if ptx['montant'] > 0 else 'OUT'
                    amount_abs = abs(float(ptx['montant']))

                    cat_code, _ = analyzer.categorize(ptx['libelle'])
                    category_id = categories_map.get(cat_code) if cat_code else default_category_id

                    cur.execute("""
                        INSERT INTO finance_transactions
                        (entity_id, account_id, direction, source, date_operation, amount, ref_externe, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (entity_id, account_id, direction, 'IMPORT_PDF',
                          ptx['date_op'].date(), amount_abs, f"stmtline:{checksum}", 'CONFIRMED'))
                    tx_id = cur.fetchone()[0]

                    cur.execute("""
                        INSERT INTO finance_transaction_lines
                        (transaction_id, category_id, montant_ttc, description, position)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (tx_id, category_id, amount_abs, ptx['libelle'], 1))
                    total_transactions += 1

                conn.commit()
                print(f"   ✓ {pdf_file.name}: {len(parsed_transactions)} tx → compte {account_id}")

        except Exception as e:
            conn.rollback()
            print(f"   ✗ {pdf_file.name}: ERREUR - {e}")
            import traceback
            traceback.print_exc()

    # Résumé
    print()
    print("=" * 60)
    print(f"📊 RÉSUMÉ DE L'IMPORT")
    print(f"   Statements créés: {total_statements}")
    print(f"   Lignes de relevé: {total_lines}")
    print(f"   Transactions: {total_transactions}")

    # Vérifier les soldes
    cur.execute("""
        SELECT fa.label,
               COALESCE(SUM(CASE WHEN fbsl.montant > 0 THEN fbsl.montant ELSE 0 END), 0) as entrees,
               COALESCE(SUM(CASE WHEN fbsl.montant < 0 THEN ABS(fbsl.montant) ELSE 0 END), 0) as sorties,
               COALESCE(SUM(fbsl.montant), 0) as solde
        FROM finance_accounts fa
        LEFT JOIN finance_bank_statements fbs ON fbs.account_id = fa.id
        LEFT JOIN finance_bank_statement_lines fbsl ON fbsl.statement_id = fbs.id
        GROUP BY fa.id, fa.label
        ORDER BY fa.label
    """)

    print()
    print("📈 SOLDES PAR COMPTE")
    print("-" * 60)
    for row in cur.fetchall():
        label, entrees, sorties, solde = row
        print(f"   {label:<25} | E: {entrees:>12,.2f}€ | S: {sorties:>12,.2f}€ | Solde: {solde:>12,.2f}€")

    cur.close()
    conn.close()
    print()
    print("✅ Import terminé!")


if __name__ == "__main__":
    import_to_db()
