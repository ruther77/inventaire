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

# Importer les parseurs depuis analyze_releves
sys.path.insert(0, str(Path(__file__).parent))
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
FILE_TO_ACCOUNT = {
    # LCL - INCONTOURNABLE (entity_id=3)
    "COMPTECOURANT_00459448258": (1, 3),
    "l'incontournable": (1, 3),
    # LCL - NOUTAM (entity_id=2)
    "releve noutam lcl": (2, 2),
    # SUMUP - INCONTOURNABLE (entity_id=3)
    "sumup releve": (3, 3),
    # BNP - ANGELE (entity_id=2)
    "releve 23 24 25 BNP angele": (14, 2),
}


def get_account_info(filename: str) -> tuple[int, int]:
    """Détermine l'ID du compte et de l'entité à partir du nom de fichier."""
    for pattern, (account_id, entity_id) in FILE_TO_ACCOUNT.items():
        if pattern.lower() in filename.lower():
            return account_id, entity_id
    raise ValueError(f"Compte non trouvé pour: {filename}")


def parse_date(date_str: str, bank_type: str) -> datetime:
    """Parse une date selon le format de la banque."""
    if not date_str:
        return None

    # Nettoyer
    date_str = date_str.strip()

    # Format DD.MM (LCL/BNP) - on ajoute l'année courante
    if re.match(r"^\d{2}\.\d{2}$", date_str):
        day, month = date_str.split(".")
        # On utilise 2024 par défaut, sera ajusté selon le relevé
        return datetime(2024, int(month), int(day))

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


def compute_checksum(date_op, libelle, montant, account_id) -> str:
    """Calcule un checksum unique pour éviter les doublons."""
    data = f"{date_op}|{libelle}|{montant}|{account_id}"
    return hashlib.md5(data.encode()).hexdigest()


def import_to_db(folder: str = "/app/releve"):
    """Import les relevés dans la base de données."""
    folder_path = Path(folder)
    pdf_files = list(folder_path.glob("*.pdf"))

    print(f"📂 Import depuis: {folder}")
    print(f"   {len(pdf_files)} fichiers PDF trouvés")

    # Connexion BDD
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Récupérer les catégories
    cur.execute("SELECT id, code FROM finance_categories")
    categories_map = {row[1]: row[0] for row in cur.fetchall()}
    print(f"   {len(categories_map)} catégories en BDD")

    # Catégorie par défaut pour les non-catégorisées
    default_category_id = categories_map.get('frais_generaux', categories_map.get('achats_fournisseurs'))
    if not default_category_id:
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

            # Déterminer la période
            period_start = None
            period_end = None

            if stmt.period_start:
                period_start = parse_date(stmt.period_start, stmt.bank_type)
            if stmt.period_end:
                period_end = parse_date(stmt.period_end, stmt.bank_type)

            # Si pas de période, utiliser les dates des transactions
            if not period_start or not period_end:
                dates = []
                for tx in stmt.transactions:
                    d = parse_date(tx.date, stmt.bank_type)
                    if d:
                        dates.append(d)
                if dates:
                    period_start = min(dates)
                    period_end = max(dates)

            # Calculer le hash du fichier pour éviter doublons
            file_hash = hashlib.md5(pdf_file.read_bytes()).hexdigest()

            # Vérifier si déjà importé
            cur.execute("SELECT id FROM finance_bank_statements WHERE hash = %s", (file_hash,))
            existing = cur.fetchone()
            if existing:
                print(f"   ⏭ {pdf_file.name}: Déjà importé (id={existing[0]})")
                continue

            # Insérer le statement
            cur.execute("""
                INSERT INTO finance_bank_statements
                (account_id, period_start, period_end, source, file_name, hash)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (account_id, period_start, period_end, 'PDF_IMPORT', pdf_file.name, file_hash))
            statement_id = cur.fetchone()[0]
            total_statements += 1

            # Préparer les lignes
            lines_data = []
            transactions_data = []

            for tx in stmt.transactions:
                # Parser la date
                date_op = parse_date(tx.date, stmt.bank_type)
                date_val = parse_date(tx.valeur, stmt.bank_type) if tx.valeur else date_op

                if not date_op:
                    continue

                # Ajuster l'année selon la période
                if period_start and date_op.year == 2024:
                    if period_start.year != 2024:
                        # Ajuster l'année (attention au 29 février)
                        target_year = period_start.year if date_op.month >= period_start.month else (period_end.year if period_end else period_start.year)
                        try:
                            date_op = date_op.replace(year=target_year)
                        except ValueError:
                            # 29 février dans une année non bissextile
                            date_op = date_op.replace(day=28, year=target_year)

                # Calculer le montant (positif pour crédit, négatif pour débit)
                montant = Decimal("0")
                if tx.credit:
                    montant = tx.credit
                elif tx.debit:
                    montant = -tx.debit

                # Checksum pour éviter doublons
                checksum = compute_checksum(date_op, tx.libelle, montant, account_id)

                # Catégoriser
                cat_code, keywords = analyzer.categorize(tx.libelle)
                category_id = categories_map.get(cat_code) if cat_code else None

                lines_data.append((
                    statement_id,
                    date_op,
                    date_val,
                    tx.libelle,
                    float(montant),
                    None,  # balance_apres
                    None,  # ref_banque
                    None,  # raw_data
                    checksum,
                ))

                transactions_data.append((
                    account_id,
                    date_op,
                    tx.libelle,
                    float(montant),
                    category_id,
                    checksum,
                ))

            # Insérer les lignes de statement (sans ON CONFLICT car pas de contrainte UNIQUE)
            if lines_data:
                for line in lines_data:
                    statement_id_l, date_op_l, date_val_l, libelle_l, montant_l, balance_l, ref_l, raw_l, checksum_l = line
                    # Vérifier si le checksum existe déjà
                    cur.execute("SELECT id FROM finance_bank_statement_lines WHERE checksum = %s", (checksum_l,))
                    if cur.fetchone():
                        continue
                    cur.execute("""
                        INSERT INTO finance_bank_statement_lines
                        (statement_id, date_operation, date_valeur, libelle_banque, montant,
                         balance_apres, ref_banque, raw_data, checksum)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, line)
                    total_lines += 1

            # Insérer les transactions
            for tx_data in transactions_data:
                _, date_op, libelle, montant, category_id, checksum = tx_data

                # Déterminer la direction
                direction = 'IN' if montant > 0 else 'OUT'
                amount_abs = abs(montant)

                # Vérifier si existe déjà (même compte, date, montant, libellé)
                cur.execute("""
                    SELECT ft.id FROM finance_transactions ft
                    JOIN finance_transaction_lines ftl ON ftl.transaction_id = ft.id
                    WHERE ft.account_id = %s AND ft.date_operation = %s
                      AND ft.amount = %s AND ftl.description = %s
                    LIMIT 1
                """, (account_id, date_op, amount_abs, libelle))

                if cur.fetchone():
                    continue

                # Insérer transaction
                cur.execute("""
                    INSERT INTO finance_transactions
                    (entity_id, account_id, direction, source, date_operation, amount, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (entity_id, account_id, direction, 'IMPORT_PDF', date_op, amount_abs, 'CONFIRMED'))
                tx_id = cur.fetchone()[0]

                # Catégorie fallback si non trouvée (frais_generaux)
                if category_id is None:
                    category_id = default_category_id

                # Insérer ligne de transaction avec catégorie
                cur.execute("""
                    INSERT INTO finance_transaction_lines
                    (transaction_id, category_id, montant_ttc, description, position)
                    VALUES (%s, %s, %s, %s, %s)
                """, (tx_id, category_id, amount_abs, libelle, 1))

                total_transactions += 1

            conn.commit()
            print(f"   ✓ {pdf_file.name}: {len(stmt.transactions)} tx → compte {account_id}")

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
