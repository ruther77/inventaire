#!/usr/bin/env python3
"""
Parseur LCL v2 - Basé sur les positions X des colonnes.

Ce parseur utilise pdfplumber pour extraire les positions exactes des montants
et les classifier en DEBIT ou CREDIT selon leur position horizontale.

Colonnes LCL (positions en points):
- DATE: x ≈ 41-66
- LIBELLE: x ≈ 100-350
- VALEUR: x ≈ 364-401
- DEBIT: x ≈ 430-475
- CREDIT: x ≈ 500-540
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional

import pdfplumber


@dataclass
class Transaction:
    """Représente une transaction bancaire."""
    date: str
    libelle: str
    debit: Decimal | None = None
    credit: Decimal | None = None
    valeur: str | None = None
    source_page: int = 0
    statement_period: tuple[str, str] | None = None


@dataclass
class ParsedStatement:
    """Résultat du parsing d'un relevé."""
    bank_type: str = "LCL"
    period_start: str | None = None
    period_end: str | None = None
    account_holder: str = ""
    iban: str = ""
    transactions: list[Transaction] = field(default_factory=list)
    source_file: str = ""
    total_pages: int = 0
    opening_balances: dict[tuple[int, int], Decimal] = field(default_factory=dict)
    closing_balances: dict[tuple[int, int], Decimal] = field(default_factory=dict)


def parse_amount(amount_str: str | None) -> Decimal | None:
    """Convertit une chaîne de montant en Decimal."""
    if not amount_str:
        return None
    cleaned = amount_str.strip()
    cleaned = re.sub(r'\s+', '', cleaned)
    cleaned = re.sub(r'\.(?=\d{3})', '', cleaned)  # Points de milliers
    cleaned = cleaned.replace(',', '.')
    cleaned = cleaned.rstrip('.')
    try:
        val = Decimal(cleaned)
        return val if val != 0 else None
    except (InvalidOperation, ValueError):
        return None


class LCLParserV2:
    """
    Parseur LCL basé sur les positions X.

    Algorithme:
    1. Extraire tous les mots avec leurs coordonnées (x, y)
    2. Grouper par ligne (y similaire)
    3. Pour chaque ligne de transaction:
       - Identifier la date (pattern DD.MM au début)
       - Identifier le montant et sa position X
       - Classifier DEBIT (x < 490) ou CREDIT (x >= 490)
       - Extraire le libellé entre date et montant
    """

    # Seuils de position X
    DEBIT_X_MIN = 420
    DEBIT_X_MAX = 480
    CREDIT_X_MIN = 490
    CREDIT_X_MAX = 550

    # Seuil pour distinguer débit/crédit
    CREDIT_THRESHOLD = 485

    @classmethod
    def parse(cls, pdf_path: str | Path) -> ParsedStatement:
        """Parse un relevé LCL complet."""
        pdf_path = Path(pdf_path)
        result = ParsedStatement(source_file=str(pdf_path))

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

                # Chercher le solde de clôture sur toutes les pages de cette période
                closing_match = re.search(
                    r"SOLDE\s+EN\s+EUROS\s+([\d\s]+[,\.]\d{2})", text
                )
                if closing_match and current_period:
                    period_end = current_period[1]
                    year = int(period_end[6:10])
                    month = int(period_end[3:5])
                    closing = parse_amount(closing_match.group(1))
                    if closing is not None:
                        result.closing_balances[(year, month)] = closing

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

        Stratégie améliorée:
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
                    current_tx.libelle = ' '.join(current_libelle_parts).strip()
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
                    source_page=page_num,
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
            current_tx.libelle = ' '.join(current_libelle_parts).strip()
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
    def _looks_like_amount(cls, text: str) -> bool:
        """Vérifie si un texte ressemble à un montant."""
        # Nettoyer
        cleaned = text.replace(' ', '').replace('.', '')
        if not cleaned:
            return False
        # Doit avoir une virgule et des chiffres
        if ',' not in cleaned:
            return False
        # Doit être majoritairement des chiffres
        digits = sum(1 for c in cleaned if c.isdigit())
        return digits >= len(cleaned) * 0.7

    @classmethod
    def _is_header_footer(cls, line_text: str) -> bool:
        """Détermine si une ligne est un header/footer à ignorer."""
        skip_patterns = [
            'RELEVE DE COMPTE', 'RELEVE D\'IDENTITE', 'CREDIT LYONNAIS',
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


def test_parser():
    """Teste le parseur sur un fichier."""
    import sys

    if len(sys.argv) < 2:
        pdf_path = Path("releve/COMPTECOURANT_00459448258_20240131.pdf")
    else:
        pdf_path = Path(sys.argv[1])

    if not pdf_path.exists():
        print(f"❌ Fichier non trouvé: {pdf_path}")
        return

    print(f"📄 Parsing: {pdf_path}")
    stmt = LCLParserV2.parse(pdf_path)

    print(f"\n📊 Résultats:")
    print(f"   Période: {stmt.period_start} - {stmt.period_end}")
    print(f"   IBAN: {stmt.iban}")
    print(f"   Soldes ouverture: {stmt.opening_balances}")
    print(f"   Soldes clôture: {stmt.closing_balances}")
    print(f"   Transactions: {len(stmt.transactions)}")

    total_debit = sum(tx.debit or Decimal('0') for tx in stmt.transactions)
    total_credit = sum(tx.credit or Decimal('0') for tx in stmt.transactions)

    print(f"\n💰 Totaux:")
    print(f"   Débits:  {total_debit:>12,.2f} €")
    print(f"   Crédits: {total_credit:>12,.2f} €")
    print(f"   Solde:   {total_credit - total_debit:>12,.2f} €")

    # Vérification avec le PDF
    for (year, month), opening in stmt.opening_balances.items():
        closing = stmt.closing_balances.get((year, month))
        if closing:
            expected_mvt = closing - opening
            actual_mvt = total_credit - total_debit
            diff = actual_mvt - expected_mvt
            print(f"\n✓ Vérification période {year}-{month:02d}:")
            print(f"   Solde ouverture:  {opening:>12,.2f} €")
            print(f"   Solde clôture:    {closing:>12,.2f} €")
            print(f"   Mvt attendu:      {expected_mvt:>12,.2f} €")
            print(f"   Mvt calculé:      {actual_mvt:>12,.2f} €")
            print(f"   Écart:            {diff:>12,.2f} €")
            if abs(diff) < 1:
                print("   ✅ COHÉRENT!")
            else:
                print("   ⚠️  ÉCART DÉTECTÉ")

    print(f"\n📋 Premières transactions:")
    for tx in stmt.transactions[:10]:
        d = tx.debit or Decimal('0')
        c = tx.credit or Decimal('0')
        print(f"   {tx.date} | D:{d:>10,.2f} | C:{c:>10,.2f} | {tx.libelle[:40]}")


if __name__ == "__main__":
    test_parser()
