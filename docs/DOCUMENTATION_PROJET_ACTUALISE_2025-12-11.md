# Documentation Projet - État actualisé (11 Décembre 2025 - MAJ)

Ce document synthétise l'état courant du projet (backend, frontend, données) en référence à `DOCUMENTATION_PROJET.md`, sans le modifier.

---

## 1. Vue d'ensemble

- **Base ciblée** : `epicerie` (docker-compose).
- **Version Alembic** : `20251213_fact_invoices` (inclut matches/anomalies finance, dimensions supplier/category/product, `dim_tenant`, `dim_date`, `fact_invoices`, colonnes `currency/metadata` sur `finance_invoice_documents`).
- **Données importées** :
  - Factures : METRO, TAIYAT, EUROCIEL segmentées par `invoice_id` → 415 factures (`finance_invoice_documents`) consolidées, quantités/prix HT/TTC renseignés.
  - Relevés bancaires (parseurs par position) : LCL (NOUTAM + L'INCONTOURNABLE), BNP Angèle, SumUp Incontournable.
  - Consolidation : `fact_invoices` et `finance_invoice_documents` alimentés ; rapprochement bancaire actif (voir §5/§6).
- **Front** : scénarios 3.x implémentés mais actions avancées à brancher (Cockpit batch ACK, import facture actions, catalogue inline, rapprochement IA, décisions cash-flow).

---

## 2. Stack et métriques

- Backend : FastAPI 3.11, SQLAlchemy/Alembic, Postgres 16.
- Frontend : React 18 + Vite 5, TanStack Query, Tailwind.
- Migrations majeures récentes : `20251211_finance_fix`, `20251212_dim_*`, `20251213_fact_invoices`, `20251212_finance_invoice_documents_*`.
- Tables dimensionnelles : `dim_tenant` (1), `dim_supplier` (3), `dim_category` (30), `dim_product` (1 497), `dim_date`.
- Tables factuelles : `fact_invoices` (5 180 lignes consolidées non nulles), `finance_bank_statement_lines` (10 039 lignes).
- Historique prix : `produits_price_history` enrichi d’une colonne `produit_id` (pas de `recorded_at`, utilisation de `facture_date`).

---

## 3. Schéma BDD (ajouts récents)

- `finance_transactions` : alias `montant`, `date_transaction`.
- `processed_invoices` : `total_ttc`.
- `finance_bank_invoice_matches`, `finance_anomaly_flags` créées.
- `finance_invoice_documents` : `supplier_id`, `supplier_name`, `currency`, `metadata`, `updated_at`, index unique `(tenant_id, invoice_reference)`.
- Dimensions : `dim_tenant`, `dim_date`, `dim_supplier`, `dim_category`, `dim_product`.
- Fact : `fact_invoices` (tenant/date/supplier/document/product/category, quantity, unit_cost_excl_tax, vat_rate, currency).

---

## 4. Données importées / qualité

- Factures METRO/TAIYAT/EUROCIEL importées et consolidées (0 erreur SQL).
- Relevés bancaires importés (LCL NOUTAM/RESTO, BNP, SumUp) via scripts unitaires après install `pdftotext`.
- **Gaps corrigés** :
  - Mapping quantités/prix des parseurs corrigé (alias conservés, montants recalc). `fact_invoices.quantity` et `unit_cost_excl_tax` non nuls.
  - `finance_invoice_documents.total_excl_tax/total_incl_tax` renseignés par facture (segmentées).
- **Gaps restants** :
  - Catégorisation produits partielle (fallback libellé/barcode), à affiner.
  - `data_quality_report.md` signale encore prix/quantités manquants dans `produits`/`stock` côté application historique.

---

## 5. Front Scénarios 3.x (UX_NEXT_GEN_2025)

- 3.1 Cockpit : branché sur `/cockpit/overview`, ACK OK, batch "Tout traiter" et routage actions à implémenter.
- 3.2 Import Facture : carte traitement affichée, snapshots, actions (lier/créer/contester/valider stock) non câblées API/polling.
- 3.3 Catalogue Inline Everything : smart table + drawer, suggestions IA basiques ; manquent actions ligne (commander/analyser) + drawer complet (prix/fournisseurs/historique) + branchements API.
- 3.4 Rapprochement IA : suggestions rendues, mais flux réel dépend de `finance_bank_invoice_matches`; CTA appliquer/rejeter/détails et KPI état à brancher.
- 3.5 Décisions assistées : panneau présent, données mock ; à alimenter via API (décisions/forecast cash-flow) + graph cash-flow.

---

## 6. Plan d'action (ajout à la roadmap)

1) **Audit parsers (banques & fournisseurs)**  
   - Mesurer couverture champs (montants, quantités, libellés, dates) par fichier.  
   - Détecter anomalies (zéros, valeurs aberrantes), produire rapport JSON/CSV par parseur/fichier.  
   - Deux algos par parseur : (a) fidélité str/float (rejeu du brut + delta), (b) fidélité de catégorisation (banque vs rules / produit vs catalogue).  
   - Banques : taux de catégorisation (KeywordAnalyzer), libellés non mappés.  
   - Factures : couverture `prix/quantité`, mapping colonnes variantes, cohérence HT/TTC.

2) **Consolidation factures fiable**  
   - Mapping montants/quantités étendu implémenté (prix_achat/prix_unitaire/quantite_recue/qte_init/montant_ht/montant_ttc conservés).  
   - Segmentation par `invoice_id` activée : chaque facture d’un PDF est un document distinct (`finance_invoice_documents`, `fact_invoices`).  
   - Rejouer les imports supplémentaires (nouveaux fichiers) via sync → `fact_invoices` propres.  
   - Fallback produit/catégorie robuste (slug libellé/sku) présent, à compléter par enrichissement catalogue.

3) **Front actions**  
   - Cockpit : batch ACK et routage CTA.  
   - Import facture : actions attention (lier/créer/contester/valider stock) + polling backend.  
   - Catalogue : drawer enrichi + actions "Commander/Analyser" branchées.  
   - Rapprochement IA : flux `finance_bank_invoice_matches`, CTA appliquer/rejeter/détails, KPI état (en s’appuyant sur matches auto/pending).  
   - Décisions : alimentation API + graph cash-flow 30j, CTA appliquer/simulation.

4) **Data quality**  
   - Corriger prix/quantités nulles dans `produits`/`stock` (backfill à partir des PDF ou last known price).  
   - Rejouer le scan `data_quality_report.md` après backfill.

---

## 7. Échantillon d’état (après imports)

- `fact_invoices` : 5 180 lignes consolidées, `quantity` et `unit_cost_excl_tax` non nuls (max 146.29).  
- `finance_invoice_documents` : 415 factures segmentées, totaux HT/TTC renseignés.  
- `dim_product` : 1 497 (incl. fallback), `dim_category` : 30, `dim_supplier` : 3, `dim_tenant` : 1.  
- `produits` : ~1 596 entrées, beaucoup de prix/TVA à 0 signalés par `data_quality_report.md`.

---

## 8. Instructions de re-run

- Migrations : `docker compose exec api alembic upgrade head`.  
- Imports factures (stock + consolidation) : `docker compose exec api sh -c 'PYTHONPATH=/app python scripts/imports/import_invoice_files.py <DIR> --tenant epicerie --supplier <SUP> --initialize-stock --force'`.  
- Imports factures (consolidation seule, sans mouvements) : lancer dans le conteneur API `extract_invoice_lines -> enrich_lines_with_catalog -> sync_invoice_dataframe` (segmenté par `invoice_id`) sur `/app/METRO`, `/app/TAIYAT`, `/app/EUROCIEL`.
- Rapprochement banque/factures (sorties uniquement) : `run_reconciliation_job(tenant_id=1, amount_tolerance=300.0, max_days_difference=120, auto_threshold=0.65)`. Résultat actuel : ~283 matches (128 auto / 155 pending).
- Imports relevés : LCL (`import_lcl_pdf.py --entity EPICERIE/RESTO --account-label "LCL - ..."`) ; BNP (`import_bnp_pdf.py`) ; SumUp (`import_sumup_pdf.py`).

---

## 9. Risques / blocants

- Quantités/prix non renseignés dans les parseurs → consolidation avec valeurs à 0.  
- Catégorisation produits minimale (dim_category) → analytics limités.  
- Front : actions non câblées peuvent surprendre les utilisateurs (CTA sans effet).

## 10. Valeurs clés & workflows partagés

- **Valeur produit** : une plateforme unifiée Épicerie + Restaurant + Finance, multi-tenant, avec un spine FastAPI qui sert une SPA Vite et un module `newCMS` mobile. Le focus est la traçabilité complète (factures → mouvements → marges → décisions).  
- **Valeur technique** : chaque import/flow est documenté via `scripts/README.md` et orchestré par des CLI `scripts/imports/*.py`, `scripts/etl/*.py`, `scripts/finance/*.py`, `scripts/restaurant/*.py`. Le script `scripts/analysis/classify_dependencies.py` permet d’identifier les fichiers critiques et de surveiller leur classification (#USÉ/#DEPRECATED/#WORK_IN_PROGRESS).  
- **Workflow critique « factures zero-click »** :
  1. Upload PDF via `/api/invoices/zero-click/jobs` (backend/api/invoices.py).  
  2. Service `backend/services/zero_click_jobs.py` génère un job, stocke en `processed_invoices`, déclenche extraction `core/invoice_extractor.py`.  
  3. Front/PWA pollent `/api/invoices/zero-click/jobs/{id}` puis affichent résultats (job2document, anomalies).  
  4. n8n + Ollama (`n8n_workflows/inventaire-api-ia.json`) consomment l’API pour produire des recommandations d’actions (sujets déjà testés via `tests/test_zero_click_jobs.py` et `scripts/test_zero_click_client.py`).  
- **Workflow catalogue/intelligence** :
  1. `scripts/import_invoice_files.py` ou Eurociel/Catalog scripts gonflent `produits`, `produits_price_history`, `fact_invoices`.  
  2. `core/vendor_categories.py` alimente les règles de catégorisation utilisées par `backend/services/finance/rules.py` et `frontend/hooks/useFinance`.  
  3. Modules `core/finance/margin_calculator.py`, `core/finance/forecasting.py`, `core/finance/inventory_intelligence.py` alimentent `/margins`, `/forecasting`, `/inventory-intelligence` (API FastAPI), consommés par `frontend/features/intelligence/*`.  
- **Workflow restaurant** :
  1. `scripts/restaurant/seed_*` démarre les tables `ingredients`, `plats`, `plat_ingredients`, `restaurant_depenses`.  
  2. `backend/services/restaurant` ingère `restaurant_bank_statements`, `restaurant_depenses`, `transfers` pour produire dashboards.  
  3. Front `frontend/src/features/restaurant/*` utilise hooks (`useRestaurant`) pour afficher coûts, ingrédients, alertes mises à jour en temps réel.

## 11. Points à communiquer à l’équipe

- Les **hooks principaux** (`useInventoryIntelligence`, `useForecasting`, `useCookpit`, `useBankReconciliation`, `useAuditTrail`, `useSupplierScoring`, `useMargins`) sont documentés dans `frontend/src/hooks`. Ils sont la porte d’entrée pour ajouter de nouvelles pages ou connecter des workflows IA.  
- Le **client API** (`frontend/src/api/client.js`) regroupe les appels (400+ lignes) et doit être étendu au gré des nouveaux endpoints (ex: `zero-click` status détaillé, `newcms/mobile`).  
- Les **tests Cypress** (`frontend/cypress/`) couvrent chaque feature majeure ; utiliser `npm run test:e2e` pour valider intégrations UI.  
- Les **scripts d’analyse** (`scripts/analysis/classify_dependencies.py`) fournissent un dot + summary ; ils sont à relancer après une grosse refonte pour détecter les dépendances lourdes et les fichiers qui restent en `#DEPRECATED`.  
- Les **rapports Postgres** : `reports/classification_summary.md` et `reports/dependency_graph.dot` (à générer en PNG avec Graphviz) doivent être consultés avant de toucher à des libs massives (ex: Next, Rollup) notées dans le top dépendances.
