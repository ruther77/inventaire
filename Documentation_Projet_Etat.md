# Documentation Projet - État Actuel

**Date de génération:** 15 Décembre 2025
**Branche:** DEVELOPPEMENT
**Version:** 2.0 (Architecture Multi-Tenant)

---

## 1. Vue d'Ensemble

### 1.1 Description du Projet

Plateforme web intégrée de **gestion commerciale multi-métiers** combinant :
- **Épicerie HQ** : Gestion d'inventaire, catalogue produits, suivi des prix fournisseurs, import de factures
- **Restaurant HQ** : Fiches techniques, menus, coûts matières, charges opérationnelles, analyse food cost
- **Module Trésorerie** : Flux bancaires, catégorisation automatique, rapprochement comptable
- **Intelligence Artificielle** : Prévisions, détection d'anomalies, scoring fournisseurs

### 1.2 Architecture Technique

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ARCHITECTURE GLOBALE                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │  Frontend    │    │   Backend    │    │       Base de Données     │  │
│  │  React/Vite  │◄──►│   FastAPI    │◄──►│       PostgreSQL          │  │
│  │  Port 5173   │    │   Port 8000  │    │       Port 5432           │  │
│  └──────────────┘    └──────────────┘    └──────────────────────────┘  │
│         │                   │                       │                   │
│         │                   │                       │                   │
│         ▼                   ▼                       ▼                   │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      Services Externes                            │  │
│  │  • n8n (Workflows)  • Ollama (LLM local)  • Docker Compose       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Stack Technologique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Frontend | React + Vite | 18.x / 5.x |
| UI Framework | TailwindCSS | 3.x |
| Backend | FastAPI (Python) | 0.100+ |
| Base de données | PostgreSQL | 16.x |
| ORM | SQLAlchemy + Alembic | 2.x |
| Containerisation | Docker Compose | 2.x |
| Workflows | n8n | Latest |
| LLM Local | Ollama | Latest |

---

## 2. Structure du Projet

### 2.1 Arborescence Principale

```
monprojet/
├── backend/                    # API FastAPI
│   ├── api/                    # Endpoints REST (29 modules)
│   ├── services/               # Logique métier
│   │   ├── finance/            # Services financiers
│   │   ├── restaurant/         # Services restaurant
│   │   ├── importers/          # Parsers CSV/PDF
│   │   ├── parsers/            # Analyseurs de données
│   │   └── mappers/            # Conversions inter-modules
│   ├── schemas/                # Modèles Pydantic
│   ├── middleware/             # Rate limiter, performance
│   └── dependencies/           # Auth, Tenant, Security
│
├── frontend/                   # SPA React
│   └── src/
│       ├── app/                # Routes et shells
│       ├── features/           # Pages par domaine (17 modules)
│       ├── components/         # UI réutilisables
│       ├── hooks/              # Custom hooks (25+)
│       ├── contexts/           # Providers React
│       └── modules/            # Organisation métier
│
├── core/                       # Moteurs métier
│   ├── finance/                # Intelligence financière
│   │   ├── anomaly_detection.py
│   │   ├── forecasting.py
│   │   ├── supplier_scoring.py
│   │   ├── rules_engine.py
│   │   ├── bank_reconciliation.py
│   │   └── margin_calculator.py
│   ├── bank_import/            # Import relevés bancaires
│   ├── repositories/           # Accès données
│   └── parsers/                # Extracteurs PDF/CSV
│
├── db/                         # Schémas SQL
│   └── init.sql                # Script d'initialisation
│
├── migrations/                 # Alembic migrations
├── scripts/                    # Utilitaires CLI
├── tests/                      # Tests automatisés
├── docs/                       # Documentation
└── docker-compose.yml          # Orchestration services
```

---

## 3. Modules Backend (API)

### 3.1 Liste des Endpoints

| Module | Préfixe | Description |
|--------|---------|-------------|
| `auth.py` | `/auth` | Authentification JWT |
| `catalog.py` | `/catalog` | CRUD produits + pagination |
| `stock.py` | `/stock` | Mouvements de stock |
| `prices.py` | `/prices` | Historique prix fournisseurs |
| `invoices.py` | `/invoices` | Import/traitement factures |
| `finance.py` | `/finance` | Comptes, transactions, rapprochement |
| `cockpit.py` | `/cockpit` | Vue 360° consolidée |
| `restaurant.py` | `/restaurant` | Plats, ingrédients, charges |
| `forecasting.py` | `/forecasting` | Prévisions IA |
| `anomaly_detection.py` | `/anomaly-detection` | Détection anomalies |
| `bank_reconciliation.py` | `/bank-reconciliation` | Rapprochement bancaire |
| `supplier_scoring.py` | `/supplier-scoring` | Scoring fournisseurs |
| `inventory_intelligence.py` | `/inventory-intelligence` | EOQ, ABC-XYZ |
| `rules_engine.py` | `/rules-engine` | Règles catégorisation |
| `margins.py` | `/margins` | Calcul marges PAMP |
| `capital.py` | `/capital` | Suivi capital/trésorerie |
| `audit.py` | `/audit` | Écarts stock |
| `audit_trail.py` | `/audit-trail` | Historique actions |
| `reports.py` | `/reports` | Exports et rapports |
| `admin.py` | `/admin` | Administration système |
| `maintenance.py` | `/maintenance` | Sauvegardes PostgreSQL |
| `data_quality.py` | `/data-quality` | Qualité données |
| `supply.py` | `/supply` | Plan approvisionnement |
| `analytics.py` | `/analytics` | Statistiques |
| `dashboard.py` | `/dashboard` | KPIs épicerie |
| `eurociel.py` | `/eurociel` | Intégration caisse |
| `newcms.py` | `/newcms` | API mobile/CMS |

### 3.2 Services Finance (core/finance/)

| Service | Fonctionnalités |
|---------|-----------------|
| `anomaly_detection.py` | Z-score, IQR, détection doublons, montants suspects |
| `forecasting.py` | Holt-Winters, lissage exponentiel, prévisions cash-flow |
| `supplier_scoring.py` | Score multi-critères (prix, délais, qualité) |
| `rules_engine.py` | Catégorisation ML, regex, apprentissage progressif |
| `bank_reconciliation.py` | Matching automatique, fuzzy, multi-lignes |
| `margin_calculator.py` | PAMP, marges brutes/nettes |
| `inventory_intelligence.py` | EOQ, classification ABC-XYZ |
| `audit_trail.py` | Event sourcing, traçabilité |

---

## 4. Modules Frontend

### 4.1 Structure Navigation (6 Vues Unifiées)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NAVIGATION PRINCIPALE                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ COCKPIT  │  │OPÉRATIONS│  │ FINANCES │  │RESTAURANT│            │
│  │  Vue 360°│  │ Unifiée  │  │  Unifiée │  │ 14 pages │            │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │
│       │             │             │             │                   │
│       │        ┌────┴────┐   ┌────┴────┐   ┌────┴────┐            │
│       │        │ Pilotage│   │Trésorerie│   │Overview │            │
│       │        │ Factures│   │Transactions│ │Food Cost│            │
│       │        │Catalogue│   │ Comptes  │   │ Plats   │            │
│       │        │  Stock  │   │Rapproch. │   │Ingrédien│            │
│       │        │  Prix   │   │ Imports  │   │  Menus  │            │
│       │        └─────────┘   └─────────┘   └─────────┘            │
│                                                                      │
│  ┌──────────┐  ┌──────────┐                                        │
│  │INTELLIGENCE│ │PARAMÈTRES│                                        │
│  │  Unifiée │  │  3 pages │                                        │
│  └──────────┘  └──────────┘                                        │
│       │             │                                               │
│  ┌────┴────┐   ┌────┴────┐                                        │
│  │Dashboard│   │Audit    │                                        │
│  │  Stock  │   │Règles   │                                        │
│  │Prévisions│  │Alertes  │                                        │
│  │Anomalies│   └─────────┘                                        │
│  │ Scoring │                                                       │
│  │ Marges  │                                                       │
│  └─────────┘                                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Pages Frontend (features/)

| Domaine | Page | Fichier |
|---------|------|---------|
| **Cockpit** | Vue 360° | `CockpitUnifiedPage.jsx` |
| | Morning Brief | `CockpitPage.jsx` |
| **Opérations** | Vue unifiée | `OperationsPage.jsx` |
| | Catalogue | `CatalogPage.jsx` |
| | Import factures | `ImportPage.jsx` |
| | Suivi prix | `PricesPage.jsx` |
| | Mouvements stock | `StockMovementsPage.jsx` |
| | Dashboard épicerie | `DashboardPage.jsx` |
| **Finances** | Vue unifiée | `FinanceUnifiedPage.jsx` |
| | Trésorerie | `FinanceOverview.jsx` |
| | Transactions | `FinanceTransactionsPage.jsx` |
| | Comptes | `FinanceAccountsPage.jsx` |
| | Rapprochement | `BankReconciliationPage.jsx` |
| | Imports | `FinanceImportsPage.jsx` |
| | Règles | `FinanceRulesPage.jsx` |
| | Anomalies finance | `FinanceAnomaliesPage.jsx` |
| | Portefeuille | `PortfolioPage.jsx` |
| **Restaurant** | Overview | `RestaurantOverviewPage.jsx` |
| | Food Cost | `FoodCostAnalysisPage.jsx` |
| | Catalogue plats | `PlatsCatalogPage.jsx` |
| | Ingrédients | `IngredientsPage.jsx` |
| | Menus & coûts | `RestaurantMenusCostsPage.jsx` |
| | Pilotage | `RestaurantDashboard.jsx` |
| | Charges | `RestaurantChargesPage.jsx` |
| | Consommations | `RestaurantConsumptionPage.jsx` |
| | Liens épicerie | `RestaurantEpicerieLinkPage.jsx` |
| | Stock restaurant | `RestaurantStockMovementsPage.jsx` |
| | Prix restaurant | `RestaurantPriceHistoryComparisonPage.jsx` |
| | Tendances | `RestaurantPriceTrends.jsx` |
| | Prévisions resto | `ForecastsPage.jsx` |
| **Intelligence** | Vue unifiée | `IntelligenceUnifiedPage.jsx` |
| | Dashboard IA | `IntelligencePage.jsx` |
| | Stock intelligent | `InventoryIntelligencePage.jsx` |
| | Prévisions | `ForecastPage.jsx` |
| | Anomalies | `AnomaliesPage.jsx` |
| | Scoring overview | `SupplierScoringOverviewPage.jsx` |
| | Liste fournisseurs | `SuppliersListPage.jsx` |
| | Détails fournisseur | `SupplierDetailsPage.jsx` |
| | Critères scoring | `ScoringCriteriaPage.jsx` |
| | Alertes fournisseurs | `SupplierAlertsPage.jsx` |
| | Marges | `MarginsPage.jsx` |
| **Admin** | Audit Trail | `AuditTrailPage.jsx` |
| | Administration | `AdminPage.jsx` |
| | Maintenance | `MaintenancePage.jsx` |
| | Rapports | `ReportsPage.jsx` |

### 4.3 Composants UI Réutilisables

| Catégorie | Composants |
|-----------|------------|
| **Layout** | `CommandBar`, `Sidebar`, `TabView`, `ProgressiveDisclosure`, `AdaptiveDensity` |
| **Data Display** | `DataTable`, `Card`, `Badge`, `Tooltip`, `Grid`, `Skeleton` |
| **Feedback** | `Toast`, `LoadingOverlay`, `NotificationCenter`, `ConfirmDialog`, `EmptyState`, `ErrorBoundary`, `RetryableError` |
| **Inputs** | `Modal`, `FiltersDrawer`, `Button` |
| **Accessibility** | `SkipLinks`, `AccessibleModal` |
| **Animations** | `AnimatedComponents`, `Transitions` |
| **Mobile** | `MobileCameraScanner`, `MobileDataTable`, `SwipeableRow` |

### 4.4 Hooks Personnalisés

| Hook | Description |
|------|-------------|
| `useAuth` | Authentification et session |
| `useFinance` | Opérations financières |
| `useFinanceCategories` | Catégories comptables |
| `useFinanceImports` | Import relevés |
| `useInvoiceImport` | Import factures |
| `useStock` | Mouvements stock |
| `useProducts` | CRUD produits |
| `useDashboard` | Données dashboard |
| `usePriceHistory` | Historique prix |
| `useAudit` | Écarts stock |
| `useAdmin` | Administration |
| `useMaintenance` | Sauvegardes |
| `useOptimistic` | Updates optimistes |
| `useVirtualization` | Listes virtualisées |
| `usePrefetch` | Préchargement données |
| `useHotkeys` | Raccourcis clavier |
| `useClickOutside` | Détection clic extérieur |
| `useDebounce` | Debouncing |
| `useLocalStorage` | Persistance locale |
| `useMediaQuery` | Responsive |
| `usePersistedFilters` | Filtres persistants |
| `useGestures` | Gestes tactiles |
| `useCommandBarLiveSuggestions` | Suggestions command bar |
| `useAccessibility` | Accessibilité |

---

## 5. Base de Données

### 5.1 Schéma Multi-Tenant

```sql
-- Tenants principaux
tenants: id=1 (Épicerie HQ), id=2 (Restaurant HQ)

-- Tables partagées avec tenant_id
- produits, produits_barcodes, produits_price_history
- mouvements_stock
- restaurants, ingredients, plats, plat_ingredients
- finance_accounts, finance_transactions, finance_bank_statement_lines
- detected_anomalies, forecast_cache
- supplier_scores, finance_rules
```

### 5.2 Tables Principales

| Domaine | Tables |
|---------|--------|
| **Produits** | `produits`, `produits_barcodes`, `produits_price_history`, `mouvements_stock` |
| **Restaurant** | `restaurants`, `ingredients`, `plats`, `plat_ingredients`, `plat_equivalences`, `bundle_items`, `categories`, `ingredient_conditionnements`, `productions` |
| **Finance** | `finance_accounts`, `finance_transactions`, `finance_bank_statement_lines`, `finance_bank_invoice_matches`, `finance_rules`, `finance_categories`, `finance_cost_centers` |
| **Intelligence** | `detected_anomalies`, `forecast_cache`, `supplier_scores`, `supplier_score_history` |
| **Factures** | `processed_invoices`, `fact_invoices` |
| **Capital** | `capital_snapshot` |
| **Système** | `tenants`, `app_users`, `audit_events` |

---

## 6. Services Externes

### 6.1 n8n (Workflows)

- **Port:** 5678
- **Données:** `n8n_data/`
- **Cas d'usage:** Automatisation imports, notifications, synchronisations

### 6.2 Ollama (LLM Local)

- **Port:** 11434
- **Données:** `ollama_data/`
- **Cas d'usage:** Extraction intelligente de factures, classification

### 6.3 Blocks (Service UI)

- **Dockerfile:** `blocks/Dockerfile`
- **Script:** `blocks/start.sh`

---

## 7. Scripts Utilitaires

| Script | Description |
|--------|-------------|
| `scripts/import_bank_statements.py` | Import relevés bancaires |
| `scripts/seed_restaurant.py` | Données de démo restaurant |
| `scripts/bootstrap_local.py` | Initialisation locale complète |
| `scripts/start_dev_env.sh` | Démarrage environnement dev |
| `scripts/run-tests.sh` | Exécution tests automatisés |

---

## 8. Configuration Docker

### 8.1 Services Principaux

```yaml
services:
  db:          # PostgreSQL 16
  api:         # FastAPI (backend)
  frontend:    # Vite + React
  app:         # Streamlit legacy (optionnel)
  n8n:         # Workflows
  ollama:      # LLM local
```

### 8.2 Commandes Make

| Commande | Description |
|----------|-------------|
| `make start-dev` | Démarrage complet développement |
| `make rebuild` | Reconstruction conteneurs |
| `make down` | Arrêt services |
| `make import-data` | Import CSV produits |
| `make seed-restaurant` | Données démo restaurant |
| `make bootstrap-local` | Initialisation locale |
| `make refresh-reports` | Réimport relevés PDF |

---

## 9. Tests

### 9.1 Structure Tests

```
tests/
├── test_finance_api.py
├── test_finance_dashboard.py
├── test_anomaly_detection_api.py
├── test_forecasting_api.py
└── conftest.py

backend/tests/
├── conftest.py
├── test_finance_api.py
└── test_finance_dashboard.py
```

### 9.2 Exécution

```bash
# Installation dépendances
pip install -r requirements-dev.txt

# Lancement tests
pytest

# Avec script complet
./scripts/run-tests.sh
```

---

## 10. Environnement

### 10.1 Variables d'Environnement

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | URL connexion PostgreSQL |
| `POSTGRES_*` | Credentials PostgreSQL |
| `VITE_API_BASE_URL` | URL API pour frontend |
| `SECRET_KEY` | Clé JWT |
| `PG_DUMP_PATH` / `PSQL_PATH` | Chemins binaires PostgreSQL |
| `BACKUP_DIR` | Dossier sauvegardes |

### 10.2 Fichiers Configuration

- `.env` : Variables développement
- `.env.prod` : Variables production
- `.env.test` : Variables tests
- `alembic.ini` : Configuration migrations
- `docker-compose.yml` : Orchestration services

---

## 11. État des Fonctionnalités

### 11.1 Fonctionnalités Implémentées

- Gestion catalogue multi-tenant
- Import factures PDF (METRO, Promocash, Brake)
- Historique prix fournisseurs
- Mouvements de stock avec triggers
- Dashboard épicerie avec KPIs
- Cockpit 360° unifié
- Trésorerie et rapprochement bancaire
- Détection d'anomalies (Z-score, doublons)
- Prévisions (Holt-Winters)
- Scoring fournisseurs multi-critères
- Règles de catégorisation avec ML
- Restaurant: plats, ingrédients, menus, charges
- Analyse Food Cost
- Audit trail et traçabilité
- Sauvegardes PostgreSQL

### 11.2 En Cours de Développement

- Module newCMS (API mobile)
- Composants mobile (MobileCameraScanner, SwipeableRow)
- Intégration Ollama pour extraction IA
- Workflows n8n avancés

---

**Document généré automatiquement - Décembre 2025**
