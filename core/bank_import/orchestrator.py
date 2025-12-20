"""Main orchestrator for bank statement import workflow."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .categorizer import TransactionCategorizer
from .deduplicator import TransactionDeduplicator
from .detector import BankDetector
from .extractor import PDFExtractor
from .models import (
    BankType,
    ImportResult,
    ImportStatus,
    ParsedStatement,
    ParsedTransaction,
    TransactionDirection,
)
from .parser import UnifiedBankParser, parse_sumup_statement
from .validator import BalanceValidator

logger = logging.getLogger(__name__)


class BankImportOrchestrator:
    """Orchestrates the complete bank statement import workflow.

    Workflow steps:
    1. Extract text from PDF
    2. Detect bank type
    3. Detect statement periods
    4. For each period:
       a. Extract balance information
       b. Parse transactions
       c. Validate balance
       d. Categorize transactions
       e. Deduplicate
       f. Insert into database
    5. Return summary result
    """

    # Maximum libelle length for database insertion
    MAX_LIBELLE_LENGTH = 500

    def __init__(
        self,
        engine: Optional[Engine] = None,
        dry_run: bool = False,
        strict_validation: bool = False,
    ):
        """Initialize orchestrator.

        Args:
            engine: SQLAlchemy engine for database operations
            dry_run: If True, don't insert into database
            strict_validation: If True, reject imports with balance validation errors
        """
        self.engine = engine
        self.dry_run = dry_run
        self.strict_validation = strict_validation

        # Initialize components
        self.extractor = PDFExtractor()
        self.detector = BankDetector()
        self.parser = UnifiedBankParser()
        self.categorizer = TransactionCategorizer()
        self.validator = BalanceValidator()
        self.deduplicator = TransactionDeduplicator(engine)

    def import_pdf(
        self,
        pdf_path: Path,
        entity_code: str,
        account_label: str,
        account_id_override: Optional[int] = None,
    ) -> ImportResult:
        """Import a bank statement PDF.

        Args:
            pdf_path: Path to PDF file
            entity_code: Entity code (e.g., "RESTO", "EPICERIE")
            account_label: Account label for identification
            account_id_override: Optional explicit account ID

        Returns:
            ImportResult with summary and details
        """
        result = ImportResult(
            status=ImportStatus.SUCCESS,
            started_at=datetime.now(),
        )

        try:
            # Step 1: Extract PDF
            logger.info(f"Extracting PDF: {pdf_path}")
            extraction = self.extractor.extract(pdf_path)

            if not extraction.periods:
                result.status = ImportStatus.FAILED
                result.add_error("No statement periods detected in PDF")
                return self._finalize_result(result)

            result.statements_detected = len(extraction.periods)
            logger.info(f"Detected {len(extraction.periods)} period(s)")

            # Step 2: Detect bank type
            bank_type, confidence = self.detector.detect(extraction.full_text)
            if bank_type == BankType.UNKNOWN:
                result.add_warning("Could not detect bank type, using LCL as default")
                bank_type = BankType.LCL
            else:
                logger.info(f"Detected bank: {bank_type.value} (confidence: {confidence:.2f})")

            # Get account ID
            if self.engine and not self.dry_run:
                account_id = account_id_override or self._ensure_account(
                    entity_code, account_label
                )
            else:
                account_id = account_id_override or 0

            # Special handling for SumUp - different PDF format
            if bank_type == BankType.SUMUP:
                logger.info("Using SumUp-specific parser")
                return self._import_sumup(
                    extraction.full_text,
                    account_id,
                    pdf_path.name,
                    result
                )

            # Step 3: Process each period (for LCL/BNP)
            for period in extraction.periods:
                logger.info(f"Processing period: {period}")

                # Get lines for this period (using period_line_ranges for multi-period PDFs)
                period_lines = self.extractor.get_lines_for_period(
                    extraction.full_text.splitlines(),
                    period,
                    extraction.period_line_ranges
                )
                logger.debug(f"Period lines extracted: {len(period_lines)}")

                # Clean lines
                clean_lines = self.extractor.clean_lines(period_lines, bank_type)
                logger.debug(f"Clean lines after filtering: {len(clean_lines)}")

                # Parse statement
                statement = self.parser.parse(clean_lines, period, bank_type)
                logger.debug(f"Statement parsed: {len(statement.transactions)} transactions")

                # Process statement (pass bank_type for categorization)
                stmt_result = self._process_statement(
                    statement,
                    account_id,
                    pdf_path.name,
                    bank_type,
                )
                logger.debug(
                    f"Statement processed: {stmt_result['inserted']} inserted, "
                    f"{stmt_result['duplicates']} duplicates, "
                    f"{stmt_result['categorized']} categorized"
                )

                result.statement_results.append(stmt_result)

                # Aggregate totals
                if stmt_result.get("inserted", 0) > 0:
                    result.statements_imported += 1
                result.transactions_total += stmt_result.get("total", 0)
                result.transactions_inserted += stmt_result.get("inserted", 0)
                result.transactions_duplicates += stmt_result.get("duplicates", 0)
                result.transactions_categorized += stmt_result.get("categorized", 0)
                result.transactions_uncategorized += stmt_result.get("uncategorized", 0)
                result.total_credits += Decimal(str(stmt_result.get("total_in", 0)))
                result.total_debits += Decimal(str(stmt_result.get("total_out", 0)))

                if stmt_result.get("errors"):
                    result.errors.extend(stmt_result["errors"])
                if stmt_result.get("warnings"):
                    result.warnings.extend(stmt_result["warnings"])

            # Determine final status
            if result.transactions_inserted == 0 and result.transactions_total > 0:
                if result.transactions_duplicates == result.transactions_total:
                    result.status = ImportStatus.DUPLICATE
                else:
                    result.status = ImportStatus.FAILED
            elif result.errors:
                result.status = ImportStatus.PARTIAL

        except Exception as e:
            logger.exception(f"Import failed: {e}")
            result.status = ImportStatus.FAILED
            result.add_error(str(e))

        return self._finalize_result(result)

    def _process_statement(
        self,
        statement: ParsedStatement,
        account_id: int,
        source_file: str,
        bank_type: Optional[BankType] = None,
    ) -> dict:
        """Process a single parsed statement.

        Args:
            statement: Parsed statement
            account_id: Target account ID
            source_file: Source filename
            bank_type: Bank type for categorization

        Returns:
            Dict with processing results
        """
        result = {
            "period_start": statement.period.start_date.isoformat(),
            "period_end": statement.period.end_date.isoformat(),
            "total": 0,
            "inserted": 0,
            "duplicates": 0,
            "categorized": 0,
            "uncategorized": 0,
            "total_in": 0.0,
            "total_out": 0.0,
            "errors": [],
            "warnings": [],
        }

        transactions = statement.transactions
        result["total"] = len(transactions)

        if not transactions:
            result["warnings"].append("No transactions found in period")
            return result

        # Step 4: Validate balance
        validation = self.validator.validate(statement)
        if not validation.is_valid:
            result["errors"].extend(validation.errors)
            # In strict mode, stop processing if validation fails
            if self.strict_validation:
                logger.error(f"Strict validation failed for period {statement.period}. Skipping import.")
                result["warnings"].append("Import skipped due to strict validation failure")
                return result
        result["warnings"].extend(validation.warnings)

        # Step 5: Categorize transactions (using bank-specific keywords)
        cat_count, uncat_count = self.categorizer.apply_categories(transactions, bank_type)
        result["categorized"] = cat_count
        result["uncategorized"] = uncat_count

        # Step 6: Deduplicate
        dedup_result = self.deduplicator.deduplicate(
            transactions,
            account_id=account_id if not self.dry_run else None,
            period_start=statement.period.start_date,
            period_end=statement.period.end_date,
        )
        result["duplicates"] = dedup_result.duplicate_transactions
        new_transactions = dedup_result.new_list

        # Calculate totals
        for txn in transactions:
            if txn.direction == TransactionDirection.IN:
                result["total_in"] += float(txn.montant)
            else:
                result["total_out"] += float(txn.montant)

        # Step 7: Insert into database
        if not self.dry_run and self.engine and new_transactions:
            try:
                inserted = self._insert_transactions(
                    new_transactions,
                    account_id,
                    statement.period.start_date,
                    statement.period.end_date,
                    source_file,
                )
                result["inserted"] = inserted
            except Exception as e:
                result["errors"].append(f"Database insert failed: {e}")
        else:
            result["inserted"] = len(new_transactions)

        return result

    def _ensure_account(self, entity_code: str, account_label: str) -> int:
        """Ensure account exists and return its ID.

        Args:
            entity_code: Entity code
            account_label: Account label

        Returns:
            Account ID
        """
        with self.engine.begin() as conn:
            # Get entity ID
            entity_row = conn.execute(
                text("SELECT id FROM finance_entities WHERE lower(code) = lower(:code)"),
                {"code": entity_code}
            ).fetchone()

            if not entity_row:
                raise ValueError(f"Entity not found: {entity_code}")

            entity_id = int(entity_row.id)

            # Check if account exists
            acc_row = conn.execute(
                text("SELECT id FROM finance_accounts WHERE entity_id = :e AND label = :l"),
                {"e": entity_id, "l": account_label}
            ).fetchone()

            if acc_row:
                return int(acc_row.id)

            # Create account
            return int(conn.execute(
                text(
                    "INSERT INTO finance_accounts (entity_id, type, label, currency, is_active) "
                    "VALUES (:e, 'BANQUE', :l, 'EUR', TRUE) RETURNING id"
                ),
                {"e": entity_id, "l": account_label}
            ).scalar_one())

    def _insert_transactions(
        self,
        transactions: List[ParsedTransaction],
        account_id: int,
        period_start,
        period_end,
        source_file: str,
    ) -> int:
        """Insert transactions into database.

        Following the flowchart workflow:
        1. Insert raw lines into finance_bank_statement_lines
        2. Create corresponding finance_transactions (journal entries)
        3. Link them via finance_reconciliations (auto-reconciled)

        Args:
            transactions: Transactions to insert
            account_id: Target account ID
            period_start: Statement period start
            period_end: Statement period end
            source_file: Source filename

        Returns:
            Number of inserted transactions
        """
        with self.engine.begin() as conn:
            # Get entity_id from account
            entity_row = conn.execute(
                text("SELECT entity_id FROM finance_accounts WHERE id = :acc"),
                {"acc": account_id}
            ).fetchone()
            entity_id = int(entity_row.entity_id) if entity_row else 1

            # Check if statement exists
            stmt_row = conn.execute(
                text(
                    "SELECT id FROM finance_bank_statements "
                    "WHERE account_id = :acc AND period_start = :ps AND period_end = :pe"
                ),
                {"acc": account_id, "ps": period_start, "pe": period_end}
            ).fetchone()

            if stmt_row:
                statement_id = int(stmt_row.id)
                # Update source
                conn.execute(
                    text("UPDATE finance_bank_statements SET source = :src WHERE id = :id"),
                    {"src": source_file, "id": statement_id}
                )
            else:
                # Create statement
                statement_id = int(conn.execute(
                    text(
                        "INSERT INTO finance_bank_statements "
                        "(account_id, period_start, period_end, source, imported_at) "
                        "VALUES (:acc, :ps, :pe, :src, now()) RETURNING id"
                    ),
                    {"acc": account_id, "ps": period_start, "pe": period_end, "src": source_file}
                ).scalar_one())

            # Insert transactions following the complete workflow
            inserted = 0
            for txn in transactions:
                # Step 1: Insert raw bank statement line
                stmt_line_id = conn.execute(
                    text(
                        "INSERT INTO finance_bank_statement_lines "
                        "(statement_id, account_id, date_operation, date_valeur, "
                        "libelle_banque, montant, category, checksum) "
                        "VALUES (:sid, :acc, :do, :dv, :lib, :amt, :cat, :chk) "
                        "RETURNING id"
                    ),
                    {
                        "sid": statement_id,
                        "acc": account_id,
                        "do": txn.date_operation,
                        "dv": txn.date_valeur,
                        "lib": txn.libelle,
                        "amt": float(txn.montant_signe),
                        "cat": txn.category,
                        "chk": txn.checksum,
                    }
                ).scalar_one()

                # Step 2: Create finance_transaction (journal entry)
                # Direction: IN=credit (positive), OUT=debit (negative)
                direction = "IN" if txn.direction == TransactionDirection.IN else "OUT"
                ref_externe = f"stmtline:{stmt_line_id}"

                # Prepare libelle with length limit and logging
                libelle = txn.libelle if txn.libelle else None
                if libelle and len(libelle) > self.MAX_LIBELLE_LENGTH:
                    logger.warning(
                        f"Truncating libelle from {len(libelle)} to {self.MAX_LIBELLE_LENGTH} chars. "
                        f"Date: {txn.date_operation}, Amount: {txn.montant}, "
                        f"First 50 chars: {libelle[:50]}"
                    )
                    libelle = libelle[:self.MAX_LIBELLE_LENGTH]

                tx_id = conn.execute(
                    text(
                        "INSERT INTO finance_transactions "
                        "(entity_id, account_id, direction, source, date_operation, "
                        "date_value, amount, currency, ref_externe, label, note, tenant_id) "
                        "VALUES (:eid, :acc, :dir, 'BANK_IMPORT', :do, :dv, "
                        ":amt, 'EUR', :ref, :label, :note, NULL) "
                        "RETURNING id"
                    ),
                    {
                        "eid": entity_id,
                        "acc": account_id,
                        "dir": direction,
                        "do": txn.date_operation,
                        "dv": txn.date_valeur,
                        "amt": abs(float(txn.montant)),  # Always positive, direction indicates sign
                        "ref": ref_externe,
                        "label": libelle,
                        "note": f"Category: {txn.category}" if txn.category else None,
                    }
                ).scalar_one()

                # Step 3: Auto-link statement line to transaction (self-reconciliation)
                conn.execute(
                    text(
                        "INSERT INTO finance_reconciliations "
                        "(statement_line_id, transaction_id, status, confidence) "
                        "VALUES (:sl_id, :tx_id, 'AUTO', 1.0)"
                    ),
                    {"sl_id": stmt_line_id, "tx_id": tx_id}
                )

                inserted += 1

            return inserted

    def _import_sumup(
        self,
        full_text: str,
        account_id: int,
        source_file: str,
        result: ImportResult,
    ) -> ImportResult:
        """Import SumUp statement using specialized parser.

        SumUp statements have a different format than traditional bank statements.
        They are payment terminal reports with transaction history.

        Args:
            full_text: Full PDF text content
            account_id: Target account ID
            source_file: Source filename
            result: ImportResult to populate

        Returns:
            Populated ImportResult
        """
        try:
            # Parse SumUp statement
            statement = parse_sumup_statement(full_text)
            logger.info(f"SumUp parser found {len(statement.transactions)} transactions")

            result.statements_detected = 1

            if not statement.transactions:
                result.add_warning("No transactions found in SumUp statement")
                result.status = ImportStatus.PARTIAL
                return self._finalize_result(result)

            # Process the statement
            stmt_result = self._process_statement(
                statement,
                account_id,
                source_file,
                BankType.SUMUP,
            )

            result.statement_results.append(stmt_result)

            # Aggregate totals
            if stmt_result.get("inserted", 0) > 0:
                result.statements_imported = 1
            result.transactions_total = stmt_result.get("total", 0)
            result.transactions_inserted = stmt_result.get("inserted", 0)
            result.transactions_duplicates = stmt_result.get("duplicates", 0)
            result.transactions_categorized = stmt_result.get("categorized", 0)
            result.transactions_uncategorized = stmt_result.get("uncategorized", 0)
            result.total_credits = Decimal(str(stmt_result.get("total_in", 0)))
            result.total_debits = Decimal(str(stmt_result.get("total_out", 0)))

            if stmt_result.get("errors"):
                result.errors.extend(stmt_result["errors"])
            if stmt_result.get("warnings"):
                result.warnings.extend(stmt_result["warnings"])

            # Determine final status
            if result.transactions_inserted == 0 and result.transactions_total > 0:
                if result.transactions_duplicates == result.transactions_total:
                    result.status = ImportStatus.DUPLICATE
                else:
                    result.status = ImportStatus.FAILED
            elif result.errors:
                result.status = ImportStatus.PARTIAL

        except Exception as e:
            logger.exception(f"SumUp import failed: {e}")
            result.status = ImportStatus.FAILED
            result.add_error(f"SumUp import error: {str(e)}")

        return self._finalize_result(result)

    def _finalize_result(self, result: ImportResult) -> ImportResult:
        """Finalize import result.

        Args:
            result: Import result to finalize

        Returns:
            Finalized result
        """
        result.completed_at = datetime.now()
        return result

    def test_pdf(self, pdf_path: Path) -> dict:
        """Test PDF parsing without database operations.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict with test results including all parsed data
        """
        extraction = self.extractor.extract(pdf_path)
        bank_type, confidence = self.detector.detect(extraction.full_text)

        results = {
            "file": pdf_path.name,
            "bank_type": bank_type.value,
            "bank_confidence": confidence,
            "periods_detected": len(extraction.periods),
            "total_lines": extraction.line_count,
            "statements": [],
        }

        for period in extraction.periods:
            period_lines = self.extractor.get_lines_for_period(
                extraction.full_text.splitlines(),
                period,
                extraction.period_line_ranges
            )
            clean_lines = self.extractor.clean_lines(period_lines, bank_type)
            statement = self.parser.parse(clean_lines, period, bank_type)

            # Categorize (using bank-specific keywords)
            self.categorizer.apply_categories(statement.transactions, bank_type)

            # Validate
            validation = self.validator.validate(statement)

            stmt_data = {
                "period": str(period),
                "transaction_count": len(statement.transactions),
                "balance": {
                    "opening": float(statement.balance.opening_balance) if statement.balance else None,
                    "closing": float(statement.balance.closing_balance) if statement.balance else None,
                    "expected_debits": float(statement.balance.total_debits) if statement.balance else None,
                    "expected_credits": float(statement.balance.total_credits) if statement.balance else None,
                },
                "validation": {
                    "is_valid": validation.is_valid,
                    "calculated_credits": float(validation.calculated_credits),
                    "calculated_debits": float(validation.calculated_debits),
                    "credit_diff": float(validation.credit_difference),
                    "debit_diff": float(validation.debit_difference),
                    "errors": validation.errors,
                    "warnings": validation.warnings,
                },
                "categorization": {
                    "categorized": sum(1 for t in statement.transactions if t.category != "a_categoriser"),
                    "uncategorized": sum(1 for t in statement.transactions if t.category == "a_categoriser"),
                },
                "transactions": [
                    {
                        "date": t.date_operation.isoformat(),
                        "libelle": t.libelle[:50],
                        "montant": float(t.montant),
                        "direction": t.direction.value,
                        "category": t.category,
                        "confidence": t.category_confidence,
                    }
                    for t in statement.transactions  # All transactions for accurate summary
                ],
            }
            results["statements"].append(stmt_data)

        return results


def import_bank_pdf(
    pdf_path: Path,
    entity_code: str,
    account_label: str,
    dry_run: bool = False,
    strict_validation: bool = False,
) -> ImportResult:
    """Convenience function for importing a bank PDF.

    Args:
        pdf_path: Path to PDF
        entity_code: Entity code
        account_label: Account label
        dry_run: If True, don't insert into database
        strict_validation: If True, reject imports with balance validation errors

    Returns:
        ImportResult
    """
    from core.data_repository import get_engine

    engine = None if dry_run else get_engine()
    orchestrator = BankImportOrchestrator(
        engine=engine,
        dry_run=dry_run,
        strict_validation=strict_validation
    )
    return orchestrator.import_pdf(pdf_path, entity_code, account_label)
