# Roadmap Backend – newCMS (Base du produit)

Objectif : newCMS devient la couche de présentation configurable pour toutes les vues (Cockpit, Opérations, Finance, Restaurant, Intelligence, Config, Alertes, Mobile). On repose sur les services existants, on formalise CMSBlocks/Datasources, on respecte Conventions et Index technique, et on maintient le multitenant aligné avec l’app.

---

## 1. Cockpit (vue 360° / Morning Brief)

### Endpoints existants à réutiliser
- `/cockpit/overview` (KPIs, alertes, prévisions stock/cash) — `backend/api/cockpit.py`
- `/cockpit/alerts` + `POST /cockpit/alerts/{id}/acknowledge`
- `/forecasting/cash-flow`, `/forecasting/sales` — `backend/api/forecasting.py`
- `/anomaly-detection/*` (résumés, anomalies critiques) — `backend/api/anomaly_detection.py`
- `/dashboard/*` (inventaire, marges) — `backend/api/dashboard.py`

### Ce qui manque pour newCMS
- Endpoint agrégé `GET /newcms/cockpit` qui combine : KPIs cockpit + alertes + anomalies critiques + prévisions (cash/stock) + suggestions IA.
- Badge alertes dynamique (critique/urgent).
- Option: endpoint `/newcms/cockpit/actions` pour lister les CTA actionnables (ack, import facture, rapprochement à traiter).

### Tables / services concernés
- `finance_*`, `fact_invoices`, `finance_bank_statement_lines`, `finance_bank_invoice_matches`
- Services : `backend/services/dashboard.py`, `core/finance/forecasting.py`, `backend/api/cockpit.py`

### Manquants/à améliorer
- Agrégation côté service (pas seulement proxy).
- Tests API sur l’agrégateur (mocks cockpit/forecast/anomalies).
### Conventions (voir Conventions.md)
- ResponseWrapper : structure `success/data/error/meta`.
- Slugs/paths en kebab-case, JSON keys snake_case.
- Pagination/filtres standard (`page`, `per_page<=100`, `q`, `date_from`, `date_to`).

---

## 2. Opérations (Catalogue, Factures, Stock, Prix)

### Endpoints existants
- Catalogue : `/catalog/products`, `/catalog/categories`, `/catalog/vendors`, `/catalog/products/barcode/{code}`
- Stock : `/stock/movements`, `/stock/movements/summary`, `/stock/movements/timeseries`
- Factures : `/invoices/extract`, `/invoices/extract/file`, `/invoices/import`, `/invoices/catalog/import`, `/invoices/history`, `/invoices/zero-click`, `/invoices/lines/link|create-product|confirm-stock` (nouveaux), `/invoices/zero-click/jobs` (nouveau)
- Prix : `/prices/history`, `/prices/corrections`

### Ce qui manque pour newCMS
- Endpoint agrégé `GET /newcms/operations/overview` : stock critique + factures récentes + anomalies prix + actions import.
- Proxy paginé simplifié pour les listings CMS : `/newcms/catalog`, `/newcms/stock`, `/newcms/invoices`.
- Support polling/état pour zéro-click : `/invoices/zero-click/jobs/{id}` à brancher front.
- Actions “lier/créer produit/valider stock” exposées via `/invoices/lines/*` : ajouter tests + docs.

### Tables / services concernés
- `produits`, `mouvements_stock`, `produits_price_history`, `processed_invoices`, `fact_invoices`
- Services : `backend/services/invoices.py`, `core/products_loader.py`, `core/consolidation_loader.py`, `core/inventory_service.py`

### Manquants/à améliorer
- Tests backend sur les nouveaux endpoints `/invoices/lines/*` et `/zero-click/jobs`.
- Agrégateur opérations (résumés stock/factures) + cache court (60s) pour CMS.
### Conventions
- Réponses paginées: meta avec `page`, `per_page`, `total`.
- Filtres `q`, `status`, `category`, bornes date/montant.

---

## 3. Finance (Transactions, Rapprochement, Comptes)

### Endpoints existants
- `/finance/transactions/search`, `/finance/accounts`, `/finance/categories`, `/finance/import/bank-statements`
- Rapprochement : `/bank-reconciliation/*` (run, unmatched transactions/invoices, manual match)
- Règles : `/rules-engine/rules` (CRUD)
- Marges : `/margins/products|dishes`

### Ce qui manque pour newCMS
- Endpoint agrégé `GET /newcms/finance/overview` : stats rapprochement (matched/pending/unmatched), cash-flow 30j, suggestions IA rapprochement (wrapper `bank_reconciliation`), transactions récentes.
- Simplifié `/newcms/finance/transactions` : proxy paginé (q, date_from/to, amount range).
- CTA actions : appliquer suggestions rapprochement, créer règle de catégorisation depuis CMS.

### Tables / services concernés
- `finance_transactions`, `finance_bank_statement_lines`, `finance_bank_invoice_matches`, `finance_accounts`, `finance_rules`
- Services : `backend/services/finance/*`, `backend/api/bank_reconciliation.py`, `backend/api/finance.py`

### Manquants/à améliorer
- Agrégateur finance, tests E2E rapprochement appliquant `createMatch` en mode IA.
### Conventions
- Même format paginé que opérations.
- Scinder vue groupe (Epicerie+Restaurant) vs comptes individuels (6 comptes).

---

## 4. Restaurant

### Endpoints existants
- `/restaurant/*` (plats, ingrédients, coûts, alertes, stock resto)
- `/restaurant/charges/*`, `/restaurant/price-history/*`

### Ce qui manque pour newCMS
- `GET /newcms/restaurant/overview` : coûts plats, alertes resto, stock par emplacement.
- Proxy mobile inventaire : `/newcms/restaurant/inventory-mobile` (liste items scannables).

### Tables / services concernés
- `plats`, `ingredients`, `plat_ingredients`, vues `v_bom_*`, `stock_mouvements` (resto)
- Services : `backend/services/restaurant/*`, `core/restaurant_costs.py`

### Manquants/à améliorer
- Agrégateur restaurant, endpoints mobiles dédiés (scan, +1/-1 stock).

---

## 5. Intelligence (IA/Analytics)

### Endpoints existants
- `/inventory-intelligence/*`, `/forecasting/*`, `/anomaly-detection/*`, `/supplier-scoring/*`, `/margins/*`

### Ce qui manque pour newCMS
- `GET /newcms/intelligence/overview` : top anomalies, prévisions clés, scoring fournisseurs, recommandations.
- Endpoint pour recommandations/decisions IA (non présent aujourd’hui) à définir ou wrapper existants (`DecisionPanel` mock côté front).

### Tables / services concernés
- `fact_invoices`, dimensions `dim_*`, `finance_anomaly_flags`, `finance_bank_invoice_matches`
- Services : `core/finance/*`, `backend/services/dashboard.py`

### Manquants/à améliorer
- Endpoint de recommandations IA consolidées (aujourd’hui mock côté front).

---

## 6. Configuration / Audit

### Endpoints existants
- `/admin/*`, `/audit-trail/*`, `/rules-engine/*`, `/settings` (via env)

### Ce qui manque pour newCMS
- Exposer config de navigation CMS (pages/nav) déjà CRUD via `/newcms/nav` mais à sécuriser par rôle.
- Vue audit CMS : wrapper `/audit-trail/report`.

---

## 7. Mobile / Inventaire

### Endpoints existants
- Stock / catalogue utilisés par l’app web (`/catalog/products`, `/stock/movements`).

### Ce qui manque pour newCMS
- Endpoints mobiles légers : `/newcms/mobile/inventory` (liste scannable, filtres rupture), `/newcms/mobile/scan` (lookup code-barres).

---

## 8. Actions à réaliser (backend)

1) **Agrégateurs newCMS (façades)**  
   - `/newcms/cockpit` (KPIs, alertes, anomalies, prévisions)  
   - `/newcms/operations/overview` (stock critique, factures récentes, anomalies prix)  
   - `/newcms/finance/overview` (rapprochement, cash, transactions récentes)  
   - `/newcms/restaurant/overview` (coûts plats, stock resto)  
   - `/newcms/intelligence/overview` (anomalies top, prévisions clés, scoring)  
   - `/newcms/mobile/*` (inventory list + scan)

2) **Proxies simplifiés**  
   - `/newcms/catalog`, `/newcms/stock`, `/newcms/invoices`, `/newcms/finance/transactions` (pagination + filtres simples).

3) **Zéro-click / factures**  
   - Finaliser `/invoices/zero-click/jobs` (mode async réel ou simuler statut).  
   - Tests pour `/invoices/lines/link|create-product|confirm-stock`.

4) **Sécurité / Auth**  
   - Décider si newCMS routes passent par `_security_dependencies` (RBAC) ou non.  
   - Ajouter scopes/roles si nécessaire.

5) **Tests backend**  
   - Pytest sur agrégateurs newCMS (mock des services).  
   - Pytest sur nouvelles routes factures.

6) **Documentation**  
   - Ouvrir un swagger tag “newcms” avec schémas `CMSPage/CMSNav` et agrégateurs.  
   - Aligner `docs/DOCUMENTATION_PROJET.md` avec la présence des façades newCMS.

---

## 9. Données / Tables

- `cms_pages` (slug, title, description, content JSONB, status, tenant_id)
- `cms_nav_items` (label, path, section, order_index, icon, tenant_id)
- Aucune donnée métier du CMS n’est encore peuplée ; besoin d’upserts initiaux (nav des 6 vues, pages placeholder).

---

## 10. Scripts / Services à prévoir

- Scripts de seed : navigation par défaut (Cockpit, Opérations, Finance, Restaurant, Intelligence, Config).  
- Services de façade : modules Python newcms_* pour orchestrer les appels aux services existants (cockpit, finance, catalog, etc.) sans dupliquer SQL.

---

## 11. Suivi

- Status actuel : endpoints `newcms/pages|nav` CRUD + tables créées ; pas d’agrégateurs métier.  
- Étapes suivantes : implémenter les agrégateurs et proxies, décider RBAC, ajouter tests.

---

## 12. Tests backend
- Pytest sur façades newCMS (mocks services existants).
- Pytest sur factures `/invoices/lines/*` et `/zero-click/jobs`.
- Pytest sur règle stock Restaurant (rejet de sources externes).
- Conventions tests : couvrir happy path + erreurs 400/401/404 ; fixtures par tenant (epicerie, restaurant) ; valider ResponseWrapper (success/data/error/meta).
