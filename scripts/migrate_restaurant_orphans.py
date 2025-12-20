#!/usr/bin/env python3
"""
Migration Script: Phase 3 - Unification Restaurant Bank Statements

Objectif: Migrer les données orphelines de restaurant_bank_statements vers finance_bank_statement_lines
          et créer les finance_transactions correspondantes.

Usage:
    python scripts/migrate_restaurant_orphans.py --dry-run  # Analyse seulement
    python scripts/migrate_restaurant_orphans.py --execute  # Exécute la migration
    python scripts/migrate_restaurant_orphans.py --execute --limit 100  # Migre 100 lignes max
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_repository import get_engine, query_df, exec_sql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("migration_restaurant_orphans.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RestaurantOrphansMigrator:
    """Migre les orphelins de restaurant_bank_statements vers finance_*."""

    def __init__(self, engine: Engine):
        self.engine = engine
        self.stats = {
            "total_rbs": 0,
            "already_matched": 0,
            "orphans_found": 0,
            "migrated": 0,
            "with_depense_id": 0,
            "errors": 0,
        }

    def analyze_orphans(self) -> pd.DataFrame:
        """Identifie les orphelins dans restaurant_bank_statements."""
        logger.info("Analyse des orphelins dans restaurant_bank_statements...")

        sql = text("""
            SELECT
                rbs.id,
                rbs.tenant_id,
                rbs.account,
                rbs.date,
                rbs.libelle,
                rbs.categorie,
                rbs.montant,
                rbs.type,
                rbs.mois,
                rbs.source,
                rbs.depense_id,
                rbs.created_at,
                -- Vérifier si un match existe déjà
                CASE
                    WHEN fbsl.id IS NOT NULL THEN true
                    ELSE false
                END as has_match
            FROM restaurant_bank_statements rbs
            LEFT JOIN finance_bank_statement_lines fbsl
                ON rbs.date::date = fbsl.date_operation
                AND ABS(rbs.montant - fbsl.montant) < 0.01
            ORDER BY rbs.date DESC, rbs.id
        """)

        df = query_df(sql)

        self.stats["total_rbs"] = len(df)
        self.stats["already_matched"] = len(df[df["has_match"] == True])
        self.stats["orphans_found"] = len(df[df["has_match"] == False])
        self.stats["with_depense_id"] = len(df[(df["has_match"] == False) & (df["depense_id"].notna())])

        logger.info(f"Total restaurant_bank_statements: {self.stats['total_rbs']}")
        logger.info(f"Déjà matchés avec finance_bank_statement_lines: {self.stats['already_matched']}")
        logger.info(f"Orphelins détectés: {self.stats['orphans_found']}")
        logger.info(f"Orphelins avec depense_id: {self.stats['with_depense_id']}")

        return df[df["has_match"] == False]

    def _get_or_create_account(self, account_label: str, entity_id: int = 2) -> int:
        """Récupère ou crée un compte finance_accounts."""
        # Chercher le compte existant
        sql_find = text("""
            SELECT id FROM finance_accounts
            WHERE entity_id = :entity_id AND label = :label
            LIMIT 1
        """)
        result = query_df(sql_find, {"entity_id": entity_id, "label": account_label})

        if not result.empty:
            return int(result.iloc[0]["id"])

        # Créer le compte
        sql_create = text("""
            INSERT INTO finance_accounts (entity_id, type, label, currency, is_active)
            VALUES (:entity_id, 'BANQUE', :label, 'EUR', true)
            RETURNING id
        """)
        result = query_df(sql_create, {"entity_id": entity_id, "label": account_label})
        account_id = int(result.iloc[0]["id"])
        logger.info(f"Compte créé: {account_label} (id={account_id})")
        return account_id

    def _get_or_create_statement(self, account_id: int, date_operation: str) -> int:
        """Récupère ou crée un finance_bank_statements pour regrouper les lignes."""
        # Utiliser le mois comme période
        period_start = pd.to_datetime(date_operation).replace(day=1).date()
        period_end = (period_start + pd.DateOffset(months=1) - pd.DateOffset(days=1)).date()

        sql_find = text("""
            SELECT id FROM finance_bank_statements
            WHERE account_id = :account_id
              AND period_start = :period_start
              AND period_end = :period_end
            LIMIT 1
        """)
        result = query_df(sql_find, {
            "account_id": account_id,
            "period_start": period_start,
            "period_end": period_end
        })

        if not result.empty:
            return int(result.iloc[0]["id"])

        # Créer le statement
        sql_create = text("""
            INSERT INTO finance_bank_statements (account_id, period_start, period_end, source, file_name)
            VALUES (:account_id, :period_start, :period_end, 'migration_rbs', 'restaurant_bank_statements')
            RETURNING id
        """)
        result = query_df(sql_create, {
            "account_id": account_id,
            "period_start": period_start,
            "period_end": period_end
        })
        return int(result.iloc[0]["id"])

    def _create_statement_line(self, row: pd.Series, statement_id: int) -> int:
        """Crée une ligne dans finance_bank_statement_lines."""
        sql = text("""
            INSERT INTO finance_bank_statement_lines (
                statement_id, date_operation, date_valeur, libelle_banque,
                montant, ref_banque, raw_data, checksum
            )
            VALUES (
                :statement_id, :date_operation, :date_valeur, :libelle_banque,
                :montant, :ref_banque, :raw_data, :checksum
            )
            RETURNING id
        """)

        # Calculer un checksum unique pour éviter les doublons
        import hashlib
        checksum_str = f"{row['account']}_{row['date']}_{row['montant']}_{row['libelle']}"
        checksum = hashlib.md5(checksum_str.encode()).hexdigest()

        raw_data = {
            "original_rbs_id": int(row["id"]),
            "tenant_id": int(row["tenant_id"]),
            "categorie": row["categorie"],
            "type": row["type"],
            "mois": row["mois"],
            "source": row["source"],
            "migrated_at": datetime.now().isoformat(),
        }

        result = query_df(sql, {
            "statement_id": statement_id,
            "date_operation": row["date"],
            "date_valeur": row["date"],
            "libelle_banque": row["libelle"],
            "montant": float(row["montant"]),
            "ref_banque": f"RBS-{row['id']}",
            "raw_data": str(raw_data),  # PostgreSQL JSONB
            "checksum": checksum,
        })

        return int(result.iloc[0]["id"])

    def _create_transaction(self, row: pd.Series, account_id: int, statement_line_id: int) -> int:
        """Crée une transaction dans finance_transactions."""
        direction = "IN" if float(row["montant"]) > 0 else "OUT"
        amount = abs(float(row["montant"]))

        sql = text("""
            INSERT INTO finance_transactions (
                entity_id, account_id, direction, source, date_operation, date_value,
                amount, currency, ref_externe, note, status
            )
            VALUES (
                :entity_id, :account_id, :direction, :source, :date_operation, :date_value,
                :amount, :currency, :ref_externe, :note, :status
            )
            RETURNING id
        """)

        # entity_id: Restaurant = 2 (convention du projet)
        entity_id = 2 if row["tenant_id"] == 2 else 1

        result = query_df(sql, {
            "entity_id": entity_id,
            "account_id": account_id,
            "direction": direction,
            "source": "migration_rbs",
            "date_operation": row["date"],
            "date_value": row["date"],
            "amount": amount,
            "currency": "EUR",
            "ref_externe": f"stmtline:{statement_line_id}",
            "note": f"Migré de RBS #{row['id']} - {row['libelle']}",
            "status": "CONFIRMED",
        })

        return int(result.iloc[0]["id"])

    def _create_reconciliation(self, statement_line_id: int, transaction_id: int):
        """Crée le lien dans finance_reconciliations."""
        sql = text("""
            INSERT INTO finance_reconciliations (
                statement_line_id, transaction_id, mode, reconciled_at, reconciled_by
            )
            VALUES (
                :statement_line_id, :transaction_id, 'AUTO', NOW(), 'migration_script'
            )
            ON CONFLICT DO NOTHING
        """)

        exec_sql(sql, {
            "statement_line_id": statement_line_id,
            "transaction_id": transaction_id,
        })

    def _link_depense(self, transaction_id: int, depense_id: int, original_rbs_id: int):
        """Crée le lien dans finance_transaction_expense_links."""
        sql = text("""
            INSERT INTO finance_transaction_expense_links (
                transaction_id, depense_id, migrated_from, original_rbs_id
            )
            VALUES (
                :transaction_id, :depense_id, 'restaurant_bank_statements', :original_rbs_id
            )
            ON CONFLICT DO NOTHING
        """)

        exec_sql(sql, {
            "transaction_id": transaction_id,
            "depense_id": depense_id,
            "original_rbs_id": original_rbs_id,
        })

    def migrate_orphan(self, row: pd.Series) -> bool:
        """Migre une ligne orpheline vers finance_*."""
        try:
            # 1. Obtenir ou créer le compte
            account_id = self._get_or_create_account(row["account"], entity_id=2)

            # 2. Obtenir ou créer le statement
            statement_id = self._get_or_create_statement(account_id, row["date"])

            # 3. Créer la ligne de statement
            statement_line_id = self._create_statement_line(row, statement_id)
            logger.debug(f"Statement line créée: {statement_line_id}")

            # 4. Créer la transaction
            transaction_id = self._create_transaction(row, account_id, statement_line_id)
            logger.debug(f"Transaction créée: {transaction_id}")

            # 5. Créer la réconciliation
            self._create_reconciliation(statement_line_id, transaction_id)

            # 6. Si depense_id existe, créer le lien
            if pd.notna(row["depense_id"]):
                depense_id = int(row["depense_id"])
                self._link_depense(transaction_id, depense_id, int(row["id"]))
                logger.debug(f"Lien depense_id créé: {depense_id}")

            logger.info(f"✓ Migré RBS #{row['id']}: {row['date']} - {row['libelle']} ({row['montant']}€)")
            return True

        except Exception as e:
            logger.error(f"✗ Erreur migration RBS #{row['id']}: {e}")
            return False

    def execute_migration(self, orphans_df: pd.DataFrame, limit: int | None = None):
        """Exécute la migration des orphelins."""
        if orphans_df.empty:
            logger.info("Aucun orphelin à migrer.")
            return

        if limit:
            orphans_df = orphans_df.head(limit)
            logger.info(f"Migration limitée à {limit} lignes")

        logger.info(f"Début migration de {len(orphans_df)} orphelins...")

        with self.engine.begin() as conn:
            for idx, row in orphans_df.iterrows():
                if self.migrate_orphan(row):
                    self.stats["migrated"] += 1
                else:
                    self.stats["errors"] += 1

        logger.info("=" * 80)
        logger.info("RÉSUMÉ DE MIGRATION")
        logger.info("=" * 80)
        logger.info(f"Total orphelins: {self.stats['orphans_found']}")
        logger.info(f"Migrés avec succès: {self.stats['migrated']}")
        logger.info(f"Erreurs: {self.stats['errors']}")
        logger.info(f"Liens depense_id créés: {self.stats['with_depense_id']}")
        logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Migration des orphelins restaurant_bank_statements")
    parser.add_argument("--dry-run", action="store_true", help="Analyse seulement, pas d'écriture")
    parser.add_argument("--execute", action="store_true", help="Exécute la migration")
    parser.add_argument("--limit", type=int, help="Limite le nombre de lignes à migrer")

    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        parser.print_help()
        logger.error("Vous devez spécifier --dry-run ou --execute")
        sys.exit(1)

    engine = get_engine()
    migrator = RestaurantOrphansMigrator(engine)

    # Analyse
    orphans_df = migrator.analyze_orphans()

    if args.dry_run:
        logger.info("Mode DRY-RUN: Aucune migration effectuée")
        logger.info(f"Aperçu des orphelins à migrer:")
        print(orphans_df.head(10).to_string())
        return

    # Exécution
    if args.execute:
        response = input(f"\nVoulez-vous migrer {len(orphans_df)} orphelins? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Migration annulée")
            sys.exit(0)

        migrator.execute_migration(orphans_df, limit=args.limit)


if __name__ == "__main__":
    main()
