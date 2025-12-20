# Bank Import Module

Module unifié pour l'import de relevés bancaires depuis des PDFs.

## Vue d'ensemble

Ce module fournit un workflow complet pour importer des relevés bancaires:
- Support multi-banques (LCL, BNP, SumUp, CA*, SG*)
- Gestion de PDFs multi-périodes
- Validation des soldes
- Catégorisation automatique
- Détection de doublons
- Audit trail complet

> *CA = Crédit Agricole, SG = Société Générale (patterns ajoutés, parsers à implémenter)

## Installation

```python
# Le module fait partie du projet
from core.bank_import import BankImportOrchestrator
```

## Usage Rapide

### Import Simple

```python
from core.bank_import import BankImportOrchestrator

orchestrator = BankImportOrchestrator(engine=db_engine)
result = orchestrator.import_pdf(
    pdf_path="releve.pdf",
    entity_code="RESTO",
    account_label="LCL - Principal"
)

print(f"Importé: {result.transactions_inserted} transactions")
```

### Détection Automatique

```python
from core.bank_import import detect_bank_full, get_parser

# 1. Détecter le type de banque
result = detect_bank_full(pdf_text)
print(f"Banque: {result.bank_type.value}")
print(f"Confiance: {result.confidence:.2%}")
print(f"IBAN: {result.iban}")

# 2. Obtenir le parser approprié
parser = get_parser(result.bank_type)

# 3. Parser le relevé
statement = parser.parse(lines, period)
```

## Phase 2 - EXTRACTION (✅ TERMINÉE)

La Phase 2 a ajouté:
- ✨ **Interface `BaseBankParser`** pour créer de nouveaux parsers
- ✨ **Détection enrichie** avec IBAN et confidence score
- ✨ **Support CA/SG** (patterns prêts, parsers à venir)
- ✅ **100% backward compatible**

### Créer un Parser Custom

```python
from core.bank_import import BaseBankParser, BankType

class MonParser(BaseBankParser):
    @property
    def bank_type(self) -> BankType:
        return BankType.MA_BANQUE

    def parse(self, lines, period):
        # Logique de parsing
        return ParsedStatement(...)

    def can_parse(self, text: str) -> bool:
        return "MA_BANQUE" in text.upper()
```

Voir `PARSER_INTERFACE.md` pour plus de détails.

## Architecture

```
core/bank_import/
├── __init__.py              # API publique
├── orchestrator.py          # Workflow principal
├── detector.py              # Détection type banque
├── extractor.py             # Extraction texte PDF
├── parser.py                # Parsing transactions
├── categorizer.py           # Catégorisation auto
├── validator.py             # Validation soldes
├── deduplicator.py          # Détection doublons
├── models.py                # Modèles de données
├── PARSER_INTERFACE.md      # Guide interface parsers
├── USAGE_EXAMPLES.py        # Exemples pratiques
└── README.md                # Ce fichier
```

## Banques Supportées

| Banque | Status | Parser | Patterns |
|--------|--------|--------|----------|
| LCL | ✅ Complet | `UnifiedBankParser` | 6 patterns |
| BNP Paribas | ✅ Complet | `UnifiedBankParser` | 6 patterns |
| SumUp | ✅ Complet | `parse_sumup_statement()` | 9 patterns |
| Crédit Agricole | ⏳ Patterns prêts | À implémenter | 6 patterns |
| Société Générale | ⏳ Patterns prêts | À implémenter | 5 patterns |

## API Publique

### Classes

```python
from core.bank_import import (
    # Orchestrator
    BankImportOrchestrator,

    # Interfaces
    BaseBankParser,          # ABC pour parsers
    BankParser,              # Protocol

    # Composants
    BankDetector,
    PDFExtractor,
    UnifiedBankParser,
    TransactionCategorizer,
    BalanceValidator,
    TransactionDeduplicator,
)
```

### Fonctions

```python
from core.bank_import import (
    # Détection
    detect_bank_type,        # (text) -> (bank_type, confidence, iban)
    detect_bank_type_simple, # (text) -> bank_type (legacy)
    detect_bank_full,        # (text) -> DetectionResult

    # Factory
    get_parser,              # (bank_type) -> parser
    parse_statement,         # (lines, period, type) -> statement
)
```

### Modèles

```python
from core.bank_import import (
    BankType,              # Enum: LCL, BNP, SUMUP, CA, SG
    ParsedStatement,       # Relevé parsé
    ParsedTransaction,     # Transaction parsée
    StatementPeriod,       # Période de relevé
    StatementBalance,      # Soldes et totaux
    ImportResult,          # Résultat d'import
    DetectionResult,       # Résultat de détection
)
```

## Workflow Complet

```python
from pathlib import Path
from core.bank_import import BankImportOrchestrator

# 1. Initialiser l'orchestrator
orchestrator = BankImportOrchestrator(
    engine=db_engine,
    dry_run=False,
    strict_validation=True
)

# 2. Importer le PDF
result = orchestrator.import_pdf(
    pdf_path=Path("releve_lcl_2024_01.pdf"),
    entity_code="RESTO",
    account_label="LCL - Compte principal"
)

# 3. Vérifier le résultat
if result.status == ImportStatus.SUCCESS:
    print(f"✓ {result.transactions_inserted} transactions importées")
    print(f"✓ {result.transactions_categorized} catégorisées")
    print(f"✓ {result.transactions_duplicates} doublons détectés")
else:
    print(f"✗ Erreurs: {result.errors}")
```

## Features

### Détection Multi-Banques ✅

- Détection automatique via patterns regex
- Extraction IBAN automatique
- Score de confiance (0.0-1.0)
- Validation via BIC/SWIFT

### Parsing Robuste ✅

- Support multi-formats (LCL, BNP, SumUp)
- Gestion de la pagination
- Parsing des continuations de libellé
- Extraction de soldes et totaux

### Validation ✅

- Vérification équation comptable
- Validation des soldes d'ouverture/clôture
- Détection d'anomalies
- Warnings et erreurs détaillés

### Catégorisation ✅

- Règles basées sur mots-clés
- Score de confiance par catégorie
- Catégories personnalisables
- Historique des catégorisations

### Déduplication ✅

- Checksum SHA256 par transaction
- Détection via (date, libellé, montant, sens)
- Base de données de checksums
- Prévention des doublons

## Configuration

### Parser Configuration

```python
from core.bank_import import UnifiedBankParser, ParserConfig

config = ParserConfig(
    min_line_length=20,
    amount_decimal_separator=",",
    amount_thousands_separator=" ",
    date_format="dd.mm",
    pad_lines=True,
    pad_length=200
)

parser = UnifiedBankParser(config=config)
```

### Detection Configuration

```python
from core.bank_import import BankDetector

detector = BankDetector()

# Détection avec détails
result = detector.detect_full(pdf_text)

# Scores par banque
print(result.detection_scores)
# {'lcl': 3, 'bnp': 0, 'sumup': 0, ...}
```

## Tests

```bash
# Validation complète Phase 2
python3 test_phase_2_validation.py

# Tests unitaires (à venir)
pytest tests/test_bank_import.py
```

## Documentation

- **`PARSER_INTERFACE.md`** - Guide complet interface parsers
- **`USAGE_EXAMPLES.py`** - 6 exemples pratiques
- **`PHASE_2_COMPLETE.md`** - Résumé Phase 2
- **`CHANGELOG_PHASE_2.md`** - Liste changements
- **`QUICK_REFERENCE_PHASE_2.md`** - Référence rapide

## Prochaines Étapes

1. ⏳ Phase 3: Implémenter `CreditAgricoleParser`
2. ⏳ Phase 4: Implémenter `SocieteGeneraleParser`
3. ⏳ Phase 5: Tests unitaires complets
4. ⏳ Phase 6: Support banques régionales

## Contributing

Pour ajouter une nouvelle banque:

1. Ajouter l'enum dans `models.py`:
   ```python
   class BankType(Enum):
       MA_BANQUE = "ma_banque"
   ```

2. Ajouter les patterns dans `detector.py`:
   ```python
   MA_BANQUE_PATTERNS = [...]
   ```

3. Créer le parser dans `parser.py`:
   ```python
   class MaBanqueParser(BaseBankParser):
       ...
   ```

4. Enregistrer dans le registry:
   ```python
   _parser_registry.register(BankType.MA_BANQUE, MaBanqueParser)
   ```

Voir `PARSER_INTERFACE.md` pour plus de détails.

## Support

- Issues: GitHub Issues
- Docs: `PARSER_INTERFACE.md`
- Examples: `USAGE_EXAMPLES.py`

## License

Propriétaire - Usage interne uniquement

## Changelog

Voir `CHANGELOG_PHASE_2.md` pour l'historique complet.

---

**Version**: Phase 2 - EXTRACTION Complete
**Date**: 2025-12-19
**Auteur**: Claude Opus 4.5
