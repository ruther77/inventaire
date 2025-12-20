"""Transaction deduplication for bank imports."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional, Set, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .models import ParsedTransaction, TransactionDirection


@dataclass
class DeduplicationResult:
    """Result of deduplication check."""
    total_transactions: int
    new_transactions: int
    duplicate_transactions: int
    new_list: List[ParsedTransaction]
    duplicate_list: List[ParsedTransaction]


class TransactionDeduplicator:
    """Handles transaction deduplication using checksums.

    Deduplication strategy:
    1. Generate SHA256 checksum from date + libelle + amount + direction
    2. Compare against existing checksums in database
    3. For within-batch duplicates: allow them (legitimate duplicates like commissions)
    4. Return lists of new and duplicate transactions

    IMPORTANT: Within-batch duplicates are ALLOWED because banks can have
    multiple identical transactions on the same day (e.g., multiple commission
    entries of 0.19€ for different card remittances).
    """

    def __init__(self, engine: Optional[Engine] = None, allow_batch_duplicates: bool = True):
        self.engine = engine
        self._existing_checksums: Set[str] = set()
        self._existing_checksum_counts: dict[str, int] = {}  # Track count per checksum
        self.allow_batch_duplicates = allow_batch_duplicates
        self.logger = logging.getLogger(__name__)

    def generate_checksum(self, txn: ParsedTransaction) -> str:
        """Generate a unique checksum for a transaction.

        Args:
            txn: Transaction to generate checksum for

        Returns:
            SHA256 hex digest (32 chars)
        """
        # Normalize data for consistent checksums
        data_parts = [
            txn.date_operation.isoformat(),
            txn.libelle.strip().upper(),
            str(txn.montant.quantize(Decimal("0.01"))),
            txn.direction.value,
        ]
        data = "|".join(data_parts)
        return hashlib.sha256(data.encode("utf-8")).hexdigest()[:32]

    def load_existing_checksums(
        self,
        account_id: int,
        period_start: date,
        period_end: date
    ) -> Set[str]:
        """Load existing checksums from database with occurrence counts.

        Args:
            account_id: Bank account ID
            period_start: Period start date
            period_end: Period end date

        Returns:
            Set of existing checksum strings
        """
        if not self.engine:
            return set()

        # Query checksums from a wider window to catch edge cases
        from datetime import timedelta
        start = period_start - timedelta(days=7)
        end = period_end + timedelta(days=7)

        # Get checksums WITH counts to handle legitimate duplicates
        query = text("""
            SELECT checksum, COUNT(*) as cnt
            FROM finance_bank_statement_lines
            WHERE account_id = :account_id
              AND date_operation BETWEEN :start AND :end
              AND checksum IS NOT NULL
            GROUP BY checksum
        """)

        with self.engine.connect() as conn:
            result = conn.execute(
                query,
                {"account_id": account_id, "start": start, "end": end}
            )
            self._existing_checksum_counts = {}
            for row in result:
                if row[0]:
                    self._existing_checksum_counts[row[0]] = row[1]
            self._existing_checksums = set(self._existing_checksum_counts.keys())

        return self._existing_checksums

    def check_duplicate(self, txn: ParsedTransaction) -> bool:
        """Check if a transaction is a duplicate.

        Args:
            txn: Transaction to check

        Returns:
            True if duplicate (already exists)
        """
        checksum = txn.checksum or self.generate_checksum(txn)
        return checksum in self._existing_checksums

    def deduplicate(
        self,
        transactions: List[ParsedTransaction],
        account_id: Optional[int] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
    ) -> DeduplicationResult:
        """Deduplicate a list of transactions.

        Deduplication logic:
        - For DB duplicates: only reject if batch count exceeds expected
        - For batch duplicates: ALLOW (legitimate duplicates like commissions)

        This handles the case where a bank statement has multiple identical
        commission entries on the same day (e.g., two 0.19€ commissions).

        Args:
            transactions: Transactions to deduplicate
            account_id: Optional account ID for DB lookup
            period_start: Period start for DB lookup
            period_end: Period end for DB lookup

        Returns:
            DeduplicationResult with new and duplicate lists
        """
        from collections import Counter

        self.logger.debug(
            f"Starting deduplication: {len(transactions)} transactions, "
            f"account_id={account_id}, period={period_start} to {period_end}"
        )

        # Load existing checksums if we have DB connection and parameters
        if self.engine and account_id and period_start and period_end:
            self.load_existing_checksums(account_id, period_start, period_end)
            self.logger.debug(
                f"Loaded {len(self._existing_checksums)} existing checksums from DB "
                f"(some with multiple occurrences)"
            )

        new_transactions: List[ParsedTransaction] = []
        duplicate_transactions: List[ParsedTransaction] = []

        # Count occurrences of each checksum in the current batch
        batch_checksum_counts: Counter = Counter()

        for txn in transactions:
            # Ensure checksum is set
            if not txn.checksum:
                txn.checksum = self.generate_checksum(txn)

            batch_checksum_counts[txn.checksum] += 1
            current_batch_count = batch_checksum_counts[txn.checksum]
            existing_db_count = self._existing_checksum_counts.get(txn.checksum, 0)

            # Only reject if this occurrence number already exists in DB
            # Example: if DB has 2 entries with this checksum, and this is the 3rd
            # occurrence in batch, allow it. If it's the 1st or 2nd, reject.
            if current_batch_count <= existing_db_count:
                self.logger.debug(
                    f"Duplicate (DB, occurrence {current_batch_count}/{existing_db_count}): "
                    f"{txn.date_operation} {txn.libelle[:30]} {txn.montant}"
                )
                duplicate_transactions.append(txn)
            else:
                self.logger.debug(
                    f"New transaction (occurrence {current_batch_count}, DB has {existing_db_count}): "
                    f"{txn.date_operation} {txn.libelle[:30]} {txn.montant}"
                )
                new_transactions.append(txn)

        self.logger.debug(
            f"Deduplication complete: {len(new_transactions)} new, "
            f"{len(duplicate_transactions)} duplicates"
        )

        return DeduplicationResult(
            total_transactions=len(transactions),
            new_transactions=len(new_transactions),
            duplicate_transactions=len(duplicate_transactions),
            new_list=new_transactions,
            duplicate_list=duplicate_transactions,
        )

    def deduplicate_in_memory(
        self,
        transactions: List[ParsedTransaction],
        existing_checksums: Set[str]
    ) -> DeduplicationResult:
        """Deduplicate against a provided set of checksums.

        Args:
            transactions: Transactions to deduplicate
            existing_checksums: Set of existing checksums

        Returns:
            DeduplicationResult
        """
        self._existing_checksums = existing_checksums
        return self.deduplicate(transactions)


class SmartDeduplicator(TransactionDeduplicator):
    """Extended deduplicator with fuzzy matching capabilities.

    Can detect near-duplicates based on:
    - Same date + similar amount
    - Similar libelle (Levenshtein distance)
    """

    # Threshold for amount similarity (percentage)
    AMOUNT_TOLERANCE_PERCENT = Decimal("0.01")  # 1%

    def __init__(self, engine: Optional[Engine] = None):
        super().__init__(engine)
        self._existing_transactions: List[Tuple[date, str, Decimal]] = []

    def load_existing_transactions(
        self,
        account_id: int,
        period_start: date,
        period_end: date
    ) -> None:
        """Load existing transactions for fuzzy matching.

        Args:
            account_id: Bank account ID
            period_start: Period start date
            period_end: Period end date
        """
        if not self.engine:
            return

        from datetime import timedelta
        start = period_start - timedelta(days=7)
        end = period_end + timedelta(days=7)

        query = text("""
            SELECT date_operation, libelle_banque, montant
            FROM finance_bank_statement_lines
            WHERE account_id = :account_id
              AND date_operation BETWEEN :start AND :end
        """)

        with self.engine.connect() as conn:
            result = conn.execute(
                query,
                {"account_id": account_id, "start": start, "end": end}
            )
            self._existing_transactions = [
                (row[0], row[1] or "", Decimal(str(row[2])))
                for row in result
            ]

    def is_near_duplicate(self, txn: ParsedTransaction) -> bool:
        """Check if transaction is a near-duplicate.

        Args:
            txn: Transaction to check

        Returns:
            True if likely duplicate
        """
        for existing_date, existing_lib, existing_amt in self._existing_transactions:
            # Same date
            if txn.date_operation == existing_date:
                # Similar amount (within tolerance)
                if existing_amt != 0:
                    diff_pct = abs(txn.montant - existing_amt) / abs(existing_amt)
                    if diff_pct <= self.AMOUNT_TOLERANCE_PERCENT:
                        # Similar libelle (basic check)
                        if self._similar_libelle(txn.libelle, existing_lib):
                            return True
        return False

    def _similar_libelle(self, lib1: str, lib2: str) -> bool:
        """Check if two libelles are similar.

        Args:
            lib1: First libelle
            lib2: Second libelle

        Returns:
            True if similar
        """
        # Normalize
        norm1 = lib1.upper().strip()
        norm2 = lib2.upper().strip()

        # Exact match
        if norm1 == norm2:
            return True

        # One contains the other
        if norm1 in norm2 or norm2 in norm1:
            return True

        # First 20 characters match
        if len(norm1) >= 20 and len(norm2) >= 20:
            if norm1[:20] == norm2[:20]:
                return True

        return False


def deduplicate_transactions(
    transactions: List[ParsedTransaction],
    existing_checksums: Set[str]
) -> Tuple[List[ParsedTransaction], List[ParsedTransaction]]:
    """Convenience function for deduplication.

    Args:
        transactions: Transactions to check
        existing_checksums: Known checksums

    Returns:
        Tuple of (new_transactions, duplicate_transactions)
    """
    deduplicator = TransactionDeduplicator()
    result = deduplicator.deduplicate_in_memory(transactions, existing_checksums)
    return result.new_list, result.duplicate_list
