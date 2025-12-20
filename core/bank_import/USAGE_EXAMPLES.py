"""Examples d'utilisation de l'interface BankParser - Phase 2.

Ce fichier contient des exemples pratiques d'utilisation des nouvelles
fonctionnalités ajoutées lors de la Phase 2 du refactoring.
"""

from typing import List
from core.bank_import import (
    BaseBankParser,
    BankType,
    ParsedStatement,
    StatementPeriod,
    detect_bank_type,
    detect_bank_full,
    get_parser,
)


# =============================================================================
# EXEMPLE 1: Détection automatique avec IBAN et confidence
# =============================================================================

def example_enhanced_detection():
    """Utiliser la détection enrichie avec IBAN et confidence score."""

    # Texte extrait d'un PDF
    pdf_text = """
    CREDIT LYONNAIS
    Relevé de compte
    IBAN: FR76 1234 5678 9012 3456 7890 123
    BIC: CRLYFRPP
    """

    # Méthode 1: Tuple simple (bank_type, confidence, iban)
    bank_type, confidence, iban = detect_bank_type(pdf_text)

    print(f"Banque détectée: {bank_type.value}")
    print(f"Niveau de confiance: {confidence:.2%}")
    print(f"IBAN extrait: {iban}")

    if confidence > 0.5:
        print("✓ Détection fiable")
    else:
        print("⚠ Détection peu fiable, vérification manuelle recommandée")


def example_full_detection():
    """Utiliser la détection complète avec tous les détails."""

    pdf_text = """
    BNP PARIBAS
    N° de compte: 12345678901
    IBAN: FR76 9876 5432 1098 7654 3210 987
    BIC: BNPAFRPP
    """

    # Détection complète
    result = detect_bank_full(pdf_text)

    print(f"Banque: {result.bank_type.value}")
    print(f"Confiance: {result.confidence:.2%}")
    print(f"IBAN: {result.iban}")
    print(f"BIC: {result.bic}")
    print(f"N° compte: {result.account_number}")
    print(f"Détection fiable? {result.is_confident}")
    print(f"Scores détaillés: {result.detection_scores}")

    # Conversion en dict pour API/JSON
    print("\nPour API/JSON:")
    print(result.to_dict())


# =============================================================================
# EXEMPLE 2: Créer un parser custom pour une nouvelle banque
# =============================================================================

class CreditAgricoleParser(BaseBankParser):
    """Parser pour les relevés Crédit Agricole.

    Cet exemple montre comment créer un parser pour une nouvelle banque
    en héritant de BaseBankParser.
    """

    @property
    def bank_type(self) -> BankType:
        """Type de banque géré par ce parser."""
        return BankType.CREDIT_AGRICOLE

    def can_parse(self, text: str) -> bool:
        """Vérifie si ce parser peut traiter le texte donné.

        Args:
            text: Texte complet du PDF

        Returns:
            True si le texte semble être un relevé CA
        """
        text_upper = text.upper()
        return any([
            "CREDIT AGRICOLE" in text_upper,
            "AGRIFRPP" in text_upper,  # BIC CA
            "CA-" in text and ".FR" in text_upper,  # Site régional
        ])

    def parse(
        self,
        lines: List[str],
        period: StatementPeriod,
    ) -> ParsedStatement:
        """Parse les lignes du relevé Crédit Agricole.

        Args:
            lines: Lignes de texte du PDF
            period: Période du relevé

        Returns:
            ParsedStatement avec transactions et balance

        Raises:
            ValueError: Si le format n'est pas reconnu
        """
        # TODO: Implémenter la logique de parsing CA
        # Pour l'instant, juste un exemple de structure

        from core.bank_import import ParsedTransaction, TransactionDirection
        from decimal import Decimal
        from datetime import date

        transactions = []

        # Exemple de parsing (à remplacer par la vraie logique)
        for i, line in enumerate(lines):
            if self._is_transaction_line(line):
                # Parser la ligne
                transaction = self._parse_ca_transaction(line, i, period)
                if transaction:
                    transactions.append(transaction)

        # Créer le statement
        from core.bank_import import ParsedStatement

        return ParsedStatement(
            period=period,
            transactions=transactions,
            balance=None,  # TODO: extraire balance
            bank_type=self.bank_type,
        )

    def _is_transaction_line(self, line: str) -> bool:
        """Vérifie si une ligne est une transaction."""
        # TODO: Implémenter la détection CA
        return False

    def _parse_ca_transaction(self, line, line_num, period):
        """Parse une ligne de transaction CA."""
        # TODO: Implémenter le parsing CA
        return None


def example_custom_parser():
    """Utiliser un parser custom."""

    # Créer le parser
    parser = CreditAgricoleParser()

    # Vérifier s'il peut parser le texte
    pdf_text = "CREDIT AGRICOLE - Relevé de compte"
    if parser.can_parse(pdf_text):
        print(f"✓ Le parser {parser.bank_type.value} peut traiter ce document")

        # Parser le document
        lines = pdf_text.split('\n')
        from datetime import date
        period = StatementPeriod(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        # statement = parser.parse(lines, period)
        # print(f"✓ {len(statement.transactions)} transactions parsées")


# =============================================================================
# EXEMPLE 3: Utiliser le factory pattern
# =============================================================================

def example_factory_pattern():
    """Utiliser get_parser() pour obtenir le bon parser."""

    # Détecter le type de banque
    pdf_text = "LCL - CREDIT LYONNAIS"
    bank_type, confidence, iban = detect_bank_type(pdf_text)

    if confidence > 0.5:
        # Obtenir le parser approprié via factory
        parser = get_parser(bank_type)
        print(f"✓ Parser obtenu: {type(parser).__name__}")
        print(f"✓ Gère la banque: {parser.bank_type.value}")

        # Utiliser le parser
        lines = pdf_text.split('\n')
        from datetime import date
        period = StatementPeriod(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        # statement = parser.parse(lines, period, bank_type)


# =============================================================================
# EXEMPLE 4: Workflow complet d'import
# =============================================================================

def example_complete_workflow():
    """Workflow complet de détection et parsing."""

    # 1. Extraire le texte du PDF
    pdf_text = """
    SOCIETE GENERALE
    Relevé de compte du 01/01/2024 au 31/01/2024
    IBAN: FR76 1111 2222 3333 4444 5555 666
    BIC: SOGEFRPP
    """

    # 2. Détection complète
    result = detect_bank_full(pdf_text)

    print("=== Étape 1: Détection ===")
    print(f"Banque: {result.bank_type.value}")
    print(f"Confiance: {result.confidence:.2%}")
    print(f"IBAN: {result.iban}")

    if not result.is_confident:
        print("⚠ Attention: confiance faible")
        # Demander confirmation utilisateur
        return

    # 3. Obtenir le parser approprié
    parser = get_parser(result.bank_type)
    print(f"\n=== Étape 2: Parser ===")
    print(f"Parser: {type(parser).__name__}")

    # 4. Parser le document
    # lines = extract_pdf_lines(pdf_path)
    # period = extract_period(pdf_text)
    # statement = parser.parse(lines, period, result.bank_type)

    # 5. Valider et importer
    # if statement.is_balanced:
    #     save_to_database(statement)


# =============================================================================
# EXEMPLE 5: Enregistrer un parser custom dans le registry
# =============================================================================

def example_register_parser():
    """Enregistrer un nouveau parser dans le registry."""

    from core.bank_import.parser import _parser_registry

    # Enregistrer le parser CA
    _parser_registry.register(BankType.CREDIT_AGRICOLE, CreditAgricoleParser)

    # Maintenant, get_parser() retournera automatiquement le bon parser
    parser = get_parser(BankType.CREDIT_AGRICOLE)
    print(f"✓ Parser CA enregistré: {type(parser).__name__}")

    # Liste des banques supportées
    supported = _parser_registry.get_available_banks()
    print(f"✓ Banques supportées: {[b.value for b in supported]}")


# =============================================================================
# EXEMPLE 6: Gestion des erreurs et validation
# =============================================================================

def example_error_handling():
    """Gérer les erreurs et cas limites."""

    pdf_text = "Document bancaire sans marqueur clair"

    # Détection avec gestion d'erreur
    result = detect_bank_full(pdf_text)

    if result.bank_type == BankType.UNKNOWN:
        print("❌ Impossible de détecter la banque")
        print(f"Scores: {result.detection_scores}")
        # Fallback: demander à l'utilisateur
        return

    if result.confidence < 0.3:
        print("⚠ Confiance très faible")
        # Proposer une sélection manuelle
        return

    if result.confidence < 0.7:
        print("⚠ Confiance moyenne - vérification recommandée")
        # Afficher les scores pour debug
        print(f"Détails: {result.detection_scores}")

    # Parser avec gestion d'erreur
    try:
        parser = get_parser(result.bank_type)
        # statement = parser.parse(lines, period)
    except ValueError as e:
        print(f"❌ Erreur de parsing: {e}")
        # Logger l'erreur, notifier l'utilisateur
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        # Logger l'erreur critique


# =============================================================================
# Main pour tester les exemples
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("EXEMPLES D'UTILISATION - Phase 2 Refactoring")
    print("=" * 70)

    print("\n### Exemple 1: Détection enrichie ###")
    example_enhanced_detection()

    print("\n### Exemple 2: Détection complète ###")
    example_full_detection()

    print("\n### Exemple 3: Parser custom ###")
    example_custom_parser()

    print("\n### Exemple 4: Factory pattern ###")
    example_factory_pattern()

    print("\n### Exemple 5: Workflow complet ###")
    example_complete_workflow()

    print("\n### Exemple 6: Gestion d'erreurs ###")
    example_error_handling()

    print("\n" + "=" * 70)
    print("✅ Tous les exemples exécutés avec succès!")
    print("=" * 70)
