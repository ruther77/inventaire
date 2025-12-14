<!-- #DEPRECATED -->
<!-- 📦 MODULE: FINANCE -->
# Documentation projet (dépréciée)

La documentation détaillant les modules (`core/`, `backend/services/`, `finance/*`) a été consolidée dans `docs/ARCHITECTURE.md`.

> Ce fichier sert uniquement de trace historique ; bascule toute révision vers `docs/ARCHITECTURE.md`.

## Revue complète du dossier `/monprojet` (en s’appuyant sur `docs/ARCHITECTURE.md` et `docs/DOCUMENTATION_PROJET_ACTUALISE_2025-12-11.md`)

- **Front/SPA** : la racine `frontend/src/` contient la SPA Vite+React, les hooks TanStack Query, les pages par domaine (finance, restaurant, cockpit, intelligence) et le module newCMS. Les fixtures Cypress et les tests unitaires s’appuient sur `frontend/src/api/client.js` (45+ endpoints).  
- **Backend** : `backend/main.py` monte tous les routers, dont les nouveaux services Intelligence (`inventory_intelligence`, `forecasting`, `margins`, `anomaly_detection`, `supplier_scoring`), ainsi que les routers `newcms` et `zero-click`. Les services `backend/services/*` consomment les modules partagés `core/*`.  
- **Core & data** : `core/finance/*` calcule marges, prévisions, réparations automatiques ; `core/invoice_extractor.py`, `core/products_loader.py`, `core/vendor_categories.py` alimentent la base `postgresql` (`db/init.sql` + `migrations/versions/`). `reports/classification_summary.md` documente les dépendances critiques identifiées par `scripts/analysis/classify_dependencies.py`.  
- **Scripts/Workflows** : `scripts/imports/`, `scripts/catalog/`, `scripts/etl/`, `scripts/finance/`, `scripts/restaurant/`, `scripts/data_quality_*`, `scripts/sql/*` sont décrits dans `docs/ARCHITECTURE.md`. `n8n_workflows/README.md` décrit l’intégration Ollama + API.  
- **Documentations réactivées** : Les anciennes sections (`docs/CARTOGRAPHIE_PROJET.md`, `docs/INDEX_TECHNIQUE.md`, `docs/README_ZERO_CLICK.md`, `docs/ZERO_CLICK_*`) existent toujours mais renvoient ici ou restent archivées avec leurs tags `#DEPRECATED`.

## Synthèse des pages prioritaires (état actuel vs objectif)

- [ ] `frontend/src/features/restaurant/ForecastsPage.jsx`
  - Flowchart actuel : données mock/fixtures → render tableaux statistiques et graphiques → aucune action live (CTA désactivées).  
  - Flowchart voulu : API `/restaurant/forecast` → `useForecasting` → affichage des KPI/courbes → actions « appliquer », « simuler », « suivre un objectif » (payloads POST).  
- [ ] `frontend/src/features/finance/FinanceTransactionsPage.jsx`
  - Flowchart actuel : routage vers `useFinance` pour listes + filtres → affichage table + boutons manuels (draft).  
  - Flowchart voulu : ajout de `rules_engine` + `anomaly_detection` → suggestions automatiques dans la table → workflow d’approbation (sélection → `batch_categorize` / `create_reconciliation`).  
- [x] `frontend/src/features/intelligence/ForecastPage.jsx`
  - Flowchart actuel : appels directs (hook `useForecasting` en cours de refactor) → rendus statiques (graph + KPI).  
  - Flowchart voulu : même flow, mais avec rerender automatique sur nouvelles données API (`/forecasting/cash-flow`, `/forecasting/price-trend`), plus actions « exporter », « demander revue ».  
- [ ] `scripts/imports/import_invoice_files.py`
  - Flowchart actuel : charger PDF/DOCX → `invoice_extractor` → enrichir catalogue → créer `fact_invoices` + `finance_movements` (seulement `epicerie`).  
  - Flowchart voulu : : ajouter séquence `inventory_intelligence` → produire `margin_calculator` → enregistrer `finance_matches` → signaler anomalies via `scripts/analysis/classify_dependencies.py` (immuté).  
- [x] `backend/api/invoices.py` (zero-click)
  - Flowchart actuel : réception PDF → job `zero_click_jobs` → status GET → `fact_invoices`/`processed_invoices` → réponse utilisateur.  
  - Flowchart voulu : conserver ce pipeline, avec extension `GET /api/invoices/zero-click/jobs/{id}/analysis` + trigger IA (Ollama/n8n) pour recommander actions (documenté dans `n8n_workflows/README.md`).
