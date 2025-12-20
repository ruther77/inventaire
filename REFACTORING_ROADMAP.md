# Bank Import Module - Roadmap de Refactoring

## Vision

Transformer le module `core/bank_import` en une solution extensible et maintenable pour supporter de multiples banques françaises avec une architecture claire et documentée.

## Statut Global

- ✅ **Phase 1**: ANALYSE (Terminée)
- ✅ **Phase 2**: EXTRACTION (Terminée - 2025-12-19)
- ⏳ **Phase 3**: CRÉDIT AGRICOLE (À venir)
- ⏳ **Phase 4**: SOCIÉTÉ GÉNÉRALE (À venir)
- ⏳ **Phase 5**: TESTS & VALIDATION (À venir)
- ⏳ **Phase 6**: BANQUES RÉGIONALES (À venir)

---

## Phase 1: ANALYSE ✅

**Objectif**: Comprendre l'architecture existante et identifier les besoins

### Actions Réalisées
- ✅ Analyse du code existant
- ✅ Identification des patterns communs
- ✅ Recensement des banques supportées (LCL, BNP, SumUp)
- ✅ Documentation de l'architecture actuelle

### Livrables
- Documentation technique existante
- Liste des améliorations nécessaires

---

## Phase 2: EXTRACTION ✅ TERMINÉE

**Objectif**: Consolider les parsers bancaires avec une interface claire

**Date de complétion**: 2025-12-19

### Actions Réalisées

#### 1. Interface BankParser ✅
- **`BaseBankParser` (ABC)**: Classe abstraite pour créer des parsers
- **`BankParser` (Protocol)**: Interface pour type checking
- Documentation complète avec exemples

**Fichiers**: `core/bank_import/parser.py` (lignes 30-144)

#### 2. UnifiedBankParser Refactoré ✅
- Implémente l'interface `BankParser`
- 100% compatible avec le code existant
- Utilisable via factory `get_parser()`

#### 3. BankDetector Amélioré ✅

**Nouvelles fonctionnalités**:
- `detect_bank_type()`: Retourne `(bank_type, confidence, iban)`
- `detect_bank_full()`: Détection complète avec `DetectionResult`
- `detect_bank_type_simple()`: Fonction legacy (backward compat)
- Extraction IBAN automatique (formats FR et IE)
- Extraction BIC/SWIFT automatique
- Score de confiance (0.0-1.0)

**Fichiers**: `core/bank_import/detector.py`

#### 4. Support Crédit Agricole et Société Générale ✅

**BankType étendus**:
```python
BankType.CREDIT_AGRICOLE      # "credit_agricole"
BankType.SOCIETE_GENERALE     # "societe_generale"
```

**Patterns ajoutés**:
- Crédit Agricole: 6 patterns
- Société Générale: 5 patterns

**Fichiers**:
- `core/bank_import/models.py` (lignes 12-29)
- `core/bank_import/detector.py` (lignes 88-105)

#### 5. Documentation Complète ✅

**Fichiers créés**:
- `core/bank_import/PARSER_INTERFACE.md` - Guide d'interface
- `core/bank_import/USAGE_EXAMPLES.py` - 6 exemples pratiques
- `core/bank_import/README.md` - Documentation module
- `PHASE_2_EXTRACTION_SUMMARY.md` - Résumé technique
- `PHASE_2_COMPLETE.md` - Résumé exécutif
- `CHANGELOG_PHASE_2.md` - Liste changements
- `QUICK_REFERENCE_PHASE_2.md` - Référence rapide
- `test_phase_2_validation.py` - Tests de validation

### Métriques Phase 2

| Métrique | Valeur |
|----------|--------|
| Lignes ajoutées | ~350 |
| Lignes modifiées | ~100 |
| Fichiers modifiés | 4 |
| Fichiers créés | 8 |
| Nouveaux exports | 8 |
| Nouveaux patterns | 11 |
| Backward compatibility | 100% |

### Validation Phase 2

- ✅ 10/10 tests de validation passés
- ✅ Aucune erreur de syntaxe Python
- ✅ Tous les imports fonctionnent
- ✅ Code existant non cassé

---

## Phase 3: CRÉDIT AGRICOLE ⏳

**Objectif**: Implémenter un parser complet pour les relevés Crédit Agricole

**Statut**: PRÉPARÉ (patterns ajoutés, parser à implémenter)

### Actions Planifiées

#### 1. Analyse Format CA
- [ ] Obtenir des PDFs de relevés CA
- [ ] Analyser la structure (colonnes, dates, montants)
- [ ] Identifier les spécificités CA vs LCL/BNP
- [ ] Documenter le format

#### 2. Créer CreditAgricoleParser
```python
class CreditAgricoleParser(BaseBankParser):
    @property
    def bank_type(self) -> BankType:
        return BankType.CREDIT_AGRICOLE

    def parse(self, lines, period):
        # TODO: Implémenter parsing CA
        pass

    def can_parse(self, text: str) -> bool:
        return "CREDIT AGRICOLE" in text.upper()
```

#### 3. Patterns Spécifiques CA
- [ ] Identifier les patterns de transactions CA
- [ ] Adapter la détection de colonnes
- [ ] Gérer les variantes régionales (CA-IDF, CA-Normandie, etc.)

#### 4. Tests
- [ ] Tests unitaires pour CreditAgricoleParser
- [ ] Tests avec vrais PDFs CA
- [ ] Validation des soldes
- [ ] Benchmark de performance

### Livrables Attendus
- `CreditAgricoleParser` fonctionnel
- Tests unitaires
- Documentation spécifique CA
- Exemples de parsing CA

---

## Phase 4: SOCIÉTÉ GÉNÉRALE ⏳

**Objectif**: Implémenter un parser complet pour les relevés Société Générale

**Statut**: PRÉPARÉ (patterns ajoutés, parser à implémenter)

### Actions Planifiées

#### 1. Analyse Format SG
- [ ] Obtenir des PDFs de relevés SG
- [ ] Analyser la structure
- [ ] Identifier les spécificités SG
- [ ] Documenter le format

#### 2. Créer SocieteGeneraleParser
```python
class SocieteGeneraleParser(BaseBankParser):
    @property
    def bank_type(self) -> BankType:
        return BankType.SOCIETE_GENERALE

    def parse(self, lines, period):
        # TODO: Implémenter parsing SG
        pass

    def can_parse(self, text: str) -> bool:
        return "SOCIETE GENERALE" in text.upper()
```

#### 3. Tests
- [ ] Tests unitaires pour SocieteGeneraleParser
- [ ] Tests avec vrais PDFs SG
- [ ] Validation des soldes

### Livrables Attendus
- `SocieteGeneraleParser` fonctionnel
- Tests unitaires
- Documentation spécifique SG

---

## Phase 5: TESTS & VALIDATION ⏳

**Objectif**: Tests complets et validation de l'architecture

### Actions Planifiées

#### 1. Tests Unitaires
- [ ] Tests pour BaseBankParser
- [ ] Tests pour BankDetector
- [ ] Tests pour chaque parser (LCL, BNP, SumUp, CA, SG)
- [ ] Tests de la factory `get_parser()`

#### 2. Tests d'Intégration
- [ ] Workflow complet d'import
- [ ] Gestion des erreurs
- [ ] Déduplication
- [ ] Catégorisation

#### 3. Tests de Performance
- [ ] Benchmark de parsing (transactions/seconde)
- [ ] Benchmark de détection
- [ ] Memory profiling
- [ ] Optimisations si nécessaire

#### 4. Validation
- [ ] Tests avec vrais PDFs de chaque banque
- [ ] Validation des soldes sur plusieurs mois
- [ ] Vérification anti-régression

### Livrables Attendus
- Suite de tests complète (>80% coverage)
- Rapport de performance
- Documentation des tests

---

## Phase 6: BANQUES RÉGIONALES ⏳

**Objectif**: Support des banques régionales françaises

### Banques Ciblées

#### 1. Caisse d'Épargne
- [ ] Patterns de détection
- [ ] Parser spécifique
- [ ] Tests

#### 2. Banque Postale
- [ ] Patterns de détection
- [ ] Parser spécifique
- [ ] Tests

#### 3. Banques Populaires
- [ ] Patterns de détection
- [ ] Parser spécifique
- [ ] Tests

#### 4. Boursorama
- [ ] Patterns de détection
- [ ] Parser spécifique
- [ ] Tests

### Livrables Attendus
- 4+ nouveaux parsers
- Documentation étendue
- Tests pour chaque banque

---

## Architecture Cible

### Structure Finale

```
core/bank_import/
├── __init__.py
├── orchestrator.py
├── detector.py              # Détection multi-banques
├── extractor.py
├── categorizer.py
├── validator.py
├── deduplicator.py
├── models.py                # BankType étendu
├── parsers/
│   ├── __init__.py
│   ├── base.py              # BaseBankParser
│   ├── unified.py           # UnifiedBankParser (LCL, BNP, SumUp)
│   ├── credit_agricole.py   # CreditAgricoleParser
│   ├── societe_generale.py  # SocieteGeneraleParser
│   ├── caisse_epargne.py    # CaisseEpargneParser
│   ├── banque_postale.py    # BanquePostaleParser
│   ├── banques_populaires.py
│   └── boursorama.py
├── docs/
│   ├── PARSER_INTERFACE.md
│   ├── USAGE_EXAMPLES.py
│   └── README.md
└── tests/
    ├── test_detector.py
    ├── test_parsers.py
    ├── test_lcl.py
    ├── test_bnp.py
    ├── test_ca.py
    └── test_sg.py
```

### BankType Final

```python
class BankType(Enum):
    # Banques nationales
    LCL = "lcl"
    BNP = "bnp"
    SOCIETE_GENERALE = "societe_generale"
    CREDIT_AGRICOLE = "credit_agricole"

    # Banques régionales
    CAISSE_EPARGNE = "caisse_epargne"
    BANQUE_POSTALE = "banque_postale"
    BANQUES_POPULAIRES = "banques_populaires"
    BOURSORAMA = "boursorama"

    # Processeurs de paiement
    SUMUP = "sumup"

    # Autres
    UNKNOWN = "unknown"
```

---

## Principes de Design

### 1. Extensibilité
- Interface claire (`BaseBankParser`)
- Factory pattern pour instanciation
- Registry pour nouveaux parsers
- Patterns pluggables

### 2. Maintenabilité
- Documentation complète
- Tests pour chaque parser
- Exemples d'utilisation
- Code commenté

### 3. Backward Compatibility
- Fonctions legacy maintenues
- Migrations documentées
- Pas de breaking changes
- Versioning clair

### 4. Performance
- Parsing optimisé
- Cache de détection
- Batch processing
- Memory-efficient

### 5. Robustesse
- Validation des données
- Gestion d'erreurs complète
- Logging détaillé
- Fallbacks appropriés

---

## Métriques de Succès

### Coverage
- [ ] Tests: >80% coverage
- [ ] Documentation: 100% API documentée
- [ ] Exemples: 1+ exemple par feature

### Performance
- [ ] Parsing: >1000 transactions/seconde
- [ ] Détection: <10ms par PDF
- [ ] Memory: <100MB pour 10k transactions

### Qualité
- [ ] Pas de breaking changes
- [ ] Toutes les banques validées avec vrais PDFs
- [ ] Zero regression sur code existant

---

## Timeline Estimée

| Phase | Durée Estimée | Statut |
|-------|---------------|--------|
| Phase 1: Analyse | 1 jour | ✅ Terminée |
| Phase 2: Extraction | 1 jour | ✅ Terminée |
| Phase 3: CA Parser | 2-3 jours | ⏳ À venir |
| Phase 4: SG Parser | 2-3 jours | ⏳ À venir |
| Phase 5: Tests | 2 jours | ⏳ À venir |
| Phase 6: Régionales | 1 semaine | ⏳ À venir |

**Total**: ~2-3 semaines

---

## Dépendances

### Techniques
- Python 3.8+
- SQLAlchemy
- pdftotext / pdfplumber
- pytest (pour tests)

### Ressources
- PDFs de relevés pour chaque banque
- Base de données de test
- Documentation formats bancaires

---

## Risques et Mitigations

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| Variabilité formats PDFs | Élevé | Moyenne | Tests avec multiples PDFs, patterns robustes |
| Changements formats banque | Moyen | Faible | Versioning des parsers, fallbacks |
| Performance avec gros volumes | Moyen | Faible | Batch processing, optimisation |
| Backward compatibility | Élevé | Faible | Tests de régression, fonctions legacy |

---

## Communication

### Documentation
- ✅ README.md par module
- ✅ CHANGELOG pour chaque phase
- ✅ Guides d'utilisation
- ✅ Exemples de code

### Code
- ✅ Docstrings complètes
- ✅ Type hints
- ✅ Comments pour logique complexe

---

## Conclusion

Le refactoring du module `core/bank_import` suit une approche progressive et structurée:

1. ✅ **Phase 1-2 terminées**: Infrastructure et interfaces en place
2. ⏳ **Phase 3-4 à venir**: Parsers CA et SG
3. ⏳ **Phase 5-6 futures**: Tests et extension régionales

**Objectif final**: Solution extensible, maintainable et performante pour supporter toutes les banques françaises majeures.

---

**Dernière mise à jour**: 2025-12-19
**Auteur**: Claude Opus 4.5
**Version**: 1.0 (Phase 2 Complete)
