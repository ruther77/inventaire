#!/usr/bin/env python3
"""
Script d'analyse des relevés bancaires - Version améliorée.

Algorithme 1: Parseurs spécifiques par banque (LCL, BNP, SUMUP)
Algorithme 2: Catégorisation par mots-clés dans 12 catégories

Usage:
    python scripts/analyze_releves.py [dossier]
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pdfplumber


# =============================================================================
# STRUCTURES DE DONNÉES
# =============================================================================


@dataclass
class Transaction:
    """Représente une transaction bancaire extraite."""
    date: str
    libelle: str
    debit: Decimal | None = None
    credit: Decimal | None = None
    valeur: str | None = None
    raw_text: str = ""
    source_file: str = ""
    source_page: int = 0
    bank_type: str = ""
    # Période du relevé d'origine (period_start, period_end) au format DD.MM.YYYY
    statement_period: tuple[str, str] | None = None


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
    total_pages: int = 0
    parsing_errors: list[str] = field(default_factory=list)
    # Soldes d'ouverture par période: {(year, month): Decimal}
    opening_balances: dict[tuple[int, int], Decimal] = field(default_factory=dict)


# =============================================================================
# UTILITAIRES
# =============================================================================


def parse_amount(amount_str: str | None) -> Decimal | None:
    """Convertit une chaîne de montant en Decimal."""
    if not amount_str:
        return None
    # Nettoyer: enlever espaces, points de milliers, remplacer virgule par point
    cleaned = amount_str.strip()
    cleaned = re.sub(r'\s+', '', cleaned)  # Enlever tous les espaces
    cleaned = re.sub(r'\.(?=\d{3})', '', cleaned)  # Enlever points de milliers
    cleaned = cleaned.replace(',', '.')
    cleaned = cleaned.rstrip('.')  # Enlever point final (indicateur débit LCL)
    try:
        val = Decimal(cleaned)
        return val if val != 0 else None
    except (InvalidOperation, ValueError):
        return None


def clean_libelle(text: str) -> str:
    """Nettoie un libellé de transaction."""
    # Supprimer les retours à la ligne multiples
    text = re.sub(r'\s+', ' ', text)
    # Supprimer les caractères de contrôle
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    return text.strip()


# =============================================================================
# PARSEUR LCL - Version 2 basée sur les positions X
# =============================================================================


class LCLParser:
    """
    Parseur pour les relevés LCL (Crédit Lyonnais) - Version 2.

    Utilise les positions X des mots dans le PDF pour classifier
    correctement les montants en DEBIT ou CREDIT.

    Colonnes LCL (positions en points):
    - DATE: x ≈ 41-66
    - LIBELLE: x ≈ 100-350
    - VALEUR: x ≈ 364-401
    - DEBIT: x ≈ 430-480
    - CREDIT: x ≈ 500-550
    """

    # Seuil de position X pour distinguer DEBIT / CREDIT
    CREDIT_THRESHOLD = 485

    @classmethod
    def parse(cls, pdf_path: str | Path) -> ParsedStatement:
        """Parse un relevé LCL complet."""
        pdf_path = Path(pdf_path)
        result = ParsedStatement(
            bank_type="LCL",
            source_file=str(pdf_path),
        )

        with pdfplumber.open(pdf_path) as pdf:
            result.total_pages = len(pdf.pages)
            current_period = None
            seen_periods = set()

            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""

                # Extraire métadonnées
                if page_num == 1:
                    cls._extract_metadata(text, result)

                # Détecter la période de cette page
                period_match = re.search(
                    r"du\s+(\d{2}\.\d{2}\.\d{4})\s+au\s+(\d{2}\.\d{2}\.\d{4})", text
                )
                if period_match:
                    new_period = (period_match.group(1), period_match.group(2))

                    if new_period not in seen_periods:
                        seen_periods.add(new_period)
                        period_end = new_period[1]
                        year = int(period_end[6:10])
                        month = int(period_end[3:5])

                        # Solde d'ouverture
                        solde_match = re.search(
                            r"ANCIEN\s+SOLDE\s+([\d\s]+[,\.]\d{2})", text
                        )
                        if solde_match:
                            solde = parse_amount(solde_match.group(1))
                            if solde is not None:
                                result.opening_balances[(year, month)] = solde

                    current_period = new_period

                # Parser les transactions de cette page
                page_transactions = cls._parse_page_position_based(
                    page, page_num, current_period
                )
                result.transactions.extend(page_transactions)

        return result

    @classmethod
    def _extract_metadata(cls, text: str, result: ParsedStatement) -> None:
        """Extrait période, IBAN, titulaire."""
        period_match = re.search(
            r"du\s+(\d{2}\.\d{2}\.\d{4})\s+au\s+(\d{2}\.\d{2}\.\d{4})", text
        )
        if period_match:
            result.period_start = period_match.group(1)
            result.period_end = period_match.group(2)

        iban_match = re.search(r"IBAN\s*:\s*([A-Z]{2}\d{2}[\s\dA-Z]+)", text)
        if iban_match:
            result.iban = re.sub(r'\s+', '', iban_match.group(1))

        holder_match = re.search(
            r"Titulaire du compte[-\s]*([\w\s]+?)(?:\d|---|----|PARIS|75)", text
        )
        if holder_match:
            result.account_holder = holder_match.group(1).strip()

    @classmethod
    def _parse_page_position_based(
        cls, page, page_num: int, period: tuple | None
    ) -> list[Transaction]:
        """
        Parse une page en utilisant les positions X des mots.

        Stratégie:
        1. Grouper les mots par ligne (Y)
        2. Pour chaque ligne, fusionner les mots adjacents dans la zone montant
        3. Classifier débit/crédit par position X
        """
        transactions = []

        # Extraire tous les mots avec positions
        words = page.extract_words(
            x_tolerance=2,
            y_tolerance=2,
            keep_blank_chars=False,
        )

        if not words:
            return transactions

        # Grouper par ligne (y arrondi)
        lines_by_y = defaultdict(list)
        for w in words:
            y_key = round(w['top'])
            lines_by_y[y_key].append(w)

        # Fusionner les lignes proches (différence y < 5)
        merged_lines = []
        sorted_ys = sorted(lines_by_y.keys())
        current_line = []
        current_y = None

        for y in sorted_ys:
            if current_y is None or abs(y - current_y) < 5:
                current_line.extend(lines_by_y[y])
                current_y = y if current_y is None else current_y
            else:
                if current_line:
                    merged_lines.append((current_y, current_line))
                current_line = list(lines_by_y[y])
                current_y = y

        if current_line:
            merged_lines.append((current_y, current_line))

        # Patterns
        date_pattern = re.compile(r'^(\d{2}\.\d{2})$')
        valeur_pattern = re.compile(r'^(\d{2}\.\d{2}\.\d{2})$')

        # État pour les transactions multi-lignes
        current_tx = None
        current_libelle_parts = []

        for y, line_words in merged_lines:
            # Trier par X
            line_words = sorted(line_words, key=lambda w: w['x0'])

            # Ignorer les lignes vides ou headers/footers
            line_text = ' '.join(w['text'] for w in line_words)
            if cls._is_header_footer(line_text):
                continue

            # Ignorer les lignes SOLDE (ancien solde, solde intermédiaire, etc.)
            if 'SOLDE' in line_text.upper():
                continue

            # Chercher une date au début de la ligne
            first_word = line_words[0] if line_words else None
            has_date = first_word and date_pattern.match(first_word['text'])

            if has_date:
                # Sauvegarder la transaction précédente
                if current_tx:
                    current_tx.libelle = clean_libelle(' '.join(current_libelle_parts))
                    if current_tx.debit or current_tx.credit:
                        transactions.append(current_tx)

                # Nouvelle transaction
                date_str = first_word['text']

                # Extraire année de la période
                tx_year = None
                if period:
                    period_end = period[1]  # DD.MM.YYYY
                    period_year = int(period_end[6:10])
                    period_month = int(period_end[3:5])
                    tx_month = int(date_str[3:5])
                    tx_year = period_year - 1 if tx_month > period_month + 1 else period_year

                date_with_year = f"{date_str}.{tx_year}" if tx_year else date_str

                # Identifier les zones de montants
                # Zone DEBIT: X ≈ 430-480
                # Zone CREDIT: X ≈ 500-550
                debit_parts = []
                credit_parts = []
                valeur_str = None
                libelle_words = []
                has_dot_indicator = False

                for w in line_words[1:]:  # Skip date
                    text = w['text']
                    x_pos = w['x0']

                    # Point final isolé = indicateur débit
                    if text == '.':
                        has_dot_indicator = True
                        continue

                    # Date valeur (format DD.MM.YY)
                    if valeur_pattern.match(text):
                        valeur_str = text
                        continue

                    # Zone CREDIT (X >= 500)
                    if x_pos >= 500:
                        if cls._is_amount_part(text):
                            credit_parts.append(text)
                        continue

                    # Zone DEBIT (X >= 430 et < 500)
                    if x_pos >= 430:
                        if cls._is_amount_part(text):
                            debit_parts.append(text)
                        continue

                    # Zone libellé (X < 400)
                    if x_pos < 400:
                        libelle_words.append(text)

                # Reconstruire les montants
                debit_val = None
                credit_val = None

                if credit_parts:
                    credit_str = ''.join(credit_parts)
                    credit_val = parse_amount(credit_str)

                if debit_parts:
                    debit_str = ''.join(debit_parts)
                    debit_val = parse_amount(debit_str)

                # Si un seul montant trouvé, utiliser le point indicateur ou le libellé
                if debit_val and not credit_val and not has_dot_indicator:
                    # Vérifier si c'est un crédit par le libellé
                    libelle_str = ' '.join(libelle_words).upper()
                    credit_keywords = ['REMISE', 'VERSEMENT', 'VIR SEPA RECU', 'AVOIR',
                                      'LCL A LA CARTE', 'VRST', 'ENCAISSEMENT']
                    if any(kw in libelle_str for kw in credit_keywords):
                        credit_val = debit_val
                        debit_val = None

                current_tx = Transaction(
                    date=date_with_year,
                    libelle='',
                    debit=debit_val,
                    credit=credit_val,
                    valeur=valeur_str,
                    raw_text=line_text,
                    source_file='',
                    source_page=page_num,
                    bank_type="LCL",
                    statement_period=period,
                )
                current_libelle_parts = libelle_words

            elif current_tx:
                # Ligne de continuation - ajouter au libellé
                for w in line_words:
                    text = w['text']
                    x_pos = w['x0']

                    if x_pos > 400:
                        continue
                    if text in ('.', 'Page', 'www', 'IBAN'):
                        continue
                    if text.startswith(('LIBELLE:', 'REF.', 'ID.', 'MDT/')):
                        break

                    current_libelle_parts.append(text)

        # Dernière transaction
        if current_tx:
            current_tx.libelle = clean_libelle(' '.join(current_libelle_parts))
            if current_tx.debit or current_tx.credit:
                transactions.append(current_tx)

        return transactions

    @classmethod
    def _is_amount_part(cls, text: str) -> bool:
        """Vérifie si un texte fait partie d'un montant."""
        # Peut être un chiffre seul (partie milliers) ou un montant complet
        cleaned = text.replace(' ', '').replace('.', '')
        if cleaned.isdigit():
            return True
        if re.match(r'^\d+,\d{2}$', cleaned):
            return True
        return False

    @classmethod
    def _is_header_footer(cls, line_text: str) -> bool:
        """Détermine si une ligne est un header/footer à ignorer."""
        skip_patterns = [
            'RELEVE DE COMPTE', "RELEVE D'IDENTITE", 'CREDIT LYONNAIS',
            'Page ', 'www.LCL', 'www.amf', 'SIREN', 'ORIAS',
            'Titulaire du compte', 'Domiciliation', 'Votre conseiller',
            'IBAN', 'BIC', 'Indicatif', 'Références bancaires',
            'garantiedesdepots', 'médiateur', 'mediateurducredit',
            'Conditions Générales', 'Dispositions', 'Ce document ne vaut',
            'Les sommes figurant', 'reprisdansles',
            'DATE LIBELLE VALEUR', 'TOTAUX',
        ]
        upper = line_text.upper()
        return any(p.upper() in upper for p in skip_patterns)


# =============================================================================
# PARSEUR BNP - Amélioré
# =============================================================================


class BNPParser:
    """
    Parseur pour les relevés BNP Paribas - Version 2 basée sur les positions X.

    Format BNP:
    - Date opération: X ≈ 28
    - Libellé: X ≈ 68
    - Date valeur: X ≈ 312
    - Zone DEBIT: X ≈ 418-480
    - Zone CREDIT: X ≥ 500
    """

    # Seuils de position X pour BNP
    X_DATE_VAL_MIN = 280     # Date valeur commence vers X=312
    X_DATE_VAL_MAX = 360     # Date valeur finit avant X=360
    X_DEBIT_MIN = 380        # Zone débit commence à X=380
    X_CREDIT_THRESHOLD = 480 # Seuil: < 480 = débit, >= 480 = crédit

    @classmethod
    def parse(cls, pdf_path: str | Path) -> ParsedStatement:
        pdf_path = Path(pdf_path)
        result = ParsedStatement(
            bank_type="BNP",
            source_file=str(pdf_path),
        )

        # Mois français pour conversion
        mois_fr = {
            'janvier': 1, 'fØvrier': 2, 'février': 2, 'mars': 3, 'avril': 4,
            'mai': 5, 'juin': 6, 'juillet': 7, 'aoØt': 8, 'août': 8,
            'septembre': 9, 'octobre': 10, 'novembre': 11, 'dØcembre': 12, 'décembre': 12
        }

        with pdfplumber.open(pdf_path) as pdf:
            result.total_pages = len(pdf.pages)
            seen_periods = set()

            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""

                if page_num == 1:
                    cls._extract_metadata(text, result)

                # Extraire la période de cette page
                period_match = re.search(
                    r"du(\d{1,2})(\w+?)(\d{4})au(\d{1,2})(\w+?)(\d{4})", text
                )
                if period_match:
                    day_end = int(period_match.group(4))
                    month_name = period_match.group(5).lower()
                    year_end = int(period_match.group(6))
                    month_end = mois_fr.get(month_name, 0)

                    if month_end and (year_end, month_end) not in seen_periods:
                        seen_periods.add((year_end, month_end))

                        solde_match = re.search(
                            r"SOLDE(CREDITEUR|DEBITEUR)AU\d+\.\d+\.\d+\s+([\d\s,]+)",
                            text
                        )
                        if solde_match:
                            solde_type = solde_match.group(1)
                            solde_str = solde_match.group(2).strip()
                            solde = parse_amount(solde_str)
                            if solde is not None:
                                if solde_type == "DEBITEUR":
                                    solde = -solde
                                result.opening_balances[(year_end, month_end)] = solde

                # Parser avec les positions X
                transactions = cls._parse_page_position_based(page, page_num, str(pdf_path))
                result.transactions.extend(transactions)

        return result

    @classmethod
    def _extract_metadata(cls, text: str, result: ParsedStatement) -> None:
        """Extrait les métadonnées BNP."""
        period_match = re.search(
            r"du(\d{1,2})(\w+?)(\d{4})au(\d{1,2})(\w+?)(\d{4})", text
        )
        if period_match:
            result.period_start = f"{period_match.group(1)} {period_match.group(2)} {period_match.group(3)}"
            result.period_end = f"{period_match.group(4)} {period_match.group(5)} {period_match.group(6)}"

        iban_match = re.search(r"IBAN\s*:\s*([A-Z]{2}\d{2}[\s\dA-Z]+)", text)
        if iban_match:
            result.iban = re.sub(r'\s+', '', iban_match.group(1))

    @classmethod
    def _is_amount_part(cls, text: str) -> bool:
        """Vérifie si le texte est une partie de montant."""
        text = text.strip()
        if not text:
            return False
        # Chiffres purs (milliers séparés)
        if text.replace(' ', '').isdigit():
            return True
        # Format avec virgule: 500,00
        if re.match(r'^\d[\d\s]*,\d{2}$', text):
            return True
        return False

    @classmethod
    def _is_date(cls, text: str) -> bool:
        """Vérifie si le texte est une date DD.MM."""
        return bool(re.match(r'^\d{2}\.\d{2}$', text.strip()))

    @classmethod
    def _is_header_footer(cls, text: str) -> bool:
        """Vérifie si le texte est un header/footer à ignorer."""
        patterns = [
            "RELEVEDECOMPTE", "RELEVE DE COMPTE", "BNPPARIBASSAaucapital",
            "RCSParis", "ORIAS", "mabanque.bnpparibas", "P.",
            "COMPTECOURANT", "30004", "00994", "94",
        ]
        return any(p in text for p in patterns)

    @classmethod
    def _parse_page_position_based(
        cls, page, page_num: int, source_file: str
    ) -> list[Transaction]:
        """Parse une page BNP en utilisant les positions X des mots."""
        transactions = []
        words = page.extract_words()

        # Grouper les mots par ligne (même Y à 3px près)
        lines_dict = {}
        for w in words:
            y_key = round(w['top'] / 3) * 3  # Grouper par tranches de 3px
            if y_key not in lines_dict:
                lines_dict[y_key] = []
            lines_dict[y_key].append({
                'text': w['text'],
                'x0': w['x0'],
                'top': w['top']
            })

        # Trier les lignes par Y, puis les mots par X
        for y_key in sorted(lines_dict.keys()):
            line_words = sorted(lines_dict[y_key], key=lambda w: w['x0'])

            # Vérifier si la ligne commence par une date (transaction)
            if not line_words:
                continue

            first_word = line_words[0]
            if not cls._is_date(first_word['text']):
                continue

            # Ignorer les headers/footers
            full_text = ' '.join(w['text'] for w in line_words)
            if cls._is_header_footer(full_text):
                continue

            # Extraire les composants selon la position X
            date_op = first_word['text']
            date_val = None
            libelle_parts = []
            debit_parts = []
            credit_parts = []

            for w in line_words[1:]:  # Skip la première (date_op)
                x_pos = w['x0']
                text = w['text']

                # Zone DATE VALEUR (X entre 280 et 360)
                if cls.X_DATE_VAL_MIN <= x_pos < cls.X_DATE_VAL_MAX:
                    if cls._is_date(text):
                        date_val = text
                    continue

                # Zone MONTANTS (X >= 380)
                if x_pos >= cls.X_DEBIT_MIN:
                    if cls._is_amount_part(text):
                        # CREDIT si X >= 480, sinon DEBIT
                        if x_pos >= cls.X_CREDIT_THRESHOLD:
                            credit_parts.append(text)
                        else:
                            debit_parts.append(text)
                    continue

                # Zone LIBELLE (tout le reste)
                if not cls._is_header_footer(text):
                    libelle_parts.append(text)

            # Construire les montants
            debit_str = ' '.join(debit_parts) if debit_parts else None
            credit_str = ' '.join(credit_parts) if credit_parts else None

            debit = parse_amount(debit_str)
            credit = parse_amount(credit_str)

            # Créer la transaction si on a au moins un montant
            if debit or credit:
                libelle = clean_libelle(' '.join(libelle_parts))

                tx = Transaction(
                    date=date_op,
                    libelle=libelle,
                    valeur=date_val,
                    debit=debit,
                    credit=credit,
                    raw_text=full_text,
                    source_file=source_file,
                    source_page=page_num,
                    bank_type="BNP",
                )
                transactions.append(tx)

        return transactions


# =============================================================================
# PARSEUR SUMUP - Amélioré
# =============================================================================


class SUMUPParser:
    """
    Parseur pour les relevés SumUp - Version 2 basée sur les positions X.

    Format SumUp (positions X observées):
    - Date: X ≈ 43
    - Code transaction: X ≈ 111
    - Type: X ≈ 200-280
    - Référence: X ≈ 318-436
    - Statut: X ≈ 495
    - Débit: X ≈ 583
    - Crédit: X ≈ 643
    - Frais: X ≈ 702
    - Solde: X ≈ 746
    """

    # Seuils de position X pour SumUp
    X_CODE = 100           # Code transaction
    X_TYPE = 190           # Type de transaction
    X_REF = 300            # Référence
    X_STATUT = 480         # Statut
    X_DEBIT = 560          # Zone débit
    X_CREDIT = 620         # Zone crédit
    X_FRAIS = 680          # Zone frais
    X_SOLDE = 720          # Zone solde

    @classmethod
    def parse(cls, pdf_path: str | Path) -> ParsedStatement:
        pdf_path = Path(pdf_path)
        result = ParsedStatement(
            bank_type="SUMUP",
            source_file=str(pdf_path),
        )

        with pdfplumber.open(pdf_path) as pdf:
            result.total_pages = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""

                if page_num == 1:
                    cls._extract_metadata(text, result)

                # Parser avec les positions X
                transactions = cls._parse_page_position_based(page, page_num, str(pdf_path))
                result.transactions.extend(transactions)

        return result

    @classmethod
    def _extract_metadata(cls, text: str, result: ParsedStatement) -> None:
        """Extrait les métadonnées SumUp."""
        period_match = re.search(
            r"période.*?:\s*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})",
            text, re.IGNORECASE
        )
        if period_match:
            result.period_start = period_match.group(1)
            result.period_end = period_match.group(2)

        iban_match = re.search(r"IBAN:\s*([A-Z]{2}\d{2}\w+)", text)
        if iban_match:
            result.iban = iban_match.group(1)

        merchant_match = re.search(r"Identifiant marchand:\s*(\w+)", text)
        if merchant_match:
            result.account_holder = f"SUMUP-{merchant_match.group(1)}"

    @classmethod
    def _is_amount(cls, text: str) -> bool:
        """Vérifie si le texte est un montant."""
        text = text.strip()
        if not text:
            return False
        # Format: 0.00 ou 123.45 ou 1,234.56
        return bool(re.match(r'^[\d,]+\.\d{2}$', text.replace(',', '')))

    @classmethod
    def _is_date(cls, text: str) -> bool:
        """Vérifie si le texte est une date DD/MM/YYYY."""
        return bool(re.match(r'^\d{2}/\d{2}/\d{4}$', text.strip()))

    @classmethod
    def _parse_page_position_based(
        cls, page, page_num: int, source_file: str
    ) -> list[Transaction]:
        """Parse une page SumUp en utilisant les positions X."""
        transactions = []
        words = page.extract_words()

        # Grouper par ligne Y (à 3px près)
        lines_dict = {}
        for w in words:
            y_key = round(w['top'] / 3) * 3
            if y_key not in lines_dict:
                lines_dict[y_key] = []
            lines_dict[y_key].append({
                'text': w['text'],
                'x0': w['x0'],
                'top': w['top']
            })

        for y_key in sorted(lines_dict.keys()):
            line_words = sorted(lines_dict[y_key], key=lambda w: w['x0'])

            if not line_words:
                continue

            # Vérifier si la ligne commence par une date
            first_word = line_words[0]
            if not cls._is_date(first_word['text']):
                continue

            # Extraire les composants par position X
            date_str = first_word['text']
            code = None
            type_parts = []
            ref_parts = []
            statut = None
            debit = None
            credit = None

            for w in line_words[1:]:
                x_pos = w['x0']
                text = w['text']

                # Zone CODE (X >= 100 et < 190)
                if cls.X_CODE <= x_pos < cls.X_TYPE:
                    if re.match(r'^[A-Z0-9]{8,}$', text):
                        code = text
                    continue

                # Zone TYPE (X >= 190 et < 300)
                if cls.X_TYPE <= x_pos < cls.X_REF:
                    type_parts.append(text)
                    continue

                # Zone REFERENCE (X >= 300 et < 480)
                if cls.X_REF <= x_pos < cls.X_STATUT:
                    ref_parts.append(text)
                    continue

                # Zone STATUT (X >= 480 et < 560)
                if cls.X_STATUT <= x_pos < cls.X_DEBIT:
                    if text in ('Approuvé', 'Entrant', 'Remboursé', 'Envoyé'):
                        statut = text
                    continue

                # Zone DEBIT (X >= 560 et < 620)
                if cls.X_DEBIT <= x_pos < cls.X_CREDIT:
                    if cls._is_amount(text):
                        val = Decimal(text.replace(',', ''))
                        if val > 0:
                            debit = val
                    continue

                # Zone CREDIT (X >= 620 et < 680)
                if cls.X_CREDIT <= x_pos < cls.X_FRAIS:
                    if cls._is_amount(text):
                        val = Decimal(text.replace(',', ''))
                        if val > 0:
                            credit = val
                    continue

            # Créer la transaction si on a un montant
            if debit or credit:
                type_str = ' '.join(type_parts)
                ref_str = ' '.join(ref_parts)
                libelle = f"{type_str} {ref_str}".strip()
                if statut and statut != "Approuvé":
                    libelle += f" [{statut}]"

                tx = Transaction(
                    date=date_str,
                    libelle=clean_libelle(libelle),
                    valeur=code,
                    debit=debit,
                    credit=credit,
                    raw_text=' '.join(w['text'] for w in line_words),
                    source_file=source_file,
                    source_page=page_num,
                    bank_type="SUMUP",
                )
                transactions.append(tx)

        return transactions


# =============================================================================
# DÉTECTION ET PARSING
# =============================================================================


def detect_bank_type(pdf_path: str | Path) -> str:
    """Détecte automatiquement le type de banque."""
    with pdfplumber.open(pdf_path) as pdf:
        # Lire les 2 premières pages pour plus de fiabilité
        text = ""
        for page in pdf.pages[:2]:
            text += (page.extract_text() or "") + "\n"

        text_upper = text.upper()

        if "CREDIT LYONNAIS" in text_upper or "LCL.FR" in text_upper or "CRLYFRPP" in text_upper:
            return "LCL"
        elif "BNPPARIBAS" in text_upper or "BNP PARIBAS" in text_upper:
            return "BNP"
        elif "SUMUP" in text_upper:
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
        # Tenter LCL par défaut
        result = ParsedStatement(
            bank_type="UNKNOWN",
            source_file=str(pdf_path),
        )
        result.parsing_errors.append(f"Type de banque non reconnu")
        return result


# =============================================================================
# LES 12 CATÉGORIES - Mots-clés enrichis
# =============================================================================

CATEGORIES = {
    "encaissements": {
        "name": "Encaissements",
        "keywords": [
            # Encaissements CB/Carte
            "REMISE CB", "REMISE CARTE", "ENCAISSEMENT",
            "VERSEMENT ALS", "VERSEMENT ESPECES", "VERSEMENT",
            "VRSTESPECESAUTOMATE", "VRST ESPECES",
            # Virements reçus
            "VIREMENT RECU", "VIR SEPA RECU", "VIRSEPARECU", "VIR INST",
            "VIRCPTEACPTERECU", "Virement entrant",
            # SumUp
            "Paiement entrant", "SUMUP PID", "PAYOUT",
            # Autres
            "REGLEMENT CLIENT", "CREDIT", "AVOIR",
            "REMBT", "REMBTPRLV",  # Remboursement de prélèvement
            # Remises de chèques
            "REM CHQ", "REMISECHEQUES", "REM CHQ CAE",
        ],
    },
    "achats_fournisseurs": {
        "name": "Achats et frais fournisseurs",
        "keywords": [
            # Grossistes alimentaires
            "METRO", "METRO CASH", "METRO FRANCE", "PROMOCASH", "CARREFOUR", "TRANSGOURMET",
            "BRAKE FRANCE", "SYSCO", "DAVIGEL", "POMONA",
            "EUROCIEL", "TAIYAT", "HAUDECOEUR", "ETSHAUDECOEUR",
            "PRLV SEPA METRO",  # METRO via prélèvement
            # Commerces alimentaires / Fournisseurs
            "GNANAM", "EXOTI", "ETHAN",
            "BOUCH", "BVS", "BOUCH BVS", "BOUCHERIE",  # Boucher
            "PRIMEUR", "POISSONNIER", "FROMAGERIE", "BOULANGERIE",
            # Achats CB génériques
            "CB55", "CB12", "CB1755",  # Préfixes CB LCL
            "PAIEMENT POS", "PAIEMENT CB",
            "FACTURE(S)CARTE", "FACTURECARTE",  # BNP factures carte
            "Paiement en ligne",  # SumUp achats
            # Magasins
            "CENTRAKOR", "SAINT MAXIMO", "PICARD", "LIDL", "ALDI",
            "LECLERC", "AUCHAN", "INTERMARCHE",
            "PRIMARKO", "PRIMARK",  # Achats vestimentaire
            "H&M", "ZARA", "ACTION", "ELCORTEINGLES", "CETA",  # Autres magasins
            "SUMUP *LINCONT",  # Paiements SumUp internes
            "BRICO",  # Bricolage
            # Restauration rapide / commerces
            "KFC", "MACDONALDS", "MCDONALDS", "BURGER KING",
            "MARIONNAUD", "IKEA", "LEROYMERLIN", "LEROY MERLIN",
            "MERCADONA", "ROYALAIRMAROC",
            # Fitness
            "NEONESS", "PRLVSEPANEONESS",
            # Voyages/Loisirs
            "PALAISDURIRE", "ADAMAX", "APRR", "AVIA",
            # Virements étrangers
            "VIRETRANGERRECU",
            # Remboursements CB
            "REMBOURSTCB",
            # Services en ligne
            "PAYPAL", "PAYPALEUROPE",
            "AMAZON", "AMAZON PAYMENTS",
            # Fitness/Autres achats
            "BASICFIT", "BASIC-FIT",
            # Énergie/Gaz pro
            "GAZELENERGIE", "GAZEL",
            "ENGIE", "GAZPROM", "TOTALE ELEC",  # Énergie
            "Paiement POS", "Paiement en ligne",  # Paiements SumUp fournisseurs
            "TAI YAT", "TAIYAT",  # Fournisseur
            "dhgate",  # Achats en ligne
            "CARREFOURBANQUE",  # Services bancaires Carrefour
        ],
    },
    "salaires_remunerations": {
        "name": "Salaires & rémunérations",
        "keywords": [
            "SALAIRE", "REMUNERATION", "PAIE", "VIR SALAIRE",
            "PRIME", "AVANCE", "ACOMPTE", "INDEMNITE", "CONGES",
            "VIREMENT PERMANENT", "VIRPERM",
        ],
    },
    "charges_sociales": {
        "name": "Charges sociales",
        "keywords": [
            "URSSAF", "URSSAF D ILE", "URSSAF D'ILE", "COTISATION SOCIALE", "CHARGES SOCIALES",
            "RETRAITE", "PREVOYANCE", "MUTUELLE SANTE",
            "CPAM", "POLE EMPLOI", "ASSEDIC",
            "FORMATION PRO", "OPCO", "ORGANISME FORMATION",
            "PRLV SEPA URSSAF",  # URSSAF via prélèvement
            "KLESIA",  # Caisse retraite
        ],
    },
    "impots_taxes": {
        "name": "Impôts & taxes",
        "keywords": [
            "IMPOT", "TAXE", "TVA", "CFE", "CVAE",
            "TRESOR PUBLIC", "DGFIP", "DIRECTION GENERALE FINANCES",
            "CONTRIBUTION", "PRELEVEMENT SOURCE", "PAS ",
            "TAXE FONCIERE", "TAXE HABITATION",
        ],
    },
    "frais_generaux": {
        "name": "Frais généraux",
        "keywords": [
            # Frais bancaires
            "COMMISSION", "FRAIS TENUE", "FRAIS GESTION",
            "AGIOS", "ABON LCL", "LCL ACCESS", "ABONNEMENT",
            "RESULTAT ARRETE", "ARRETE COMPTE",
            "COTISATION CARTE", "COTISATION CB",
            "COTISATION MENSUELLE", "COTISATION DE VOTRE",
            "TRAIT.IRREG", "LCL A LA CARTE",
            "OPTION PRO",
            # Fournitures
            "FOURNITURES", "BUREAU VALLEE", "STAPLES", "OFFICE DEPOT",
            # Nettoyage/Entretien
            "NETTOYAGE", "ENTRETIEN", "HYGIENE", "MENAGE",
            # Restauration
            "RESTAURANT", "DEJEUNER", "REPAS",
            # Sécurité
            "SPB", "SECTOR ALARM",
            # Chèques
            "CHQ.", "CHEQUE", "REM CHQ",
            # Opérations bancaires
            "BLOCAGE", "DEBLOC", "FRAIS CODE SECRET",
            "FRAIS SAISIE", "FRAIS DOSSIER",
            "COTIS CARTE", "DEPOT", "REAPRO",
            "COTISATION", "PAIEMENT",
            # NOTE: NE PAS mettre "PRLV SEPA" ici car trop générique
            # Les PRLV sont catégorisés par leur destinataire (METRO, URSSAF, etc.)
        ],
    },
    "transport_deplacement": {
        "name": "Transport & déplacement",
        "keywords": [
            # Transport public
            "SNCF", "RATP", "NAVIGO", "TRANSILIEN",
            # VTC/Taxi
            "UBER", "BOLT", "KAPTEN", "TAXI", "FREE NOW",
            # Carburant / Recharge électrique
            "TOTAL", "TOTALENERGIES", "SHELL", "BP ", "ESSO",
            "CARBURANT", "ESSENCE", "GASOIL", "DIESEL",
            "ELECTRA", "IONITY", "CHARGING",  # Bornes recharge
            # Parking/Péage
            "PARKING", "PEAGE", "AUTOROUTE", "VINCI", "SANEF",
            "ASF", "COFIROUTE", "DYNEFF", "CEDIP",  # Péages/Stations autoroute
            # Livraison
            "RELAIS COLIS", "CHRONOPOST", "COLISSIMO", "LA POSTE",
            "DHL", "UPS", "FEDEX", "TNT",
            # Location véhicule
            "HERTZ", "AVIS", "EUROPCAR", "SIXT",
            # Hôtels
            "HOTEL", "IBIS", "HOTELIBIS",
        ],
    },
    "immobilisations_investissements": {
        "name": "Immobilisations & investissements",
        "keywords": [
            "EQUIPEMENT", "MATERIEL", "MACHINE", "MOBILIER",
            "AMENAGEMENT", "TRAVAUX", "INSTALLATION", "RENOVATION",
            "CAISSE ENREGISTREUSE", "ORDINATEUR", "ECRAN", "IMPRIMANTE",
            "ELECTROMENAGER", "REFRIGERATEUR", "CONGELATEUR",
        ],
    },
    "loyer_immobilier": {
        "name": "Loyer & immobilier",
        "keywords": [
            "LOYER", "BAIL", "LOCATION LOCAL",
            "CHARGES LOCATIVES", "SYNDIC", "COPROPRIETE",
            "FONCIER", "RESIDENCE",
            "PREFILOC", "CREDIT BAIL",
            "ECHEANCE PRET", "ECHEANCEPRET", "PRET IMMOBILIER", "EMPRUNT IMMO",
        ],
    },
    "marketing_communication": {
        "name": "Marketing & communication",
        "keywords": [
            "PUBLICITE", "PUB ", "MARKETING", "COMMUNICATION",
            "FLYER", "AFFICHE", "CARTE VISITE", "IMPRIMERIE",
            "SITE WEB", "GOOGLE ADS", "FACEBOOK", "INSTAGRAM", "META",
            "RESEAUX SOCIAUX", "INFLUENCEUR",
        ],
    },
    "frais_financiers": {
        "name": "Frais financiers",
        "keywords": [
            "INTERET", "INTERETS DEBITEURS", "AGIOS",
            "FRAIS FINANCIERS", "DECOUVERT",
            "PRLV IMPAYE", "REJET", "COM PRLV IMPAYE",
            "COMMISSIONS SUR REMISE",  # Commissions CB
            "FRAIS BANCAIRES",
            "SAISIEADMINISTRATIVE", "SAISIE ADMINISTRATIVE",  # Saisies/blocages
            "REGUL", "REG ",  # Régularisations bancaires
            "*COMMISSIONS",  # Commissions BNP
            "FRAIS",  # Frais génériques
        ],
    },
    "informatique_telecom": {
        "name": "Informatique & télécom",
        "keywords": [
            # Opérateurs
            "ORANGE", "SFR", "BOUYGUES TELECOM", "FREE MOBILE", "FREE TELECOM",
            "TELEPHONE", "MOBILE", "INTERNET", "FIBRE",
            # FAI/Services
            "IMAGINER", "OVH", "AMAZON WEB", "AWS",
            # Logiciels
            "MICROSOFT", "GOOGLE", "APPLE", "ADOBE",
            "LOGICIEL", "LICENCE", "SAAS",
            # Streaming (usage pro possible)
            "LEBARA", "CRUNCHYROLL", "NETFLIX", "SPOTIFY",
        ],
    },
    "remboursements_clients": {
        "name": "Remboursements clients & litiges",
        "keywords": [
            "REMBOURSEMENT", "REMBOURSER", "REMB ",
            "AVOIR CLIENT", "ANNULATION",
            "LITIGE", "CONTENTIEUX", "REFUND",
            "RETOUR MARCHANDISE",
        ],
    },
    "prestations_externes": {
        "name": "Prestations externes",
        "keywords": [
            "PRESTATION", "HONORAIRES", "COMPTABLE", "EXPERT COMPTABLE",
            "AVOCAT", "NOTAIRE", "HUISSIER",
            "CONSULTANT", "CONSEIL", "AUDIT",
            "SECURITE", "GARDIENNAGE", "SURVEILLANCE",
            "HMD AUDIT",  # Spécifique trouvé dans les relevés
        ],
    },
    "assurance_vehicule": {
        "name": "Assurance véhicule & vie",
        "keywords": [
            "ASSURANCE VEHICULE", "ASSURANCE AUTO", "ASSURANCE VOITURE",
            "CARDIF", "CARDIFASSURANCEVIE", "CARDIFIARD",
            "MACIF", "MAIF", "MATMUT", "ALLIANZ",
            "APRIL", "APRILPARTENAIRES",
            "ABEILLE", "ABEILLEVIE",
            "SWISSLIFE", "SWISS LIFE",
            "PRLVSEPACARDIF",  # Prélèvement Cardif
            "ASSURANCE LCL", "PACIFICA", "MULTIRISQUE",  # Assurances LCL
        ],
    },
    "virements_internes": {
        "name": "Virements internes & transferts",
        "keywords": [
            "VIRTCPTEACPTE", "VIR CPTE A CPTE",
            "VIREMENT INTERNE", "TRANSFERT",
            "Virement sortant", "VIREMENT EMIS",
            "VIR SEPA", "VIRSEPARECU",  # Virements SEPA
            "L INCONTOURNABLE", "NOUTAM", "LINCONTOURNABL",  # Entités internes
            "Retrait au distributeur",  # Retraits DAB
            "RETRAITCARTEESPECES", "RETRAIT CARTE", "RETRAITDAB",  # Retraits BNP
            "CB1755 RETRAIT", "RETRAIT",  # Retraits CB LCL
            "VIRSCTINSTRECU", "VIRSCTINSTEMIS",  # Virements instantanés
            "VIRCPTEACPTEEMIS", "VIREMENTSEPAEMIS",  # Virements BNP émis
            "LIVRETA", "EPARGNE",  # Virements épargne
            "ALIMENTATION COMPTE",  # Approvisionnement compte
            "VERSEMENT", "VRSTESPECESAUTOMATE", "VRST ESPECES",  # Versements espèces
            "VIR ", "VIREMENT",  # Virements génériques
            "CHQ.",  # Chèques émis
            "BLOCAGE", "DEBLOC",  # Blocages/déblocages sur compte
            "PRELEVEMENT",  # Prélèvements génériques
        ],
    },
}


# =============================================================================
# ANALYSEUR DE CATÉGORIES
# =============================================================================


@dataclass
class CategoryStats:
    """Statistiques pour une catégorie."""
    code: str
    name: str
    transaction_count: int = 0
    keyword_counts: Counter = field(default_factory=Counter)
    total_debit: Decimal = field(default_factory=lambda: Decimal("0"))
    total_credit: Decimal = field(default_factory=lambda: Decimal("0"))
    examples: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Résultat complet de l'analyse."""
    source_files: list[str] = field(default_factory=list)
    total_transactions: int = 0
    categorized_transactions: int = 0
    uncategorized_transactions: int = 0
    categories: dict[str, CategoryStats] = field(default_factory=dict)
    uncategorized_samples: list[str] = field(default_factory=list)
    all_keywords: Counter = field(default_factory=Counter)


class KeywordAnalyzer:
    """Analyseur de mots-clés pour catégoriser les transactions."""

    def __init__(self):
        self.categories = CATEGORIES
        # Compiler patterns (insensible à la casse)
        self._patterns: dict[str, list[tuple[re.Pattern, str]]] = {}
        for cat_code, cat_info in self.categories.items():
            patterns = []
            for kw in cat_info["keywords"]:
                pattern = re.compile(re.escape(kw), re.IGNORECASE)
                patterns.append((pattern, kw))
            self._patterns[cat_code] = patterns

    def categorize(self, libelle: str) -> tuple[str | None, list[str]]:
        """
        Catégorise un libellé.

        Returns:
            (category_code, [matched_keywords]) ou (None, [])
        """
        matches: dict[str, list[str]] = defaultdict(list)

        for cat_code, patterns in self._patterns.items():
            for pattern, keyword in patterns:
                if pattern.search(libelle):
                    matches[cat_code].append(keyword)

        if not matches:
            return None, []

        # Prendre la catégorie avec le plus de correspondances
        # En cas d'égalité, priorité aux catégories plus spécifiques
        best_cat = max(matches.keys(), key=lambda c: (len(matches[c]), -len(c)))
        return best_cat, matches[best_cat]

    def analyze_statements(self, statements: list[ParsedStatement]) -> AnalysisResult:
        """Analyse plusieurs relevés."""
        result = AnalysisResult()

        # Initialiser stats
        for cat_code, cat_info in self.categories.items():
            result.categories[cat_code] = CategoryStats(
                code=cat_code,
                name=cat_info["name"],
            )

        for stmt in statements:
            result.source_files.append(stmt.source_file)

            for tx in stmt.transactions:
                result.total_transactions += 1

                # Extraire mots pour stats globales
                words = re.findall(r"\b[A-Z]{3,}\b", tx.libelle.upper())
                for w in words:
                    result.all_keywords[w] += 1

                # Catégoriser
                cat_code, keywords = self.categorize(tx.libelle)

                if cat_code:
                    result.categorized_transactions += 1
                    stats = result.categories[cat_code]
                    stats.transaction_count += 1

                    for kw in keywords:
                        stats.keyword_counts[kw] += 1

                    if tx.debit:
                        stats.total_debit += tx.debit
                    if tx.credit:
                        stats.total_credit += tx.credit

                    if len(stats.examples) < 5:
                        amt = tx.debit or tx.credit or Decimal("0")
                        stats.examples.append(f"{tx.date}: {tx.libelle[:50]} ({amt}€)")
                else:
                    result.uncategorized_transactions += 1
                    if len(result.uncategorized_samples) < 50:
                        result.uncategorized_samples.append(
                            f"[{tx.bank_type}] {tx.date}: {tx.libelle[:60]}"
                        )

        return result


# =============================================================================
# RAPPORT
# =============================================================================


def print_report(result: AnalysisResult) -> None:
    """Affiche le rapport d'analyse."""
    print("\n" + "=" * 80)
    print("RAPPORT D'ANALYSE DES RELEVÉS BANCAIRES")
    print("=" * 80)

    print(f"\n📁 Fichiers analysés: {len(result.source_files)}")
    for f in result.source_files:
        print(f"   • {Path(f).name}")

    print(f"\n📊 STATISTIQUES GLOBALES")
    pct_cat = result.categorized_transactions / max(1, result.total_transactions) * 100
    pct_uncat = result.uncategorized_transactions / max(1, result.total_transactions) * 100
    print(f"   Total transactions: {result.total_transactions}")
    print(f"   ✓ Catégorisées: {result.categorized_transactions} ({pct_cat:.1f}%)")
    print(f"   ✗ Non catégorisées: {result.uncategorized_transactions} ({pct_uncat:.1f}%)")

    print(f"\n📋 RÉPARTITION PAR CATÉGORIE")
    print("-" * 80)

    # Trier par nombre de transactions
    sorted_cats = sorted(
        result.categories.items(),
        key=lambda x: x[1].transaction_count,
        reverse=True,
    )

    for cat_code, stats in sorted_cats:
        if stats.transaction_count == 0:
            continue

        print(f"\n🏷️  {stats.name}")
        print(f"    Transactions: {stats.transaction_count}")
        print(f"    Débits: {stats.total_debit:,.2f} € | Crédits: {stats.total_credit:,.2f} €")

        if stats.keyword_counts:
            top_kw = stats.keyword_counts.most_common(8)
            kw_str = ", ".join(f"{kw}({c})" for kw, c in top_kw)
            print(f"    Mots-clés: {kw_str}")

        if stats.examples:
            print("    Exemples:")
            for ex in stats.examples[:3]:
                print(f"      • {ex}")

    print(f"\n⚠️  TRANSACTIONS NON CATÉGORISÉES (échantillon)")
    print("-" * 80)
    for sample in result.uncategorized_samples[:20]:
        print(f"   {sample}")

    print("\n" + "=" * 80)


# =============================================================================
# MAIN
# =============================================================================


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "releve"
    folder_path = Path(folder)

    if not folder_path.exists():
        print(f"❌ Dossier non trouvé: {folder}")
        sys.exit(1)

    print(f"🔍 Analyse du dossier: {folder}")
    pdf_files = list(folder_path.glob("*.pdf"))
    print(f"   {len(pdf_files)} fichiers PDF trouvés")

    statements = []
    for pdf_file in pdf_files:
        try:
            stmt = parse_statement(pdf_file)
            statements.append(stmt)
            print(f"   ✓ {pdf_file.name}: {stmt.bank_type}, {len(stmt.transactions)} tx")
        except Exception as e:
            print(f"   ✗ {pdf_file.name}: ERREUR - {e}")

    analyzer = KeywordAnalyzer()
    result = analyzer.analyze_statements(statements)
    print_report(result)

    return result


if __name__ == "__main__":
    main()
