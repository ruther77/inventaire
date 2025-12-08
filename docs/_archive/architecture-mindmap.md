# Carte mentale (flux inter-fichiers)

```
backend/main.py
├─ dépendances: backend/dependencies/{auth,security,tenant}.py
├─ routeurs API (epicerie): backend/api/{catalog,supply,audit,invoices,stock,dashboard,prices,maintenance,reports,admin,finance}.py
├─ routeurs API (restaurant): backend/api/restaurant.py
├─ routeur capital: backend/api/capital.py
└─ services utilisés par les routeurs: backend/services/**

backend/api/restaurant.py
└─ délègue au service restaurant: backend/services/restaurant.py
   ├─ lecture/écriture SQL: core/data_repository.py
   ├─ catalogue client: backend/services/catalog_data.py
   ├─ calcul marges plats: core/restaurant_costs.py
   ├─ prévisions conso: core/inventory_forecast.py
   ├─ règles fournisseurs: core/vendor_categories.py
   └─ parsing PDF: pypdf + regex internes

backend/api/reports.py
└─ agrégations: backend/services/reports.py → core/data_repository.py

backend/api/finance.py
└─ rapprochement & anomalies: backend/services/finance.py
   ├─ reconciliation job: core/finance/reconciliation.py
   └─ insights récurrents/anomalies: core/finance/insights.py

backend/api/catalog.py (et supply/audit/stock/prices/maintenance/admin/invoices/dashboard)
└─ chacun délègue à son service dédié sous backend/services/{catalog,supply,audit,stock,prices,maintenance,admin,invoices,dashboard}.py

backend/services/catalog_data.py
└─ requêtes SQL catalogue partagées (SPA + Streamlit) via core/data_repository.py

legacy/streamlit/app.py
└─ UI historique Streamlit
   ├─ consulte core/{data_repository,inventory_service,price_history_service,product_service}
   ├─ utilise backend/services/catalog_data.py pour les catalogues clients
   └─ appels ponctuels aux extracteurs: core/invoice_extractor.py, backend/services/invoice_utils.py

core/*
├─ data_repository.py : accès DB (engine, query_df/exec_sql)
├─ inventory_service.py : ventes/stock, utilisé par backend/main.py et Streamlit
├─ product_service.py : CRUD produits, utilisé par API et Streamlit
├─ price_history_service.py : historiques prix (Streamlit)
├─ invoice_extractor.py : parsing factures (Streamlit)
├─ vendor_categories.py : règles fournisseurs (restaurant)
├─ inventory_forecast.py : prévisions consommation (restaurant)
└─ restaurant_costs.py : calcul marges plats (restaurant)

frontend/*
├─ SPA React (Vite)
├─ API client: frontend/src/api/client.js → appelle endpoints FastAPI exposés par backend/main.py
└─ Features restaurant (ex: BankStatementAnalyzer) ↔ backend/api/restaurant.py

docs/restaurant/menu_seed.yaml
└─ jeu de données seed consommé par scripts/seed_restaurant.py et DB
```
