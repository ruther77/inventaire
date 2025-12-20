# Bank Parser Interface - Documentation

## Phase 2 du Refactoring - EXTRACTION

Cette documentation décrit les améliorations apportées aux parsers bancaires dans la Phase 2 du refactoring.

## Nouvelles Interfaces

### 1. Interface ABC: `BaseBankParser`

Une classe abstraite pour créer de nouveaux parsers bancaires de manière structurée.

```python
from abc import ABC, abstractmethod
from core.bank_import import BaseBankParser, BankType, ParsedStatement, StatementPeriod

class CreditAgricoleParser(BaseBankParser):
    @property
    def bank_type(self) -> BankType:
        return BankType.CREDIT_AGRICOLE

    def parse(self, lines: List[str], period: StatementPeriod) -> ParsedStatement:
        # Implémentation du parsing spécifique CA
        ...

    def can_parse(self, text: str) -> bool:
        return "CREDIT AGRICOLE" in text.upper()
```

### 2. Protocol: `BankParser`

Un protocol Python pour le type checking (compatible avec mypy).

```python
from core.bank_import import BankParser

def process_statement(parser: BankParser, lines: List[str]) -> None:
    if parser.can_parse("\n".join(lines)):
        statement = parser.parse(lines, period)
```

## Détection Bancaire Améliorée

### Fonction `detect_bank_type()` avec confidence et IBAN

```python
from core.bank_import import detect_bank_type

# Nouvelle signature enrichie
bank_type, confidence, iban = detect_bank_type(pdf_text)

if confidence > 0.5:
    print(f"Banque détectée: {bank_type.value}")
    print(f"Confiance: {confidence:.2%}")
    print(f"IBAN: {iban}")
```

### Détection complète avec `detect_bank_full()`

Pour obtenir toutes les informations disponibles:

```python
from core.bank_import import detect_bank_full

result = detect_bank_full(pdf_text)

print(f"Banque: {result.bank_type.value}")
print(f"Confiance: {result.confidence:.2%}")
print(f"IBAN: {result.iban}")
print(f"BIC: {result.bic}")
print(f"Numéro de compte: {result.account_number}")
print(f"Scores de détection: {result.detection_scores}")
```

### Fonction legacy `detect_bank_type_simple()`

Pour la compatibilité avec le code existant:

```python
from core.bank_import import detect_bank_type_simple

# Ancienne signature (compatibilité)
bank_type = detect_bank_type_simple(pdf_text)
```

## Nouveaux Types de Banques Supportés

### Types Actuellement Implémentés

- `BankType.LCL` - Crédit Lyonnais
- `BankType.BNP` - BNP Paribas
- `BankType.SUMUP` - SumUp (processeur de paiement)

### Types Préparés pour Extension Future

- `BankType.CREDIT_AGRICOLE` - Crédit Agricole (patterns ajoutés, parser à implémenter)
- `BankType.SOCIETE_GENERALE` - Société Générale (patterns ajoutés, parser à implémenter)

## Patterns de Détection Ajoutés

### Crédit Agricole

```python
CREDIT_AGRICOLE_PATTERNS = [
    r"CREDIT\s+AGRICOLE"
    r"www\.credit-agricole\.fr"
    r"ca-[\w-]+\.fr"  # Sites régionaux
    r"AGRIFRPP"  # Code BIC
    r"Caisse\s+Régionale"
    r"Relevé\s+de\s+compte.*Crédit\s+Agricole"
]
```

### Société Générale

```python
SOCIETE_GENERALE_PATTERNS = [
    r"SOCIETE\s+GENERALE"
    r"www\.particuliers\.societegenerale\.fr"
    r"SOGEFRPP"  # Code BIC
    r"Relevé\s+de\s+compte.*Société\s+Générale"
    r"SG\s+BANQUE"
]
```

## Extraction IBAN Automatique

Le `BankDetector` extrait automatiquement l'IBAN via regex:

- Format français standard: `FR76 1234 5678 9012 3456 7890 123`
- Format compact: `FR76123456789012345678901234`
- Format SumUp irlandais: `IE12SUMU...`

### Exemple d'utilisation

```python
from core.bank_import import BankDetector

detector = BankDetector()
result = detector.detect_full(pdf_text)

if result.iban:
    print(f"IBAN extrait: {result.iban}")
```

## Factory Pattern pour les Parsers

### Utiliser `get_parser()`

```python
from core.bank_import import get_parser, BankType

# Obtenir le parser approprié
parser = get_parser(BankType.LCL)
statement = parser.parse(lines, period)
```

### Utiliser `parse_statement()` (convenience)

```python
from core.bank_import import parse_statement, BankType

# Fonction de commodité
statement = parse_statement(lines, period, BankType.LCL)
```

## Compatibilité Backward

Toutes les modifications sont **rétro-compatibles**:

1. ✅ `UnifiedBankParser` fonctionne comme avant
2. ✅ `detect_bank_type_simple()` pour l'ancienne signature
3. ✅ Les imports existants ne sont pas cassés
4. ✅ `BankParser` Protocol n'affecte pas le code existant

## Codes BIC Supportés

```python
BANK_BIC_CODES = {
    "CRLYFRPP": BankType.LCL,
    "BNPAFRPP": BankType.BNP,
    "AGRIFRPP": BankType.CREDIT_AGRICOLE,
    "SOGEFRPP": BankType.SOCIETE_GENERALE,
}
```

Le BIC détecté est utilisé pour:
- Confirmer le type de banque détecté (+20% confidence)
- Corriger le type détecté si incohérent (confidence = 0.9)

## Exemple Complet d'Extension

### Créer un parser pour une nouvelle banque

```python
from core.bank_import import BaseBankParser, BankType, ParsedStatement, StatementPeriod
from typing import List

class SocieteGeneraleParser(BaseBankParser):
    """Parser pour les relevés Société Générale."""

    @property
    def bank_type(self) -> BankType:
        return BankType.SOCIETE_GENERALE

    def parse(self, lines: List[str], period: StatementPeriod) -> ParsedStatement:
        """Parse les lignes du relevé SG."""
        # TODO: Implémenter la logique de parsing
        transactions = []
        balance = None

        # ... logique de parsing spécifique SG ...

        return ParsedStatement(
            period=period,
            transactions=transactions,
            balance=balance,
            bank_type=self.bank_type,
        )

    def can_parse(self, text: str) -> bool:
        """Vérifie si ce parser peut traiter le texte."""
        return any([
            "SOCIETE GENERALE" in text.upper(),
            "SOGEFRPP" in text.upper(),
        ])
```

### Enregistrer le nouveau parser

```python
from core.bank_import.parser import _parser_registry

# Enregistrer le parser
_parser_registry.register(BankType.SOCIETE_GENERALE, SocieteGeneraleParser)

# Utiliser le factory
parser = get_parser(BankType.SOCIETE_GENERALE)
```

## Tests

### Tester la détection

```python
def test_detection():
    from core.bank_import import detect_bank_full

    pdf_text = "CREDIT AGRICOLE ... AGRIFRPP ... FR76 1234..."
    result = detect_bank_full(pdf_text)

    assert result.bank_type == BankType.CREDIT_AGRICOLE
    assert result.confidence > 0.5
    assert result.iban.startswith("FR76")
    assert result.bic == "AGRIFRPP"
```

### Tester un parser custom

```python
def test_custom_parser():
    from tests.fixtures import sample_ca_statement

    parser = CreditAgricoleParser()
    assert parser.can_parse(sample_ca_statement)

    statement = parser.parse(lines, period)
    assert statement.bank_type == BankType.CREDIT_AGRICOLE
    assert len(statement.transactions) > 0
```

## Roadmap Future

1. ✅ Phase 2: Interface et détection (FAIT)
2. ⏳ Phase 3: Parser Crédit Agricole
3. ⏳ Phase 4: Parser Société Générale
4. ⏳ Phase 5: Banques régionales (Caisse d'Épargne, Banque Postale, etc.)

## Migration Guide

### Code Existant

```python
# Avant (fonctionne toujours)
from core.bank_import import UnifiedBankParser

parser = UnifiedBankParser()
statement = parser.parse(lines, period, BankType.LCL)
```

### Code Recommandé

```python
# Après (recommandé)
from core.bank_import import get_parser, detect_bank_full

# Détection automatique
result = detect_bank_full(pdf_text)
parser = get_parser(result.bank_type)
statement = parser.parse(lines, period)
```

## Support

Pour toute question ou contribution, voir:
- `/core/bank_import/README.md` - Documentation générale
- `/docs/BANK_IMPORT_ARCHITECTURE.md` - Architecture détaillée
