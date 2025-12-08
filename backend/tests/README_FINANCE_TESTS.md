# Tests Finance API

## Description

Ce fichier contient les tests pytest complets pour l'API Finance (`test_finance_api.py`).

## Structure des tests

### 1. Tests de pagination

- `test_transactions_search_pagination`: Vérifie que la pagination fonctionne (items, page, size, total)
- `test_transactions_search_pagination_bounds`: Teste les limites (page < 1, size > 500)
- `test_bank_statements_search_pagination`: Pagination des relevés bancaires
- `test_invoices_search_pagination`: Pagination des factures

### 2. Tests de filtres

- `test_transactions_search_filters`: Teste tous les filtres (entity_id, account_id, category_id, date_from, date_to, q)
- `test_transactions_search_amount_filters`: Filtres amount_min et amount_max
- `test_transactions_search_sorting`: Tri ascendant/descendant sur différents champs

### 3. Tests batch categorize

- `test_batch_categorize_by_ids`: Recatégorisation par liste d'IDs
- `test_batch_categorize_by_rule`: Recatégorisation par règle (keywords)
- `test_batch_categorize_validation_error`: Erreur quand ni IDs ni règle

### 4. Tests suggestions

- `test_suggestions_autre_top`: Suggestions des libellés fréquents non catégorisés
- `test_suggestions_autre_top_with_limit`: Suggestions avec limite personnalisée
- `test_categories_autocomplete`: Autocomplete des catégories
- `test_categories_autocomplete_missing_query`: Validation du paramètre q obligatoire
- `test_categories_list`: Liste complète des catégories

### 5. Tests import CSV

- `test_import_csv_format`: Import valide avec CSV correct
- `test_import_csv_invalid`: Import avec format invalide
- `test_import_csv_missing_account_id`: Validation du paramètre account_id obligatoire

### 6. Tests réconciliation

- `test_reconciliation_run`: Lancement d'une réconciliation
- `test_reconciliation_run_default_params`: Réconciliation avec paramètres par défaut
- `test_reconciliation_matches`: Liste des matches
- `test_reconciliation_matches_all_statuses`: Matches sans filtre de statut
- `test_reconciliation_update_match_status`: Mise à jour du statut d'un match
- `test_reconciliation_update_match_not_found`: Erreur 404 pour match inexistant

### 7. Tests CRUD de base

- `test_create_account`: Création d'un compte
- `test_list_accounts`: Liste des comptes
- `test_create_transaction`: Création d'une transaction
- `test_update_transaction`: Mise à jour d'une transaction
- `test_lock_transaction`: Verrouillage d'une transaction

### 8. Tests récurrences et anomalies

- `test_refresh_recurring`: Rafraîchissement des dépenses récurrentes
- `test_list_recurring`: Liste des dépenses récurrentes
- `test_refresh_anomalies`: Détection d'anomalies
- `test_list_anomalies`: Liste des anomalies

### 9. Tests edge cases

- `test_transactions_search_no_results`: Recherche sans résultats
- `test_reconciliation_matches_empty`: Gestion d'erreur quand table absente
- `test_anomalies_optional_table_missing`: Gestion d'erreur pour table optionnelle

## Fixtures

### `client`
Crée une instance `TestClient` pour tester l'API FastAPI.

### `mock_tenant`
Mock du tenant pour bypasser l'authentification dans les tests.

### `override_dependencies`
Override automatique de la dépendance `get_current_tenant` pour tous les tests.

## Exécution des tests

### Tous les tests finance
```bash
pytest backend/tests/test_finance_api.py -v
```

### Un test spécifique
```bash
pytest backend/tests/test_finance_api.py::test_transactions_search_pagination -v
```

### Avec couverture
```bash
pytest backend/tests/test_finance_api.py --cov=backend.api.finance --cov-report=html
```

### Tests par catégorie (utiliser -k)
```bash
# Tests de pagination
pytest backend/tests/test_finance_api.py -k pagination -v

# Tests de filtres
pytest backend/tests/test_finance_api.py -k filters -v

# Tests de réconciliation
pytest backend/tests/test_finance_api.py -k reconciliation -v
```

## Mocking

Tous les tests utilisent `unittest.mock.patch` pour mocker les services sous-jacents:
- `backend.services.finance_transactions`
- `backend.services.finance_invoices`
- `backend.services.finance_bank_statements`
- `backend.services.finance_categories`
- `backend.services.finance`
- etc.

Cela permet de tester l'API sans accès à la base de données.

## Notes importantes

1. **Authentification**: Les tests overrident la dépendance `get_current_tenant` pour éviter l'authentification réelle.

2. **Base de données**: Aucune interaction réelle avec la DB grâce aux mocks.

3. **Validation Pydantic**: Les tests vérifient aussi la validation des schémas (codes 422 pour erreurs de validation).

4. **Gestion d'erreurs**: Les tests couvrent les cas d'erreur (400, 404, 422) et la gestion gracieuse des tables optionnelles.

5. **Types de réponses**: Tous les tests vérifient la structure des réponses JSON conformément aux schémas Pydantic.

## Améliorations futures

- Tests d'intégration avec base de données réelle (fixtures DB)
- Tests de performance pour les recherches paginées
- Tests de concurrence pour batch operations
- Tests de sécurité (injection, XSS, etc.)
- Tests E2E avec Playwright/Selenium
