"""Parseur unifié de relevés bancaires.

Fournit une interface commune pour analyser des relevés issus de différentes banques.
Prend en charge les formats LCL, BNP et SumUp.
"""

from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple, Protocol

from .models import (
    BalanceType,
    BankType,
    ColumnPositions,
    ParsedStatement,
    ParsedTransaction,
    StatementBalance,
    StatementPeriod,
    TransactionDirection,
)


# =============================================================================
# INTERFACE : protocole BankParser et classe abstraite
# =============================================================================

class BankParser(Protocol):
    """Interface pour les parseurs de relevés bancaires (Protocol pour le typage).

    Tous les parseurs spécifiques à une banque doivent implémenter ce protocole,
    ce qui facilite l'extension à de nouveaux formats.

    Usage :
        parser: BankParser = LCLParser()
        statement = parser.parse(lines, period)
    """

    @property
    def bank_type(self) -> BankType:
        """Retourne le type de banque géré par ce parseur."""
        ...

    def parse(
        self,
        lines: List[str],
        period: StatementPeriod,
    ) -> ParsedStatement:
        """Analyse les lignes du relevé en données structurées.

        Args:
            lines: Lignes de texte extraites du PDF
            period: Période du relevé pour l'inférence des dates

        Returns:
            ParsedStatement avec transactions et solde
        """
        ...

    def can_parse(self, text: str) -> bool:
        """Vérifie si ce parseur peut gérer le texte fourni.

        Args:
            text: Contenu texte complet du PDF

        Returns:
            True si ce parseur peut traiter le format
        """
        ...


class BaseBankParser(ABC):
    """Classe de base abstraite pour les parseurs de relevés bancaires.

    Fournit un contrat clair pour implémenter de nouveaux parseurs. Héritez de
    cette classe pour créer un parseur spécifique à une banque.

    Exemple :
        class CreditAgricoleParser(BaseBankParser):
            @property
            def bank_type(self) -> BankType:
                return BankType.CREDIT_AGRICOLE

            def parse(self, lines: List[str], period: StatementPeriod) -> ParsedStatement:
                # Logique de parsing spécifique
                ...

            def can_parse(self, text: str) -> bool:
                # Logique de détection
                return "CREDIT AGRICOLE" in text.upper()
    """

    @property
    @abstractmethod
    def bank_type(self) -> BankType:
        """Return the bank type this parser handles.

        Returns:
            BankType enum value for this parser
        """
        pass

    @abstractmethod
    def parse(
        self,
        lines: List[str],
        period: StatementPeriod,
    ) -> ParsedStatement:
        """Analyse les lignes du relevé en données structurées.

        Args:
            lines: Lignes de texte extraites du PDF
            period: Période du relevé pour l'inférence des dates

        Returns:
            ParsedStatement avec transactions et solde

        Raises:
            ValueError: si les lignes ne peuvent pas être parsées
        """
        pass

    @abstractmethod
    def can_parse(self, text: str) -> bool:
        """Vérifie si ce parseur peut gérer le texte fourni.

        Args:
            text: Contenu texte complet du PDF

        Returns:
            True si ce parseur peut traiter le format, False sinon

        Example:
            parser = LCLParser()
            if parser.can_parse(pdf_text):
                statement = parser.parse(lines, period)
        """
        pass


@dataclass
class ParserConfig:
    """Configuration for the parser."""
    min_line_length: int = 20
    amount_decimal_separator: str = ","
    amount_thousands_separator: str = " "
    date_format: str = "dd.mm"  # ou "dd/mm/yyyy"
    pad_lines: bool = True
    pad_length: int = 200


class UnifiedBankParser:
    """Analyse le texte des relevés bancaires en données structurées."""

    # Longueur maximale du libellé pour éviter une concaténation excessive
    MAX_LIBELLE_LENGTH = 500

    # Motifs de date
    DATE_SHORT_RE = re.compile(r"^(\d{2})[./](\d{2})$")  # 30.12
    DATE_FULL_RE = re.compile(r"^(\d{2})[./](\d{2})[./](\d{2,4})$")  # 30.12.23 ou 30.12.2023

    # Motifs de solde
    # Format LCL : ANCIEN SOLDE CREDITEUR/DEBITEUR suivi du montant
    # Capture le type (CREDITEUR/DEBITEUR) et le montant
    ANCIEN_SOLDE_RE = re.compile(
        r"ANCIEN\s+SOLDE\s+(CREDITEUR|DEBITEUR).*?([\d][\d\s]*,\d{2})",
        re.IGNORECASE
    )
    # Repli sans type (par défaut CREDITEUR)
    ANCIEN_SOLDE_SIMPLE_RE = re.compile(
        r"ANCIEN\s+SOLDE.*?([\d][\d\s]*,\d{2})",
        re.IGNORECASE
    )
    NOUVEAU_SOLDE_RE = re.compile(
        r"NOUVEAU\s+SOLDE\s+(CREDITEUR|DEBITEUR)?.*?([\d][\d\s]*,\d{2})",
        re.IGNORECASE
    )
    # Repli sans type
    NOUVEAU_SOLDE_SIMPLE_RE = re.compile(
        r"NOUVEAU\s+SOLDE.*?([\d][\d\s]*,\d{2})",
        re.IGNORECASE
    )
    TOTAL_DEBIT_RE = re.compile(
        r"TOTAL\s+(?:DES\s+)?DEBITS?\s*:?\s*([\d][\d\s]*,\d{2})",
        re.IGNORECASE
    )
    TOTAL_CREDIT_RE = re.compile(
        r"TOTAL\s+(?:DES\s+)?CREDITS?\s*:?\s*([\d][\d\s]*,\d{2})",
        re.IGNORECASE
    )
    # TOTAUX avec deux montants (débit puis crédit) - capture chaque montant séparément
    TOTAUX_RE = re.compile(
        r"TOTAUX\s+([\d][\d\s]*,\d{2})\s+([\d][\d\s]*,\d{2})",
        re.IGNORECASE
    )

    # Motifs de solde spécifiques BNP
    # Ouverture BNP : "SOLDE CREDITEUR AU dd.mm.yyyy ... montant"
    BNP_SOLDE_CREDITEUR_RE = re.compile(
        r"SOLDE\s+CREDITEUR\s+AU\s+\d{2}\.\d{2}\.\d{4}.*?([\d][\d\s]*,\d{2})",
        re.IGNORECASE
    )
    # Solde de clôture BNP : même motif mais on prend la dernière occurrence
    # Totaux BNP : "TOTAL DES OPERATIONS ... montant_debit ... montant_credit"
    BNP_TOTAL_OPERATIONS_RE = re.compile(
        r"TOTAL\s+DES\s+OPERATIONS\s+([\d][\d\s]*,\d{2})\s+([\d][\d\s]*,\d{2})",
        re.IGNORECASE
    )

    # Mots à ignorer - les lignes qui les contiennent ne sont pas des transactions
    # Attention à ne pas exclure des transactions légitimes
    STOP_PREFIXES = (
        "PAGE", "ECRITURES DE LA PERIODE", "DATE LIBELLE", "ANCIEN SOLDE",
        "SOLDE INTERMEDIAIRE", "SOLDE EN EUROS", "TITULAIRE DU COMPTE",
        "VOTRECONSEILLER", "CREDIT LYONNAIS", "RELEVE DE COMPTE",
        "RELEVE D'IDENTITE", "DOMICILIATION", "REFERENCES BANCAIRES",
        "PRENEZ RENDEZ", "IBAN :", "BIC :", "COMPTE :", "NOUVEAU SOLDE",
        "TOTAUX", "TOTAL DES"
    )

    # Préfixes d'en-tête de transaction
    HEADER_PREFIXES = (
        "PRLV", "VIR", "VIREMENT", "VERSEMENT", "REMISE", "REM CB",
        "CB", "CHEQUE", "CHQ", "DEPOT", "DEBLOC", "FRAIS", "AGIOS",
        "PAIEMENT", "PREFILOC", "LOYER", "RESIDENCE", "METRO", "GNANAM",
        "NOUTAM", "ENGIE", "GAZ", "SFR", "CANAL", "ASSURANCE", "AVEM",
        "SPB", "URSSAF", "KLESIA", "HMD", "FACTURE", "INT", "AVIS",
        "SALAIRE", "RETRAIT"
    )

    # Préfixes de détail (lignes de continuation)
    DETAIL_PREFIXES = (
        "LIBELLE", "REF", "ID", "BRUT", "COM", "PCE", "REG",
        "N", "NO", "NUMERO", "CLIENT", "RIB", "DUPLICATA",
        "COTIS", "HEANCE"
    )

    def __init__(
        self,
        config: Optional[ParserConfig] = None,
        bank_type: Optional[BankType] = None
    ):
        self.config = config or ParserConfig()
        self._bank_type = bank_type or BankType.LCL
        self.logger = logging.getLogger(__name__)

    @property
    def bank_type(self) -> BankType:
        """Return the bank type this parser is configured for."""
        return self._bank_type

    def can_parse(self, text: str) -> bool:
        """Check if this parser can handle the given text.

        Uses pattern matching to detect if the text is from this bank type.
        """
        from .detector import BankDetector
        detector = BankDetector()
        detected_type, confidence = detector.detect(text)
        return detected_type == self._bank_type and confidence > 0.3

    def parse(
        self,
        lines: List[str],
        period: StatementPeriod,
        bank_type: BankType = BankType.LCL
    ) -> ParsedStatement:
        """Analyse les lignes pour constituer un relevé complet.

        Args:
            lines: Lignes de texte à parser
            period: Période du relevé
            bank_type: Type de banque pour positionner les colonnes

        Returns:
            ParsedStatement avec transactions et solde
        """
        self.logger.debug(f"Starting parse for {bank_type.value}, period: {period}, lines: {len(lines)}")

        # Récupère les positions de colonnes selon la banque
        columns = self._get_columns(bank_type)

        # Extrait les informations de solde (spécifique à la banque)
        balance = self._extract_balance(lines, bank_type)
        if balance:
            self.logger.debug(
                f"Balance extracted: opening={balance.opening_balance}, "
                f"closing={balance.closing_balance}, "
                f"total_debits={balance.total_debits}, "
                f"total_credits={balance.total_credits}"
            )
        else:
            self.logger.warning("No balance information found in statement")

        # Analyse les transactions
        transactions = self._parse_transactions(lines, period, columns, bank_type)
        self.logger.debug(f"Parsed {len(transactions)} transactions")

        # Construit le relevé
        statement = ParsedStatement(
            period=period,
            transactions=transactions,
            balance=balance,
            bank_type=bank_type,
        )

        # Valide le solde si disponible
        if balance:
            calculated_credits = sum(
                t.montant for t in transactions
                if t.direction == TransactionDirection.IN
            )
            calculated_debits = sum(
                t.montant for t in transactions
                if t.direction == TransactionDirection.OUT
            )

            # Utilise les totaux réels des transactions (ajustés de l'ANCIEN SOLDE)
            expected_credits = balance.actual_transaction_credits
            expected_debits = balance.actual_transaction_debits

            self.logger.debug(
                f"Calculated totals: credits={calculated_credits}, debits={calculated_debits}"
            )
            self.logger.debug(
                f"Expected totals: credits={expected_credits}, debits={expected_debits}"
            )

            # Compare aux totaux attendus (totaux réels des transactions, pas ceux du PDF TOTAUX)
            if abs(calculated_credits - expected_credits) < Decimal("0.02"):
                if abs(calculated_debits - expected_debits) < Decimal("0.02"):
                    statement.is_balanced = True
                    self.logger.debug("Statement is balanced")

            if not statement.is_balanced:
                error_msg = (
                    f"Balance mismatch: calculated credits={calculated_credits}, "
                    f"expected={expected_credits}, "
                    f"calculated debits={calculated_debits}, "
                    f"expected={expected_debits}"
                )
                statement.validation_notes.append(error_msg)
                self.logger.warning(error_msg)

        return statement

    def _get_columns(self, bank_type: BankType) -> ColumnPositions:
        """Retourne les positions de colonnes selon le type de banque."""
        if bank_type == BankType.LCL:
            return ColumnPositions.for_lcl()
        elif bank_type == BankType.BNP:
            return ColumnPositions.for_bnp()
        return ColumnPositions.for_lcl()  # Par défaut

    def _detect_ancien_solde_from_position(
        self,
        lines: List[str]
    ) -> Tuple[Optional[Decimal], BalanceType]:
        """Détecte le montant et le type d'ANCIEN SOLDE via la position de colonne.

        Mise en page des colonnes PDF LCL :
        - Colonne DEBIT : positions ~105-124 (avant la position 125)
        - Colonne CREDIT : positions ~125-200 (après la position 125)

        Si le montant apparaît avant 125, il s'agit d'un DEBITEUR (découvert).
        Après 125, c'est un CREDITEUR (solde positif).

        Args:
            lines: Lignes texte du PDF

        Returns:
            Tuple (montant, type de solde). Retourne (None, CREDITEUR) si non trouvé.
        """
        # Limite de colonne entre DEBIT et CREDIT
        DEBIT_CREDIT_BOUNDARY = 125

        for line in lines:
            if "ANCIEN SOLDE" not in line.upper():
                continue

            # Complète la ligne pour garantir assez de caractères
            padded_line = line.ljust(200)

            # Trouve le montant dans la ligne via regex
            amount_pattern = re.compile(r"([\d][\d\s]*,\d{2})")
            matches = list(amount_pattern.finditer(line))

            if not matches:
                continue

            # Prend la dernière occurrence (censée être le montant)
            match = matches[-1]
            amount_start_pos = match.start()
            amount_str = match.group(1)
            amount = self._parse_amount(amount_str)

            if amount is None:
                continue

            # Détermine le type en fonction de la position
            if amount_start_pos < DEBIT_CREDIT_BOUNDARY:
                self.logger.debug(
                    f"ANCIEN SOLDE amount '{amount_str}' at position {amount_start_pos} "
                    f"(< {DEBIT_CREDIT_BOUNDARY}) -> DEBITEUR"
                )
                return amount, BalanceType.DEBITEUR
            else:
                self.logger.debug(
                    f"ANCIEN SOLDE amount '{amount_str}' at position {amount_start_pos} "
                    f"(>= {DEBIT_CREDIT_BOUNDARY}) -> CREDITEUR"
                )
                return amount, BalanceType.CREDITEUR

        return None, BalanceType.CREDITEUR

    def _extract_balance(
        self,
        lines: List[str],
        bank_type: BankType = BankType.LCL
    ) -> Optional[StatementBalance]:
        """Extrait les informations de solde depuis le relevé.

        Args:
            lines: Lignes de texte
            bank_type: Type de banque pour le parsing spécifique

        Returns:
            StatementBalance ou None
        """
        full_text = "\n".join(lines)

        opening = None
        closing = None
        total_debits = None
        total_credits = None
        opening_balance_type = BalanceType.CREDITEUR  # Par défaut
        closing_balance_type = BalanceType.CREDITEUR  # Par défaut

        if bank_type == BankType.BNP:
            # Format BNP :
            # - Ouverture : première occurrence "SOLDE CREDITEUR AU dd.mm.yyyy ... montant"
            # - Clôture : dernière occurrence "SOLDE CREDITEUR AU dd.mm.yyyy ... montant"
            # - Totaux : "TOTAL DES OPERATIONS ... débit ... crédit"

            # Trouver toutes les occurrences de SOLDE CREDITEUR
            solde_matches = list(self.BNP_SOLDE_CREDITEUR_RE.finditer(full_text))
            if solde_matches:
                # La première correspond au solde d'ouverture
                opening = self._parse_amount(solde_matches[0].group(1))
                # La dernière correspond au solde de clôture
                if len(solde_matches) > 1:
                    closing = self._parse_amount(solde_matches[-1].group(1))

            # Récupérer les totaux via TOTAL DES OPERATIONS
            match = self.BNP_TOTAL_OPERATIONS_RE.search(full_text)
            if match:
                total_debits = self._parse_amount(match.group(1))
                total_credits = self._parse_amount(match.group(2))

        else:
            # Format LCL (par défaut)
            # Solde d'ouverture (ANCIEN SOLDE CREDITEUR/DEBITEUR)
            # Première tentative : rechercher un libellé CREDITEUR/DEBITEUR explicite
            match = self.ANCIEN_SOLDE_RE.search(full_text)
            if match:
                opening_type_str = match.group(1).upper()
                opening_balance_type = (
                    BalanceType.DEBITEUR if opening_type_str == "DEBITEUR"
                    else BalanceType.CREDITEUR
                )
                opening = self._parse_amount(match.group(2))
                self.logger.debug(f"ANCIEN SOLDE {opening_type_str}: {opening}")
            else:
                # Repli : détecte le type via la position de colonne
                # Colonne DEBIT ~105-124, colonne CREDIT ~125-200
                opening, opening_balance_type = self._detect_ancien_solde_from_position(lines)
                if opening is not None:
                    self.logger.debug(
                        f"ANCIEN SOLDE detected by position: {opening} ({opening_balance_type.value})"
                    )

            # Solde de clôture (NOUVEAU SOLDE CREDITEUR/DEBITEUR)
            match = self.NOUVEAU_SOLDE_RE.search(full_text)
            if match:
                closing_type_str = (match.group(1) or "CREDITEUR").upper()
                closing_balance_type = (
                    BalanceType.DEBITEUR if closing_type_str == "DEBITEUR"
                    else BalanceType.CREDITEUR
                )
                closing = self._parse_amount(match.group(2))
                self.logger.debug(f"NOUVEAU SOLDE {closing_type_str}: {closing}")
            else:
                # Repli sans type
                match = self.NOUVEAU_SOLDE_SIMPLE_RE.search(full_text)
                if match:
                    closing = self._parse_amount(match.group(1))
                    closing_balance_type = BalanceType.CREDITEUR
                    self.logger.debug(f"NOUVEAU SOLDE (default CREDITEUR): {closing}")

            # Totaux (ligne TOTAUX avec débit et crédit)
            # Format LCL : "TOTAUX   15 737,93           15 881,69"
            match = self.TOTAUX_RE.search(full_text)
            if match:
                total_debits = self._parse_amount(match.group(1))
                total_credits = self._parse_amount(match.group(2))
            else:
                # Essaie les lignes de total individuelles
                match = self.TOTAL_DEBIT_RE.search(full_text)
                if match:
                    total_debits = self._parse_amount(match.group(1))

                match = self.TOTAL_CREDIT_RE.search(full_text)
                if match:
                    total_credits = self._parse_amount(match.group(1))

        # Si des totaux sont présents sans solde de clôture, on le calcule
        # Spécificité LCL : les crédits TOTAUX incluent déjà l'ANCIEN SOLDE
        # Pour BNP : closing = opening + credits - debits
        if closing is None and total_debits is not None and total_credits is not None:
            if bank_type == BankType.BNP and opening is not None:
                closing = opening + total_credits - total_debits
            else:
                closing = total_credits - total_debits

        # Return balance if we have at least opening and totals
        if opening is not None and total_debits is not None and total_credits is not None:
            if closing is None:
                if bank_type == BankType.BNP:
                    closing = opening + total_credits - total_debits
                else:
                    # LCL: TOTAUX already includes ANCIEN SOLDE
                    # NOUVEAU SOLDE = TOTAUX credits - TOTAUX debits
                    closing = total_credits - total_debits
            return StatementBalance(
                opening_balance=opening,
                closing_balance=closing,
                total_debits=total_debits,
                total_credits=total_credits,
                opening_balance_type=opening_balance_type,
                closing_balance_type=closing_balance_type,
            )

        return None

    def _parse_transactions(
        self,
        lines: List[str],
        period: StatementPeriod,
        columns: ColumnPositions,
        bank_type: BankType = BankType.LCL
    ) -> List[ParsedTransaction]:
        """Parse transaction lines.

        Args:
            lines: Text lines
            period: Statement period for year inference
            columns: Column positions
            bank_type: Bank type for specific parsing

        Returns:
            List of ParsedTransaction objects
        """
        transactions: List[ParsedTransaction] = []
        current_transaction: Optional[ParsedTransaction] = None

        # Mots vides spécifiques BNP
        bnp_stop_words = (
            "SOLDE CREDITEUR", "SOLDE DEBITEUR", "NOUVEAU SOLDE",
            "BNP PARIBAS", "RELEVE DE COMPTE", "RIB :", "IBAN :",
            "BIC :", "Nature des opérations", "Monnaie du compte"
        )

        for line_num, raw_line in enumerate(lines):
            # Normalise la ligne
            line = raw_line.replace("\u00a0", " ")

            # Ignore les lignes vides
            if not line.strip():
                continue

            # Ignore les stop words (si un préfixe de stop apparaît dans la ligne)
            stripped_upper = line.strip().upper()
            should_skip = False

            # Vérifie les préfixes d'arrêt standards
            for prefix in self.STOP_PREFIXES:
                if prefix in stripped_upper:
                    should_skip = True
                    break

            # Vérifie les stop words spécifiques BNP
            if bank_type == BankType.BNP and not should_skip:
                for stop in bnp_stop_words:
                    if stop.upper() in stripped_upper:
                        should_skip = True
                        break

            if should_skip:
                # Sauvegarde la transaction courante avant de passer
                if current_transaction:
                    transactions.append(current_transaction)
                    current_transaction = None
                continue

            # Pour BNP, utilise une regex pour détecter les lignes de transaction
            if bank_type == BankType.BNP:
                # BNP : la ligne commence par une date dd.mm
                is_new_transaction = bool(re.match(r"^\s*\d{2}\.\d{2}\s+", line))
            else:
                # LCL : utilise les positions de colonnes
                if self.config.pad_lines:
                    line = line.ljust(self.config.pad_length)
                date_str = line[columns.date_start:columns.date_end].strip()
                is_new_transaction = bool(self.DATE_SHORT_RE.match(date_str))

            if is_new_transaction:
                # Sauvegarde la transaction précédente
                if current_transaction:
                    transactions.append(current_transaction)

                # Parse la nouvelle transaction
                current_transaction = self._parse_transaction_line(
                    line, line_num, period, columns, bank_type
                )
            elif current_transaction:
                # Ligne de continuation - ajoute au libellé avec limite de longueur
                detail_text = line.strip()
                if detail_text and not self._is_header_line(detail_text):
                    # Vérifie s'il s'agit d'une ligne de préfixe de détail
                    first_word = detail_text.split()[0].upper() if detail_text.split() else ""
                    if first_word not in self.DETAIL_PREFIXES:
                        new_libelle = (current_transaction.libelle + " " + detail_text).strip()

                        # Impose la limite de longueur
                        if len(new_libelle) > self.MAX_LIBELLE_LENGTH:
                            self.logger.warning(
                                f"Libelle exceeds max length ({self.MAX_LIBELLE_LENGTH} chars). "
                                f"Truncating. Original length: {len(new_libelle)}, "
                                f"Transaction date: {current_transaction.date_operation}, "
                                f"First 50 chars: {new_libelle[:50]}"
                            )
                            current_transaction.libelle = new_libelle[:self.MAX_LIBELLE_LENGTH]
                        else:
                            current_transaction.libelle = new_libelle

        # Don't forget last transaction
        if current_transaction:
            transactions.append(current_transaction)

        return transactions

    def _parse_transaction_line(
        self,
        line: str,
        line_num: int,
        period: StatementPeriod,
        columns: ColumnPositions,
        bank_type: BankType = BankType.LCL
    ) -> Optional[ParsedTransaction]:
        """Parse a single transaction line.

        Args:
            line: Text line (already padded)
            line_num: Line number for debugging
            period: Statement period
            columns: Column positions
            bank_type: Bank type for specific parsing

        Returns:
            ParsedTransaction or None if parsing fails
        """
        # Use BNP-specific parsing for BNP statements
        if bank_type == BankType.BNP:
            return self._parse_bnp_transaction_line(line, line_num, period)

        try:
            # Extract date
            date_str = line[columns.date_start:columns.date_end].strip()
            op_date = self._parse_date(date_str, period)
            if not op_date:
                return None

            # Extract value date (if present)
            valeur_str = line[columns.valeur_start:columns.valeur_end].strip()
            # Find date in valeur zone
            valeur_match = self.DATE_SHORT_RE.search(valeur_str)
            if valeur_match:
                val_date = self._parse_date(valeur_match.group(), period)
            else:
                val_date = op_date

            # Extract libelle
            libelle = line[columns.libelle_start:columns.libelle_end].strip()

            # Extract amounts
            debit_zone = line[columns.debit_start:columns.debit_end].strip()
            credit_zone = line[columns.credit_start:columns.credit_end].strip()

            debit_amt = self._parse_amount(debit_zone)
            credit_amt = self._parse_amount(credit_zone)

            # Determine direction and amount
            if credit_amt is not None and credit_amt > 0:
                montant = credit_amt
                direction = TransactionDirection.IN
            elif debit_amt is not None and debit_amt > 0:
                montant = debit_amt
                direction = TransactionDirection.OUT
            else:
                # No valid amount found
                return None

            # Generate checksum
            checksum = self._generate_checksum(op_date, libelle, montant, direction)

            self.logger.debug(
                f"LCL parsed: date={op_date}, libelle={libelle[:30]}, "
                f"amount={montant}, direction={direction.value}"
            )

            return ParsedTransaction(
                date_operation=op_date,
                date_valeur=val_date or op_date,
                libelle=libelle,
                montant=montant,
                direction=direction,
                line_number=line_num,
                raw_text=line.rstrip(),
                checksum=checksum,
            )

        except Exception as e:
            self.logger.debug(f"LCL parse exception at line {line_num}: {e}")
            return None

    # BNP semantic direction detection keywords
    BNP_DEBIT_KEYWORDS = (
        "PRLV", "PRELEVEMENT", "FACTURE", "ECHEANCE PRET", "ECHEANCEPRET",
        "VIR EMIS", "VIR INST EMIS", "VIR SCT INST EMIS", "VIR SEPA EMIS",
        "VIRT CPTE A CPTE EMIS", "VIREMENT EMIS", "RETRAIT", "CHEQUE",
        "COMMISSION", "FRAIS", "AGIOS", "SAISIE"
    )
    BNP_CREDIT_KEYWORDS = (
        "VIR RECU", "VIR INST RECU", "VIR SCT INST RECU", "VIR SEPA RECU",
        "VIR CPTE A CPTE RECU", "VIREMENT RECU", "VRST ESPECES", "VERSEMENT",
        "REMISE CB", "REMBOURST", "AVOIR", "EXTOURNE"
    )

    def _parse_bnp_transaction_line(
        self,
        line: str,
        line_num: int,
        period: StatementPeriod
    ) -> Optional[ParsedTransaction]:
        """Parse a BNP transaction line using semantic direction detection.

        BNP statement format varies, so we use keyword-based direction detection
        instead of fixed column positions.

        Direction is determined by keywords in the libellé:
        - OUT: PRLV, FACTURE, VIR EMIS, ECHEANCE PRET, etc.
        - IN: VIR RECU, VRST ESPECES, REMISE CB, etc.

        Args:
            line: Text line
            line_num: Line number
            period: Statement period

        Returns:
            ParsedTransaction or None
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Extract date from beginning of line
            date_search_re = re.compile(r"(\d{2})[./](\d{2})")
            date_match = date_search_re.search(line[:15])
            if not date_match:
                logger.debug(f"No date found in line start: {line[:15]}")
                return None

            op_date = self._parse_date(date_match.group(), period)
            if not op_date:
                logger.debug(f"Could not parse date: {date_match.group()}")
                return None

            # Find value date (second date pattern in line)
            all_dates = date_search_re.findall(line)
            if len(all_dates) >= 2:
                val_date_str = f"{all_dates[1][0]}.{all_dates[1][1]}"
                val_date = self._parse_date(val_date_str, period)
            else:
                val_date = op_date

            # Extract amount (last amount pattern in line)
            amount_pattern = re.compile(r"(\d{1,3}(?:[\s]\d{3})*,\d{2})")
            amounts = amount_pattern.findall(line)
            if not amounts:
                logger.debug(f"No amount found in line: {line[:80]}")
                return None

            # Use the LAST amount (usually the transaction amount, not intermediate values)
            montant = self._parse_amount(amounts[-1])
            if not montant or montant <= 0:
                logger.debug(f"Invalid amount: {amounts[-1]}")
                return None

            # Extract libelle (text between first date and amounts area)
            # Remove date patterns and amounts to get clean libelle
            libelle = line
            # Remove dates (DD.MM pattern)
            libelle = re.sub(r"\d{2}\.\d{2}", "", libelle)
            # Remove amounts
            libelle = re.sub(r"\d{1,3}(?:[\s]\d{3})*,\d{2}", "", libelle)
            # Clean up whitespace
            libelle = " ".join(libelle.split()).strip()

            if not libelle:
                libelle = "Transaction BNP"

            # SEMANTIC DIRECTION DETECTION based on keywords
            libelle_upper = libelle.upper()
            direction = None

            # Vérifie d'abord les mots-clés de crédit (plus spécifiques)
            for keyword in self.BNP_CREDIT_KEYWORDS:
                if keyword in libelle_upper:
                    direction = TransactionDirection.IN
                    logger.debug(f"BNP credit detected by keyword '{keyword}': {libelle[:40]}")
                    break

            # Vérifie les mots-clés de débit
            if direction is None:
                for keyword in self.BNP_DEBIT_KEYWORDS:
                    if keyword in libelle_upper:
                        direction = TransactionDirection.OUT
                        logger.debug(f"BNP debit detected by keyword '{keyword}': {libelle[:40]}")
                        break

            # Par défaut OUT si aucun mot-clé ne correspond (la plupart des transactions sont des débits)
            if direction is None:
                direction = TransactionDirection.OUT
                logger.debug(f"BNP defaulting to OUT for: {libelle[:40]}")

            checksum = self._generate_checksum(op_date, libelle, montant, direction)

            logger.debug(f"BNP parsed: date={op_date}, libelle={libelle[:30]}, "
                        f"amount={montant}, direction={direction.value}")

            return ParsedTransaction(
                date_operation=op_date,
                date_valeur=val_date or op_date,
                libelle=libelle,
                montant=montant,
                direction=direction,
                line_number=line_num,
                raw_text=line.rstrip(),
                checksum=checksum,
            )

        except Exception as e:
            logger.debug(f"BNP parse exception: {e}", exc_info=True)
            return None

    def _parse_date(self, date_str: str, period: StatementPeriod) -> Optional[date]:
        """Parse a date string.

        Args:
            date_str: Date string (dd.mm or dd.mm.yy or dd.mm.yyyy)
            period: Statement period for year inference

        Returns:
            date object or None
        """
        # Try short format first (dd.mm)
        match = self.DATE_SHORT_RE.match(date_str)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            # Infer year from period
            year = period.start_date.year
            if month < period.start_date.month:
                year = period.end_date.year
            try:
                return date(year, month, day)
            except ValueError:
                return None

        # Try full format (dd.mm.yy or dd.mm.yyyy)
        match = self.DATE_FULL_RE.match(date_str)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3))
            if year < 100:
                year += 2000
            try:
                return date(year, month, day)
            except ValueError:
                return None

        return None

    def _parse_amount(self, amount_str: str) -> Optional[Decimal]:
        """Parse an amount string.

        Args:
            amount_str: Amount string (e.g., "1 234,56")

        Returns:
            Decimal or None
        """
        if not amount_str:
            return None

        # Clean the string
        cleaned = amount_str.strip()
        cleaned = cleaned.replace("\u00a0", "")  # Non-breaking space
        cleaned = cleaned.replace(" ", "")  # Regular space (thousands)
        cleaned = cleaned.replace(",", ".")  # Decimal separator

        # Remove any non-numeric characters except dot and minus
        cleaned = re.sub(r"[^\d.\-]", "", cleaned)

        if not cleaned:
            return None

        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    def _is_header_line(self, line: str) -> bool:
        """Vérifie si la ligne correspond à un en-tête ou des métadonnées."""
        upper = line.upper()
        return any(upper.startswith(prefix) for prefix in self.STOP_PREFIXES)

    def _generate_checksum(
        self,
        op_date: date,
        libelle: str,
        montant: Decimal,
        direction: TransactionDirection
    ) -> str:
        """Génère un checksum unique pour le dédoublonnage.

        IMPORTANT : doit correspondre exactement au calcul de deduplicator.py.
        Utilise quantize pour garantir un montant normalisé à 2 décimales.

        Args:
            op_date: Date d'opération
            libelle: Description de transaction
            montant: Montant
            direction: IN ou OUT

        Returns:
            Hex digest SHA256 (32 caractères)
        """
        # Normalise le montant à 2 décimales (doit correspondre au dédoublonneur)
        normalized_amount = montant.quantize(Decimal("0.01"))
        data = f"{op_date.isoformat()}|{libelle.strip().upper()}|{normalized_amount}|{direction.value}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()[:32]


def parse_lcl_statement(
    lines: List[str],
    period: StatementPeriod
) -> ParsedStatement:
    """Fonction utilitaire pour parser un relevé LCL.

    Args:
        lines: Lignes de texte
        period: Période du relevé

    Returns:
        ParsedStatement
    """
    parser = UnifiedBankParser()
    return parser.parse(lines, period, BankType.LCL)


def parse_sumup_statement(text: str) -> ParsedStatement:
    """Analyse le texte PDF d'un relevé de compte SumUp (format tabulaire).

    Les relevés SumUp extraits avec pdftotext -layout sont tabulaires :
    11/11/2025       C9BY63LJ2Z   Paiement en ligne   Merchant   Approuvé   19.99   0.00   0.00   147.06
    22:04                                              Paris FR

    Args:
        text: Contenu texte complet du PDF SumUp (avec -layout)

    Returns:
        ParsedStatement avec transactions
    """
    logger = logging.getLogger(__name__)
    transactions: List[ParsedTransaction] = []

    lines = text.split('\n')

    # Extrait la période depuis l'en-tête
    period_match = re.search(
        r"période\s+du\s+rapport:\s*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})",
        text, re.IGNORECASE
    )
    if period_match:
        start_date = datetime.strptime(period_match.group(1), "%d/%m/%Y").date()
        end_date = datetime.strptime(period_match.group(2), "%d/%m/%Y").date()
    else:
        start_date = date(2022, 1, 1)
        end_date = date.today()

    period = StatementPeriod(start_date=start_date, end_date=end_date)

    # Motif des lignes de transaction : commence par une date dd/mm/yyyy
    # Format : DATE  CODE  TYPE  REFERENCE  STATUT  DEBIT  CREDIT  FRAIS  SOLDE
    tx_line_re = re.compile(
        r"^(\d{2}/\d{2}/\d{4})\s+"  # Date
        r"([A-Z0-9]{8,12})\s+"       # Code transaction
        r"(.+?)\s+"                   # Type + Référence (gourmand jusqu'aux nombres)
        r"(\d+[.,]\d{2})\s+"         # Montant débit
        r"(\d+[.,]\d{2})\s+"         # Montant crédit
        r"(\d+[.,]\d{2})\s+"         # Frais
        r"(\d+[.,]\d{2})"            # Solde
    )

    # Motif simplifié pour la majorité des lignes
    simple_tx_re = re.compile(r"^(\d{2}/\d{2}/\d{4})\s+([A-Z0-9]{8,12})")

    # Indicateurs d'encaissement
    income_keywords = ("paiement entrant", "entrant", "remboursé", "rembourser")

    for line in lines:
        # Ignore les lignes vides et les en-têtes
        if not line.strip() or "Date de la" in line or "transaction" in line.lower() and "code" in line.lower():
            continue

        # Tente de faire correspondre une ligne de transaction débutant par la date
        simple_match = simple_tx_re.match(line)
        if simple_match:
            tx_date_str = simple_match.group(1)
            tx_code = simple_match.group(2)

            try:
                tx_date = datetime.strptime(tx_date_str, "%d/%m/%Y").date()
            except ValueError:
                continue

            # Extrait le reste de la ligne après le code
            rest = line[simple_match.end():].strip()

            # Trouve les montants dans la ligne (format dd.dd)
            amounts = re.findall(r'(\d+[.,]\d{2})', rest)

            # Parse les montants (attendu : débit, crédit, frais, solde)
            tx_debit = Decimal("0")
            tx_credit = Decimal("0")

            if len(amounts) >= 4:
                try:
                    tx_debit = Decimal(amounts[0].replace(",", "."))
                    tx_credit = Decimal(amounts[1].replace(",", "."))
                except:
                    pass

            # Détermine le sens et le montant
            if tx_credit > 0:
                tx_direction = TransactionDirection.IN
                tx_amount = tx_credit
            elif tx_debit > 0:
                tx_direction = TransactionDirection.OUT
                tx_amount = tx_debit
            else:
                continue  # Ignore si aucun montant

            # Extrait le type/la référence du texte avant les montants
            type_ref = rest
            for amt in amounts:
                type_ref = type_ref.replace(amt, "").strip()

            # Nettoie le type/la référence
            type_ref = re.sub(r'\s+', ' ', type_ref).strip()

            # Corrige la direction si des mots-clés d'encaissement sont présents
            type_ref_lower = type_ref.lower()
            for kw in income_keywords:
                if kw in type_ref_lower:
                    tx_direction = TransactionDirection.IN
                    break

            # Construit le libellé
            libelle = f"{type_ref} - Ref:{tx_code}" if type_ref else f"SumUp {tx_code}"

            transaction = ParsedTransaction(
                date_operation=tx_date,
                date_valeur=tx_date,
                libelle=libelle[:500],
                montant=tx_amount,
                direction=tx_direction,
            )
            transactions.append(transaction)

    # Calcule les totaux
    total_credits = sum(t.montant for t in transactions if t.direction == TransactionDirection.IN)
    total_debits = sum(t.montant for t in transactions if t.direction == TransactionDirection.OUT)

    balance = StatementBalance(
        opening_balance=Decimal("0"),
        closing_balance=total_credits - total_debits,
        total_credits=total_credits,
        total_debits=total_debits,
    )

    logger.info(f"Parsed {len(transactions)} SumUp transactions: IN={total_credits}, OUT={total_debits}")

    return ParsedStatement(
        period=period,
        transactions=transactions,
        balance=balance,
        bank_type=BankType.SUMUP,
    )


# =============================================================================
# FABRIQUE DE PARSEURS
# =============================================================================

@dataclass
class ParserRegistry:
    """Registre des parseurs bancaires disponibles.

    Autorise l'enregistrement dynamique de nouveaux parseurs pour étendre le support.
    """
    _parsers: dict = field(default_factory=dict)

    def register(self, bank_type: BankType, parser_class: type) -> None:
        """Enregistre une classe de parseur pour un type de banque."""
        self._parsers[bank_type] = parser_class

    def get_parser(self, bank_type: BankType) -> UnifiedBankParser:
        """Récupère une instance de parseur pour un type de banque."""
        # Pour l'instant, UnifiedBankParser gère tous les types
        return UnifiedBankParser(bank_type=bank_type)

    def get_available_banks(self) -> List[BankType]:
        """Retourne la liste des types de banque pris en charge."""
        return [BankType.LCL, BankType.BNP, BankType.SUMUP]


# Instance globale du registre
_parser_registry = ParserRegistry()


def get_parser(bank_type: BankType) -> UnifiedBankParser:
    """Fonction fabrique pour obtenir le parseur adapté à un type de banque.

    Args:
        bank_type: Type de relevé bancaire

    Returns:
        Instance de parseur configurée pour ce type de banque

    Example:
        parser = get_parser(BankType.LCL)
        statement = parser.parse(lines, period)
    """
    return _parser_registry.get_parser(bank_type)


def parse_statement(
    lines: List[str],
    period: StatementPeriod,
    bank_type: BankType
) -> ParsedStatement:
    """Fonction utilitaire pour parser un relevé.

    Args:
        lines: Lignes de texte issues du PDF
        period: Période du relevé
        bank_type: Type de banque

    Returns:
        ParsedStatement avec transactions
    """
    parser = get_parser(bank_type)
    return parser.parse(lines, period, bank_type)
