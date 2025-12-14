# NEWCMS Backend Roadmap

Document de cadrage pour brancher les CTA du nouveau front (newCMS) sur des endpoints réels. Les sections "Déjà fait" évitent les doublons, les sections "À faire" listent les développements backend à prioriser.

## État actuel (vérifié)
- ✅ `/newcms/cockpit` agrégateur Morning Brief – `backend/api/newcms/cockpit.py`
- ✅ `/newcms/operations` (overview, catalog, stock, invoices) – `backend/api/newcms/operations.py`
- ✅ `/newcms/finance` (overview, transactions, reconciliation/apply) – `backend/api/newcms/finance.py`
- ✅ `/newcms/restaurant` (overview) + `/newcms/mobile/*` (inventory, scan, adjust) – `backend/api/newcms/restaurant.py`
- ✅ `/api/newcms/intelligence/*` (overview, recommendations, apply, health, metrics) – `backend/api/newcms/intelligence.py`
- ✅ Routing FastAPI câblé dans `backend/api/newcms/__init__.py` et `backend/main.py`

## Priorités Semaine 1 (pour débloquer les boutons du front)
- Finance : endpoints d’actions ligne-à-ligne (marquer rapproché/ignore, reclasser catégorie, export CSV) en s’appuyant sur `finance_transactions` et `finance_reconciliations`.
- Règles de catégorisation : CRUD `finance_rules` + évaluation/ré-application sur un batch de transactions.
- Opérations : upload facture (PDF/CSV) + OCR/parse + création de brouillon d’import (table staging) avec état d’avancement (CTA dropzone, scanner, email).
- Opérations : endpoint de correction prix/TVA/produit sur les lignes d’un import, puis validation qui met à jour stock + historique prix.
- Cockpit : rendre les cartes "voir détail" actionnables via endpoints filtres (alerts, anomalies, ruptures) réutilisant les services existants.
- Restaurant : endpoint pour simuler l’impact marge/food-cost après changement de prix ou de recette (CTA "ajuster prix" / "changer fournisseur").
- Mobile inventaire : endpoint de création de mouvement multi-lignes (inventaire flash) pour le bouton "valider comptage".

## Backlog détaillé par page/CTA

### Cockpit (front: `frontend/src/newCMS/pages/CockpitPage.jsx`)
- Déjà fait : `/newcms/cockpit` renvoie KPIs/alerts/suggestions.
- À faire : endpoints ciblés pour les CTA "Voir détail" des alertes stock/anomalies (ex: `/newcms/operations/stock?status=critical`, `/newcms/intelligence/anomalies?severity=high`), avec pagination/filtre prêts pour le front.

### Operations (front: `OperationsPage.jsx`)
- Déjà fait : `/newcms/operations/overview`, `/catalog`, `/stock`, `/invoices`.
- À faire (dropzone/CTA Parcourir/Scanner/Email) :
  - `POST /newcms/operations/invoices/import` : upload PDF/CSV ou photo (base64) → ID d’import + statut.
  - `GET /newcms/operations/invoices/import/{id}` : statut, erreurs, lignes extraites.
  - `POST /newcms/operations/invoices/import/{id}/lines/{line_id}` : correction produit/TVA/quantité/prix.
  - `POST /newcms/operations/invoices/import/{id}/confirm` : applique stock + prix + écritures fournisseur (recycle `invoices_service` + `catalog_service`).
  - `POST /newcms/operations/invoices/import/{id}/cancel`.
  - Hook mail entrant : endpoint interne `POST /newcms/operations/invoices/email-webhook` (adresse factures@...).
- À faire (actions tableau) :
  - `POST /newcms/operations/price-anomalies/{product_id}/resolve` (motif + nouveau prix).
  - `POST /newcms/operations/orders` : création de commande fournisseur depuis recommandations.

### Finance (front: `FinancePage.jsx`)
- Déjà fait : `/newcms/finance/overview`, `/transactions`, `/reconciliation/apply`.
- À faire (CTA lignes transactions) :
  - `POST /newcms/finance/transactions/{id}/categorize` (category_id ou free text).
  - `POST /newcms/finance/transactions/{id}/ignore` (motif, réversible).
  - `POST /newcms/finance/transactions/{id}/reconcile-manual` (invoice_ids, commentaire) pour un rapprochement manuel sans suggestion IA.
  - `POST /newcms/finance/transactions/bulk-export` : export CSV filtré (mêmes filtres que `/transactions`).
- À faire (onglet Règles) :
  - CRUD `POST/GET/PUT/DELETE /newcms/finance/rules` (pattern libellé, montant, IBAN, priorité, action catégorie).
  - `POST /newcms/finance/rules/apply` : ré-application d’un set de règles sur un scope filtré.
- À faire (comptes bancaires) :
  - `GET /newcms/finance/accounts` + `POST /.../refresh` (synchro), `POST /.../simulate-cashflow` (pour le widget forecast).

### Intelligence (front: `IntelligencePage.jsx`)
- Déjà fait : overview/recommendations/apply/health/metrics.
- À faire :
  - `GET /api/newcms/intelligence/anomalies` : liste filtrable pour les CTA "Voir anomalies".
  - `POST /api/newcms/intelligence/forecasts/recompute` : relancer un calcul (stock/cash/prix).
  - `POST /api/newcms/intelligence/recommendations/{id}/feedback` : bouton "ignorer/valider" avec apprentissage.

### Restaurant (front: `RestaurantPage.jsx`)
- Déjà fait : `/newcms/restaurant/overview`.
- À faire :
  - `GET /newcms/restaurant/plats` (pagination + search) et `GET /.../plats/{id}` (détail recette/food-cost).
  - `POST /newcms/restaurant/plats/{id}/simulate` : simuler impact marge après changement de prix/recette.
  - `POST /newcms/restaurant/plats/{id}/supplier-switch` : recommandation de substitution fournisseur.

### Mobile inventaire (front: `MobileInventoryPage.jsx`)
- Déjà fait : `/newcms/mobile/inventory`, `/mobile/scan`, `/mobile/adjust`.
- À faire :
  - `POST /newcms/mobile/inventory/bulk-adjust` : appliquer plusieurs ajustements d’un coup (comptage flash).
  - `POST /newcms/mobile/inventory/sync` : push des ajustements en offline-first (optionnel mais utile).

### Config / multi-tenant / audit
- À faire :
  - Standardiser l’audit trail pour toutes les actions ci-dessus (table `audit_log` ou event bus).
  - Vérifier auth/tenant sur tous les nouveaux endpoints (réutiliser `get_current_tenant`).
  - Rate limiting léger sur uploads/scan pour éviter l’abus.

## Séquencement conseillé
1) Finance actions lignes + export (débloque les CTA principaux du front Finance).  
2) Pipeline import facture (upload → staging → correction → apply) pour la page Opérations.  
3) Rules Engine finance + ré-application.  
4) Endpoints détaillés anomalies/alerts pour Cockpit/Intelligence.  
5) Restaurant simulateurs marge/recette.  
6) Mobile bulk adjust + sync.  

## Tests à prévoir
- Tests FastAPI pour chaque nouveau endpoint (status, payload, multi-tenant, erreurs 400/404/422).
- Tests de workflow complet import facture (upload → correction → apply) avec fixtures PDF/CSV de test.
- Tests de règles finance (priorité, overlap, re-application) sur un dataset factice.
- Golden files pour exports CSV (Finance).
