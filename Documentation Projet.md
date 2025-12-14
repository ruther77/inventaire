# Documentation Projet - Plateforme Multi-Tenant

**Version consolidée — 11 Décembre 2025**

Ce document est la **référence unique** du projet. Il regroupe :
- Index technique complet
- Cartographie des dépendances
- Conventions de code
- Scénarios utilisateur
- Roadmap projet

---

## Table des Matières

1. [Vue d'Ensemble](#1-vue-densemble)
2. [Cartographie Architecture](#2-cartographie-architecture)
3. [Arborescence des Fichiers](#3-arborescence-des-fichiers)
4. [Flux de Données](#4-flux-de-données)
5. [Base de Données](#5-base-de-données)
6. [API Client Frontend](#6-api-client-frontend)
7. [Conventions & Standards](#7-conventions--standards)
8. [Scénarios Utilisateur](#8-scénarios-utilisateur)
9. [Roadmap & Priorités](#9-roadmap--priorités)
10. [État du Projet](#10-état-du-projet)
11. [Historique des Avancées](#11-historique-des-avancées)
12. [Vision UX Next-Gen 2025](#12-vision-ux-next-gen-2025)

---

# 1. Vue d'Ensemble

## 1.1 Description du Projet

Plateforme de gestion multi-tenant pour la restauration et l'épicerie comprenant :
- Gestion de trésorerie et finance
- Gestion des stocks et inventaires
- Système de facturation et extraction PDF
- Intelligence business et analytics avancés

## 1.2 Stack Technique

| Composant | Technologie |
|-----------|-------------|
| Backend | FastAPI 0.111+, Python 3.11+, Pydantic 2 |
| Frontend | React 18, Vite 5, TanStack Query, Tailwind CSS |
| Base de données | PostgreSQL 16 |
| Authentification | JWT (PyJWT), OAuth2 |
| Conteneurisation | Docker, Docker Compose |

## 1.3 Métriques Clés (Décembre 2025)

| Métrique | Valeur |
|----------|--------|
| Routers API Backend | **28** |
| Modules Core | **26** + 14 (finance/) |
| Hooks Frontend | **38** |
| Features Frontend | **20** domaines |
| Tables SQL | ~43 |
| Endpoints API | ~180 |

---

# 2. Cartographie Architecture

## 2.1 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    UTILISATEUR                                       │
│                                         │                                            │
│                                         ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────────────┐   │
│  │                              FRONTEND (React 18)                              │   │
│  │                                                                               │   │
│  │   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │   │
│  │   │Épicerie │  │Restaurant│  │Trésorerie│  │Factures │  │Intelligence│        │   │
│  │   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘           │   │
│  │        │            │            │            │            │                  │   │
│  │        └────────────┴────────────┴────────────┴────────────┘                  │   │
│  │                                   │                                            │   │
│  │                          ┌────────┴────────┐                                  │   │
│  │                          │   api/client.js │  (130+ fonctions)                │   │
│  │                          └────────┬────────┘                                  │   │
│  └───────────────────────────────────┼──────────────────────────────────────────┘   │
│                                      │                                               │
│                             HTTP REST API (JSON)                                     │
│                                      │                                               │
│  ┌───────────────────────────────────┼──────────────────────────────────────────┐   │
│  │                              BACKEND (FastAPI)                                │   │
│  │                                   │                                           │   │
│  │                          ┌────────┴────────┐                                  │   │
│  │                          │    main.py      │                                  │   │
│  │                          │   (28 routers)  │                                  │   │
│  │                          └────────┬────────┘                                  │   │
│  │                                   │                                           │   │
│  │   ┌─────────┐  ┌─────────┐  ┌────┴────┐  ┌─────────┐  ┌─────────┐           │   │
│  │   │auth.py  │  │finance.py│  │invoices │  │cockpit  │  │intelligence│        │   │
│  │   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘           │   │
│  │        │            │            │            │            │                  │   │
│  │        └────────────┴────────────┴────────────┴────────────┘                  │   │
│  │                                   │                                           │   │
│  │                          ┌────────┴────────┐                                  │   │
│  │                          │    services/    │                                  │   │
│  │                          └────────┬────────┘                                  │   │
│  └───────────────────────────────────┼──────────────────────────────────────────┘   │
│                                      │                                               │
│  ┌───────────────────────────────────┼──────────────────────────────────────────┐   │
│  │                                 CORE (40 modules)                             │   │
│  │                                   │                                           │   │
│  │   ┌─────────────────┐    ┌───────┴───────┐    ┌─────────────────┐            │   │
│  │   │ invoice_        │    │ data_         │    │ inventory_      │            │   │
│  │   │ extractor.py    │    │ repository.py │    │ service.py      │            │   │
│  │   └────────┬────────┘    └───────┬───────┘    └────────┬────────┘            │   │
│  │            │                     │                     │                      │   │
│  │            └─────────────────────┼─────────────────────┘                      │   │
│  │                                  │                                            │   │
│  │                         ┌────────┴────────┐                                   │   │
│  │                         │  core/finance/  │  (14 modules avancés)             │   │
│  │                         └─────────────────┘                                   │   │
│  └──────────────────────────────────┼────────────────────────────────────────────┘   │
│                                     │                                                │
│                              SQL (psycopg2)                                          │
│                                     │                                                │
│  ┌──────────────────────────────────┼────────────────────────────────────────────┐   │
│  │                            PostgreSQL 16                                       │   │
│  │                                  │                                             │   │
│  │   ┌────────────┐  ┌────────────┐│┌────────────┐  ┌────────────┐              │   │
│  │   │ finance_*  │  │ produits   │││ invoices   │  │ tenants    │              │   │
│  │   │ (15 tables)│  │ mouvements │││ (5 tables) │  │ users      │              │   │
│  │   └────────────┘  └────────────┘│└────────────┘  └────────────┘              │   │
│  └──────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Domaines Fonctionnels

```
                    ┌──────────────────────┐
                    │   PLATEFORME MULTI   │
                    │       TENANT         │
                    └──────────┬───────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   ÉPICERIE    │    │  RESTAURANT   │    │  TRÉSORERIE   │
│               │    │               │    │               │
│ • Catalogue   │    │ • Recettes    │    │ • Transactions│
│ • Inventaire  │    │ • Coûts plats │    │ • Relevés     │
│ • Fournisseurs│    │ • Marges      │    │ • Rapprochmt  │
│ • Commandes   │    │ • POS/Ventes  │    │ • Capital     │
└───────────────┘    └───────────────┘    └───────────────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    INTELLIGENCE      │
                    │                      │
                    │ • Forecasting        │
                    │ • Anomaly Detection  │
                    │ • Supplier Scoring   │
                    │ • Margin Calculator  │
                    │ • Inventory Intel    │
                    └──────────────────────┘
```

---

# 3. Arborescence des Fichiers

## 3.1 Frontend (`frontend/src/`)

```
frontend/src/
│
├── App.jsx                          # Point d'entrée, providers
├── main.jsx                         # Bootstrap React
│
├── api/
│   └── client.js                    # 130+ fonctions API Axios
│
├── app/
│   ├── routes.jsx                   # Définition routes
│   ├── SidebarNav.jsx               # Navigation latérale
│   ├── TopBar.jsx                   # Barre supérieure
│   └── AppShell.jsx                 # Layout principal
│
├── components/
│   ├── ui/                          # Composants génériques
│   │   ├── Button.jsx
│   │   ├── Card.jsx
│   │   ├── DataTable.jsx
│   │   ├── Modal.jsx
│   │   ├── Select.jsx
│   │   ├── Input.jsx
│   │   ├── Skeleton.jsx
│   │   ├── EmptyState.jsx
│   │   └── ...
│   ├── layout/                      # Layout components
│   ├── feedback/                    # Toast, Loading
│   ├── animations/                  # Framer Motion
│   └── accessibility/               # A11y components
│
├── context/
│   ├── AuthContext.jsx              # Authentification
│   └── TenantContext.jsx            # Multi-tenant state
│
├── hooks/                           # 38 hooks React
│   ├── index.js                     # Exports centralisés
│   ├── useAuth.js                   # Authentification
│   ├── useProducts.js               # Produits catalogue
│   ├── useFinance.js                # Transactions finance
│   ├── useFinanceCategories.js      # Catégories finance
│   ├── useStock.js                  # Mouvements stock
│   ├── useRestaurant.js             # Données restaurant
│   ├── useDashboard.js              # Métriques dashboard
│   ├── usePriceHistory.js           # Historique prix
│   ├── useInvoiceImport.js          # Import factures
│   ├── useSupplyPlan.js             # Plan approvisionnement
│   ├── useBankReconciliation.js     # Rapprochement bancaire
│   ├── useAuditTrail.js             # Piste d'audit
│   ├── useInventoryIntelligence.js  # Intelligence inventaire
│   ├── useForecasting.js            # Prévisions
│   ├── useAnomalyDetection.js       # Détection anomalies
│   ├── useMargins.js                # Calcul marges
│   ├── useSupplierScoring.js        # Scoring fournisseurs
│   ├── useCockpit.js                # Vue cockpit
│   ├── usePrefetch.js               # Préchargement
│   ├── useAccessibility.js          # A11y
│   ├── useOptimistic.js             # Updates optimistes
│   ├── useVirtualization.js         # Listes longues
│   └── ...
│
└── features/                        # 20 domaines
    ├── admin/
    │   ├── AdminPage.jsx
    │   └── AuditTrailPage.jsx
    ├── auth/
    │   └── LoginPage.jsx
    ├── catalog/
    │   └── CatalogPage.jsx
    ├── cockpit/
    │   └── CockpitPage.jsx
    ├── dashboard/
    │   ├── DashboardPage.jsx
    │   └── components/
    ├── finance/
    │   ├── FinanceOverview.jsx
    │   ├── FinanceTransactionsPage.jsx
    │   ├── FinanceAccountsPage.jsx
    │   ├── BankReconciliationPage.jsx
    │   └── components/
    ├── intelligence/
    │   ├── InventoryIntelligencePage.jsx
    │   ├── ForecastPage.jsx
    │   ├── AnomaliesPage.jsx
    │   ├── MarginsPage.jsx
    │   └── ScoringPage.jsx
    ├── invoices/
    │   ├── ImportPage.jsx
    │   └── components/
    ├── maintenance/
    │   └── MaintenancePage.jsx
    ├── portfolio/
    │   └── PortfolioPage.jsx
    ├── pos/
    │   └── POSPage.jsx
    ├── prices/
    │   └── PriceHistoryPage.jsx
    ├── reports/
    │   └── ReportsPage.jsx
    ├── restaurant/
    │   ├── RestaurantDashboard.jsx
    │   ├── RecipesPage.jsx
    │   ├── CostsPage.jsx
    │   ├── ForecastsPage.jsx
    │   └── RestaurantChargesPage.jsx
    ├── stock/
    │   └── StockPage.jsx
    ├── supply/
    │   └── SupplyPlanPage.jsx
    └── treasury/
        └── TreasuryPage.jsx
```

## 3.2 Backend (`backend/`)

```
backend/
│
├── main.py                          # FastAPI app, routers mount
│
├── api/                             # 28 routers
│   ├── admin.py                     # Administration
│   ├── analytics.py                 # Analytics
│   ├── anomaly_detection.py         # /anomaly-detection/*
│   ├── audit.py                     # /audit/*
│   ├── audit_trail.py               # /audit-trail/*
│   ├── auth.py                      # /auth/*
│   ├── bank_reconciliation.py       # /bank-reconciliation/*
│   ├── capital.py                   # /capital/*
│   ├── catalog.py                   # /catalog/*
│   ├── cockpit.py                   # /cockpit/*
│   ├── dashboard.py                 # /dashboard/*
│   ├── data_quality.py              # /data-quality/*
│   ├── eurociel.py                  # /eurociel/*
│   ├── finance.py                   # /finance/*
│   ├── forecasting.py               # /forecasting/*
│   ├── inventory_intelligence.py    # /inventory-intelligence/*
│   ├── invoices.py                  # /invoices/*
│   ├── maintenance.py               # /maintenance/*
│   ├── margins.py                   # /margins/*
│   ├── prices.py                    # /prices/*
│   ├── reports.py                   # /reports/*
│   ├── restaurant.py                # /restaurant/*
│   ├── routes.py                    # Routes index
│   ├── rules_engine.py              # /rules-engine/*
│   ├── stock.py                     # /stock/*
│   ├── supplier_scoring.py          # /supplier-scoring/*
│   └── supply.py                    # /supply/*
│
├── middleware/
│   ├── __init__.py                  # Middlewares registration
│   ├── auth.py                      # JWT validation
│   ├── performance.py               # Métriques performance
│   ├── request_context.py           # Request context
│   └── response_wrapper.py          # Response wrapper
│
├── schemas/                         # Pydantic models
│   ├── auth.py
│   ├── finance.py
│   ├── invoices.py
│   ├── capital.py
│   ├── prices.py
│   └── ...
│
└── services/
    ├── auth.py
    ├── invoices.py
    ├── dashboard.py
    ├── catalog.py
    ├── stock.py
    ├── capital.py
    ├── finance/
    │   ├── transactions.py
    │   ├── rules.py
    │   ├── stats.py
    │   └── dedupe.py
    ├── importers/
    │   └── bank_statement_csv.py
    └── restaurant/
        └── mappings.py
```

## 3.3 Core (`core/`)

```
core/
│
├── __init__.py
├── settings.py                      # Configuration
├── database_url.py                  # DB connection string
│
├── data_repository.py               # SQL queries centralisées (~850 lignes)
├── catalog_repository.py            # Catalogue produits
├── catalog_sql_repository.py        # SQL catalogue
│
├── invoice_extractor.py             # Extraction PDF (~1123 lignes)
├── invoice_workflow.py              # Workflow factures
├── pdf_utils.py                     # Utilitaires PDF
├── products_loader.py               # Chargement produits
├── product_input.py                 # Input produits
├── vendor_categories.py             # Catégories fournisseurs
│
├── inventory_service.py             # Gestion inventaire
├── inventory_classification.py      # Classification ABC-XYZ
├── inventory_costing.py             # Calcul coûts FIFO
├── inventory_forecast.py            # Prévisions stock
│
├── price_history_service.py         # Historique prix
├── price_correction_service.py      # Correction prix
├── product_service.py               # Service produits
├── restaurant_costs.py              # Coûts restaurant
├── cart_normalizer.py               # Normalisation panier
├── consolidation_loader.py          # Chargement consolidation
│
├── tenant_service.py                # Multi-tenant
├── user_service.py                  # Gestion utilisateurs
├── backup_manager.py                # Sauvegardes
├── event_handlers.py                # Event handlers
│
├── parsers/                         # Parseurs spécialisés
│
└── finance/                         # 14 modules finance avancés
    ├── __init__.py
    ├── insights.py                  # Analytics finance
    ├── reconciliation.py            # Rapprochement simple
    ├── analytic_accounting.py       # Comptabilité analytique
    ├── anomaly_detection.py         # Détection anomalies
    ├── audit_trail.py               # Piste d'audit
    ├── bank_reconciliation.py       # Rapprochement bancaire
    ├── event_sourcing.py            # Event sourcing
    ├── forecasting.py               # Prévisions cash-flow
    ├── inventory_intelligence.py    # EOQ, safety stock
    ├── margin_calculator.py         # Calcul marges PAMP
    ├── rules_engine.py              # Moteur de règles
    ├── supplier_scoring.py          # Scoring fournisseurs
    └── transaction_line_defaults.py # Défauts lignes
```

---

# 4. Flux de Données

## 4.1 Authentification

L'API supporte deux modes d'authentification :

### Mode 1 : Cookies httpOnly (recommandé pour navigateurs)

| Endpoint | Description |
|----------|-------------|
| `POST /auth/login` | Login avec cookies httpOnly (access + refresh) |
| `POST /auth/refresh` | Rafraîchir le token via refresh cookie |
| `POST /auth/logout` | Déconnexion et révocation des tokens |

**Avantages** : Protection XSS, rotation automatique, gestion transparente.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    FLUX AUTHENTIFICATION (Cookies)                       │
└─────────────────────────────────────────────────────────────────────────┘

   ┌─────────┐     1. POST /auth/login      ┌─────────┐
   │ Browser │ ─────────────────────────────▶│ auth.py │
   │         │     {username, password}      │ (API)   │
   └─────────┘                               └────┬────┘
        ▲                                         │
        │                                         │ 2. validate_user()
        │                                         ▼
        │                                   ┌─────────┐
        │     3. Set-Cookie: access_token   │ Create  │
        │        Set-Cookie: refresh_token  │ Tokens  │
        │        (httpOnly, Secure)         └─────────┘
        └─────────────────────────────────────────┘

   ┌─────────┐     4. Cookie: access_token  ┌─────────┐
   │ Browser │ ─────────────────────────────▶│middleware│
   │         │     (automatique)             │ security│
   └─────────┘                               └────┬────┘
        │                                         │
        │     5. Response                         │ decode JWT
        └─────────────────────────────────────────┘

   ┌─────────┐     6. POST /auth/refresh    ┌─────────┐
   │ Browser │ ─────────────────────────────▶│ auth.py │
   │         │     Cookie: refresh_token     │ (API)   │
   └─────────┘                               └────┬────┘
        ▲                                         │
        │     7. New access_token cookie          │ Rotation
        │        New refresh_token cookie         │ + Revoke old
        └─────────────────────────────────────────┘
```

### Mode 2 : Bearer Token (pour API clients)

| Endpoint | Description |
|----------|-------------|
| `POST /auth/token` | Obtenir un bearer token OAuth2 |

**Usage** : Clients API, scripts, intégrations.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    FLUX AUTHENTIFICATION (Bearer)                         │
└──────────────────────────────────────────────────────────────────────────┘

   ┌─────────┐     1. POST /auth/token       ┌─────────┐
   │ Client  │ ─────────────────────────────▶│ auth.py │
   │  API    │     {username, password}       │ (API)   │
   └─────────┘                               └────┬────┘
        ▲                                         │
        │     2. { access_token: "..." }          │
        └─────────────────────────────────────────┘

   ┌─────────┐     3. Authorization: Bearer  ┌─────────┐
   │ Client  │ ─────────────────────────────▶│middleware│
   │  API    │     <token>                   │ security│
   └─────────┘                               └────┬────┘
        │                                         │
        │     4. Response                         │ decode JWT
        └─────────────────────────────────────────┘
```

## 4.2 Transactions Finance

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     FLUX TRANSACTIONS FINANCE                            │
└──────────────────────────────────────────────────────────────────────────┘

┌────────────────┐                              ┌────────────────┐
│FinanceTransac- │  1. useFinance()             │ TanStack       │
│ tionsPage.jsx  │─────────────────────────────▶│ Query Cache    │
└────────────────┘                              └───────┬────────┘
        ▲                                               │
        │                                               │ 2. searchFinanceTransactions()
        │ 8. Render table                               ▼
        │                                        ┌────────────────┐
        │                                        │ api/client.js  │
        │                                        │ POST /finance/ │
        │                                        │ transactions/  │
        │                                        │ search         │
        │                                        └───────┬────────┘
        │                                               │
        │                                               │ 3. HTTP POST
        │                                               ▼
        │                                        ┌────────────────┐
        │                                        │ finance.py     │
        │                                        │ (API router)   │
        │                                        └───────┬────────┘
        │                                               │
        │                                               │ 4. search_transactions()
        │                                               ▼
        │                                        ┌────────────────┐
        │                                        │ transactions.py│
        │                                        │ (service)      │
        │                                        └───────┬────────┘
        │                                               │
        │                                               │ 5. SQL Query
        │                                               ▼
        │                                        ┌────────────────┐
        │                                        │finance_        │
        │  7. JSON Response                      │transactions    │
        └────────────────────────────────────────│ (PostgreSQL)   │
                                                 └────────────────┘
```

## 4.3 Import Factures

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        FLUX IMPORT FACTURES                              │
└──────────────────────────────────────────────────────────────────────────┘

┌────────────┐    1. File Upload (PDF)    ┌────────────┐
│ ImportPage │───────────────────────────▶│ invoices.py│
│    .jsx    │    POST /invoices/extract  │  (API)     │
└────────────┘                            └─────┬──────┘
      ▲                                         │
      │                                         │ 2. process_upload()
      │                                         ▼
      │                                   ┌────────────┐
      │                                   │invoices.py │
      │                                   │ (service)  │
      │                                   └─────┬──────┘
      │                                         │
      │                                         │ 3. extract_invoice()
      │                                         ▼
      │   ┌─────────────────────────────────────────────────────────┐
      │   │                  invoice_extractor.py                    │
      │   │                                                          │
      │   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
      │   │  │  pdf_utils   │  │  products_   │  │   vendor_    │  │
      │   │  │    .py       │  │  loader.py   │  │  categories  │  │
      │   │  │              │  │              │  │     .py      │  │
      │   │  │ • read_pdf() │  │ • match()    │  │ • classify() │  │
      │   │  └──────────────┘  └──────────────┘  └──────────────┘  │
      │   └─────────────────────────────────────────────────────────┘
      │                                         │
      │                                         │ 4. save_invoice()
      │                                         ▼
      │                                   ┌────────────┐
      │                                   │data_       │
      │                                   │repository  │
      │                                   └─────┬──────┘
      │                                         │
      │   5. JSON Response                      │ 5. INSERT INTO:
      └─────────────────────────────────────────┘   - processed_invoices
                                                    - produits_price_history
                                                    - mouvements_stock
```

## 4.4 Intelligence (Forecasting)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        FLUX FORECASTING                                  │
└──────────────────────────────────────────────────────────────────────────┘

┌────────────┐    1. useForecasting()     ┌────────────┐
│ForecastPage│───────────────────────────▶│  Hook      │
│   .jsx     │                            │ TanStack   │
└────────────┘                            └─────┬──────┘
      ▲                                         │
      │                                         │ 2. fetchForecastingSummary()
      │                                         ▼
      │                                   ┌────────────┐
      │                                   │forecasting │
      │                                   │.py (API)   │
      │                                   └─────┬──────┘
      │                                         │
      │                                         │ 3. get_summary()
      │                                         ▼
      │   ┌─────────────────────────────────────────────────────────┐
      │   │              core/finance/forecasting.py                 │
      │   │                                                          │
      │   │  • ForecastingEngine                                     │
      │   │  • CashFlowForecast                                      │
      │   │  • SalesProjection                                       │
      │   │  • SeasonalityAnalysis                                   │
      │   └─────────────────────────────────────────────────────────┘
      │                                         │
      │   4. JSON Response                      │
      └─────────────────────────────────────────┘
```

---

# 5. Base de Données

## 5.1 Schéma Relationnel Principal

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              SCHEMA RELATIONNEL                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   tenants   │
                              │─────────────│
                              │ id (PK)     │
                              │ code        │
                              │ name        │
                              └──────┬──────┘
                                     │
                                     │ 1:N
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
        ▼                            ▼                            ▼
┌─────────────┐             ┌─────────────┐             ┌─────────────┐
│   users     │             │ finance_    │             │  produits   │
│─────────────│             │ accounts    │             │─────────────│
│ id (PK)     │             │─────────────│             │ id (PK)     │
│ tenant_id   │             │ id (PK)     │             │ tenant_id   │
│ username    │             │ tenant_id   │             │ nom         │
│ role        │             │ name        │             │ categorie   │
│ password    │             │ iban        │             │ unite       │
└─────────────┘             │ bank_name   │             │ prix_achat  │
                            └─────────────┘             │ prix_vente  │
                                                        └──────┬──────┘
                                                               │
                                                               │ 1:N
                                    ┌──────────────────────────┼──────────────────┐
                                    │                          │                  │
                                    ▼                          ▼                  ▼
                           ┌─────────────────┐     ┌─────────────────┐   ┌─────────────────┐
                           │mouvements_stock │     │produits_price_  │   │produits_        │
                           │─────────────────│     │history          │   │barcodes         │
                           │ id (PK)         │     │─────────────────│   │─────────────────│
                           │ produit_id (FK) │     │ id (PK)         │   │ id (PK)         │
                           │ quantite        │     │ produit_id (FK) │   │ produit_id (FK) │
                           │ type            │     │ prix            │   │ barcode         │
                           │ date_mouvement  │     │ date            │   │ type            │
                           │ source          │     │ source          │   └─────────────────┘
                           └─────────────────┘     └─────────────────┘
```

## 5.2 Tables Finance

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                FINANCE TABLES                                        │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
│ finance_        │            │ finance_        │            │ finance_        │
│ transactions    │            │ categories      │            │ rules           │
│─────────────────│            │─────────────────│            │─────────────────│
│ id (PK)         │            │ id (PK)         │            │ id (PK)         │
│ entity_id       │────────────│ entity_id       │            │ entity_id       │
│ category_id (FK)│──────────▶ │ nom             │            │ pattern         │
│ amount          │            │ type            │            │ category_id     │
│ date            │            │ parent_id (FK)  │───┐        │ priority        │
│ label           │            │ icon            │   │        │ active          │
│ counterparty    │            └─────────────────┘   │        └─────────────────┘
│ bank_ref        │                                  │
│ reconciled      │                                  └────▶ (self-reference hierarchy)
└─────────────────┘

┌─────────────────┐            ┌─────────────────┐
│ finance_        │            │ bank_           │
│ reconciliations │            │ statements      │
│─────────────────│            │─────────────────│
│ id (PK)         │            │ id (PK)         │
│ transaction_id  │            │ account_id      │
│ invoice_id      │            │ date            │
│ match_score     │            │ balance         │
│ created_at      │            │ currency        │
└─────────────────┘            └─────────────────┘
```

## 5.3 Tables Restaurant

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              RESTAURANT TABLES (tenant_id=2)                         │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   restaurants   │     │     plats       │     │   ingredients   │
│─────────────────│     │─────────────────│     │─────────────────│
│ id (PK)         │◀────│ restaurant_id   │     │ id (PK)         │
│ tenant_id       │     │ id (PK)         │     │ tenant_id       │
│ nom             │     │ tenant_id       │     │ nom (UNIQUE)    │
│ code (UNIQUE)   │     │ nom             │     │ unite_base      │
└─────────────────┘     │ type (dish/     │     │ etat            │
                        │ beverage/bundle)│     │ tva_pct         │
                        │ prix_vente_ttc  │     └────────┬────────┘
                        │ tva_pct         │              │
                        │ portions_par_   │              │
                        │  batch          │              │
                        │ poids_portion_g │              │
                        │ actif           │              │
                        └────────┬────────┘              │
                                 │                       │
                                 │ N:M                   │
                                                       ▼                                     ▼
                        ┌─────────────────────────────────┐
                        │       plat_ingredients          │
                        │─────────────────────────────────│
                        │ id (PK)                         │
                        │ plat_id (FK) ──▶ plats          │
                        │ ingredient_id (FK) ──▶ ingredients
                        │ quantite_batch                  │
                        │ UNIQUE(plat_id, ingredient_id)  │
                        └─────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│plat_equivalences│     │   bundle_items  │     │   categories    │
│─────────────────│     │─────────────────│     │─────────────────│
│ plat_id (FK)    │     │ bundle_id (FK)  │     │ id (PK)         │
│ ingredient_id   │     │ item_plat_id    │     │ nom (UNIQUE)    │
│ qte_ingredient  │     │ quantite        │     └─────────────────┘
└─────────────────┘     └─────────────────┘              │
(boissons→stock)        (formules→composants)           │
                                                                                              ▼
                                                ┌─────────────────┐
                                                │ plat_categories │
                                                │─────────────────│
                                                │ plat_id (FK)    │
                                                │ categorie_id(FK)│
                                                └─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│ stock_          │     │ stock_          │
│ emplacements    │     │ mouvements      │
│─────────────────│     │─────────────────│
│ id (PK)         │◀────│ emplacement_id  │
│ nom (Cuisine,   │     │ ingredient_id   │
│      Bar)       │     │ qte (signée)    │
└─────────────────┘     │ ref_type        │
                        │ ref_doc         │
                        └─────────────────┘

Données actuelles : 77 plats, 39 ingrédients, 52 recettes, 7 catégories
```

### Vues Restaurant

| Vue | Description |
|-----|-------------|
| `v_bom_dish` | BOM des plats (type='dish') |
| `v_bom_beverage` | BOM des boissons (type='beverage') |
| `v_bom_bundle` | BOM des formules (type='bundle') |
| `v_bom_unifie` | Union de tous les BOM |
| `v_bundle_explode` | Formules éclatées en composants |
| `v_bundle_equivalents` | Équivalences ingrédients des bundles |
| `v_frigo_cuisine` | Portions disponibles en cuisine |
| `v_frigo_bar` | Portions disponibles au bar |
| `v_portions_vendables` | Portions vendables par emplacement |

## 5.4 Mapping Entity/Tenant

| entity_id | tenant_id | Code | Description |
|-----------|-----------|------|-------------|
| 1 | 1 | epicerie | Épicerie principale |
| 2 | 4 | intelligence | Restaurant / Intelligence |

**Conversion** : `entity_id = 2 if tenant_id == 4 else tenant_id`

---

# 6. API Client Frontend

## 6.1 Configuration

**Fichier** : `frontend/src/api/client.js`

```javascript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
});
```

## 6.2 Fonctions par Domaine (130+)

### Catalogue & Produits
| Fonction | Endpoint |
|----------|----------|
| `fetchProducts` | GET /catalog/products |
| `createProduct` | POST /catalog/products |
| `updateProductRequest` | PUT /catalog/products/{id} |
| `deleteProductRequest` | DELETE /catalog/products/{id} |
| `lookupProductByBarcode` | GET /catalog/products/barcode/{code} |
| `fetchCategories` | GET /catalog/categories |
| `fetchVendors` | GET /catalog/vendors |
| `fetchInventorySummary` | GET /dashboard/inventory-summary |

### Stock & Supply
| Fonction | Endpoint |
|----------|----------|
| `fetchSupplyPlan` | GET /supply/plan |
| `fetchStockMovements` | GET /stock/movements |
| `fetchStockSummary` | GET /stock/movements/summary |
| `fetchStockTimeseries` | GET /stock/movements/timeseries |

### Factures
| Fonction | Endpoint |
|----------|----------|
| `extractInvoiceFromFile` | POST /invoices/extract |
| `importInvoiceLines` | POST /invoices/import |
| `fetchInvoiceHistory` | GET /invoices/history |
| `downloadInvoiceFile` | GET /invoices/{id}/file |

### Finance
| Fonction | Endpoint |
|----------|----------|
| `searchFinanceTransactions` | POST /finance/transactions/search |
| `batchCategorizeFinanceTransactions` | POST /finance/transactions/batch-categorize |
| `importFinanceBankStatements` | POST /finance/import/bank-statements |
| `fetchFinanceAccounts` | GET /finance/accounts |
| `fetchFinanceCategories` | GET /finance/categories |
| `fetchFinanceRules` | GET /rules-engine/rules |
| `createFinanceRule` | POST /rules-engine/rules |

### Intelligence
| Fonction | Endpoint |
|----------|----------|
| `calculateEOQ` | POST /inventory-intelligence/eoq |
| `calculateSafetyStock` | POST /inventory-intelligence/safety-stock |
| `fetchReorderPoints` | GET /inventory-intelligence/reorder-points |
| `fetchStockoutPredictions` | GET /inventory-intelligence/stockout-predictions |
| `fetchABCXYZClassification` | GET /inventory-intelligence/abc-xyz |
| `forecastSales` | POST /forecasting/sales |
| `fetchCashFlowForecast` | GET /forecasting/cash-flow |
| `scanForAnomalies` | POST /anomaly-detection/scan |
| `detectTransactionOutliers` | GET /anomaly-detection/outliers |
| `fetchSupplierScore` | GET /supplier-scoring/supplier/{id} |
| `fetchSuppliersRanking` | GET /supplier-scoring/ranking |
| `fetchProductMargins` | GET /margins/products |
| `fetchDishMargins` | GET /margins/dishes |

### Bank Reconciliation
| Fonction | Endpoint |
|----------|----------|
| `runBankReconciliation` | POST /bank-reconciliation/run |
| `fetchUnmatchedTransactions` | GET /bank-reconciliation/unmatched/transactions |
| `fetchUnmatchedInvoices` | GET /bank-reconciliation/unmatched/invoices |
| `createManualMatch` | POST /bank-reconciliation/match/manual |
| `fetchReconciliationSummary` | GET /bank-reconciliation/summary |

### Cockpit
| Fonction | Endpoint |
|----------|----------|
| `fetchCockpitOverview` | GET /cockpit/overview |
| `fetchCockpitLiveKPIs` | GET /cockpit/kpis/live |
| `fetchCockpitAlerts` | GET /cockpit/alerts |
| `acknowledgeCockpitAlert` | POST /cockpit/alerts/{id}/acknowledge |

---

# 7. Conventions & Standards

## 7.1 Style Guide

- **ESLint + Prettier** configurés
- Formatage automatique au pre-commit
- Aucune exception : tout le code doit passer le lint

## 7.2 Naming Conventions

| Élément | Convention | Exemple |
|---------|------------|---------|
| Variables JS | camelCase | `userName`, `orderTotal` |
| Variables Python | snake_case | `user_name`, `order_total` |
| Constantes | SCREAMING_SNAKE | `MAX_RETRY`, `API_URL` |
| Fonctions JS | camelCase (verbe) | `getUser()`, `createOrder()` |
| Fonctions Python | snake_case (verbe) | `get_user()`, `create_order()` |
| Classes | PascalCase | `UserService`, `OrderRepository` |
| Fichiers JS | PascalCase (composants) | `UserCard.jsx`, `SearchInput.jsx` |
| Fichiers Python | snake_case | `user_service.py`, `order_dto.py` |
| Endpoints API | kebab-case pluriel | `/api/users`, `/api/order-items` |
| Hooks React | camelCase (use*) | `useAuth`, `useDebounce` |

## 7.3 Conventional Commits

Format obligatoire pour tous les messages de commit :

```
<type>(<scope>): <description>
```

| Type | Usage | Exemple |
|------|-------|---------|
| feat | Nouvelle fonctionnalité | `feat(auth): add OAuth2 support` |
| fix | Correction de bug | `fix(api): handle null response` |
| refactor | Refactoring | `refactor(users): extract validation` |
| docs | Documentation | `docs(readme): update setup` |
| test | Tests | `test(orders): add unit tests` |
| style | CSS, formatage UI | `style(button): update hover state` |
| chore | Maintenance | `chore(deps): upgrade lodash` |

## 7.4 Git Workflow

- **Branche principale** : `main` (protégée)
- **Branches feature** : `feature/nom-court`
- **Branches hotfix** : `hotfix/description`
- Merge via Pull Request uniquement
- Squash commits avant merge

## 7.5 Tests

| Type | Coverage | Description |
|------|----------|-------------|
| Tests unitaires | 70% | Rapides, isolés, mockés |
| Tests intégration | 20% | API, database |
| Tests E2E | 10% | Parcours critiques (Cypress) |

**Coverage minimum cible** : 80%

---

# 8. Scénarios Utilisateur

## 8.1 Import Facture → Stock → Finance

```
1. Import Facture PDF              2. Extraction automatique
┌─────────────────────┐           ┌─────────────────────┐
│  /invoices/import   │ ────────▶ │  invoice_extractor  │
│  [Drop PDF]         │           │  → Lignes extraites │
└─────────────────────┘           │  → Produits matchés │
                                  └──────────┬──────────┘
                                             │
                                             ▼
3. Mise à jour Stock              4. Catégorisation Finance
┌─────────────────────┐           ┌─────────────────────┐
│  Event:             │ ────────▶ │  Rules Engine:      │
│  INVOICE_IMPORTED   │           │  Catégorisation     │
│  → +Stock reçu      │           │  automatique        │
│  → Prix MAJ         │           │  → 94% confiance    │
└─────────────────────┘           └─────────────────────┘
```

## 8.2 Alerte Stock → Commande → Prévision

```
1. Alerte Cockpit                 2. Détail Produit
┌─────────────────────┐           ┌─────────────────────┐
│  CockpitPage:       │ ────────▶ │  Intelligence:      │
│  "⚠️ Stock critique │           │  Stock: 5kg         │
│   Tomates: 2 jours" │           │  Conso moy: 2.5kg/j │
│  [Voir]             │           │  Jours restants: 2  │
└─────────────────────┘           └──────────┬──────────┘
                                             │
                                             ▼
3. Recommandation EOQ             4. Création Commande
┌─────────────────────┐           ┌─────────────────────┐
│  inventory_intel:   │ ────────▶ │  Créer bon de       │
│  "Commander 50kg    │           │  commande           │
│   chez METRO        │           │  → Pré-rempli       │
│   (EOQ optimal)"    │           │  → Quantité EOQ     │
└─────────────────────┘           └─────────────────────┘
```

## 8.3 Anomalie Prix → Investigation → Action

```
1. Détection Anomalie             2. Alerte Intelligence
┌─────────────────────┐           ┌─────────────────────┐
│  anomaly_detection  │ ────────▶ │  /intelligence/     │
│  "Huile d'olive     │           │  anomalies          │
│   +35% vs moyenne"  │           │  Sévérité: HAUTE    │
│                     │           │  Impact: 450€/mois  │
└─────────────────────┘           └──────────┬──────────┘
                                             │
                                             ▼
3. Investigation                  4. Action Corrective
┌─────────────────────┐           ┌─────────────────────┐
│  Contexte:          │ ────────▶ │  Options:           │
│  - Historique prix  │           │  □ Changer fournis. │
│  - Comparatif       │           │  □ Négocier prix    │
│  - Impact marge     │           │  □ Produit subst.   │
└─────────────────────┘           └─────────────────────┘
```

## 8.4 Rapprochement Bancaire

```
1. Import Relevé                  2. Matching Auto
┌─────────────────────┐           ┌─────────────────────┐
│  Import CSV/OFX     │ ────────▶ │  bank_reconciliation│
│  Transactions       │           │  • Match exact      │
│  bancaires          │           │  • Match fuzzy      │
└─────────────────────┘           │  • Suggestions      │
                                  └──────────┬──────────┘
                                             │
                                             ▼
3. Validation Manuelle            4. Réconciliation
┌─────────────────────┐           ┌─────────────────────┐
│  BankReconciliation │ ────────▶ │  Transaction liée   │
│  Page:              │           │  à facture          │
│  [Valider] [Ignorer]│           │  → reconciled=true  │
└─────────────────────┘           └─────────────────────┘
```

---

# 9. Roadmap & Priorités

## Vue d'ensemble

```
                    ROADMAP UX NEXT-GEN 2025
    ════════════════════════════════════════════════════════

    DÉC 2025          ║  JAN 2026         ║  FÉV 2026
    ──────────────────║──────────────────║──────────────────
    PHASE 0-4         ║  PHASE 5          ║  PHASE 6+
    Fondations+       ║  Intégration      ║  Mobile+Offline
    ✅ P0 terminé     ║  complète         ║  PWA
    ✅ P1 terminé     ║                   ║
    ✅ P2 terminé     ║                   ║
    ✅ P3 terminé     ║                   ║
    ✅ P4 terminé     ║                   ║
    ══════════════════╩══════════════════╩══════════════════
```

### Détail des Phases Terminées

| Phase | Composants | Status |
|-------|------------|--------|
| **Phase 0** | Fondations, Design System | ✅ 100% |
| **Phase 1** | Composants UI core (Skeleton, EmptyState, Toast, Modal) | ✅ 100% |
| **Phase 2** | Grid System, Breakpoints, Layout responsive | ✅ 100% |
| **Phase 3** | TabView, Navigation unifiée 6 vues | ✅ 100% |
| **Phase 4** | InlineEditor, CardExpandable, SmartTable, AIConfidenceBadge | ✅ 100% |

---


# UX Next-Gen 2025 - Plateforme Unifiée

**Vision** : Une interface où l'utilisateur ne navigue plus, il **agit**. L'IA anticipe, suggère, et l'action est toujours à un clic.

---

## 1. Philosophie de Design

### Principes Fondamentaux

| Principe | Description | Impact |
|----------|-------------|--------|
| **Zero Navigation** | L'utilisateur reste sur une vue, le contenu vient à lui | -80% de clics |
| **Action-First** | Chaque élément affiché est actionnable | +60% efficacité |
| **Context-Aware** | L'interface s'adapte au contexte (heure, urgences, rôle) | UX personnalisée |
| **AI-Assisted** | Suggestions proactives, auto-complétion intelligente | Réduction erreurs |
| **Offline-Ready** | Fonctionne hors connexion, sync en arrière-plan | Fiabilité terrain |

### Anti-Patterns à Éliminer

```
❌ AVANT (39 pages, navigation profonde)
┌─────────────────────────────────────────────────────────────┐
│ Sidebar → Opérations → Catalogue → Filtrer → Cliquer       │
│ → Nouvelle page → Charger → Filtrer encore → Action        │
│                                                             │
│ 🐢 8 clics pour modifier un prix                           │
└─────────────────────────────────────────────────────────────┘

✅ APRÈS (6 vues, actions directes)
┌─────────────────────────────────────────────────────────────┐
│ Cockpit → Alerte "Prix anormal" → Clic → Modifier inline   │
│                                                             │
│ ⚡ 2 clics pour la même action                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture des Vues

### 2.1 Structure Globale

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              TOPBAR CONTEXTUELLE                                 │
│  ┌────────────┐ ┌──────────────────┐ ┌─────────────────┐ ┌────────┐ ┌────────┐ │
│  │🏪 Épicerie │ │📅 Déc 2025    ▼ │ │⚡ Actions      ▼│ │🔔 12   │ │👤 Chef │ │
│  │   ▼        │ │ [Aujourd'hui]    │ │ [Commande rapide]│ │alertes │ │        │ │
│  └────────────┘ └──────────────────┘ └─────────────────┘ └────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────┐  ┌─────────────────────────────────────────────────────────────┐  │
│  │          │  │                                                              │  │
│  │  SIDEBAR │  │                    ZONE PRINCIPALE                          │  │
│  │          │  │                                                              │  │
│  │ ┌──────┐ │  │  ┌─────────────────────────────────────────────────────┐   │  │
│  │ │🎯    │ │  │  │                 ONGLETS CONTEXTUELS                  │   │  │
│  │ │Cockpit│ │ │  └─────────────────────────────────────────────────────┘   │  │
│  │ └──────┘ │  │                                                              │  │
│  │          │  │  ┌─────────────────────────────────────────────────────┐   │  │
│  │ ┌──────┐ │  │  │                                                      │   │  │
│  │ │📦    │ │  │  │              CONTENU PRINCIPAL                       │   │  │
│  │ │Ops   │ │  │  │           (Table / Cards / Timeline)                 │   │  │
│  │ └──────┘ │  │  │                                                      │   │  │
│  │          │  │  └─────────────────────────────────────────────────────┘   │  │
│  │ ┌──────┐ │  │                                                              │  │
│  │ │💰    │ │  │  ┌─────────────────────────────────────────────────────┐   │  │
│  │ │Finance││  │  │              PANNEAU CONTEXTUEL                     │   │  │
│  │ └──────┘ │  │  │         (Drawer détail / Actions / Graphiques)      │   │  │
│  │          │  │  └─────────────────────────────────────────────────────┘   │  │
│  │ ┌──────┐ │  │                                                              │  │
│  │ │🍽️    │ │  └─────────────────────────────────────────────────────────────┘  │
│  │ │Resto │ │                                                                    │
│  │ └──────┘ │  ┌─────────────────────────────────────────────────────────────┐  │
│  │          │  │                    COMMAND BAR (⌘K)                        │  │
│  │ ┌──────┐ │  │  🔍 Recherche intelligente... "facture metro décembre"      │  │
│  │ │🧠    │ │  └─────────────────────────────────────────────────────────────┘  │
│  │ │Intel │ │                                                                    │
│  │ └──────┘ │                                                                    │
│  │          │                                                                    │
│  │ ┌──────┐ │                                                                    │
│  │ │⚙️    │ │                                                                    │
│  │ │Config│ │                                                                    │
│  │ └──────┘ │                                                                    │
│  └──────────┘                                                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Les 6 Vues Principales

| Vue | Description | Onglets | Actions Principales |
|-----|-------------|---------|---------------------|
| **Cockpit** | Vue 360°, alertes, KPIs temps réel | - | Acknowledge, Drill-down |
| **Opérations** | Catalogue, Factures, Stock unifié | Catalogue \| Factures \| Stock \| Prix | CRUD inline, Import, Export |
| **Finance** | Trésorerie consolidée | Transactions \| Rapprochement \| Comptes \| Règles | Catégoriser, Matcher, Valider |
| **Restaurant** | Gestion resto complète | Menus \| Charges \| Stock \| Prévisions | Costing, Commandes |
| **Intelligence** | IA & Analytics | Dashboard \| Alertes \| Recommandations | Appliquer suggestion |
| **Config** | Paramètres système | Règles \| Audit \| Utilisateurs | Configurer |

---

## 3. Scénarios Utilisateur Next-Gen

### 3.1 Scénario : Journée Type du Gérant (Mode "Morning Brief")

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🌅 COCKPIT - Mode Matin (7h00)                                                  │
│ ════════════════════════════════════════════════════════════════════════════════│
│                                                                                  │
│  "Bonjour Chef ! Voici votre brief du jour"                                     │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 📊 HIER EN BREF                                                              ││
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            ││
│  │ │ CA Jour     │ │ Marge Brute │ │ Tickets     │ │ Panier Moy  │            ││
│  │ │ 2 847 €     │ │ 38.2%       │ │ 127         │ │ 22.4 €      │            ││
│  │ │ ↑ +12%      │ │ ↓ -2.1%     │ │ ↑ +8        │ │ → stable    │            ││
│  │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 🚨 À TRAITER AUJOURD'HUI (3 actions)                        [Tout traiter ▶]││
│  │ ─────────────────────────────────────────────────────────────────────────────││
│  │                                                                              ││
│  │ ⚠️ URGENT │ Stock Tomates: 2kg restants (besoin 15kg/jour)                  ││
│  │           │ 💡 Suggestion: Commander 50kg chez METRO (livraison demain)     ││
│  │           │ [📦 Commander maintenant] [⏰ Reporter] [❌ Ignorer]             ││
│  │ ──────────┼──────────────────────────────────────────────────────────────────││
│  │ 💰 MOYEN  │ 3 factures à valider (Metro, Brake, PromoC) - Total: 1 247€     ││
│  │           │ 💡 Catégorisation auto: 94% confiance                            ││
│  │           │ [✅ Valider tout] [👁️ Vérifier] [⏰ Plus tard]                  ││
│  │ ──────────┼──────────────────────────────────────────────────────────────────││
│  │ 📈 INFO   │ Anomalie prix: Huile olive +23% vs moyenne marché               ││
│  │           │ 💡 Alternative: Fournisseur B à -15% (même qualité)             ││
│  │           │ [🔄 Changer fournisseur] [📊 Voir analyse] [👍 OK prix]         ││
│  └───────────┴──────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 📅 PRÉVISIONS SEMAINE                                                        ││
│  │ ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐                                 ││
│  │ │ Lun │ Mar │ Mer │ Jeu │ Ven │ Sam │ Dim │                                 ││
│  │ │2.1k │2.4k │2.2k │2.8k │3.5k │4.2k │1.8k │  CA Prévu                       ││
│  │ │ 🟢  │ 🟢  │ 🟢  │ 🟡  │ 🔴  │ 🔴  │ 🟢  │  Stock OK?                      ││
│  │ └─────┴─────┴─────┴─────┴─────┴─────┴─────┘                                 ││
│  │ ⚠️ Vendredi/Samedi: Rupture probable sur 4 produits [Voir détail]           ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Scénario : Import Facture Intelligent (Zero-Click Processing)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 📦 OPÉRATIONS > Factures                                                        │
│ ════════════════════════════════════════════════════════════════════════════════│
│ [Catalogue] [▶ Factures] [Stock] [Prix]                                         │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 📤 ZONE DROP (Drag & Drop ou 📷 Photo mobile)                               ││
│  │ ┌─────────────────────────────────────────────────────────────────────────┐ ││
│  │ │                                                                          │ ││
│  │ │     📄 Glissez vos factures ici                                         │ ││
│  │ │         ou                                                               │ ││
│  │ │     [📁 Parcourir] [📷 Scanner] [📧 Email: factures@monepicerie.com]    │ ││
│  │ │                                                                          │ ││
│  │ └─────────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ ⚡ TRAITEMENT EN COURS                                                       ││
│  │ ─────────────────────────────────────────────────────────────────────────────││
│  │                                                                              ││
│  │  Facture_METRO_2025-12-10.pdf                                               ││
│  │  ┌────────────────────────────────────────────────────────────────────────┐ ││
│  │  │ ✅ OCR terminé          → 47 lignes extraites                          │ ││
│  │  │ ✅ Matching produits    → 45/47 matchés (96%)                          │ ││
│  │  │ ✅ Prix analysés        → 2 anomalies détectées                        │ ││
│  │  │ ✅ Catégorisation       → 100% auto-catégorisé                         │ ││
│  │  │ 🔄 Mise à jour stock    → En cours...                                  │ ││
│  │  └────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                              ││
│  │  ⚠️ 2 POINTS D'ATTENTION                                                    ││
│  │  ┌────────────────────────────────────────────────────────────────────────┐ ││
│  │  │ 1. "Huile Olive Extra 5L" → Nouveau produit                            │ ││
│  │  │    💡 Similaire à: "Huile Olive 5L" (existant)                         │ ││
│  │  │    [🔗 Lier à existant] [➕ Créer nouveau] [❓ Ignorer]                 │ ││
│  │  │                                                                         │ ││
│  │  │ 2. "Tomates Grappe" → Prix +18% vs dernier achat                       │ ││
│  │  │    Avant: 2.40€/kg → Maintenant: 2.83€/kg                              │ ││
│  │  │    💡 Saisonnier (décembre) - Historique similaire                     │ ││
│  │  │    [✅ Accepter] [🚫 Contester] [📊 Voir historique]                   │ ││
│  │  └────────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 📋 RÉSUMÉ IMPORT                                                            ││
│  │ ┌─────────────┬─────────────┬─────────────┬─────────────┐                   ││
│  │ │ Total HT    │ TVA         │ Total TTC   │ Lignes      │                   ││
│  │ │ 847.32€     │ 72.45€      │ 919.77€     │ 47          │                   ││
│  │ └─────────────┴─────────────┴─────────────┴─────────────┘                   ││
│  │                                                                              ││
│  │ [✅ Valider et mettre à jour stock] [📝 Modifier avant validation]          ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Scénario : Gestion Stock Intelligente (Inline Everything)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 📦 OPÉRATIONS > Catalogue                                                       │
│ ════════════════════════════════════════════════════════════════════════════════│
│ [▶ Catalogue] [Factures] [Stock] [Prix]                                         │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 🔍 FILTRES INTELLIGENTS                                                      ││
│  │ ┌───────────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   ││
│  │ │ 🔍 Recherche...   │ │ Cat: Tous ▼│ │ Stock: ⚠️ 12│ │ Qualité: 🔴 5  │   ││
│  │ └───────────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘   ││
│  │                                                                              ││
│  │ 💡 Suggestions: [Voir ruptures imminentes] [Prix anormaux] [Sans code-barre]││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 📊 TABLE INTELLIGENTE (247 produits)                     [📥 Export] [➕]   ││
│  │ ─────────────────────────────────────────────────────────────────────────────││
│  │ ☐ │ Produit              │ Stock  │ Seuil │ P.Achat│ P.Vente│ Marge │ 🔧   ││
│  │ ──┼──────────────────────┼────────┼───────┼────────┼────────┼───────┼──────││
│  │ ☐ │ 🟢 Riz Basmati 5kg   │ 23     │ 10    │ 4.50€  │ 6.90€  │ 34.8% │ ⋮    ││
│  │ ☐ │ 🔴 Huile Olive 1L    │ 2 ⚠️   │ 10    │ ?.??€  │ 8.50€  │  -    │ ⋮    ││
│  │   │   └─ 💡 Commander 24u chez METRO                    [📦 Commander]      ││
│  │ ☐ │ 🟡 Café Moulu 250g   │ 8      │ 15    │ 3.20€  │ 5.90€  │ 45.7% │ ⋮    ││
│  │ ☐ │ 🟢 Sucre 1kg         │ 45     │ 20    │ 0.89€  │ 1.45€  │ 38.6% │ ⋮    ││
│  │ ☐ │ 🔴 Tomates kg        │ 2 ⚠️   │ 15    │ 2.83€↑ │ 4.50€  │ 37.1% │ ⋮    ││
│  │   │   └─ ⚠️ Prix +18% vs moyenne. Saisonnier.          [📊 Analyser]       ││
│  │ ──┼──────────────────────┼────────┼───────┼────────┼────────┼───────┼──────││
│  │   │ 🔽 Charger plus (242 restants)                                          ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 📋 DRAWER DÉTAIL - Huile Olive 1L                                    [✕]   ││
│  │ ─────────────────────────────────────────────────────────────────────────────││
│  │                                                                              ││
│  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │ 📈 HISTORIQUE PRIX (6 mois)                                             │││
│  │  │ 8€ ┤                                            ╭──●                    │││
│  │  │ 7€ ┤                              ╭─────────────╯                        │││
│  │  │ 6€ ┤───────────────●──────────────╯                                     │││
│  │  │    └────┬────┬────┬────┬────┬────┬────                                  │││
│  │  │        Juil Août Sept Oct  Nov  Déc                                     │││
│  │  │  ⚠️ Tendance: +22% sur 6 mois                                           │││
│  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │                                                                              ││
│  │  ┌─────────────────────────────────────────────────────────────────────────┐││
│  │  │ 🏪 FOURNISSEURS                                                         │││
│  │  │ ┌────────────────┬─────────┬──────────┬─────────┐                       │││
│  │  │ │ Fournisseur    │ Prix    │ Délai    │ Score   │                       │││
│  │  │ ├────────────────┼─────────┼──────────┼─────────┤                       │││
│  │  │ │ 🥇 Direct Prod │ 6.20€   │ 3 jours  │ ⭐ 4.8  │ [Commander]           │││
│  │  │ │ 🥈 Metro       │ 6.80€   │ 1 jour   │ ⭐ 4.5  │ [Commander]           │││
│  │  │ │ 🥉 PromoC      │ 7.10€   │ 2 jours  │ ⭐ 4.2  │ [Commander]           │││
│  │  │ └────────────────┴─────────┴──────────┴─────────┘                       │││
│  │  │ 💡 Économie potentielle: 14.40€/mois en changeant pour Direct Prod      │││
│  │  └─────────────────────────────────────────────────────────────────────────┘││
│  │                                                                              ││
│  │  [📦 Créer commande] [📝 Modifier produit] [📊 Analyse complète]            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Scénario : Finance - Rapprochement Assisté par IA

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 💰 FINANCE > Rapprochement                                                      │
│ ════════════════════════════════════════════════════════════════════════════════│
│ [Transactions] [▶ Rapprochement] [Comptes] [Règles]                             │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 📊 ÉTAT DU RAPPROCHEMENT                                                    ││
│  │ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐                 ││
│  │ │ ✅ Rapprochées  │ │ 🤖 Suggestions  │ │ ❓ Non matchées │                 ││
│  │ │ 847 (89%)       │ │ 67 (7%)         │ │ 38 (4%)         │                 ││
│  │ │ 124 350€        │ │ 8 720€          │ │ 4 230€          │                 ││
│  │ └─────────────────┘ └─────────────────┘ └─────────────────┘                 ││
│  │                                                                              ││
│  │ [🤖 Appliquer toutes les suggestions (67)] [📥 Importer relevé]             ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 🤖 SUGGESTIONS IA (67 matchs proposés)                    [✅ Tout valider] ││
│  │ ─────────────────────────────────────────────────────────────────────────────││
│  │                                                                              ││
│  │ ┌─ Match #1 ─────────────────────────────────────────── Confiance: 98% ──┐  ││
│  │ │                                                                         │  ││
│  │ │  💳 RELEVÉ BANCAIRE              🔗           📄 FACTURE               │  ││
│  │ │  ┌─────────────────────────┐     ↔️     ┌─────────────────────────┐    │  ││
│  │ │  │ 10/12 METRO CASH 847.32│            │ Metro #F2025-4521       │    │  ││
│  │ │  │ Débit: -847.32€        │            │ Total TTC: 847.32€      │    │  ││
│  │ │  └─────────────────────────┘            └─────────────────────────┘    │  ││
│  │ │                                                                         │  ││
│  │ │  💡 Match exact: même montant, même date, nom fournisseur reconnu      │  ││
│  │ │  [✅ Valider] [👁️ Détails] [❌ Rejeter]                                │  ││
│  │ └─────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                              ││
│  │ ┌─ Match #2 ─────────────────────────────────────────── Confiance: 87% ──┐  ││
│  │ │                                                                         │  ││
│  │ │  💳 RELEVÉ BANCAIRE              🔗           📄 FACTURES (2)          │  ││
│  │ │  ┌─────────────────────────┐     ↔️     ┌─────────────────────────┐    │  ││
│  │ │  │ 08/12 VIR BRAKE 1523.40│            │ Brake #B-7842: 987.20€  │    │  ││
│  │ │  │ Débit: -1523.40€       │            │ Brake #B-7901: 536.20€  │    │  ││
│  │ │  └─────────────────────────┘            │ Total: 1523.40€ ✓      │    │  ││
│  │ │                                         └─────────────────────────┘    │  ││
│  │ │  💡 Paiement groupé détecté (2 factures = 1 virement)                  │  ││
│  │ │  [✅ Valider groupé] [🔀 Séparer] [❌ Rejeter]                         │  ││
│  │ └─────────────────────────────────────────────────────────────────────────┘  ││
│  │                                                                              ││
│  │ [Voir les 65 autres suggestions...]                                          ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ ❓ NON MATCHÉES (38 transactions)                         [🔍 Rechercher]   ││
│  │ ─────────────────────────────────────────────────────────────────────────────││
│  │ │ Date  │ Libellé                      │ Montant  │ Actions                  ││
│  │ ├───────┼──────────────────────────────┼──────────┼──────────────────────────││
│  │ │ 05/12 │ CB AMAZON 45.99              │ -45.99€  │ [🏷️ Catégoriser] [🔗]    ││
│  │ │ 03/12 │ VIR LOYER LOCAL              │ -1200€   │ [🔄 Récurrent] [🔗]      ││
│  │ │ 01/12 │ PRLV ASSURANCE               │ -234.50€ │ [🔄 Récurrent] [🔗]      ││
│  │ └───────┴──────────────────────────────┴──────────┴──────────────────────────┘│
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.5 Scénario : Intelligence - Décisions Assistées

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🧠 INTELLIGENCE                                                                 │
│ ════════════════════════════════════════════════════════════════════════════════│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 🎯 RECOMMANDATIONS DU JOUR                              Score global: 7.2/10││
│  │ ─────────────────────────────────────────────────────────────────────────────││
│  │                                                                              ││
│  │ ┌─ 💰 OPTIMISATION MARGE ──────────────────────────── Impact: +847€/mois ─┐ ││
│  │ │                                                                          │ ││
│  │ │  "Augmenter le prix de 5 produits sous-margés"                          │ ││
│  │ │                                                                          │ ││
│  │ │  ┌─────────────────────┬──────────┬──────────┬───────────┐              │ ││
│  │ │  │ Produit             │ Prix act.│ Prix sug.│ Impact    │              │ ││
│  │ │  ├─────────────────────┼──────────┼──────────┼───────────┤              │ ││
│  │ │  │ Café Premium 500g   │ 8.90€    │ 9.90€    │ +124€/mois│              │ ││
│  │ │  │ Miel Bio 500g       │ 12.50€   │ 14.90€   │ +216€/mois│              │ ││
│  │ │  │ Huile Truffe 100ml  │ 18.00€   │ 22.00€   │ +180€/mois│              │ ││
│  │ │  └─────────────────────┴──────────┴──────────┴───────────┘              │ ││
│  │ │                                                                          │ ││
│  │ │  💡 Basé sur: élasticité prix, prix concurrence, historique ventes      │ ││
│  │ │  [✅ Appliquer tout] [📝 Modifier] [📊 Simulation] [❌ Ignorer]         │ ││
│  │ └──────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                              ││
│  │ ┌─ 📦 OPTIMISATION STOCK ──────────────────────────── Impact: -2 340€ ────┐ ││
│  │ │                                                                          │ ││
│  │ │  "Réduire le sur-stock sur 8 produits à rotation lente"                 │ ││
│  │ │                                                                          │ ││
│  │ │  Classification ABC-XYZ:                                                 │ ││
│  │ │  ┌────────┬────────┬────────┐                                           │ ││
│  │ │  │        │   X    │   Y    │   Z    │                                  │ ││
│  │ │  │   A    │  12    │   8    │   3    │  ← Focus ici                     │ ││
│  │ │  │   B    │  23    │  15    │  11    │                                  │ ││
│  │ │  │   C    │  18    │  24    │  45 ⚠️ │  ← 45 produits CZ = sur-stock   │ ││
│  │ │  └────────┴────────┴────────┘                                           │ ││
│  │ │                                                                          │ ││
│  │ │  💡 Suggestion: Déstockage progressif sur produits CZ (-20% prix)       │ ││
│  │ │  [📋 Voir liste] [🏷️ Créer promo] [📊 Simulation]                       │ ││
│  │ └──────────────────────────────────────────────────────────────────────────┘ ││
│  │                                                                              ││
│  │ ┌─ 🏪 SCORING FOURNISSEURS ────────────────────────── Économie: 1 200€/an ─┐││
│  │ │                                                                          │ ││
│  │ │  "3 fournisseurs sous-performants identifiés"                           │ ││
│  │ │                                                                          │ ││
│  │ │  ┌────────────────┬───────┬─────────┬─────────┬──────────────────────┐  │ ││
│  │ │  │ Fournisseur    │ Score │ Délai   │ Prix    │ Recommandation       │  │ ││
│  │ │  ├────────────────┼───────┼─────────┼─────────┼──────────────────────┤  │ ││
│  │ │  │ FourniPlus     │ 2.1/5 │ +3j moy │ +12%    │ ⚠️ Remplacer         │  │ ││
│  │ │  │ QuickFood      │ 2.8/5 │ OK      │ +8%     │ 🔄 Renégocier        │  │ ││
│  │ │  │ DistribLocal   │ 3.2/5 │ -1j     │ +5%     │ 👀 Surveiller        │  │ ││
│  │ │  └────────────────┴───────┴─────────┴─────────┴──────────────────────┘  │ ││
│  │ │                                                                          │ ││
│  │ │  [📧 Générer email négociation] [🔄 Trouver alternatives] [📊 Détails] │ ││
│  │ └──────────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ 📈 PRÉVISIONS CASH-FLOW (30 jours)                                          ││
│  │                                                                              ││
│  │  50k€ ┤                              ╭────────                              ││
│  │  40k€ ┤────────────╮                    ╭────╯                                      ││
│  │  30k€ ┤            ╰────────────╯                                           ││
│  │  20k€ ┤                                    ⚠️ Creux prévu: 15 janv          ││
│  │       └────┬────┬────┬────┬────┬────┬────                                  ││
│  │          Déc   S2   S3   S4  Janv  S2                                       ││
│  │                                                                              ││
│  │  💡 Conseil: Décaler paiement fournisseur METRO au 20/01 (+5 jours)        ││
│  │  [📅 Planifier] [📊 Scénarios] [💳 Options financement]                    ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Interactions Avancées

### 4.1 Command Bar (⌘K / Ctrl+K)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ ⌘K  COMMAND BAR                                                                 │
│ ════════════════════════════════════════════════════════════════════════════════│
│                                                                                  │
│  🔍 facture metro décembre                                                      │
│  ────────────────────────────────────────────────────────────────────────────── │
│                                                                                  │
│  📄 FACTURES                                                                    │
│  ├─ Metro #F2025-4521 - 847.32€ - 10/12/2025                    [Ouvrir]       │
│  ├─ Metro #F2025-4398 - 1 234.50€ - 03/12/2025                  [Ouvrir]       │
│  └─ Metro #F2025-4201 - 567.80€ - 28/11/2025                    [Ouvrir]       │
│                                                                                  │
│  💳 TRANSACTIONS                                                                │
│  └─ METRO CASH -847.32€ - 10/12/2025                            [Voir]         │
│                                                                                  │
│  ⚡ ACTIONS RAPIDES                                                             │
│  ├─ Créer commande Metro                                        [⏎]            │
│  ├─ Voir historique Metro                                       [⏎]            │
│  └─ Contacter Metro                                             [⏎]            │
│                                                                                  │
│  ────────────────────────────────────────────────────────────────────────────── │
│  💡 Astuce: Tapez ">" pour les commandes, "@" pour les mentions                │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Actions Contextuelles (Clic droit / Long press mobile)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ MENU CONTEXTUEL - Produit "Huile Olive 1L"                                      │
│ ═══════════════════════════════════════════                                     │
│                                                                                  │
│  ┌─────────────────────────────────────────┐                                    │
│  │ 📝 Modifier                         ⌘E │                                    │
│  │ 📦 Commander                        ⌘O │                                    │
│  │ 📊 Voir analyse prix                ⌘A │                                    │
│  │ ──────────────────────────────────────  │                                    │
│  │ 🏷️ Changer catégorie                ▶  │                                    │
│  │ 🔗 Lier à fournisseur               ▶  │                                    │
│  │ 📋 Copier référence                 ⌘C │                                    │
│  │ ──────────────────────────────────────  │                                    │
│  │ 🗑️ Désactiver produit             ⌘⌫ │                                    │
│  └─────────────────────────────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Raccourcis Clavier Globaux

| Raccourci | Action |
|-----------|--------|
| `⌘K` | Command bar |
| `⌘/` | Aide contextuelle |
| `⌘1-6` | Navigation sections |
| `⌘N` | Nouvelle entrée (contexte) |
| `⌘S` | Sauvegarder |
| `⌘Z` | Annuler |
| `⌘⇧Z` | Refaire |
| `Esc` | Fermer drawer/modal |
| `Tab` | Navigation champs |
| `↑↓` | Navigation liste |
| `Space` | Sélection |
| `⏎` | Valider/Ouvrir |

---

## 5. États & Feedback

### 5.1 États des Données

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ INDICATEURS VISUELS                                                             │
│ ═══════════════════════════════════════════════════════════════════════════════ │
│                                                                                  │
│  STOCK                           QUALITÉ DONNÉES         TENDANCE               │
│  ──────                          ───────────────         ────────               │
│  🟢 OK (>seuil)                  🟢 Complet              ↑ Hausse               │
│  🟡 Attention (<150% seuil)      🟡 Partiel (>80%)       → Stable               │
│  🔴 Critique (<seuil)            🔴 Incomplet (<80%)     ↓ Baisse               │
│  ⚫ Rupture (=0)                 ⚪ Nouveau               ⚡ Volatil             │
│                                                                                  │
│  CONFIANCE IA                    URGENCE                 STATUT                 │
│  ────────────                    ───────                 ──────                 │
│  ████████░░ 80%+ Fiable          🔴 Urgent (<24h)        ✅ Validé              │
│  █████░░░░░ 50-80% À vérifier    🟡 Moyen (1-7j)         🔄 En cours            │
│  ███░░░░░░░ <50% Manuel          🟢 Normal (>7j)         ⏸️ En pause            │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Notifications & Toasts

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ SYSTÈME DE NOTIFICATIONS                                                        │
│ ═══════════════════════════════════════════════════════════════════════════════ │
│                                                                                  │
│  ┌─ TOAST SUCCESS ──────────────────────────────────────────────────────────┐   │
│  │ ✅ Facture importée avec succès                                          │   │
│  │    47 lignes • Stock mis à jour • 2 alertes prix                         │   │
│  │    [Voir détails] [✕]                                    Auto-close: 5s  │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─ TOAST WARNING ──────────────────────────────────────────────────────────┐   │
│  │ ⚠️ 3 produits sans correspondance                                        │   │
│  │    Nécessite une action manuelle                                          │   │
│  │    [Résoudre maintenant] [Plus tard] [✕]                                 │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─ TOAST ERROR ────────────────────────────────────────────────────────────┐   │
│  │ ❌ Échec de l'import                                                      │   │
│  │    Erreur: Format de fichier non reconnu                                  │   │
│  │    [🔄 Réessayer] [📧 Support] [✕]                       Persist until X │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌─ NOTIFICATION PUSH ──────────────────────────────────────────────────────┐   │
│  │ 🔔 Alerte Stock                                              Il y a 2min │   │
│  │                                                                           │   │
│  │ Stock Tomates critique (2kg)                                              │   │
│  │ Rupture estimée: demain 14h                                               │   │
│  │                                                                           │   │
│  │ [📦 Commander] [⏰ Rappel 1h] [👁️ Voir] [✕]                              │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Mobile & Responsive

### 6.1 Vue Mobile (Bottom Navigation)

```
┌─────────────────────────────────┐
│ 🏪 Épicerie    📅 Déc    🔔 3  │
├─────────────────────────────────┤
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🚨 ALERTES (3)            │  │
│  │                           │  │
│  │ ⚠️ Stock Tomates: 2kg    │  │
│  │    [📦 Commander]         │  │
│  │                           │  │
│  │ 💰 3 factures à valider  │  │
│  │    [✅ Valider]           │  │
│  │                           │  │
│  │ 📈 Anomalie prix huile   │  │
│  │    [📊 Voir]              │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 📊 AUJOURD'HUI            │  │
│  │                           │  │
│  │ CA: 2 847€  ↑12%          │  │
│  │ Marge: 38.2%              │  │
│  │ Tickets: 127              │  │
│  └───────────────────────────┘  │
│                                 │
│  [📷 Scanner facture]           │
│                                 │
├─────────────────────────────────┤
│  🎯    📦    💰    🍽️    🧠   │
│Cockpit  Ops  Finance Resto Intel│
└─────────────────────────────────┘
```

### 6.2 Actions Mobiles Spécifiques

| Action | Geste | Description |
|--------|-------|-------------|
| Scanner facture | Tap caméra | OCR instantané |
| Inventaire rapide | Swipe produit | +1 / -1 stock |
| Validation batch | Long press | Multi-sélection |
| Refresh | Pull down | Actualisation |
| Actions | Swipe gauche | Menu contextuel |

---

## 7. Implémentation Technique

### 7.1 Composants Clés à Créer

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── TopBar.jsx           # Barre contextuelle
│   │   ├── Sidebar.jsx          # Navigation 6 sections
│   │   ├── CommandBar.jsx       # ⌘K search
│   │   └── BottomNav.jsx        # Mobile
│   │
│   ├── smart/
│   │   ├── SmartTable.jsx       # Table avec inline edit
│   │   ├── SmartDrawer.jsx      # Panneau détail contextuel
│   │   ├── SmartFilters.jsx     # Filtres intelligents
│   │   ├── ActionCard.jsx       # Card avec actions intégrées
│   │   └── AlertBanner.jsx      # Alertes actionnables
│   │
│   ├── ai/
│   │   ├── SuggestionCard.jsx   # Recommandation IA
│   │   ├── ConfidenceBadge.jsx  # Indicateur confiance
│   │   ├── ImpactPreview.jsx    # Simulation impact
│   │   └── QuickAction.jsx      # Action en 1 clic
│   │
│   └── feedback/
│       ├── Toast.jsx            # Notifications
│       ├── LoadingState.jsx     # États chargement
│       ├── EmptyState.jsx       # États vides actionnables
│       └── ErrorState.jsx       # États erreur récupérables
│
├── features/
│   ├── cockpit/                 # Vue 360°
│   ├── operations/              # Catalogue + Factures + Stock + Prix
│   ├── finance/                 # Transactions + Rapprochement + Comptes
│   ├── restaurant/              # Menus + Charges + Stock resto
│   ├── intelligence/            # Dashboard IA + Recommandations
│   └── settings/                # Config + Audit
│
├── hooks/
│   ├── useCommandBar.js         # Gestion ⌘K
│   ├── useInlineEdit.js         # Édition inline
│   ├── useSmartFilters.js       # Filtres persistants
│   ├── useOptimisticUpdate.js   # MAJ optimistes
│   ├── useOfflineSync.js        # Mode offline
│   └── useKeyboardNav.js        # Navigation clavier
│
└── contexts/
    ├── GlobalFiltersContext.jsx # Filtres partagés
    ├── AlertsContext.jsx        # Système alertes
    └── CommandBarContext.jsx    # État command bar
```

### 7.2 Migration Progressive

| Phase | Durée | Objectif |
|-------|-------|----------|
| **Phase 1** | 1-2 sem | TopBar contextuelle + CommandBar |
| **Phase 2** | 2-3 sem | Consolidation pages → onglets |
| **Phase 3** | 2 sem | SmartTable + inline edit |
| **Phase 4** | 1-2 sem | Système alertes + suggestions IA |
| **Phase 5** | 1 sem | Mobile + offline |

---

## 8. Métriques de Succès

| Métrique | Avant | Cible | Mesure |
|----------|-------|-------|--------|
| Clics pour action courante | 8 | 2 | Analytics |
| Temps import facture | 5 min | 30 sec | Chrono |
| Taux erreur saisie | 12% | 3% | Logs |
| Adoption mobile | 5% | 40% | Sessions |
| Satisfaction utilisateur | - | >4.5/5 | NPS |

---

**Document créé le 11 Décembre 2025**
**Version 1.0 - Next-Gen UX Proposal**


## 9.1 PHASE 0 - Fondations ✅

> **Statut** : 100% terminé

- [x] Sécurité : JWT obligatoire, cookies httpOnly, CORS strict, accès mobile
- [x] Données Restaurant : 77 plats, 39 ingrédients, 52 recettes, 9 vues BOM
- [x] Endpoints : 9 erreurs 500/422 corrigées, ResponseWrapper, 18 tests
- [x] Infrastructure : ErrorBoundary global, lazy loading, format API unifié

---

## 9.2 PHASE 1 - Qualité Données ✅

> **Statut** : 100% terminé (11 décembre 2025) | **Scénarios** : 3.2, 3.3

- [x] Supprimé 251 doublons `finance_bank_statement_lines`
- [x] Tous les produits ont `prix_achat`/`prix_vente` (854 produits)
- [x] Loader : mapping étendu colonnes (`quantite`, `qte_recue`, `montant_ht`, `prix_ttc`, etc.)
- [x] Loader : recalcul `total_excl_tax`/`total_incl_tax` depuis montants si prix unitaire absent
- [x] `dim_product` peuplé (854), `fact_invoices` peuplé (7280 lignes avec qty/prix non nuls)
- [x] Catégorisation produits : mapping slug+similarité intégré dans `products_loader.py`
- [x] Validation Pydantic stricte + pagination `/catalog/products` (page≥1, per_page≤100)

---

## 9.3 PHASE 2 - Import & Catégorisation ✅

> **Statut** : 100% terminé (11 décembre 2025) | **Scénarios** : 3.1, 3.2

- [x] Module `core/import_analyzer.py` : taux lignes valides, anomalies, coverage champs
- [x] Rapport qualité intégré dans `consolidation_loader` (quality_score, flags, anomalies)
- [x] Endpoint `/data-quality/categorization/coverage` : couverture KeywordAnalyzer + suggestions
- [x] Endpoint `/invoices/zero-click` : PDF → Extraction → Stock + fact_invoices automatique
- [x] Auto-catégorisation : 15 catégories bancaires + mapping fournisseurs (METRO, EUROCIEL, TAIYAT)

---

## 9.4 PHASE 3 - Navigation 6 Vues ✅

> **Statut** : 100% terminé (11 décembre 2025) | **Scénarios** : 3.1 (Morning Brief), 3.3 (Stock Intelligent)

- [x] Composant `TabView` (onglets, clavier ←→, URL sync `?tab=`) — `components/ui/TabView.jsx`
- [x] Cockpit unifié : Dashboard + Portfolio + Alertes + Morning Brief — `CockpitUnifiedPage.jsx`
- [x] Vue Ops (Pilotage | Factures | Catalogue | Stock | Prix) — `OperationsPage.jsx` avec TabView
- [x] Vue Finance (Trésorerie | Transactions | Comptes | Rapprochement | Portefeuille | Imports) — `FinanceUnifiedPage.jsx`
- [x] Vue Intel (Dashboard | Stock Intel | Prévisions | Anomalies | Scoring | Marges) — `IntelligenceUnifiedPage.jsx`
- [x] Build frontend validé (2945 modules, 7.3s)

---

## 9.5 PHASE 4 - Composants UX Avancés

> **Scénarios** : 3.2 (Zero-Click Import), 3.3 (Stock Intelligent)

- [x] CommandBar ⌘K : recherche globale + actions rapides + suggestions IA
- [x] InlineEditor : double-clic → édition + validation optimiste + rollback
- [x] CardExpandable : compact/expand + animation + lazy load
- [x] SmartTable : inline edit intégré DataTable
- [x] AIConfidenceBadge : indicateur visuel confiance IA

---

## 9.6 PHASE 5 - Intelligence & Alertes

> **Scénarios** : 3.1 (Morning Brief)

- [ ] Smart Matching (transaction ↔ facture)
- [ ] Alertes Proactives (stock, prix, catégorisation)
- [ ] Suggestions IA contextuelles dans CommandBar
- [ ] États vides actionnables + erreurs récupérables

---

## 9.7 PHASE 6 - Optimisations

> **Long terme**

- [ ] Refactorer `core/invoice_extractor.py` (1413 lignes)
- [ ] Rate limiting/quotas par tenant
- [ ] Migration SQLAlchemy + Redis
- [ ] Migration TypeScript + bundle splitting
- [ ] Mode sombre + Dashboard métriques

---

## Récapitulatif Priorités

| Phase | Priorité | Statut | Description | Scénarios |
|-------|----------|--------|-------------|-----------|
| **0** | P0 | ✅ 100% | Fondations, sécurité, endpoints | - |
| **1** | P0 | ✅ 100% | Qualité données, loader | 3.2, 3.3 |
| **2** | P0 | ✅ 100% | Import & Catégorisation | 3.1, 3.2 |
| **3** | P1 | ✅ 100% | Navigation 6 vues | 3.1, 3.3 |
| **4** | P1 | ⏳ 0% | Composants UX avancés | 3.2, 3.3 |
| **5** | P2 | ⏳ 0% | Intelligence & Alertes | 3.1 |
| **6** | P3 | ⏳ 0% | Optimisations long terme | - |

---

# 10. État du Projet

## 10.1 Scores par Domaine (11 Décembre 2025 - Mise à jour)

| Aspect | Score | État | Évolution |
|--------|-------|------|-----------|
| Backend | 6.5/10 | Fonctionnel, ResponseWrapper unifié | ↑ +1 |
| Frontend | 7/10 | ErrorBoundary global, lazy loading | ↑ +0.5 |
| Core | 6/10 | Monolithique, refactoring nécessaire | = |
| Base de données | 7/10 | Bonne fondation | = |
| Sécurité | 7/10 | Cookies httpOnly, CORS strict | ↑ +3 |
| Documentation | 8/10 | Consolidée + Vision UX 2025 | ↑ +1 |
| Tests | 4/10 | 18 nouveaux tests endpoints | ↑ +1 |
| **MOYENNE** | **6.5/10** | **Progression significative** | ↑ +0.9 |

## 10.2 Tests (11 Décembre 2025)

| Métrique | Valeur |
|----------|--------|
| Tests hardcore | 160 |
| Tests endpoints corrigés | 18 (nouveau fichier) |
| Tests réussis | 160+ |
| Tests échoués | 0 (endpoints P0) |
| **Taux de réussite P0** | **100%** |
| Front tests UI (Vitest) | ✅ `npm run test:ui` (236 tests, warnings jsdom `window.scrollTo`) |

### Nouveau fichier de tests : `tests/test_fixed_endpoints.py`
- 4 tests `/finance/categories/suggestions/complete` (fix 422)
- 3 tests `/audit-trail/report` (fix 422)
- 6 tests `/restaurant/plats` et `/restaurant/ingredients`
- 2 tests intégration plats/ingrédients
- 3 tests format réponse `ResponseWrapper`

### Modules 100% Fonctionnels
- Stock (15 tests)
- Dashboard (10 tests)
- Bank Reconciliation (10 tests)
- Cockpit (10 tests)
- Prices (5 tests)
- Invoices (5 tests)
- Analytics (5 tests)
- Capital (5 tests)
- **Finance Categories** (4 tests) ← Nouveau
- **Audit Trail** (3 tests) ← Nouveau
- **Restaurant Plats/Ingredients** (8 tests) ← Nouveau

### Avancées UX Phase 4 (décembre)
- CommandBar : catégories contextuelles (Opérations/Finances/Intelligence), récents, actions directes.
- CommandBar live : suggestions issues du cache (alertes cockpit, stocks critiques).
- SmartTable/InlineEditor : branchement catalogue avec update optimiste + rollback.
- Cockpit/Intelligence : CardExpandable + AIConfidenceBadge sur suggestions/prévisions.
- Rapprochement : suggestions IA dans CardExpandable + badge, CTA applique `createMatch`.
- Import facture : card Zero-Click (scénario 3.2) avec badges de confiance et CTA rapides.
- Mobile : navigation bottom (Cockpit/Opérations/Finance/Resto/Intel) activée.

### Endpoints Critiques - Tous Corrigés ✓

| Endpoint | Statut | Fix appliqué |
|----------|--------|--------------|
| GET /catalog/vendors | ✅ | `processed_invoices` au lieu de tables inexistantes |
| GET /finance/recurring | ✅ | Table `finance_recurring_expenses` créée |
| GET /margins/products | ✅ | Colonne `total_margin` + `NULLS LAST` |
| GET /admin/users | ✅ | Sérialisation datetime `.isoformat()` |
| GET /reports/overview | ✅ | Import `text()` corrigé |
| GET /finance/categories/suggestions/complete | ✅ | Param `q` optionnel |
| GET /audit-trail/report | ✅ | Dates optionnelles avec défauts |

## 10.3 Qualité Données (Audit 10 Décembre)

| Table | Problème | Quantité |
|-------|----------|----------|
| processed_invoices | file_path NULL | 250 |
| produits | prix_vente NULL | 499 |
| produits | prix_achat NULL | 499 |
| finance_transactions | label NULL | 8,973 |
| finance_transactions | doublons potentiels | 342 groupes |

## 10.4 Améliorations Techniques Récentes

### ResponseWrapper Middleware (activé)
Format de réponse API unifié sur tous les endpoints :
```json
{
  "success": true,
  "data": [...],
  "error": null,
  "meta": {
    "request_id": "uuid",
    "duration_ms": 45,
    "timestamp": "2025-12-11T..."
  }
}
```
- Exclusions : `/health`, `/docs`, `/redoc`, `/openapi.json`, `/metrics`
- Fichier : `backend/middleware/response_wrapper.py`

### ErrorBoundary Global (activé)
- Niveau `page` : autour de l'application entière
- Niveau `section` : autour de `AppShell`
- Composant : `frontend/src/components/feedback/ErrorBoundary.jsx`

### Authentification Cookies httpOnly
- Access token (15 min) + Refresh token (7 jours)
- Rotation automatique des tokens
- Support hybride : cookies (web) + Bearer (API)

---

# 11. Historique des Avancées

## Décembre 2025

### Semaine 1 (9-10 décembre)
- Audit complet du projet (backend, frontend, core, BDD, sécurité)
- Création des 14 modules `core/finance/` (event sourcing, rules engine, etc.)
- Création des pages Intelligence (Forecasting, Anomalies, Margins, Scoring)
- Création des pages Admin (AuditTrail, BankReconciliation)
- Ajout de 28 routers API backend
- Tests hardcore : 89.4% de réussite (143/160 tests)
- Création de 38 hooks React

### Semaine 2 (11 décembre)
- Correction du bug prix history endpoint
- Création hooks useBankReconciliation et useAuditTrail
- **Consolidation de la documentation** (ce fichier unique)
- Archivage des fichiers obsolètes

#### Sécurité (11 décembre après-midi)
- **Authentification cookies httpOnly** : nouveaux endpoints `/auth/login`, `/auth/refresh`, `/auth/logout`
  - Access token (15 min) + Refresh token (7 jours) avec rotation automatique
  - Support hybride : cookies httpOnly (navigateurs) + Bearer token (API clients)
  - Fichiers modifiés : `backend/dependencies/security.py`, `backend/api/auth.py`, `backend/schemas/auth.py`
- **CORS whitelist stricte** : obligatoire en production, wildcard interdit
  - Erreur au démarrage si `CORS_ALLOWED_ORIGINS` absent en prod
  - Fichier modifié : `backend/main.py`
- **Accès mobile** : script `scripts/mobile_access.sh` + configuration ngrok
- **Sidebar mobile** : correction du bouton fermer (X) avec `onTouchStart` et zone tactile 48x48px
  - Fichier modifié : `frontend/src/app/SidebarNav.jsx`

#### Données Restaurant (11 décembre soir)
- **Import des données restaurant** : peuplement des tables `plats`, `ingredients`, `plat_ingredients`
  - 77 plats importés : 7 dishes (Heru, Ndole, sauces africaines), 65 boissons, 5 formules
  - 39 ingrédients importés avec 52 recettes liées
  - 9 équivalences boissons/formules, 7 catégories, 2 emplacements (Cuisine, Bar)
  - Scripts sources : `docs/restaurant/PLATS_EN_SAUCE_MODELISATION.txt`, `docs/restaurant/PARTIE_3_MENU.txt`
- **Création des vues restaurant** :
  - `v_bom_dish`, `v_bom_beverage`, `v_bom_bundle`, `v_bom_unifie` : Bill of Materials par type
  - `v_bundle_explode`, `v_bundle_equivalents` : explosion des formules
  - `v_frigo_cuisine`, `v_frigo_bar`, `v_portions_vendables` : portions disponibles par emplacement
  - Scripts sources : `docs/restaurant/RESTAURANT_DEBUT_MODELISATION.txt`, `docs/restaurant/BOM_MENU.txt`

#### Corrections Endpoints (11 décembre nuit)
- **GET /reports/overview** : suppression de `text()` non importé dans `backend/services/reports.py`
- **GET /catalog/vendors** : utilisation de `processed_invoices` au lieu de tables `suppliers`/`invoices` inexistantes
- **GET /restaurant/alerts** : création des tables `restaurant_alerts` et `restaurant_plat_costs`
- **Dockerfile.api** : ajout de `COPY core core` pour inclure le dossier `core/` dans l'image Docker
- **GET /admin/users** : sérialisation datetime timezone-aware avec `.isoformat()` dans `backend/services/admin.py`
- **GET /margins/products** : ajout colonne `total_margin` dans le SQL + `NULLS LAST` dans `backend/api/margins.py`
- **GET /catalog/products/barcode/{code}** : préfixage colonnes `p.*` via `PRODUCT_COLUMNS_PREFIXED` pour éviter ambiguïté dans JOIN (`backend/services/catalog.py`)
- **GET /finance/recurring** : création table `finance_recurring_expenses`

**Résultat** : 7 endpoints critiques corrigés, passage de 17 à 11 échecs tests hardcore.

#### APIs Restaurant connectées aux nouvelles tables (11 décembre)
- **Migration schéma** : Les services `backend/services/restaurant/ingredients.py` et `core/restaurant_costs.py` utilisent maintenant les tables `plats`, `ingredients`, `plat_ingredients` au lieu de `restaurant_*`
- **Colonnes ajoutées** : `ingredients.cout_unitaire`, `ingredients.stock_actuel` pour compatibilité API
- **Stock initial** : 39 mouvements créés (21 ingrédients cuisine à 10 unités, 18 boissons bar à 24 unités)
- **Coûts unitaires** : Prix renseignés pour tous les ingrédients (viandes, épices, bières, champagnes)
- **Calcul marges** : Les plats cuisine affichent maintenant leur coût matière et marge (ex: Heru 5.78€ coût, 61% marge)

#### Corrections 422 (11 décembre)
- **GET /finance/categories/suggestions/complete** : paramètre `q` optionnel avec défaut `""` - `backend/api/finance.py`
- **GET /audit-trail/report** : paramètres `start_date`/`end_date` optionnels avec défauts (30 derniers jours) - `backend/api/audit_trail.py`

## À Venir
- Brancher Import Facture zero-click : lier/créer produit, valider stock, polling, CTA Cockpit.
- CommandBar live : suggestions basées sur données temps réel (catalogue/finance) au-delà du cache.
- Déployer CardExpandable/AIConfidenceBadge & SmartTable/InlineEditor sur transactions/règles/stock avec mutations API.
- Gestes mobile (swipe/long press) + scan facture mobile.
- Migration TypeScript progressive
- Augmentation de la couverture tests

---

# 12. Vision UX Next-Gen 2025

> **Document détaillé** : [`docs/UX_NEXT_GEN_2025.md`](./UX_NEXT_GEN_2025.md)

## 12.1 Philosophie

L'UX actuelle souffre d'une **fragmentation excessive** : 39 pages, 28 routes, navigation complexe. La vision Next-Gen adopte deux principes fondamentaux :

### Zéro Navigation
> *L'utilisateur n'a pas à chercher l'information — elle vient à lui.*

- Cockpit centralisé avec alertes proactives
- Actions contextuelles directement dans les vues
- Pas de menu > sous-menu > sous-sous-menu

### Action-First
> *Chaque élément affiché est interactif et actionnable.*

- Cliquer sur un chiffre = détail instantané
- Inline editing partout
- Suggestions IA avec actions en 1 clic

## 12.2 Architecture des 6 Vues Principales

```
┌─────────┬──────────────────────────────────────────┐
│ COCKPIT │ Vue 360° consolidée (pas d'onglets)      │
├─────────┼──────────────────────────────────────────┤
│ OPS     │ Catalogue | Factures | Stock | Prix      │
├─────────┼──────────────────────────────────────────┤
│ FINANCE │ Transactions | Rapprochement | Comptes   │
├─────────┼──────────────────────────────────────────┤
│ RESTO   │ Menus | Charges | Stock | Prévisions     │
├─────────┼──────────────────────────────────────────┤
│ INTEL   │ Cards expandables (pas d'onglets)        │
├─────────┼──────────────────────────────────────────┤
│ CONFIG  │ Règles | Audit | Users                   │
└─────────┴──────────────────────────────────────────┘
```

**Réduction** : 28 routes → 6 vues principales + onglets internes

## 12.3 Patterns UX Clés

### Command Bar (⌘K)
```
┌─────────────────────────────────────────────────────────┐
│ 🔍 Recherche globale...                            ⌘K  │
│                                                         │
│ RÉCENT                    ACTIONS RAPIDES               │
│ • Facture METRO #4521     • Nouvelle facture            │
│ • Tomates (Stock)         • Ajouter produit             │
│ • Transaction 15/12       • Import relevé               │
│                                                         │
│ SUGGESTIONS IA                                          │
│ ⚡ 3 factures à rapprocher                              │
│ ⚠️ Stock critique: Tomates                              │
└─────────────────────────────────────────────────────────┘
```

### Inline Editing
- Double-clic sur une cellule = édition directe
- Validation optimiste (UI update immédiat, rollback si erreur)
- Pas de modale pour les modifications simples

### Cards Expandables
```
┌──────────────────────────────────────────────────┐
│ 📊 Prévisions Ventes          [+15%] ↗  [▼]     │
├──────────────────────────────────────────────────┤
│ Mini-graphique sparkline                         │
│ "Hausse attendue vendredi (événement sportif)"   │
│                                                  │
│ [Détail expansé au clic]                         │
│ • Graphique complet                              │
│ • Recommandations                                │
│ • Actions                                        │
└──────────────────────────────────────────────────┘
```

## 12.4 Scénarios Utilisateurs Avancés

Le document [`UX_NEXT_GEN_2025.md`](./UX_NEXT_GEN_2025.md) détaille 5 scénarios complets :

| # | Scénario | Gain |
|---|----------|------|
| 1 | **Morning Brief** | 8h00 → Vue santé globale en 1 écran |
| 2 | **Zero-Click Import** | Drop PDF → Stock + Finance MAJ auto |
| 3 | **Inline Stock Management** | Ajustement sans quitter la vue |
| 4 | **AI-Assisted Reconciliation** | Match suggéré + validation en 1 clic |
| 5 | **Intelligence Decisions** | Alerte → Investigation → Action |

## 12.5 Composants à Développer

| Composant | Priorité | Description |
|-----------|----------|-------------|
| `CommandBar` | P0 | Recherche globale + actions rapides |
| `InlineEditor` | P0 | Édition directe dans les tables |
| `CardExpandable` | P1 | Cards avec expansion progressive |
| `MorningBrief` | P1 | Widget santé globale Cockpit |
| `AIConfidenceBadge` | P2 | Indicateur confiance suggestions IA |
| `QuickActionPanel` | P2 | Actions contextuelles flottantes |

---

# Configuration et Environnement

## Variables d'Environnement

### Backend

| Variable | Description | Défaut |
|----------|-------------|--------|
| `DATABASE_URL` | URL PostgreSQL | `postgresql://postgres:postgres@db:5432/epicerie` |
| `JWT_SECRET_KEY` | Clé secrète JWT | **(obligatoire - pas de défaut!)** |
| `JWT_ALGORITHM` | Algorithme JWT | `HS256` |
| `CORS_ALLOWED_ORIGINS` | Origines CORS | `http://localhost:5173` |

### Frontend

| Variable | Description | Défaut |
|----------|-------------|--------|
| `VITE_API_BASE_URL` | URL de l'API | `/api` |

## Docker Compose

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/epicerie
      - JWT_SECRET_KEY=...
    depends_on: [db]

  frontend:
    build: ./frontend
    ports: ["5175:5175"]
    environment:
      - VITE_API_BASE_URL=http://localhost:8000

  db:
    image: postgres:16
    volumes: [postgres_data:/var/lib/postgresql/data]
    environment:
      - POSTGRES_DB=epicerie
      - POSTGRES_PASSWORD=postgres
```

## Scripts Utiles

| Script | Description |
|--------|-------------|
| `scripts/import_eurociel.py` | Import données Eurociel |
| `scripts/imports/import_invoice_files.py` | Import batch factures |
| `scripts/imports/import_releves_to_db.py` | Import relevés bancaires |
| `scripts/audit_database.py` | Audit de la base de données |
| `scripts/etl/analyze_releves.py` | Analyse relevés bancaires |
| `scripts/mobile_access.sh` | Configuration accès mobile |

## Accès Mobile

Pour accéder à l'application depuis un appareil mobile sur le même réseau local :

### 1. Lancer le script de configuration

```bash
./scripts/mobile_access.sh start
```

Ce script affiche :
- L'adresse IP locale de votre machine
- Les URLs d'accès (Frontend et API)
- Un QR code pour scanner facilement (si `qrencode` est installé)
- Les instructions de configuration CORS

### 2. Configurer CORS

Ajoutez l'IP locale aux origines autorisées dans `.env` :

```env
CORS_ALLOWED_ORIGINS=http://localhost:5175,http://192.168.1.XX:5175
```

### 3. Configurer le Frontend (optionnel)

Si vous développez en mode dev, créez `frontend/.env.local` :

```env
VITE_API_BASE_URL=http://192.168.1.XX:8000
```

### 4. Vérifier le pare-feu

Assurez-vous que les ports 5175 (frontend) et 8000 (API) sont ouverts :

```bash
# UFW (Ubuntu)
sudo ufw allow 5175/tcp
sudo ufw allow 8000/tcp

# firewalld (Fedora/RHEL)
sudo firewall-cmd --add-port=5175/tcp --permanent
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

### 5. Accéder depuis le mobile

1. Connectez votre mobile au même réseau Wi-Fi
2. Ouvrez l'URL affichée par le script dans le navigateur mobile
3. Acceptez les avertissements de sécurité (HTTP non sécurisé)

## Connexions

| Source | Destination | Type | Port |
|--------|-------------|------|------|
| Browser | Frontend | HTTP | 5175 |
| Frontend | Backend | REST/JSON | 8000 |
| Backend | PostgreSQL | psycopg2 | 5432 |

---

> **Ce document est la référence unique du projet.**
> Toute modification d'architecture, de convention ou d'avancée majeure doit être reflétée ici.

**Dernière mise à jour** : 11 Décembre 2025 (Roadmap UX Next-Gen, État projet MAJ, Section 12 ajoutée)
