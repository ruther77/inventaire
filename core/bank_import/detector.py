"""Bank type detection from PDF content.

Provides automatic detection of bank type from PDF text content,
with IBAN extraction and confidence scoring.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from .models import BankType


@dataclass
class DetectionResult:
    """Result of bank type detection.

    Attributes:
        bank_type: Detected bank type
        confidence: Confidence score (0.0-1.0)
        iban: Extracted IBAN if found
        account_number: Extracted account number if found
        bic: Extracted BIC/SWIFT code if found
        detection_scores: Per-bank detection scores for debugging
    """
    bank_type: BankType
    confidence: float
    iban: Optional[str] = None
    account_number: Optional[str] = None
    bic: Optional[str] = None
    detection_scores: dict = field(default_factory=dict)

    @property
    def is_confident(self) -> bool:
        """Return True if detection confidence is high enough."""
        return self.confidence >= 0.5

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "bank_type": self.bank_type.value,
            "confidence": round(self.confidence, 2),
            "iban": self.iban,
            "account_number": self.account_number,
            "bic": self.bic,
            "is_confident": self.is_confident,
        }


class BankDetector:
    """Detects bank type from PDF text content."""

    # LCL detection patterns
    LCL_PATTERNS = [
        re.compile(r"CREDIT\s*LYONNAIS", re.IGNORECASE),
        re.compile(r"LCL\s*(?:BANQUE|CREDIT)", re.IGNORECASE),
        re.compile(r"RELEVE\s+DE\s+COMPTE.*LCL", re.IGNORECASE),
        re.compile(r"www\.lcl\.fr", re.IGNORECASE),
        re.compile(r"ECRITURES\s+DE\s+LA\s+PERIODE", re.IGNORECASE),
        re.compile(r"ANCIEN\s+SOLDE\s+CREDITEUR", re.IGNORECASE),
    ]

    # BNP detection patterns
    BNP_PATTERNS = [
        re.compile(r"BNP\s*PARIBAS", re.IGNORECASE),
        re.compile(r"mabanque\.bnpparibas", re.IGNORECASE),
        re.compile(r"www\.bnpparibas", re.IGNORECASE),
        re.compile(r"BANQUE\s+NATIONALE\s+DE\s+PARIS", re.IGNORECASE),
        re.compile(r"RELEVE\s+DE\s+COMPTE\s+CHEQUES", re.IGNORECASE),  # BNP header
        re.compile(r"BNPAFRPP", re.IGNORECASE),  # BNP BIC code
    ]

    # SumUp detection patterns (more specific to avoid false positives from transaction labels)
    SUMUP_PATTERNS = [
        re.compile(r"sumup\s+limited", re.IGNORECASE),
        re.compile(r"support\.sumup\.com", re.IGNORECASE),
        re.compile(r"Relevé\s+de\s+compte\s+SumUp", re.IGNORECASE),
        re.compile(r"Historique\s+des\s+transactions\s+SumUp", re.IGNORECASE),
        re.compile(r"Encaissements\s+par\s+carte", re.IGNORECASE),
        re.compile(r"Identifiant\s+marchand", re.IGNORECASE),
        re.compile(r"IE\d{2}SUMU\d+", re.IGNORECASE),  # SumUp IBAN pattern
        re.compile(r"Paiement\s+POS", re.IGNORECASE),
        re.compile(r"Paiement\s+entrant\s+SumUp", re.IGNORECASE),
    ]

    # Crédit Agricole detection patterns (for future extension)
    CREDIT_AGRICOLE_PATTERNS = [
        re.compile(r"CREDIT\s+AGRICOLE", re.IGNORECASE),
        re.compile(r"www\.credit-agricole\.fr", re.IGNORECASE),
        re.compile(r"ca-[\w-]+\.fr", re.IGNORECASE),  # Regional CA websites
        re.compile(r"AGRIFRPP", re.IGNORECASE),  # CA BIC code
        re.compile(r"Caisse\s+Régionale", re.IGNORECASE),
        re.compile(r"Relevé\s+de\s+compte.*Crédit\s+Agricole", re.IGNORECASE),
    ]

    # Société Générale detection patterns (for future extension)
    SOCIETE_GENERALE_PATTERNS = [
        re.compile(r"SOCIETE\s+GENERALE", re.IGNORECASE),
        re.compile(r"www\.particuliers\.societegenerale\.fr", re.IGNORECASE),
        re.compile(r"SOGEFRPP", re.IGNORECASE),  # SG BIC code
        re.compile(r"Relevé\s+de\s+compte.*Société\s+Générale", re.IGNORECASE),
        re.compile(r"SG\s+BANQUE", re.IGNORECASE),
    ]

    # Account number patterns per bank
    LCL_ACCOUNT_RE = re.compile(r"Compte\s*:?\s*(\d{5,})", re.IGNORECASE)
    BNP_ACCOUNT_RE = re.compile(r"N[°o]\s*(?:de\s*)?compte\s*:?\s*(\d{5,})", re.IGNORECASE)

    # IBAN patterns (French IBANs start with FR)
    # Standard format: FR76 1234 5678 9012 3456 7890 123
    IBAN_RE = re.compile(
        r"(?:IBAN\s*:?\s*)?"
        r"(FR\d{2}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{3})",
        re.IGNORECASE
    )
    # Also match compact format without spaces
    IBAN_COMPACT_RE = re.compile(
        r"(FR\d{2}\d{10,21})",
        re.IGNORECASE
    )
    # SumUp Irish IBAN
    SUMUP_IBAN_RE = re.compile(
        r"(IE\d{2}SUMU\d+)",
        re.IGNORECASE
    )

    # BIC/SWIFT patterns
    BIC_RE = re.compile(
        r"BIC\s*:?\s*([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)",
        re.IGNORECASE
    )

    # Known BIC codes for French banks
    BANK_BIC_CODES = {
        "CRLYFRPP": BankType.LCL,      # LCL
        "BNPAFRPP": BankType.BNP,      # BNP Paribas
        "AGRIFRPP": BankType.CREDIT_AGRICOLE,  # Crédit Agricole
        "SOGEFRPP": BankType.SOCIETE_GENERALE,  # Société Générale
    }

    def __init__(self):
        self._detection_scores: dict[BankType, int] = {}

    def detect(self, text: str) -> Tuple[BankType, float]:
        """Detect bank type from text content.

        Args:
            text: Full text content of the PDF

        Returns:
            Tuple of (BankType, confidence score 0.0-1.0)
        """
        self._detection_scores = {
            BankType.LCL: 0,
            BankType.BNP: 0,
            BankType.SUMUP: 0,
            BankType.CREDIT_AGRICOLE: 0,
            BankType.SOCIETE_GENERALE: 0,
        }

        # Count pattern matches
        for pattern in self.LCL_PATTERNS:
            if pattern.search(text):
                self._detection_scores[BankType.LCL] += 1

        for pattern in self.BNP_PATTERNS:
            if pattern.search(text):
                self._detection_scores[BankType.BNP] += 1

        for pattern in self.SUMUP_PATTERNS:
            if pattern.search(text):
                self._detection_scores[BankType.SUMUP] += 1

        for pattern in self.CREDIT_AGRICOLE_PATTERNS:
            if pattern.search(text):
                self._detection_scores[BankType.CREDIT_AGRICOLE] += 1

        for pattern in self.SOCIETE_GENERALE_PATTERNS:
            if pattern.search(text):
                self._detection_scores[BankType.SOCIETE_GENERALE] += 1

        # Find best match
        best_bank = BankType.UNKNOWN
        best_score = 0

        for bank, score in self._detection_scores.items():
            if score > best_score:
                best_score = score
                best_bank = bank

        # Calculate confidence (0.0-1.0)
        max_patterns = max(
            len(self.LCL_PATTERNS),
            len(self.BNP_PATTERNS),
            len(self.SUMUP_PATTERNS),
            len(self.CREDIT_AGRICOLE_PATTERNS),
            len(self.SOCIETE_GENERALE_PATTERNS),
        )
        confidence = best_score / max_patterns if max_patterns > 0 else 0.0

        return best_bank, min(confidence, 1.0)

    def extract_account_number(self, text: str, bank_type: BankType) -> Optional[str]:
        """Extract account number based on bank type.

        Args:
            text: PDF text content
            bank_type: Detected bank type

        Returns:
            Account number string or None
        """
        if bank_type == BankType.LCL:
            match = self.LCL_ACCOUNT_RE.search(text)
            if match:
                return match.group(1)

        elif bank_type == BankType.BNP:
            match = self.BNP_ACCOUNT_RE.search(text)
            if match:
                return match.group(1)

        return None

    def get_detection_details(self) -> dict[str, int]:
        """Get detailed detection scores for debugging."""
        return {bank.value: score for bank, score in self._detection_scores.items()}

    def detect_full(self, text: str) -> DetectionResult:
        """Perform full detection with IBAN and BIC extraction.

        This is the recommended method for complete bank detection.

        Args:
            text: Full text content of the PDF

        Returns:
            DetectionResult with bank type, confidence, and extracted identifiers
        """
        # Get basic detection
        bank_type, confidence = self.detect(text)

        # Extract IBAN
        iban = self.extract_iban(text, bank_type)

        # Extract BIC and use it to boost detection confidence
        bic = self.extract_bic(text)
        if bic:
            bic_bank = self.BANK_BIC_CODES.get(bic.upper())
            if bic_bank and bic_bank != BankType.UNKNOWN:
                if bic_bank == bank_type:
                    confidence = min(1.0, confidence + 0.2)  # Boost confidence
                else:
                    # BIC suggests different bank - use BIC as authoritative
                    bank_type = bic_bank
                    confidence = 0.9

        # Extract account number
        account_number = self.extract_account_number(text, bank_type)

        return DetectionResult(
            bank_type=bank_type,
            confidence=confidence,
            iban=iban,
            account_number=account_number,
            bic=bic,
            detection_scores=self.get_detection_details(),
        )

    def extract_iban(self, text: str, bank_type: Optional[BankType] = None) -> Optional[str]:
        """Extract IBAN from text.

        Args:
            text: PDF text content
            bank_type: Optional bank type for bank-specific patterns

        Returns:
            IBAN string (normalized without spaces) or None
        """
        # Try SumUp IBAN first if applicable
        if bank_type == BankType.SUMUP:
            match = self.SUMUP_IBAN_RE.search(text)
            if match:
                return match.group(1).replace(" ", "").upper()

        # Try standard French IBAN with spaces
        match = self.IBAN_RE.search(text)
        if match:
            return match.group(1).replace(" ", "").upper()

        # Try compact format
        match = self.IBAN_COMPACT_RE.search(text)
        if match:
            return match.group(1).upper()

        return None

    def extract_bic(self, text: str) -> Optional[str]:
        """Extract BIC/SWIFT code from text.

        Args:
            text: PDF text content

        Returns:
            BIC code or None
        """
        match = self.BIC_RE.search(text)
        if match:
            return match.group(1).upper()
        return None


def detect_bank_type(text: str) -> Tuple[BankType, float, Optional[str]]:
    """Enhanced bank type detection with confidence and IBAN.

    This function provides a richer detection result including:
    - Bank type
    - Confidence score (0.0-1.0)
    - IBAN if found

    Args:
        text: PDF text content

    Returns:
        Tuple of (bank_type, confidence, iban)

    Example:
        bank_type, confidence, iban = detect_bank_type(pdf_text)
        if confidence > 0.5:
            print(f"Detected: {bank_type.value}, IBAN: {iban}")

    Note:
        For full detection with BIC and account number, use detect_bank_full()
    """
    detector = BankDetector()
    result = detector.detect_full(text)
    return result.bank_type, result.confidence, result.iban


def detect_bank_type_simple(text: str) -> BankType:
    """Simple bank type detection (backward compatibility).

    Args:
        text: PDF text content

    Returns:
        Detected BankType

    Note:
        This is the legacy function. For new code, prefer detect_bank_type()
        or detect_bank_full() for more information.
    """
    detector = BankDetector()
    bank_type, _ = detector.detect(text)
    return bank_type


def detect_bank_full(text: str) -> DetectionResult:
    """Convenience function for full bank detection with IBAN extraction.

    Args:
        text: PDF text content

    Returns:
        DetectionResult with bank type, confidence, IBAN, BIC, and account number

    Example:
        result = detect_bank_full(pdf_text)
        if result.is_confident:
            print(f"Bank: {result.bank_type.value}, IBAN: {result.iban}")
    """
    detector = BankDetector()
    return detector.detect_full(text)
