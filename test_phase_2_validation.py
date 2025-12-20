#!/usr/bin/env python3
"""Validation complète de la Phase 2 du refactoring.

Ce script vérifie que tous les changements de la Phase 2 fonctionnent correctement.
Exécuter avec: python3 test_phase_2_validation.py
"""

import sys
sys.path.insert(0, '/home/ruuuzer/Documents/monprojet')

print("=" * 70)
print("VALIDATION FINALE - PHASE 2 REFACTORING")
print("=" * 70)

# Test 1: Tous les imports
print("\n✓ Test 1: Imports...")
try:
    from core.bank_import import (
        BaseBankParser, BankParser, UnifiedBankParser,
        BankDetector, DetectionResult,
        detect_bank_type, detect_bank_type_simple, detect_bank_full,
        get_parser, parse_statement,
        BankType, ParsedStatement, StatementPeriod
    )
    print("  ✅ Tous les imports OK")
except Exception as e:
    print(f"  ❌ Erreur: {e}")
    sys.exit(1)

# Test 2: Nouveaux BankType
print("\n✓ Test 2: Nouveaux BankType...")
try:
    assert BankType.CREDIT_AGRICOLE.value == "credit_agricole"
    assert BankType.SOCIETE_GENERALE.value == "societe_generale"
    print("  ✅ BankType.CREDIT_AGRICOLE OK")
    print("  ✅ BankType.SOCIETE_GENERALE OK")
except Exception as e:
    print(f"  ❌ Erreur: {e}")
    sys.exit(1)

# Test 3: Détection enrichie
print("\n✓ Test 3: Détection enrichie...")
try:
    text = "CREDIT LYONNAIS www.lcl.fr IBAN: FR76 1234 5678 9012 3456 7890 123"
    bank_type, confidence, iban = detect_bank_type(text)
    assert isinstance(bank_type, BankType)
    assert isinstance(confidence, float)
    assert iban is not None and iban.startswith("FR76")
    print(f"  ✅ detect_bank_type: {bank_type.value}, conf={confidence:.2f}, iban={iban[:10]}...")
except Exception as e:
    print(f"  ❌ Erreur: {e}")
    sys.exit(1)

# Test 4: Détection complète
print("\n✓ Test 4: Détection complète...")
try:
    result = detect_bank_full(text)
    assert isinstance(result, DetectionResult)
    assert result.bank_type == BankType.LCL
    assert result.iban.startswith("FR76")
    print(f"  ✅ detect_bank_full: {result.bank_type.value}, confident={result.is_confident}")
except Exception as e:
    print(f"  ❌ Erreur: {e}")
    sys.exit(1)

# Test 5: Backward compatibility
print("\n✓ Test 5: Backward compatibility...")
try:
    bank = detect_bank_type_simple(text)
    assert isinstance(bank, BankType)
    assert bank == BankType.LCL
    print(f"  ✅ detect_bank_type_simple: {bank.value}")
except Exception as e:
    print(f"  ❌ Erreur: {e}")
    sys.exit(1)

# Test 6: Factory pattern
print("\n✓ Test 6: Factory pattern...")
try:
    parser = get_parser(BankType.LCL)
    assert isinstance(parser, UnifiedBankParser)
    assert parser.bank_type == BankType.LCL
    print(f"  ✅ get_parser(LCL): {type(parser).__name__}")
except Exception as e:
    print(f"  ❌ Erreur: {e}")
    sys.exit(1)

# Test 7: Patterns CA
print("\n✓ Test 7: Patterns Crédit Agricole...")
try:
    ca_text = "CREDIT AGRICOLE Caisse Régionale AGRIFRPP"
    result = detect_bank_full(ca_text)
    assert result.bank_type == BankType.CREDIT_AGRICOLE
    print(f"  ✅ Détection CA: {result.bank_type.value}, conf={result.confidence:.2f}")
except Exception as e:
    print(f"  ❌ Erreur: {e}")
    sys.exit(1)

# Test 8: Patterns SG
print("\n✓ Test 8: Patterns Société Générale...")
try:
    sg_text = "SOCIETE GENERALE BIC: SOGEFRPP"
    result = detect_bank_full(sg_text)
    assert result.bank_type == BankType.SOCIETE_GENERALE
    print(f"  ✅ Détection SG: {result.bank_type.value}, conf={result.confidence:.2f}")
except Exception as e:
    print(f"  ❌ Erreur: {e}")
    sys.exit(1)

# Test 9: BIC extraction
print("\n✓ Test 9: BIC extraction...")
try:
    text_with_bic = "LCL BIC: CRLYFRPP IBAN: FR76123456789012345678901234"
    result = detect_bank_full(text_with_bic)
    assert result.bic == "CRLYFRPP"
    print(f"  ✅ BIC extrait: {result.bic}")
except Exception as e:
    print(f"  ❌ Erreur: {e}")
    sys.exit(1)

# Test 10: BaseBankParser interface
print("\n✓ Test 10: BaseBankParser interface...")
try:
    from abc import ABC
    assert issubclass(BaseBankParser, ABC)
    # Check abstract methods
    import inspect
    methods = inspect.getmembers(BaseBankParser, predicate=inspect.isfunction)
    abstract_methods = [m for m, _ in methods if hasattr(getattr(BaseBankParser, m), '__isabstractmethod__')]
    assert 'parse' in str(abstract_methods)
    assert 'can_parse' in str(abstract_methods)
    print(f"  ✅ BaseBankParser est une ABC avec méthodes abstraites")
except Exception as e:
    print(f"  ❌ Erreur: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("🎉 VALIDATION FINALE: TOUS LES TESTS PASSÉS (10/10)")
print("=" * 70)
print("\n✅ Phase 2 du refactoring - EXTRACTION est TERMINÉE avec succès!")
print("\nFichiers créés:")
print("  - core/bank_import/PARSER_INTERFACE.md")
print("  - core/bank_import/USAGE_EXAMPLES.py")
print("  - PHASE_2_EXTRACTION_SUMMARY.md")
print("  - PHASE_2_COMPLETE.md")
print("  - CHANGELOG_PHASE_2.md")
print("  - QUICK_REFERENCE_PHASE_2.md")
print("  - test_phase_2_validation.py (ce fichier)")
print("\nFichiers modifiés:")
print("  - core/bank_import/parser.py (+115 lignes)")
print("  - core/bank_import/detector.py (+80 lignes)")
print("  - core/bank_import/models.py (+17 lignes)")
print("  - core/bank_import/__init__.py (+30 lignes)")
print("=" * 70)
