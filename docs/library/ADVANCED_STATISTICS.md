# Analyse Statistique Approfondie

Statistiques avancées sur le catalogue de fonctions Python

---

## Vue d'Ensemble

- **Fonctions totales**: 1149
- **Fichiers analysés**: 20
- **Dépendances uniques**: 509

## Distribution de la Réutilisabilité

| Niveau | Nombre | Pourcentage |
|--------|--------|-------------|
| High | 504 | 43.9% |
| Medium | 604 | 52.6% |
| Low | 41 | 3.6% |

## Annotations de Type

| Type | Nombre | Pourcentage |
|------|--------|-------------|
| With Params | 242 | 21.1% |
| With Return | 161 | 14.0% |
| Fully Typed | 679 | 59.1% |
| Untyped | 67 | 5.8% |

## Complexité des Signatures

Distribution basée sur le nombre de paramètres :

| Complexité | Nombre | Description |
|------------|--------|-------------|
| Simple (≤2 params) | 797 | Facile à utiliser |
| Moyenne (3-4 params) | 260 | Standard |
| Élevée (5-6 params) | 62 | À simplifier |
| Très élevée (≥7 params) | 30 | Refactoring recommandé |

## Décorateurs les Plus Utilisés

| Décorateur | Utilisation |
|------------|-------------|
| `router.get` | 163 |
| `router.post` | 97 |
| `property` | 28 |
| `app.task` | 19 |
| `abstractmethod` | 13 |
| `router.delete` | 12 |
| `field_validator` | 10 |
| `classmethod` | 10 |
| `router.patch` | 7 |
| `router.put` | 6 |
| `app.get` | 6 |
| `pytest.fixture` | 4 |
| `functools.wraps` | 4 |
| `staticmethod` | 4 |
| `mobile_router.post` | 2 |

## Noms de Paramètres les Plus Fréquents

| Paramètre | Occurrences |
|-----------|-------------|
| `self` | 392 |
| `tenant` | 275 |
| `tenant_id` | 136 |
| `payload` | 83 |
| `limit` | 49 |
| `entity_id` | 48 |
| `request` | 35 |
| `product_id` | 32 |
| `ingredient_id` | 31 |
| `user_id` | 25 |
| `account_id` | 23 |
| `plat_id` | 22 |
| `text` | 20 |
| `period_start` | 18 |
| `period_end` | 18 |
| `period` | 18 |
| `bank_type` | 18 |
| `lines` | 16 |
| `transaction_id` | 15 |
| `cls` | 15 |

## Analyse des Dépendances

- **Dépendances uniques**: 509
- **Fonctions sans dépendances**: 91
- **Fonctions avec nombreuses dépendances (>5)**: 366

### Dépendances les Plus Communes

| Dépendance | Utilisations |
|------------|--------------|
| `sqlalchemy.text` | 337 |
| `typing.Any` | 295 |
| `backend.dependencies.tenant.Tenant` | 282 |
| `fastapi.Depends` | 282 |
| `typing.List` | 201 |
| `typing.Optional` | 200 |
| `datetime.datetime` | 198 |
| `core.data_repository.get_engine` | 198 |
| `core.data_repository.query_df` | 195 |
| `typing.Dict` | 176 |
| `datetime.timedelta` | 150 |
| `backend.dependencies.tenant.get_current_tenant` | 142 |
| `fastapi.HTTPException` | 136 |
| `fastapi.Query` | 124 |
| `backend.dependencies.tenant.get_current_tenant_or_default` | 111 |
| `datetime.date` | 111 |
| `__future__.annotations` | 104 |
| `decimal.Decimal` | 84 |
| `core.data_repository.exec_sql` | 66 |
| `backend.dependencies.tenant.get_restaurant_tenant` | 57 |

## Fonctions Asynchrones par Catégorie

| Catégorie | Fonctions Async |
|-----------|-----------------|
| API | 45 |
| Finance | 18 |
| Middleware | 8 |
| Data Retrieval | 7 |
| Cache | 3 |
| General | 2 |

## Fichiers avec le Plus de Fonctions

| Fichier | Fonctions |
|---------|-----------|
| `backend/api/restaurant.py` | 59 |
| `backend/api/finance.py` | 52 |
| `core/finance/audit_trail.py` | 28 |
| `core/bank_import/parser.py` | 27 |
| `core/finance/anomaly_detection.py` | 24 |
| `core/finance/event_sourcing.py` | 22 |
| `core/finance/forecasting.py` | 21 |
| `backend/services/restaurant/ingredients.py` | 20 |
| `core/repositories/users.py` | 20 |
| `backend/cache.py` | 19 |
| `core/finance/bank_reconciliation.py` | 19 |
| `core/repositories/base.py` | 19 |
| `core/bank_import/models.py` | 18 |
| `backend/api/supplier_scoring.py` | 17 |
| `core/bank_import/categorizer.py` | 17 |
| `backend/api/invoices.py` | 16 |
| `backend/api/newcms/finance.py` | 16 |
| `core/backup_manager.py` | 16 |
| `core/finance/analytic_accounting.py` | 16 |
| `core/finance/rules_engine.py` | 16 |

## Fonctions avec Signatures Complexes

Fonctions avec 6+ paramètres (candidates au refactoring) :

| Fonction | Fichier | Nb Params |
|----------|---------|-----------|
| `create_stock_movement` | `backend/services/restaurant/stock.py` | 14 |
| `log` | `core/finance/audit_trail.py` | 13 |
| `search_transactions` | `backend/api/finance.py` | 12 |
| `create_stock_movement` | `backend/api/restaurant.py` | 12 |
| `list_audit_entries` | `backend/api/audit_trail.py` | 11 |
| `get_transactions` | `backend/api/newcms/finance.py` | 10 |
| `_build_margin_result` | `core/finance/margin_calculator.py` | 10 |
| `record_invoice_entry` | `backend/services/restaurant/stock.py` | 10 |
| `search_invoices` | `backend/api/finance.py` | 9 |
| `calculate_eoq` | `core/finance/inventory_intelligence.py` | 9 |
| `__init__` | `backend/api/auth.py` | 8 |
| `search_bank_statements` | `backend/api/finance.py` | 8 |
| `get_price_history` | `backend/api/prices.py` | 8 |
| `list_stock_movements` | `backend/api/restaurant.py` | 8 |
| `list_plats_paginated` | `backend/api/restaurant.py` | 8 |
| `assign_expense` | `core/finance/analytic_accounting.py` | 8 |
| `calculate_safety_stock` | `core/finance/inventory_intelligence.py` | 8 |
| `calculate_reorder_point` | `core/finance/inventory_intelligence.py` | 8 |
| `record_feedback` | `core/finance/rules_engine.py` | 8 |
| `list_plats_paginated` | `backend/services/restaurant/overview.py` | 8 |
| `list_stock_movements` | `backend/services/restaurant/stock.py` | 8 |
| `get_suppliers_list` | `backend/api/supplier_scoring.py` | 7 |
| `log_update` | `core/finance/audit_trail.py` | 7 |
| `log_delete` | `core/finance/audit_trail.py` | 7 |
| `log_bulk_operation` | `core/finance/audit_trail.py` | 7 |
| `emit_invoice_imported` | `core/finance/event_sourcing.py` | 7 |
| `emit_price_updated` | `core/finance/event_sourcing.py` | 7 |
| `emit_stock_movement` | `core/finance/event_sourcing.py` | 7 |
| `add_rule` | `core/finance/rules_engine.py` | 7 |
| `create_job` | `backend/services/zero_click_jobs.py` | 7 |

## Fonctions Nécessitant Attention

Fonctions sans description, sans types, et faible réutilisabilité :

**Total : 4 fonctions**

| Fonction | Fichier | Catégorie |
|----------|---------|-----------|
| `__call__` | `backend/middleware/rate_limiter.py` | Middleware |
| `decorator` | `core/finance/audit_trail.py` | Finance |
| `wrapper` | `core/finance/audit_trail.py` | Finance |
| `demo` | `core/finance/audit_trail.py` | Finance |

## Recommandations

- ✅ 43.9% de fonctions hautement réutilisables
- ✅ 5.8% de fonctions sans types (bon niveau)
- ⚠️ 4 fonctions nécessitent documentation et amélioration
- ⚠️ 30 fonctions avec nombreux paramètres (≥7). Envisager le refactoring

---

**Note** : Ces statistiques sont basées sur l'analyse statique du code et peuvent nécessiter une validation manuelle.