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
# PARSEUR LCL - Amélioré
# =============================================================================


class LCLParser:
    """
    Parseur pour les relevés LCL (Crédit Lyonnais).

    Format LCL:
    - Header avec RIB, IBAN, infos conseiller
    - Section "ECRITURES DE LA PERIODE"
    - Colonnes: DATE | LIBELLE | VALEUR | DEBIT | CREDIT
    - Date format: DD.MM
    - Valeur format: DD.MM.YY
    - Montants avec virgule, point final pour débit
    """

    @classmethod
    def parse(cls, pdf_path: str | Path) -> ParsedStatement:
        pdf_path = Path(pdf_path)
        result = ParsedStatement(
            bank_type="LCL",
            source_file=str(pdf_path),
        )

        with pdfplumber.open(pdf_path) as pdf:
            result.total_pages = len(pdf.pages)
            all_lines = []

            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""

                # Extraire métadonnées de la première page
                if page_num == 1:
                    cls._extract_metadata(text, result)

                # Extraire les lignes de cette page
                lines = cls._extract_operation_lines(text, page_num)
                all_lines.extend(lines)

            # Parser les transactions depuis les lignes
            result.transactions = cls._parse_lines_to_transactions(
                all_lines, str(pdf_path)
            )

        return result

    @classmethod
    def _extract_metadata(cls, text: str, result: ParsedStatement) -> None:
        """Extrait période, IBAN, titulaire."""
        # Période: "du DD.MM.YYYY au DD.MM.YYYY"
        period_match = re.search(
            r"du\s+(\d{2}\.\d{2}\.\d{4})\s+au\s+(\d{2}\.\d{2}\.\d{4})", text
        )
        if period_match:
            result.period_start = period_match.group(1)
            result.period_end = period_match.group(2)

        # IBAN
        iban_match = re.search(r"IBAN\s*:\s*([A-Z]{2}\d{2}[\s\dA-Z]+)", text)
        if iban_match:
            result.iban = re.sub(r'\s+', '', iban_match.group(1))

        # Titulaire (après "Titulaire du compte")
        holder_match = re.search(
            r"Titulaire du compte[-\s]*([\w\s]+?)(?:\d|---|----|PARIS|75)", text
        )
        if holder_match:
            result.account_holder = holder_match.group(1).strip()

    @classmethod
    def _extract_operation_lines(cls, text: str, page_num: int) -> list[tuple[int, str]]:
        """Extrait les lignes d'opérations d'une page."""
        lines = text.split('\n')
        operation_lines = []
        in_operations = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Détecter début de section opérations
            if "ECRITURES DE LA PERIODE" in line.upper():
                in_operations = True
                continue

            # Ignorer l'en-tête de colonnes
            if re.match(r"DATE\s+LIBELLE\s+VALEUR", line, re.IGNORECASE):
                continue

            # Ignorer les footers
            if any(p in line for p in [
                "Page ", "Crédit Lyonnais", "SIREN",
                "Ce document ne vaut", "Les sommes figurant",
                "garantiedesdepots", "médiateur"
            ]):
                continue

            # Ignorer les headers répétés sur pages suivantes
            if any(p in line for p in [
                "RELEVE DE COMPTE", "Indicatif :", "CREDIT LYONNAIS"
            ]):
                in_operations = True  # Réactiver après header répété
                continue

            if in_operations:
                operation_lines.append((page_num, line))

        return operation_lines

    @classmethod
    def _parse_lines_to_transactions(
        cls, lines: list[tuple[int, str]], source_file: str
    ) -> list[Transaction]:
        """Parse les lignes en transactions."""
        transactions = []
        current_tx = None
        current_libelle_parts = []

        # Pattern pour ligne de transaction LCL
        # Format: DD.MM LIBELLE DD.MM.YY MONTANT [.]
        # Le point final indique un DÉBIT, son absence indique un CRÉDIT
        tx_pattern = re.compile(
            r"^(\d{2}\.\d{2})\s+"  # Date
            r"(.+?)\s+"  # Libellé (non-greedy)
            r"(\d{2}\.\d{2}\.\d{2})\s*"  # Date valeur
            r"([\d\s,]+(?:,\d{2}))\s*"  # Montant
            r"(\.)?$"  # Point final = débit, absence = crédit
        )

        # Pattern alternatif pour lignes avec seulement date et libellé
        simple_pattern = re.compile(r"^(\d{2}\.\d{2})\s+(.+)$")

        for page_num, line in lines:
            # Ignorer lignes "SOLDE"
            if "SOLDE" in line.upper() and "ANCIEN" not in line.upper():
                continue

            # Essayer le pattern complet
            match = tx_pattern.match(line)

            if match:
                # Sauvegarder transaction précédente
                if current_tx:
                    current_tx.libelle = clean_libelle(" ".join(current_libelle_parts))
                    transactions.append(current_tx)

                date = match.group(1)
                libelle = match.group(2).strip()
                valeur = match.group(3)
                montant_str = match.group(4)
                has_dot = match.group(5) is not None  # Point final = débit

                # Logique de classification LCL:
                # - Point final (.) -> toujours débit (frais, commissions)
                # - Sans point:
                #   - "REMISE" dans le libellé -> crédit (entrée d'argent)
                #   - Autres (CB, PRLV, VIR) -> débit (sortie d'argent)
                montant = parse_amount(montant_str)
                is_remise = "REMISE" in libelle.upper()

                if has_dot:
                    # Point final = débit certain (frais, commissions)
                    debit_val = montant
                    credit_val = None
                elif is_remise:
                    # REMISE = crédit (entrée d'argent)
                    debit_val = None
                    credit_val = montant
                else:
                    # Par défaut = débit (CB, PRLV, VIR, etc.)
                    debit_val = montant
                    credit_val = None

                current_tx = Transaction(
                    date=date,
                    libelle=libelle,
                    valeur=valeur,
                    debit=debit_val,
                    credit=credit_val,
                    raw_text=line,
                    source_file=source_file,
                    source_page=page_num,
                    bank_type="LCL",
                )
                current_libelle_parts = [libelle]

            elif current_tx:
                # Ligne de continuation - ajouter au libellé
                # Ignorer les lignes de détail technique
                if not re.match(r"^(LIBELLE|REF\.|ID\.|REF\.MANDAT|BRUT|NO\s+\d)", line):
                    if not line.startswith(("LIBELLE:", "REF.CLIENT:", "ID.CREANCIER:")):
                        current_libelle_parts.append(line)

        # Ajouter la dernière transaction
        if current_tx:
            current_tx.libelle = clean_libelle(" ".join(current_libelle_parts))
            transactions.append(current_tx)

        return transactions


# =============================================================================
# PARSEUR BNP - Amélioré
# =============================================================================


class BNPParser:
    """
    Parseur pour les relevés BNP Paribas.

    Format BNP:
    - Texte souvent collé (pas d'espaces entre mots)
    - Caractères encodés (Ø pour é, etc.)
    - Format: DD.MM OPERATION DD.MM DEBIT CREDIT
    - Utilise extract_tables() pour meilleure précision
    """

    @classmethod
    def parse(cls, pdf_path: str | Path) -> ParsedStatement:
        pdf_path = Path(pdf_path)
        result = ParsedStatement(
            bank_type="BNP",
            source_file=str(pdf_path),
        )

        with pdfplumber.open(pdf_path) as pdf:
            result.total_pages = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""

                if page_num == 1:
                    cls._extract_metadata(text, result)

                # Extraire via texte (plus fiable pour BNP)
                transactions = cls._parse_page_text(text, page_num, str(pdf_path))
                result.transactions.extend(transactions)

        return result

    @classmethod
    def _extract_metadata(cls, text: str, result: ParsedStatement) -> None:
        """Extrait les métadonnées BNP."""
        # Période (format collé: du27décembre2022au27janvier2023)
        period_match = re.search(
            r"du(\d{1,2})(\w+?)(\d{4})au(\d{1,2})(\w+?)(\d{4})", text
        )
        if period_match:
            result.period_start = f"{period_match.group(1)} {period_match.group(2)} {period_match.group(3)}"
            result.period_end = f"{period_match.group(4)} {period_match.group(5)} {period_match.group(6)}"

        # IBAN
        iban_match = re.search(r"IBAN\s*:\s*([A-Z]{2}\d{2}[\s\dA-Z]+)", text)
        if iban_match:
            result.iban = re.sub(r'\s+', '', iban_match.group(1))

    @classmethod
    def _parse_page_text(
        cls, text: str, page_num: int, source_file: str
    ) -> list[Transaction]:
        """Parse une page BNP depuis le texte."""
        transactions = []
        lines = text.split('\n')

        # Pattern BNP: DD.MM TEXTE DD.MM MONTANT [MONTANT]
        # Les montants peuvent avoir des espaces (1 500,00)
        tx_pattern = re.compile(
            r"^(\d{2}\.\d{2})\s+"  # Date opération
            r"(.+?)\s+"  # Libellé
            r"(\d{2}\.\d{2})\s+"  # Date valeur
            r"([\d\s]+,\d{2})?\s*"  # Débit
            r"([\d\s]+,\d{2})?$"  # Crédit
        )

        current_tx = None
        current_parts = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Ignorer headers/footers
            if any(p in line for p in [
                "RELEVEDECOMPTE", "RELEVE DE COMPTE", "P.", "P. ",
                "BNPPARIBASSAaucapital", "3477", "mabanque.bnpparibas",
                "RCSParis", "ORIAS"
            ]):
                continue

            match = tx_pattern.match(line)

            if match:
                # Sauvegarder précédente
                if current_tx:
                    current_tx.libelle = clean_libelle(" ".join(current_parts))
                    transactions.append(current_tx)

                date = match.group(1)
                libelle = match.group(2).strip()
                valeur = match.group(3)
                debit_str = match.group(4)
                credit_str = match.group(5)

                current_tx = Transaction(
                    date=date,
                    libelle=libelle,
                    valeur=valeur,
                    debit=parse_amount(debit_str),
                    credit=parse_amount(credit_str),
                    raw_text=line,
                    source_file=source_file,
                    source_page=page_num,
                    bank_type="BNP",
                )
                current_parts = [libelle]

            elif current_tx:
                # Continuation - ignorer les lignes techniques
                if not line.startswith(("ECH/", "MDT/", "REF/", "LIB/", "ID")):
                    current_parts.append(line)

        if current_tx:
            current_tx.libelle = clean_libelle(" ".join(current_parts))
            transactions.append(current_tx)

        return transactions


# =============================================================================
# PARSEUR SUMUP - Amélioré
# =============================================================================


class SUMUPParser:
    """
    Parseur pour les relevés SumUp.

    Format SumUp (relevé de compte carte):
    - Date DD/MM/YYYY HH:MM
    - Code transaction
    - Type (Paiement POS, Paiement en ligne, Paiement entrant, etc.)
    - Référence
    - Statut
    - Montant débité, crédité, frais, solde
    """

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

                transactions = cls._parse_page_text(text, page_num, str(pdf_path))
                result.transactions.extend(transactions)

        return result

    @classmethod
    def _extract_metadata(cls, text: str, result: ParsedStatement) -> None:
        """Extrait les métadonnées SumUp."""
        # Période
        period_match = re.search(
            r"période.*?:\s*(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})",
            text, re.IGNORECASE
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
            result.account_holder = f"SUMUP-{merchant_match.group(1)}"

    @classmethod
    def _parse_page_text(
        cls, text: str, page_num: int, source_file: str
    ) -> list[Transaction]:
        """Parse une page SumUp."""
        transactions = []
        lines = text.split('\n')

        # Pattern SumUp:
        # DD/MM/YYYY HH:MM CODE TYPE REFERENCE STATUT DEBIT CREDIT FRAIS SOLDE
        tx_pattern = re.compile(
            r"^(\d{2}/\d{2}/\d{4})\s+"  # Date
            r"(\d{2}:\d{2})?\s*"  # Heure (optionnel)
            r"([A-Z0-9]+)\s+"  # Code transaction
            r"(.+?)\s+"  # Type + Référence
            r"(Approuvé|Entrant|Remboursé|Envoyé par SumUp|Envoyé|En attente)\s+"  # Statut
            r"([\d.]+)\s+"  # Débité
            r"([\d.]+)\s+"  # Crédité
            r"([\d.]+)\s+"  # Frais
            r"([\d.]+)"  # Solde
        )

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Ignorer headers/footers
            if any(p in line for p in [
                "card.export", "address_footer", "legal_footer",
                "Des questions", "support.sumup"
            ]):
                continue

            match = tx_pattern.match(line)

            if match:
                date = match.group(1)
                heure = match.group(2) or ""
                code = match.group(3)
                type_ref = match.group(4).strip()
                statut = match.group(5)
                debit = match.group(6)
                credit = match.group(7)

                # Construire libellé
                libelle = f"{type_ref}"
                if statut != "Approuvé":
                    libelle += f" [{statut}]"

                tx = Transaction(
                    date=f"{date} {heure}".strip(),
                    libelle=libelle,
                    valeur=code,
                    debit=Decimal(debit) if float(debit) > 0 else None,
                    credit=Decimal(credit) if float(credit) > 0 else None,
                    raw_text=line,
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
