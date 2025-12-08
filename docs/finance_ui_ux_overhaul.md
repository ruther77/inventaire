# Finance UI/UX Overhaul – Plan détaillé (aligné sur `finance_tresury_refactor.md`)

Objectif : livrer une expérience finance fiable (restaurant = RESTO, épicerie = EPICERIE) sur les tables `finance_*`, avec import/reco, catégorisation assistée, filtres rapides et vues synthétiques. Cette note liste les lots, contrats d’API, exigences UX, tests et opérations.

## [1] Périmètre & principes
- Multi-entités natif (RESTO/EPICERIE) et filtres persistants.
- Pas de nouveau modèle : s’appuyer sur `finance_entities/accounts/transactions/transaction_lines/categories/bank_statements/lines`.
- Réduction de “autre” (objectif <10 %) et accélération des tâches récurrentes (import/reco/clôture/TVA).
- Pagination/tri server-side, actions en masse, erreurs explicites.

## [2] Architecture cible & flux
- Ingestion : import CSV/PDF → `finance_bank_statements/lines` → `finance_transactions/transaction_lines`.
- Catégorisation : règles (mots-clés) + suggestions “autre-top” + batch recat.
- Reco : rapprochement auto, anomalies à traiter, statut par relevé.
- Consultation : tableaux paginés/filtrés (transactions, relevés, catégories, fournisseurs/factures), vues synthétiques (cash, groupes).

## [3] Backlog par lots (actionnable)
1) Backend pagination/tri : GET paginé/trié pour transactions, relevés, catégories, fournisseurs/factures (+ index SQL).
2) Suggestions/batch recat : endpoint “autre-top” (libellés fréquents), autocomplete catégories, batch-categorize (IDs ou règle mots-clés).
3) Reco/import observabilité : statut d’import, anomalies reco, logs erreurs parsing, métriques (taux auto, durée import).
4) Front Transactions/Catégories : table virtualisée, filtres persistants (entité, compte, période, catégorie, montant, texte), edit inline catégorie, bulk recat, éditeur de règles.
5) Relevés & Reco : upload CSV/PDF (drag&drop), stepper état (upload→parse→validation→status), lancer reco, tableau anomalies/matches avec actions.
6) Overview & Fournisseurs : KPIs (soldes, cash-in/out, part “autre”, reco en attente), graph trésorerie, liste fournisseurs/factures avec filtres/tri.
7) Design system & QA : tokens (couleurs/espacements/polices), composants (tables, filtres, badges, toasts, modales), accessibilité, e2e/perf.

## [4] API/Contrats (à livrer)
- Transactions : `GET /finance/transactions?page&size&sort&entity_id&account_id&date_from&date_to&category_id&amount_min&amount_max&q`.
- Relevés : `GET /finance/bank-statements?page&size&sort&account_id&period&status`.
- Catégories : `GET /finance/categories?page&size&entity_id&type` ; `GET /finance/categories/suggestions/autre-top` (payload `{key,count,examples[]}`).
- Batch recat : `POST /finance/transactions/batch-categorize` body `{transaction_ids[]?, rule?: {keywords[], category_id}}` → `{updated, category_id, rule_applied?}`.
- Autocomplete catégories : `GET /finance/categories/suggestions/complete?q=`.
- Reco : `POST /finance/reconciliation/run` ; `GET /finance/reconciliation/runs/{id}/anomalies` → `{run_id,status,anomalies:[{bank_line_id,transaction_id?,reason,confidence}]}`.
- Import : `POST /finance/bank-statements/import` (CSV/PDF) → `{status, inserted, errors[]}` ; lister import errors via `GET /finance/bank-statements?status=error`.
- Sécurité : filtrage par `entity_id`, validation Pydantic, erreurs 4xx claires.

## [5] Frontend UX (desktop + mobile)
- Overview : KPIs (soldes par compte, cash-in/out période, part “autre”, reco en attente), graph ligne trésorerie, alertes (autre>seuil, import erreur).
- Transactions : table virtualisée, filtres persistants (localStorage), recherche `q`, badges statut/reco, edit inline catégorie, sélection multi + bulk recat, toasts/undo court.
- Catégories : stats par catégorie, top “autre” (libellés fréquents), éditeur de règle (mots-clés→catégorie) avec prévisualisation.
- Relevés & Reco : upload dropzone + stepper, état parsing/reco, tableau anomalies/matches avec actions de validation/rejet.
- Fournisseurs/Factures : liste filtrable (statut, échéance, entité/compte), liens vers transactions/payments.
- Accessibilité : focus visible, contrastes AA, navigation clavier, aria tables/formulaires.

## [6] Données & perf
- Index à ajouter :  
  - `finance_transactions(entity_id, account_id, date_operation)` ; `finance_transactions(category_id)` si champ existe.  
  - `finance_transaction_lines(category_id)` ; trigram sur libellé/note pour `q`.  
  - `finance_bank_statements(account_id, period_start, period_end)` ; `finance_bank_statement_lines(statement_id, date_operation)`.
- Pagination stricte (page/size) et tri whitelist (date_operation|amount|category|account).
- Latence cible filtres <1s sur 10k lignes.

## [7] Tests & QA
- API contract tests pour chaque endpoint (pagination, filtres, batch-categorize, suggestions, import error).
- e2e (Cypress) : import→reco→bulk recat→filtres persistants→undo.
- Perf : mesure temps réponse sur 10k+ transactions, temps import <30s.
- Accessibilité : focus/clavier/aria, contrastes.

## [8] Déploiement & ops
- Feature flag par entité pour activer la nouvelle UI.
- Playbook : backup DB, migrations (déjà en place via Alembic), déploiement, rollback.
- Observabilité : logs import/reco, métriques part “autre”, taux reco auto, durée import.

## [9] À brancher maintenant (état)
- Backend restaurant : routes existantes ajustées pour lire `finance_*` (chart should reflect new data après restart API).
- Rester à faire : nouveaux endpoints paginés + suggestions + batch recat + UI côté front (tables/filtres/stepper import).

## [10] Prochaines actions recommandées
1) Implémenter endpoints paginés + suggestions (lots 1/2) avec validations Pydantic.  
2) Ajouter index SQL listés en [6] via migration Alembic.  
3) Mettre en place table virtualisée + filtres persistants + bulk recat côté front.  
4) Ajouter stepper import + écran anomalies reco.  
5) Activer feature flag et lancer e2e perf/accessibilité.  
