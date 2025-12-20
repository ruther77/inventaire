"""Balance validation for bank statements."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from .models import BalanceType, ParsedStatement, ParsedTransaction, StatementBalance, TransactionDirection


@dataclass
class ValidationResult:
    """Result of balance validation."""
    is_valid: bool
    expected_credits: Decimal
    calculated_credits: Decimal
    expected_debits: Decimal
    calculated_debits: Decimal
    credit_difference: Decimal
    debit_difference: Decimal
    opening_balance: Optional[Decimal]
    closing_balance: Optional[Decimal]
    calculated_closing: Optional[Decimal]
    balance_equation_valid: bool
    errors: List[str]
    warnings: List[str]

    @property
    def total_difference(self) -> Decimal:
        """Total absolute difference."""
        return abs(self.credit_difference) + abs(self.debit_difference)


class BalanceValidator:
    """Validates statement balance against parsed transactions.

    Validation checks:
    1. Sum of credits matches expected total credits
    2. Sum of debits matches expected total debits
    3. Opening + credits - debits = closing (if all balances available)
    """

    # Tolerance for rounding differences
    TOLERANCE = Decimal("0.02")

    def validate(self, statement: ParsedStatement) -> ValidationResult:
        """Validate statement balance.

        Args:
            statement: Parsed statement with transactions and balance

        Returns:
            ValidationResult with detailed comparison
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Calculate totals from transactions
        calc_credits = Decimal("0")
        calc_debits = Decimal("0")

        for txn in statement.transactions:
            if txn.direction == TransactionDirection.IN:
                calc_credits += txn.montant
            else:
                calc_debits += txn.montant

        # Get expected values from balance
        exp_credits = Decimal("0")
        exp_debits = Decimal("0")
        opening = None
        closing = None
        calc_closing = None
        balance_equation_valid = False

        if statement.balance:
            # Use the balance object's actual transaction values
            # These automatically account for ANCIEN SOLDE type (CREDITEUR/DEBITEUR)
            # - If CREDITEUR: ANCIEN SOLDE is in total_credits, subtract it
            # - If DEBITEUR: ANCIEN SOLDE is in total_debits, subtract it
            exp_credits = statement.balance.actual_transaction_credits
            exp_debits = statement.balance.actual_transaction_debits
            opening = statement.balance.opening_balance
            closing = statement.balance.closing_balance

            # Check balance equation: opening + credits - debits = closing
            # For LCL, we need to use the actual transaction totals
            # IMPORTANT: opening_balance is always positive, but for DEBITEUR it represents
            # a negative value (overdraft), so we need to negate it
            if opening is not None and closing is not None:
                signed_opening = opening
                if statement.balance.opening_balance_type == BalanceType.DEBITEUR:
                    signed_opening = -opening  # Overdraft = negative balance
                calc_closing = signed_opening + calc_credits - calc_debits
                if abs(calc_closing - closing) <= self.TOLERANCE:
                    balance_equation_valid = True
                else:
                    errors.append(
                        f"Balance equation failed: {signed_opening} + {calc_credits} - {calc_debits} = "
                        f"{calc_closing}, expected {closing}"
                    )

        # Calculate differences
        credit_diff = calc_credits - exp_credits
        debit_diff = calc_debits - exp_debits

        # Check credits
        if exp_credits > 0:
            if abs(credit_diff) > self.TOLERANCE:
                errors.append(
                    f"Credit mismatch: calculated {calc_credits}, expected {exp_credits}, "
                    f"diff {credit_diff}"
                )
            elif abs(credit_diff) > Decimal("0"):
                warnings.append(
                    f"Minor credit difference: {credit_diff} (within tolerance)"
                )

        # Check debits
        if exp_debits > 0:
            if abs(debit_diff) > self.TOLERANCE:
                errors.append(
                    f"Debit mismatch: calculated {calc_debits}, expected {exp_debits}, "
                    f"diff {debit_diff}"
                )
            elif abs(debit_diff) > Decimal("0"):
                warnings.append(
                    f"Minor debit difference: {debit_diff} (within tolerance)"
                )

        # Determine overall validity
        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            expected_credits=exp_credits,
            calculated_credits=calc_credits,
            expected_debits=exp_debits,
            calculated_debits=calc_debits,
            credit_difference=credit_diff,
            debit_difference=debit_diff,
            opening_balance=opening,
            closing_balance=closing,
            calculated_closing=calc_closing,
            balance_equation_valid=balance_equation_valid,
            errors=errors,
            warnings=warnings,
        )

    def validate_transaction(self, txn: ParsedTransaction) -> List[str]:
        """Validate a single transaction.

        Args:
            txn: Transaction to validate

        Returns:
            List of error messages (empty if valid)
        """
        errors: List[str] = []

        # Check amount is positive
        if txn.montant <= 0:
            errors.append(f"Invalid amount: {txn.montant}")

        # Check dates are reasonable
        if txn.date_valeur < txn.date_operation:
            # Value date before operation date is unusual but possible
            pass

        # Check libelle is not empty
        if not txn.libelle.strip():
            errors.append("Empty libelle")

        return errors

    def quick_check(self, statement: ParsedStatement) -> bool:
        """Quick validation check without detailed results.

        Args:
            statement: Statement to validate

        Returns:
            True if validation passes
        """
        result = self.validate(statement)
        return result.is_valid


def validate_statement(statement: ParsedStatement) -> ValidationResult:
    """Convenience function for validation.

    Args:
        statement: Statement to validate

    Returns:
        ValidationResult
    """
    validator = BalanceValidator()
    return validator.validate(statement)
