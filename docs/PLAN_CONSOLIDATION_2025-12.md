# Plan de Consolidation du Projet
**Date:** 8 Décembre 2025
**Statut:** En attente de validation

---

## Contexte

Le projet a atteint un point de maturité où la croissance organique a créé :
- Une duplication de responsabilités entre modules (Restaurant, Épicerie, Trésorerie)
- Une page `/bank-statement` surchargée (4 onglets, ~10 hooks API simultanés)
- Des fichiers monolithiques difficiles à maintenir (`restaurant.py` : 77K lignes)
- Une documentation vieillissante et des plans non appliqués
- ~40 scripts fragmentés sans organisation claire

Ce plan vise à remettre de l'ordre de manière méthodique.

---

## Vue d'ensemble des phases

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PLAN DE CONSOLIDATION                               │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────────┤
│   PHASE 1    │   PHASE 2    │   PHASE 3    │   PHASE 4    │   PHASE 5   │
│   Nettoyage  │   Backend    │   Frontend   │   Refacto    │   Qualité   │
│   & Archive  │   Trésorerie │   UX/UI      │   Restaurant │   & Docs    │
├──────────────┼──────────────┼──────────────┼──────────────┼─────────────┤
│ • Archiver   │ • Appliquer  │ • Simplifier │ • Découper   │ • Tests     │
│   legacy/    │   migrations │   /bank-     │   restaurant │ • E2E       │
│ • Trier      │ • Éliminer   │   statement  │   .py        │ • Perf      │
│   scripts    │   dualité    │ • Lazy load  │ • Centraliser│ • README    │
│ • Nettoyer   │   API        │   onglets    │   charges    │   à jour    │
│   docs       │ • Services   │ • Design     │              │             │
│              │   unifiés    │   system     │              │             │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────────┘
```

---

## PHASE 1 : Nettoyage & Archivage

**Objectif:** Éliminer le bruit, clarifier ce qui est actif vs obsolète

### 1.1 Archiver les dossiers obsolètes

| Dossier | Action | Destination |
|---------|--------|-------------|
| `legacy/` | Archiver | `_archive/legacy_2025-12/` |
| `Dev à venir/` | Sauvegarder captures puis supprimer | `_archive/captures_dev/` |
| `experiments/` | Évaluer puis archiver si abandonné | `_archive/experiments/` |

**Commandes:**
```bash
mkdir -p _archive/{legacy_2025-12,captures_dev,experiments}
mv legacy/* _archive/legacy_2025-12/
mv "Dev à venir"/* _archive/captures_dev/
mv experiments/* _archive/experiments/
rmdir legacy "Dev à venir" experiments
```

### 1.2 Trier les scripts

Créer une organisation claire :

```
scripts/
├── imports/              # Scripts d'import actifs
│   ├── import_lcl_pdf.py
│   ├── import_bnp_pdf.py
│   └── import_sumup_pdf.py
├── etl/                  # Transformation de données
│   ├── import_releves_to_db.py
│   └── classify_finance_transactions.py
├── catalog/              # Gestion catalogue
│   ├── eurociel_prepare_catalogue.py
│   └── prepare_articles_for_db.py
├── _deprecated/          # Scripts one-shot terminés
│   └── (scripts de migration anciens)
└── README.md             # Documenter chaque script
```

**Critères de tri:**
- Script utilisé régulièrement → garder dans catégorie appropriée
- Script one-shot déjà exécuté → `_deprecated/`
- Script jamais utilisé → supprimer

### 1.3 Nettoyer la documentation

| Fichier | Action |
|---------|--------|
| `docs/roadmap_finance_epicerie_restaurant.md` | Archiver → `docs/_archive/` |
| `docs/module_map.txt` | Archiver |
| `docs/migration_plan.md` | Archiver |
| `docs/finance_tresury_refactor.md` | **GARDER** - Base pour Phase 2 |
| `docs/finance_ui_ux_overhaul.md` | **GARDER** - Base pour Phase 3 |
| `docs/AUDIT_UX_UI_EXPERT.md` | **GARDER** - Référence UX |

Structure finale :
```
docs/
├── PLAN_CONSOLIDATION_2025-12.md   # Ce document
├── DEMARRAGE_RAPIDE.md             # Onboarding
├── finance_tresury_refactor.md     # Plan technique backend
├── finance_ui_ux_overhaul.md       # Plan UX frontend
├── AUDIT_UX_UI_EXPERT.md           # Référence design
└── _archive/                       # Anciens plans
```

### 1.4 Vérifier les permissions anormales

```bash
# Fichiers verrouillés détectés (chmod 400)
chmod 644 frontend/src/features/treasury/BankStatementPage.jsx
chmod 644 backend/services/finance_bank_statements.py
```

**Checklist Phase 1:**
- [ ] Créer `_archive/` et déplacer legacy
- [ ] Organiser scripts en sous-dossiers
- [ ] Archiver docs obsolètes
- [ ] Corriger permissions fichiers
- [ ] Commit : "chore: archive legacy files and organize scripts"

---

## PHASE 2 : Consolidation Backend Trésorerie

**Objectif:** Une seule source de vérité pour les données financières

### 2.1 Appliquer les migrations Alembic

Le plan `finance_tresury_refactor.md` contient le DDL complet. À appliquer :

```sql
-- Tables à créer (résumé)
finance_entities          -- Entités (RESTO, EPICERIE)
finance_entity_members    -- Liaison tenant ↔ entité
finance_accounts          -- Comptes bancaires unifiés
finance_transactions      -- Transactions centralisées
finance_transaction_lines -- Lignes analytiques
finance_categories        -- Catégories partagées
finance_bank_statements   -- Relevés importés
finance_bank_statement_lines
finance_reconciliations   -- Rapprochements
finance_vendors           -- Fournisseurs
finance_invoices_supplier -- Factures fournisseurs
finance_payments          -- Paiements
```

**Étapes:**
1. Créer migration Alembic `2025_12_finance_treasury.py`
2. Appliquer en dev : `alembic upgrade head`
3. Script backfill pour migrer données existantes

### 2.2 Éliminer la dualité API

**Situation actuelle (problématique):**
```
/restaurant/bank-statements/*    ← À SUPPRIMER
/finance/bank-statements/*       ← GARDER (source unique)
```

**Plan de migration:**

| Endpoint Restaurant | Action | Équivalent Finance |
|---------------------|--------|-------------------|
| `GET /restaurant/bank-statements` | Déprécier | `GET /finance/transactions?entity=RESTO` |
| `POST /restaurant/bank-statements` | Déprécier | `POST /finance/transactions` |
| `POST /restaurant/bank-statements/import-pdf` | Déprécier | `POST /finance/bank-statements/import` |
| `GET /restaurant/bank-accounts/overview` | Déprécier | `GET /finance/accounts/overview` |

**Fichiers à modifier:**

1. `backend/api/restaurant.py` :
   - Marquer endpoints bank-statements comme `@deprecated`
   - Rediriger vers `/finance/*`
   - Planifier suppression après migration frontend

2. `backend/api/finance.py` :
   - Ajouter paramètre `entity_id` à tous les endpoints
   - S'assurer de la pagination (page/size/sort)

### 2.3 Unifier les services

**Actuellement fragmenté:**
```
backend/services/
├── finance.py
├── finance_accounts.py
├── finance_bank_statements.py
├── finance_categories.py
├── finance_dashboard.py
├── finance_imports.py
├── finance_invoices.py
├── finance_metrics.py
├── finance_reconciliation.py
├── finance_rules.py
├── finance_stats.py
└── finance_transactions.py
```

**Réorganisation proposée:**
```
backend/services/finance/
├── __init__.py           # Exports publics
├── accounts.py           # Comptes
├── transactions.py       # Transactions + lignes
├── bank_statements.py    # Import relevés
├── reconciliation.py     # Rapprochement
├── categories.py         # Catégories + règles
├── vendors.py            # Fournisseurs
├── invoices.py           # Factures
└── stats.py              # Stats + dashboard + metrics
```

### 2.4 Schémas Pydantic unifiés

Fusionner dans `backend/schemas/finance.py` :
- `RestaurantBankStatementCreate` → `FinanceBankStatementCreate`
- `RestaurantBankStatementEntry` → `FinanceTransaction`
- `RestaurantBankAccountOverview` → `FinanceAccountOverview`

**Checklist Phase 2:**
- [ ] Créer et appliquer migration Alembic
- [ ] Script backfill données existantes
- [ ] Déprécier endpoints restaurant bank-statements
- [ ] Réorganiser services finance en package
- [ ] Unifier schémas Pydantic
- [ ] Tests API
- [ ] Commit : "feat: unified treasury backend"

---

## PHASE 3 : Refonte Frontend UX/UI

**Objectif:** Simplifier `/bank-statement`, améliorer l'expérience

### 3.1 Problème actuel de `/bank-statement`

```
BankStatementPage.jsx (189 lignes)
├── Charge 4 onglets simultanément
├── ~10 hooks API en parallèle
│   ├── useFinanceTransactions()
│   ├── useFinanceCategories()
│   ├── useFinanceAccounts()
│   ├── useFinanceAccountsOverviewStats()
│   ├── useFinanceRules()
│   ├── useFinanceTreasury()
│   ├── useFinanceAnomalies()
│   ├── useFinanceMatches()
│   ├── useFinanceImports()
│   └── useFinanceImportMutation()
└── Pas de lazy loading
```

### 3.2 Solution : Diviser en pages distinctes

**Nouvelle architecture routes:**

```javascript
// routes.jsx - Treasury routes
{
  path: '/tresorerie',
  children: [
    { index: true, element: <TreasuryOverview /> },         // Vue d'ensemble
    { path: 'transactions', element: <TreasuryTransactions /> },
    { path: 'comptes', element: <TreasuryAccounts /> },
    { path: 'imports', element: <TreasuryImports /> },
    { path: 'regles', element: <TreasuryRules /> },
    { path: 'rapprochement', element: <TreasuryReconciliation /> },
  ]
}
```

**Avantages:**
- Chaque page charge uniquement ses hooks
- URLs bookmarkables
- Navigation claire
- Chargement plus rapide

### 3.3 Navigation Trésorerie

Remplacer les onglets par une sidebar/sous-menu :

```
┌─────────────────────────────────────────────────────┐
│  TRÉSORERIE                                         │
├─────────────────┬───────────────────────────────────┤
│                 │                                   │
│  Vue d'ensemble │   [Contenu de la page active]    │
│  Transactions   │                                   │
│  Comptes        │                                   │
│  Imports        │                                   │
│  Règles         │                                   │
│  Rapprochement  │                                   │
│                 │                                   │
└─────────────────┴───────────────────────────────────┘
```

### 3.4 Lazy loading des composants

```javascript
// Utiliser React.lazy pour chaque page
const TreasuryTransactions = lazy(() =>
  import('./features/treasury/TreasuryTransactions')
);

// Suspense avec skeleton loader
<Suspense fallback={<PageSkeleton />}>
  <TreasuryTransactions />
</Suspense>
```

### 3.5 Optimisations UX (basées sur l'audit)

| Problème | Solution |
|----------|----------|
| Surcharge cognitive | Diviser en pages distinctes |
| ~10 appels API simultanés | Lazy loading par page |
| Pas de feedback | Toasts + loading states |
| Contraste insuffisant | Appliquer corrections design-tokens |
| Taille tactile < 44px | Corriger boutons xs |

### 3.6 Activer CategoryInlineEdit

Le composant existe mais n'est pas activé :

```javascript
// Dans TreasuryTransactions.jsx
import { CategoryInlineEdit } from '../finance/components/CategoryInlineEdit';

// Remplacer le TODO modal par le composant
<CategoryInlineEdit
  transactionId={tx.id}
  currentCategory={tx.category}
  onUpdate={handleCategoryUpdate}
/>
```

**Checklist Phase 3:**
- [ ] Créer nouvelles pages Trésorerie (Overview, Transactions, etc.)
- [ ] Configurer routes avec lazy loading
- [ ] Créer sous-navigation Trésorerie
- [ ] Activer CategoryInlineEdit
- [ ] Implémenter export CSV (TODO existant)
- [ ] Appliquer corrections design-tokens
- [ ] Tests Cypress e2e
- [ ] Commit : "feat: treasury UX overhaul - split pages"

---

## PHASE 4 : Refactoring Restaurant

**Objectif:** Découper le monolithe, centraliser les charges dans Finance

### 4.1 Découper `restaurant.py` (76K lignes)

**Structure actuelle (monolithique):**
```
backend/services/restaurant.py  # 76,957 lignes - TOUT
```

**Structure cible (modulaire):**
```
backend/services/restaurant/
├── __init__.py
├── dashboard.py          # Stats dashboard
├── expenses.py           # Dépenses (migrées vers finance)
├── ingredients.py        # Gestion ingrédients
├── consumption.py        # Consommation
├── forecasts.py          # Prévisions
├── menu.py               # Gestion menu
├── suppliers.py          # Fournisseurs (à lier avec finance_vendors)
└── cost_analysis.py      # Analyse coûts
```

### 4.2 Migrer les charges vers Finance

Les charges restaurant doivent être des `finance_transactions` avec `entity_id=RESTO` :

```python
# Avant : RestaurantExpense séparé
class RestaurantExpense:
    restaurant_id: int
    category_id: int
    amount: Decimal

# Après : FinanceTransaction unifié
class FinanceTransaction:
    entity_id: int  # RESTO
    category_id: int  # finance_categories
    amount: Decimal
    cost_center_id: int  # Optional - pour analyse restaurant
```

### 4.3 Mapping catégories

| Restaurant Category | Finance Category | Code |
|---------------------|------------------|------|
| Alimentation | Achats alimentaires | FOOD_PURCHASE |
| Boissons | Achats boissons | BEV_PURCHASE |
| Personnel | Charges personnel | PERSONNEL |
| Loyer | Charges locatives | RENT |
| Énergie | Fluides & énergie | ENERGY |

**Checklist Phase 4:**
- [ ] Créer package `backend/services/restaurant/`
- [ ] Extraire modules depuis monolithe
- [ ] Script migration charges → finance_transactions
- [ ] Mettre à jour frontend Restaurant pour utiliser API finance
- [ ] Tests de non-régression
- [ ] Commit : "refactor: split restaurant.py into modules"

---

## PHASE 5 : Qualité & Documentation

**Objectif:** Stabiliser, documenter, tester

### 5.1 Tests à ajouter

| Type | Fichier | Couverture |
|------|---------|------------|
| Unit | `tests/test_finance_transactions.py` | Services finance |
| Unit | `tests/test_finance_import.py` | Import relevés |
| Integration | `tests/test_finance_api.py` | Endpoints API |
| E2E | `cypress/e2e/treasury.cy.js` | Parcours utilisateur |

### 5.2 Tests de performance

```python
# tests/test_finance_perf.py
def test_transactions_pagination_10k():
    """Pagination < 1s sur 10k transactions"""
    # Seed 10k transactions
    # Mesurer temps réponse
    assert response_time < 1.0
```

### 5.3 Mettre à jour README.md

```markdown
# Mon Projet - Gestion Multi-Entités

## Architecture
- **Épicerie HQ** : Gestion stock, catalogue, fournisseurs
- **Restaurant HQ** : Menu, consommation, prévisions
- **Trésorerie HQ** : Transactions, rapprochement, analytics

## Démarrage rapide
[voir DEMARRAGE_RAPIDE.md]

## Structure
backend/
  api/           # Routes FastAPI
  services/      # Logique métier
    finance/     # Module trésorerie unifié
    restaurant/  # Module restaurant (modulaire)
  schemas/       # Pydantic models

frontend/
  features/
    treasury/    # Pages trésorerie
    restaurant/  # Pages restaurant
    catalog/     # Pages épicerie
```

### 5.4 Checklist finale

- [ ] Tous les tests passent
- [ ] Documentation à jour
- [ ] Plus de fichiers dans `legacy/`
- [ ] Scripts organisés et documentés
- [ ] Performance validée (< 1s pagination)
- [ ] Pas de duplication API bank-statements

---

## Ordre d'exécution recommandé

```
Semaine 1-2 : PHASE 1 (Nettoyage)
    ↓
Semaine 3-4 : PHASE 2 (Backend Trésorerie)
    ↓
Semaine 5-6 : PHASE 3 (Frontend UX)
    ↓
Semaine 7-8 : PHASE 4 (Refacto Restaurant)
    ↓
Semaine 9   : PHASE 5 (Tests & Docs)
```

## Risques et mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Régression données | Haut | Backup DB avant migration |
| Casse frontend | Moyen | Feature flags, déploiement progressif |
| Perte fonctionnalité | Moyen | Tests e2e avant/après |
| Temps sous-estimé | Moyen | Prioriser Phase 1-2-3, différer Phase 4 si nécessaire |

---

## Fichiers clés à modifier

### Backend
- `backend/api/finance.py` - Consolider endpoints
- `backend/api/restaurant.py` - Déprécier bank-statements
- `backend/services/restaurant.py` → `backend/services/restaurant/`
- `backend/schemas/finance.py` - Unifier schémas

### Frontend
- `frontend/src/app/routes.jsx` - Nouvelles routes trésorerie
- `frontend/src/features/treasury/` - Nouvelles pages
- `frontend/src/features/finance/` - Intégrer CategoryInlineEdit

### Documentation
- `docs/PLAN_CONSOLIDATION_2025-12.md` - Ce document
- `README.md` - Mettre à jour

---

## Validation du plan

**Pour démarrer, confirmez :**
- [ ] Phase 1 (Nettoyage) peut commencer immédiatement
- [ ] Backup de la base de données disponible
- [ ] Environnement de dev isolé pour tester migrations

**Questions en suspens :**
1. Y a-t-il des scripts dans `scripts/` actuellement utilisés en production (cron) ?
2. Les données EUROCIEL sont-elles nécessaires ou archivables ?
3. Préférence pour la navigation Trésorerie : sidebar ou onglets horizontaux ?
