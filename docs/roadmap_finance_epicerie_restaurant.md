# Feuille de route Finance / Épicerie / Restaurant

Document de cadrage pour aligner les futures itérations. Chaque section décrit l'état actuel, les briques à mettre en place (backend, data, frontend) et l'ordre de priorité.

---

## 1. Finance : rapprochement et détection

### État actuel
- Import PDF factures METRO (script `scripts/import_invoice_files.py`) → tables `fact_invoices`, `dim_*`.
- Relevés bancaires restaurant déjà stockés (`restaurant_bank_statements`, vues associées) mais sans rapprochement automatique.

### Objectifs
1. **Rapprochement banque ⇄ factures**
   - Construire un moteur hybride règles + fuzzy:
     - Règles déterministes: exact match sur montant/date ±1j, fournisseur connu.
     - Fuzzy: similitude chaîne (ratio), heuristique sur TVA/montant HT.
     - Étape ML légère: logistic regression ou gradient boosting pour scorer match.
   - Pipeline:
     1. Extraction features (`core/finance/reconciliation_features.py`).
     2. Scoring + décision (seuil calibré).
     3. Journalisation des matches (table `finance_bank_invoice_matches`).
   - API REST `/finance/reconciliation/run` (POST) + `/finance/reconciliation/pending` (GET).
   - UI: écran « Rapprochement » (vue type Kanban: match auto, à valider, rejeté).

2. **Détection récurrences & anomalies**
   - Identifier charges fixes (méthode STFT simple + clustering sur libellé/montant).
   - Détection anomalies:
     - IsolationForest sur montants/dates.
     - Bande de confiance par série temporelle (rolling median ±k*IQR).
   - Table `finance_recurring_expenses`, `finance_anomaly_flags`.
   - UI: graphiques (sparklines) + notifications.

3. **Consolidé multi-entités**
   - Intégrer les flux perso + L’Incontournable + NOUTAM: unifier dans `dim_entity`.
   - Vue matérialisée `finance_capital_overview` alimentée quotidiennement.
   - API `/finance/capital/overview`.
   - Front: widget « Capital en mouvement » (stacked area + treemap).

### Priorité / Sprint
1. Implémenter pipeline rapprochement (backend + batch CLI) + écran validation.
2. Ajouter détection récurrences/anomalies.
3. Étendre au consolidé multi-entités.

---

## 2. Épicerie : stock intelligent

### État actuel
- Tables fact/invoices renseignées, écran import, suivi prix partiel.
- Pas encore de coût moyen/FIFO ni de classification ABC-XYZ.

### Objectifs
1. **Calcul coût moyen + FIFO**
   - Créer table `inventory_cost_layers` (tenant_id, product_id, batch_id, qty, unit_cost, received_at).
   - Mécanisme:
     - Entrées stock → création couche FIFO.
     - Sorties → consommation couches FIFO + recalcul coût moyen pondéré (`inventory_products.average_cost`).
   - Fonction SQL `apply_stock_movement_with_cost`.
   - Mettre à jour API `/inventory/summary` pour exposer coût moyen et valorisation.

2. **Classification ABC-XYZ**
   - ABC: basé sur valeur annuelle (CA ou consommation).
   - XYZ: variabilité (coefficient de variation demande).
   - Script `core/analytics/abc_xyz.py` → persist `inventory_classification` (A/B/C, X/Y/Z).
   - UI: badges sur catalogue + filtres.

3. **Prévision réappro (Prophet/ARIMA)**
   - Pipeline TS (étape Airflow future) mais MVP en batch Python `scripts/forecast_restock.py`.
   - Inputs: ventes quotidiennes, consommation, lead time.
   - Output: projection jours de couverture + recommandation commande.
   - API `/supply/plan` enrichie avec champ `auto_order_qty`.
   - UI: composant « Réappro auto » (slider cible jours, suggestions).

### Ordre
1. Coût moyen/FIFO (pré-requis valorisation + marge).
2. ABC-XYZ (utilise valorisation).
3. Prévisions (besoin séries temps stables).

---

## 3. Restaurant : coût matière & audits

### État actuel
- Tables `restaurant_ingredients`, `restaurant_plats`, historique prix partiel.
- Pas de moteur de coût matière dynamique ni d’alertes dérive.

### Objectifs
1. **Coût matière dynamique**
   - Job qui combine recettes (quantités ingrédient) × dernier prix (ou coût moyen restaurant).
   - Table `restaurant_plat_costs` (plat_id, cost, margin, updated_at).
   - API `/restaurant/plats/:id/cost`.
   - UI: colonnes coût/marge + tags (OK/Dérive).

2. **Alertes dérive**
   - Trigger quand marge < seuil ou coût ↑ x%.
   - Stocker alertes dans `restaurant_alerts`.
   - Notifications (sonner Toaster + page « Alertes »).

3. **Écarts théoriques vs réels**
   - Collecte consommations physiques (inventaire) vs théorique (ventes × recette).
   - Rapport `restaurant_consumption_audit` (écart %, statut).
   - UI: graphique radar ou table highlight écarts.

### Ordre
1. Calcul coût matière (dépend prix ingrédient).
2. Alertes dérive (s’appuie sur coûts/marges calculés).
3. Audit conso (nécessite historique mouvements ingrédients).

---

## 4. Frontend & UX

- Ajouter pages/modules correspondants :
  - `/finance/reconciliation`, `/finance/anomalies`, `/capital`.
  - `/inventory/classification`, sections « Réappro auto ».
  - `/restaurant/alerts`, `/restaurant/audit`.
- Gestion d’état: hooks React Query dédiés + context si besoin.
- Graphiques: réutiliser Recharts, badges UI existants.

---

## 5. Planning / Ressources

| Sprint | Cible principale | Détails |
| --- | --- | --- |
| S1 | Rapprochement banque + coût moyen/FIFO | Implémentation backend + écrans validation/valorisation. |
| S2 | ABC-XYZ + détection récurrences/anomalies | Scripts analytics + UI monitoring finance/stock. |
| S3 | Prévisions réappro + coût matière dynamique | Scripts Prophet/ARIMA, service coût plats. |
| S4 | Alertes dérive + audit conso + capital multi-entités | Finalisation reporting restaurant/finance. |

---

## 6. Pré-requis techniques
- Accès aux relevés bancaires (format PDF/CSV) pour entraînement fuzzy/ML.
- Historique mouvements stock précis (pour FIFO & audit).
- Paramétrage environnements (Airflow ou cron) pour jobs batch.
- Mise à jour `.env` + migrations Alembic pour nouvelles tables.

---

## 7. Prochaines actions
1. Valider ce plan fonctionnel.
2. Rédiger specs techniques détaillées par module (API, schémas tables).
3. Exécuter Sprint 1 (issues Git):
   - `feat/finance-reconciliation-engine`
   - `feat/inventory-fifo-cost`
   - `feat/frontend-auth-fix` (déjà livré)

--- 
