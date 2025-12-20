# Phase 1 - Checklist de Vérification

## Vérifications Rapides Post-Nettoyage

### 1. Vérifier que les répertoires ont été supprimés
```bash
# Ces commandes doivent renvoyer "No such file or directory"
ls backend/services/parsers/
ls backend/services/mappers/
```

### 2. Vérifier que les fichiers critiques existent toujours
```bash
# Ces commandes doivent réussir
ls core/finance/event_sourcing.py
ls core/consolidation_loader.py
ls backend/services/restaurant/bank_statements.py
```

### 3. Vérifier les imports Python
```bash
# Dans le container ou avec l'env virtuel activé
python3 -c "from core.finance import event_sourcing; print('event_sourcing OK')"
python3 -c "from core import consolidation_loader; print('consolidation_loader OK')"
python3 -c "from backend.services.restaurant import bank_statements; print('bank_statements OK')"
```

### 4. Vérifier le build Docker
```bash
# Le build doit réussir sans erreur
docker-compose build api

# Résultat attendu : "Successfully built" ou "DONE"
```

### 5. Vérifier que l'API démarre
```bash
# Démarrer l'API
docker-compose up -d api

# Attendre quelques secondes puis vérifier les logs
docker-compose logs api | tail -20

# Résultat attendu : "Application startup complete" (FastAPI)
```

### 6. Vérifier les endpoints API
```bash
# Vérifier que l'API répond
curl http://localhost:8000/health

# Vérifier la documentation OpenAPI
curl http://localhost:8000/docs

# Résultat attendu : Status 200 OK
```

### 7. Vérifier le frontend
```bash
# Build du frontend
docker-compose build frontend

# Résultat attendu : "Successfully built" ou "DONE"
```

## Fichiers Supprimés (À Vérifier)

### Parsers Supprimés
```bash
# Ces fichiers NE DOIVENT PLUS exister
! test -f backend/services/parsers/bank_statement_parsers.py && echo "OK: parser supprimé"
! test -f backend/services/parsers/keyword_analyzer.py && echo "OK: analyzer supprimé"
! test -f backend/services/mappers/restaurant_to_finance.py && echo "OK: mapper supprimé"
! test -f core/finance/insights.py && echo "OK: insights supprimé"
```

### Scripts Obsolètes Supprimés
```bash
# Vérifier que les anciens scripts ETL sont supprimés
! test -f scripts/etl/analyze_releves.py && echo "OK: ETL supprimé"
! test -f scripts/imports/import_lcl_pdf.py && echo "OK: Import supprimé"
```

## Vérifications de Régression

### Base de Données
```bash
# Vérifier que les tables critiques existent toujours
docker-compose exec db psql -U postgres -d inventaire -c "\dt" | grep finance_transactions
docker-compose exec db psql -U postgres -d inventaire -c "\dt" | grep restaurant_ingredients

# Résultat attendu : Les tables doivent être listées
```

### Endpoints Restaurant
```bash
# Vérifier que les endpoints principaux fonctionnent
curl http://localhost:8000/restaurant/ingredients
curl http://localhost:8000/restaurant/plats
curl http://localhost:8000/restaurant/overview

# Résultat attendu : JSON valide (pas d'erreur 500)
```

### Endpoints Finance
```bash
# Vérifier que les endpoints finance fonctionnent
curl http://localhost:8000/finance/transactions
curl http://localhost:8000/finance/dashboard

# Résultat attendu : JSON valide (pas d'erreur 500)
```

## Statistiques du Nettoyage

### Lignes de Code
```bash
# Voir les statistiques du nettoyage
git diff --stat

# Résultat attendu :
# - ~17,629 lignes supprimées
# - ~9,387 lignes ajoutées
# - Bilan net : -8,242 lignes
```

### Fichiers Supprimés
```bash
# Lister tous les fichiers supprimés
git diff --name-status | grep "^D" | wc -l

# Résultat attendu : Au moins 40+ fichiers supprimés
```

## Rollback (Si Nécessaire)

Si quelque chose ne fonctionne pas, vous pouvez annuler toutes les modifications :

```bash
# Annuler tous les changements non commités
git reset --hard HEAD

# Ou annuler un commit spécifique
git revert <commit-hash>
```

## Prochaines Étapes

Une fois toutes les vérifications passées :

1. **Commit les changements**
```bash
git add .
git commit -m "Phase 1 refactoring: Remove deprecated parsers and dead code

- Remove deprecated parsers (bank_statement_parsers, keyword_analyzer)
- Remove orphaned files (insights.py, restaurant_to_finance.py)
- Remove obsolete ETL scripts
- Remove obsolete documentation
- Clean up empty directories

Total: -8,242 lines of dead code removed
Build: OK
Tests: Passed

🤖 Generated with Claude Code"
```

2. **Push vers le repository**
```bash
git push origin DEVELOPPEMENT
```

3. **Créer une Pull Request** (optionnel)
```bash
# Si vous utilisez gh CLI
gh pr create --title "Phase 1: Clean up deprecated code" --body "See PHASE1_CLEANUP_COMPLETE.md for details"
```

## Notes Importantes

- ✅ Tous les tests doivent passer avant de commit
- ✅ Le build Docker doit réussir
- ✅ L'application doit démarrer sans erreur
- ✅ Les endpoints critiques doivent répondre

Si l'une de ces vérifications échoue, **NE PAS COMMIT** et investiguer le problème.

---

**Dernière mise à jour** : 2025-12-19
**Auteur** : Claude Opus 4.5
