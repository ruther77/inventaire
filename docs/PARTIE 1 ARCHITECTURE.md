# PARTIE 1: ARCHITECTURE ACTUELLE

## 1.1 Frontend (23 Modules)

### Modules Principaux
| Module | Fichiers | Rôle |
|--------|----------|------|
| `catalog/` | 8 fichiers | Gestion produits, CatalogSmartDemo (970 lignes) |
| `finance/` | 12 fichiers | Dashboard, transactions, rapprochement, imports |
| `restaurant/` | 15 fichiers | Plats, ingrédients, coûts, marges |
| `stock/` | 6 fichiers | Mouvements, alertes, inventaires |
| `operations/` | 4 fichiers | Pilotage opérationnel, imports |
| `intelligence/` | 8 fichiers | Scoring fournisseurs, anomalies, forecasting |
| `supply/` | 3 fichiers | Plan d'approvisionnement, EOQ |
| `prices/` | 2 fichiers | Historique prix, comparaisons |
| `cockpit/` | 2 fichiers | Dashboard unifié |
| `invoices/` | 3 fichiers | Import/scan factures |

### Hooks Principaux (50 fichiers)
```
hooks/
├── useFinance.js (250+ lignes)        # Transactions, comptes, catégorisation
├── useFinanceCategories.js            # Categories, trésorerie, timeline
├── useSupplierScoring.js (200 lignes) # Scoring 7 dimensions + legacy
├── useInvoiceImport.js (150 lignes)   # Extraction, import, zero-click
├── useBankReconciliation.js           # Rapprochement bancaire complet
├── useInventoryIntelligence.js        # EOQ, safety stock, classifications
├── useRestaurant.js                   # Plats, ingrédients, coûts
├── useCatalog.js                      # Produits, fournisseurs, catégories
├── useStock.js                        # Mouvements, alertes, snapshots
└── useProducts.js                     # Produits épicerie
```

### Flux de Données Frontend
```
User Action → Hook (React Query) → API Call → Backend
                    ↓
              Cache invalidation → Refetch → UI Update
```

---

## 1.2 Backend (35 Routers, 15,021 lignes)

### API Routes
| Endpoint | Lignes | Fonctionnalités |
|----------|--------|-----------------|
| `/auth/*` | 400+ | JWT, refresh tokens, session |
| `/catalog/*` | 800+ | CRUD produits, fournisseurs |
| `/finance/*` | 1,200+ | Comptes, transactions, catégories |
| `/bank-reconciliation/*` | 600+ | Matching relevés/factures |
| `/supplier-scoring/*` | 500+ | Scoring 7 dimensions |
| `/restaurant/*` | 1,500+ | Menu, ingrédients, food cost |
| `/invoices/*` | 800+ | Import, extraction PDF/OCR |
| `/stock/*` | 700+ | Mouvements, alertes, timeseries |
| `/intelligence/*` | 1,000+ | Anomalies, forecasting, EOQ |
| `/dashboard/*` | 400+ | Métriques consolidées |

### Services Backend (21+ modules)
```
backend/services/
├── finance/
│   ├── accounts.py        # Gestion comptes bancaires
│   ├── transactions.py    # CRUD transactions
│   ├── stats.py           # Statistiques financières
│   └── views.py           # Agrégations complexes
├── catalog/
│   ├── products.py        # CRUD produits
│   ├── suppliers.py       # Gestion fournisseurs
│   └── categories.py      # Catégories produits
├── stock/
│   ├── movements.py       # Entrées/sorties stock
│   └── alerts.py          # Seuils et alertes
├── restaurant/
│   ├── plats.py           # Gestion plats
│   ├── ingredients.py     # Mapping ingrédients
│   └── costs.py           # Calcul food cost
└── zero_click_jobs.py     # Jobs automatiques
```

### Core Business Logic (60+ modules)
```
core/
├── invoice_workflow.py (439 lignes)      # Import factures → stock
├── finance/
│   ├── reconciliation.py (800+ lignes)   # Rapprochement bancaire
│   ├── supplier_scoring.py (756 lignes)  # Scoring 7 dimensions
│   ├── event_sourcing.py                 # Event sourcing finance
│   └── categorization.py                 # Auto-catégorisation
├── bank_import/
│   ├── orchestrator.py                   # Orchestration imports
│   ├── bnp_parser.py                     # Parser BNP
│   └── generic_parser.py                 # Parser générique
├── restaurant_costs.py                   # Food cost calculation
├── inventory_intelligence.py             # EOQ, safety stock
└── anomaly_detection.py                  # Détection anomalies
```

---

## 1.3 Base de Données

### Tables Principales
```sql
-- Multi-tenant
tenants (id, code, name)                    -- epicerie=1, restaurant=2

-- Catalogue
produits (id, tenant_id, nom, fournisseur_id, prix_achat)
categories (id, tenant_id, nom, parent_id)

-- Finance
finance_accounts (id, tenant_id, label, balance)
finance_transactions (id, account_id, amount, date, category_id)
finance_categories (id, tenant_id, name, type, parent_id)
finance_bank_statements (id, tenant_id, file_path, status)
finance_bank_statement_lines (id, statement_id, amount, label)
bank_reconciliations (id, transaction_id, invoice_id, confidence)

-- Stock
mouvements_stock (id, produit_id, quantite, type, date)
inventory_alerts (id, produit_id, threshold, current_qty)

-- Restaurant
restaurant_plats (id, tenant_id, nom, prix_vente)
restaurant_ingredients (id, tenant_id, nom, prix_unitaire)
restaurant_plat_ingredients (plat_id, ingredient_id, quantite)

-- Scoring
supplier_scores (id, supplier_id, dimension, score, date)
supplier_score_history (id, supplier_id, overall_score, date)
```

---

# PARTIE 2: WORKFLOWS EXISTANTS

## 2.1 Workflow Import Factures

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPORT FACTURE FOURNISSEUR                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Upload fichier (PDF/Image)                                  │
│     └──► POST /invoices/extract                                 │
│          └──► OCR/LLM extraction                                │
│               └──► Retourne: fournisseur, date, lignes[]        │
│                                                                  │
│  2. Validation utilisateur                                      │
│     └──► UI: Correction/Confirmation des lignes                 │
│                                                                  │
│  3. Import final                                                │
│     └──► POST /invoices/import                                  │
│          ├──► core/invoice_workflow.py:import_invoice()         │
│          │    ├──► Création mouvement_stock (type='entree')     │
│          │    ├──► MAJ prix_achat si changé                     │
│          │    ├──► Historisation prix (produits_price_history)   │
│          │    └──► Création finance_transaction                 │
│          └──► Retourne: invoice_id, stock_movements[]           │
│                                                                  │
│  4. Post-traitement automatique                                 │
│     └──► Recalcul supplier_scores (si enabled)                  │
│     └──► Invalidation cache dashboard                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Fichiers impliqués**:
- `frontend/src/features/invoices/InvoiceImportPage.jsx`
- `frontend/src/hooks/useInvoiceImport.js`
- `backend/api/invoices.py`
- `core/invoice_workflow.py` (lignes 179-439)

---

## 2.2 Workflow Rapprochement Bancaire

```
┌─────────────────────────────────────────────────────────────────┐
│                   RAPPROCHEMENT BANCAIRE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Import relevé bancaire                                      │
│     └──► POST /bank-reconciliation/import                       │
│          ├──► Parsing (BNP/Générique CSV/OFX)                   │
│          └──► Création finance_bank_statement_lines[]           │
│                                                                  │
│  2. Matching automatique                                        │
│     └──► POST /bank-reconciliation/auto-match                   │
│          └──► core/finance/reconciliation.py                    │
│               ├──► Match par montant exact                      │
│               ├──► Match par date ±3 jours                      │
│               ├──► Match par label (fuzzy)                      │
│               └──► Retourne: matches[] avec confidence score    │
│                                                                  │
│  3. Validation manuelle                                         │
│     └──► UI: Accepter/Rejeter suggestions                       │
│     └──► PUT /bank-reconciliation/{id}/confirm                  │
│                                                                  │
│  4. Création transactions                                       │
│     └──► Pour lignes non-matchées:                              │
│          └──► POST /finance/transactions (auto-catégorisation)  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Fichiers impliqués**:
- `frontend/src/features/finance/BankReconciliationPage.jsx`
- `frontend/src/hooks/useBankReconciliation.js`
- `backend/api/bank_reconciliation.py`
- `core/finance/reconciliation.py`
- `core/bank_import/orchestrator.py`

---

## 2.3 Workflow Scoring Fournisseurs

```
┌─────────────────────────────────────────────────────────────────┐
│                   SCORING FOURNISSEURS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  7 Dimensions (pondérées):                                      │
│  ┌──────────────────────┬────────┬─────────────────────────────┐│
│  │ Dimension            │ Poids  │ Calcul                      ││
│  ├──────────────────────┼────────┼─────────────────────────────┤│
│  │ Delivery Reliability │ 25%    │ Livraisons à temps/total    ││
│  │ Quality              │ 20%    │ Retours/réclamations        ││
│  │ Price Competitiveness│ 20%    │ Écart prix marché           ││
│  │ Lead Time            │ 15%    │ Délai moyen livraison       ││
│  │ Flexibility          │ 10%    │ Commandes urgentes OK       ││
│  │ Communication        │  5%    │ Réactivité                  ││
│  │ Financial Stability  │  5%    │ Respect délais paiement     ││
│  └──────────────────────┴────────┴─────────────────────────────┘│
│                                                                  │
│  Trigger: POST /supplier-scoring/recalculate                    │
│  └──► core/finance/supplier_scoring.py:calculate_all_scores()   │
│       └──► Agrège données 12 derniers mois                      │
│       └──► Calcule score par dimension                          │
│       └──► Calcule score global pondéré                         │
│       └──► Stocke dans supplier_scores + supplier_score_history │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Fichiers impliqués**:
- `frontend/src/features/intelligence/SupplierScoringPage.jsx`
- `frontend/src/hooks/useSupplierScoring.js`
- `backend/api/supplier_scoring.py`
- `core/finance/supplier_scoring.py` (lignes 64-756)

---

## 2.4 Workflow Restaurant (Épicerie → Restaurant)

```
┌─────────────────────────────────────────────────────────────────┐
│                   LIAISON ÉPICERIE → RESTAURANT                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Mapping Ingrédients                                         │
│     restaurant_epicerie_sku_map:                                │
│     ┌─────────────────┬────────────────┬────────────────┐       │
│     │ ingredient_id   │ produit_id     │ conversion_rate│       │
│     │ (restaurant)    │ (épicerie)     │                │       │
│     ├─────────────────┼────────────────┼────────────────┤       │
│     │ 1 (Farine)      │ 42 (Farine 5kg)│ 0.2 (1kg=0.2)  │       │
│     │ 2 (Tomates)     │ 15 (Tomates kg)│ 1.0            │       │
│     └─────────────────┴────────────────┴────────────────┘       │
│                                                                  │
│  2. Calcul Food Cost                                            │
│     └──► GET /restaurant/plats/{id}/cost                        │
│          └──► core/restaurant_costs.py:calculate_plat_cost()    │
│               ├──► Récupère ingrédients du plat                 │
│               ├──► Pour chaque ingrédient:                      │
│               │    └──► Récupère prix via mapping épicerie      │
│               └──► Retourne: coût_total, marge, food_cost_%     │
│                                                                  │
│  3. Alertes Marges                                              │
│     └──► Seuil global: 30% food cost                            │
│     └──► Alerte si plat dépasse seuil                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Fichiers impliqués**:
- `frontend/src/features/restaurant/RestaurantCostManagement.jsx`
- `frontend/src/hooks/useRestaurant.js`
- `backend/api/restaurant.py`
- `core/restaurant_costs.py`

---

# PARTIE 3: PROBLÈMES CRITIQUES IDENTIFIÉS (15)

## 3.1 Problèmes Data Flow

### P1: Pas de prévention ré-import factures
**Localisation**: `core/invoice_workflow.py`
**Problème**: Une même facture peut être importée plusieurs fois
**Impact**: Doublons stock, transactions dupliquées
**Fix requis**:
```python
# Ajouter dans processed_invoices
ALTER TABLE processed_invoices ADD COLUMN file_hash VARCHAR(64) UNIQUE;
# Vérifier hash avant import
```

### P2: Détection fournisseur limitée (8 regex)
**Localisation**: `core/invoice_workflow.py:89-120`
**Problème**: Map regex statique avec seulement 8 fournisseurs
**Impact**: Fournisseurs non reconnus → import manuel
**Fix requis**:
```python
# Migrer vers table supplier_aliases dynamique
CREATE TABLE supplier_aliases (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER REFERENCES dim_supplier(id),
    alias VARCHAR(255),
    pattern_type VARCHAR(20), -- 'exact', 'contains', 'regex'
    tenant_id INTEGER
);
```

### P3: Stock initial non initialisé
**Localisation**: `backend/api/stock.py`
**Problème**: `current_stock` parfois NULL si jamais de mouvement
**Impact**: Calculs erronés, division par zéro
**Fix requis**:
```sql
-- Ajouter valeur par défaut
ALTER TABLE produits ALTER COLUMN stock_initial SET DEFAULT 0;
UPDATE produits SET stock_initial = 0 WHERE stock_initial IS NULL;
```

### P4: Colonne label manquante dans finance_transactions
**Localisation**: `backend/services/finance/transactions.py`
**Problème**: Le code utilise `label` mais la colonne n'existe pas
**Impact**: Erreur 500 sur certaines requêtes
**Fix requis**:
```sql
ALTER TABLE finance_transactions ADD COLUMN label VARCHAR(255);
```

---

## 3.2 Problèmes Sync Multi-Tenant

### P5: Pas de sync temps réel Épicerie → Restaurant
**Localisation**: `core/restaurant_costs.py`
**Problème**: Prix épicerie mis à jour mais restaurant non notifié
**Impact**: Food cost calculé avec anciens prix
**Fix requis**:
- Ajouter système d'événements inter-tenant
- Invalider cache restaurant quand prix épicerie change

### P6: Tenant IDs hardcodés dans finance
**Localisation**: `backend/services/finance/*.py`
**Problème**: `tenant_id=1` hardcodé dans plusieurs endroits
**Impact**: Finance ne fonctionne que pour épicerie
**Fix requis**: Utiliser `current_user.tenant_id` partout

---

## 3.3 Problèmes Business Logic

### P7: Seuil marge global (pas par plat/catégorie)
**Localisation**: `core/restaurant_costs.py:45`
**Problème**: Seuil 30% pour tous les plats
**Impact**: Pas de différenciation entrées/plats/desserts
**Fix requis**:
```python
# Ajouter seuils par catégorie
plat_categories.target_food_cost_percent
```

### P8: Multi-devise non supporté
**Localisation**: Global
**Problème**: Tout en EUR hardcodé
**Impact**: Impossible d'avoir fournisseurs internationaux
**Fix requis**: Ajouter currency_code aux transactions

### P9: Seuils fournisseurs statiques
**Localisation**: `core/finance/supplier_scoring.py`
**Problème**: Seuils de scoring identiques pour tous
**Impact**: PME et grands comptes traités pareil
**Fix requis**: Seuils dynamiques par catégorie fournisseur

---

## 3.4 Problèmes Techniques

### P10: Event handling incomplet
**Localisation**: `core/finance/event_sourcing.py`
**Problème**: Certains events non gérés (ex: StockCorrectionEvent)
**Impact**: Historique incomplet

### P11: Pas de job scheduling async
**Localisation**: `backend/services/zero_click_jobs.py`
**Problème**: Jobs exécutés de façon synchrone
**Impact**: Timeout sur gros volumes

### P12: Contraintes uniques manquantes
**Localisation**: Migrations
**Problème**: Pas de contrainte unique sur (supplier_id, date) dans supplier_scores
**Impact**: Scores dupliqués possibles

### P13: Pas de soft delete
**Localisation**: Global
**Problème**: DELETE supprime définitivement
**Impact**: Pas d'audit trail, pas de récupération

### P14: Snapshots inventaire pas toujours dispo
**Localisation**: `backend/api/stock.py`
**Problème**: Snapshot demandé mais table vide
**Impact**: Comparaisons inventaire impossibles

### P15: Formats import limités
**Localisation**: `core/bank_import/`
**Problème**: Seulement BNP CSV supporté nativement
**Impact**: Autres banques nécessitent conversion manuelle

---

# PARTIE 4: PLAN D'IMPLÉMENTATION PAGE PAR PAGE

## Phase 1: Corrections Critiques (Prérequis)

### 1.1 Migrations Base de Données
```sql
-- P4: Ajouter colonne label
ALTER TABLE finance_transactions ADD COLUMN IF NOT EXISTS label VARCHAR(255);

-- P3: Stock initial
ALTER TABLE produits ALTER COLUMN stock_initial SET DEFAULT 0;
UPDATE produits SET stock_initial = COALESCE(stock_initial, 0);

-- P1: Hash factures
ALTER TABLE processed_invoices ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64);
CREATE UNIQUE INDEX IF NOT EXISTS idx_processed_invoices_hash ON processed_invoices(file_hash);

-- P12: Contrainte unique scoring
CREATE UNIQUE INDEX IF NOT EXISTS idx_supplier_scores_unique
ON supplier_scores(supplier_id, dimension, DATE(calculated_at));
```

### 1.2 Fix Tenant ID Hardcodé
**Fichiers à modifier**:
- `backend/services/finance/accounts.py`
- `backend/services/finance/transactions.py`
- `backend/services/finance/stats.py`

---

## Phase 2: Pages Épicerie

### 2.1 CatalogPage (/catalog)
**État actuel**: Fonctionne, données réelles
**Améliorations**:
- [ ] Ajouter indication sync Restaurant
- [ ] Afficher si produit utilisé comme ingrédient

### 2.2 StockPage (/stock)
**État actuel**: Mouvements affichés
**Améliorations**:
- [ ] Fix stock initial NULL
- [ ] Ajouter graphique évolution stock
- [ ] Alertes seuils en temps réel

### 2.3 InvoicesPage (/operations/invoices)
**État actuel**: Import fonctionnel
**Améliorations**:
- [ ] Prévention ré-import (P1)
- [ ] Détection fournisseur dynamique (P2)
- [ ] Afficher historique imports avec statuts

### 2.4 SupplyPage (/supply)
**État actuel**: Plan appro basique
**Améliorations**:
- [ ] Intégrer scoring fournisseurs
- [ ] Suggestions basées sur EOQ

---

## Phase 3: Pages Finance

### 3.1 FinanceOverview (/finances)
**État actuel**: Dashboard avec vraies données
**Améliorations**:
- [ ] Graphique trésorerie interactif
- [ ] Prévisions basées sur récurrence
- [ ] Export comptable

### 3.2 FinanceAccountsPage (/finances/accounts)
**État actuel**: Cards comptes, vraies données
**Améliorations**:
- [ ] Sync avec banque (API ou import)
- [ ] Alertes solde bas

### 3.3 FinanceTransactionsPage (/finances/transactions)
**État actuel**: Liste avec filtres
**Améliorations**:
- [ ] Auto-catégorisation IA
- [ ] Règles récurrentes
- [ ] Fix label (P4)

### 3.4 BankReconciliationPage (/finances/reconciliation)
**État actuel**: Matching automatique
**Améliorations**:
- [ ] Support multi-format (P15)
- [ ] Améliorer confidence IA
- [ ] Règles de matching personnalisées

### 3.5 FinanceSupplierPortfolioPage (/finances/fournisseurs)
**État actuel**: Nouvelle page créée
**Améliorations**:
- [ ] Connecter vraies données encours
- [ ] Actions: commander, voir historique
- [ ] Intégrer scoring

---

## Phase 4: Pages Restaurant

### 4.1 RestaurantPlatsPage (/restaurant/plats)
**État actuel**: Liste plats
**Améliorations**:
- [ ] Food cost temps réel
- [ ] Alertes marge par catégorie (P7)

### 4.2 RestaurantIngredientsPage (/restaurant/ingredients)
**État actuel**: Liste ingrédients
**Améliorations**:
- [ ] Mapping auto épicerie
- [ ] Alertes rupture stock épicerie

### 4.3 RestaurantCostManagement (/restaurant/costs)
**État actuel**: Calcul coûts
**Améliorations**:
- [ ] Sync temps réel prix épicerie (P5)
- [ ] Seuils par catégorie (P7)
- [ ] Historique variations coûts

---

## Phase 5: Pages Intelligence/IA

### 5.1 SupplierScoringPage (/intelligence/scoring)
**État actuel**: Scoring 7 dimensions
**Améliorations**:
- [ ] Seuils dynamiques (P9)
- [ ] Recommandations IA
- [ ] Comparaison fournisseurs

### 5.2 AnomalyDetectionPage (/intelligence/anomalies)
**État actuel**: Détection basique
**Améliorations**:
- [ ] ML pour patterns
- [ ] Alertes temps réel
- [ ] Actions correctives

### 5.3 ForecastingPage (/intelligence/forecasting)
**État actuel**: Prévisions simples
**Améliorations**:
- [ ] Saisonnalité
- [ ] Intégration événements

---

## Phase 6: Workflows Automatiques

### 6.1 Workflow Import Intelligent
```
Détection format → Parser adapté → Extraction IA → Validation → Import
                                                       ↓
                                            Prévention doublons (hash)
```

### 6.2 Workflow Sync Prix
```
Prix épicerie modifié → Event émis → Restaurant notifié → Cache invalidé → Food cost recalculé
```

### 6.3 Workflow Alertes
```
Seuil dépassé → Alerte créée → Notification → Action suggérée
```

---

# PARTIE 5: FICHIERS CRITIQUES À MODIFIER

## Backend
| Fichier | Lignes | Modifications |
|---------|--------|---------------|
| `core/invoice_workflow.py` | 179-439 | P1, P2: hash + supplier_aliases |
| `core/finance/reconciliation.py` | 800+ | P15: multi-format |
| `core/restaurant_costs.py` | 45+ | P5, P7: sync + seuils |
| `backend/services/finance/*.py` | 4 fichiers | P4, P6: label + tenant |
| `core/finance/supplier_scoring.py` | 64-756 | P9: seuils dynamiques |

## Frontend
| Fichier | Lignes | Modifications |
|---------|--------|---------------|
| `src/features/invoices/InvoiceImportPage.jsx` | 400+ | UI prévention doublons |
| `src/features/restaurant/RestaurantCostManagement.jsx` | 300+ | Sync temps réel |
| `src/features/finance/FinanceTransactionsPage.jsx` | 400+ | Label display |
| `src/hooks/useInvoiceImport.js` | 150+ | Hash verification |

## Migrations
| Migration | Description |
|-----------|-------------|
| `add_label_to_transactions.py` | P4 |
| `add_file_hash_to_invoices.py` | P1 |
| `create_supplier_aliases.py` | P2 |
| `add_category_thresholds.py` | P7 |

---

# PARTIE 6: ORDRE D'EXÉCUTION

## Semaine 1: Fondations
1. [ ] Créer migrations (P1, P3, P4, P12)
2. [ ] Fix tenant_id hardcodé (P6)
3. [ ] Tester tous les endpoints existants

## Semaine 2: Import/Stock
4. [ ] Implémenter hash factures (P1)
5. [ ] Créer table supplier_aliases (P2)
6. [ ] Fix stock initial (P3)

## Semaine 3: Finance
7. [ ] Ajouter label transactions (P4)
8. [ ] Multi-format import bancaire (P15)
9. [ ] Améliorer rapprochement

## Semaine 4: Restaurant
10. [ ] Sync temps réel prix (P5)
11. [ ] Seuils par catégorie (P7)
12. [ ] Tests intégration Épicerie ↔ Restaurant

## Semaine 5: Intelligence
13. [ ] Seuils scoring dynamiques (P9)
14. [ ] Alertes temps réel
15. [ ] Jobs async (P11)

## Semaine 6: Polish
16. [ ] Soft delete (P13)
17. [ ] Snapshots inventaire (P14)
18. [ ] Documentation API

---

# VALIDATION

## Tests à Effectuer
- [ ] Import facture avec même hash → rejeté
- [ ] Nouveau fournisseur → détecté via alias
- [ ] Prix épicerie modifié → food cost restaurant MAJ
- [ ] Transaction sans label → pas d'erreur
- [ ] Scoring recalculé → pas de doublons
- [ ] Import relevé Crédit Agricole → parsing OK

---

# PARTIE 7: MAPPING PAGE → STACK COMPLET

Cette section documente chaque page avec son flux complet depuis le frontend jusqu'à la base de données.

## 7.1 COCKPIT (Vue Unifiée)

### CockpitUnifiedPage (`/`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /                                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/cockpit/CockpitUnifiedPage.jsx                  │
│ ├── Layout: src/app/layouts/DashboardLayout.jsx                             │
│ └── Hooks:                                                                   │
│     ├── useCockpit() → useCockpitOverview, useCockpitLiveKPIs              │
│     ├── useCockpitAlerts({ severity, acknowledged })                        │
│     └── useCockpitHealth()                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /cockpit/overview       → Vue d'ensemble consolidée                │
│ ├── GET  /cockpit/kpis/live      → KPIs temps réel (refetch 30s)           │
│ ├── GET  /cockpit/alerts         → Alertes actives                          │
│ ├── GET  /cockpit/health         → État de santé système                    │
│ └── POST /cockpit/alerts/{id}/ack → Acquitter alerte                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/cockpit.py                                          │
│ └── Service: Agrégation multi-source (pas de service dédié)                │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE (lecture multi-tables)                                              │
│ ├── produits (stock, alertes)                                               │
│ ├── finance_transactions (CA, trésorerie)                                   │
│ ├── mouvements_stock (activité récente)                                     │
│ ├── detected_anomalies (alertes)                                            │
│ ├── supplier_scores (scoring fournisseurs)                                  │
│ └── restaurant_plats (si tenant restaurant)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7.2 OPERATIONS (Catalogue, Stock, Factures)

### CatalogPage (`/operations/catalogue`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /operations/catalogue                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/catalog/CatalogSmartDemo.jsx (970 lignes)       │
│ └── Hooks:                                                                   │
│     ├── useProducts({ page, per_page, category, supplier_id, q })          │
│     ├── useCatalogMutations() → useCreateProduct, useUpdateProduct         │
│     ├── useCategories()                                                     │
│     └── useSuppliers()                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET    /catalog/products     → Liste paginée avec filtres               │
│ ├── GET    /catalog/products/:id → Détail produit                           │
│ ├── POST   /catalog/products     → Création produit                         │
│ ├── PUT    /catalog/products/:id → Mise à jour complète                     │
│ ├── PATCH  /catalog/products/:id → Mise à jour partielle (prix, stock)      │
│ ├── DELETE /catalog/products/:id → Suppression (soft delete)                │
│ ├── GET    /catalog/categories   → Liste catégories                         │
│ └── GET    /catalog/vendors      → Liste fournisseurs                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/catalog.py                                          │
│ ├── Service: backend/services/catalog/products.py                           │
│ └── Core: core/catalog_sql_repository.py                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── produits (id, tenant_id, nom, fournisseur_id, prix_vente, prix_achat)  │
│ ├── categories (id, tenant_id, nom, parent_id)                             │
│ ├── dim_supplier (id, tenant_id, name, contact)                            │
│ ├── produits_barcodes (id, produit_id, barcode)                            │
│ └── produits_price_history (id, produit_id, prix_achat, date_change)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### StockMovementsPage (`/operations/stock`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /operations/stock                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/stock/StockMovementsPage.jsx                    │
│ └── Hooks:                                                                   │
│     ├── useStockTimeseries({ windowDays, productId })                       │
│     ├── useRecentMovements({ limit, productId })                            │
│     └── useStockAdjustment() → Mutation                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /stock/movements/timeseries → Agrégation par période               │
│ ├── GET  /stock/movements/recent     → Derniers mouvements                  │
│ ├── GET  /stock/movements/summary    → Résumé stock                         │
│ ├── POST /stock/adjustments          → Ajustement inventaire                │
│ └── GET  /stock/alerts               → Produits sous seuil                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/stock.py                                            │
│ └── Service: backend/services/stock/movements.py                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── mouvements_stock (id, produit_id, quantite, type, date_mouvement)      │
│ ├── produits (stock_actuel, seuil_alerte)                                   │
│ └── inventory_alerts (id, produit_id, threshold, current_qty)              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### ImportPage (`/operations/factures/import`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /operations/factures/import                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/invoices/ImportPage.jsx                         │
│ └── Hooks:                                                                   │
│     ├── useInvoiceExtract() → Extraction OCR/LLM                            │
│     ├── useInvoiceImport() → Import validé                                  │
│     └── useInvoiceZeroClick() → Import automatique                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── POST /invoices/extract         → OCR + LLM extraction                   │
│ ├── POST /invoices/import          → Import après validation                │
│ ├── POST /invoices/zero-click      → Import automatique complet             │
│ ├── GET  /invoices/history         → Historique imports                     │
│ └── GET  /invoices/{id}/details    → Détails facture importée               │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/invoices.py                                         │
│ ├── Service: backend/services/zero_click_jobs.py                            │
│ └── Core: core/invoice_workflow.py (179-439 lignes critiques)               │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── processed_invoices (id, tenant_id, file_path, supplier_id, status)     │
│ ├── fact_invoices (id, invoice_id, line_number, product_id, qty, price)    │
│ ├── mouvements_stock (entrées créées)                                       │
│ ├── produits (prix_achat mis à jour)                                        │
│ └── produits_price_history (nouvel historique)                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### PricesPage (`/operations/prix`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /operations/prix                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/prices/PricesPage.jsx                           │
│ └── Hooks:                                                                   │
│     ├── usePriceHistory({ productId, limit })                               │
│     └── usePriceComparison({ suppliers[] })                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /prices/history           → Historique prix par produit            │
│ ├── GET  /prices/comparison        → Comparaison multi-fournisseurs         │
│ └── GET  /prices/trends            → Tendances prix                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ └── Router: backend/api/prices.py                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── produits_price_history (prix_achat, date_change, source)               │
│ └── produits (prix_achat actuel)                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### SupplyPage (`/operations/approvisionnement`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /operations/approvisionnement                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/supply/SupplyPage.jsx                           │
│ └── Hooks:                                                                   │
│     ├── useSupplyPlan({ targetCoverage })                                   │
│     └── useCreateOrder() → Génération commande                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /supply/plan              → Plan approvisionnement                 │
│ ├── GET  /supply/suggestions       → Suggestions réappro                    │
│ └── POST /supply/orders            → Création commande                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/supply.py                                           │
│ └── Core: core/inventory_intelligence.py (EOQ, safety stock)               │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── produits (stock_actuel, seuil_alerte, delai_livraison)                 │
│ ├── mouvements_stock (pour calcul vélocité)                                 │
│ ├── dim_supplier (fournisseurs)                                             │
│ └── inventory_intelligence (EOQ, safety_stock pré-calculés)                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7.3 FINANCES

### FinanceOverview (`/finances/tresorerie`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /finances/tresorerie                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/finance/FinanceOverview.jsx                     │
│ └── Hooks:                                                                   │
│     ├── useFinanceAccounts()                                                │
│     ├── useDashboardMetrics()                                               │
│     └── useFinanceTimeline()                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /finance/accounts/overview → Soldes comptes                        │
│ ├── GET  /finance/stats             → Stats période                         │
│ ├── GET  /finance/timeline          → Timeline CA/dépenses                  │
│ └── GET  /dashboard/metrics         → Métriques globales                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/finance.py                                          │
│ ├── Service: backend/services/finance/stats.py                              │
│ └── Service: backend/services/finance/views.py                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── finance_accounts (id, tenant_id, label, balance)                       │
│ ├── finance_transactions (id, account_id, amount, date)                    │
│ └── finance_categories (id, name, type)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FinanceTransactionsPage (`/finances/transactions`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /finances/transactions                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/finance/FinanceTransactionsPage.jsx             │
│ └── Hooks:                                                                   │
│     ├── useFinanceTransactions({ entityId, categoryId, dateFrom... })      │
│     ├── useUpdateFinanceTransaction() → Mutation                            │
│     ├── useLockFinanceTransaction() → Verrouillage                          │
│     ├── useFinanceBatchCategorize() → Catégorisation masse                  │
│     ├── useCategoryFeedback() → Feedback ML (Phase 4)                       │
│     └── useCommonCorrections() → Corrections fréquentes                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET   /finance/transactions/search    → Liste paginée filtrée           │
│ ├── PUT   /finance/transactions/{id}      → Mise à jour                     │
│ ├── POST  /finance/transactions/{id}/lock → Verrouillage                    │
│ ├── POST  /finance/transactions/batch-categorize → Catégorisation          │
│ ├── POST  /finance/categories/feedback    → Enregistrer correction          │
│ └── GET   /finance/categories/suggestions/complete → Auto-complétion       │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/finance.py                                          │
│ ├── Service: backend/services/finance/transactions.py                       │
│ └── Core: core/finance/categorization.py (auto-catégorisation ML)          │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── finance_transactions (id, account_id, amount, label, category_id)      │
│ ├── finance_categories (id, name, type, parent_id)                          │
│ ├── finance_category_feedback (id, transaction_id, old_cat, new_cat)       │
│ └── finance_transaction_lines (détail lignes)                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### BankReconciliationPage (`/finances/rapprochement`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /finances/rapprochement                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/finance/BankReconciliationPage.jsx              │
│ └── Hooks:                                                                   │
│     ├── useReconciliationSummary({ daysBack })                              │
│     ├── useUnmatchedTransactions({ daysBack })                              │
│     ├── useUnmatchedInvoices()                                              │
│     ├── useRunReconciliation() → Mutation                                   │
│     ├── useCreateManualMatch() → Match manuel                               │
│     └── useSupplierAliases() → Gestion alias                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /bank-reconciliation/summary              → Résumé                 │
│ ├── GET  /bank-reconciliation/unmatched/transactions                        │
│ ├── GET  /bank-reconciliation/unmatched/invoices                            │
│ ├── POST /bank-reconciliation/run                  → Lancer matching        │
│ ├── POST /bank-reconciliation/manual-match         → Match manuel           │
│ ├── GET  /bank-reconciliation/supplier-aliases     → Liste alias            │
│ └── POST /bank-reconciliation/supplier-aliases     → Créer alias            │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/bank_reconciliation.py                              │
│ └── Core: core/finance/reconciliation.py (800+ lignes)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── finance_bank_statements (id, tenant_id, file_path, status)             │
│ ├── finance_bank_statement_lines (id, statement_id, amount, label)         │
│ ├── bank_reconciliations (id, line_id, invoice_id, confidence)             │
│ ├── supplier_aliases (id, supplier_id, alias, pattern_type)                │
│ └── processed_invoices (pour matching)                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FinanceAccountsPage (`/finances/comptes`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /finances/comptes                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/finance/FinanceAccountsPage.jsx                 │
│ └── Hooks:                                                                   │
│     ├── useFinanceAccounts()                                                │
│     ├── useFinanceAccount(accountId)                                        │
│     ├── useCreateFinanceAccount() → Mutation                                │
│     ├── useUpdateFinanceAccount() → Mutation                                │
│     └── useDeleteFinanceAccount() → Mutation                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET    /finance/accounts           → Liste comptes                      │
│ ├── GET    /finance/accounts/{id}      → Détail compte                      │
│ ├── POST   /finance/accounts           → Création                           │
│ ├── PUT    /finance/accounts/{id}      → Mise à jour                        │
│ └── DELETE /finance/accounts/{id}      → Suppression                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/finance.py                                          │
│ └── Service: backend/services/finance/accounts.py                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ └── finance_accounts (id, tenant_id, label, type, balance, bank_name)      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### FinanceImportsPage (`/finances/imports`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /finances/imports                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/finance/FinanceImportsPage.jsx                  │
│ └── Hooks:                                                                   │
│     ├── useFinanceImport() → Import CSV                                     │
│     ├── useFinanceImportPDF() → Import relevé PDF                           │
│     └── useDeduplicateTransactions() → Dédoublonnage                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── POST /finance/import/bank-statements     → Import CSV                   │
│ ├── POST /finance/import/bank-statements/pdf → Import PDF                   │
│ └── POST /finance/transactions/deduplicate   → Dédoublonnage                │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/finance.py                                          │
│ └── Core: core/bank_import/orchestrator.py, bnp_parser.py                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── finance_bank_statements (id, file_path, status, rows_imported)         │
│ └── finance_bank_statement_lines (lignes parsées)                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7.4 RESTAURANT

### FoodCostAnalysisPage (`/restaurant/food-cost`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /restaurant/food-cost                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/restaurant/FoodCostAnalysisPage.jsx             │
│ └── Hooks:                                                                   │
│     ├── useRestaurantFoodCostAnalysis({ period, targetFoodCost })          │
│     ├── useRestaurantOverview()                                             │
│     ├── useRestaurantAlerts()                                               │
│     └── useSimulatePlatPrice() → Simulation                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /restaurant/food-cost/analysis → Analyse food cost                 │
│ ├── GET  /restaurant/overview           → Vue d'ensemble                    │
│ ├── GET  /restaurant/alerts             → Alertes marges                    │
│ └── POST /restaurant/plats/{id}/simulate → Simulation prix                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/restaurant.py                                       │
│ ├── Service: backend/services/restaurant/costs.py                           │
│ └── Core: core/restaurant_costs.py                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── restaurant_plats (id, tenant_id, nom, prix_vente)                      │
│ ├── restaurant_plat_ingredients (plat_id, ingredient_id, quantite)         │
│ ├── restaurant_ingredients (id, prix_unitaire, unite)                      │
│ ├── restaurant_epicerie_sku_map (ingredient_id, produit_id, ratio)         │
│ ├── restaurant_plat_costs (coûts pré-calculés)                              │
│ └── produits (épicerie - pour prix ingrédients liés)                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### PlatsCatalogPage (`/restaurant/plats`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /restaurant/plats                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/restaurant/PlatsCatalogPage.jsx                 │
│ └── Hooks:                                                                   │
│     ├── useRestaurantPlats()                                                │
│     ├── useRestaurantPlatDetails(platId)                                    │
│     ├── useCreateRestaurantPlat() → Mutation                                │
│     ├── useDeleteRestaurantPlat() → Mutation                                │
│     ├── useAddIngredientToPlat() → Mutation                                 │
│     ├── useUpdateIngredientOnPlat() → Mutation                              │
│     └── useRemoveIngredientFromPlat() → Mutation                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET    /restaurant/plats                        → Liste plats           │
│ ├── GET    /restaurant/plats/{id}                   → Détail plat           │
│ ├── POST   /restaurant/plats                        → Création              │
│ ├── DELETE /restaurant/plats/{id}                   → Suppression           │
│ ├── POST   /restaurant/plats/{id}/ingredients       → Ajouter ingrédient    │
│ ├── PATCH  /restaurant/plats/{id}/ingredients/{iid} → Modifier quantité     │
│ └── DELETE /restaurant/plats/{id}/ingredients/{iid} → Retirer ingrédient    │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/restaurant.py                                       │
│ └── Service: backend/services/restaurant/plats.py                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── restaurant_plats (id, tenant_id, nom, description, prix_vente)         │
│ ├── restaurant_plat_ingredients (plat_id, ingredient_id, quantite)         │
│ └── plat_categories (id, nom)                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### IngredientsPage (`/restaurant/ingredients`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /restaurant/ingredients                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/restaurant/IngredientsPage.jsx                  │
│ └── Hooks:                                                                   │
│     ├── useRestaurantIngredients()                                          │
│     ├── useCreateRestaurantIngredient() → Mutation                          │
│     ├── useUpdateRestaurantIngredient() → Mutation                          │
│     ├── useDeleteRestaurantIngredient() → Mutation                          │
│     ├── useUpdateRestaurantIngredientPrice() → Mutation                     │
│     └── useRestaurantIngredientPriceHistory(ingredientId)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET    /restaurant/ingredients           → Liste ingrédients            │
│ ├── POST   /restaurant/ingredients           → Création                     │
│ ├── PUT    /restaurant/ingredients/{id}      → Mise à jour                  │
│ ├── DELETE /restaurant/ingredients/{id}      → Suppression                  │
│ ├── PUT    /restaurant/ingredients/{id}/price → Mise à jour prix            │
│ └── GET    /restaurant/ingredients/{id}/price-history                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ └── Router: backend/api/restaurant.py                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── restaurant_ingredients (id, tenant_id, nom, prix_unitaire, unite)      │
│ └── restaurant_ingredient_price_history (id, ingredient_id, prix, date)    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### LiensEpiceriePage (`/restaurant/liens`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /restaurant/liens                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/restaurant/LiensEpiceriePage.jsx                │
│ └── Hooks:                                                                   │
│     ├── useRestaurantIngredients()                                          │
│     ├── useEpicerieProducts()                                               │
│     ├── useLinkIngredientEpicerie() → Mutation                              │
│     ├── useUnlinkIngredientEpicerie() → Mutation                            │
│     ├── useUpdateIngredientRatio() → Mutation                               │
│     ├── useSyncIngredientPrices() → Sync depuis épicerie                    │
│     └── usePriceSyncStatus()                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /restaurant/epicerie-products      → Produits épicerie             │
│ ├── POST /restaurant/ingredients/{id}/link  → Créer lien                    │
│ ├── DELETE /restaurant/ingredients/{id}/link → Supprimer lien               │
│ ├── PUT  /restaurant/ingredients/{id}/ratio → Modifier ratio                │
│ ├── POST /restaurant/sync-prices            → Synchroniser prix             │
│ └── GET  /restaurant/sync-status            → État synchronisation          │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ └── Router: backend/api/restaurant.py                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── restaurant_epicerie_sku_map (ingredient_id, produit_id, ratio)         │
│ ├── restaurant_ingredients (mise à jour prix)                               │
│ └── produits (lecture prix épicerie)                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### RestaurantStockMovementsPage (`/restaurant/stock`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /restaurant/stock                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/restaurant/RestaurantStockMovementsPage.jsx     │
│ └── Hooks:                                                                   │
│     ├── useRestaurantStockMovements({ ingredientId, source, type })        │
│     ├── useRestaurantStockSummary()                                         │
│     ├── useRestaurantStockAnalytics(days)                                   │
│     ├── useRestaurantStockDailyByPlat({ dateFrom, dateTo })                │
│     └── useCreateRestaurantStockMovement() → Mutation                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /restaurant/stock/movements        → Liste mouvements              │
│ ├── GET  /restaurant/stock/summary          → Résumé stock                  │
│ ├── GET  /restaurant/stock/analytics        → Analytics                     │
│ ├── GET  /restaurant/stock/movements/daily-by-plat                          │
│ ├── GET  /restaurant/stock/movements/daily-by-category                      │
│ └── POST /restaurant/stock/movements        → Créer mouvement               │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ └── Router: backend/api/restaurant.py                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── restaurant_stock_movements (id, ingredient_id, quantite, type, date)   │
│ └── restaurant_ingredients (stock_actuel mis à jour)                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### RestaurantChargesPage (`/restaurant/charges`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /restaurant/charges                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/restaurant/RestaurantChargesPage.jsx            │
│ └── Hooks:                                                                   │
│     ├── useRestaurantExpenses()                                             │
│     ├── useRestaurantExpenseSummary()                                       │
│     ├── useRestaurantCategories()                                           │
│     ├── useRestaurantCostCenters()                                          │
│     └── useCreateRestaurantExpense() → Mutation                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /restaurant/charges/expenses       → Liste dépenses                │
│ ├── GET  /restaurant/charges/summary        → Résumé                        │
│ ├── GET  /restaurant/charges/categories     → Catégories                    │
│ ├── GET  /restaurant/charges/cost-centers   → Centres de coûts              │
│ └── POST /restaurant/charges/expenses       → Créer dépense                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ └── Router: backend/api/restaurant.py                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── restaurant_depenses (id, tenant_id, montant, date, category_id)        │
│ ├── restaurant_depense_categories (id, nom)                                 │
│ └── restaurant_cost_centers (id, nom)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7.5 INTELLIGENCE

### SupplierScoringOverviewPage (`/intelligence/scoring`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /intelligence/scoring                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/intelligence/SupplierScoringOverviewPage.jsx    │
│ └── Hooks:                                                                   │
│     ├── useSupplierScoring()                                                │
│     ├── useSuppliersRanking()                                               │
│     ├── useScoringDimensions()                                              │
│     ├── useCompareSuppliers(supplierIds[])                                  │
│     └── useRecordDelivery() → Mutation                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /supplier-scoring/overview         → Vue d'ensemble                │
│ ├── GET  /supplier-scoring/suppliers        → Liste avec scores             │
│ ├── GET  /supplier-scoring/suppliers/{id}   → Détail fournisseur            │
│ ├── GET  /supplier-scoring/dimensions       → Dimensions scoring            │
│ ├── GET  /supplier-scoring/compare          → Comparaison                   │
│ ├── POST /supplier-scoring/recalculate      → Recalculer scores             │
│ └── POST /supplier-scoring/record-delivery  → Enregistrer livraison         │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/supplier_scoring.py                                 │
│ └── Core: core/finance/supplier_scoring.py (756 lignes)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── supplier_scores (id, supplier_id, dimension, score, calculated_at)     │
│ ├── supplier_score_history (id, supplier_id, overall_score, date)          │
│ ├── supplier_delivery_log (id, supplier_id, on_time, date)                 │
│ ├── supplier_invoice_issues (id, supplier_id, issue_type, date)            │
│ └── dim_supplier (informations fournisseur)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### InventoryIntelligencePage (`/intelligence/stock`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /intelligence/stock                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/intelligence/InventoryIntelligencePage.jsx      │
│ └── Hooks:                                                                   │
│     ├── useInventoryIntelligenceSummary()                                   │
│     ├── useReorderPoints()                                                  │
│     ├── useStockoutPredictions()                                            │
│     ├── useDeadStock()                                                      │
│     ├── useABCXYZClassification()                                           │
│     ├── useReorderSuggestions()                                             │
│     └── useCalculateEOQ(productId)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /inventory-intelligence/summary        → Résumé                    │
│ ├── GET  /inventory-intelligence/reorder-points → Points de réappro         │
│ ├── GET  /inventory-intelligence/stockout-predictions                       │
│ ├── GET  /inventory-intelligence/dead-stock     → Stock mort                │
│ ├── GET  /inventory-intelligence/abc-xyz        → Classification            │
│ ├── GET  /inventory-intelligence/reorder-suggestions                        │
│ ├── GET  /inventory-intelligence/eoq/{id}       → Calcul EOQ                │
│ └── GET  /inventory-intelligence/safety-stock/{id}                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/inventory_intelligence.py                           │
│ └── Core: core/inventory_intelligence.py                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── inventory_intelligence (id, produit_id, eoq, safety_stock)             │
│ ├── inventory_classifications (id, produit_id, abc_class, xyz_class)       │
│ ├── produits (stock_actuel, seuil_alerte)                                   │
│ └── mouvements_stock (historique pour calculs)                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### ForecastPage (`/intelligence/previsions`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /intelligence/previsions                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/intelligence/ForecastPage.jsx                   │
│ └── Hooks:                                                                   │
│     ├── useForecastingSummary()                                             │
│     ├── useStockDepletionForecast()                                         │
│     ├── useCashFlowForecast()                                               │
│     ├── usePriceTrendForecast()                                             │
│     └── useForecastSales({ horizonDays, productId })                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /forecasting/summary            → Résumé prévisions                │
│ ├── GET  /forecasting/stock-depletion    → Prévision épuisement             │
│ ├── GET  /forecasting/cash-flow          → Prévision trésorerie             │
│ ├── GET  /forecasting/price-trends       → Tendances prix                   │
│ └── GET  /forecasting/sales              → Prévision ventes                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/forecasting.py                                      │
│ └── Core: core/forecasting.py                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── forecast_cache (id, type, data, calculated_at)                          │
│ ├── mouvements_stock (historique pour modèles)                              │
│ ├── finance_transactions (historique CA)                                    │
│ └── produits_price_history (tendances prix)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AnomaliesPage (`/intelligence/anomalies`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /intelligence/anomalies                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/intelligence/AnomaliesPage.jsx                  │
│ └── Hooks:                                                                   │
│     ├── useAnomalySummary({ daysBack })                                     │
│     ├── useTransactionOutliers()                                            │
│     ├── useDuplicateInvoices()                                              │
│     ├── useInvoiceSequenceGaps()                                            │
│     ├── useRoundAmounts()                                                   │
│     ├── useScanAnomalies() → Mutation                                       │
│     └── useResolveAnomaly() → Mutation                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /anomaly-detection/summary          → Résumé anomalies             │
│ ├── GET  /anomaly-detection/transaction-outliers                            │
│ ├── GET  /anomaly-detection/duplicate-invoices                              │
│ ├── GET  /anomaly-detection/sequence-gaps    → Ruptures séquence            │
│ ├── GET  /anomaly-detection/round-amounts    → Montants ronds               │
│ ├── POST /anomaly-detection/scan             → Lancer scan                  │
│ └── POST /anomaly-detection/{id}/resolve     → Résoudre                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/anomaly_detection.py                                │
│ └── Core: core/anomaly_detection.py                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── detected_anomalies (id, type, entity_id, severity, resolved)           │
│ ├── finance_transactions (transactions analysées)                           │
│ └── processed_invoices (factures analysées)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### MarginsPage (`/intelligence/marges`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /intelligence/marges                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/intelligence/MarginsPage.jsx                    │
│ └── Hooks:                                                                   │
│     ├── useMarginSummary()                                                  │
│     ├── useProductMargins({ category, sortBy })                             │
│     ├── useCategoryMargins()                                                │
│     ├── useProductPAMP(productId)                                           │
│     ├── useDishMargins() (pour restaurant)                                  │
│     └── useMarginAlerts()                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /margins/summary           → Résumé marges                         │
│ ├── GET  /margins/products          → Marges par produit                    │
│ ├── GET  /margins/categories        → Marges par catégorie                  │
│ ├── GET  /margins/products/{id}/pamp → PAMP produit                         │
│ ├── GET  /margins/dishes            → Marges plats restaurant               │
│ └── GET  /margins/alerts            → Alertes marges                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ └── Router: backend/api/margins.py                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── margin_snapshots (id, produit_id, margin_pct, date)                    │
│ ├── produits (prix_achat, prix_vente)                                       │
│ ├── categories (pour agrégation)                                            │
│ └── restaurant_plat_costs (marges plats)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7.6 PARAMETRES & ADMIN

### AuditTrailPage (`/parametres/audit`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /parametres/audit                                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/admin/AuditTrailPage.jsx                        │
│ └── Hooks:                                                                   │
│     ├── useAuditSummary()                                                   │
│     ├── useAuditEntries({ entityType, userId, dateFrom, dateTo })          │
│     ├── useSearchAuditEntries(query)                                        │
│     ├── useEntityHistory(entityType, entityId)                              │
│     ├── useUserActivity(userId)                                             │
│     ├── useSecurityEvents()                                                 │
│     └── useGenerateAuditReport() → Mutation                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET  /audit-trail/summary           → Résumé audit                      │
│ ├── GET  /audit-trail/entries           → Liste entrées                     │
│ ├── GET  /audit-trail/search            → Recherche                         │
│ ├── GET  /audit-trail/entity/{type}/{id}/history                            │
│ ├── GET  /audit-trail/user/{id}/activity                                    │
│ ├── GET  /audit-trail/security-events   → Événements sécurité               │
│ └── POST /audit-trail/report            → Générer rapport                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ └── Router: backend/api/audit_trail.py                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── audit_trail (id, user_id, entity_type, entity_id, action, timestamp)   │
│ ├── audit_log (legacy)                                                      │
│ └── app_users (informations utilisateur)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AdminUsersPage (`/admin/users`)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ROUTE: /admin/users                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ FRONTEND                                                                     │
│ ├── Component: src/features/admin/AdminUsersPage.jsx                        │
│ └── Hooks:                                                                   │
│     └── useAdmin() → CRUD utilisateurs                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ API ENDPOINTS                                                                │
│ ├── GET    /admin/users           → Liste utilisateurs                      │
│ ├── POST   /admin/users           → Créer utilisateur                       │
│ ├── PUT    /admin/users/{id}      → Modifier utilisateur                    │
│ └── DELETE /admin/users/{id}      → Supprimer utilisateur                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ BACKEND                                                                      │
│ ├── Router: backend/api/admin.py                                            │
│ └── Core: core/user_service.py                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ DATABASE                                                                     │
│ ├── app_users (id, username, email, role, tenant_id, hashed_password)      │
│ └── tenants (id, code, name)                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7.7 RÉSUMÉ DES TABLES PAR DOMAINE

### Tables Épicerie (tenant_id=1)
```
produits              # Catalogue produits
produits_barcodes     # Codes-barres
produits_price_history # Historique prix
categories            # Catégories produits
dim_supplier          # Fournisseurs
mouvements_stock      # Entrées/sorties
inventory_alerts      # Alertes seuils
processed_invoices    # Factures importées
fact_invoices         # Lignes factures
```

### Tables Restaurant (tenant_id=2)
```
restaurant_plats             # Menu plats
restaurant_ingredients       # Ingrédients
restaurant_plat_ingredients  # Composition plats
restaurant_plat_costs        # Coûts calculés
restaurant_epicerie_sku_map  # Liens épicerie
restaurant_stock_movements   # Mouvements ingrédients
restaurant_depenses          # Charges
restaurant_depense_categories
restaurant_cost_centers
restaurant_ingredient_price_history
restaurant_plat_price_history
```

### Tables Finance (tous tenants)
```
finance_accounts             # Comptes bancaires
finance_transactions         # Mouvements
finance_transaction_lines    # Détail lignes
finance_categories           # Catégories comptables
finance_bank_statements      # Relevés importés
finance_bank_statement_lines # Lignes relevés
bank_reconciliations         # Rapprochements
finance_category_feedback    # Feedback ML
```

### Tables Intelligence (tous tenants)
```
supplier_scores              # Scores fournisseurs
supplier_score_history       # Historique scores
supplier_delivery_log        # Logs livraisons
detected_anomalies           # Anomalies détectées
forecast_cache               # Prévisions en cache
inventory_intelligence       # EOQ, safety stock
inventory_classifications    # ABC-XYZ
margin_snapshots             # Snapshots marges
```

### Tables Système
```
tenants                      # Multi-tenant
app_users                    # Utilisateurs
audit_trail                  # Audit complet
event_log                    # Événements système
```

---

# PARTIE 8: DOCUMENTATION EXHAUSTIVE DES PAGES

Cette section documente de manière exhaustive chaque page, chaque bouton, chaque fonction, et chaque workflow de bout en bout.

---

## 8.1 CATALOGPAGE - DOCUMENTATION COMPLÈTE

### 8.1.1 Fiche d'identité

| Propriété | Valeur |
|-----------|--------|
| **Fichier** | `frontend/src/features/catalog/CatalogSmartDemo.jsx` |
| **Route** | `/operations/catalogue` |
| **Lignes de code** | 677 lignes |
| **Composants enfants** | SmartTable, SmartFilters, ProductCard, ProductDetailDrawer, AddProductModal, EditProductModal, StockAdjustmentModal, ConfirmDialog |
| **Hooks utilisés** | useProducts, useUpdateProduct, useDeleteProduct, useQueryClient, useState, useCallback, useMemo, useEffect |

---

### 8.1.2 TOUS LES BOUTONS DE L'INTERFACE

#### Header - Actions principales

| Bouton | Icône | Label | Condition d'affichage | Action au clic |
|--------|-------|-------|----------------------|----------------|
| `+ Ajouter un produit` | `Plus` (lucide) | "Ajouter un produit" | `!embedded` (toujours visible si pas mode embarqué) | `setAddProductOpen(true)` → Ouvre AddProductModal |

**Code source (lignes 504-508):**
```jsx
<Button variant="primary" onClick={() => setAddProductOpen(true)}>
  <Plus className="w-4 h-4" />
  Ajouter un produit
</Button>
```

---

#### SmartFilters - Barre de filtres

| Élément | Type | Icône | Options | Action |
|---------|------|-------|---------|--------|
| Recherche | Input text | - | placeholder: "Rechercher un produit..." | `onSearchChange={setSearchValue}` |
| Catégorie | Select | `Tag` | Dynamique: extrait des produits | `handleFilterChange('categorie', value)` |
| Statut stock | Select | `AlertTriangle` | 'critical', 'warning', 'ok' | `handleFilterChange('status', value)` |
| Marge | Select | `TrendingUp` | 'low', 'medium', 'high' | `handleFilterChange('marge', value)` |
| Reset | Button | - | "Réinitialiser" | `handleResetFilters()` |

**Suggestions de filtres rapides (lignes 457-461):**
```javascript
const suggestions = [
  { label: 'Ruptures de stock', filters: { status: 'critical' } },
  { label: 'Marges faibles', filters: { marge: 'low' } },
  { label: 'À surveiller', filters: { status: 'warning' } },
];
```

**Presets de filtres (lignes 464-467):**
```javascript
const presets = [
  { label: 'Produits critiques', description: 'Ruptures et marges faibles', filters: { status: 'critical', marge: 'low' } },
  { label: 'Top performers', description: 'Stock OK et bonnes marges', filters: { status: 'ok', marge: 'high' } },
];
```

---

#### SmartTable - Actions par ligne (Desktop)

| Action | Icône | Label | Condition | Handler |
|--------|-------|-------|-----------|---------|
| Voir | `Eye` | "Voir détails" | Toujours | `handleRowAction('view', row)` → Ouvre ProductDetailDrawer |
| Éditer | `Edit` | "Éditer" | Toujours | `handleRowAction('edit', row)` → Ouvre ProductDetailDrawer |
| Stock | `Package2` | "Ajuster stock" | Toujours | `handleRowAction('stock', row)` → Ouvre StockAdjustmentModal |
| Supprimer | `Trash2` | "Supprimer" | Toujours | `handleRowAction('delete', row)` → Ouvre ConfirmDialog |

**Handler handleRowAction (lignes 426-445):**
```javascript
const handleRowAction = useCallback((action, row) => {
  switch (action) {
    case 'view':
      setSelectedProduct(row);
      setDrawerOpen(true);
      break;
    case 'edit':
      setSelectedProduct(row);
      setDrawerOpen(true);
      break;
    case 'stock':
      handleQuickStock(row);
      break;
    case 'delete':
      handleDeleteProduct(row);
      break;
  }
}, [handleQuickStock, handleDeleteProduct]);
```

---

#### SmartTable - Édition inline (Desktop)

| Colonne | Éditable | Type input | Validation | Action |
|---------|----------|------------|------------|--------|
| `nom` | ❌ Non | - | - | - |
| `categorie` | ❌ Non | - | - | - |
| `prix_achat` | ✅ Oui | `number` | `> 0` | `handleUpdate(row, 'prix_achat', value)` |
| `prix_vente` | ✅ Oui | `number` | `> 0` | `handleUpdate(row, 'prix_vente', value)` |
| `stock_actuel` | ✅ Oui | `number` | `>= 0` | `handleUpdate(row, 'stock_actuel', value)` |
| `marge` | ❌ Non | - | - | Calculé: `((vente - achat) / achat * 100)` |

**Handler handleUpdate avec Optimistic Update (lignes 313-353):**
```javascript
const handleUpdate = useCallback(async (row, field, value) => {
  const parsedValue = Number.isFinite(parseFloat(value)) ? parseFloat(value) : value;

  // 1. Sauvegarder l'état précédent pour rollback
  const previousStates = queryClient.getQueriesData({ queryKey: ['products'] });

  // 2. Optimistic update : appliquer localement AVANT l'API
  previousStates.forEach(([queryKey, oldData]) => {
    if (!oldData) return;
    queryClient.setQueryData(queryKey, (current) => {
      if (Array.isArray(current)) {
        return current.map((product) =>
          product.id === row.id ? { ...product, [field]: parsedValue } : product
        );
      }
      if (Array.isArray(current.items)) {
        return {
          ...current,
          items: current.items.map((product) =>
            product.id === row.id ? { ...product, [field]: parsedValue } : product
          ),
        };
      }
      return current;
    });
  });

  // 3. Appel API
  try {
    await updateMutation.mutateAsync({
      productId: row.id,
      payload: { [field]: parsedValue },
    });
  } catch (err) {
    // 4. Rollback en cas d'erreur
    previousStates.forEach(([queryKey, oldData]) => {
      queryClient.setQueryData(queryKey, oldData);
    });
    toast.error('Mise à jour impossible');
    throw err;
  }
}, [queryClient, updateMutation]);
```

---

#### Mobile - SwipeableRow Actions

| Direction | Action | Icône | Couleur | Handler |
|-----------|--------|-------|---------|---------|
| Gauche → | Scanner | `Scan` | primary (bleu) | `handleScanBarcode(product)` |
| ← Droite | Détails | `Eye` | primary (bleu) | `handleViewDetails(product)` |
| ← Droite | Stock | `Package2` | success (vert) | `handleQuickStock(product)` |

**Code SwipeableRow (lignes 535-568):**
```jsx
<SwipeableRow
  key={product.id}
  id={`product-${product.id}`}
  leftActions={[
    { label: 'Scanner', icon: Scan, variant: 'primary', onAction: () => handleScanBarcode(product) },
  ]}
  rightActions={[
    { label: 'Détails', icon: Eye, variant: 'primary', onAction: () => handleViewDetails(product) },
    { label: 'Stock', icon: Package2, variant: 'success', onAction: () => handleQuickStock(product) },
  ]}
>
```

---

#### ProductDetailDrawer - Actions

| Bouton | Label | Condition | Handler |
|--------|-------|-----------|---------|
| Éditer | "Modifier" | Toujours | `handleEditFromDrawer(product)` → Ferme drawer, ouvre EditProductModal |
| Historique | "Historique" | Toujours | `handleViewHistory(product)` → Toast info (TODO) |
| Commander | "Commander" | Toujours | `handleOrderProduct(product)` → Toast info (TODO) |
| Fermer | ✕ | Toujours | `setDrawerOpen(false)` |

---

#### ConfirmDialog (Suppression)

| Bouton | Label | Variant | Condition | Handler |
|--------|-------|---------|-----------|---------|
| Annuler | "Annuler" | ghost | Toujours | `setDeleteConfirmOpen(false); setProductToDelete(null)` |
| Confirmer | "Supprimer" | destructive | `!deleteMutation.isPending` | `confirmDelete()` |

**Handler confirmDelete (lignes 448-454):**
```javascript
const confirmDelete = useCallback(() => {
  if (productToDelete) {
    deleteMutation.mutate(productToDelete.id);
    setDeleteConfirmOpen(false);
    setProductToDelete(null);
  }
}, [productToDelete, deleteMutation]);
```

---

### 8.1.3 TOUTES LES FONCTIONS DU COMPOSANT

#### États (useState)

| État | Type initial | Description |
|------|--------------|-------------|
| `addProductOpen` | `false` | Contrôle ouverture AddProductModal |
| `editProductOpen` | `false` | Contrôle ouverture EditProductModal |
| `stockAdjustOpen` | `false` | Contrôle ouverture StockAdjustmentModal |
| `deleteConfirmOpen` | `false` | Contrôle ouverture ConfirmDialog |
| `productToAdjust` | `null` | Produit sélectionné pour ajustement |
| `productToDelete` | `null` | Produit sélectionné pour suppression |
| `selectedProduct` | `null` | Produit sélectionné (drawer/edit) |
| `drawerOpen` | `false` | Contrôle ouverture ProductDetailDrawer |
| `filterValues` | `{}` | Valeurs des filtres actifs |
| `searchValue` | `''` | Valeur de la recherche |
| `isMobile` | `window.innerWidth < 768` | Mode mobile |

---

#### Handlers (useCallback)

| Fonction | Signature | Description | Lignes |
|----------|-----------|-------------|--------|
| `handleUpdate` | `(row, field, value) => Promise<void>` | Mise à jour inline avec optimistic update | 313-353 |
| `handleRowClick` | `(row) => void` | Ouvre le drawer de détail | 356-359 |
| `handleFilterChange` | `(key, value) => void` | Met à jour un filtre | 362-364 |
| `handleResetFilters` | `() => void` | Réinitialise tous les filtres | 367-370 |
| `handleRefresh` | `() => Promise<void>` | Invalide le cache products (pull-to-refresh) | 373-375 |
| `handleScanBarcode` | `(product) => void` | Affiche toast "Scanner non disponible" | 378-382 |
| `handleViewDetails` | `(product) => void` | Ouvre le drawer pour un produit | 385-388 |
| `handleQuickStock` | `(product) => void` | Ouvre StockAdjustmentModal | 391-394 |
| `handleOrderProduct` | `(product) => void` | Toast "Commander" (TODO) | 397-402 |
| `handleViewHistory` | `(product) => void` | Toast "Historique" (TODO) | 405-410 |
| `handleEditFromDrawer` | `(product) => void` | Ferme drawer, ouvre EditProductModal | 413-417 |
| `handleDeleteProduct` | `(product) => void` | Ouvre ConfirmDialog | 420-423 |
| `handleRowAction` | `(action, row) => void` | Dispatch actions ligne (view/edit/stock/delete) | 426-445 |
| `confirmDelete` | `() => void` | Exécute la suppression | 448-454 |

---

#### Mémoïsations (useMemo)

| Variable | Dépendances | Description |
|----------|-------------|-------------|
| `columns` | `[]` | Configuration colonnes SmartTable (6 colonnes) |
| `filters` | `[products]` | Configuration filtres (catégories dynamiques) |
| `filteredProducts` | `[products, searchValue, filterValues]` | Produits après filtrage local |
| `aiSuggestions` | `[filteredProducts]` | Suggestions IA (stock bas, prix manquant) |

---

### 8.1.4 WORKFLOW CASCADE COMPLET

#### Workflow: Édition inline d'un prix

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1: INTERACTION UTILISATEUR                                                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  [SmartTable] Colonne "prix_achat" (editable: true)                                                         │
│       ↓                                                                                                      │
│  Utilisateur double-clique sur la cellule                                                                   │
│       ↓                                                                                                      │
│  SmartTable passe en mode édition (input type="number")                                                     │
│       ↓                                                                                                      │
│  Utilisateur saisit "12.50" et appuie Entrée                                                                │
│       ↓                                                                                                      │
│  SmartTable appelle: onUpdate(row, 'prix_achat', '12.50')                                                   │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 2: HANDLER handleUpdate (CatalogSmartDemo.jsx:313-353)                                                 │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  const handleUpdate = async (row, field, value) => {                                                        │
│    const parsedValue = parseFloat(value);  // 12.50                                                         │
│                                                                                                              │
│    // 1. Snapshot état actuel                                                                               │
│    const previousStates = queryClient.getQueriesData({ queryKey: ['products'] });                          │
│                                                                                                              │
│    // 2. OPTIMISTIC UPDATE (UI immédiat sans attendre API)                                                  │
│    queryClient.setQueryData(['products'], (current) =>                                                      │
│      current.map(p => p.id === row.id ? {...p, prix_achat: 12.50} : p)                                     │
│    );                                                                                                        │
│    // → L'utilisateur voit immédiatement le changement                                                      │
│                                                                                                              │
│    // 3. Appel API                                                                                          │
│    try {                                                                                                     │
│      await updateMutation.mutateAsync({                                                                     │
│        productId: row.id,  // ex: 42                                                                        │
│        payload: { prix_achat: 12.50 }                                                                       │
│      });                                                                                                     │
│    } catch (err) {                                                                                          │
│      // 4. ROLLBACK si erreur                                                                               │
│      previousStates.forEach(([key, data]) => queryClient.setQueryData(key, data));                         │
│      toast.error('Mise à jour impossible');                                                                 │
│    }                                                                                                         │
│  };                                                                                                          │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 3: HOOK useUpdateProduct (hooks/useCatalogMutations.js:25-40)                                          │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  export function useUpdateProduct() {                                                                        │
│    const queryClient = useQueryClient();                                                                    │
│    return useMutation({                                                                                      │
│      mutationFn: ({ productId, payload }) =>                                                                │
│        updateProductRequest(productId, payload),  // API call                                               │
│      onSuccess: () => {                                                                                     │
│        toast.success('Produit mis à jour');                                                                 │
│        // Invalidation de tous les caches liés                                                              │
│        queryClient.invalidateQueries({ queryKey: ['products'] });                                          │
│        queryClient.invalidateQueries({ queryKey: ['inventory'] });                                         │
│        queryClient.invalidateQueries({ queryKey: ['stock'] });                                             │
│        queryClient.invalidateQueries({ queryKey: ['supply-plan'] });                                       │
│        queryClient.invalidateQueries({ queryKey: ['dashboard'] });                                         │
│        queryClient.invalidateQueries({ queryKey: ['margins'] });                                           │
│      },                                                                                                      │
│      onError: () => toast.error('Mise à jour impossible'),                                                  │
│    });                                                                                                       │
│  }                                                                                                           │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 4: API CLIENT (api/client.js)                                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  export async function updateProductRequest(productId, payload) {                                           │
│    const response = await fetch(`/api/catalog/products/${productId}`, {                                    │
│      method: 'PATCH',                                                                                        │
│      headers: {                                                                                              │
│        'Content-Type': 'application/json',                                                                  │
│        'Authorization': `Bearer ${token}`,                                                                  │
│      },                                                                                                      │
│      body: JSON.stringify(payload),  // { prix_achat: 12.50 }                                               │
│    });                                                                                                       │
│    return response.json();                                                                                   │
│  }                                                                                                           │
│                                                                                                              │
│  → Requête HTTP:                                                                                            │
│    PATCH /api/catalog/products/42                                                                           │
│    Content-Type: application/json                                                                            │
│    Authorization: Bearer eyJ...                                                                              │
│    Body: {"prix_achat": 12.50}                                                                              │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 5: ROUTER FastAPI (backend/api/catalog.py:83-96)                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  @router.patch("/products/{product_id}", response_model=ProductOut)                                         │
│  def update_product(                                                                                         │
│      product_id: int,                               # 42                                                    │
│      payload: ProductUpdate,                        # {"prix_achat": 12.50}                                 │
│      tenant: Tenant = Depends(get_current_tenant),  # extrait du JWT                                        │
│  ):                                                                                                          │
│      try:                                                                                                    │
│          return catalog_service.update_product(                                                             │
│              product_id,                                                                                     │
│              payload.model_dump(exclude_none=True, exclude={"codes"}),                                      │
│              codes=payload.codes,                                                                            │
│              tenant_id=tenant.id,  # 1 (épicerie)                                                           │
│          )                                                                                                   │
│      except catalog_service.ProductNotFound as exc:                                                         │
│          raise HTTPException(status_code=404, detail=str(exc))                                              │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 6: SERVICE catalog_service.update_product (backend/services/catalog.py:220-316)                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  def update_product(product_id, changes, codes=None, *, tenant_id):                                         │
│      set_clauses = ", ".join(f"{col} = :{col}" for col in changes.keys())                                  │
│      # → "prix_achat = :prix_achat"                                                                         │
│                                                                                                              │
│      with get_engine().begin() as conn:                                                                     │
│          # 1. Lire ancien prix pour event                                                                   │
│          old_row = conn.execute(text(                                                                       │
│              "SELECT prix_achat, nom, categorie FROM produits WHERE id = :pid AND tenant_id = :tid"        │
│          ), {"pid": 42, "tid": 1}).fetchone()                                                               │
│          old_price = float(old_row[0])  # 10.00                                                             │
│                                                                                                              │
│          # 2. UPDATE SQL                                                                                    │
│          conn.execute(text(                                                                                  │
│              "UPDATE produits SET prix_achat = :prix_achat, updated_at = now() "                            │
│              "WHERE id = :pid AND tenant_id = :tid"                                                         │
│          ), {"prix_achat": 12.50, "pid": 42, "tid": 1})                                                     │
│                                                                                                              │
│          # 3. Émettre événement de changement de prix                                                       │
│          if tenant_id == 1:  # Épicerie uniquement                                                          │
│              event = PriceChangedEvent(                                                                      │
│                  product_id=42,                                                                              │
│                  old_price=10.00,                                                                            │
│                  new_price=12.50,                                                                            │
│                  source="api",                                                                               │
│              )                                                                                               │
│              get_event_dispatcher().publish(event)                                                          │
│                                                                                                              │
│              # 4. Aussi émettre vers event sourcing finance                                                 │
│              emit_price_updated(tenant_id=1, product_id=42, old_price=10.00, new_price=12.50)               │
│                                                                                                              │
│          return get_product(42, tenant_id=1)  # Retourne produit mis à jour                                 │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 7: BASE DE DONNÉES                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  Tables modifiées:                                                                                           │
│                                                                                                              │
│  1. produits                                                                                                 │
│     UPDATE produits                                                                                          │
│     SET prix_achat = 12.50, updated_at = '2025-12-27 14:30:00'                                              │
│     WHERE id = 42 AND tenant_id = 1;                                                                        │
│                                                                                                              │
│  2. event_log (si event sourcing actif)                                                                     │
│     INSERT INTO event_log (type, payload, created_at)                                                       │
│     VALUES ('PriceChangedEvent', '{"product_id":42,"old":10,"new":12.5}', NOW());                           │
│                                                                                                              │
│  Tables potentiellement affectées par le cache invalidation:                                                │
│  - produits_price_history (via trigger ou job)                                                              │
│  - restaurant_plat_costs (recalcul food cost si ingrédient lié)                                             │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 8: RETOUR AU FRONTEND                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  1. API retourne: { id: 42, nom: "Tomates", prix_achat: 12.50, ... }                                        │
│  2. useMutation.onSuccess() exécute:                                                                        │
│     - toast.success('Produit mis à jour') → Notification verte                                              │
│     - invalidateQueries(['products']) → Déclenche refetch                                                   │
│  3. useProducts refetch automatique                                                                          │
│  4. UI se met à jour (déjà fait par optimistic update, confirmé par refetch)                                │
│                                                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

#### Workflow: Création d'un produit

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1: OUVERTURE MODAL                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  [Bouton "+ Ajouter un produit"] onClick={() => setAddProductOpen(true)}                                    │
│       ↓                                                                                                      │
│  <AddProductModal open={addProductOpen} onClose={...} onSuccess={...} />                                    │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 2: FORMULAIRE AddProductModal (modals/AddProductModal.jsx)                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  Sections du formulaire:                                                                                     │
│  ┌────────────────────────────────────────────────────────────────────────────────┐                         │
│  │ 📦 Informations principales                                                    │                         │
│  │    ├─ nom*          [input text]     "Tomates grappe bio"                     │                         │
│  │    ├─ categorie*    [select]         Options: CATEGORIES (10 valeurs fixes)   │                         │
│  │    └─ unite         [select]         Options: UNITS (7 valeurs: kg,L,unit...) │                         │
│  ├────────────────────────────────────────────────────────────────────────────────┤                         │
│  │ 💶 Tarification                                                                │                         │
│  │    ├─ prix_achat*   [input number]   "3.50" €                                 │                         │
│  │    └─ prix_vente*   [input number]   "5.90" €  + calcul marge automatique     │                         │
│  ├────────────────────────────────────────────────────────────────────────────────┤                         │
│  │ 🚚 Fournisseur & Conditionnement                                               │                         │
│  │    ├─ fournisseur   [select]         Options: SUPPLIERS (6 valeurs fixes)     │                         │
│  │    └─ conditionnement [input text]   "Carton de 12"                           │                         │
│  ├────────────────────────────────────────────────────────────────────────────────┤                         │
│  │ 📦 Stock                                                                       │                         │
│  │    ├─ stock_actuel  [input number]   "50"                                     │                         │
│  │    ├─ seuil_alerte  [input number]   "10" (défaut)                            │                         │
│  │    └─ stock_max     [input number]   "200"                                    │                         │
│  ├────────────────────────────────────────────────────────────────────────────────┤                         │
│  │ 🔢 Codes & Références                                                          │                         │
│  │    ├─ code_barre    [input + btn scan]  "3700123456789"                       │                         │
│  │    └─ code_interne  [input text]        "METRO-TOM-001"                       │                         │
│  ├────────────────────────────────────────────────────────────────────────────────┤                         │
│  │ 📝 Description (optionnel)                                                     │                         │
│  │    └─ description   [textarea]                                                 │                         │
│  └────────────────────────────────────────────────────────────────────────────────┘                         │
│                                                                                                              │
│  Boutons:                                                                                                    │
│  [Annuler] variant=ghost → handleClose()                                                                    │
│  [Créer le produit] variant=primary, disabled={isPending} → handleSubmit()                                  │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 3: VALIDATION (AddProductModal.jsx:71-106)                                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  const validate = useCallback(() => {                                                                        │
│    const newErrors = {};                                                                                     │
│                                                                                                              │
│    // Règle 1: Nom requis et min 2 caractères                                                               │
│    if (!form.nom.trim()) newErrors.nom = 'Le nom est requis';                                               │
│    else if (form.nom.trim().length < 2) newErrors.nom = 'Minimum 2 caractères';                             │
│                                                                                                              │
│    // Règle 2: Catégorie requise                                                                            │
│    if (!form.categorie) newErrors.categorie = 'La catégorie est requise';                                   │
│                                                                                                              │
│    // Règle 3: Prix d'achat > 0                                                                             │
│    if (!form.prix_achat || parseFloat(form.prix_achat) <= 0)                                                │
│      newErrors.prix_achat = 'Prix d\'achat invalide';                                                       │
│                                                                                                              │
│    // Règle 4: Prix de vente > 0                                                                            │
│    if (!form.prix_vente || parseFloat(form.prix_vente) <= 0)                                                │
│      newErrors.prix_vente = 'Prix de vente invalide';                                                       │
│                                                                                                              │
│    // Règle 5: Prix vente >= Prix achat                                                                     │
│    if (parseFloat(form.prix_vente) < parseFloat(form.prix_achat))                                           │
│      newErrors.prix_vente = 'Le prix de vente doit être supérieur au prix d\'achat';                        │
│                                                                                                              │
│    // Règle 6: Stock >= 0                                                                                   │
│    if (form.stock_actuel && parseFloat(form.stock_actuel) < 0)                                              │
│      newErrors.stock_actuel = 'Le stock ne peut pas être négatif';                                          │
│                                                                                                              │
│    // Règle 7: Seuil >= 0                                                                                   │
│    if (form.seuil_alerte && parseFloat(form.seuil_alerte) < 0)                                              │
│      newErrors.seuil_alerte = 'Le seuil ne peut pas être négatif';                                          │
│                                                                                                              │
│    setErrors(newErrors);                                                                                     │
│    return Object.keys(newErrors).length === 0;  // true si pas d'erreurs                                    │
│  }, [form]);                                                                                                 │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 4: SOUMISSION handleSubmit (AddProductModal.jsx:108-137)                                               │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  const handleSubmit = async (e) => {                                                                         │
│    e.preventDefault();                                                                                       │
│    if (!validate()) return;  // Arrête si validation échoue                                                 │
│                                                                                                              │
│    // Construction du payload                                                                                │
│    const payload = {                                                                                         │
│      nom: form.nom.trim(),                        // "Tomates grappe bio"                                   │
│      categorie: form.categorie,                   // "Fruits & Légumes"                                     │
│      prix_achat: parseFloat(form.prix_achat),     // 3.50                                                   │
│      prix_vente: parseFloat(form.prix_vente),     // 5.90                                                   │
│      stock_actuel: form.stock_actuel ? parseFloat(form.stock_actuel) : 0,  // 50                            │
│      seuil_alerte: form.seuil_alerte ? parseFloat(form.seuil_alerte) : 10, // 10                            │
│      stock_max: form.stock_max ? parseFloat(form.stock_max) : null,        // 200                           │
│      unite: form.unite,                           // "kg"                                                   │
│      code_barre: form.code_barre.trim() || null,  // "3700123456789"                                        │
│      code_interne: form.code_interne.trim() || null,                                                        │
│      conditionnement: form.conditionnement.trim() || null,                                                  │
│      fournisseur: form.fournisseur || null,                                                                 │
│      description: form.description.trim() || null,                                                          │
│    };                                                                                                        │
│                                                                                                              │
│    createProduct.mutate(payload, {                                                                          │
│      onSuccess: () => {                                                                                     │
│        setForm(initialFormState);  // Reset form                                                            │
│        setErrors({});                                                                                        │
│        onSuccess?.();              // Callback parent                                                       │
│        onClose();                  // Ferme modal                                                           │
│      },                                                                                                      │
│    });                                                                                                       │
│  };                                                                                                          │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 5: HOOK useCreateProduct (hooks/useCatalogMutations.js:9-23)                                           │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  export function useCreateProduct() {                                                                        │
│    const queryClient = useQueryClient();                                                                    │
│    return useMutation({                                                                                      │
│      mutationFn: createProduct,  // api/client.js                                                           │
│      onSuccess: () => {                                                                                     │
│        toast.success('Produit créé');                                                                       │
│        queryClient.invalidateQueries({ queryKey: ['products'] });                                          │
│        queryClient.invalidateQueries({ queryKey: ['inventory'] });                                         │
│        queryClient.invalidateQueries({ queryKey: ['stock'] });                                             │
│        queryClient.invalidateQueries({ queryKey: ['supply-plan'] });                                       │
│        queryClient.invalidateQueries({ queryKey: ['dashboard'] });                                         │
│      },                                                                                                      │
│      onError: () => toast.error('Création impossible'),                                                     │
│    });                                                                                                       │
│  }                                                                                                           │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 6: ROUTER (backend/api/catalog.py:73-80)                                                               │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  @router.post("/products", response_model=ProductOut, status_code=201)                                      │
│  def create_product(payload: ProductCreate, tenant: Tenant = Depends(get_current_tenant)):                  │
│      record = catalog_service.create_product(                                                               │
│          payload.model_dump(exclude={"codes"}),                                                             │
│          tenant_id=tenant.id,                                                                                │
│          codes=payload.codes,                                                                                │
│      )                                                                                                       │
│      return record                                                                                           │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 7: SERVICE (backend/services/catalog.py:192-218)                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  def create_product(payload, *, tenant_id, codes=None):                                                     │
│      codes = parse_barcode_input(codes or [])                                                               │
│      with get_engine().begin() as conn:                                                                     │
│          # INSERT INTO produits                                                                             │
│          row = conn.execute(text("""                                                                        │
│              INSERT INTO produits                                                                            │
│              (nom, tenant_id, prix_achat, prix_vente, tva, categorie, seuil_alerte, stock_actuel, actif)    │
│              VALUES (:nom, :tenant_id, :prix_achat, :prix_vente, :tva, :categorie, :seuil, :stock, :actif)  │
│              RETURNING id, nom, tenant_id, prix_achat, prix_vente, ...                                      │
│          """), {...payload, tenant_id}).fetchone()                                                          │
│                                                                                                              │
│          # INSERT codes-barres si fournis                                                                   │
│          for code in codes:                                                                                  │
│              insert_or_update_barcode(conn, record["id"], code, tenant_id=tenant_id)                        │
│                                                                                                              │
│          return record                                                                                       │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 8: BASE DE DONNÉES                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  INSERT INTO produits (                                                                                      │
│      nom, tenant_id, prix_achat, prix_vente, tva, categorie,                                                │
│      seuil_alerte, stock_actuel, actif                                                                      │
│  ) VALUES (                                                                                                  │
│      'Tomates grappe bio', 1, 3.50, 5.90, 20.0, 'Fruits & Légumes',                                         │
│      10, 50, true                                                                                            │
│  ) RETURNING id;  -- → 143                                                                                  │
│                                                                                                              │
│  INSERT INTO produits_barcodes (produit_id, tenant_id, code)                                                │
│  VALUES (143, 1, '3700123456789');                                                                          │
│                                                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

#### Workflow: Ajustement de stock

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1: OUVERTURE StockAdjustmentModal                                                                      │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  Action: Swipe → "Stock" OU Clic action "stock" dans SmartTable                                             │
│       ↓                                                                                                      │
│  handleQuickStock(product) → setProductToAdjust(product); setStockAdjustOpen(true)                          │
│       ↓                                                                                                      │
│  <StockAdjustmentModal open={stockAdjustOpen} product={productToAdjust} ... />                              │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 2: INTERFACE StockAdjustmentModal (modals/StockAdjustmentModal.jsx)                                    │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────────────┐                         │
│  │ 📦 [Nom produit]                              Stock actuel: 25 kg             │                         │
│  ├────────────────────────────────────────────────────────────────────────────────┤                         │
│  │ Type d'ajustement:                                                             │                         │
│  │   [= Définir]  [+ Ajouter]  [- Retirer]                                       │                         │
│  │       ↑ sélectionné                                                            │                         │
│  ├────────────────────────────────────────────────────────────────────────────────┤                         │
│  │ Quantité:                                                                      │                         │
│  │   [-] ──────────── [  30  ] ──────────── [+]                                  │                         │
│  ├────────────────────────────────────────────────────────────────────────────────┤                         │
│  │ Aperçu:                                                                        │                         │
│  │   Avant: 25  ────→  Après: 30  │  Diff: +5                                    │                         │
│  │   (vert si +, rouge si -)                                                     │                         │
│  ├────────────────────────────────────────────────────────────────────────────────┤                         │
│  │ Motif: [Select: Inventaire physique ▼]                                        │                         │
│  │   Options: inventory, loss, theft, expiry, transfer, correction, other        │                         │
│  ├────────────────────────────────────────────────────────────────────────────────┤                         │
│  │ Note: [Textarea optionnel]                                                     │                         │
│  ├────────────────────────────────────────────────────────────────────────────────┤                         │
│  │            [Annuler]  [Confirmer l'ajustement]                                │                         │
│  └────────────────────────────────────────────────────────────────────────────────┘                         │
│                                                                                                              │
│  Calcul du nouveau stock (useMemo):                                                                         │
│  - mode 'set':    newStock = quantity                                                                       │
│  - mode 'add':    newStock = currentStock + quantity                                                        │
│  - mode 'remove': newStock = max(0, currentStock - quantity)                                                │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 3: VALIDATION (StockAdjustmentModal.jsx:75-92)                                                         │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  const validate = useCallback(() => {                                                                        │
│    // Règle 1: Quantité valide                                                                              │
│    if (!quantity || parseFloat(quantity) < 0) {                                                             │
│      setError('Quantité invalide');                                                                         │
│      return false;                                                                                           │
│    }                                                                                                         │
│                                                                                                              │
│    // Règle 2: Mode 'remove' - quantité <= stock actuel                                                     │
│    if (mode === 'remove' && parseFloat(quantity) > currentStock) {                                          │
│      setError(`Quantité à retirer supérieure au stock actuel (${currentStock} ${unit})`);                   │
│      return false;                                                                                           │
│    }                                                                                                         │
│                                                                                                              │
│    // Règle 3: Mode 'set' - nouveau stock différent de l'actuel                                             │
│    if (mode === 'set' && parseFloat(quantity) === currentStock) {                                           │
│      setError('Le nouveau stock est identique au stock actuel');                                            │
│      return false;                                                                                           │
│    }                                                                                                         │
│                                                                                                              │
│    return true;                                                                                              │
│  }, [quantity, mode, currentStock, unit]);                                                                  │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 4: SOUMISSION (StockAdjustmentModal.jsx:94-125)                                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  const handleSubmit = async (e) => {                                                                         │
│    e.preventDefault();                                                                                       │
│    if (!validate()) return;                                                                                  │
│                                                                                                              │
│    stockAdjustment.mutate(                                                                                   │
│      {                                                                                                       │
│        productId: product.id,           // 42                                                               │
│        targetQuantity: newStock,        // 30 (calculé selon mode)                                          │
│        username: 'admin',               // TODO: Get from auth context                                      │
│      },                                                                                                      │
│      {                                                                                                       │
│        onSuccess: () => {                                                                                   │
│          toast.success(`Stock mis à jour: ${currentStock} → ${newStock} ${unit}`);                         │
│                                                                                                              │
│          // Invalidation des caches liés au stock                                                           │
│          queryClient.invalidateQueries({ queryKey: ['products'] });                                        │
│          queryClient.invalidateQueries({ queryKey: ['stock-timeseries'] });                                │
│          queryClient.invalidateQueries({ queryKey: ['stock-recent'] });                                    │
│                                                                                                              │
│          onSuccess?.();                                                                                     │
│          handleClose();                                                                                      │
│        },                                                                                                    │
│        onError: (err) => {                                                                                  │
│          toast.error('Erreur lors de l\'ajustement du stock');                                              │
│          setError(err.message || 'Une erreur est survenue');                                                │
│        },                                                                                                    │
│      }                                                                                                       │
│    );                                                                                                        │
│  };                                                                                                          │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 5: HOOK useStockAdjustment (hooks/useStock.js)                                                         │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  export function useStockAdjustment() {                                                                      │
│    return useMutation({                                                                                      │
│      mutationFn: ({ productId, targetQuantity, username }) =>                                               │
│        adjustStock(productId, targetQuantity, username),                                                    │
│    });                                                                                                       │
│  }                                                                                                           │
│                                                                                                              │
│  // api/client.js                                                                                            │
│  export async function adjustStock(productId, targetQuantity, username) {                                   │
│    return fetch(`/api/stock/adjustments`, {                                                                 │
│      method: 'POST',                                                                                         │
│      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },                  │
│      body: JSON.stringify({ product_id: productId, target_quantity: targetQuantity, username }),            │
│    }).then(r => r.json());                                                                                   │
│  }                                                                                                           │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 6: ROUTER (backend/api/stock.py)                                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  @router.post("/adjustments")                                                                                │
│  def create_adjustment(                                                                                      │
│      payload: StockAdjustmentPayload,                                                                       │
│      tenant: Tenant = Depends(get_current_tenant),                                                          │
│  ):                                                                                                          │
│      return stock_service.adjust_stock(                                                                     │
│          product_id=payload.product_id,                                                                     │
│          target_qty=payload.target_quantity,                                                                │
│          username=payload.username,                                                                          │
│          tenant_id=tenant.id,                                                                                │
│      )                                                                                                       │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 7: SERVICE stock_service.adjust_stock                                                                  │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  def adjust_stock(product_id, target_qty, username, tenant_id):                                             │
│      with get_engine().begin() as conn:                                                                     │
│          # 1. Lire stock actuel                                                                             │
│          current = conn.execute(text(                                                                       │
│              "SELECT stock_actuel FROM produits WHERE id = :pid AND tenant_id = :tid"                       │
│          ), {"pid": product_id, "tid": tenant_id}).scalar()                                                 │
│                                                                                                              │
│          # 2. Calculer différence                                                                           │
│          diff = target_qty - current  # ex: 30 - 25 = +5                                                    │
│          type_mvt = 'ENTREE' if diff > 0 else 'SORTIE'                                                      │
│                                                                                                              │
│          # 3. Créer mouvement stock                                                                         │
│          conn.execute(text("""                                                                              │
│              INSERT INTO mouvements_stock (produit_id, tenant_id, quantite, type, source, created_by)       │
│              VALUES (:pid, :tid, :qty, :type, 'AJUSTEMENT', :user)                                          │
│          """), {"pid": product_id, "tid": tenant_id, "qty": abs(diff), "type": type_mvt, "user": username})│
│                                                                                                              │
│          # 4. Mettre à jour stock_actuel                                                                    │
│          conn.execute(text(                                                                                  │
│              "UPDATE produits SET stock_actuel = :target WHERE id = :pid AND tenant_id = :tid"              │
│          ), {"target": target_qty, "pid": product_id, "tid": tenant_id})                                    │
│                                                                                                              │
│          return {"success": True, "old_stock": current, "new_stock": target_qty}                            │
│                                                                                                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ÉTAPE 8: BASE DE DONNÉES                                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                              │
│  -- 1. Insertion mouvement                                                                                  │
│  INSERT INTO mouvements_stock (produit_id, tenant_id, quantite, type, source, date_mvt, created_by)         │
│  VALUES (42, 1, 5, 'ENTREE', 'AJUSTEMENT', NOW(), 'admin');                                                 │
│                                                                                                              │
│  -- 2. Update produit                                                                                       │
│  UPDATE produits SET stock_actuel = 30, updated_at = NOW()                                                  │
│  WHERE id = 42 AND tenant_id = 1;                                                                           │
│                                                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 8.1.5 ÉTATS D'ERREUR ET FEEDBACK

#### États de chargement

| État | Composant affiché | Condition |
|------|-------------------|-----------|
| Chargement initial | `<TableSkeleton rows={8} columns={5} />` | `isLoading && products.length === 0` |
| Erreur API | `<QueryErrorState error={error} onRetry={refetch} variant="full" />` | `isError && products.length === 0` |
| Liste vide | `"Aucun produit trouvé"` (emptyMessage SmartTable) | `filteredProducts.length === 0` |
| Chargement mobile | `"Chargement..."` div centré | `isLoading` en mode mobile |

#### Toasts de feedback

| Action | Type | Message |
|--------|------|---------|
| Création produit réussie | success | "Produit créé" |
| Création produit échouée | error | "Création impossible" |
| Mise à jour réussie | success | "Produit mis à jour" |
| Mise à jour échouée | error | "Mise à jour impossible" |
| Suppression réussie | success | "Produit supprimé" |
| Suppression échouée | error | "Suppression impossible" |
| Ajustement stock réussi | success | "Stock mis à jour: {old} → {new} {unit}" |
| Ajustement stock échoué | error | "Erreur lors de l'ajustement du stock" |
| Scan non disponible | info | "Scanner pour {nom}" |
| Commander non dispo | info | "Commander {nom}" |
| Historique non dispo | info | "Historique de {nom}" |

---

### 8.1.6 FILTRAGE LOCAL

Le filtrage est effectué côté client (useMemo) pour une réactivité instantanée.

```javascript
const filteredProducts = useMemo(() => {
  let result = products;

  // 1. Recherche textuelle (nom ou catégorie)
  if (searchValue) {
    const search = searchValue.toLowerCase();
    result = result.filter((p) =>
      p.nom?.toLowerCase().includes(search) ||
      p.categorie?.toLowerCase().includes(search)
    );
  }

  // 2. Filtre par catégorie exacte
  if (filterValues.categorie) {
    result = result.filter((p) => p.categorie === filterValues.categorie);
  }

  // 3. Filtre par statut stock
  if (filterValues.status) {
    result = result.filter((p) => {
      const stock = p.stock_actuel || 0;
      const threshold = p.seuil_alerte || 8;
      const status = stock === 0 ? 'critical' : stock < threshold ? 'warning' : 'ok';
      return status === filterValues.status;
    });
  }

  // 4. Filtre par marge
  if (filterValues.marge) {
    result = result.filter((p) => {
      const achat = p.prix_achat || 0;
      const vente = p.prix_vente || 0;
      if (achat === 0) return false;
      const marge = ((vente - achat) / achat * 100);
      switch (filterValues.marge) {
        case 'low': return marge < 15;
        case 'medium': return marge >= 15 && marge <= 30;
        case 'high': return marge > 30;
      }
    });
  }

  return result;
}, [products, searchValue, filterValues]);
```

---

### 8.1.7 SUGGESTIONS IA (Inline)

Les suggestions sont calculées automatiquement et affichées en bas de page.

```javascript
const aiSuggestions = useMemo(() => {
  // 1. Produits bientôt en rupture (stock < seuil)
  const lowStock = filteredProducts
    .filter((p) => (p.stock_actuel || 0) < (p.seuil_alerte || 8))
    .slice(0, 2)
    .map((p) => ({
      type: 'stock',
      title: `${p.nom} bientôt en rupture`,
      action: 'Commander',
    }));

  // 2. Produits sans prix d'achat
  const priceUnknown = filteredProducts
    .filter((p) => !p.prix_achat)
    .slice(0, 1)
    .map((p) => ({
      type: 'price',
      title: `${p.nom}: prix achat manquant`,
      action: 'Compléter',
    }));

  return [...lowStock, ...priceUnknown];
}, [filteredProducts]);
```

---

## 8.2 STOCKMOVEMENTSPAGE - DOCUMENTATION COMPLÈTE

### 8.2.1 Fiche d'identité

| Propriété | Valeur |
|-----------|--------|
| **Fichier** | `frontend/src/features/stock/StockMovementsPage.jsx` |
| **Route** | `/operations/stock` |
| **Lignes de code** | 486 lignes |
| **Composants enfants** | Card, Button, StockScannerPanel, Recharts (BarChart, LineChart) |
| **Hooks utilisés** | useProducts, useStockTimeseries, useRecentMovements, useStockAdjustment, useState, useMemo, useEffect, useSearchParams |

---

### 8.2.2 ARCHITECTURE MULTI-PANELS

La page utilise un système de sections/panels configurable:

```javascript
const SECTION_DEFINITIONS = [
  {
    id: 'overview',
    label: 'Pilotage',
    groups: [{
      title: 'Flux',
      items: [{ id: 'overview.core', label: 'Vue globale', description: '...' }],
    }],
  },
  {
    id: 'analytics',
    label: 'Analyses',
    groups: [{
      title: 'Classements & historique',
      items: [{ id: 'analytics.history', label: 'Top & journal', description: '...' }],
    }],
  },
  {
    id: 'operations',
    label: 'Opérations',
    groups: [{
      title: 'Inventaire',
      items: [{ id: 'operations.adjust', label: 'Ajustements', description: '...' }],
    }],
  },
];
```

---

### 8.2.3 TOUS LES BOUTONS ET CONTRÔLES

#### Panel: overview.core (Pilotage)

| Élément | Type | Options | Action |
|---------|------|---------|--------|
| Sélecteur produit | Select | `productOptions` (tous produits + "Catalogue complet") | `setSelectedProduct(value)` |
| Fenêtre temporelle | Select | 7, 30, 90, 180 jours | `setWindowDays(Number(value))` |
| Limite lignes | Select | 25, 50, 100, 200 | `setRecentLimit(Number(value))` |

**Graphiques affichés:**
- **BarChart**: Entrées/sorties par jour (barres bleues/roses)
- **LineChart**: Cumul variation nette (ligne verte)

---

#### Panel: analytics.history (Analyses)

| Section | Contenu |
|---------|---------|
| Top Entrées récentes | Liste 5 produits avec plus d'entrées (somme) |
| Top Sorties récentes | Liste 5 produits avec plus de sorties (somme) |
| Tableau Mouvements récents | `recentLimit` lignes avec Date, Produit, Type, Quantité, Source |

---

#### Panel: operations.adjust (Opérations)

| Élément | Type | Description | Handler |
|---------|------|-------------|---------|
| StockScannerPanel | Component | Scanner code-barres | `onProductFound` → `setAdjustProductId()` |
| Sélecteur produit | Select | Choix manuel produit | `setAdjustProductId(value)` |
| Stock cible | Input number | Quantité finale souhaitée | `setTargetQuantity(value)` |
| Stock actuel | Input readonly | Affiche stock actuel | - |
| Bouton "Enregistrer" | Button variant=brand | Soumet l'ajustement | `handleAdjustment()` |

---

### 8.2.4 HOOKS ET ÉTATS

| État | Type | Description |
|------|------|-------------|
| `selectedProduct` | `'all' \| string` | Produit filtré ou tous |
| `windowDays` | `number` | Fenêtre temporelle (7/30/90/180) |
| `recentLimit` | `number` | Limite mouvements récents |
| `targetQuantity` | `string` | Quantité cible pour ajustement |
| `adjustProductId` | `number \| null` | ID produit pour ajustement |
| `activePanel` | `string` | Panel actif (`'overview.core'`, etc.) |

**Hooks TanStack Query:**
```javascript
const timeseriesQuery = useStockTimeseries({ windowDays, productId });
const recentQuery = useRecentMovements({ limit: recentLimit, productId });
const adjustment = useStockAdjustment();
```

---

### 8.2.5 WORKFLOW: AJUSTEMENT DE STOCK VIA SCANNER

```
┌───────────────────────────────────────────────────────────────────────────┐
│ 1. Utilisateur scanne un code-barres                                      │
│    └─> StockScannerPanel.onProductFound(product)                         │
│        └─> setAdjustProductId(product.id)                                │
│        └─> setTargetQuantity('')                                         │
├───────────────────────────────────────────────────────────────────────────┤
│ 2. Utilisateur saisit la quantité cible et clique "Enregistrer"          │
│    └─> handleAdjustment()                                                │
│        └─> adjustment.mutate({ productId, targetQuantity, username })    │
├───────────────────────────────────────────────────────────────────────────┤
│ 3. Hook useStockAdjustment                                                │
│    └─> POST /api/stock/adjustments                                       │
│    └─> onSuccess: invalidateQueries(['stock', 'products', ...])          │
│    └─> toast.success('Stock ajusté')                                     │
├───────────────────────────────────────────────────────────────────────────┤
│ 4. Backend calcule la différence et crée le mouvement                    │
│    └─> diff = target_quantity - current_stock                            │
│    └─> INSERT INTO mouvements_stock (type=ENTREE ou SORTIE)              │
│    └─> UPDATE produits SET stock_actuel = target_quantity                │
└───────────────────────────────────────────────────────────────────────────┘
```

---

### 8.2.6 MÉTRIQUES CALCULÉES

```javascript
const metrics = useMemo(() => {
  const dataset = timeseriesQuery.data ?? [];
  const entries = dataset
    .filter((item) => item.type === 'ENTREE')
    .reduce((sum, item) => sum + item.quantite, 0);
  const outputs = dataset
    .filter((item) => item.type === 'SORTIE')
    .reduce((sum, item) => sum + item.quantite, 0);
  return {
    entries,   // Total entrées sur la période
    outputs,   // Total sorties sur la période
    net: entries - outputs,  // Variation nette
  };
}, [timeseriesQuery.data]);
```

---

## 8.3 PRICESPAGE - DOCUMENTATION COMPLÈTE

### 8.3.1 Fiche d'identité

| Propriété | Valeur |
|-----------|--------|
| **Fichier** | `frontend/src/features/prices/PricesPage.jsx` |
| **Route** | `/operations/prix` |
| **Lignes de code** | 665 lignes |
| **Composants enfants** | Card, Button, Recharts (LineChart, AreaChart, BarChart) |
| **Hooks utilisés** | useProducts, usePriceHistory, useState, useMemo, useCallback |

---

### 8.3.2 FILTRES DISPONIBLES

| Filtre | Type | Default | Description |
|--------|------|---------|-------------|
| `productId` | Select | `'all'` | Filtre par produit |
| `supplier` | Input text | `''` | Filtre par fournisseur |
| `code` | Input text | `''` | Filtre par code EAN |
| `search` | Input text | `''` | Recherche libre |
| `dateStart` | Input date | `''` | Date début période |
| `dateEnd` | Input date | `''` | Date fin période |
| `limit` | Number | `200` | Limite résultats |

---

### 8.3.3 BOUTONS ET ACTIONS

| Bouton | Label | Condition | Handler |
|--------|-------|-----------|---------|
| Export CSV | "Export CSV" | `!items.length` (disabled) | `downloadCsv(items)` |

**Fonction downloadCsv:**
```javascript
const downloadCsv = (rows) => {
  const headers = ['Date', 'Produit', 'Code', 'Fournisseur', ...];
  const body = [headers, ...rows.map(row => [...])];
  const blob = new Blob([body], { type: 'text/csv' });
  // Téléchargement automatique
};
```

---

### 8.3.4 MÉTRIQUES AFFICHÉES

| Métrique | Calcul | Description |
|----------|--------|-------------|
| Dernier prix | `prices[prices.length - 1]` | Dernier prix observé |
| Variation | `last - first` | Delta entre premier et dernier |
| Variation % | `(delta / first) * 100` | Pourcentage de variation |
| Prix moyen | `sum(prices) / count` | Moyenne sur la période |
| Fourchette | `min → max` | Plage observée |

---

### 8.3.5 VISUALISATIONS

| Chart | Type | Données |
|-------|------|---------|
| Timeline | LineChart + AreaChart | `timelineData` (moyenne quotidienne + glissante 5j) |
| Top Fournisseurs | BarChart horizontal | `supplierBreakdown` (top 8 par montant) |
| Top hausses | Liste | `topIncreases` (5 plus fortes hausses) |
| Top baisses | Liste | `topDrops` (5 plus fortes baisses) |

---

### 8.3.6 ALERTES PRIX/STOCK

Section dédiée aux alertes:

```javascript
const alertItems = useMemo(() =>
  items.filter((entry) =>
    entry.margin_alert ||      // Marge trop faible
    entry.stock_alert ||       // Stock critique
    entry.stockout_repeated    // Ruptures répétées
  ),
[items]);
```

| Type alerte | Badge | Couleur |
|-------------|-------|---------|
| margin_alert | Marge faible | rose |
| stock_alert | Stock critique | amber |
| stockout_repeated | Ruptures (N) | rose |

---

## 8.4 IMPORTPAGE - DOCUMENTATION RÉSUMÉE

### 8.4.1 Fiche d'identité

| Propriété | Valeur |
|-----------|--------|
| **Fichier** | `frontend/src/features/import/ImportPage.jsx` |
| **Route** | `/operations/factures` |
| **Hook principal** | `useInvoiceZeroClick` |

---

### 8.4.2 Fonctionnalité Zero-Click

L'import Zero-Click permet de:
1. Uploader une facture PDF/image
2. L'IA extrait automatiquement les lignes (produit, quantité, prix)
3. Les données sont matchées avec les produits existants
4. Le stock et l'historique prix sont mis à jour automatiquement

**Workflow:**
```
Upload PDF → OCR/AI extraction → Match produits → Update DB → Toast success
```

---

## 8.5 SUPPLYPAGE - DOCUMENTATION RÉSUMÉE

### 8.5.1 Fiche d'identité

| Propriété | Valeur |
|-----------|--------|
| **Fichier** | `frontend/src/features/supply/SupplyPage.jsx` |
| **Route** | Non routé actuellement (TODO) |
| **Hook principal** | `useSupplyPlan` |

---

### 8.5.2 Fonctionnalités

- Affichage du plan d'approvisionnement
- Calcul des quantités à commander basé sur:
  - Stock actuel
  - Ventes moyennes
  - Jours de couverture souhaités
- Génération de commandes fournisseur

---

# PARTIE 9: INCOHÉRENCES DÉTECTÉES

Cette section liste les incohérences, TODO et problèmes identifiés lors de l'analyse du code.

---

## 9.1 DONNÉES HARDCODÉES (Frontend)

### AddProductModal.jsx

| Constante | Valeur | Problème |
|-----------|--------|----------|
| `CATEGORIES` | Array de 10 catégories fixes | Devrait être fetchée depuis `/api/catalog/categories` |
| `SUPPLIERS` | Array de 6 fournisseurs fixes | Devrait être fetché depuis `/api/catalog/vendors` |
| `UNITS` | Array de 7 unités fixes | Pourrait être configurable par tenant |

**Impact:** Les catégories et fournisseurs dans le modal ne correspondent pas aux données réelles.

**Correction suggérée:**
```javascript
// Remplacer les constantes par des hooks
const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: fetchCategories });
const { data: vendors } = useQuery({ queryKey: ['vendors'], queryFn: fetchVendors });
```

---

## 9.2 USERNAME HARDCODÉ

### StockAdjustmentModal.jsx:103

```javascript
username: 'admin', // TODO: Get from auth context
```

**Impact:** Tous les ajustements sont attribués à "admin" au lieu de l'utilisateur connecté.

**Correction suggérée:**
```javascript
import { useAuth } from '@/contexts/AuthContext';
const { user } = useAuth();
// ...
username: user?.username || 'system',
```

---

### StockMovementsPage.jsx:201

```javascript
adjustment.mutate({ productId: pid, targetQuantity: qty, username: 'api' });
```

**Impact:** Même problème, tous les ajustements marqués "api".

---

## 9.3 TABLE MANQUANTE DANS LA DOCUMENTATION

### product_suppliers

Le service `backend/services/catalog.py` référence une table `product_suppliers`:

```python
JOIN product_suppliers ps ON ps.product_id = p.id AND ps.tenant_id = p.tenant_id
```

**Cette table n'est pas documentée dans les schémas de base de données.**

---

## 9.4 INCOHÉRENCES UI - THÈME

| Page | Thème | Classes |
|------|-------|---------|
| CatalogSmartDemo.jsx | Dark | `bg-[#0a0a0f]` |
| StockMovementsPage.jsx | Light | `text-slate-900`, `bg-slate-50` |
| PricesPage.jsx | Dark | `bg-white/5`, `text-white` |

**Correction suggérée:** Uniformiser vers le thème dark.

---

## 9.5 FONCTIONS NON IMPLÉMENTÉES (TODO)

### CatalogSmartDemo.jsx

| Fonction | Lignes | État actuel |
|----------|--------|-------------|
| `handleScanBarcode` | 378-382 | Toast info "Scanner non disponible" |
| `handleOrderProduct` | 397-402 | Toast info seulement |
| `handleViewHistory` | 405-410 | Toast info seulement |

---

## 9.6 CACHE INVALIDATION INCOMPLÈTE

```javascript
// useCreateProduct - invalidate:
['products', 'inventory', 'stock', 'supply-plan', 'dashboard']

// useUpdateProduct - invalidate:
['products', 'inventory', 'stock', 'supply-plan', 'dashboard', 'margins']

// Différence: 'margins' manquant dans useCreateProduct
```

---

## 9.7 ÉVÉNEMENTS LIMITÉS AU TENANT 1

### backend/services/catalog.py:260

```python
if "prix_achat" in changes and tenant_id == 1:  # Épicerie uniquement
```

**Impact:** Les événements de changement de prix ne sont émis que pour le tenant "épicerie".

---

## 9.8 ROUTE SUPPLYPAGE MANQUANTE

Le fichier `SupplyPage.jsx` existe mais n'est pas routé.

**Correction dans routes.jsx:**
```javascript
{ path: '/operations/approvisionnement', element: <SupplyPage /> }
```

---

## 9.9 RÉCAPITULATIF DES CORRECTIONS PRIORITAIRES

| Priorité | Incohérence | Effort |
|----------|-------------|--------|
| 🔴 Haute | Username hardcodé (audit trail incorrect) | 15 min |
| 🔴 Haute | Route SupplyPage manquante | 5 min |
| 🟡 Moyenne | CATEGORIES/SUPPLIERS dynamiques | 30 min |
| 🟡 Moyenne | Thème uniforme dark | 1-2h |
| 🟡 Moyenne | Cache invalidation complète | 15 min |
| 🟢 Basse | Scanner barcode fonctionnel | 2-4h |
| 🟢 Basse | Events multi-tenant | 30 min |

---

# PARTIE 10: MODULE FINANCE - DOCUMENTATION EXHAUSTIVE

---

## 10.1 VUE D'ENSEMBLE DU MODULE

Le module Finance gère la trésorerie, les transactions bancaires, le rapprochement bancaire et la catégorisation automatique des dépenses.

### 10.1.1 ARCHITECTURE DES PAGES

```
/finance
├── /overview          → FinanceOverview.jsx (Dashboard trésorerie)
├── /transactions      → FinanceTransactionsPage.jsx (Transactions)
├── /reconciliation    → BankReconciliationPage.jsx (Rapprochement)
├── /accounts          → FinanceAccountsPage.jsx (Comptes)
├── /imports           → FinanceImportsPage.jsx (Imports)
├── /anomalies         → FinanceAnomaliesPage.jsx (Anomalies)
└── /rules             → FinanceRulesPage.jsx (Règles catégorisation)
```

### 10.1.2 HOOKS DU MODULE FINANCE

```
frontend/src/hooks/
├── useFinance.js              # Transactions, mutations, anomalies
├── useFinanceCategories.js    # Catégories, timeline, trésorerie
├── useFinanceImports.js       # Import relevés bancaires
└── useBankReconciliation.js   # Rapprochement bancaire
```

---

## 10.2 FINANCEOVERVIEW.JSX - DASHBOARD TRÉSORERIE

**Fichier:** `frontend/src/features/finance/FinanceOverview.jsx`
**Lignes:** 471
**Route:** `/finance/overview`

### 10.2.1 ÉTAT LOCAL

```javascript
const [period, setPeriod] = useState('30d');  // Période sélectionnée
```

### 10.2.2 HOOKS UTILISÉS

| Hook | Import | Purpose |
|------|--------|---------|
| `useFinanceTimeline` | `useFinanceCategories.js` | Timeline entrées/sorties |
| `useFinanceTreasury` | `useFinanceCategories.js` | Solde et tendances |
| `useFinanceTransactions` | `useFinance.js` | 5 dernières transactions |
| `useFinanceAnomalies` | `useFinance.js` | Nombre d'anomalies |
| `useFinanceMatches` | `useFinance.js` | Rapprochements en attente |

### 10.2.3 CONSTANTES

```javascript
const PERIODS = [
  { key: '7d', label: '7 jours', days: 7 },
  { key: '30d', label: '30 jours', days: 30 },
  { key: '90d', label: '90 jours', days: 90 },
  { key: '12m', label: '12 mois', days: 365 },
  { key: 'all', label: 'Tout', days: null },
];
```

### 10.2.4 COMPOSANTS INTERNES

#### `PeriodTabs({ value, onChange })`
- **Lignes:** 72-91
- **Rôle:** Onglets de sélection de période
- **UI:** Boutons avec style actif `bg-amber-500/20 text-amber-400`

#### `ChartTooltip({ active, payload, label })`
- **Lignes:** 94-127
- **Rôle:** Tooltip personnalisé pour le graphique
- **Affiche:** Solde, entrées, sorties pour le point survolé

#### `TransactionRow({ tx, onClick })`
- **Lignes:** 130-167
- **Rôle:** Ligne de tableau pour une transaction
- **Style:** Couleur verte (IN) ou rose (OUT) selon direction

### 10.2.5 ÉLÉMENTS UI

#### HERO BALANCE
```
┌─────────────────────────────────────────────────────────┐
│                    TRÉSORERIE                           │
│               € 125,450.00                              │
│           ↑ +12.5% vs période précédente                │
└─────────────────────────────────────────────────────────┘
```

#### STATS ROW (4 cards)
| Card | Valeur | Couleur |
|------|--------|---------|
| Entrées | +{totalInflow} | emerald |
| Sorties | -{totalOutflow} | rose |
| Solde net | {netChange} | amber/rose |
| Alertes | {anomalies}/{pending} | variable |

### 10.2.6 BOUTONS ET ACTIONS

| Bouton | Ligne | Handler | Action |
|--------|-------|---------|--------|
| Rafraîchir | 278-284 | `handleRefresh()` | Refetch toutes les queries |
| Période personnalisée | 285-288 | - | TODO: Modal calendrier |
| Exporter CSV | 372-375 | - | TODO: Export données chart |
| Voir tout | 422-425 | - | Navigue vers transactions |

### 10.2.7 GRAPHIQUE RECHARTS

```javascript
<BarChart data={chartData}>
  <XAxis dataKey="period" />
  <YAxis tickFormatter={formatCompact} />
  <Tooltip content={<ChartTooltip />} />
  <Bar dataKey="balance" radius={[4, 4, 0, 0]}>
    {chartData.map((entry, index) => (
      <Cell fill={`rgba(245, 158, 11, ${0.4 + (index / chartData.length) * 0.6})`} />
    ))}
  </Bar>
</BarChart>
```

---

## 10.3 FINANCETRANSACTIONSPAGE.JSX - LISTE TRANSACTIONS

**Fichier:** `frontend/src/features/finance/FinanceTransactionsPage.jsx`
**Lignes:** 797
**Route:** `/finance/transactions`

### 10.3.1 ÉTAT LOCAL

```javascript
const [selectedRows, setSelectedRows] = useState([]);
const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
const [categoryModalOpen, setCategoryModalOpen] = useState(false);
const [detailModalOpen, setDetailModalOpen] = useState(false);
const [selectedTransaction, setSelectedTransaction] = useState(null);
```

### 10.3.2 FILTRES PERSISTANTS

```javascript
const defaultFilters = {
  entity_id: undefined,
  account_id: undefined,
  category_id: undefined,
  date_from: undefined,
  date_to: undefined,
  amount_min: undefined,
  amount_max: undefined,
  q: undefined,
};
```

### 10.3.3 HOOKS UTILISÉS

| Hook | Purpose |
|------|---------|
| `useFinanceTransactions(apiFilters)` | Query infinie paginée |
| `useUpdateFinanceTransaction()` | Mutation mise à jour |
| `useLockFinanceTransaction()` | Mutation verrouillage |
| `useFinanceCategories({})` | Liste catégories |
| `useFinanceAccounts({})` | Liste comptes |
| `useFinanceTreasury({ period: '30d' })` | Stats trésorerie |
| `usePersistedFilters('finance_transactions', defaultFilters)` | Filtres persistés localStorage |

### 10.3.4 COLONNES SMARTTABLE

```javascript
const columns = [
  columnHelpers.date('date_operation', 'Date'),
  { key: 'label', header: 'Libellé', editable: true },
  { key: 'amount', header: 'Montant', type: 'currency' },
  { key: 'category_id', header: 'Catégorie' }, // avec CategoryInlineEdit
  { key: 'account_id', header: 'Compte' },
  columnHelpers.status('status', 'Statut'),
  columnHelpers.actions((row) => <LockButton />),
];
```

### 10.3.5 CATÉGORISATION INLINE

**Composant:** `CategoryInlineEdit`

```javascript
<CategoryInlineEdit
  transactionId={row.id}
  currentCategoryId={value}
  currentCategoryName={category?.name}
  aiConfidence={row.ai_confidence}
  predictedCategoryId={row.predicted_category_id}
  onUpdate={handleCategoryUpdate}
/>
```

**Avec badge IA:**
```javascript
{hasAIConfidence && (
  <AIConfidenceBadge
    confidence={row.ai_confidence}
    size="sm"
    variant="compact"
    showTooltip={true}
    explanation={row.ai_suggestion_reason}
  />
)}
```

### 10.3.6 STATS ROW (4 KPIs)

| KPI | Calcul | Couleur |
|-----|--------|---------|
| Entrées ce mois | `sum(tx.amount where direction='IN')` | emerald |
| Sorties ce mois | `sum(tx.amount where direction='OUT')` | rose |
| Solde net | entrées - sorties | amber/rose |
| Non rapprochées | `count(tx where status!='matched')` | slate |

### 10.3.7 ACTIONS EN MASSE

```javascript
const bulkActions = [
  {
    id: 'recategorize',
    label: 'Recatégoriser',
    onClick: (selectedData) => {
      // TODO: Ouvrir modal de recatégorisation
    },
  },
];
```

### 10.3.8 VUE MOBILE (SwipeableRow)

```javascript
<SwipeableRow
  id={transaction.id}
  leftActions={[
    { label: 'Catégoriser', icon: Tag, variant: 'primary', onAction: handleOpenCategoryModal },
    { label: 'Verrouiller', icon: Lock, variant: 'secondary', onAction: handleLockTransaction },
  ]}
  rightActions={[
    { label: 'Détails', icon: Info, variant: 'primary', onAction: handleOpenDetailModal },
  ]}
>
  <MobileTransactionCard transaction={transaction} />
</SwipeableRow>
```

### 10.3.9 EXPORT CSV

```javascript
const handleExport = useCallback(() => {
  const headers = ['Date', 'Libellé', 'Montant', 'Catégorie', 'Compte', 'Statut'];
  const rows = transactions.map((tx) => [
    tx.date_operation,
    `"${(tx.label || '').replace(/"/g, '""')}"`,
    tx.amount,
    category?.name,
    account?.label,
    tx.status,
  ].join(';'));

  const csvContent = [headers.join(';'), ...rows].join('\n');
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
  // ... download logic
}, [transactions]);
```

---

## 10.4 BANKRECONCILIATIONPAGE.JSX - RAPPROCHEMENT BANCAIRE

**Fichier:** `frontend/src/features/finance/BankReconciliationPage.jsx`
**Lignes:** 563
**Route:** `/finance/reconciliation`

### 10.4.1 ÉTAT LOCAL

```javascript
const [activeTab, setActiveTab] = useState('transactions');
const [viewMode, setViewMode] = useState('split'); // 'split' or 'list'
const [selectedTransaction, setSelectedTransaction] = useState(null);
const [selectedInvoice, setSelectedInvoice] = useState(null);
const [matchModalOpen, setMatchModalOpen] = useState(false);
const [filters, setFilters] = useState({ daysBack: 365, minAmount: 0 });
```

### 10.4.2 HOOK COMBINÉ useBankReconciliation

```javascript
const {
  summary,        // Query: stats rapprochement
  transactions,   // Query: transactions non rapprochées
  invoices,       // Query: factures non rapprochées
  isLoading,
  runReconciliation, // Mutation: lancer auto-matching
  createMatch,       // Mutation: rapprochement manuel
  refetchAll,
} = useBankReconciliation(filters);
```

### 10.4.3 KPIs

```javascript
<Stat label="À rapprocher" value={unmatchedTransactions.length} accent="amber" />
<Stat label="Factures" value={unmatchedInvoices.length} accent="rose" />
<Stat label="Rapprochées" value={summary.matched_count} accent="emerald" />
<Stat label="Taux" value={`${summary.match_rate * 100}%`} accent="white" />
```

### 10.4.4 MODES DE VUE

| Mode | Composant | Description |
|------|-----------|-------------|
| `split` | `ReconciliationSplitView` | Vue côte à côte transactions/factures |
| `list` | Onglets + DataTable | Vue liste avec onglets |

### 10.4.5 SUGGESTIONS IA

```javascript
const suggestions = useMemo(() => {
  return unmatchedTransactions.slice(0, 3).map((tx, idx) => {
    const inv = unmatchedInvoices[idx];
    return {
      id: tx.id,
      txId: tx.id,
      invoiceId: inv?.id,
      transaction: { label, date, amount, bank_account },
      invoice: { supplier, reference, date, amount },
      confidence: 0.92,  // Confiance IA
    };
  });
}, [unmatchedTransactions, unmatchedInvoices]);
```

### 10.4.6 BOUTONS ET ACTIONS

| Bouton | Ligne | Handler | Action |
|--------|-------|---------|--------|
| Vue Split | 256-260 | `setViewMode('split')` | Bascule vue split |
| Vue Liste | 261-267 | `setViewMode('list')` | Bascule vue liste |
| Actualiser | 271-274 | `refetchAll()` | Rafraîchit toutes les données |
| Rapprochement Auto | 275-278 | `handleRunReconciliation()` | Lance matching IA |
| Rapprocher (modal) | 543-549 | `handleManualMatch()` | Crée match manuel |

### 10.4.7 CASCADE - RAPPROCHEMENT MANUEL

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. UI: Sélection transaction + facture                              │
│    └─ selectedTransaction = {...}                                   │
│    └─ selectedInvoice = {...}                                       │
├─────────────────────────────────────────────────────────────────────┤
│ 2. Click "Rapprocher" → handleManualMatch()                         │
│    └─ createMatch.mutate({ transaction_id, invoice_id, type })      │
├─────────────────────────────────────────────────────────────────────┤
│ 3. Hook: useCreateManualMatch()                                     │
│    └─ POST /bank-reconciliation/match                               │
├─────────────────────────────────────────────────────────────────────┤
│ 4. API: backend/api/bank_reconciliation.py                          │
│    └─ create_match_endpoint()                                       │
├─────────────────────────────────────────────────────────────────────┤
│ 5. Service: backend/services/bank_reconciliation.py                 │
│    └─ create_match(tx_id, invoice_id)                               │
├─────────────────────────────────────────────────────────────────────┤
│ 6. DB: UPDATE finance_bank_invoice_matches                          │
│    └─ INSERT (transaction_id, invoice_id, match_type='manual')      │
├─────────────────────────────────────────────────────────────────────┤
│ 7. onSuccess:                                                       │
│    └─ invalidateQueries(['reconciliation', 'unmatched'])            │
│    └─ invalidateQueries(['reconciliation', 'summary'])              │
│    └─ Ferme modal, reset sélection                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10.5 HOOKS FINANCE - SIGNATURES COMPLÈTES

### 10.5.1 useFinance.js (380 lignes)

```javascript
// QUERIES
export const useFinanceTransactions = (filters = {}) => useInfiniteQuery({...})
  // Retourne: { data: { pages: [{items, total, page}] }, fetchNextPage, hasNextPage }

export const useFinanceAutreSuggestions = (params = {}) => useQuery({...})
  // Retourne: suggestions pour catégorie "Autre"

export const useFinanceCategoriesAutocomplete = (params = {}) => useQuery({...})
  // Retourne: autocomplete catégories (enabled if params.q)

export const useFinanceAnomalies = (params = {}) => useQuery({...})
  // Retourne: liste anomalies détectées

export const useFinanceMatches = (params = {}) => useQuery({...})
  // Retourne: rapprochements (filtrés par status)

export const useFinanceAccounts = (params = {}) => useQuery({...})
  // Retourne: liste comptes bancaires

export const useFinanceAccount = (accountId) => useQuery({...})
  // Retourne: détail un compte

// MUTATIONS
export const useFinanceBatchCategorize = () => useOfflineUpdate({...})
  // Catégorise plusieurs transactions

export const useUpdateFinanceTransaction = () => useOfflineUpdate({...})
  // Met à jour une transaction (optimistic update)

export const useLockFinanceTransaction = () => useMutation({...})
  // Verrouille une transaction

export const useFinanceImport = () => useMutation({...})
  // Import relevé CSV

export const useFinanceImportPDF = () => useMutation({...})
  // Import relevé PDF

export const useFinanceReconciliation = () => useMutation({...})
  // Lance rapprochement auto

export const useFinanceRefreshAnomalies = () => useMutation({...})
  // Rafraîchit détection anomalies

export const useFinanceMatchStatus = () => useMutation({...})
  // Change statut match

// ACCOUNTS CRUD
export const useCreateFinanceAccount = () => useOfflineCreate({...})
export const useUpdateFinanceAccount = () => useOfflineUpdate({...})
export const useDeleteFinanceAccount = () => useOfflineDelete({...})

// DEDUP & STATS
export const useDeduplicateTransactions = () => useMutation({...})
export const useRefreshFinanceStats = () => useMutation({...})

// PHASE 4: ML FEEDBACK
export const useCategoryFeedback = () => useMutation({...})
  // Enregistre correction catégorie pour ML

export const useCategoryFeedbackStats = () => useQuery({...})
  // Stats corrections globales

export const useCommonCorrections = (limit = 10) => useQuery({...})
  // Patterns de correction fréquents
```

### 10.5.2 useFinanceCategories.js (131 lignes)

```javascript
// QUERIES
export const useFinanceCategories = (filters = {}) => useQuery({...})
  // staleTime: 5 minutes

export const useFinanceCostCenters = (filters = {}) => useQuery({...})

export const useFinanceAccounts = (filters = {}) => useQuery({...})

export const useFinanceRules = (filters = {}) => useQuery({...})

export const useFinanceCategoryStats = (filters = {}) => useQuery({...})

export const useFinanceAccountsOverviewStats = (filters = {}) => useQuery({...})

export const useFinanceDashboardSummary = (filters = {}) => useQuery({...})

export const useFinanceTimeline = (filters = {}) => useQuery({...})
  // Timeline entrées/sorties par période

export const useFinanceCategoryBreakdown = (filters = {}) => useQuery({...})
  // Répartition par catégorie

export const useFinanceTreasury = (filters = {}) => useQuery({...})
  // Solde, trends, flux

// MUTATIONS
export const useCreateFinanceCategory = () => useMutation({...})
export const useCreateFinanceCostCenter = () => useMutation({...})

export const useFinanceRuleMutations = () => ({
  create: useMutation({...}),
  update: useMutation({...}),
  remove: useMutation({...}),
})
```

### 10.5.3 useBankReconciliation.js (187 lignes)

```javascript
// QUERIES INDIVIDUELLES
export function useReconciliationSummary(daysBack = 90)
export function useUnmatchedTransactions(filters = {})
export function useUnmatchedInvoices(daysBack = 90)
export function useSupplierAliases()

// MUTATIONS
export function useRunReconciliation()     // Lance matching auto
export function useCreateManualMatch()     // Match manuel
export function useCreateSupplierAlias()   // Crée alias fournisseur
export function useDeleteSupplierAlias()   // Supprime alias

// HOOK COMBINÉ
export function useBankReconciliation(filters = {}) {
  return {
    summary,
    transactions,
    invoices,
    aliases,
    isLoading,
    isError,
    runReconciliation,
    createMatch,
    createAlias,
    deleteAlias,
    refetchAll,
  };
}
```

---

## 10.6 INVALIDATION DE CACHE - MODULE FINANCE

| Mutation | Queries invalidées |
|----------|-------------------|
| `useUpdateFinanceTransaction` | `['finance', 'transactions']`, `['finance', 'autre-top']` |
| `useLockFinanceTransaction` | `['finance', 'transactions']` |
| `useFinanceImport` | `['finance', 'transactions']` |
| `useFinanceImportPDF` | `['finance', 'transactions']`, `['finance', 'imports']` |
| `useFinanceReconciliation` | `['finance', 'transactions']`, `['finance', 'matches']`, `['finance', 'anomalies']`, `['bank-reconciliation']` |
| `useFinanceRefreshAnomalies` | `['finance', 'anomalies']`, `['anomaly-detection']` |
| `useFinanceMatchStatus` | `['finance', 'matches']`, `['finance', 'transactions']`, `['bank-reconciliation']` |
| `useCreateManualMatch` | `['reconciliation', 'unmatched']`, `['reconciliation', 'summary']` |
| `useRunReconciliation` | `['reconciliation']` (toutes les sous-clés) |
| `useCategoryFeedback` | `['finance', 'feedback']`, `['finance', 'transactions']` |

---

# PARTIE 11: MODULE RESTAURANT - DOCUMENTATION EXHAUSTIVE

---

## 11.1 VUE D'ENSEMBLE DU MODULE

Le module Restaurant gère les plats, ingrédients, food cost, tarification et stock restaurant.

### 11.1.1 ARCHITECTURE DES PAGES

```
/restaurant
├── /plats              → PlatsCatalogPage.jsx (Catalogue plats)
├── /ingredients        → IngredientsPage.jsx (Ingrédients)
├── /overview           → RestaurantOverviewPage.jsx (Dashboard)
├── /food-cost          → FoodCostAnalysisPage.jsx (Analyses)
├── /liens              → LiensEpiceriePage.jsx (Liens épicerie)
├── /stock              → RestaurantStockMovementsPage.jsx
├── /consumptions       → RestaurantConsumptionPage.jsx
├── /forecasts          → ForecastsPage.jsx
├── /charges            → RestaurantChargesPage.jsx
└── /menus              → RestaurantMenusCostsPage.jsx
```

### 11.1.2 HOOKS DU MODULE RESTAURANT

```
frontend/src/hooks/useRestaurant.js  # 589 lignes
├── Queries plats et ingrédients
├── Mutations CRUD
├── Prix et historiques
├── Liens épicerie
├── Stock restaurant
└── Forecasts et analyses
```

---

## 11.2 PLATSCATALOGPAGE.JSX - CATALOGUE DES PLATS

**Fichier:** `frontend/src/features/restaurant/PlatsCatalogPage.jsx`
**Lignes:** 519
**Route:** `/restaurant/plats`

### 11.2.1 ÉTAT LOCAL

```javascript
const [activeTab, setActiveTab] = useState('foodcost');
const [search, setSearch] = useState('');
const [categoryFilter, setCategoryFilter] = useState('');
const [selectedPlat, setSelectedPlat] = useState(null);      // Modal édition prix
const [drawerPlat, setDrawerPlat] = useState(null);          // Drawer détails
const [showCreateModal, setShowCreateModal] = useState(false);
const [simulatorPlat, setSimulatorPlat] = useState(null);    // Modal simulateur
const [historyPlat, setHistoryPlat] = useState(null);        // Modal historique
```

### 11.2.2 ONGLETS

```javascript
const TABS = [
  { id: 'foodcost', label: 'Food Cost & Plats' },
  { id: 'ingredients', label: 'Ingrédients & Prix' },
  { id: 'stock', label: 'Stock & Consommations' },
];
```

### 11.2.3 HOOKS UTILISÉS

| Hook | Purpose |
|------|---------|
| `useRestaurantPlats()` | Liste des plats avec food cost |
| `useRestaurantDashboard()` | Stats globales restaurant |
| `useUpdateRestaurantPlatPrice()` | Mutation prix plat |
| `useRestaurantPlatPriceHistory(platId)` | Historique prix plat |

### 11.2.4 HERO FOOD COST

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FOOD COST MOYEN                              │
│                            28%                                      │
│                 ✓ Objectif atteint (<30%)                           │
│                                                                     │
│   Couleurs: emerald (<30%) | amber (30-35%) | rose (>35%)           │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.2.5 STATS GRID (4 cards)

| Card | Valeur | Calcul |
|------|--------|--------|
| Prix Moyen Plat | €14.50 | `avg(prix_vente_ttc)` |
| Coût Moyen Matière | €4.20 | `avg(cout_matiere)` |
| Marge Moyenne | €10.30 | `avgPrice - avgCost` |
| Plat le + Rentable | "Burger" | `min(food_cost_pct)` |

### 11.2.6 CARTE PLAT

```
┌────────────────────────────────────────────┐
│  [Image/Emoji]               [28%]         │  ← Badge food cost coloré
│  [Inactif] (si !actif)                     │
├────────────────────────────────────────────┤
│  Burger Maison                             │
│  PLATS • Cuisine                           │
├────────────────────────────────────────────┤
│  Prix vente    │  Coût matière             │
│  €14.50        │  €4.20                    │
│  Marge         │  Food Cost                │
│  €10.30        │  28.9%                    │
├────────────────────────────────────────────┤
│  Ingrédients (5)                           │
│  [Pain] [Steak] [Tomate] [Salade] [+2]     │
├────────────────────────────────────────────┤
│  [Modifier prix]  [Détails]                │
└────────────────────────────────────────────┘
```

### 11.2.7 BOUTONS ET ACTIONS

| Bouton | Ligne | Handler | Action |
|--------|-------|---------|--------|
| Nouveau plat | 152-158 | `setShowCreateModal(true)` | Ouvre AddPlatModal |
| Modifier prix | 336-341 | `setSelectedPlat(plat)` | Ouvre PlatDetailModal |
| Détails | 345-350 | `setDrawerPlat(plat)` | Ouvre PlatDetailDrawer |
| Historique (drawer) | 417-420 | `setHistoryPlat(plat)` | Ouvre modal historique |
| Simulateur (drawer) | 421-424 | `setSimulatorPlat(plat)` | Ouvre PriceSimulatorPanel |

### 11.2.8 MODALS ET DRAWERS

| Composant | Props | Fichier |
|-----------|-------|---------|
| `PlatDetailModal` | `plat, isOpen, onClose, onUpdatePrice` | `components/PlatDetailModal.jsx` |
| `PlatDetailDrawer` | `open, onClose, plat, onEdit, onHistory, onSimulate` | `components/PlatDetailDrawer.jsx` |
| `AddPlatModal` | `open, onClose, onSuccess` | `components/AddPlatModal.jsx` |
| `PriceSimulatorPanel` | `platData, onApply` | `components/PriceSimulatorPanel.jsx` |

### 11.2.9 CASCADE - CRÉATION PLAT

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. UI: Click "Nouveau plat"                                         │
│    └─ setShowCreateModal(true)                                      │
├─────────────────────────────────────────────────────────────────────┤
│ 2. AddPlatModal: Formulaire                                         │
│    └─ nom, categorie, prix_vente_ttc, type                          │
├─────────────────────────────────────────────────────────────────────┤
│ 3. Submit → useCreateRestaurantPlat.mutate(payload)                 │
│    └─ POST /restaurant/plats                                        │
├─────────────────────────────────────────────────────────────────────┤
│ 4. API: backend/api/restaurant.py                                   │
│    └─ create_plat_endpoint()                                        │
├─────────────────────────────────────────────────────────────────────┤
│ 5. Service: backend/services/restaurant.py                          │
│    └─ create_plat(tenant_id, payload)                               │
├─────────────────────────────────────────────────────────────────────┤
│ 6. DB: INSERT INTO restaurant_plats                                 │
│    └─ Calcul auto cout_matiere = 0 (pas d'ingrédients)              │
├─────────────────────────────────────────────────────────────────────┤
│ 7. onSuccess:                                                       │
│    └─ invalidateQueries(['restaurant', 'plats'])                    │
│    └─ invalidateQueries(['restaurant', 'dashboard'])                │
│    └─ platsQuery.refetch()                                          │
│    └─ setShowCreateModal(false)                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 11.3 INGREDIENTSPAGE.JSX - LISTE INGRÉDIENTS

**Fichier:** `frontend/src/features/restaurant/IngredientsPage.jsx`
**Lignes:** 935
**Route:** `/restaurant/ingredients`

### 11.3.1 ÉTAT LOCAL

```javascript
const [search, setSearch] = useState('');
const [supplierFilter, setSupplierFilter] = useState('');
const [categoryFilter, setCategoryFilter] = useState('');
const [trendFilter, setTrendFilter] = useState('all');
const [selectedIngredient, setSelectedIngredient] = useState(null);
const [isEditing, setIsEditing] = useState(false);
const [editForm, setEditForm] = useState({});
const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
const [quickStockUpdate, setQuickStockUpdate] = useState(null);
const [quickStockValue, setQuickStockValue] = useState('');
const [showCreateModal, setShowCreateModal] = useState(false);
const [drawerIngredient, setDrawerIngredient] = useState(null);
```

### 11.3.2 HOOKS UTILISÉS

| Hook | Purpose |
|------|---------|
| `useRestaurantIngredients()` | Liste ingrédients |
| `useUpdateRestaurantIngredient()` | Mutation update |
| `useDeleteRestaurantIngredient()` | Mutation delete |
| `useSyncIngredientPrices()` | Sync prix depuis épicerie |
| `usePriceSyncStatus()` | Statut liens épicerie |
| `useRestaurantIngredientPriceHistory(id)` | Historique prix |

### 11.3.3 FILTRES

```javascript
const filters = [
  { type: 'search', placeholder: 'Rechercher un ingrédient...' },
  { type: 'select', options: suppliers, placeholder: 'Tous les fournisseurs' },
  { type: 'select', options: categories, placeholder: 'Toutes les catégories' },
  { type: 'select', options: ['all', 'up', 'down', 'stable'], placeholder: 'Tendance' },
];
```

### 11.3.4 STATS HEADER

| Stat | Valeur | Condition couleur |
|------|--------|-------------------|
| Total | `ingredients.length` | blanc |
| Stock bas | `count(stock_actuel <= stock_min)` | rose (si > 0) |
| Prix en hausse | `count(price_trend === 'up')` | rose |
| Prix en baisse | `count(price_trend === 'down')` | emerald |
| Liés épicerie | `syncStatus.linked_count` | cyan |

### 11.3.5 COLONNES SMARTTABLE

| Colonne | Render |
|---------|--------|
| Ingrédient | Nom + catégorie + fournisseur |
| Prix unitaire | `formatCurrency(cout_unitaire)` / unité |
| Stock | Valeur + badge (Critique/Bas/OK) |
| Tendance | Icon (↑/↓/—) + badge pourcentage |
| Évolution (30j) | `<Sparkline data={price_history} />` |
| Actions | Boutons aperçu / détails |

### 11.3.6 VUE MOBILE (MobileIngredientRow)

```javascript
<MobileIngredientRow
  ingredient={ingredient}
  onOpenDetail={handleOpenDetail}
  onQuickStockUpdate={handleQuickStockOpen}
  onDelete={handleDeleteWithConfirm}
  formatCurrency={formatCurrency}
/>
```

### 11.3.7 BOUTONS ET ACTIONS

| Bouton | Ligne | Handler | Action |
|--------|-------|---------|--------|
| Nouvel ingrédient | 388-395 | `setShowCreateModal(true)` | Ouvre AddIngredientModal |
| Sync Prix | 396-403 | `handleSyncPrices(false)` | Synchronise depuis épicerie |
| Liens Epicerie | 404-411 | `navigate('/restaurant/liens')` | Navigue vers liens |
| Modifier | 765-770 | `setIsEditing(true)` | Passe en mode édition |
| Supprimer | 771-777 | `setShowDeleteConfirm(true)` | Ouvre confirmation |

### 11.3.8 MODAL ÉDITION INGRÉDIENT

**Champs éditables:**
```javascript
const editForm = {
  nom: ingredient.nom,
  unite_base: ingredient.unite_base,
  cout_unitaire: ingredient.cout_unitaire,
  stock_actuel: ingredient.stock_actuel,
  stock_min: ingredient.stock_min,
  categorie: ingredient.categorie,
  fournisseur: ingredient.fournisseur,
};
```

### 11.3.9 QUICK STOCK UPDATE

Modal optimisée cuisine avec:
- Grande zone de saisie numérique
- Boutons +1, +5, +10
- Targets touch 44px minimum

```javascript
<Modal title="Mise à jour du stock" size="sm">
  <input type="number" className="text-2xl font-bold text-center" />
  <div className="grid grid-cols-3 gap-2">
    <Button onClick={() => setQuickStockValue(val + 1)}>+1</Button>
    <Button onClick={() => setQuickStockValue(val + 5)}>+5</Button>
    <Button onClick={() => setQuickStockValue(val + 10)}>+10</Button>
  </div>
</Modal>
```

---

## 11.4 HOOKS RESTAURANT - SIGNATURES COMPLÈTES

### 11.4.1 useRestaurant.js (589 lignes)

```javascript
// ============================================================================
// CATÉGORIES ET CENTRES DE COÛTS
// ============================================================================
export const useRestaurantCategories = () => useQuery({...})
export const useCreateRestaurantCategory = () => useOfflineCreate({...})
export const useRestaurantCostCenters = () => useQuery({...})
export const useCreateRestaurantCostCenter = () => useOfflineCreate({...})

// ============================================================================
// CHARGES (DÉPENSES)
// ============================================================================
export const useRestaurantExpenses = () => useQuery({...})
export const useCreateRestaurantExpense = () => useOfflineCreate({...})
export const useRestaurantExpenseSummary = () => useQuery({...})

// ============================================================================
// INGRÉDIENTS
// ============================================================================
export const useRestaurantIngredients = () => useQuery({
  queryKey: ['restaurant', 'ingredients'],
  staleTime: 60 * 1000,
})

export const useCreateRestaurantIngredient = () => useOfflineCreate({...})
export const useUpdateRestaurantIngredient = () => useOfflineUpdate({...})
export const useDeleteRestaurantIngredient = () => useOfflineDelete({...})

// ============================================================================
// PLATS
// ============================================================================
export const useRestaurantPlats = () => useQuery({
  queryKey: ['restaurant', 'plats'],
  staleTime: 60 * 1000,
})

export const useCreateRestaurantPlat = () => useOfflineCreate({...})
export const useDeleteRestaurantPlat = () => useOfflineDelete({...})

// ============================================================================
// INGRÉDIENTS D'UN PLAT
// ============================================================================
export const useAddIngredientToPlat = () => useMutation({
  mutationFn: ({ platId, payload }) => api.post(`/restaurant/plats/${platId}/ingredients`, payload),
})

export const useUpdateIngredientOnPlat = () => useMutation({...})
export const useRemoveIngredientFromPlat = () => useMutation({...})
export const useAttachIngredientToPlat = () => useOfflineCreate({...})

// ============================================================================
// PRIX ET HISTORIQUES
// ============================================================================
export const useUpdateRestaurantIngredientPrice = () => useOfflineUpdate({...})
export const useRestaurantIngredientPriceHistory = (ingredientId) => useQuery({...})
export const useUpdateRestaurantPlatPrice = () => useOfflineUpdate({...})
export const useRestaurantPlatPriceHistory = (platId) => useQuery({...})
export const useRestaurantPriceHistoryOverview = (limit = 12) => useQuery({...})

// ============================================================================
// DASHBOARD ET ANALYTICS
// ============================================================================
export const useRestaurantDashboard = () => useQuery({
  queryKey: ['restaurant', 'dashboard'],
  staleTime: 60 * 1000,
})

export const useRestaurantForecastOverview = (options) => useQuery({...})
export const useRestaurantTvaSummary = (months) => useQuery({...})
export const useRestaurantConsumptions = (period) => useQuery({...})
export const useRestaurantPriceHistoryComparison = () => useQuery({...})

// ============================================================================
// FOOD COST & OVERVIEW
// ============================================================================
export const useRestaurantOverview = (filters) => useQuery({...})
export const useRestaurantPlatDetails = (platId) => useQuery({...})
export const useRestaurantPlatIngredients = (platId) => useQuery({...})
export const useSimulatePlatPrice = () => useMutation({...})
export const useRestaurantAlerts = (filters) => useQuery({...})
export const useRestaurantFoodCostAnalysis = (filters) => useQuery({...})
export const useRestaurantMenusOverview = () => useQuery({...})

// ============================================================================
// LIENS ÉPICERIE
// ============================================================================
export const useEpicerieProducts = () => useQuery({
  queryKey: ['epicerie', 'products'],
  staleTime: 5 * 60 * 1000,
})

export const useLinkIngredientEpicerie = () => useMutation({
  mutationFn: ({ ingredientId, epicerieProductId, ratio }) =>
    linkIngredientToEpicerie(ingredientId, epicerieProductId, ratio),
})

export const useUnlinkIngredientEpicerie = () => useMutation({...})
export const useUpdateIngredientRatio = () => useMutation({...})

// ============================================================================
// SYNCHRONISATION PRIX
// ============================================================================
export const useSyncIngredientPrices = () => useMutation({
  mutationFn: ({ forceUpdate }) => syncRestaurantIngredientPrices(forceUpdate),
  onSuccess: () => {
    invalidateQueries(['restaurant', 'ingredients'])
    invalidateQueries(['restaurant', 'price-sync-status'])
    invalidateQueries(['restaurant', 'dashboard'])
    invalidateQueries(['restaurant', 'prices', 'history'])
  },
})

export const usePriceSyncStatus = () => useQuery({...})

// ============================================================================
// TRANSFERTS STOCK ÉPICERIE → RESTAURANT
// ============================================================================
export const useTransferFromEpicerie = () => useMutation({
  mutationFn: ({ ingredientId, produitEpicerieId, quantite, commentaire }) =>
    api.post('/restaurant/stock/transfer-from-epicerie', {...}),
})

// ============================================================================
// STOCK RESTAURANT
// ============================================================================
export const useRestaurantStockMovements = (filters) => useQuery({...})
export const useRestaurantStockSummary = () => useQuery({...})
export const useRestaurantStockAnalytics = (days) => useQuery({...})
export const useRestaurantStockDailyByCategory = (filters) => useQuery({...})
export const useRestaurantStockDailyByPlat = (filters) => useQuery({...})
export const useCreateRestaurantStockMovement = () => useMutation({...})
```

---

## 11.5 INVALIDATION DE CACHE - MODULE RESTAURANT

| Mutation | Queries invalidées |
|----------|-------------------|
| `useCreateRestaurantIngredient` | `['restaurant', 'ingredients']`, `['restaurant', 'dashboard']` |
| `useUpdateRestaurantIngredient` | `['restaurant', 'ingredients']`, `['restaurant', 'plats']`, `['restaurant', 'dashboard']` |
| `useDeleteRestaurantIngredient` | `['restaurant', 'ingredients']`, `['restaurant', 'dashboard']` |
| `useCreateRestaurantPlat` | `['restaurant', 'plats']`, `['restaurant', 'dashboard']` |
| `useDeleteRestaurantPlat` | `['restaurant', 'plats']`, `['restaurant', 'dashboard']` |
| `useAddIngredientToPlat` | `['restaurant', 'plats']`, `['restaurant', 'plat', 'details', platId]` |
| `useUpdateRestaurantIngredientPrice` | `['restaurant', 'ingredients']`, `['restaurant', 'dashboard']`, `['restaurant', 'prices', 'history']`, `['restaurant', 'ingredient', 'history', id]` |
| `useUpdateRestaurantPlatPrice` | `['restaurant', 'plats']`, `['restaurant', 'dashboard']`, `['restaurant', 'prices', 'history']`, `['restaurant', 'plat', 'history', platId]` |
| `useSyncIngredientPrices` | `['restaurant', 'ingredients']`, `['restaurant', 'price-sync-status']`, `['restaurant', 'dashboard']`, `['restaurant', 'prices', 'history']` |
| `useLinkIngredientEpicerie` | `['restaurant', 'ingredients']`, `['restaurant', 'dashboard']` |
| `useTransferFromEpicerie` | `['restaurant-stock']`, `['restaurant', 'ingredients']`, `['restaurant', 'dashboard']` |
| `useCreateRestaurantStockMovement` | `['restaurant-stock']`, `['restaurant', 'ingredients']` |

---

## 11.6 TABLES POSTGRESQL - MODULE RESTAURANT

```sql
-- Plats
CREATE TABLE restaurant_plats (
  id SERIAL PRIMARY KEY,
  tenant_id INT REFERENCES tenants(id),
  nom VARCHAR(200) NOT NULL,
  categorie VARCHAR(100),
  type VARCHAR(50) DEFAULT 'cuisine',  -- 'cuisine' ou 'bar'
  prix_vente_ttc DECIMAL(10,2),
  cout_matiere DECIMAL(10,2) DEFAULT 0,
  food_cost_pct DECIMAL(5,2) DEFAULT 0,
  actif BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Ingrédients
CREATE TABLE restaurant_ingredients (
  id SERIAL PRIMARY KEY,
  tenant_id INT REFERENCES tenants(id),
  nom VARCHAR(200) NOT NULL,
  unite_base VARCHAR(20),
  cout_unitaire DECIMAL(10,4),
  stock_actuel DECIMAL(10,2) DEFAULT 0,
  stock_min DECIMAL(10,2),
  categorie VARCHAR(100),
  fournisseur VARCHAR(100),
  epicerie_product_id INT,  -- Lien vers produits épicerie
  epicerie_ratio DECIMAL(10,4) DEFAULT 1.0,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Composition plat
CREATE TABLE restaurant_plat_ingredients (
  id SERIAL PRIMARY KEY,
  plat_id INT REFERENCES restaurant_plats(id) ON DELETE CASCADE,
  ingredient_id INT REFERENCES restaurant_ingredients(id),
  quantite DECIMAL(10,4) NOT NULL,
  tenant_id INT
);

-- Historique prix plats
CREATE TABLE restaurant_plat_price_history (
  id SERIAL PRIMARY KEY,
  plat_id INT REFERENCES restaurant_plats(id),
  prix_vente_ttc DECIMAL(10,2),
  created_at TIMESTAMP DEFAULT NOW(),
  tenant_id INT
);

-- Historique prix ingrédients
CREATE TABLE restaurant_ingredient_price_history (
  id SERIAL PRIMARY KEY,
  ingredient_id INT REFERENCES restaurant_ingredients(id),
  cout_unitaire DECIMAL(10,4),
  changed_at TIMESTAMP DEFAULT NOW(),
  tenant_id INT
);
```

---

# PARTIE 12: Dashboard & Cockpit - Documentation Exhaustive

## 12.1 DashboardPage.jsx - Vue d'Ensemble Complète

**Fichier**: `frontend/src/features/dashboard/DashboardPage.jsx` (250 lignes)

### Rôle et Responsabilités

Le Dashboard est le point d'entrée principal de l'application. Il agrège les métriques clés de tous les modules (stock, ventes, marges, alertes) pour donner une vision synthétique de l'état de l'entreprise.

### Import et Dépendances

```javascript
import { useDashboardMetrics } from '../../hooks/useDashboard.js';
import { useProducts } from '../../hooks/useProducts.js';
import DashboardHero from './components/DashboardHero.jsx';
import DashboardMetrics from './components/DashboardMetrics.jsx';
import WeeklyFlowsChart from './components/WeeklyFlowsChart.jsx';
import CategoryStockChart from './components/CategoryStockChart.jsx';
import DashboardList from './components/DashboardList.jsx';
```

### Hooks Utilisés

| Hook | Source | Données Retournées |
|------|--------|-------------------|
| `useDashboardMetrics()` | `useDashboard.js` | KPIs agrégés, alertes, variations |
| `useProducts({ low_stock: true })` | `useProducts.js` | Produits en stock bas pour alertes |

### Structure du Composant

```javascript
export default function DashboardPage() {
  // Données dashboard agrégées
  const { data: metrics, isLoading, error } = useDashboardMetrics();

  // Produits en alerte stock pour liste rapide
  const { data: lowStockProducts } = useProducts({
    low_stock: true,
    per_page: 10
  });

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorState error={error} />;

  return (
    <div className="min-h-screen bg-[#0a0a0f] p-6">
      {/* Hero avec KPIs principaux */}
      <DashboardHero metrics={metrics} />

      {/* Grille de métriques détaillées */}
      <DashboardMetrics metrics={metrics} />

      {/* Graphiques côte à côte */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <WeeklyFlowsChart data={metrics.weekly_flows} />
        <CategoryStockChart data={metrics.category_stock} />
      </div>

      {/* Listes d'alertes et actions rapides */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <DashboardList
          title="Stock Bas"
          items={lowStockProducts}
          type="low_stock"
        />
        <DashboardList
          title="Marge < 20%"
          items={metrics.margin_alerts}
          type="margin"
        />
        <DashboardList
          title="Top Ventes"
          items={metrics.top_sales}
          type="sales"
        />
      </div>
    </div>
  );
}
```

### Composants Enfants Détaillés

#### DashboardHero.jsx

**Props attendues:**
```javascript
{
  metrics: {
    total_stock_value: number,      // Valeur totale stock
    total_stock_value_trend: number, // % variation vs période précédente
    margin_global: number,           // Marge brute globale %
    margin_trend: number,            // Variation marge
    products_count: number,          // Nombre total produits
    low_stock_count: number,         // Produits en stock bas
    out_of_stock_count: number       // Produits en rupture
  }
}
```

**Rendu:**
```jsx
<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
  {/* KPI Card - Valeur Stock */}
  <div className="glass-card p-6 rounded-2xl">
    <div className="text-slate-400 text-sm">Valeur Stock</div>
    <div className="text-3xl font-bold text-white">
      {formatCurrency(metrics.total_stock_value)}
    </div>
    <TrendBadge value={metrics.total_stock_value_trend} />
  </div>

  {/* KPI Card - Marge Globale */}
  <div className="glass-card p-6 rounded-2xl">
    <div className="text-slate-400 text-sm">Marge Brute</div>
    <div className="text-3xl font-bold text-emerald-400">
      {metrics.margin_global.toFixed(1)}%
    </div>
    <TrendBadge value={metrics.margin_trend} />
  </div>

  {/* Alertes compteurs */}
  <div className="glass-card p-6 rounded-2xl">
    <div className="text-amber-400 text-4xl font-bold">
      {metrics.low_stock_count}
    </div>
    <div className="text-slate-400">Stock Bas</div>
  </div>

  <div className="glass-card p-6 rounded-2xl">
    <div className="text-red-400 text-4xl font-bold">
      {metrics.out_of_stock_count}
    </div>
    <div className="text-slate-400">Ruptures</div>
  </div>
</div>
```

#### DashboardMetrics.jsx

**Props attendues:**
```javascript
{
  metrics: {
    ca_jour: number,           // CA du jour
    ca_semaine: number,        // CA semaine
    ca_mois: number,           // CA mois
    panier_moyen: number,      // Panier moyen
    transactions_jour: number, // Nombre transactions jour
    rotation_stock: number,    // Jours de stock moyen
    top_category: string,      // Catégorie top ventes
    top_supplier: string       // Fournisseur principal
  }
}
```

**Grille de métriques:**
```jsx
<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
  <MetricCard
    label="CA Jour"
    value={formatCurrency(metrics.ca_jour)}
    icon={<Euro />}
    color="emerald"
  />
  <MetricCard
    label="Panier Moyen"
    value={formatCurrency(metrics.panier_moyen)}
    icon={<ShoppingCart />}
    color="blue"
  />
  <MetricCard
    label="Rotation Stock"
    value={`${metrics.rotation_stock}j`}
    icon={<RefreshCw />}
    color="amber"
  />
  <MetricCard
    label="Transactions"
    value={metrics.transactions_jour}
    icon={<Receipt />}
    color="violet"
  />
</div>
```

#### WeeklyFlowsChart.jsx

**Props attendues:**
```javascript
{
  data: [
    { jour: "Lun", entrees: 1500, sorties: 1200 },
    { jour: "Mar", entrees: 2000, sorties: 1800 },
    // ... 7 jours
  ]
}
```

**Visualisation:**
- Graphique à barres empilées (entrées vs sorties)
- Couleurs: Entrées = emerald, Sorties = rose
- Affichage du solde net par jour

#### CategoryStockChart.jsx

**Props attendues:**
```javascript
{
  data: [
    { category: "Épicerie", value: 45000, percentage: 35 },
    { category: "Boissons", value: 30000, percentage: 23 },
    { category: "Frais", value: 25000, percentage: 19 },
    { category: "Surgelés", value: 15000, percentage: 12 },
    { category: "Autres", value: 14000, percentage: 11 }
  ]
}
```

**Visualisation:**
- Donut chart avec légende
- Centre: Valeur totale
- Hover: Détail catégorie

#### DashboardList.jsx

**Props attendues:**
```javascript
{
  title: string,           // Titre de la liste
  items: Array<{
    id: number,
    name: string,
    value: number | string,
    trend?: number,
    alert_level?: 'warning' | 'critical'
  }>,
  type: 'low_stock' | 'margin' | 'sales'
}
```

**Rendu conditionnel par type:**
```jsx
{type === 'low_stock' && (
  <div className="flex items-center justify-between p-3 hover:bg-white/5 rounded-lg">
    <div>
      <div className="text-white font-medium">{item.name}</div>
      <div className="text-slate-400 text-sm">Stock: {item.value}</div>
    </div>
    <StatusBadge level={item.alert_level} />
  </div>
)}

{type === 'margin' && (
  <div className="flex items-center justify-between p-3">
    <div className="text-white">{item.name}</div>
    <div className={`font-bold ${item.value < 15 ? 'text-red-400' : 'text-amber-400'}`}>
      {item.value}%
    </div>
  </div>
)}

{type === 'sales' && (
  <div className="flex items-center justify-between p-3">
    <div className="text-white">{item.name}</div>
    <div className="text-emerald-400 font-bold">
      {formatCurrency(item.value)}
    </div>
  </div>
)}
```

---

## 12.2 Hook useDashboard.js

**Fichier**: `frontend/src/hooks/useDashboard.js`

### Implémentation Complète

```javascript
import { useQuery } from '@tanstack/react-query';
import { fetchDashboardMetrics, fetchDashboardAlerts } from '../api/client.js';

/**
 * Hook principal pour les métriques du dashboard.
 * Agrège toutes les données nécessaires à la vue d'ensemble.
 *
 * @param {Object} options
 * @param {number} options.period - Période en jours (default: 30)
 * @returns {Object} Query avec métriques agrégées
 */
export function useDashboardMetrics(options = { period: 30 }) {
  return useQuery({
    queryKey: ['dashboard', 'metrics', options.period],
    queryFn: () => fetchDashboardMetrics(options),
    staleTime: 5 * 60 * 1000,      // 5 minutes - données relativement stables
    refetchInterval: 5 * 60 * 1000, // Refresh auto toutes les 5 min
    refetchOnWindowFocus: true,
  });
}

/**
 * Hook pour les alertes temps réel du dashboard.
 *
 * @returns {Object} Query avec alertes actives
 */
export function useDashboardAlerts() {
  return useQuery({
    queryKey: ['dashboard', 'alerts'],
    queryFn: fetchDashboardAlerts,
    staleTime: 60 * 1000,           // 1 minute - données plus volatiles
    refetchInterval: 60 * 1000,     // Refresh toutes les minutes
  });
}

/**
 * Hook pour le résumé stock rapide.
 *
 * @returns {Object} Compteurs stock
 */
export function useStockSummary() {
  return useQuery({
    queryKey: ['dashboard', 'stock-summary'],
    queryFn: async () => {
      const response = await fetch('/api/stock/summary');
      return response.json();
    },
    staleTime: 2 * 60 * 1000,
  });
}
```

### Fonction API Client

**Fichier**: `frontend/src/api/client.js`

```javascript
export async function fetchDashboardMetrics(options = {}) {
  const params = new URLSearchParams();
  if (options.period) params.set('period', options.period);

  const response = await apiFetch(`/dashboard/metrics?${params}`);
  return response;
}

export async function fetchDashboardAlerts() {
  return apiFetch('/dashboard/alerts');
}
```

---

## 12.3 Backend Service Dashboard

**Fichier**: `backend/services/dashboard.py` (232 lignes)

### Structure Complète du Service

```python
"""
Services d'agrégation pour le dashboard principal.

Ce module centralise toutes les requêtes nécessaires au dashboard
en optimisant les accès base de données.
"""

from __future__ import annotations

from typing import Any
from decimal import Decimal
from datetime import datetime, timedelta

from sqlalchemy import text

from core.data_repository import query_df, get_engine


def fetch_kpis(*, tenant_id: int = 1) -> dict[str, Any]:
    """
    Récupère les KPIs principaux du dashboard.

    Returns:
        dict contenant:
        - total_products: int
        - total_stock_value: Decimal
        - low_stock_count: int
        - out_of_stock_count: int
        - avg_margin: Decimal
    """
    sql = """
        SELECT
            COUNT(*) as total_products,
            COALESCE(SUM(stock_actuel * prix_achat_ht), 0) as total_stock_value,
            COUNT(*) FILTER (
                WHERE stock_actuel > 0
                AND stock_actuel <= COALESCE(stock_min, 5)
            ) as low_stock_count,
            COUNT(*) FILTER (WHERE stock_actuel <= 0) as out_of_stock_count,
            COALESCE(AVG(
                CASE WHEN prix_vente_ttc > 0 AND prix_achat_ht > 0
                THEN (prix_vente_ttc - prix_achat_ht) / prix_vente_ttc * 100
                END
            ), 0) as avg_margin
        FROM produits
        WHERE tenant_id = :tenant_id
          AND actif = true
    """
    df = query_df(sql, params={"tenant_id": tenant_id})
    if df.empty:
        return {
            "total_products": 0,
            "total_stock_value": Decimal("0"),
            "low_stock_count": 0,
            "out_of_stock_count": 0,
            "avg_margin": Decimal("0"),
        }

    row = df.iloc[0]
    return {
        "total_products": int(row["total_products"]),
        "total_stock_value": Decimal(str(row["total_stock_value"])),
        "low_stock_count": int(row["low_stock_count"]),
        "out_of_stock_count": int(row["out_of_stock_count"]),
        "avg_margin": Decimal(str(row["avg_margin"])),
    }


def fetch_top_stock_value(*, tenant_id: int = 1, limit: int = 10) -> list[dict]:
    """
    Récupère les produits avec la plus haute valeur stock.

    Args:
        tenant_id: ID du tenant
        limit: Nombre de produits à retourner

    Returns:
        Liste de dicts avec id, nom, stock_value, stock_actuel
    """
    sql = """
        SELECT
            id,
            nom,
            (stock_actuel * prix_achat_ht) as stock_value,
            stock_actuel,
            prix_achat_ht
        FROM produits
        WHERE tenant_id = :tenant_id
          AND actif = true
          AND stock_actuel > 0
          AND prix_achat_ht > 0
        ORDER BY stock_value DESC
        LIMIT :limit
    """
    df = query_df(sql, params={"tenant_id": tenant_id, "limit": limit})
    return df.to_dict("records")


def fetch_top_sales(
    *,
    tenant_id: int = 1,
    days: int = 30,
    limit: int = 10
) -> list[dict]:
    """
    Récupère les produits les plus vendus sur la période.

    Args:
        tenant_id: ID du tenant
        days: Nombre de jours à analyser
        limit: Nombre de produits à retourner

    Returns:
        Liste de dicts avec id, nom, total_sold, revenue
    """
    sql = """
        SELECT
            p.id,
            p.nom,
            COALESCE(SUM(ABS(m.quantite)), 0) as total_sold,
            COALESCE(SUM(ABS(m.quantite) * p.prix_vente_ttc), 0) as revenue
        FROM produits p
        LEFT JOIN mouvements_stock m
            ON m.produit_id = p.id
            AND m.type = 'SORTIE'
            AND m.source LIKE '%vente%'
            AND m.date_mvt >= NOW() - INTERVAL ':days days'
            AND m.tenant_id = :tenant_id
        WHERE p.tenant_id = :tenant_id
          AND p.actif = true
        GROUP BY p.id, p.nom
        HAVING SUM(ABS(m.quantite)) > 0
        ORDER BY total_sold DESC
        LIMIT :limit
    """
    df = query_df(sql, params={
        "tenant_id": tenant_id,
        "days": days,
        "limit": limit
    })
    return df.to_dict("records")


def fetch_weekly_variation(*, tenant_id: int = 1) -> list[dict]:
    """
    Récupère les flux entrants/sortants par jour sur la semaine.

    Returns:
        Liste de 7 dicts avec jour, entrees, sorties, solde
    """
    sql = """
        WITH days AS (
            SELECT generate_series(
                DATE_TRUNC('day', NOW()) - INTERVAL '6 days',
                DATE_TRUNC('day', NOW()),
                INTERVAL '1 day'
            )::date as jour
        ),
        movements AS (
            SELECT
                DATE_TRUNC('day', date_mvt)::date as jour,
                SUM(CASE WHEN type = 'ENTREE' THEN quantite ELSE 0 END) as entrees,
                SUM(CASE WHEN type = 'SORTIE' THEN quantite ELSE 0 END) as sorties
            FROM mouvements_stock
            WHERE tenant_id = :tenant_id
              AND date_mvt >= NOW() - INTERVAL '7 days'
            GROUP BY 1
        )
        SELECT
            TO_CHAR(d.jour, 'Dy') as jour_label,
            d.jour,
            COALESCE(m.entrees, 0) as entrees,
            COALESCE(m.sorties, 0) as sorties,
            COALESCE(m.entrees, 0) - COALESCE(m.sorties, 0) as solde
        FROM days d
        LEFT JOIN movements m ON m.jour = d.jour
        ORDER BY d.jour
    """
    df = query_df(sql, params={"tenant_id": tenant_id})
    return df.to_dict("records")


def fetch_margin_alerts(
    *,
    tenant_id: int = 1,
    threshold: float = 20.0,
    limit: int = 20
) -> list[dict]:
    """
    Récupère les produits avec marge inférieure au seuil.

    Args:
        tenant_id: ID du tenant
        threshold: Seuil de marge en %
        limit: Nombre max de résultats

    Returns:
        Liste de dicts avec id, nom, margin, prix_achat, prix_vente
    """
    sql = """
        SELECT
            id,
            nom,
            prix_achat_ht,
            prix_vente_ttc,
            CASE WHEN prix_vente_ttc > 0
                THEN (prix_vente_ttc - prix_achat_ht) / prix_vente_ttc * 100
                ELSE 0
            END as margin
        FROM produits
        WHERE tenant_id = :tenant_id
          AND actif = true
          AND prix_vente_ttc > 0
          AND prix_achat_ht > 0
          AND (prix_vente_ttc - prix_achat_ht) / prix_vente_ttc * 100 < :threshold
        ORDER BY margin ASC
        LIMIT :limit
    """
    df = query_df(sql, params={
        "tenant_id": tenant_id,
        "threshold": threshold,
        "limit": limit
    })
    return df.to_dict("records")


def fetch_category_stock(*, tenant_id: int = 1) -> list[dict]:
    """
    Récupère la répartition du stock par catégorie.

    Returns:
        Liste de dicts avec category, value, count, percentage
    """
    sql = """
        WITH totals AS (
            SELECT COALESCE(SUM(stock_actuel * prix_achat_ht), 0) as total
            FROM produits
            WHERE tenant_id = :tenant_id AND actif = true
        )
        SELECT
            COALESCE(c.nom, 'Non catégorisé') as category,
            COALESCE(SUM(p.stock_actuel * p.prix_achat_ht), 0) as value,
            COUNT(p.id) as count,
            CASE WHEN t.total > 0
                THEN ROUND(SUM(p.stock_actuel * p.prix_achat_ht) / t.total * 100, 1)
                ELSE 0
            END as percentage
        FROM produits p
        LEFT JOIN categories c ON c.id = p.category_id
        CROSS JOIN totals t
        WHERE p.tenant_id = :tenant_id
          AND p.actif = true
        GROUP BY c.nom, t.total
        ORDER BY value DESC
    """
    df = query_df(sql, params={"tenant_id": tenant_id})
    return df.to_dict("records")


def fetch_dashboard_metrics(
    *,
    tenant_id: int = 1,
    period: int = 30
) -> dict[str, Any]:
    """
    Agrège toutes les métriques dashboard en un seul appel.

    Cette fonction optimise les accès en base en combinant
    plusieurs requêtes en une seule structure de retour.

    Args:
        tenant_id: ID du tenant
        period: Période d'analyse en jours

    Returns:
        dict complet avec toutes les métriques dashboard
    """
    kpis = fetch_kpis(tenant_id=tenant_id)
    top_stock = fetch_top_stock_value(tenant_id=tenant_id, limit=5)
    top_sales = fetch_top_sales(tenant_id=tenant_id, days=period, limit=10)
    weekly = fetch_weekly_variation(tenant_id=tenant_id)
    margins = fetch_margin_alerts(tenant_id=tenant_id, limit=10)
    categories = fetch_category_stock(tenant_id=tenant_id)

    return {
        **kpis,
        "top_stock_value": top_stock,
        "top_sales": top_sales,
        "weekly_flows": weekly,
        "margin_alerts": margins,
        "category_stock": categories,
        "period": period,
        "generated_at": datetime.now().isoformat(),
    }


__all__ = [
    "fetch_kpis",
    "fetch_top_stock_value",
    "fetch_top_sales",
    "fetch_weekly_variation",
    "fetch_margin_alerts",
    "fetch_category_stock",
    "fetch_dashboard_metrics",
]
```

---

## 12.4 API Endpoint Dashboard

**Fichier**: `backend/api/dashboard.py`

```python
from fastapi import APIRouter, Depends, Query

from backend.services import dashboard as dashboard_service
from backend.dependencies.tenant import Tenant, get_current_tenant

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics")
def get_dashboard_metrics(
    period: int = Query(default=30, ge=1, le=365),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Récupère toutes les métriques agrégées du dashboard.

    Args:
        period: Période d'analyse en jours (1-365)

    Returns:
        Dict avec KPIs, top ventes, alertes, graphiques
    """
    return dashboard_service.fetch_dashboard_metrics(
        tenant_id=tenant.id,
        period=period,
    )


@router.get("/alerts")
def get_dashboard_alerts(
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Récupère les alertes actives pour le dashboard.

    Returns:
        Liste d'alertes avec niveau, message, action
    """
    kpis = dashboard_service.fetch_kpis(tenant_id=tenant.id)
    margins = dashboard_service.fetch_margin_alerts(tenant_id=tenant.id, limit=5)

    alerts = []

    # Alertes rupture stock
    if kpis["out_of_stock_count"] > 0:
        alerts.append({
            "level": "critical",
            "type": "out_of_stock",
            "message": f"{kpis['out_of_stock_count']} produit(s) en rupture",
            "action": "/operations/stock?filter=rupture",
        })

    # Alertes stock bas
    if kpis["low_stock_count"] > 5:
        alerts.append({
            "level": "warning",
            "type": "low_stock",
            "message": f"{kpis['low_stock_count']} produit(s) en stock bas",
            "action": "/operations/stock?filter=bas",
        })

    # Alertes marge
    if len(margins) > 3:
        alerts.append({
            "level": "warning",
            "type": "margin",
            "message": f"{len(margins)} produit(s) avec marge < 20%",
            "action": "/operations/prix",
        })

    return alerts


@router.get("/stock/summary")
def get_stock_summary(
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Résumé rapide du stock pour widgets.
    """
    return dashboard_service.fetch_kpis(tenant_id=tenant.id)
```

---

## 12.5 CockpitPage - Vue Décisionnelle

**Fichier**: `frontend/src/features/cockpit/CockpitPage.jsx`

Le Cockpit est une vue avancée avec des analyses plus poussées que le Dashboard classique.

### Différences Dashboard vs Cockpit

| Aspect | Dashboard | Cockpit |
|--------|-----------|---------|
| Public | Tous utilisateurs | Managers/Admin |
| Complexité | KPIs simples | Analyses croisées |
| Période | Jour/Semaine | Mois/Trimestre/Année |
| Actions | Navigation rapide | Décisions stratégiques |
| Refresh | 5 minutes | 15 minutes |

### Composants Cockpit

```javascript
import CockpitPeriodSelector from './components/CockpitPeriodSelector.jsx';
import CockpitMarginAnalysis from './components/CockpitMarginAnalysis.jsx';
import CockpitSupplierComparison from './components/CockpitSupplierComparison.jsx';
import CockpitSeasonality from './components/CockpitSeasonality.jsx';
import CockpitPredictions from './components/CockpitPredictions.jsx';
```

### Hook useCockpit

```javascript
export function useCockpitMetrics(period = '30d') {
  return useQuery({
    queryKey: ['cockpit', 'metrics', period],
    queryFn: () => fetchCockpitMetrics(period),
    staleTime: 15 * 60 * 1000, // 15 minutes
  });
}

export function useCockpitTrends(category = null) {
  return useQuery({
    queryKey: ['cockpit', 'trends', category],
    queryFn: () => fetchCockpitTrends(category),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
}
```

---

## 12.6 Cascade Complète Dashboard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUX DASHBOARD COMPLET                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [1] FRONTEND - DashboardPage.jsx                                           │
│      │                                                                       │
│      ├──► useDashboardMetrics()                                             │
│      │    └──► fetchDashboardMetrics() ─────────────────────────┐           │
│      │                                                           │           │
│      ├──► useProducts({ low_stock: true })                       │           │
│      │    └──► fetchProducts() ─────────────────────────────┐   │           │
│      │                                                       │   │           │
│  [2] API CLIENT - client.js                                  │   │           │
│      │                                                       │   │           │
│      ├──► apiFetch('/dashboard/metrics?period=30')   ◄───────┘   │           │
│      │                                                           │           │
│      ├──► apiFetch('/catalog/products?low_stock=true') ◄────────┘           │
│      │                                                                       │
│  [3] BACKEND API - dashboard.py / catalog.py                                │
│      │                                                                       │
│      ├──► get_dashboard_metrics()                                           │
│      │    └──► dashboard_service.fetch_dashboard_metrics()                  │
│      │                                                                       │
│      ├──► list_products()                                                   │
│      │    └──► catalog_service.list_products_page()                         │
│      │                                                                       │
│  [4] SERVICES - services/dashboard.py                                       │
│      │                                                                       │
│      ├──► fetch_kpis()                                                      │
│      │    └──► SELECT COUNT(*), SUM(stock * prix)... FROM produits          │
│      │                                                                       │
│      ├──► fetch_top_sales()                                                 │
│      │    └──► SELECT p.*, SUM(m.quantite) FROM produits p                  │
│      │         JOIN mouvements_stock m...                                   │
│      │                                                                       │
│      ├──► fetch_weekly_variation()                                          │
│      │    └──► WITH days AS (generate_series...)                            │
│      │         SELECT jour, SUM(entrees), SUM(sorties)...                   │
│      │                                                                       │
│      ├──► fetch_margin_alerts()                                             │
│      │    └──► SELECT * WHERE margin < :threshold                           │
│      │                                                                       │
│  [5] CORE - data_repository.py                                              │
│      │                                                                       │
│      └──► query_df(sql, params)                                             │
│           └──► pd.read_sql(text(sql), engine, params=params)                │
│                                                                              │
│  [6] DATABASE                                                                │
│      │                                                                       │
│      ├──► produits (stock, prix, catégorie)                                 │
│      ├──► mouvements_stock (entrées, sorties, dates)                        │
│      ├──► categories (regroupement)                                         │
│      └──► (calculs agrégés dans les requêtes)                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# PARTIE 13: Backend Services - Documentation Exhaustive

## 13.1 Architecture Services Backend

### Organisation des Services

```
backend/services/
├── __init__.py           # Exports centralisés
├── catalog.py            # CRUD produits, catégories
├── stock.py              # Mouvements, ajustements
├── prices.py             # Historique prix, comparaisons
├── dashboard.py          # Agrégations métriques
├── invoices.py           # Import factures, OCR
├── supply.py             # Plan approvisionnement
├── margins.py            # Calcul marges
├── reports.py            # Génération rapports
├── supplier_scoring.py   # Notation fournisseurs
├── finance/              # Sous-module finance
│   ├── __init__.py
│   ├── accounts.py       # Comptes comptables
│   ├── transactions.py   # Écritures
│   ├── stats.py          # Statistiques
│   └── views.py          # Vues agrégées
└── restaurant/           # Sous-module restaurant
    ├── __init__.py
    ├── plats.py          # Gestion plats
    ├── ingredients.py    # Ingrédients
    ├── costs.py          # Calcul food cost
    └── stock.py          # Stock restaurant
```

---

## 13.2 Service Catalog (catalog.py)

**Fichier**: `backend/services/catalog.py`

### Exception Personnalisée

```python
class ProductNotFound(Exception):
    """Levée quand un produit n'existe pas."""
    pass
```

### Fonctions CRUD

#### list_products_page

```python
def list_products_page(
    tenant_id: int,
    search: str | None = None,
    category: str | None = None,
    status: str | None = None,
    fournisseur: str | None = None,
    supplier_id: int | None = None,
    page: int = 1,
    per_page: int = 25,
) -> tuple[list[dict], int]:
    """
    Liste les produits avec pagination et filtres.

    Args:
        tenant_id: ID du tenant
        search: Recherche textuelle (nom, SKU, EAN)
        category: Filtrer par nom catégorie
        status: 'active', 'inactive', 'low_stock', 'out_of_stock'
        fournisseur: Nom fournisseur (recherche partielle)
        supplier_id: ID exact du fournisseur
        page: Numéro de page (1-based)
        per_page: Éléments par page (max 100)

    Returns:
        Tuple (liste_produits, total_count)
    """
    # Construction dynamique de la requête
    conditions = ["p.tenant_id = :tenant_id"]
    params = {"tenant_id": tenant_id}

    if search:
        conditions.append("""
            (p.nom ILIKE :search
             OR p.sku ILIKE :search
             OR EXISTS (
                SELECT 1 FROM produits_barcodes pb
                WHERE pb.produit_id = p.id AND pb.code ILIKE :search
             ))
        """)
        params["search"] = f"%{search}%"

    if category:
        conditions.append("c.nom = :category")
        params["category"] = category

    if status == "low_stock":
        conditions.append("p.stock_actuel > 0 AND p.stock_actuel <= COALESCE(p.stock_min, 5)")
    elif status == "out_of_stock":
        conditions.append("p.stock_actuel <= 0")
    elif status == "active":
        conditions.append("p.actif = true")
    elif status == "inactive":
        conditions.append("p.actif = false")

    if fournisseur:
        conditions.append("p.fournisseur ILIKE :fournisseur")
        params["fournisseur"] = f"%{fournisseur}%"

    if supplier_id:
        conditions.append("p.fournisseur_id = :supplier_id")
        params["supplier_id"] = supplier_id

    where_clause = " AND ".join(conditions)

    # Requête count
    count_sql = f"""
        SELECT COUNT(*)
        FROM produits p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE {where_clause}
    """

    # Requête données
    data_sql = f"""
        SELECT
            p.id,
            p.nom,
            p.sku,
            p.stock_actuel,
            p.stock_min,
            p.prix_achat_ht,
            p.prix_vente_ttc,
            p.fournisseur,
            p.fournisseur_id,
            c.nom as category_name,
            p.unite,
            p.actif,
            p.created_at,
            p.updated_at,
            CASE
                WHEN p.prix_vente_ttc > 0 AND p.prix_achat_ht > 0
                THEN ROUND((p.prix_vente_ttc - p.prix_achat_ht) / p.prix_vente_ttc * 100, 1)
                ELSE 0
            END as margin_percent
        FROM produits p
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE {where_clause}
        ORDER BY p.nom ASC
        LIMIT :limit OFFSET :offset
    """

    params["limit"] = per_page
    params["offset"] = (page - 1) * per_page

    with get_engine().connect() as conn:
        total = conn.execute(text(count_sql), params).scalar() or 0
        rows = conn.execute(text(data_sql), params).fetchall()

    items = [dict(row._mapping) for row in rows]
    return items, total
```

#### get_product

```python
def get_product(product_id: int, *, tenant_id: int) -> dict:
    """
    Récupère un produit par son ID.

    Raises:
        ProductNotFound: Si le produit n'existe pas
    """
    sql = """
        SELECT
            p.*,
            c.nom as category_name,
            ARRAY_AGG(pb.code) FILTER (WHERE pb.code IS NOT NULL) as barcodes
        FROM produits p
        LEFT JOIN categories c ON c.id = p.category_id
        LEFT JOIN produits_barcodes pb ON pb.produit_id = p.id
        WHERE p.id = :pid AND p.tenant_id = :tenant_id
        GROUP BY p.id, c.nom
    """

    with get_engine().connect() as conn:
        row = conn.execute(text(sql), {"pid": product_id, "tenant_id": tenant_id}).fetchone()

    if not row:
        raise ProductNotFound(f"Produit {product_id} non trouvé")

    return dict(row._mapping)
```

#### get_product_detail

```python
def get_product_detail(product_id: int, *, tenant_id: int) -> dict:
    """
    Récupère un produit avec toutes ses métriques enrichies.

    Returns:
        dict avec:
        - Données de base du produit
        - sales_30d: Ventes 30 derniers jours
        - sales_7d: Ventes 7 derniers jours
        - sales_trend: Variation % vs période précédente
        - rotation_days: Jours de stock estimés
        - coverage_days: Couverture stock actuelle
        - last_purchase: Dernier achat (date, source, qty)
        - price_history: 10 derniers changements de prix
        - recent_movements: 10 derniers mouvements
        - stock_max_estimated: Stock max observé
    """
    # Données de base
    product = get_product(product_id, tenant_id=tenant_id)

    # Ventes 30j
    sales_30d = query_df("""
        SELECT COALESCE(SUM(ABS(quantite)), 0) as total
        FROM mouvements_stock
        WHERE produit_id = :pid
          AND tenant_id = :tenant_id
          AND type = 'SORTIE'
          AND date_mvt >= NOW() - INTERVAL '30 days'
    """, params={"pid": product_id, "tenant_id": tenant_id}).iloc[0]["total"]

    # Ventes 7j
    sales_7d = query_df("""
        SELECT COALESCE(SUM(ABS(quantite)), 0) as total
        FROM mouvements_stock
        WHERE produit_id = :pid
          AND tenant_id = :tenant_id
          AND type = 'SORTIE'
          AND date_mvt >= NOW() - INTERVAL '7 days'
    """, params={"pid": product_id, "tenant_id": tenant_id}).iloc[0]["total"]

    # Trend ventes (30j actuels vs 30j précédents)
    prev_sales = query_df("""
        SELECT COALESCE(SUM(ABS(quantite)), 0) as total
        FROM mouvements_stock
        WHERE produit_id = :pid
          AND tenant_id = :tenant_id
          AND type = 'SORTIE'
          AND date_mvt >= NOW() - INTERVAL '60 days'
          AND date_mvt < NOW() - INTERVAL '30 days'
    """, params={"pid": product_id, "tenant_id": tenant_id}).iloc[0]["total"]

    sales_trend = 0
    if prev_sales > 0:
        sales_trend = round((sales_30d - prev_sales) / prev_sales * 100, 1)

    # Rotation et couverture
    daily_sales = sales_30d / 30 if sales_30d > 0 else 0
    stock_actuel = product.get("stock_actuel", 0) or 0
    coverage_days = int(stock_actuel / daily_sales) if daily_sales > 0 else 999

    # Dernier achat
    last_purchase = query_df("""
        SELECT date_mvt, source, quantite
        FROM mouvements_stock
        WHERE produit_id = :pid
          AND tenant_id = :tenant_id
          AND type = 'ENTREE'
        ORDER BY date_mvt DESC
        LIMIT 1
    """, params={"pid": product_id, "tenant_id": tenant_id})

    # Historique prix
    price_history = query_df("""
        SELECT prix_achat, created_at
        FROM produits_price_history
        WHERE produit_id = :pid AND tenant_id = :tenant_id
        ORDER BY created_at DESC
        LIMIT 10
    """, params={"pid": product_id, "tenant_id": tenant_id})

    # Mouvements récents
    recent_movements = query_df("""
        SELECT id, date_mvt, type, quantite, source
        FROM mouvements_stock
        WHERE produit_id = :pid AND tenant_id = :tenant_id
        ORDER BY date_mvt DESC
        LIMIT 10
    """, params={"pid": product_id, "tenant_id": tenant_id})

    return {
        **product,
        "sales_30d": float(sales_30d),
        "sales_7d": float(sales_7d),
        "sales_trend": sales_trend,
        "daily_average": round(daily_sales, 2),
        "coverage_days": coverage_days,
        "last_purchase": last_purchase.to_dict("records")[0] if not last_purchase.empty else None,
        "price_history": price_history.to_dict("records"),
        "recent_movements": recent_movements.to_dict("records"),
    }
```

#### create_product

```python
def create_product(
    data: dict,
    *,
    tenant_id: int,
    codes: list[str] | None = None,
) -> dict:
    """
    Crée un nouveau produit.

    Args:
        data: Données du produit (nom, prix, etc.)
        tenant_id: ID du tenant
        codes: Liste optionnelle de codes-barres

    Returns:
        Produit créé avec son ID
    """
    engine = get_engine()

    with engine.begin() as conn:
        # Vérifier unicité SKU si fourni
        if data.get("sku"):
            existing = conn.execute(
                text("SELECT id FROM produits WHERE sku = :sku AND tenant_id = :tid"),
                {"sku": data["sku"], "tid": tenant_id}
            ).fetchone()
            if existing:
                raise ValueError(f"SKU {data['sku']} déjà utilisé")

        # Insertion produit
        columns = list(data.keys()) + ["tenant_id"]
        values_placeholders = ", ".join(f":{k}" for k in columns)

        sql = f"""
            INSERT INTO produits ({", ".join(columns)})
            VALUES ({values_placeholders})
            RETURNING *
        """

        params = {**data, "tenant_id": tenant_id}
        row = conn.execute(text(sql), params).fetchone()
        product = dict(row._mapping)

        # Insertion codes-barres
        if codes:
            for code in codes:
                conn.execute(
                    text("""
                        INSERT INTO produits_barcodes (produit_id, code, tenant_id)
                        VALUES (:pid, :code, :tid)
                        ON CONFLICT (code, tenant_id) DO NOTHING
                    """),
                    {"pid": product["id"], "code": code, "tid": tenant_id}
                )

    return product
```

#### update_product

```python
def update_product(
    product_id: int,
    data: dict,
    *,
    codes: list[str] | None = None,
    tenant_id: int,
) -> dict:
    """
    Met à jour un produit existant.

    - Enregistre l'historique de prix si prix_achat change
    - Met à jour les codes-barres si fournis
    """
    engine = get_engine()

    with engine.begin() as conn:
        # Vérifier existence
        current = conn.execute(
            text("SELECT * FROM produits WHERE id = :pid AND tenant_id = :tid FOR UPDATE"),
            {"pid": product_id, "tid": tenant_id}
        ).fetchone()

        if not current:
            raise ProductNotFound(f"Produit {product_id} non trouvé")

        current_dict = dict(current._mapping)

        # Historique prix si changement
        if "prix_achat_ht" in data and data["prix_achat_ht"] != current_dict.get("prix_achat_ht"):
            conn.execute(
                text("""
                    INSERT INTO produits_price_history (produit_id, prix_achat, tenant_id)
                    VALUES (:pid, :prix, :tid)
                """),
                {"pid": product_id, "prix": current_dict.get("prix_achat_ht"), "tid": tenant_id}
            )

        # Construction UPDATE dynamique
        if data:
            set_clauses = ", ".join(f"{k} = :{k}" for k in data.keys())
            sql = f"UPDATE produits SET {set_clauses}, updated_at = NOW() WHERE id = :pid AND tenant_id = :tid RETURNING *"
            params = {**data, "pid": product_id, "tid": tenant_id}
            row = conn.execute(text(sql), params).fetchone()
        else:
            row = current

        # Mise à jour codes-barres
        if codes is not None:
            # Supprimer anciens codes
            conn.execute(
                text("DELETE FROM produits_barcodes WHERE produit_id = :pid AND tenant_id = :tid"),
                {"pid": product_id, "tid": tenant_id}
            )
            # Ajouter nouveaux
            for code in codes:
                conn.execute(
                    text("""
                        INSERT INTO produits_barcodes (produit_id, code, tenant_id)
                        VALUES (:pid, :code, :tid)
                    """),
                    {"pid": product_id, "code": code, "tid": tenant_id}
                )

    return dict(row._mapping)
```

#### delete_product

```python
def delete_product(product_id: int, *, tenant_id: int) -> None:
    """
    Supprime un produit (soft delete via actif=false ou hard delete).

    La suppression hard n'est possible que si:
    - Aucun mouvement de stock n'existe
    - Aucune ligne de facture ne référence le produit
    """
    engine = get_engine()

    with engine.begin() as conn:
        # Vérifier existence
        exists = conn.execute(
            text("SELECT 1 FROM produits WHERE id = :pid AND tenant_id = :tid"),
            {"pid": product_id, "tid": tenant_id}
        ).fetchone()

        if not exists:
            raise ProductNotFound(f"Produit {product_id} non trouvé")

        # Vérifier si des mouvements existent
        has_movements = conn.execute(
            text("SELECT 1 FROM mouvements_stock WHERE produit_id = :pid LIMIT 1"),
            {"pid": product_id}
        ).fetchone()

        if has_movements:
            # Soft delete
            conn.execute(
                text("UPDATE produits SET actif = false, updated_at = NOW() WHERE id = :pid AND tenant_id = :tid"),
                {"pid": product_id, "tid": tenant_id}
            )
        else:
            # Hard delete
            conn.execute(
                text("DELETE FROM produits_barcodes WHERE produit_id = :pid"),
                {"pid": product_id}
            )
            conn.execute(
                text("DELETE FROM produits WHERE id = :pid AND tenant_id = :tid"),
                {"pid": product_id, "tid": tenant_id}
            )
```

---

## 13.3 Service Stock (stock.py)

**Fichier**: `backend/services/stock.py` (172 lignes)

### fetch_movement_timeseries

```python
def fetch_movement_timeseries(
    window_days: int = 30,
    product_id: Optional[int] = None,
    *,
    tenant_id: int = 1,
) -> pd.DataFrame:
    """
    Récupère les mouvements de stock groupés par jour.

    La fenêtre est calculée à partir de la date du DERNIER mouvement,
    pas de la date actuelle, pour éviter les périodes vides en fin de graphique.

    Returns:
        DataFrame avec colonnes: jour, type, quantite
    """
    sql = """
        WITH latest AS (
            SELECT COALESCE(MAX(date_mvt), now()) AS max_date
            FROM mouvements_stock
            WHERE tenant_id = :tenant_id
        )
        SELECT
            date_trunc('day', m.date_mvt) AS jour,
            m.type,
            SUM(m.quantite) AS quantite
        FROM mouvements_stock m, latest
        WHERE m.date_mvt >= latest.max_date - make_interval(days => :window)
          AND m.tenant_id = :tenant_id
    """
    params = {"window": int(max(1, window_days)), "tenant_id": int(tenant_id)}

    if product_id is not None:
        sql += " AND m.produit_id = :pid"
        params["pid"] = int(product_id)

    sql += " GROUP BY 1, m.type ORDER BY jour ASC, m.type"

    df = query_df(sql, params=params)
    if not df.empty:
        df["jour"] = pd.to_datetime(df["jour"]).dt.date
    return df
```

### adjust_stock_level

```python
def adjust_stock_level(
    product_id: int,
    target_quantity: float,
    *,
    username: str | None = None,
    tenant_id: int = 1,
) -> dict[str, object]:
    """
    Ajuste le niveau de stock d'un produit vers une quantité cible.

    Process:
    1. SELECT FOR UPDATE pour verrouiller le produit
    2. Calcule le delta (target - current)
    3. Crée un mouvement ENTREE ou SORTIE
    4. Le trigger PostgreSQL met à jour stock_actuel
    5. Émet un événement de correction stock

    Returns:
        dict avec product_id, product_name, current_stock, new_stock,
        movement_created, movement_type, movement_quantity
    """
    engine = get_engine()

    with engine.begin() as conn:
        # Verrouillage pessimiste
        row = conn.execute(
            text(
                "SELECT nom, COALESCE(stock_actuel, 0) AS stock_actuel "
                "FROM produits WHERE id = :pid AND tenant_id = :tenant_id FOR UPDATE"
            ),
            {"pid": product_id, "tenant_id": int(tenant_id)},
        ).fetchone()

        if row is None:
            raise ValueError(f"Produit {product_id} introuvable.")

        current_stock = float(row.stock_actuel or 0.0)
        delta = float(target_quantity) - current_stock

        # Pas de changement si delta négligeable
        if abs(delta) < 1e-6:
            return {
                "product_id": product_id,
                "product_name": row.nom,
                "current_stock": current_stock,
                "new_stock": current_stock,
                "movement_created": False,
            }

        movement_type = "ENTREE" if delta > 0 else "SORTIE"

        # Création du mouvement
        conn.execute(
            text("""
                INSERT INTO mouvements_stock (produit_id, type, quantite, source, tenant_id)
                VALUES (:pid, :type, :quantite, :source, :tenant_id)
            """),
            {
                "pid": product_id,
                "type": movement_type,
                "quantite": abs(delta),
                "source": f"Ajustement API ({username or 'inconnu'})",
                "tenant_id": int(tenant_id),
            },
        )

    # Récupérer nouvelle valeur (mise à jour par trigger)
    with engine.connect() as conn:
        new_row = conn.execute(
            text("SELECT COALESCE(stock_actuel, 0) FROM produits WHERE id = :pid"),
            {"pid": product_id},
        ).fetchone()
        new_stock = float(new_row[0] if new_row else target_quantity)

    # Émettre événement de correction
    try:
        emit_stock_correction(
            tenant_id=tenant_id,
            product_id=product_id,
            old_quantity=current_stock,
            new_quantity=new_stock,
            reason=f"Ajustement manuel par {username or 'système'}",
        )
    except Exception as e:
        print(f"Warning: Failed to emit stock correction event: {e}")

    return {
        "product_id": product_id,
        "product_name": row.nom,
        "current_stock": current_stock,
        "new_stock": new_stock,
        "movement_created": True,
        "movement_type": movement_type,
        "movement_quantity": abs(delta),
    }
```

---

## 13.4 Service Prices (prices.py)

**Fichier**: `backend/services/prices.py`

### fetch_price_history

```python
def fetch_price_history(
    *,
    tenant_id: int = 1,
    product_id: int | None = None,
    category_id: int | None = None,
    days: int = 90,
) -> pd.DataFrame:
    """
    Récupère l'historique des prix d'achat.

    Returns:
        DataFrame avec produit_id, produit_nom, prix_achat, date, variation_pct
    """
    sql = """
        SELECT
            ph.produit_id,
            p.nom as produit_nom,
            ph.prix_achat,
            ph.created_at as date,
            LAG(ph.prix_achat) OVER (
                PARTITION BY ph.produit_id
                ORDER BY ph.created_at
            ) as prix_precedent
        FROM produits_price_history ph
        JOIN produits p ON p.id = ph.produit_id
        WHERE ph.tenant_id = :tenant_id
          AND ph.created_at >= NOW() - INTERVAL ':days days'
    """
    params = {"tenant_id": tenant_id, "days": days}

    if product_id:
        sql += " AND ph.produit_id = :product_id"
        params["product_id"] = product_id

    if category_id:
        sql += " AND p.category_id = :category_id"
        params["category_id"] = category_id

    sql += " ORDER BY ph.created_at DESC"

    df = query_df(sql, params=params)

    if not df.empty:
        df["variation_pct"] = (
            (df["prix_achat"] - df["prix_precedent"]) / df["prix_precedent"] * 100
        ).round(2)

    return df
```

### compare_supplier_prices

```python
def compare_supplier_prices(
    product_ids: list[int],
    *,
    tenant_id: int = 1,
) -> list[dict]:
    """
    Compare les prix d'un produit entre différents fournisseurs.

    Utile pour l'optimisation des achats.
    """
    if not product_ids:
        return []

    sql = """
        SELECT
            p.id as product_id,
            p.nom as product_name,
            p.fournisseur as current_supplier,
            p.prix_achat_ht as current_price,
            va.fournisseur as alternative_supplier,
            va.prix_achat_ht as alternative_price,
            (p.prix_achat_ht - va.prix_achat_ht) as savings
        FROM produits p
        CROSS JOIN LATERAL (
            SELECT DISTINCT ON (fournisseur)
                fournisseur,
                prix_achat_ht
            FROM produits_price_history
            WHERE produit_id = p.id
            ORDER BY fournisseur, created_at DESC
        ) va
        WHERE p.id = ANY(:pids)
          AND p.tenant_id = :tenant_id
          AND va.fournisseur != p.fournisseur
          AND va.prix_achat_ht < p.prix_achat_ht
        ORDER BY savings DESC
    """

    df = query_df(sql, params={"pids": product_ids, "tenant_id": tenant_id})
    return df.to_dict("records")
```

---

## 13.5 Service Supply (supply.py)

**Fichier**: `backend/services/supply.py`

### compute_supply_plan

```python
def compute_supply_plan(
    *,
    tenant_id: int = 1,
    target_coverage: int = 14,
    only_critical: bool = False,
) -> list[dict]:
    """
    Calcule un plan d'approvisionnement basé sur:
    - Stock actuel
    - Consommation moyenne (30 derniers jours)
    - Couverture cible en jours
    - Stock minimum défini

    Args:
        tenant_id: ID du tenant
        target_coverage: Jours de stock cible
        only_critical: Ne retourner que les produits critiques (< 7j)

    Returns:
        Liste de dicts avec:
        - product_id, product_name
        - current_stock, daily_consumption
        - days_remaining, quantity_to_order
        - urgency_level (critical, warning, ok)
        - supplier, estimated_cost
    """
    sql = """
        WITH consumption AS (
            SELECT
                produit_id,
                COALESCE(SUM(ABS(quantite)) / 30.0, 0) as daily_avg
            FROM mouvements_stock
            WHERE tenant_id = :tenant_id
              AND type = 'SORTIE'
              AND date_mvt >= NOW() - INTERVAL '30 days'
            GROUP BY produit_id
        )
        SELECT
            p.id as product_id,
            p.nom as product_name,
            p.stock_actuel as current_stock,
            p.stock_min,
            p.prix_achat_ht,
            p.fournisseur as supplier,
            COALESCE(c.daily_avg, 0) as daily_consumption,
            CASE
                WHEN COALESCE(c.daily_avg, 0) > 0
                THEN FLOOR(p.stock_actuel / c.daily_avg)
                ELSE 999
            END as days_remaining
        FROM produits p
        LEFT JOIN consumption c ON c.produit_id = p.id
        WHERE p.tenant_id = :tenant_id
          AND p.actif = true
    """

    if only_critical:
        sql += " AND (p.stock_actuel / NULLIF(c.daily_avg, 0)) < 7"

    sql += " ORDER BY days_remaining ASC, p.stock_actuel ASC"

    df = query_df(sql, params={"tenant_id": tenant_id})

    results = []
    for _, row in df.iterrows():
        days = row["days_remaining"]
        daily = row["daily_consumption"]

        # Calculer quantité à commander
        if daily > 0:
            target_stock = daily * target_coverage
            qty_to_order = max(0, target_stock - row["current_stock"])
        else:
            qty_to_order = max(0, (row["stock_min"] or 10) - row["current_stock"])

        # Niveau d'urgence
        if days < 3:
            urgency = "critical"
        elif days < 7:
            urgency = "warning"
        else:
            urgency = "ok"

        results.append({
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "current_stock": float(row["current_stock"]),
            "daily_consumption": round(float(daily), 2),
            "days_remaining": int(days) if days < 999 else None,
            "quantity_to_order": round(float(qty_to_order), 1),
            "urgency_level": urgency,
            "supplier": row["supplier"],
            "estimated_cost": round(float(qty_to_order * row["prix_achat_ht"]), 2) if row["prix_achat_ht"] else None,
        })

    return results
```

### generate_supplier_order

```python
def generate_supplier_order(
    supplier: str,
    items: list[dict],
    *,
    tenant_id: int = 1,
) -> dict:
    """
    Génère un bon de commande fournisseur.

    Args:
        supplier: Nom du fournisseur
        items: Liste de {product_id, quantity}

    Returns:
        dict avec order_id, supplier, items, total, pdf_url
    """
    engine = get_engine()

    with engine.begin() as conn:
        # Créer l'en-tête de commande
        order = conn.execute(
            text("""
                INSERT INTO supplier_orders (supplier, status, tenant_id)
                VALUES (:supplier, 'draft', :tenant_id)
                RETURNING id, created_at
            """),
            {"supplier": supplier, "tenant_id": tenant_id}
        ).fetchone()

        order_id = order.id
        total = Decimal("0")
        order_items = []

        for item in items:
            # Récupérer infos produit
            product = conn.execute(
                text("SELECT nom, prix_achat_ht, unite FROM produits WHERE id = :pid"),
                {"pid": item["product_id"]}
            ).fetchone()

            if not product:
                continue

            line_total = Decimal(str(item["quantity"])) * (product.prix_achat_ht or Decimal("0"))
            total += line_total

            # Insérer ligne
            conn.execute(
                text("""
                    INSERT INTO supplier_order_lines
                    (order_id, product_id, quantity, unit_price, line_total)
                    VALUES (:oid, :pid, :qty, :price, :total)
                """),
                {
                    "oid": order_id,
                    "pid": item["product_id"],
                    "qty": item["quantity"],
                    "price": product.prix_achat_ht,
                    "total": line_total,
                }
            )

            order_items.append({
                "product_id": item["product_id"],
                "product_name": product.nom,
                "quantity": item["quantity"],
                "unit": product.unite,
                "unit_price": float(product.prix_achat_ht or 0),
                "line_total": float(line_total),
            })

        # Mettre à jour total
        conn.execute(
            text("UPDATE supplier_orders SET total = :total WHERE id = :oid"),
            {"total": total, "oid": order_id}
        )

    return {
        "order_id": order_id,
        "supplier": supplier,
        "items": order_items,
        "total": float(total),
        "status": "draft",
        "created_at": order.created_at.isoformat(),
    }
```

---

## 13.6 Service Invoices (invoices.py)

### Processus Zero-Click Import

```python
def process_invoice_upload(
    file_content: bytes,
    filename: str,
    *,
    tenant_id: int = 1,
    user_id: int | None = None,
) -> dict:
    """
    Traite une facture uploadée avec extraction automatique.

    Process:
    1. Détection format (PDF, image, Excel)
    2. OCR si nécessaire
    3. Extraction structurée des lignes
    4. Matching produits existants
    5. Création mouvements stock
    6. Mise à jour prix si écart détecté

    Returns:
        dict avec:
        - invoice_id
        - supplier (détecté)
        - date
        - lines: [{product_id, matched, quantity, price, confidence}]
        - auto_created_movements: int
        - price_updates: int
        - needs_review: bool
    """
    # Détection format
    ext = filename.lower().split(".")[-1]

    if ext == "pdf":
        text_content = extract_pdf_text(file_content)
        lines = parse_invoice_lines(text_content)
    elif ext in ("jpg", "jpeg", "png"):
        text_content = ocr_image(file_content)
        lines = parse_invoice_lines(text_content)
    elif ext in ("xlsx", "xls"):
        lines = parse_excel_invoice(file_content)
    else:
        raise ValueError(f"Format non supporté: {ext}")

    # Matching produits
    matched_lines = []
    for line in lines:
        match = find_product_match(
            line["description"],
            line.get("sku"),
            line.get("barcode"),
            tenant_id=tenant_id,
        )
        matched_lines.append({
            **line,
            "product_id": match["product_id"] if match else None,
            "match_confidence": match["confidence"] if match else 0,
            "match_method": match["method"] if match else None,
        })

    # Créer enregistrement facture
    engine = get_engine()
    with engine.begin() as conn:
        invoice = conn.execute(
            text("""
                INSERT INTO processed_invoices
                (filename, supplier, invoice_date, raw_content, tenant_id, user_id)
                VALUES (:filename, :supplier, :date, :content, :tenant_id, :user_id)
                RETURNING id
            """),
            {
                "filename": filename,
                "supplier": detect_supplier(text_content),
                "date": detect_invoice_date(text_content),
                "content": text_content[:10000],
                "tenant_id": tenant_id,
                "user_id": user_id,
            }
        ).fetchone()

        # Auto-créer mouvements pour les matchs haute confiance
        movements_created = 0
        price_updates = 0

        for line in matched_lines:
            if line["product_id"] and line["match_confidence"] >= 0.9:
                # Créer mouvement entrée
                conn.execute(
                    text("""
                        INSERT INTO mouvements_stock
                        (produit_id, type, quantite, source, tenant_id)
                        VALUES (:pid, 'ENTREE', :qty, :source, :tenant_id)
                    """),
                    {
                        "pid": line["product_id"],
                        "qty": line["quantity"],
                        "source": f"Facture {filename}",
                        "tenant_id": tenant_id,
                    }
                )
                movements_created += 1

                # Vérifier si prix différent
                if line.get("unit_price"):
                    current_price = conn.execute(
                        text("SELECT prix_achat_ht FROM produits WHERE id = :pid"),
                        {"pid": line["product_id"]}
                    ).scalar()

                    if current_price and abs(float(current_price) - line["unit_price"]) > 0.01:
                        # Mettre à jour prix
                        conn.execute(
                            text("""
                                UPDATE produits
                                SET prix_achat_ht = :prix, updated_at = NOW()
                                WHERE id = :pid
                            """),
                            {"prix": line["unit_price"], "pid": line["product_id"]}
                        )
                        price_updates += 1

    needs_review = any(
        line["match_confidence"] < 0.9 or line["product_id"] is None
        for line in matched_lines
    )

    return {
        "invoice_id": invoice.id,
        "supplier": detect_supplier(text_content),
        "date": detect_invoice_date(text_content),
        "lines": matched_lines,
        "total_lines": len(matched_lines),
        "auto_matched": sum(1 for l in matched_lines if l["product_id"]),
        "auto_created_movements": movements_created,
        "price_updates": price_updates,
        "needs_review": needs_review,
    }
```

---

## 13.7 Core Data Repository

**Fichier**: `core/data_repository.py`

### Engine Singleton

```python
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import pandas as pd
import os

_engine = None

def get_engine():
    """
    Retourne l'engine SQLAlchemy singleton.

    Configuration:
    - Pool de connexions avec QueuePool
    - Recyclage connexions après 30 min
    - Max 10 connexions simultanées
    """
    global _engine
    if _engine is None:
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/epicerie"
        )
        _engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_recycle=1800,
            echo=os.environ.get("SQL_ECHO", "false").lower() == "true",
        )
    return _engine


def query_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    """
    Exécute une requête et retourne un DataFrame pandas.

    Args:
        sql: Requête SQL (peut contenir des placeholders :name)
        params: Paramètres nommés

    Returns:
        pd.DataFrame avec les résultats
    """
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def execute_sql(sql: str, params: dict | None = None) -> int:
    """
    Exécute une requête de modification.

    Returns:
        Nombre de lignes affectées
    """
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text(sql), params or {})
        return result.rowcount
```

---

## 13.8 Event Sourcing (core/finance/event_sourcing.py)

### Émission d'Événements Stock

```python
from datetime import datetime
from typing import Any
import json

from core.data_repository import get_engine
from sqlalchemy import text


def emit_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    tenant_id: int,
    user_id: int | None = None,
) -> int:
    """
    Émet un événement dans le log d'événements.

    Les événements sont immutables et servent de source de vérité
    pour la reconstruction de l'état du système.

    Returns:
        ID de l'événement créé
    """
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO event_log
                (event_type, payload, tenant_id, user_id, created_at)
                VALUES (:type, :payload::jsonb, :tenant_id, :user_id, NOW())
                RETURNING id
            """),
            {
                "type": event_type,
                "payload": json.dumps(payload),
                "tenant_id": tenant_id,
                "user_id": user_id,
            }
        )
        return result.fetchone().id


def emit_stock_correction(
    *,
    tenant_id: int,
    product_id: int,
    old_quantity: float,
    new_quantity: float,
    reason: str,
) -> int:
    """
    Émet un événement de correction de stock.

    Ces événements sont utilisés pour:
    - Audit trail
    - Détection anomalies
    - Reconstruction historique
    """
    return emit_event(
        "stock.correction",
        {
            "product_id": product_id,
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
            "delta": new_quantity - old_quantity,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        },
        tenant_id=tenant_id,
    )


def emit_price_change(
    *,
    tenant_id: int,
    product_id: int,
    old_price: float,
    new_price: float,
    source: str,
) -> int:
    """
    Émet un événement de changement de prix.
    """
    return emit_event(
        "price.change",
        {
            "product_id": product_id,
            "old_price": old_price,
            "new_price": new_price,
            "change_percent": round((new_price - old_price) / old_price * 100, 2) if old_price else 0,
            "source": source,
            "timestamp": datetime.now().isoformat(),
        },
        tenant_id=tenant_id,
    )


def emit_invoice_processed(
    *,
    tenant_id: int,
    invoice_id: int,
    supplier: str,
    total: float,
    lines_count: int,
    auto_matched: int,
) -> int:
    """
    Émet un événement de facture traitée.
    """
    return emit_event(
        "invoice.processed",
        {
            "invoice_id": invoice_id,
            "supplier": supplier,
            "total": total,
            "lines_count": lines_count,
            "auto_matched": auto_matched,
            "match_rate": round(auto_matched / lines_count * 100, 1) if lines_count else 0,
            "timestamp": datetime.now().isoformat(),
        },
        tenant_id=tenant_id,
    )
```

---

## 13.9 Tables Base de Données Services

### Table event_log

```sql
CREATE TABLE event_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    tenant_id INT NOT NULL,
    user_id INT,
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_event_type (event_type),
    INDEX idx_tenant_created (tenant_id, created_at DESC),
    INDEX idx_payload_gin (payload) USING GIN
);
```

### Table processed_invoices

```sql
CREATE TABLE processed_invoices (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    supplier VARCHAR(255),
    invoice_date DATE,
    invoice_number VARCHAR(100),
    total_ht DECIMAL(12,2),
    total_ttc DECIMAL(12,2),
    raw_content TEXT,
    structured_data JSONB,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, validated, rejected
    tenant_id INT NOT NULL,
    user_id INT,
    created_at TIMESTAMP DEFAULT NOW(),
    validated_at TIMESTAMP,

    INDEX idx_tenant_status (tenant_id, status),
    INDEX idx_supplier (supplier),
    INDEX idx_invoice_date (invoice_date)
);
```

### Table supplier_orders

```sql
CREATE TABLE supplier_orders (
    id SERIAL PRIMARY KEY,
    supplier VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',  -- draft, sent, confirmed, received, cancelled
    total DECIMAL(12,2),
    notes TEXT,
    expected_delivery DATE,
    tenant_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP,
    received_at TIMESTAMP,

    INDEX idx_tenant_status (tenant_id, status),
    INDEX idx_supplier_date (supplier, created_at DESC)
);

CREATE TABLE supplier_order_lines (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES supplier_orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES produits(id),
    quantity DECIMAL(10,3) NOT NULL,
    unit_price DECIMAL(10,4),
    line_total DECIMAL(12,2),
    received_quantity DECIMAL(10,3),

    INDEX idx_order (order_id)
);
```

---

# PARTIE 14: Composants UI Réutilisables - Documentation Exhaustive

## 14.1 Vue d'Ensemble du Design System

**Répertoire**: `frontend/src/components/ui/`

### Inventaire Complet des Composants

```
components/ui/
├── Primitives (Base)
│   ├── Button.jsx           - Boutons avec variantes
│   ├── Input.jsx             - Champ de saisie
│   ├── Select.jsx            - Liste déroulante
│   ├── Checkbox.jsx          - Case à cocher
│   ├── Radio.jsx             - Bouton radio
│   ├── Toggle.jsx            - Interrupteur
│   ├── Textarea.jsx          - Zone de texte
│   └── Badge.jsx             - Badges/tags
│
├── Layout
│   ├── Card.jsx              - Carte conteneur
│   ├── GlassCard.jsx         - Carte style glass
│   ├── Grid.jsx              - Grille responsive
│   ├── Modal.jsx             - Dialogue modal
│   ├── TabView.jsx           - Navigation par onglets
│   └── SectionHeader.jsx     - En-tête de section
│
├── Data Display
│   ├── SmartTable.jsx        - Table intelligente
│   ├── DataTable.jsx         - Table simple
│   ├── MobileDataTable.jsx   - Table mobile
│   ├── Skeleton.jsx          - Placeholder chargement
│   ├── PageSkeletons.jsx     - Skeletons pages complètes
│   └── EmptyState.jsx        - État vide
│
├── Charts
│   ├── Charts.jsx            - BarChart, AreaChart, DonutChart
│   ├── Sparkline.jsx         - Mini graphique inline
│   ├── MiniChart.jsx         - Graphique compact
│   └── ChartsDemo.jsx        - Démonstration
│
├── Feedback
│   ├── Toast.jsx             - Notifications toast
│   ├── Tooltip.jsx           - Info-bulles
│   ├── ImportProgressToast.jsx - Toast progression import
│   └── AIConfidenceBadge.jsx - Badge confiance IA
│
├── Metrics
│   ├── MetricCard.jsx        - Carte métrique simple
│   ├── AnimatedMetricCard.jsx - Carte avec animations
│   ├── StatCard.jsx          - Carte statistique
│   └── CardExpandable.jsx    - Carte expansible
│
├── Mobile
│   ├── SwipeableRow.jsx      - Ligne swipeable
│   ├── PullToRefresh.jsx     - Tirer pour rafraîchir
│   ├── MobileCameraScanner.jsx - Scanner caméra
│   ├── BarcodeScanner.jsx    - Lecteur codes-barres
│   └── BarcodeScannerModal.jsx - Modal scanner
│
├── Navigation
│   ├── MegaSectionNav.jsx    - Navigation mega menu
│   ├── FiltersDrawer.jsx     - Drawer filtres
│   └── CommandPalette.jsx    - Palette de commandes
│
├── Editing
│   ├── InlineEditor.jsx      - Édition inline
│   └── PDFPreview.jsx        - Prévisualisation PDF
│
├── Utilities
│   ├── design-tokens.js      - Tokens de design
│   ├── KeyboardShortcuts.jsx - Gestion raccourcis
│   └── index.js              - Exports centralisés
│
└── Tests & Stories
    ├── *.test.jsx            - Tests unitaires
    └── *.stories.jsx         - Storybook stories
```

---

## 14.2 Charts.jsx - Composants Graphiques

**Fichier**: `frontend/src/components/ui/Charts.jsx` (674 lignes)

### Palette de Couleurs du Design System

```javascript
const CHART_COLORS = {
  emerald: { solid: '#10b981', fill: 'rgba(16, 185, 129, 0.2)' },
  teal:    { solid: '#06b6d4', fill: 'rgba(6, 182, 212, 0.2)' },
  amber:   { solid: '#f59e0b', fill: 'rgba(245, 158, 11, 0.2)' },
  rose:    { solid: '#f43f5e', fill: 'rgba(244, 63, 94, 0.2)' },
  blue:    { solid: '#3b82f6', fill: 'rgba(59, 130, 246, 0.2)' },
  violet:  { solid: '#8b5cf6', fill: 'rgba(139, 92, 246, 0.2)' },
  slate:   { solid: 'rgba(255,255,255,0.2)', fill: 'rgba(255,255,255,0.05)' },
};
```

### BarChart - Graphique à Barres

```javascript
/**
 * BarChart - Graphique à barres verticales avec légende
 *
 * @param {Object[]} data - Données [{label: 'Lun', value: 120, color: 'emerald'}]
 * @param {Object[]} series - Séries multiples (optionnel)
 * @param {string} title - Titre du graphique
 * @param {Object[]} legend - Légende [{label: 'Cette semaine', color: 'emerald'}]
 * @param {number} height - Hauteur (défaut: 200)
 * @param {boolean} animate - Animation (défaut: true)
 * @param {boolean} showLabels - Afficher labels (défaut: true)
 * @param {number} barWidth - Largeur barres (défaut: 40)
 * @param {number} gap - Espacement (défaut: 16)
 */
export function BarChart({
  data = [],
  series,
  title,
  legend = [],
  height = 200,
  animate = true,
  showLabels = true,
  barWidth = 40,
  gap = 16,
  className,
})
```

**Fonctionnalités:**
- Barres verticales animées avec Framer Motion
- Support multi-séries pour comparaisons
- Légende automatique
- Hover states avec opacité
- Calcul automatique du max pour l'échelle

**Exemple d'utilisation:**
```jsx
<BarChart
  data={[
    { label: 'Lun', value: 120, color: 'emerald' },
    { label: 'Mar', value: 180, color: 'emerald' },
    { label: 'Mer', value: 140, color: 'emerald' },
  ]}
  title="Ventes par jour"
  legend={[{ label: 'Cette semaine', color: 'emerald' }]}
  height={200}
/>
```

### AreaChart - Graphique en Aires

```javascript
/**
 * AreaChart - Graphique linéaire avec aire remplie
 *
 * @param {number[]} data - Valeurs numériques
 * @param {string[]} labels - Labels de l'axe X
 * @param {string} title - Titre du graphique
 * @param {string} color - Couleur (emerald, blue, amber, etc.)
 * @param {number} height - Hauteur (défaut: 200)
 * @param {boolean} animate - Animation (défaut: true)
 * @param {boolean} showGrid - Afficher grille (défaut: true)
 * @param {boolean} showDots - Afficher points (défaut: false)
 */
export function AreaChart({
  data = [],
  labels = [],
  title,
  color = 'emerald',
  height = 200,
  animate = true,
  showGrid = true,
  showDots = false,
  className,
})
```

**Fonctionnalités:**
- Courbe SVG avec gradient de remplissage
- Animation pathLength pour effet de dessin
- Points interactifs en option
- Grille de fond optionnelle
- Labels d'axe X

**Calcul du chemin SVG:**
```javascript
const { linePath, areaPath, points } = useMemo(() => {
  const width = 400;
  const padding = 10;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const pts = data.map((value, index) => {
    const x = padding + (index / (data.length - 1)) * (width - padding * 2);
    const y = height - padding - ((value - min) / range) * (height - padding * 2);
    return { x, y, value };
  });

  const lineD = `M ${pts.map(p => `${p.x},${p.y}`).join(' L ')}`;
  const areaD = `${lineD} L ${pts[pts.length - 1].x},${height} L ${pts[0].x},${height} Z`;

  return { linePath: lineD, areaPath: areaD, points: pts };
}, [data, height]);
```

### DonutChart - Graphique en Anneau

```javascript
/**
 * DonutChart - Graphique en anneau avec légende et valeur centrale
 *
 * @param {Object[]} data - Données [{label: 'Épicerie', value: 40, color: 'emerald'}]
 * @param {string} title - Titre du graphique
 * @param {string} centerValue - Valeur affichée au centre
 * @param {string} centerLabel - Label sous la valeur centrale
 * @param {number} size - Taille (défaut: 160)
 * @param {number} strokeWidth - Épaisseur anneau (défaut: 12)
 * @param {boolean} showLegend - Afficher légende (défaut: true)
 * @param {boolean} animate - Animation (défaut: true)
 */
export function DonutChart({
  data = [],
  title,
  centerValue,
  centerLabel,
  size = 160,
  strokeWidth = 12,
  showLegend = true,
  animate = true,
  className,
})
```

**Fonctionnalités:**
- Cercles SVG avec strokeDasharray
- Segments interactifs avec hover
- Valeur centrale personnalisable
- Légende avec pourcentages
- Animation d'entrée progressive

### ProgressRings - Anneaux de Progression

```javascript
/**
 * ProgressRings - Groupe d'anneaux de progression pour objectifs
 *
 * @param {Object[]} rings - [{label: 'CA Mensuel', value: 75, color: 'emerald'}]
 * @param {string} title - Titre du groupe
 * @param {number} size - Taille chaque anneau (défaut: 80)
 * @param {number} strokeWidth - Épaisseur (défaut: 8)
 * @param {boolean} animate - Animation (défaut: true)
 */
export function ProgressRings({
  rings = [],
  title,
  size = 80,
  strokeWidth = 8,
  animate = true,
  className,
})
```

### SparklineCard - Carte avec Mini-Graphique

```javascript
/**
 * SparklineCard - Carte KPI avec sparkline intégré
 *
 * @param {string} title - Titre de la métrique
 * @param {string} subtitle - Sous-titre optionnel
 * @param {string|number} value - Valeur principale
 * @param {number[]} data - Données pour le sparkline
 * @param {string} color - Couleur du sparkline
 * @param {string} trend - Tendance ('up', 'down', 'neutral')
 * @param {string} trendValue - Valeur tendance (ex: '+12%')
 */
export function SparklineCard({
  title,
  subtitle,
  value,
  data = [],
  color = 'emerald',
  trend,
  trendValue,
  className,
})
```

---

## 14.3 SmartTable.jsx - Table Intelligente

**Fichier**: `frontend/src/components/ui/SmartTable.jsx` (794 lignes)

### Props Complètes

```javascript
const SmartTable = forwardRef(function SmartTable({
  // Data
  data = [],                    // Données source
  columns = [],                 // Définition colonnes
  keyField = 'id',              // Clé unique par ligne

  // Features
  sortable = true,              // Tri activé
  filterable = true,            // Filtres activés
  selectable = false,           // Sélection bulk
  exportable = true,            // Export CSV/JSON
  editable = false,             // Édition inline

  // Pagination
  paginated = true,             // Pagination activée
  pageSize = 25,                // Lignes par page
  pageSizeOptions = [10, 25, 50, 100],

  // Callbacks
  onSort,                       // (config) => void
  onFilter,                     // (filters) => void
  onSelect,                     // (rows) => void
  onEdit,                       // (rowKey, colKey, value) => void
  onRowClick,                   // (row) => void
  onExport,                     // (format, data) => void

  // State
  loading = false,              // Afficher loader
  emptyMessage = 'Aucune donnée',

  // Style
  className,
  stickyHeader = true,          // En-tête fixe
  striped = true,               // Lignes alternées
  compact = false,              // Mode compact
  variant = 'default',          // default, bordered, minimal

  // External control
  initialSort,                  // { key, direction }
  initialFilters,               // { [key]: value }
}, ref)
```

### Méthodes Exposées via ref

```javascript
useImperativeHandle(ref, () => ({
  getSelectedRows: () => Array.from(selectedRows).map((key) =>
    data.find((row) => row[keyField] === key)
  ),
  clearSelection: () => setSelectedRows(new Set()),
  resetFilters: () => setFilters({}),
  exportData: (format) => handleExport(format),
  getData: () => processedData,
}));
```

### Column Helpers - Générateurs de Colonnes

```javascript
export const columnHelpers = {
  // Nombre formaté
  number: (key, header, options = {}) => ({
    key,
    header,
    align: 'right',
    render: (val) => val !== null ? Number(val).toLocaleString('fr-FR', options) : '-',
    sortFn: (a, b) => (a || 0) - (b || 0),
    ...options,
  }),

  // Prix en euros
  currency: (key, header, options = {}) => ({
    key,
    header,
    align: 'right',
    render: (val) => {
      if (val === null || val === undefined) return '-';
      const num = Number(val);
      const formatted = num.toLocaleString('fr-FR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      const isNegative = num < 0;
      return (
        <span className={isNegative ? 'text-rose-400' : 'text-emerald-400'}>
          {formatted}€
        </span>
      );
    },
    sortFn: (a, b) => (a || 0) - (b || 0),
    ...options,
  }),

  // Pourcentage
  percentage: (key, header, options = {}) => ({
    key,
    header,
    align: 'right',
    render: (val) => val !== null ? `${Number(val).toFixed(1)}%` : '-',
    sortFn: (a, b) => (a || 0) - (b || 0),
    ...options,
  }),

  // Date
  date: (key, header, options = {}) => ({
    key,
    header,
    render: (val) => val ? new Date(val).toLocaleDateString('fr-FR') : '-',
    sortFn: (a, b) => new Date(a || 0) - new Date(b || 0),
    ...options,
  }),

  // Date et heure
  datetime: (key, header, options = {}) => ({
    key,
    header,
    render: (val) => val ? new Date(val).toLocaleString('fr-FR') : '-',
    sortFn: (a, b) => new Date(a || 0) - new Date(b || 0),
    ...options,
  }),

  // Badge/Status
  status: (key, header, statusConfig = {}, options = {}) => ({
    key,
    header,
    render: (val) => {
      const config = statusConfig[val] || { label: val, color: 'slate' };
      const colorMap = {
        emerald: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
        amber: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
        rose: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
        blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        violet: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
        slate: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
      };
      return (
        <span className={clsx(
          'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
          colorMap[config.color] || colorMap.slate
        )}>
          {config.icon && <span className="mr-1">{config.icon}</span>}
          {config.label}
        </span>
      );
    },
    filterType: 'select',
    filterOptions: Object.entries(statusConfig).map(([value, cfg]) => ({
      value,
      label: cfg.label,
    })),
    ...options,
  }),

  // Boolean
  boolean: (key, header, options = {}) => ({
    key,
    header,
    align: 'center',
    render: (val) => val ? (
      <Check className="w-4 h-4 text-emerald-400 mx-auto" />
    ) : (
      <X className="w-4 h-4 text-slate-600 mx-auto" />
    ),
    filterType: 'select',
    filterOptions: [
      { value: 'true', label: 'Oui' },
      { value: 'false', label: 'Non' },
    ],
    filterFn: (val, filter) => filter === 'true' ? Boolean(val) : !Boolean(val),
    ...options,
  }),

  // Actions
  actions: (renderFn, options = {}) => ({
    key: '_actions',
    header: '',
    sortable: false,
    filterable: false,
    exportable: false,
    render: (_value, row) => renderFn(row),
    ...options,
  }),
};
```

### Exemple d'Utilisation Complète

```jsx
import SmartTable, { columnHelpers } from '@/components/ui/SmartTable.jsx';

const columns = [
  { key: 'nom', header: 'Produit', filterable: true },
  columnHelpers.number('stock_actuel', 'Stock'),
  columnHelpers.currency('prix_vente_ttc', 'Prix'),
  columnHelpers.percentage('margin', 'Marge'),
  columnHelpers.status('status', 'Statut', {
    active: { label: 'Actif', color: 'emerald' },
    inactive: { label: 'Inactif', color: 'slate' },
    low_stock: { label: 'Stock bas', color: 'amber' },
  }),
  columnHelpers.date('updated_at', 'Modifié'),
  columnHelpers.actions((row) => (
    <div className="flex gap-2">
      <Button size="sm" onClick={() => handleEdit(row)}>
        <Pencil className="w-4 h-4" />
      </Button>
      <Button size="sm" variant="destructive" onClick={() => handleDelete(row)}>
        <Trash className="w-4 h-4" />
      </Button>
    </div>
  )),
];

<SmartTable
  ref={tableRef}
  data={products}
  columns={columns}
  keyField="id"
  sortable
  filterable
  selectable
  exportable
  editable
  paginated
  pageSize={25}
  onSort={(config) => console.log('Sort:', config)}
  onFilter={(filters) => console.log('Filters:', filters)}
  onSelect={(rows) => setSelectedProducts(rows)}
  onEdit={(id, key, value) => updateProduct(id, { [key]: value })}
  onRowClick={(row) => navigate(`/products/${row.id}`)}
  loading={isLoading}
  stickyHeader
  striped
/>
```

---

## 14.4 Modal.jsx - Dialogue Modal Accessible

**Fichier**: `frontend/src/components/ui/Modal.jsx` (262 lignes)

### Caractéristiques d'Accessibilité (WCAG 2.1 AA)

1. **Focus Trap** - Tab cycle uniquement dans la modal
2. **Focus Management** - Restaure le focus à la fermeture
3. **Keyboard Navigation** - Escape pour fermer
4. **ARIA Attributes** - role="dialog", aria-modal, aria-labelledby
5. **Screen Reader** - Annonces appropriées
6. **Body Scroll Lock** - Compatible iOS
7. **Touch Target** - Bouton fermer minimum 44x44px

### Props

```javascript
/**
 * Modal - Composant de dialogue accessible avec animations
 *
 * @param {boolean} open - Contrôle la visibilité
 * @param {string} title - Titre de la modal (requis pour accessibilité)
 * @param {string} description - Description optionnelle
 * @param {ReactNode} children - Contenu de la modal
 * @param {Array} actions - Boutons d'action
 * @param {Function} onClose - Handler de fermeture
 * @param {string} size - Taille (sm, md, lg, xl, full)
 * @param {boolean} closeOnOverlayClick - Fermer au clic overlay
 * @param {boolean} showCloseButton - Afficher bouton fermer
 */
export default function Modal({
  open,
  isOpen,              // Alias pour compatibilité
  title,
  description,
  children,
  actions,
  onClose,
  size = 'md',
  closeOnOverlayClick = true,
  showCloseButton = true,
})
```

### Tailles Disponibles

```javascript
const sizes = {
  sm: 'max-w-md',      // 448px
  md: 'max-w-xl',      // 576px
  lg: 'max-w-2xl',     // 672px
  xl: 'max-w-4xl',     // 896px
  full: 'max-w-[90vw]', // 90% viewport
};
```

### Focus Trap Implementation

```javascript
useEffect(() => {
  if (!isVisible || isClosing) return;

  const handleTab = (e) => {
    if (e.key !== 'Tab') return;

    const modal = modalRef.current;
    if (!modal) return;

    const focusableElements = modal.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), ' +
      'select:not([disabled]), textarea:not([disabled]), ' +
      '[tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement?.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement?.focus();
    }
  };

  document.addEventListener('keydown', handleTab);
  return () => document.removeEventListener('keydown', handleTab);
}, [isVisible, isClosing]);
```

### ConfirmDialog - Sous-Composant

```javascript
/**
 * ConfirmDialog - Modal de confirmation pour actions destructives
 */
export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = 'Confirmer l\'action',
  description = 'Êtes-vous sûr de vouloir continuer ?',
  confirmLabel = 'Confirmer',
  cancelLabel = 'Annuler',
  variant = 'destructive',
  loading = false,
})

// Exemple d'utilisation
<ConfirmDialog
  open={showDeleteConfirm}
  onClose={() => setShowDeleteConfirm(false)}
  onConfirm={handleDelete}
  title="Supprimer le produit"
  description="Cette action est irréversible."
  confirmLabel="Supprimer"
  variant="destructive"
  loading={isDeleting}
/>
```

---

## 14.5 SwipeableRow.jsx - Ligne Swipeable Mobile

**Fichier**: `frontend/src/components/ui/SwipeableRow.jsx`

### Fonctionnalités

- Swipe gauche/droite pour actions
- Actions configurables par côté
- Seuil de déclenchement configurable
- Animation de retour élastique
- Support tactile et souris

```javascript
/**
 * SwipeableRow - Ligne avec actions swipe pour mobile
 *
 * @param {ReactNode} children - Contenu de la ligne
 * @param {Object} leftAction - Action swipe gauche
 * @param {Object} rightAction - Action swipe droite
 * @param {number} threshold - Seuil de déclenchement (défaut: 80)
 */
export function SwipeableRow({
  children,
  leftAction,   // { label, icon, color, onAction }
  rightAction,  // { label, icon, color, onAction }
  threshold = 80,
})
```

**Exemple:**
```jsx
<SwipeableRow
  leftAction={{
    label: 'Éditer',
    icon: <Pencil />,
    color: 'blue',
    onAction: () => handleEdit(item),
  }}
  rightAction={{
    label: 'Supprimer',
    icon: <Trash />,
    color: 'rose',
    onAction: () => handleDelete(item),
  }}
>
  <div className="p-4">
    {item.name}
  </div>
</SwipeableRow>
```

---

## 14.6 PullToRefresh.jsx - Tirer pour Rafraîchir

**Fichier**: `frontend/src/components/ui/PullToRefresh.jsx`

```javascript
/**
 * PullToRefresh - Conteneur avec refresh par glissement
 *
 * @param {ReactNode} children - Contenu scrollable
 * @param {Function} onRefresh - Callback async de refresh
 * @param {number} threshold - Distance de déclenchement (défaut: 80)
 * @param {boolean} disabled - Désactiver le pull
 */
export function PullToRefresh({
  children,
  onRefresh,
  threshold = 80,
  disabled = false,
})
```

**Exemple (Page Kitchen):**
```jsx
<PullToRefresh onRefresh={async () => {
  await refetchIngredients();
}}>
  <div className="space-y-2">
    {ingredients.map(ing => (
      <IngredientCard key={ing.id} ingredient={ing} />
    ))}
  </div>
</PullToRefresh>
```

---

## 14.7 BarcodeScanner.jsx - Lecteur Codes-Barres

**Fichier**: `frontend/src/components/ui/BarcodeScanner.jsx`

### Architecture

```javascript
/**
 * BarcodeScanner - Lecteur de codes-barres via caméra
 *
 * Utilise quagga2 pour la détection de codes-barres.
 *
 * @param {Function} onDetected - Callback (code, format) => void
 * @param {Function} onError - Callback erreur
 * @param {string[]} formats - Formats supportés ['ean_13', 'ean_8', 'code_128']
 * @param {boolean} continuous - Mode continu ou single shot
 */
export function BarcodeScanner({
  onDetected,
  onError,
  formats = ['ean_13', 'ean_8', 'code_128'],
  continuous = false,
})
```

### BarcodeScannerModal - Version Modal

```jsx
<BarcodeScannerModal
  open={showScanner}
  onClose={() => setShowScanner(false)}
  onScan={(code) => {
    handleProductLookup(code);
    setShowScanner(false);
  }}
/>
```

---

## 14.8 InlineEditor.jsx - Édition Inline

**Fichier**: `frontend/src/components/ui/InlineEditor.jsx`

### Props

```javascript
/**
 * EditableCell - Cellule avec édition inline
 *
 * @param {any} value - Valeur actuelle
 * @param {ReactNode} displayValue - Valeur affichée (peut être formatée)
 * @param {string} type - Type d'input (text, number, select)
 * @param {Array} options - Options pour select
 * @param {Function} onSave - Callback de sauvegarde
 * @param {Function} formatDisplay - Formateur d'affichage
 */
export default function EditableCell({
  value,
  displayValue,
  type = 'text',
  options,
  onSave,
  formatDisplay,
})
```

### Comportements

| Action | Résultat |
|--------|----------|
| Double-clic | Entre en mode édition |
| Enter | Sauvegarde et ferme |
| Escape | Annule et ferme |
| Tab | Sauvegarde et passe au suivant |
| Clic extérieur | Sauvegarde et ferme |

---

## 14.9 design-tokens.js - Tokens de Design

**Fichier**: `frontend/src/components/ui/design-tokens.js`

```javascript
export const tokens = {
  // Couleurs
  colors: {
    brand: {
      50: '#f0fdf4',
      500: '#10b981',
      600: '#059669',
    },
    surface: {
      base: '#0a0a0f',
      elevated: 'rgba(255, 255, 255, 0.03)',
      overlay: 'rgba(0, 0, 0, 0.6)',
    },
    border: {
      subtle: 'rgba(255, 255, 255, 0.1)',
      default: 'rgba(255, 255, 255, 0.15)',
      focus: '#10b981',
    },
    text: {
      primary: '#ffffff',
      secondary: 'rgba(255, 255, 255, 0.7)',
      muted: 'rgba(255, 255, 255, 0.5)',
    },
    status: {
      success: '#10b981',
      warning: '#f59e0b',
      error: '#f43f5e',
      info: '#3b82f6',
    },
  },

  // Espacements
  spacing: {
    xs: '0.25rem',  // 4px
    sm: '0.5rem',   // 8px
    md: '1rem',     // 16px
    lg: '1.5rem',   // 24px
    xl: '2rem',     // 32px
    '2xl': '3rem',  // 48px
  },

  // Rayons de bordure
  radii: {
    sm: '0.375rem',  // 6px
    md: '0.5rem',    // 8px
    lg: '0.75rem',   // 12px
    xl: '1rem',      // 16px
    '2xl': '1.5rem', // 24px
    full: '9999px',
  },

  // Ombres
  shadows: {
    sm: '0 1px 2px rgba(0, 0, 0, 0.4)',
    md: '0 4px 6px rgba(0, 0, 0, 0.5)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.6)',
    glow: '0 0 20px rgba(16, 185, 129, 0.3)',
  },

  // Transitions
  transitions: {
    fast: '150ms ease',
    normal: '200ms ease',
    slow: '300ms ease',
  },

  // Typographie
  fontSizes: {
    xs: '0.75rem',   // 12px
    sm: '0.875rem',  // 14px
    base: '1rem',    // 16px
    lg: '1.125rem',  // 18px
    xl: '1.25rem',   // 20px
    '2xl': '1.5rem', // 24px
    '3xl': '2rem',   // 32px
  },

  // Z-index
  zIndex: {
    dropdown: 50,
    sticky: 100,
    modal: 200,
    popover: 300,
    tooltip: 400,
    toast: 500,
  },
};
```

---

## 14.10 Cascade UI → Données

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FLUX COMPOSANT UI COMPLET                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [1] PAGE COMPOSANT                                                          │
│      │                                                                       │
│      ├──► SmartTable                                                        │
│      │    ├──► columns avec columnHelpers                                   │
│      │    ├──► onEdit(rowKey, colKey, value)                                │
│      │    └──► onRowClick(row) → navigation                                 │
│      │                                                                       │
│      ├──► Modal                                                              │
│      │    ├──► Form avec validation                                         │
│      │    └──► actions [{ onClick: mutation.mutate }]                       │
│      │                                                                       │
│      └──► Charts                                                             │
│           └──► data depuis useQuery                                          │
│                                                                              │
│  [2] HOOKS                                                                   │
│      │                                                                       │
│      ├──► useMutation({ onSuccess: invalidateQueries })                     │
│      │    └──► Optimistic update via queryClient.setQueryData              │
│      │                                                                       │
│      └──► useQuery({ queryKey, queryFn })                                   │
│           └──► staleTime, refetchOnWindowFocus                              │
│                                                                              │
│  [3] API CLIENT                                                              │
│      │                                                                       │
│      └──► apiFetch(endpoint, options)                                       │
│           ├──► Token JWT automatique                                        │
│           └──► Gestion erreurs centralisée                                  │
│                                                                              │
│  [4] BACKEND                                                                 │
│      │                                                                       │
│      └──► FastAPI → Service → Core → Database                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# PARTIE 15: Authentification & Sécurité - Documentation Exhaustive

## 15.1 Architecture Globale de Sécurité

### Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ARCHITECTURE SÉCURITÉ                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  [CLIENT]                                                                    │
│      │                                                                       │
│      ├──► Navigateur Web                                                    │
│      │    └──► Cookies httpOnly (access_token + refresh_token)              │
│      │                                                                       │
│      └──► Client API (curl, mobile, etc.)                                   │
│           └──► Header Authorization: Bearer <token>                          │
│                                                                              │
│  [FASTAPI BACKEND]                                                           │
│      │                                                                       │
│      ├──► Middleware Rate Limiter                                           │
│      │    └──► 5 req/min pour /auth/token (anti-brute force)                │
│      │                                                                       │
│      ├──► Extraction Token                                                   │
│      │    ├──► 1. Cookie httpOnly (priorité)                                │
│      │    └──► 2. Header Authorization: Bearer (fallback)                   │
│      │                                                                       │
│      ├──► Validation JWT                                                     │
│      │    ├──► Signature avec multi-secrets (rotation de clés)              │
│      │    ├──► Expiration (access: 15min, refresh: 7 jours)                 │
│      │    ├──► Type (access vs refresh)                                     │
│      │    └──► Révocation via JTI (mémoire RAM)                             │
│      │                                                                       │
│      ├──► Extraction AuthenticatedUser                                       │
│      │    ├──► id, username, role, tenant_id                                │
│      │    └──► Validation rôle (standard, manager, admin)                   │
│      │                                                                       │
│      ├──► Résolution Tenant                                                  │
│      │    ├──► Depuis token JWT (tenant_id)                                 │
│      │    ├──► Depuis route (/restaurant → tenant 2)                        │
│      │    └──► Depuis header X-Tenant (mode démo)                           │
│      │                                                                       │
│      └──► RBAC (Role-Based Access Control)                                  │
│           ├──► standard: lecture seule                                       │
│           ├──► manager: lecture + écriture                                   │
│           └──► admin: tous les droits                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 15.2 Module security.py - Cœur de l'Authentification

**Fichier**: `backend/dependencies/security.py` (445 lignes)

### Configuration JWT

```python
# Variables d'environnement
JWT_SECRET_KEY           # Secret de signature (minimum 32 caractères)
JWT_SECRET_KEYS          # Multi-secrets séparés par virgule (rotation)
JWT_ALGORITHM            # Algorithme (défaut: HS256)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES  # Durée access token (défaut: 15)
JWT_REFRESH_TOKEN_EXPIRE_DAYS    # Durée refresh token (défaut: 7)

# Configuration cookies
COOKIE_SECURE            # HTTPS only (défaut: false en dev)
COOKIE_SAMESITE          # Protection CSRF: lax, strict, none
```

### Constantes de Sécurité

```python
# Durées d'expiration
ACCESS_TOKEN_EXPIRE_MINUTES = 15   # Token court pour limiter l'exposition
REFRESH_TOKEN_EXPIRE_DAYS = 7      # Rotation hebdomadaire

# Noms des cookies
COOKIE_NAME_ACCESS = "access_token"
COOKIE_NAME_REFRESH = "refresh_token"

# Hiérarchie des rôles
ROLE_PRIORITY = {"standard": 0, "manager": 1, "admin": 2}
```

### Schéma AuthenticatedUser

```python
class AuthenticatedUser(BaseModel):
    """Contexte utilisateur extrait d'un access token JWT."""

    id: int           # ID utilisateur en base
    username: str     # Nom d'utilisateur
    role: str         # standard | manager | admin
    tenant_id: int    # ID du tenant courant
```

### Création de Tokens

#### create_access_token

```python
def create_access_token(claims: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Crée un token d'accès JWT signé.

    Claims inclus:
    - sub: ID utilisateur (string)
    - username: Nom d'utilisateur
    - role: Rôle (standard, manager, admin)
    - tenant_id: ID du tenant
    - tenant_code: Code du tenant
    - exp: Timestamp d'expiration
    - jti: UUID unique (pour révocation)
    - type: "access"

    Args:
        claims: Dictionnaire des claims utilisateur
        expires_delta: Durée personnalisée (optionnel)

    Returns:
        Token JWT signé encodé en string
    """
    payload = claims.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload.update({"exp": expire, "jti": uuid.uuid4().hex, "type": "access"})
    return jwt.encode(payload, _get_secret(), algorithm=_get_algorithm())
```

#### create_refresh_token

```python
def create_refresh_token(claims: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Crée un refresh token avec durée longue.

    Claims inclus (minimal pour limiter l'exposition):
    - sub: ID utilisateur
    - username: Nom d'utilisateur
    - tenant_id: ID du tenant
    - type: "refresh"
    - exp: Timestamp d'expiration
    - jti: UUID unique
    """
    payload = {
        "sub": claims.get("sub"),
        "username": claims.get("username"),
        "tenant_id": claims.get("tenant_id"),
        "type": "refresh",
    }
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    payload.update({"exp": expire, "jti": uuid.uuid4().hex})
    return jwt.encode(payload, _get_secret(), algorithm=_get_algorithm())
```

### Gestion des Cookies

#### set_auth_cookies

```python
def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_max_age: int | None = None,
    refresh_max_age: int | None = None,
) -> None:
    """
    Définit les cookies httpOnly sécurisés.

    Access token:
    - Disponible sur tous les chemins (path="/")
    - Durée: 15 minutes

    Refresh token:
    - Disponible uniquement sur /auth (path="/auth")
    - Durée: 7 jours
    - Isolé pour éviter l'envoi sur chaque requête
    """
    response.set_cookie(
        key=COOKIE_NAME_ACCESS,
        value=access_token,
        max_age=access_max_age or ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,         # Non accessible via JavaScript
        secure=COOKIE_SECURE,  # HTTPS only en production
        samesite=COOKIE_SAMESITE,  # Protection CSRF
        path="/",
    )
    response.set_cookie(
        key=COOKIE_NAME_REFRESH,
        value=refresh_token,
        max_age=refresh_max_age or REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/auth",  # Limité aux endpoints auth
    )
```

### Extraction et Validation

#### _extract_token_from_request

```python
def _extract_token_from_request(request: Request) -> str | None:
    """
    Extrait le token depuis le cookie ou le header Authorization.

    Priorité:
    1. Cookie httpOnly (préféré pour les navigateurs)
    2. Header Authorization: Bearer (pour les clients API)

    Returns:
        Token string ou None si absent
    """
    # 1. Cookie d'abord
    token = request.cookies.get(COOKIE_NAME_ACCESS)
    if token:
        return token

    # 2. Header Authorization
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    return None
```

#### get_current_user_from_request

```python
def get_current_user_from_request(request: Request) -> AuthenticatedUser:
    """
    Récupère l'utilisateur authentifié depuis la requête.

    Process:
    1. Extraction token (cookie ou header)
    2. Décodage JWT avec validation signature
    3. Vérification expiration
    4. Vérification non-révoqué (JTI)
    5. Vérification type = "access"
    6. Extraction claims (id, username, role, tenant_id)
    7. Validation rôle dans la liste autorisée

    Raises:
        HTTPException 401: Token manquant, invalide, expiré ou révoqué
    """
    token = _extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token(token)

    # Vérifie type access (pas refresh)
    if payload.get("type") == "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token non autorise pour cette operation",
        )

    # Extraction claims
    user_id = int(payload["sub"])
    username = str(payload["username"])
    role = str(payload["role"]).lower()
    tenant_id = int(payload["tenant_id"])

    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Rôle inconnu dans le token",
        )

    return AuthenticatedUser(id=user_id, username=username, role=role, tenant_id=tenant_id)
```

### Système de Révocation

```python
# Mémoire de révocation (RAM) - liste des JTI révoqués
_REVOKED_JTIS: dict[str, float] = {}  # {jti: exp_timestamp}


def revoke_token(token: str) -> None:
    """
    Révoque un token en ajoutant son JTI à la blacklist.

    Le JTI reste dans la blacklist jusqu'à son expiration naturelle
    pour éviter les réutilisations.
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        jti = payload.get("jti")
        exp = payload.get("exp")
    except Exception:
        return

    if jti and exp:
        _REVOKED_JTIS[str(jti)] = float(exp)


def _enforce_not_revoked(payload: dict[str, Any]) -> None:
    """Vérifie que le token n'est pas révoqué."""
    jti = str(payload.get("jti") or "")
    if not jti:
        return

    cutoff = _REVOKED_JTIS.get(jti)
    if cutoff is None:
        return

    # Si encore dans la période de validité, rejeter
    if time.time() <= float(cutoff):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token révoqué",
        )
    else:
        # Nettoyer les entrées expirées
        _REVOKED_JTIS.pop(jti, None)
```

### RBAC (Role-Based Access Control)

#### require_roles Factory

```python
def require_roles(*roles: str) -> Callable:
    """
    Factory pour créer une dépendance de vérification de rôles.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_roles("admin"))])
        def admin_only():
            return {"message": "Admin access"}

        @router.get("/manage", dependencies=[Depends(require_roles("manager", "admin"))])
        def manager_or_admin():
            return {"message": "Manager or admin"}
    """
    allowed = {role.lower() for role in roles} or set(ALLOWED_ROLES)

    async def _checker(request: Request) -> AuthenticatedUser:
        user = get_current_user_from_request(request)
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rôle insuffisant pour accéder à cette ressource",
            )
        return user

    return _checker
```

#### enforce_default_rbac

```python
async def enforce_default_rbac(request: Request) -> AuthenticatedUser:
    """
    Politique RBAC par défaut:
    - GET: Tous les utilisateurs authentifiés
    - POST/PUT/PATCH/DELETE: Managers et admins uniquement
    """
    user = get_current_user_from_request(request)

    method = request.method.upper()
    if method in {"POST", "PUT", "PATCH", "DELETE"}:
        if ROLE_PRIORITY[user.role] < ROLE_PRIORITY["manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rôle manager ou admin requis pour modifier les données",
            )
    return user
```

---

## 15.3 Module auth.py - Endpoints d'Authentification

**Fichier**: `backend/api/auth.py` (230 lignes)

### Endpoints Disponibles

| Endpoint | Méthode | Description | Rate Limit |
|----------|---------|-------------|------------|
| `/auth/token` | POST | OAuth2 token (pour API) | 5/min |
| `/auth/login` | POST | Login avec cookies | 5/min |
| `/auth/refresh` | POST | Rafraîchit access token | - |
| `/auth/logout` | POST | Déconnexion | - |

### OAuth2TenantRequestForm

```python
class OAuth2TenantRequestForm:
    """Extension du formulaire OAuth2 standard avec la notion de tenant."""

    def __init__(
        self,
        grant_type: str | None = Form(default=None, pattern="password"),
        username: str = Form(...),
        password: str = Form(...),
        scope: str = Form(default=""),
        client_id: str | None = Form(default=None),
        client_secret: str | None = Form(default=None),
        tenant: str = Form(default="epicerie"),
    )
```

### POST /auth/token

```python
@router.post("/token", response_model=TokenResponse)
@rate_limit(requests=5, window=60, burst=2)  # Anti brute-force
def issue_token(request: Request, form_data: OAuth2TenantRequestForm = Depends()):
    """
    Émet un token bearer OAuth2 (pour les clients API).

    Body (form-urlencoded):
    - username: string (requis)
    - password: string (requis)
    - tenant: string (défaut: "epicerie")

    Returns:
    {
        "access_token": "eyJ...",
        "token_type": "bearer",
        "expires_in": 900,
        "user": {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "tenant_id": 1,
            "tenant_code": "epicerie",
            "tenant_name": "Épicerie HQ"
        }
    }
    """
```

### POST /auth/login

```python
@router.post("/login", response_model=CookieTokenResponse)
@rate_limit(requests=5, window=60, burst=2)
def login_with_cookies(request: Request, response: Response, form_data: ...):
    """
    Connexion avec cookies httpOnly (recommandé pour navigateurs).

    Process:
    1. Valide les identifiants via core/user_service.authenticate_user()
    2. Résout le tenant
    3. Crée access token (15 min)
    4. Crée refresh token (7 jours)
    5. Place les deux en cookies httpOnly

    Cookies posés:
    - access_token: path=/, max-age=900
    - refresh_token: path=/auth, max-age=604800

    Returns:
    {
        "message": "Authentification reussie",
        "expires_in": 900,
        "user": { ... }
    }
    """
```

### POST /auth/refresh

```python
@router.post("/refresh", response_model=RefreshResponse)
def refresh_access_token(request: Request, response: Response):
    """
    Rafraîchit le token d'accès via le refresh token.

    Process:
    1. Lit refresh token depuis cookie httpOnly
    2. Valide et décode le refresh token
    3. Charge données utilisateur fraîches depuis la base
    4. Crée nouveaux tokens (rotation)
    5. Révoque l'ancien refresh token
    6. Pose les nouveaux cookies

    Sécurité:
    - Rotation systématique des refresh tokens
    - Révocation de l'ancien après usage
    - Rechargement des données utilisateur (rôle mis à jour)
    """
```

### POST /auth/logout

```python
@router.post("/logout")
def logout(request: Request, response: Response):
    """
    Déconnexion complète.

    Process:
    1. Révoque le refresh token courant
    2. Supprime les cookies access et refresh

    Returns:
    {"message": "Deconnexion reussie"}
    """
```

---

## 15.4 Module tenant.py - Multi-Tenancy

**Fichier**: `backend/dependencies/tenant.py` (234 lignes)

### Tenants Prédéfinis

```python
@dataclass(frozen=True)
class Tenant:
    id: int
    code: str
    name: str

# Tenants par défaut
DEFAULT_TENANT = Tenant(id=1, code="epicerie", name="Épicerie HQ")
RESTAURANT_TENANT = Tenant(id=2, code="restaurant", name="Restaurant HQ")
TRESORERIE_TENANT = Tenant(id=3, code="tresorerie", name="Trésorerie HQ")
INTELLIGENCE_TENANT = Tenant(id=4, code="intelligence", name="Intelligence")
```

### Résolution de Tenant

```python
@lru_cache(maxsize=32)  # Cache pour performance
def _load_tenant(identifier: str) -> Tenant | None:
    """Charge un tenant depuis la base avec cache LRU."""
    engine = get_engine()
    query = text("""
        SELECT id, name, code
        FROM tenants
        WHERE code = :code OR CAST(id AS TEXT) = :code
        LIMIT 1
    """)
    with engine.begin() as conn:
        row = conn.execute(query, {"code": identifier}).fetchone()
        if not row:
            return None
        return Tenant(id=int(row.id), code=str(row.code), name=str(row.name))


def resolve_tenant(identifier: str | int | None) -> Tenant | None:
    """
    Résout un tenant par ID ou code.

    Args:
        identifier: 1, "epicerie", "restaurant", etc.

    Returns:
        Tenant ou None
    """
```

### Dépendances FastAPI

#### get_current_tenant (Strict)

```python
async def get_current_tenant(request: Request) -> Tenant:
    """
    Récupère le tenant depuis l'utilisateur authentifié.

    Exige un token valide. Utilise tenant_id du JWT.

    Raises:
        HTTPException 401: Token manquant ou invalide
        HTTPException 400: Tenant introuvable
    """
    user = get_current_user_from_request(request)
    tenant = resolve_tenant(user.tenant_id)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant introuvable",
        )
    return tenant
```

#### get_current_tenant_or_default (Permissif)

```python
async def get_current_tenant_or_default(request: Request) -> Tenant:
    """
    Variante permissive pour le mode démo.

    Si token présent → utilise tenant du token
    Si NEWCMS_ALLOW_ANON=true → utilise tenant par défaut ou X-Tenant header

    Utile pour les endpoints publics ou le développement.
    """
```

#### get_tenant_by_route (Intelligent)

```python
async def get_tenant_by_route(request: Request) -> Tenant:
    """
    Détermine automatiquement le tenant selon la route.

    Mapping:
    - /restaurant/*       → tenant 2 (restaurant)
    - /supplier-scoring/* → tenant 1 (epicerie)
    - /intelligence/*     → tenant 4 (intelligence)
    - /forecasting/*      → tenant 4 (intelligence)
    - /anomaly/*          → tenant 4 (intelligence)
    - Autres              → tenant du token JWT
    """
    path = request.url.path.lower()
    user = get_current_user_from_request(request)

    if path.startswith("/restaurant"):
        return RESTAURANT_TENANT
    elif path.startswith("/supplier-scoring"):
        return DEFAULT_TENANT
    elif path.startswith(("/intelligence", "/forecasting", "/anomaly")):
        return INTELLIGENCE_TENANT

    return resolve_tenant(user.tenant_id) or DEFAULT_TENANT
```

---

## 15.5 Rate Limiting

**Fichier**: `backend/middleware/rate_limiter.py`

### Décorateur rate_limit

```python
from functools import wraps
from collections import defaultdict
from time import time

def rate_limit(requests: int = 10, window: int = 60, burst: int = 0):
    """
    Limite le nombre de requêtes par IP.

    Args:
        requests: Nombre max de requêtes dans la fenêtre
        window: Taille de la fenêtre en secondes
        burst: Nombre de requêtes supplémentaires autorisées en rafale

    Usage:
        @router.post("/login")
        @rate_limit(requests=5, window=60, burst=2)
        def login(...):
            ...

    Raises:
        HTTPException 429: Too Many Requests
    """
```

### Application sur /auth

```python
# 5 tentatives par minute avec burst de 2
# Protection contre brute-force sur les identifiants

@router.post("/token")
@rate_limit(requests=5, window=60, burst=2)
def issue_token(...): ...

@router.post("/login")
@rate_limit(requests=5, window=60, burst=2)
def login_with_cookies(...): ...
```

---

## 15.6 Flux d'Authentification Complets

### Flux 1: Login Navigateur (Cookies)

```
┌─────────────────────────────────────────────────────────────────┐
│  1. POST /auth/login                                            │
│     Body: username=admin&password=secret&tenant=epicerie        │
│                                                                  │
│  2. Backend:                                                     │
│     - authenticate_user(username, password)                      │
│     - resolve_tenant(tenant)                                     │
│     - create_access_token(claims)                                │
│     - create_refresh_token(claims)                               │
│     - set_auth_cookies(response, access, refresh)                │
│                                                                  │
│  3. Response:                                                    │
│     - Status: 200                                                │
│     - Set-Cookie: access_token=eyJ...; HttpOnly; Path=/          │
│     - Set-Cookie: refresh_token=eyJ...; HttpOnly; Path=/auth     │
│     - Body: {"message": "Authentification reussie", ...}         │
│                                                                  │
│  4. Requêtes suivantes:                                          │
│     - Browser envoie automatiquement Cookie: access_token=...    │
│     - Backend extrait token depuis cookie                        │
│     - Backend valide et extrait AuthenticatedUser                │
└─────────────────────────────────────────────────────────────────┘
```

### Flux 2: Client API (Bearer Token)

```
┌─────────────────────────────────────────────────────────────────┐
│  1. POST /auth/token                                            │
│     Body: username=admin&password=secret&tenant=epicerie        │
│                                                                  │
│  2. Response:                                                    │
│     - Status: 200                                                │
│     - Body: {                                                    │
│         "access_token": "eyJhbGciOiJIUzI1NiIs...",              │
│         "token_type": "bearer",                                  │
│         "expires_in": 900                                        │
│       }                                                          │
│                                                                  │
│  3. Requêtes suivantes:                                          │
│     GET /catalog/products                                        │
│     Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIs...       │
│                                                                  │
│  4. Backend:                                                     │
│     - Extract token from Authorization header                    │
│     - Validate JWT signature, expiration                         │
│     - Extract AuthenticatedUser                                  │
│     - Resolve Tenant                                             │
│     - Execute request                                            │
└─────────────────────────────────────────────────────────────────┘
```

### Flux 3: Refresh Token

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Access token expiré (15 min)                                │
│                                                                  │
│  2. POST /auth/refresh                                          │
│     Cookie: refresh_token=eyJ...                                 │
│                                                                  │
│  3. Backend:                                                     │
│     - Lit refresh_token depuis cookie                            │
│     - Valide refresh token (signature, expiration, non-révoqué)  │
│     - Charge user fraîche depuis DB                              │
│     - Crée nouveaux access + refresh tokens                      │
│     - Révoque l'ancien refresh token                             │
│     - Pose nouveaux cookies                                      │
│                                                                  │
│  4. Response:                                                    │
│     - Status: 200                                                │
│     - Set-Cookie: access_token=NOUVEAU; HttpOnly                 │
│     - Set-Cookie: refresh_token=NOUVEAU; HttpOnly                │
│     - Body: {"message": "Token rafraichi", "expires_in": 900}    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 15.7 Tables Base de Données

### Table app_users

```sql
CREATE TABLE app_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    role VARCHAR(20) DEFAULT 'standard',  -- standard, manager, admin
    email VARCHAR(255),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,

    INDEX idx_username (username),
    CONSTRAINT chk_role CHECK (role IN ('standard', 'manager', 'admin'))
);
```

### Table tenants

```sql
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,     -- epicerie, restaurant, tresorerie, intelligence
    name VARCHAR(255) NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_code (code)
);

-- Données initiales
INSERT INTO tenants (id, code, name) VALUES
    (1, 'epicerie', 'Épicerie HQ'),
    (2, 'restaurant', 'Restaurant HQ'),
    (3, 'tresorerie', 'Trésorerie HQ'),
    (4, 'intelligence', 'Intelligence');
```

---

## 15.8 Frontend - Hook useAuth

**Fichier**: `frontend/src/hooks/useAuth.js`

```javascript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiFetch } from '../api/client.js';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username, password, tenant = 'epicerie') => {
        set({ isLoading: true, error: null });
        try {
          const response = await apiFetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ username, password, tenant }),
          });

          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
          });

          return { success: true };
        } catch (error) {
          set({ error: error.message, isLoading: false });
          return { success: false, error: error.message };
        }
      },

      logout: async () => {
        try {
          await apiFetch('/auth/logout', { method: 'POST' });
        } finally {
          set({ user: null, isAuthenticated: false });
        }
      },

      refreshToken: async () => {
        try {
          const response = await apiFetch('/auth/refresh', { method: 'POST' });
          return { success: true };
        } catch (error) {
          set({ user: null, isAuthenticated: false });
          return { success: false };
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
);

// Hook simplifié
export function useAuth() {
  const store = useAuthStore();
  return {
    user: store.user,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    error: store.error,
    login: store.login,
    logout: store.logout,
    refreshToken: store.refreshToken,
  };
}
```

---

## 15.9 Sécurité - Bonnes Pratiques Implémentées

| Mesure | Implémentation |
|--------|----------------|
| **Tokens courts** | Access token 15 min (limite l'exposition) |
| **Rotation refresh** | Nouveau refresh token à chaque refresh |
| **Révocation JTI** | Blacklist en RAM avec garbage collection |
| **Cookies httpOnly** | Non accessible via JavaScript |
| **Cookies SameSite** | Protection CSRF (lax/strict) |
| **Rate limiting** | 5 tentatives/min sur /auth |
| **Multi-secrets** | Support rotation de clés JWT |
| **Secrets longs** | Minimum 32 caractères enforced |
| **Validation rôles** | Whitelist des rôles autorisés |
| **Séparation paths** | Refresh token path="/auth" uniquement |

---

