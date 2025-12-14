<!-- #USÉ -->
<!-- 📦 MODULE: FINANCE -->
# Architecture technique regroupée

Ce document remplace les anciens README dispersés (`docs/CARTOGRAPHIE_PROJET.md`, `docs/INDEX_TECHNIQUE.md`, `docs/DOCUMENTATION_PROJET.md`, les sections *Zero Click* et *docs/SUPPLIER_SCORING_*). Il offre une seule vue d'ensemble du front, de l'API FastAPI, des modules core/finance/restaurant, des workflows zéro-click/IA, et des scripts d'analyse.

---

## 1. Vue d’ensemble

```
UTILISATEUR
    │
    ▼
FRONTEND (React/Vite + newCMS)
    │
    ▼
API FastAPI (`backend/main.py` + routers)
    │
    ▼
CORE (modules métier, finance, restaurant, catalog)
    │
    ▼
POSTGRESQL 16 (tables `produits`, `mouvements_stock`, `finance_*`, `restaurant_*`, `dim_*`, `fact_*`)
```

Le front expose les expériences Épicerie, Restaurant, Finance, Intelligence et Cockpit à travers une SPA Vite/React enrichie d’un module `newCMS` (pages, hooks, intégration mobile). Il communique avec une API FastAPI qui monte 26 routers (`catalog`, `stock`, `invoices`, `supply`, `finance`, `restaurant`, `inventory-intelligence`, `forecasting`, `anomaly-detection`, `margins`, `bank-reconciliation`, `rules-engine`, `audit-trail`, `cockpit`, `newcms`, etc.). Ce backend délègue la logique métier aux services (`backend/services/*`) et aux modules partagés `core/*`, et persiste dans PostgreSQL via les scripts `db/`, `migrations/versions/` et `scripts/_sql/`.

---

## 2. Frontend (SPA + newCMS)

- `frontend/src/App.jsx`, `main.jsx`, `app/routes.jsx` et `components/ui` forment les shells Épicerie/Restaurant/Finance.  
- `frontend/src/api/client.js` unifie les 45+ appels REST utilisés par les pages métier.  
- Hooks centralisés (`useRestaurant`, `useFinance`, `useInventoryIntelligence`, `useAuditTrail`, `useForecasting`, `useMargins`, `useSupplierScoring`, `useCockpit`, etc.) injectent la logique TanStack Query et la gestion multi-tenant.  
- `newCMS/` et `frontend/src/newCMS/` embarquent l’architecture mobile/restaurant (routes, layouts, hooks, exemples d’intégration, documentation sur la restauration mobile).  
- UI modernes (command palette, feedback, layouts, animations) et outils Cypress (tests d’e2e listés dans `frontend/cypress/`).

---

## 3. Backend FastAPI & services

- `backend/main.py` inclut les middleware (CORS, RequestContext, Performance, ResponseWrapper), les dépendances (`security`, `tenant`), et l’ensemble des routers (`auth`, `catalog`, `invoices`, `stock`, `supply`, `dashboard`, `analytics`, `capital`, `maintenance`, `finance`, `restaurant`, `prices`, `admin`, `data_quality`, `zero-click`, `newcms`, etc.).  
- Les routers s’appuient sur les services `backend/services/*` : finance (accounts, transactions, reconciliation, stats, metrics, imports), restaurant (expenses, bank_statements, dashboard, mappings), catalog, invoices, audit, reports, maintenance, importers.  
- Le module `backend/services/zero_click_jobs.py` orchestre le workflow asynchrone des jobs factures ; des tests (`tests/test_zero_click_jobs.py`, `scripts/test_zero_click_client.py`) couvrent tout le pipeline.

---

## 4. Core et modules métiers

- `core/data_repository.py` + `core/database_url.py` gèrent l’accès SQL.  
- Catalogue et produits : `core/catalog_repository.py`, `core/catalog_sql_repository.py`, `core/product_service.py`, `core/products_loader.py`, `core/product_input.py`.  
- PDF et extracteurs : `core/invoice_extractor.py`, `core/pdf_utils.py`, `core/cart_normalizer.py`, `core/price_history_service.py`, `core/price_correction_service.py`.  
- Inventaire : `core/inventory_service.py`, `core/inventory_classification.py`, `core/inventory_costing.py`, `core/inventory_forecast.py`, `core/consolidation_loader.py`, `core/restaurant_costs.py`, `core/cart_normalizer.py`.  
- Finance avancée : dossier `core/finance/` (insights, reconciliation, analytic_accounting, anomaly_detection, audit_trail, bank_reconciliation, event_sourcing, forecasting, inventory_intelligence, margin_calculator, rules_engine, supplier_scoring, transaction_line_defaults).  
- Services additionnels : `core/tenant_service.py`, `core/user_service.py`, `core/backup_manager.py`, `core/vendor_categories.py`, `core/event_handlers.py`, `core/parsers/` et `core/finance` modules.

---

## 5. Base de données & SQL

- DDL initial dans `db/init.sql` (tenants, restaurants, produits, mouvements_stock, triggers, vues).  
- Vues et structures `finance_*`, `dim_*`, `fact_*` orchestrées par `migrations/versions/` (ex. `20251211_zero_click_jobs`, `finance_matches`, `newcms_finance_classification`).  
- Scripts manuels `scripts/_sql/*.sql` (carburant, réalignement finance, restructurations) protègent la cohérence des tables.  
- Gouvernance qualité : `scripts/data_quality_scan.sql`, `scripts/data_quality_fix.sql`, `scripts/sql/data_quality_governance.sql`, `scripts/sql/price_guard.sql`.

---

## 6. Workflows & scripts

- Imports : `scripts/imports/*.py` (PDF/CSV bancaires/fournisseurs, import invoices, seed vendor dictionary).  
- Catalogue Eurociel : `scripts/catalog/*.py` (extraction, enrichissement, génération SQL, normalisation).  
- ETL / bancaires : `scripts/etl/` (parseurs LCL/BNP/SumUp, refresh_from_pdf, Analyze relevés, load_bank_entries).  
- Finance : `scripts/finance/*` (run_finance_reconciliation, insights, dedupe statements, audit counts).  
- Restaurant : `scripts/restaurant/*` (seeds, charges automatiques, cost centers, exports).  
- Maintien et vérification : `scripts/run_data_quality_fix.py`, `scripts/seed_cms_navigation.py`, `scripts/verify_cms_setup.py`, `scripts/verify_zero_click_setup.py`, `scripts/test_zero_click_client.py`, `scripts/audit_database.py`, `scripts/mobile_access.sh`, `scripts/document_similarity_graph.py`.
- Référentiel script : `scripts/README.md` (structure directories, usage).

---

## 7. Zero-Click + IA

- Pipeline `zero-click` : `scripts/apply_zero_click_migration.sh`, migration `20251211_zero_click_jobs.py`, endpoints `/api/invoices/zero-click/*` dans `backend/api/invoices.py` et services (`backend/services/finance`, `backend/services/zero_click_jobs.py`).  
- Workflow complet : upload PDF → suivi job via GET → liste jobs → prompt Ollama via `n8n_workflows/inventaire-api-ia.json`.  
- Docs : remplace désormais `docs/README_ZERO_CLICK.md`, `docs/ZERO_CLICK_ARCHITECTURE.md`, `docs/ZERO_CLICK_JOBS_ASYNC.md`, `docs/ZERO_CLICK_API_EXAMPLES.md`.  
- Tests & CLI : `tests/test_zero_click_jobs.py`, `scripts/test_zero_click_client.py`, migrations de vérification.

---

## 8. Automatisation de l’analyse

- `scripts/analysis/classify_dependencies.py` parcourt `backend`, `core`, `frontend`, `newCMS`, `monprojet`, `scripts`, `docs` pour :  
  1. Taguer chaque fichier (`#USÉ`, `#DEPRECATED`, `#WORK_IN_PROGRESS`).  
  2. Construire un graphe pondéré (poids ≈ taille importée) et générer `reports/dependency_graph.dot` + `reports/classification_summary.md`.  
- Utilise ce rapport pour identifier les dépendances critiques (fichiers lourds) et les zones de code legacy vs WIP.

---

## 9. Références

- `reports/classification_summary.md` et `reports/dependency_graph.dot` (avec la version PNG) documentent automatiquement les dépendances critiques et les catégories de fichiers.  
- Les README conservés (`docs/CARTOGRAPHIE_PROJET.md`, `docs/INDEX_TECHNIQUE.md`, `docs/DOCUMENTATION_PROJET.md`, `docs/README_ZERO_CLICK.md`, `docs/ZERO_CLICK_ARCHITECTURE.md`, `docs/ZERO_CLICK_JOBS_ASYNC.md`, `docs/ZERO_CLICK_API_EXAMPLES.md`) renvoient désormais à cette page comme source unique.  
- Les instructions de déploiement et de démarrage restent dans `README.md` (Docker Compose, scripts tests, dossier scripts).
