"""
Parseurs de relevés bancaires - LCL, BNP, SUMUP

Algorithme 1: Nettoyage des headers/footers pour extraire uniquement les opérations
Algorithme 2: Extraction des mots-clés par catégorie (12 catégories)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterator

import pdfplumber


@dataclass
class Transaction:
    """Représente une transaction bancaire extraite."""

    date: str
    libelle: str
    valeur: str | None = None
    debit: Decimal | None = None
    credit: Decimal | None = None
    raw_text: str = ""
    source_file: str = ""
    source_page: int = 0
    bank_type: str = ""


@dataclass
class ParsedStatement:
    """Résultat du parsing d'un relevé."""

    bank_type: str
    period_start: str | None = None
    period_end: str | None = None
    account_holder: str = ""
    iban: str = ""
    transactions: list[Transaction] = field(default_factory=list)
    source_file: str = ""
    raw_pages: list[str] = field(default_factory=list)


# =============================================================================
# PARSEUR LCL
# =============================================================================


class LCLParser:
    """Parseur pour les relevés LCL (Crédit Lyonnais)."""

    # Patterns pour identifier les headers/footers à supprimer
    HEADER_PATTERNS = [
        r"RELEVE DE COMPTE COURANT",
        r"du \d{2}\.\d{2}\.\d{4} au \d{2}\.\d{2}\.\d{4}",
        r"RELEVE D'IDENTITE BANCAIRE",
        r"CREDIT LYONNAIS",
        r"Titulaire du compte",
        r"Domiciliation",
        r"Références bancaires",
        r"IBAN\s*:",
        r"BIC\s*:",
        r"Votre\s*conseiller",
        r"Prenez rendez-vous",
        r"Internet\s*:.*LCL\.fr",
        r"Mobile\s*:.*LCL",
        r"Les tarifs applicables",
        r"L'avenant au",
        r"A partir du",
        r"Indicatif\s*:\d+\s*Compte",
    ]

    FOOTER_PATTERNS = [
        r"Page \d+ / \d+",
        r"Crédit Lyonnais.*SIREN",
        r"Ce document ne vaut pas facture",
        r"Les sommes figurant sur ce compte",
        r"Votre conseiller et le directeur",
        r"Vous pouvez solliciter",
        r"formulaire.*lcl\.fr",
        r"médiateur",
        r"^\w{8}$",  # Code comme "92PTXE6K"
    ]

    # Pattern pour la section des opérations
    OPERATIONS_START = r"ECRITURES DE LA PERIODE"
    OPERATIONS_HEADER = r"DATE\s+LIBELLE\s+VALEUR\s+DEBIT\s+CREDIT"

    # Pattern pour une ligne d'opération (date en début de ligne)
    OPERATION_LINE = re.compile(
        r"^(\d{2}\.\d{2})\s+"  # Date DD.MM
        r"(.+?)\s+"  # Libellé
        r"(\d{2}\.\d{2}\.\d{2})\s+"  # Valeur DD.MM.YY
        r"([\d\s,\.]+)?\s*\.?\s*"  # Débit (optionnel, avec point final)
        r"([\d\s,\.]+)?$",  # Crédit (optionnel)
        re.MULTILINE,
    )

    # Pattern alternatif pour lignes avec continuation
    CONTINUATION_LINE = re.compile(r"^(?!\d{2}\.\d{2}\s)(.+)$", re.MULTILINE)

    @classmethod
    def parse(cls, pdf_path: str | Path) -> ParsedStatement:
        """Parse un relevé LCL et retourne les transactions nettoyées."""
        pdf_path = Path(pdf_path)
        result = ParsedStatement(
            bank_type="LCL",
            source_file=str(pdf_path),
        )

        with pdfplumber.open(pdf_path) as pdf:
            all_text = []

            for page_num, page in enumerate(pdf.pages, 1):
                raw_text = page.extract_text() or ""
                result.raw_pages.append(raw_text)

                # Extraire les métadonnées de la première page
                if page_num == 1:
                    cls._extract_metadata(raw_text, result)

                # Nettoyer la page
                cleaned = cls._clean_page(raw_text)
                all_text.append(cleaned)

            # Parser toutes les transactions
            full_text = "\n".join(all_text)
            result.transactions = cls._parse_transactions(full_text, str(pdf_path))

        return result

    @classmethod
    def _extract_metadata(cls, text: str, result: ParsedStatement) -> None:
        """Extrait les métadonnées du relevé (période, titulaire, IBAN)."""
        # Période
        period_match = re.search(
            r"du (\d{2}\.\d{2}\.\d{4}) au (\d{2}\.\d{2}\.\d{4})", text
        )
        if period_match:
            result.period_start = period_match.group(1)
            result.period_end = period_match.group(2)

        # IBAN
        iban_match = re.search(r"IBAN\s*:\s*([A-Z]{2}\d{2}[\s\d\w]+)", text)
        if iban_match:
            result.iban = iban_match.group(1).replace(" ", "")

        # Titulaire (après "Titulaire du compte")
        holder_match = re.search(
            r"Titulaire du compte[-\s]*([A-Z\s]+?)(?:\n|---)", text
        )
        if holder_match:
            result.account_holder = holder_match.group(1).strip()

    @classmethod
    def _clean_page(cls, text: str) -> str:
        """Nettoie une page en supprimant headers et footers."""
        lines = text.split("\n")
        cleaned_lines = []
        in_operations = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Détecter le début de la section opérations
            if re.search(cls.OPERATIONS_START, line, re.IGNORECASE):
                in_operations = True
                continue

            # Ignorer la ligne d'en-tête des colonnes
            if re.search(cls.OPERATIONS_HEADER, line, re.IGNORECASE):
                continue

            # Si pas encore dans les opérations, ignorer (c'est le header)
            if not in_operations:
                continue

            # Vérifier si c'est un footer
            is_footer = False
            for pattern in cls.FOOTER_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    is_footer = True
                    break

            if is_footer:
                continue

            # Ignorer certains headers qui peuvent apparaître en milieu de page
            is_header = False
            for pattern in cls.HEADER_PATTERNS[:5]:  # Premiers patterns seulement
                if re.search(pattern, line, re.IGNORECASE):
                    is_header = True
                    break

            if is_header:
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    @classmethod
    def _parse_transactions(
        cls, text: str, source_file: str
    ) -> list[Transaction]:
        """Parse les transactions depuis le texte nettoyé."""
        transactions = []
        lines = text.split("\n")
        current_tx = None
        current_libelle_parts = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Essayer de matcher une nouvelle transaction
            # Format: DD.MM LIBELLE DD.MM.YY [DEBIT] [CREDIT]
            tx_match = re.match(
                r"^(\d{2}\.\d{2})\s+(.+?)\s+(\d{2}\.\d{2}\.\d{2})\s*"
                r"([\d\s]+[,\.]\d{2})?\s*\.?\s*([\d\s]+[,\.]\d{2})?$",
                line,
            )

            if tx_match:
                # Sauvegarder la transaction précédente
                if current_tx:
                    current_tx.libelle = " ".join(current_libelle_parts)
                    transactions.append(current_tx)

                # Créer nouvelle transaction
                date = tx_match.group(1)
                libelle = tx_match.group(2).strip()
                valeur = tx_match.group(3)
                debit_str = tx_match.group(4)
                credit_str = tx_match.group(5)

                current_tx = Transaction(
                    date=date,
                    libelle=libelle,
                    valeur=valeur,
                    debit=cls._parse_amount(debit_str) if debit_str else None,
                    credit=cls._parse_amount(credit_str) if credit_str else None,
                    raw_text=line,
                    source_file=source_file,
                    bank_type="LCL",
                )
                current_libelle_parts = [libelle]

            elif current_tx:
                # C'est une ligne de continuation du libellé
                # Ignorer les lignes qui ressemblent à des sous-infos
                if not re.match(r"^(LIBELLE|REF\.|ID\.|REF\.MANDAT|BRUT)", line):
                    current_libelle_parts.append(line)

        # Ajouter la dernière transaction
        if current_tx:
            current_tx.libelle = " ".join(current_libelle_parts)
            transactions.append(current_tx)

        return transactions

    @staticmethod
    def _parse_amount(amount_str: str | None) -> Decimal | None:
        """Convertit une chaîne de montant en Decimal."""
        if not amount_str:
            return None
        # Nettoyer: enlever espaces, remplacer virgule par point
        cleaned = amount_str.replace(" ", "").replace(",", ".")
        try:
            return Decimal(cleaned)
        except Exception:
            return None


# =============================================================================
# PARSEUR BNP
# =============================================================================


class BNPParser:
    """Parseur pour les relevés BNP Paribas."""

    HEADER_PATTERNS = [
        r"RELEVEDECOMPTECHEQUES",
        r"RELEVE DE COMPTE CHEQUES",
        r"du\d{1,2}.*au\d{1,2}",
        r"TØl\.Agence",
        r"Tél\.Agence",
        r"RIB\s*:",
        r"IBAN\s*:",
        r"BIC\s*:",
        r"BNPPARIBAS",
        r"mabanque\.bnpparibas",
        r"Vous trouverez",
        r"l'information annuelle",
        r"Fonds de Garantie",
        r"garantiedesdepots\.fr",
        r"Monnaieducompte",
    ]

    FOOTER_PATTERNS = [
        r"P\.\s*\d+/\d+",
        r"3477.*service gratuit",
        r"BNPPARIBASSAaucapital",
        r"RCSParis",
        r"ORIAS",
        r"SCPT\d+",
    ]

    OPERATIONS_HEADER = r"Date\s+Nature\s*des\s*opØrations|Date\s+Nature\s*des\s*opérations"

    @classmethod
    def parse(cls, pdf_path: str | Path) -> ParsedStatement:
        """Parse un relevé BNP et retourne les transactions nettoyées."""
        pdf_path = Path(pdf_path)
        result = ParsedStatement(
            bank_type="BNP",
            source_file=str(pdf_path),
        )

        with pdfplumber.open(pdf_path) as pdf:
            all_text = []

            for page_num, page in enumerate(pdf.pages, 1):
                raw_text = page.extract_text() or ""
                result.raw_pages.append(raw_text)

                if page_num == 1:
                    cls._extract_metadata(raw_text, result)

                cleaned = cls._clean_page(raw_text)
                all_text.append(cleaned)

            full_text = "\n".join(all_text)
            result.transactions = cls._parse_transactions(full_text, str(pdf_path))

        return result

    @classmethod
    def _extract_metadata(cls, text: str, result: ParsedStatement) -> None:
        """Extrait les métadonnées du relevé BNP."""
        # Période (format BNP: du27décembre2022au27janvier2023)
        period_match = re.search(
            r"du(\d{1,2})(\w+)(\d{4})au(\d{1,2})(\w+)(\d{4})", text
        )
        if period_match:
            result.period_start = f"{period_match.group(1)} {period_match.group(2)} {period_match.group(3)}"
            result.period_end = f"{period_match.group(4)} {period_match.group(5)} {period_match.group(6)}"

        # IBAN
        iban_match = re.search(r"IBAN\s*:\s*([A-Z]{2}\d{2}[\s\d\w]+)", text)
        if iban_match:
            result.iban = iban_match.group(1).replace(" ", "")

    @classmethod
    def _clean_page(cls, text: str) -> str:
        """Nettoie une page BNP."""
        lines = text.split("\n")
        cleaned_lines = []
        in_operations = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Détecter le début des opérations
            if re.search(cls.OPERATIONS_HEADER, line, re.IGNORECASE):
                in_operations = True
                continue

            # Détecter aussi "SOLDECREDITEUR" comme début alternatif
            if "SOLDECREDITEUR" in line.upper() or "SOLDE CREDITEUR" in line.upper():
                in_operations = True

            if not in_operations:
                continue

            # Vérifier footers
            is_footer = any(
                re.search(p, line, re.IGNORECASE) for p in cls.FOOTER_PATTERNS
            )
            if is_footer:
                continue

            # Vérifier headers répétés
            is_header = any(
                re.search(p, line, re.IGNORECASE) for p in cls.HEADER_PATTERNS[:5]
            )
            if is_header:
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    @classmethod
    def _parse_transactions(
        cls, text: str, source_file: str
    ) -> list[Transaction]:
        """Parse les transactions BNP."""
        transactions = []
        lines = text.split("\n")
        current_tx = None
        current_libelle_parts = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Format BNP: DD.MM LIBELLE DD.MM DEBIT CREDIT
            tx_match = re.match(
                r"^(\d{2}\.\d{2})\s+(.+?)\s+(\d{2}\.\d{2})\s*"
                r"([\d\s]+[,\.]\d{2})?\s*([\d\s]+[,\.]\d{2})?$",
                line,
            )

            if tx_match:
                if current_tx:
                    current_tx.libelle = " ".join(current_libelle_parts)
                    transactions.append(current_tx)

                date = tx_match.group(1)
                libelle = tx_match.group(2).strip()
                valeur = tx_match.group(3)
                debit_str = tx_match.group(4)
                credit_str = tx_match.group(5)

                current_tx = Transaction(
                    date=date,
                    libelle=libelle,
                    valeur=valeur,
                    debit=cls._parse_amount(debit_str) if debit_str else None,
                    credit=cls._parse_amount(credit_str) if credit_str else None,
                    raw_text=line,
                    source_file=source_file,
                    bank_type="BNP",
                )
                current_libelle_parts = [libelle]

            elif current_tx:
                # Ligne de continuation
                if not line.startswith(("ECH/", "MDT/", "REF/", "LIB/", "ID")):
                    current_libelle_parts.append(line)

        if current_tx:
            current_tx.libelle = " ".join(current_libelle_parts)
            transactions.append(current_tx)

        return transactions

    @staticmethod
    def _parse_amount(amount_str: str | None) -> Decimal | None:
        if not amount_str:
            return None
        cleaned = amount_str.replace(" ", "").replace(",", ".")
        try:
            return Decimal(cleaned)
        except Exception:
            return None


# =============================================================================
# PARSEUR SUMUP
# =============================================================================


class SUMUPParser:
    """Parseur pour les relevés SumUp."""

    HEADER_PATTERNS = [
        r"Des questions",
        r"Centre d'aide",
        r"support\.sumup\.com",
        r"Relevé de compte SumUp",
        r"Date:",
        r"Sélectionnez la période",
        r"Identifiant marchand",
        r"IBAN:",
        r"Créé à:",
        r"N° de carte:",
        r"Paiements crédités",
        r"Paiements débités",
        r"Solde initial",
        r"Solde final",
    ]

    FOOTER_PATTERNS = [
        r"card\.export\.pdf",
        r"address_footer",
        r"legal_footer",
    ]

    COLUMN_HEADER = r"Date de la.*Code de la.*Type de transaction"

    @classmethod
    def parse(cls, pdf_path: str | Path) -> ParsedStatement:
        """Parse un relevé SumUp et retourne les transactions nettoyées."""
        pdf_path = Path(pdf_path)
        result = ParsedStatement(
            bank_type="SUMUP",
            source_file=str(pdf_path),
        )

        with pdfplumber.open(pdf_path) as pdf:
            all_text = []

            for page_num, page in enumerate(pdf.pages, 1):
                raw_text = page.extract_text() or ""
                result.raw_pages.append(raw_text)

                if page_num == 1:
                    cls._extract_metadata(raw_text, result)

                cleaned = cls._clean_page(raw_text)
                all_text.append(cleaned)

            full_text = "\n".join(all_text)
            result.transactions = cls._parse_transactions(full_text, str(pdf_path))

        return result

    @classmethod
    def _extract_metadata(cls, text: str, result: ParsedStatement) -> None:
        """Extrait les métadonnées SumUp."""
        # Période
        period_match = re.search(
            r"Sélectionnez la période.*?:\s*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})",
            text,
        )
        if period_match:
            result.period_start = period_match.group(1)
            result.period_end = period_match.group(2)

        # IBAN
        iban_match = re.search(r"IBAN:\s*([A-Z]{2}\d{2}\w+)", text)
        if iban_match:
            result.iban = iban_match.group(1)

        # Marchand
        merchant_match = re.search(r"Identifiant marchand:\s*(\w+)", text)
        if merchant_match:
            result.account_holder = merchant_match.group(1)

    @classmethod
    def _clean_page(cls, text: str) -> str:
        """Nettoie une page SumUp."""
        lines = text.split("\n")
        cleaned_lines = []
        in_operations = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Détecter l'en-tête des colonnes
            if re.search(cls.COLUMN_HEADER, line, re.IGNORECASE):
                in_operations = True
                continue

            # Alternative: détecter les lignes de transaction par leur format
            if re.match(r"\d{2}/\d{2}/\d{4}", line):
                in_operations = True

            if not in_operations:
                continue

            # Vérifier footers
            is_footer = any(
                re.search(p, line, re.IGNORECASE) for p in cls.FOOTER_PATTERNS
            )
            if is_footer:
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    @classmethod
    def _parse_transactions(
        cls, text: str, source_file: str
    ) -> list[Transaction]:
        """Parse les transactions SumUp."""
        transactions = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Format SumUp: DD/MM/YYYY HH:MM CODE TYPE REFERENCE STATUT DEBITE CREDITE FRAIS SOLDE
            # Simplifié: on cherche date + type + montants
            tx_match = re.match(
                r"^(\d{2}/\d{2}/\d{4})\s+"  # Date
                r"(\d{2}:\d{2})?\s*"  # Heure optionnelle
                r"(\w+)\s+"  # Code transaction
                r"(.+?)\s+"  # Type + Référence
                r"(Approuvé|Entrant|Remboursé|Envoyé par SumUp)\s+"  # Statut
                r"([\d\.]+)\s+"  # Montant débité
                r"([\d\.]+)\s+"  # Montant crédité
                r"([\d\.]+)\s+"  # Frais
                r"([\d\.]+)",  # Solde
                line,
            )

            if tx_match:
                date = tx_match.group(1)
                code = tx_match.group(3)
                type_ref = tx_match.group(4).strip()
                statut = tx_match.group(5)
                debit = tx_match.group(6)
                credit = tx_match.group(7)

                tx = Transaction(
                    date=date,
                    libelle=f"{type_ref} [{statut}]",
                    valeur=code,
                    debit=Decimal(debit) if float(debit) > 0 else None,
                    credit=Decimal(credit) if float(credit) > 0 else None,
                    raw_text=line,
                    source_file=source_file,
                    bank_type="SUMUP",
                )
                transactions.append(tx)

        return transactions


# =============================================================================
# DÉTECTEUR DE TYPE DE BANQUE
# =============================================================================


def detect_bank_type(pdf_path: str | Path) -> str:
    """Détecte automatiquement le type de banque d'un relevé PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0].extract_text() or ""

        if "CREDIT LYONNAIS" in first_page or "LCL" in first_page:
            return "LCL"
        elif "BNPPARIBAS" in first_page or "BNP PARIBAS" in first_page:
            return "BNP"
        elif "SumUp" in first_page or "SUMUP" in first_page:
            return "SUMUP"
        else:
            return "UNKNOWN"


def parse_statement(pdf_path: str | Path) -> ParsedStatement:
    """Parse automatiquement un relevé en détectant son type."""
    bank_type = detect_bank_type(pdf_path)

    if bank_type == "LCL":
        return LCLParser.parse(pdf_path)
    elif bank_type == "BNP":
        return BNPParser.parse(pdf_path)
    elif bank_type == "SUMUP":
        return SUMUPParser.parse(pdf_path)
    else:
        raise ValueError(f"Type de banque non reconnu pour {pdf_path}")
