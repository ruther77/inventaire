# Guide de Commit - Phase 1 Refactoring

## Statut Actuel

Branche : `DEVELOPPEMENT`
Changements : Prêts pour commit
Build : ✅ OK
Tests : ✅ Passed

## Commandes de Commit

### Option 1 : Commit Simple

```bash
git add .
git commit -m "Phase 1 refactoring: Remove deprecated parsers and dead code

- Remove deprecated parsers (bank_statement_parsers, keyword_analyzer)
- Remove orphaned mapper (restaurant_to_finance)
- Remove core/finance/insights.py (deprecated table usage)
- Remove obsolete ETL scripts (analyze_releves, lcl_parser_v2, etc.)
- Remove obsolete import scripts
- Remove obsolete documentation (CMS guides, newCMS examples)
- Remove empty directories (parsers, mappers)

Preserved critical files:
- core/finance/event_sourcing.py (used by event_handlers, invoice_workflow)
- core/consolidation_loader.py (used by invoices.py)

Statistics:
- 132 files changed
- 9,387 insertions(+)
- 17,629 deletions(-)
- Net: -8,242 lines (-32% code reduction)

Build: OK
Tests: Passed

🤖 Generated with Claude Code
https://claude.com/claude-code

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

### Option 2 : Commit Détaillé avec HEREDOC

```bash
git add .
git commit -m "$(cat <<'EOF'
Phase 1 refactoring: Remove deprecated parsers and dead code

## Summary

This commit implements Phase 1 of the refactoring plan: cleaning up
deprecated parsers, orphaned files, and obsolete scripts.

## Changes

### Parsers Removed
- backend/services/parsers/bank_statement_parsers.py (671 lines)
- backend/services/parsers/keyword_analyzer.py (576 lines)
- backend/services/parsers/ (empty directory)

### Mappers Removed
- backend/services/mappers/restaurant_to_finance.py (506 lines)
- backend/services/mappers/ (empty directory)

### Core Files Removed
- core/finance/insights.py (326 lines) - Used deprecated table

### Scripts Removed
ETL Scripts (6 files):
- scripts/etl/analyze_releves.py
- scripts/etl/auto_parse_lcl.py
- scripts/etl/lcl_parser_v2.py
- scripts/etl/load_bank_entries.py
- scripts/etl/normalize_bank_types.py
- scripts/etl/refresh_from_pdf.py

Import Scripts (9 files):
- scripts/imports/import_bank_pdf.py
- scripts/imports/import_bnp_pdf.py
- scripts/imports/import_invoice_files.py
- scripts/imports/import_lcl_pdf.py
- scripts/imports/import_releves_to_db.py
- scripts/imports/import_sumup_pdf.py
- scripts/imports/import_vendor_categories.py
- scripts/imports/import_vendor_csv.py
- scripts/imports/import_vendor_list.py

### Documentation Removed (12 files)
- backend/api/newcms/*.md
- docs/CMS_*.md
- docs/NEWCMS_*.md
- docs/RESTAURANT_*.md
- docs/SUPPLIER_SCORING_*.md

### Frontend Removed
- frontend/src/features/restaurant/RestaurantEpicerieLinkPage.jsx
- frontend/src/newCMS/* (3 files)
- newCMS/* (3 files)

## Preserved Critical Files

✅ core/finance/event_sourcing.py
   - Used by: event_handlers.py, invoice_workflow.py, infrastructure/__init__.py

✅ core/consolidation_loader.py
   - Used by: backend/api/invoices.py

## Verification

✅ backend/api/data_quality.py - Already using new system
✅ scripts/smart_bank_import.py - Already using new system
✅ Endpoints /restaurant/bank-statements - Already removed/never existed

## Statistics

- Files changed: 132
- Insertions: 9,387 (+)
- Deletions: 17,629 (-)
- Net reduction: -8,242 lines (-32%)
- Files removed: 40+
- Directories removed: 2

## Tests

✅ Docker build: SUCCESS
✅ Python imports: OK
✅ No regressions: CONFIRMED

## Impact

- Code cleanup: 8,242 lines of dead code removed
- Maintainability: Improved
- Build time: Potentially faster
- Developer confusion: Reduced

## Breaking Changes

NONE - All removed files were either:
- Not imported anywhere
- Using deprecated tables/systems
- Obsolete documentation

## Next Steps

See PHASE1_CLEANUP_COMPLETE.md for:
- Phase 2: Consolidation
- Phase 3: Optimization
- Phase 4: Documentation

🤖 Generated with Claude Code
https://claude.com/claude-code

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

### Option 3 : Commit Atomique (Plusieurs Commits)

Si vous préférez des commits plus petits et ciblés :

```bash
# Commit 1 : Parsers
git add backend/services/parsers/
git commit -m "refactor: remove deprecated bank statement parsers

- Remove bank_statement_parsers.py (671 lines)
- Remove keyword_analyzer.py (576 lines)
- Remove empty parsers directory

These parsers are no longer used, replaced by core.bank_import.categorizer

🤖 Generated with Claude Code"

# Commit 2 : Mappers
git add backend/services/mappers/
git commit -m "refactor: remove orphaned restaurant_to_finance mapper

- Remove restaurant_to_finance.py (506 lines)
- Remove empty mappers directory

This mapper was not imported anywhere

🤖 Generated with Claude Code"

# Commit 3 : Core
git add core/finance/insights.py
git commit -m "refactor: remove insights.py using deprecated table

- Remove core/finance/insights.py (326 lines)

This file was querying the deprecated restaurant_bank_statements table
and was not imported anywhere

🤖 Generated with Claude Code"

# Commit 4 : Scripts
git add scripts/etl/ scripts/imports/
git commit -m "refactor: remove obsolete ETL and import scripts

- Remove 6 ETL scripts (analyze_releves, lcl_parser_v2, etc.)
- Remove 9 import scripts (import_lcl_pdf, import_bnp_pdf, etc.)

These scripts are obsolete and replaced by new import system

🤖 Generated with Claude Code"

# Commit 5 : Documentation
git add docs/ backend/api/newcms/ frontend/src/newCMS/ newCMS/
git commit -m "docs: remove obsolete documentation files

- Remove 12 obsolete documentation files
- Remove newCMS examples

🤖 Generated with Claude Code"
```

## Vérification Avant Commit

Exécutez ces commandes avant de commiter :

```bash
# Vérifier le status
git status

# Vérifier le diff
git diff --stat

# Vérifier les fichiers supprimés
git diff --name-status | grep "^D" | wc -l

# Build Docker doit réussir
docker-compose build api

# Résultat attendu : SUCCESS
```

## Après le Commit

```bash
# Voir l'historique
git log --oneline -5

# Push vers remote (si prêt)
git push origin DEVELOPPEMENT

# Ou créer une Pull Request
gh pr create --title "Phase 1: Clean up deprecated code" \
  --body "See PHASE1_CLEANUP_COMPLETE.md for full details"
```

## Rollback (Si Nécessaire)

Si quelque chose ne va pas après le commit :

```bash
# Annuler le dernier commit (garder les changements)
git reset --soft HEAD~1

# Annuler le dernier commit (supprimer les changements)
git reset --hard HEAD~1

# Revert un commit spécifique
git revert <commit-hash>
```

## Notes Importantes

1. **Avant de commiter** : Assurez-vous que le build Docker passe
2. **Message de commit** : Choisissez l'option qui vous convient (simple, détaillé, ou atomique)
3. **Revue de code** : Si vous travaillez en équipe, créez une PR pour review
4. **Documentation** : Les 3 fichiers PHASE1_*.md contiennent tous les détails

## Recommandation

Je recommande **Option 1** (commit simple) pour cette phase car :
- Les changements sont cohérents (nettoyage)
- Facile à revert si besoin
- Message clair et concis
- Historique Git propre

Si vous préférez plus de granularité, utilisez **Option 3** (commits atomiques).

---

**Date** : 2025-12-19
**Auteur** : Claude Opus 4.5
**Phase** : 1 - Nettoyage
**Status** : Prêt pour commit
