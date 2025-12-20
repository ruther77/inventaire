"""Transaction categorization using keyword matching."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .categories import (
    CATEGORIES,
    KEYWORD_INDEX,
    CategoryDefinition,
    get_all_categories,
)
from .models import BankType, ParsedTransaction, TransactionDirection

logger = logging.getLogger(__name__)


@dataclass
class CategorizationResult:
    """Result of categorizing a transaction."""
    category_code: str
    category_name: str
    confidence: float  # 0.0 to 1.0
    matched_keyword: Optional[str] = None
    match_position: int = -1  # Position in libelle where keyword was found
    rule_id: Optional[int] = None  # ID of DB rule that matched


@dataclass
class DBRule:
    """A categorization rule from finance_rules table."""
    id: int
    name: str
    keywords: List[str]
    regex_pattern: Optional[str]
    category_id: int
    category_code: str
    category_name: str


class TransactionCategorizer:
    """Categorizes transactions based on keyword matching.

    Uses a priority-based matching system:
    1. DB rules from finance_rules (highest priority)
    2. Bank-specific keywords (high priority when bank_type is known)
    3. Exact phrase match (highest confidence)
    4. Word boundary match (high confidence)
    5. Substring match (medium confidence)
    6. Fallback to "à_categoriser" (zero confidence)

    Supports bank-specific keywords for LCL and BNP formats.
    """

    # Confidence levels
    CONF_DB_RULE = 0.98  # DB rules get highest confidence
    CONF_EXACT = 1.0
    CONF_BANK_SPECIFIC = 0.95  # Bank-specific keywords get high confidence
    CONF_WORD_BOUNDARY = 0.9
    CONF_SUBSTRING = 0.7
    CONF_FALLBACK = 0.0

    def __init__(self, bank_type: Optional[BankType] = None, load_db_rules: bool = True):
        """Initialize categorizer.

        Args:
            bank_type: Optional bank type for bank-specific keyword matching
            load_db_rules: If True, load rules from finance_rules table
        """
        self.bank_type = bank_type
        # Pre-compile regex patterns for each keyword
        self._patterns: Dict[str, re.Pattern] = {}
        self._db_rules: List[DBRule] = []
        self._db_rules_loaded = False

        self._build_patterns()
        if load_db_rules:
            self._load_db_rules()

    def _load_db_rules(self) -> None:
        """Load categorization rules from finance_rules table."""
        if self._db_rules_loaded:
            return

        try:
            from core.data_repository import query_df
            from sqlalchemy import text

            sql = text("""
                SELECT
                    fr.id,
                    fr.name,
                    fr.keywords,
                    fr.regex_pattern,
                    fr.category_id,
                    fc.code as category_code,
                    fc.name as category_name
                FROM finance_rules fr
                LEFT JOIN finance_categories fc ON fc.id = fr.category_id
                WHERE fr.is_active = true
                ORDER BY fr.id
            """)

            df = query_df(sql, {})

            for _, row in df.iterrows():
                keywords = row.get("keywords") or []
                if isinstance(keywords, str):
                    # Handle case where keywords is a string representation
                    keywords = [k.strip() for k in keywords.strip("{}").split(",") if k.strip()]

                rule = DBRule(
                    id=int(row["id"]),
                    name=str(row["name"] or ""),
                    keywords=[str(k).upper() for k in keywords],
                    regex_pattern=row.get("regex_pattern"),
                    category_id=int(row["category_id"]) if row.get("category_id") else 0,
                    category_code=str(row.get("category_code") or f"cat_{row['category_id']}"),
                    category_name=str(row.get("category_name") or row["name"]),
                )
                self._db_rules.append(rule)

                # Add keywords to patterns
                for kw in rule.keywords:
                    self._add_pattern(kw)

            self._db_rules_loaded = True
            logger.debug(f"Loaded {len(self._db_rules)} DB rules for categorization")

        except Exception as e:
            logger.warning(f"Could not load DB rules: {e}")
            self._db_rules_loaded = True  # Mark as loaded to avoid repeated attempts

    def _match_db_rules(self, libelle: str) -> Optional[CategorizationResult]:
        """Try to match against DB rules first.

        Args:
            libelle: Transaction description (uppercase)

        Returns:
            CategorizationResult if matched, None otherwise
        """
        for rule in self._db_rules:
            # Try regex pattern first if available
            if rule.regex_pattern:
                try:
                    if re.search(rule.regex_pattern, libelle, re.IGNORECASE):
                        return CategorizationResult(
                            category_code=rule.category_code,
                            category_name=rule.category_name,
                            confidence=self.CONF_DB_RULE,
                            matched_keyword=f"[REGEX] {rule.regex_pattern}",
                            rule_id=rule.id,
                        )
                except re.error:
                    pass

            # Try keywords
            for keyword in rule.keywords:
                if keyword in libelle:
                    return CategorizationResult(
                        category_code=rule.category_code,
                        category_name=rule.category_name,
                        confidence=self.CONF_DB_RULE,
                        matched_keyword=keyword,
                        match_position=libelle.find(keyword),
                        rule_id=rule.id,
                    )

        return None

    def _build_patterns(self) -> None:
        """Build regex patterns for word boundary matching."""
        # Build patterns for generic keywords
        for keyword in KEYWORD_INDEX.keys():
            self._add_pattern(keyword)

        # Build patterns for bank-specific keywords
        for cat in CATEGORIES.values():
            for keyword in cat.keywords_lcl:
                self._add_pattern(keyword)
            for keyword in cat.keywords_bnp:
                self._add_pattern(keyword)

    def _add_pattern(self, keyword: str) -> None:
        """Add a regex pattern for a keyword."""
        keyword_upper = keyword.upper()
        if keyword_upper not in self._patterns:
            escaped = re.escape(keyword_upper)
            pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
            self._patterns[keyword_upper] = pattern

    def _get_keywords_for_category(self, cat: CategoryDefinition) -> List[Tuple[str, float]]:
        """Get keywords for a category with their confidence bonus.

        Bank-specific keywords are checked first with higher confidence.

        Args:
            cat: Category definition

        Returns:
            List of (keyword, confidence_bonus) tuples
        """
        keywords: List[Tuple[str, float]] = []

        # Bank-specific keywords first (higher confidence)
        if self.bank_type == BankType.LCL and cat.keywords_lcl:
            for kw in cat.keywords_lcl:
                keywords.append((kw, 0.05))  # Bonus for bank-specific
        elif self.bank_type == BankType.BNP and cat.keywords_bnp:
            for kw in cat.keywords_bnp:
                keywords.append((kw, 0.05))  # Bonus for bank-specific

        # Generic keywords
        for kw in cat.keywords:
            keywords.append((kw, 0.0))

        return keywords

    def categorize(
        self,
        transaction: ParsedTransaction,
        bank_type: Optional[BankType] = None
    ) -> CategorizationResult:
        """Categorize a single transaction.

        Args:
            transaction: Transaction to categorize
            bank_type: Optional bank type override (uses instance bank_type if not provided)

        Returns:
            CategorizationResult with category and confidence
        """
        libelle = transaction.libelle.upper()
        direction = transaction.direction

        # 1. Try DB rules first (highest priority)
        db_result = self._match_db_rules(libelle)
        if db_result:
            return db_result

        # Use provided bank_type or instance bank_type
        effective_bank_type = bank_type or self.bank_type

        # Temporarily set bank_type for keyword selection
        original_bank_type = self.bank_type
        self.bank_type = effective_bank_type

        # 2. Get static categories sorted by priority
        categories = get_all_categories()

        best_match: Optional[CategorizationResult] = None
        best_score = -1

        for cat in categories:
            # Skip if direction doesn't match
            if cat.direction != "BOTH":
                expected_dir = TransactionDirection.IN if cat.direction == "IN" else TransactionDirection.OUT
                if direction != expected_dir:
                    continue

            # Try to match keywords (bank-specific first, then generic)
            for keyword, conf_bonus in self._get_keywords_for_category(cat):
                match_result = self._match_keyword(libelle, keyword)
                if match_result:
                    conf, pos = match_result
                    conf = min(1.0, conf + conf_bonus)  # Add bonus, cap at 1.0
                    # Score = confidence * priority
                    score = conf * (cat.priority + 1)

                    if score > best_score:
                        best_score = score
                        best_match = CategorizationResult(
                            category_code=cat.code,
                            category_name=cat.name,
                            confidence=conf,
                            matched_keyword=keyword,
                            match_position=pos,
                        )

        # Restore original bank_type
        self.bank_type = original_bank_type

        # Return best match or fallback
        if best_match:
            return best_match

        return CategorizationResult(
            category_code="a_categoriser",
            category_name="À Catégoriser",
            confidence=self.CONF_FALLBACK,
        )

    def _match_keyword(
        self,
        libelle: str,
        keyword: str
    ) -> Optional[Tuple[float, int]]:
        """Try to match a keyword in libelle.

        Args:
            libelle: Transaction description (uppercase)
            keyword: Keyword to match (uppercase in index)

        Returns:
            Tuple of (confidence, position) or None if no match
        """
        keyword_upper = keyword.upper()

        # 1. Exact phrase match (highest confidence)
        if libelle == keyword_upper:
            return (self.CONF_EXACT, 0)

        # 2. Word boundary match
        pattern = self._patterns.get(keyword_upper)
        if pattern:
            match = pattern.search(libelle)
            if match:
                return (self.CONF_WORD_BOUNDARY, match.start())

        # 3. Substring match (fallback)
        pos = libelle.find(keyword_upper)
        if pos >= 0:
            return (self.CONF_SUBSTRING, pos)

        return None

    def categorize_batch(
        self,
        transactions: List[ParsedTransaction],
        bank_type: Optional[BankType] = None
    ) -> List[CategorizationResult]:
        """Categorize multiple transactions.

        Args:
            transactions: List of transactions
            bank_type: Optional bank type for bank-specific matching

        Returns:
            List of CategorizationResult objects
        """
        return [self.categorize(t, bank_type) for t in transactions]

    def apply_categories(
        self,
        transactions: List[ParsedTransaction],
        bank_type: Optional[BankType] = None
    ) -> Tuple[int, int]:
        """Apply categories to transactions in-place.

        Args:
            transactions: List of transactions to categorize
            bank_type: Optional bank type for bank-specific matching

        Returns:
            Tuple of (categorized_count, uncategorized_count)
        """
        categorized = 0
        uncategorized = 0

        for txn in transactions:
            result = self.categorize(txn, bank_type)
            txn.category = result.category_code
            txn.category_confidence = result.confidence
            txn.matched_keyword = result.matched_keyword

            if result.category_code != "a_categoriser":
                categorized += 1
            else:
                uncategorized += 1

        return categorized, uncategorized


class SmartCategorizer(TransactionCategorizer):
    """Extended categorizer with learning capabilities.

    Can learn from user corrections and apply them to future transactions.
    """

    def __init__(self):
        super().__init__()
        # Custom rules learned from corrections
        self._custom_rules: Dict[str, str] = {}  # libelle_pattern -> category_code

    def add_custom_rule(self, libelle_pattern: str, category_code: str) -> None:
        """Add a custom categorization rule.

        Args:
            libelle_pattern: Pattern to match (will be uppercased)
            category_code: Category to assign
        """
        if category_code in CATEGORIES:
            self._custom_rules[libelle_pattern.upper()] = category_code

    def categorize(
        self,
        transaction: ParsedTransaction
    ) -> CategorizationResult:
        """Categorize with custom rules first.

        Args:
            transaction: Transaction to categorize

        Returns:
            CategorizationResult
        """
        libelle = transaction.libelle.upper()

        # Check custom rules first
        for pattern, cat_code in self._custom_rules.items():
            if pattern in libelle:
                cat = CATEGORIES.get(cat_code)
                if cat:
                    return CategorizationResult(
                        category_code=cat_code,
                        category_name=cat.name,
                        confidence=0.95,  # High but not 1.0
                        matched_keyword=f"[CUSTOM] {pattern}",
                    )

        # Fall back to standard categorization
        return super().categorize(transaction)


# =============================================================================
# FEEDBACK FUNCTIONS - For ML Learning Loop
# =============================================================================

def record_categorization_feedback(
    transaction_id: int,
    predicted_category_id: Optional[int],
    actual_category_id: int,
    confidence_score: Optional[float] = None,
    user_id: Optional[int] = None,
    correction_source: str = "manual"
) -> int:
    """Record a categorization correction for ML learning.

    This function stores user corrections when auto-categorization is wrong,
    enabling future ML model training.

    Args:
        transaction_id: ID of the transaction being corrected
        predicted_category_id: Original category suggested by system (or None)
        actual_category_id: Correct category chosen by user
        confidence_score: Original prediction confidence (0.0-1.0)
        user_id: ID of user making the correction (optional)
        correction_source: Source of correction ('manual', 'rule', 'bulk_action')

    Returns:
        ID of the created feedback record

    Example:
        >>> feedback_id = record_categorization_feedback(
        ...     transaction_id=12345,
        ...     predicted_category_id=5,  # "Alimentation"
        ...     actual_category_id=8,     # "Fournitures"
        ...     confidence_score=0.75,
        ...     correction_source="manual"
        ... )
    """
    from core.data_repository import exec_sql_return_id
    from sqlalchemy import text

    sql = text("""
        INSERT INTO finance_categorization_feedback
            (transaction_id, predicted_category_id, actual_category_id,
             confidence_score, user_id, correction_source)
        VALUES (:tx_id, :pred_id, :actual_id, :conf, :user_id, :source)
        RETURNING id
    """)

    return exec_sql_return_id(sql, {
        "tx_id": transaction_id,
        "pred_id": predicted_category_id,
        "actual_id": actual_category_id,
        "conf": confidence_score,
        "user_id": user_id,
        "source": correction_source,
    })


def get_feedback_stats() -> Dict:
    """Get statistics about categorization feedback.

    Returns:
        Dictionary with feedback statistics for monitoring.
    """
    from core.data_repository import query_df
    from sqlalchemy import text

    sql = text("""
        SELECT
            COUNT(*) as total_corrections,
            COUNT(DISTINCT transaction_id) as unique_transactions,
            COUNT(DISTINCT actual_category_id) as categories_corrected_to,
            COUNT(DISTINCT predicted_category_id) as categories_corrected_from,
            AVG(confidence_score) as avg_wrong_confidence,
            COUNT(CASE WHEN correction_source = 'manual' THEN 1 END) as manual_corrections,
            COUNT(CASE WHEN correction_source = 'rule' THEN 1 END) as rule_corrections,
            COUNT(CASE WHEN correction_source = 'bulk_action' THEN 1 END) as bulk_corrections
        FROM finance_categorization_feedback
    """)

    df = query_df(sql, {})
    if df.empty:
        return {
            "total_corrections": 0,
            "unique_transactions": 0,
            "categories_corrected_to": 0,
            "categories_corrected_from": 0,
            "avg_wrong_confidence": None,
            "manual_corrections": 0,
            "rule_corrections": 0,
            "bulk_corrections": 0,
        }

    row = df.iloc[0]
    return row.to_dict()


def get_common_corrections(limit: int = 20) -> List[Dict]:
    """Get the most common categorization corrections.

    Useful for identifying patterns to add as new rules.

    Args:
        limit: Maximum number of patterns to return

    Returns:
        List of dicts with correction patterns and counts
    """
    from core.data_repository import query_df
    from sqlalchemy import text

    sql = text("""
        SELECT
            fc_pred.code as predicted_code,
            fc_pred.name as predicted_name,
            fc_act.code as actual_code,
            fc_act.name as actual_name,
            COUNT(*) as correction_count,
            AVG(cf.confidence_score) as avg_confidence
        FROM finance_categorization_feedback cf
        LEFT JOIN finance_categories fc_pred ON fc_pred.id = cf.predicted_category_id
        JOIN finance_categories fc_act ON fc_act.id = cf.actual_category_id
        GROUP BY fc_pred.code, fc_pred.name, fc_act.code, fc_act.name
        ORDER BY COUNT(*) DESC
        LIMIT :limit
    """)

    df = query_df(sql, {"limit": limit})
    return df.to_dict(orient="records")


def categorize_transaction(libelle: str, direction: str = "OUT") -> str:
    """Convenience function to categorize a single transaction.

    Args:
        libelle: Transaction description
        direction: "IN" or "OUT"

    Returns:
        Category code
    """
    from .models import ParsedTransaction, TransactionDirection
    from datetime import date
    from decimal import Decimal

    txn = ParsedTransaction(
        date_operation=date.today(),
        date_valeur=date.today(),
        libelle=libelle,
        montant=Decimal("0"),
        direction=TransactionDirection.IN if direction == "IN" else TransactionDirection.OUT,
    )

    categorizer = TransactionCategorizer()
    result = categorizer.categorize(txn)
    return result.category_code
