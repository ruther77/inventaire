# UX Next-Gen 2025 - État des Scénarios et Fonctionnalités

**Date de génération:** 15 Décembre 2025
**Version:** 2.0
**Objectif:** Vue complète des scénarios utilisateur avec analyse des fonctionnalités existantes et manquantes

---

## 1. Vision Produit

### 1.1 Philosophie UX

> "Transformer l'application d'un outil fonctionnel en une **expérience fluide et invisible** où l'utilisateur accomplit ses tâches sans friction cognitive."

### 1.2 Architecture Navigation (6 Vues Unifiées)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        NAVIGATION UX 2025                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [HEADER]  Logo | Tenant Selector | CommandBar | Alerts | User          │
│                                                                          │
│  ┌──────────────┬───────────────────────────────────────────────────┐  │
│  │   SIDEBAR    │              MAIN CONTENT                          │  │
│  │              │                                                    │  │
│  │  COCKPIT ◄──┼───  Vue 360° avec KPIs + Alertes                   │  │
│  │  Vue 360°   │                                                    │  │
│  │              │  ┌────────────────────────────────────────────┐   │  │
│  │  OPÉRATIONS  │  │  Onglets intégrés pour navigation rapide   │   │  │
│  │  ▼           │  │  Pilotage | Factures | Catalogue | Stock   │   │  │
│  │              │  └────────────────────────────────────────────┘   │  │
│  │  FINANCES    │                                                    │  │
│  │  ▼           │  ┌────────────────────────────────────────────┐   │  │
│  │              │  │  CONTEXTUAL PANEL (split view)              │   │  │
│  │  RESTAURANT  │  │  - Détails item sélectionné                 │   │  │
│  │  ▼           │  │  - Actions rapides                          │   │  │
│  │              │  │  - Historique                                │   │  │
│  │ INTELLIGENCE │  └────────────────────────────────────────────┘   │  │
│  │  ▼           │                                                    │  │
│  │              │                                                    │  │
│  │  PARAMÈTRES  │                                                    │  │
│  │              │                                                    │  │
│  └──────────────┴───────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Scénarios Utilisateur Principaux

---

### SCÉNARIO 1: Import Facture → Stock → Finance

```
┌─────────────────────────────────────────────────────────────────────────┐
│          FLUX: Import Facture → Extraction → Stock → Catégorisation      │
└─────────────────────────────────────────────────────────────────────────┘

   1. Import Facture PDF                    2. Extraction automatique
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  /operations/       │                 │  Core: invoice_     │
   │  factures/import    │ ───────────────►│  extractor.py       │
   │                     │                 │                     │
   │  [Drop PDF]         │                 │  → Lignes extraites │
   │                     │                 │  → Produits matchés │
   └─────────────────────┘                 └──────────┬──────────┘
                                                      │
                                                      ▼
   3. Mise à jour Stock                    4. Catégorisation Finance
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  Event:             │                 │  Rules Engine:      │
   │  INVOICE_IMPORTED   │ ───────────────►│  Catégorisation     │
   │                     │                 │  automatique        │
   │  → +Stock reçu      │                 │                     │
   │  → Prix MAJ         │                 │  → 94% confiance    │
   │  → Alerte si écart  │                 │  → Auto-validé      │
   └─────────────────────┘                 └─────────────────────┘
```

#### Fonctionnalités Existantes

| Fonctionnalité | Fichier | État |
|----------------|---------|------|
| Page import factures | `frontend/src/features/invoices/ImportPage.jsx` | Implémenté |
| Composant upload PDF | `frontend/src/features/invoices/components/InvoiceUploadCard.jsx` | Implémenté |
| Éditeur lignes facture | `frontend/src/features/invoices/components/InvoiceLinesEditor.jsx` | Implémenté |
| Actions import | `frontend/src/features/invoices/components/InvoiceImportActions.jsx` | Implémenté |
| API import factures | `backend/api/invoices.py` | Implémenté |
| Extracteur PDF | `core/invoice_extractor.py` | Implémenté |
| Service factures | `backend/services/invoices.py` | Implémenté |
| Hook import | `frontend/src/hooks/useInvoiceImport.js` | Implémenté |
| Historique factures | `frontend/src/features/invoices/components/InvoiceHistoryTable.jsx` | Implémenté |
| Liste factures | `frontend/src/features/invoices/components/InvoiceList.jsx` | Implémenté |
| Traitement facture | `frontend/src/features/invoices/components/InvoiceProcessingCard.jsx` | Implémenté |
| Sélecteur documents | `frontend/src/features/invoices/components/InvoiceDocumentSelector.jsx` | Implémenté |
| Panneau historique | `frontend/src/features/invoices/components/InvoiceHistoryPanel.jsx` | Implémenté |
| Stepper import | `frontend/src/features/finance/components/ImportStepper.jsx` | Implémenté |
| Rules Engine | `core/finance/rules_engine.py` | Implémenté |
| API règles | `backend/api/rules_engine.py` | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| Extraction IA Ollama | Intégration LLM local pour extraction intelligente | Haute |
| Preview PDF inline | Aperçu PDF côté gauche pendant édition | Moyenne |
| Matching produits amélioré | Fuzzy matching avec suggestions | Moyenne |
| Notification temps réel | Toast avec progression import | Basse |
| Historique import par session | Grouper imports par session utilisateur | Basse |

---

### SCÉNARIO 2: Alerte Stock → Commande → Prévision

```
┌─────────────────────────────────────────────────────────────────────────┐
│          FLUX: Alerte Stock Critique → Recommandation → Action           │
└─────────────────────────────────────────────────────────────────────────┘

   1. Alerte Cockpit                       2. Détail Produit
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  AlertsPanel:       │                 │  /operations/       │
   │  "⚠ Stock critique  │ ───────────────►│  inventaire/        │
   │   Tomates: 2 jours" │                 │  produit/123        │
   │                     │                 │                     │
   │  [Voir]             │                 │  Stock: 5kg         │
   │                     │                 │  Conso moy: 2.5kg/j │
   └─────────────────────┘                 │  Rupture: 2 jours   │
                                           └──────────┬──────────┘
                                                      │
                                                      ▼
   3. Recommandation EOQ                   4. Création Commande
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  Intelligence:      │                 │  Action:            │
   │  "Commander 50kg    │ ───────────────►│  Créer bon de       │
   │   chez METRO        │                 │  commande           │
   │   (EOQ optimal)"    │                 │                     │
   │                     │                 │  → Pré-rempli       │
   │  Score METRO: 8.5   │                 │  → Fournisseur      │
   │  Score SYSCO: 7.2   │                 │  → Quantité EOQ     │
   └─────────────────────┘                 └─────────────────────┘
```

#### Fonctionnalités Existantes

| Fonctionnalité | Fichier | État |
|----------------|---------|------|
| Cockpit alertes | `backend/api/cockpit.py` | Implémenté |
| Page Cockpit unifié | `frontend/src/features/cockpit/CockpitUnifiedPage.jsx` | Implémenté |
| Morning Brief | `frontend/src/features/cockpit/CockpitPage.jsx` | Implémenté |
| Stock summary | `backend/api/cockpit.py:_get_stock_summary()` | Implémenté |
| Intelligence inventory | `backend/api/inventory_intelligence.py` | Implémenté |
| Page Stock intelligent | `frontend/src/features/intelligence/InventoryIntelligencePage.jsx` | Implémenté |
| Calcul EOQ | `core/finance/inventory_intelligence.py` | Implémenté |
| Scoring fournisseurs | `core/finance/supplier_scoring.py` | Implémenté |
| API scoring | `backend/api/supplier_scoring.py` | Implémenté |
| Page scoring overview | `frontend/src/features/intelligence/SupplierScoringOverviewPage.jsx` | Implémenté |
| Liste fournisseurs | `frontend/src/features/intelligence/SuppliersListPage.jsx` | Implémenté |
| Détails fournisseur | `frontend/src/features/intelligence/SupplierDetailsPage.jsx` | Implémenté |
| Page catalogue | `frontend/src/features/catalog/CatalogPage.jsx` | Implémenté |
| Hook stock | `frontend/src/hooks/useStock.js` | Implémenté |
| Mouvements stock | `frontend/src/features/stock/StockMovementsPage.jsx` | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité | Statut |
|----------------|-------------|----------|--------|
| ~~Fiche produit détaillée~~ | ~~Page `/inventaire/produit/:id` avec timeline events~~ | ~~Haute~~ | **FAIT** |
| ~~Génération bon de commande~~ | ~~Créer commande pré-remplie depuis suggestion~~ | ~~Haute~~ | **FAIT** |
| CTA "Commander" depuis alerte | Action directe depuis AlertsPanel | Moyenne | En attente |
| Notification push rupture | Alerte temps réel sur rupture imminente | Moyenne | En attente |
| Simulation impact cash-flow | Afficher impact trésorerie avant commande | Basse | En attente |

#### Nouveaux Fichiers Créés (S2)

| Fichier | Description |
|---------|-------------|
| `frontend/src/features/inventory/ProductDetailPage.jsx` | Page fiche produit complète avec KPIs, timeline, EOQ |
| `frontend/src/features/inventory/PurchaseOrderModal.jsx` | Modal génération bon de commande pré-rempli |
| `frontend/src/features/inventory/index.js` | Exports du module inventory |

---

### SCÉNARIO 3: Anomalie Prix → Investigation → Action

```
┌─────────────────────────────────────────────────────────────────────────┐
│          FLUX: Détection Anomalie → Analyse → Action Corrective          │
└─────────────────────────────────────────────────────────────────────────┘

   1. Détection Anomalie                   2. Alerte Intelligence
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  Core:              │                 │  /intelligence/     │
   │  anomaly_detection  │ ───────────────►│  anomalies          │
   │                     │                 │                     │
   │  "Huile d'olive     │                 │  Anomalie #456      │
   │   +35% vs moyenne"  │                 │  Sévérité: HAUTE    │
   │                     │                 │  Impact: 450€/mois  │
   └─────────────────────┘                 └──────────┬──────────┘
                                                      │
                                                      ▼
   3. Investigation                        4. Action Corrective
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  Contexte:          │                 │  Options:           │
   │  - Historique prix  │                 │  □ Changer fournis. │
   │  - Comparatif       │ ───────────────►│  □ Négocier prix    │
   │    fournisseurs     │                 │  □ Produit subst.   │
   │  - Impact marge     │                 │  □ Ignorer (motif)  │
   │                     │                 │                     │
   │  [Voir détail]      │                 │  [Appliquer]        │
   └─────────────────────┘                 └─────────────────────┘
```

#### Fonctionnalités Existantes

| Fonctionnalité | Fichier | État |
|----------------|---------|------|
| Détection anomalies | `core/finance/anomaly_detection.py` | Implémenté |
| Types anomalies | 12 types (AMOUNT_OUTLIER, DUPLICATE, PRICE_SPIKE, etc.) | Implémenté |
| API anomalies | `backend/api/anomaly_detection.py` | Implémenté |
| Page anomalies IA | `frontend/src/features/intelligence/AnomaliesPage.jsx` | Implémenté |
| Page anomalies finance | `frontend/src/features/finance/FinanceAnomaliesPage.jsx` | Implémenté |
| Table anomalies | `frontend/src/features/finance/components/RecoAnomaliesTable.jsx` | Implémenté |
| Intelligence summary | `backend/api/cockpit.py:_get_intelligence_summary()` | Implémenté |
| Historique prix | `frontend/src/features/prices/PricesPage.jsx` | Implémenté |
| Hook prix | `frontend/src/hooks/usePriceHistory.js` | Implémenté |
| Comparatif fournisseurs | `frontend/src/features/restaurant/RestaurantPriceHistoryComparisonPage.jsx` | Implémenté |
| Scoring fournisseurs | `frontend/src/features/intelligence/SupplierScoringOverviewPage.jsx` | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité | Statut |
|----------------|-------------|----------|--------|
| ~~Drawer détail anomalie~~ | ~~Panel contextuel avec historique et comparatif~~ | ~~Haute~~ | **FAIT** |
| ~~Actions correctives inline~~ | ~~Boutons MAJ prix, négocier, ignorer~~ | ~~Haute~~ | **FAIT** |
| Calcul impact marge | Afficher économie potentielle | Moyenne | En attente |
| Feedback Rules Engine | Bouton "Catégorie correcte?" avec apprentissage | Moyenne | En attente |
| Export anomalies PDF | Rapport anomalies pour négociation | Basse | En attente |

#### Nouveaux Fichiers Créés (S3)

| Fichier | Description |
|---------|-------------|
| `frontend/src/features/intelligence/components/AnomalyDetailDrawer.jsx` | Drawer slide-in avec 3 onglets: Détails, Contexte, Actions |
| `frontend/src/features/intelligence/components/AnomalyActionsInline.jsx` | Actions correctives inline avec feedback thumbs up/down |

---

### SCÉNARIO 4: Rapprochement Bancaire Assisté

```
┌─────────────────────────────────────────────────────────────────────────┐
│          FLUX: Transactions → Rapprochement Auto → Validation            │
└─────────────────────────────────────────────────────────────────────────┘

   1. Liste Transactions                   2. Suggestions ML
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  /finance/          │                 │  /finance/          │
   │  transactions       │ ───────────────►│  reconciliation     │
   │                     │                 │                     │
   │  Vue "non           │                 │  Suggestions        │
   │  rapprochées"       │                 │  affichées en ligne │
   │  + badge ML         │                 │                     │
   └─────────────────────┘                 └──────────┬──────────┘
                                                      │
                                                      ▼
   3. Validation Bulk                      4. Feedback Loop
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  Actions:           │                 │  Rules Engine:      │
   │  ☑ Valider          │ ───────────────►│  learn_from_        │
   │  ☑ Ignorer (motif)  │                 │  feedback           │
   │                     │                 │                     │
   │  [Appliquer bulk]   │                 │  → Amélioration     │
   │                     │                 │    suggestions      │
   └─────────────────────┘                 └─────────────────────┘
```

#### Fonctionnalités Existantes

| Fonctionnalité | Fichier | État |
|----------------|---------|------|
| Rapprochement engine | `core/finance/bank_reconciliation.py` | Implémenté |
| Types matching | EXACT, FUZZY_AMOUNT, MULTI_LINE, ALIAS, PATTERN, LEARNED | Implémenté |
| API rapprochement | `backend/api/bank_reconciliation.py` | Implémenté |
| Page rapprochement | `frontend/src/features/finance/BankReconciliationPage.jsx` | Implémenté |
| Page transactions | `frontend/src/features/finance/FinanceTransactionsPage.jsx` | Implémenté |
| Filtres transactions | `frontend/src/features/finance/components/TransactionFilters.jsx` | Implémenté |
| Service transactions | `backend/services/finance/transactions.py` | Implémenté |
| Service reconciliation | `backend/services/finance/reconciliation.py` | Implémenté |
| Rules Engine | `core/finance/rules_engine.py` | Implémenté |
| Catégorisation inline | `frontend/src/features/finance/components/CategoryInlineEdit.jsx` | Implémenté |
| Modal bulk catégorisation | `frontend/src/features/finance/components/BulkCategorizeModal.jsx` | Implémenté |
| Hook finance | `frontend/src/hooks/useFinance.js` | Implémenté |
| Hook catégories | `frontend/src/hooks/useFinanceCategories.js` | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité | Statut |
|----------------|-------------|----------|--------|
| ~~Split view transaction/facture~~ | ~~Panneau contextuel détail match~~ | ~~Haute~~ | **FAIT** |
| Confirmation feedback inline | Prompt "Match correct? Oui/Non" | Moyenne | En attente |
| Indicateurs progression | Taux rapprochement temps réel | Moyenne | En attente |
| Undo rapprochement | Annuler un match validé | Basse | En attente |
| Export rapprochement Excel | Export pour comptable | Basse | En attente |

#### Nouveaux Fichiers Créés (S4)

| Fichier | Description |
|---------|-------------|
| `frontend/src/features/finance/components/ReconciliationSplitView.jsx` | Vue 3 colonnes: Transactions | Preview Match | Factures |

---

### SCÉNARIO 5: Prévisions → Approvisionnement → Cash-Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│          FLUX: Prévisions Ventes → Besoin Stock → Impact Trésorerie      │
└─────────────────────────────────────────────────────────────────────────┘

   1. Cockpit Alerte                       2. Forecast Stock
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  Carte alerte:      │                 │  /intelligence/     │
   │  "Ruptures prévues  │ ───────────────►│  forecast?type=     │
   │   + cash tendu"     │                 │  stock              │
   │                     │                 │                     │
   │  CTA: Voir          │                 │  - Horizon 30j      │
   │  prévisions         │                 │  - Prédictions      │
   └─────────────────────┘                 └──────────┬──────────┘
                                                      │
                                                      ▼
   3. Recommandations EOQ                  4. Simulation Cash
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  /inventory-        │                 │  /intelligence/     │
   │  intelligence/      │ ───────────────►│  forecast?type=     │
   │  reorder            │                 │  cashflow           │
   │                     │                 │                     │
   │  - Quantité EOQ     │                 │  - Projection solde │
   │  - Fournisseur      │                 │  - Alertes négatif  │
   │  - "Créer commande" │                 │  - Options étalement│
   └─────────────────────┘                 └─────────────────────┘
```

#### Fonctionnalités Existantes

| Fonctionnalité | Fichier | État |
|----------------|---------|------|
| Forecasting engine | `core/finance/forecasting.py` | Implémenté |
| Types prévisions | SALES, STOCK, CASHFLOW, PRICE, DEMAND | Implémenté |
| Méthodes ML | Moving Average, Exponential Smoothing, Holt-Winters, Linear Regression | Implémenté |
| API forecasting | `backend/api/forecasting.py` | Implémenté |
| Page prévisions | `frontend/src/features/intelligence/ForecastPage.jsx` | Implémenté |
| Page forecasting | `frontend/src/features/intelligence/ForecastingPage.jsx` | Implémenté |
| Prévisions restaurant | `frontend/src/features/restaurant/ForecastsPage.jsx` | Implémenté |
| Inventory intelligence | `core/finance/inventory_intelligence.py` | Implémenté |
| Page stock intelligent | `frontend/src/features/intelligence/InventoryIntelligencePage.jsx` | Implémenté |
| Treasury summary | `backend/api/cockpit.py:_get_treasury_summary()` | Implémenté |
| Page trésorerie | `frontend/src/features/finance/FinanceOverview.jsx` | Implémenté |
| Portefeuille | `frontend/src/features/portfolio/PortfolioPage.jsx` | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| Graphe prévisions interactif | Recharts avec zoom, tooltip détaillé | Haute |
| Intervalle confiance visuel | Bande grisée autour prévision | Moyenne |
| Simulation "what-if" | Slider pour ajuster paramètres | Moyenne |
| Alerte cash négatif | Notification si projection < 0 | Moyenne |
| Export prévisions CSV | Pour analyse externe | Basse |

---

### SCÉNARIO 6: Restaurant - Food Cost Analysis

```
┌─────────────────────────────────────────────────────────────────────────┐
│          FLUX: Plat → Coût Matières → Optimisation Marge                 │
└─────────────────────────────────────────────────────────────────────────┘

   1. Catalogue Plats                      2. Fiche Technique
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  /restaurant/plats  │                 │  Modal détail plat  │
   │                     │ ───────────────►│                     │
   │  - Liste plats      │                 │  - Ingrédients      │
   │  - Marge calculée   │                 │  - Quantités        │
   │  - Food cost %      │                 │  - Coût unitaire    │
   └─────────────────────┘                 └──────────┬──────────┘
                                                      │
                                                      ▼
   3. Analyse Food Cost                    4. Optimisation
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  /restaurant/       │                 │  Simulateur prix:   │
   │  food-cost          │ ───────────────►│                     │
   │                     │                 │  - Ajuster prix     │
   │  - Répartition      │                 │    vente            │
   │  - Comparatif       │                 │  - Substituer       │
   │  - Tendances        │                 │    ingrédient       │
   └─────────────────────┘                 └─────────────────────┘
```

#### Fonctionnalités Existantes

| Fonctionnalité | Fichier | État |
|----------------|---------|------|
| Page overview restaurant | `frontend/src/features/restaurant/RestaurantOverviewPage.jsx` | Implémenté |
| Page Food Cost | `frontend/src/features/restaurant/FoodCostAnalysisPage.jsx` | Implémenté |
| Catalogue plats | `frontend/src/features/restaurant/PlatsCatalogPage.jsx` | Implémenté |
| Page ingrédients | `frontend/src/features/restaurant/IngredientsPage.jsx` | Implémenté |
| Menus et coûts | `frontend/src/features/restaurant/RestaurantMenusCostsPage.jsx` | Implémenté |
| Dashboard restaurant | `frontend/src/features/restaurant/RestaurantDashboard.jsx` | Implémenté |
| Charges restaurant | `frontend/src/features/restaurant/RestaurantChargesPage.jsx` | Implémenté |
| Consommations | `frontend/src/features/restaurant/RestaurantConsumptionPage.jsx` | Implémenté |
| Modal détail plat | `frontend/src/features/restaurant/components/PlatDetailModal.jsx` | Implémenté |
| KPI Cards restaurant | `frontend/src/features/restaurant/components/RestaurantKPICards.jsx` | Implémenté |
| Panel Food Cost | `frontend/src/features/restaurant/components/FoodCostAnalysisPanel.jsx` | Implémenté |
| Alertes restaurant | `frontend/src/features/restaurant/components/RestaurantAlertsWidget.jsx` | Implémenté |
| Chart répartition coûts | `frontend/src/features/restaurant/components/CostBreakdownChart.jsx` | Implémenté |
| Simulateur prix | `frontend/src/features/restaurant/components/PriceSimulatorPanel.jsx` | Implémenté |
| API restaurant | `backend/api/restaurant.py` | Implémenté |
| Service restaurant | `backend/services/restaurant/` | Implémenté |
| Liens épicerie | `frontend/src/features/restaurant/RestaurantEpicerieLinkPage.jsx` | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| Recalcul automatique prix | MAJ coût si prix ingrédient change | Haute |
| Alerte marge < seuil | Notification si food cost > 35% | Moyenne |
| Historique food cost | Graphe évolution par plat | Moyenne |
| Comparatif période | Comparer food cost N vs N-1 | Basse |
| Export fiches techniques PDF | Pour cuisine | Basse |

---

### SCÉNARIO 7: Scoring Fournisseurs → Négociation

```
┌─────────────────────────────────────────────────────────────────────────┐
│          FLUX: Analyse Fournisseur → Score → Décision Achat              │
└─────────────────────────────────────────────────────────────────────────┘

   1. Dashboard Scoring                    2. Détail Fournisseur
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  /intelligence/     │                 │  /intelligence/     │
   │  scoring            │ ───────────────►│  scoring/suppliers/ │
   │                     │                 │  :id                │
   │  - Top fournisseurs │                 │                     │
   │  - Score global     │                 │  - 7 dimensions     │
   │  - Alertes          │                 │  - Historique       │
   └─────────────────────┘                 └──────────┬──────────┘
                                                      │
                                                      ▼
   3. Analyse Critères                     4. Action Décision
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  /intelligence/     │                 │  Options:           │
   │  scoring/criteria   │ ───────────────►│                     │
   │                     │                 │  - Renégocier       │
   │  - Pondération      │                 │  - Changer fournis. │
   │  - Ajustements      │                 │  - Alerter achat    │
   └─────────────────────┘                 └─────────────────────┘
```

#### Fonctionnalités Existantes

| Fonctionnalité | Fichier | État |
|----------------|---------|------|
| Scoring engine | `core/finance/supplier_scoring.py` | Implémenté |
| 7 dimensions scoring | Price Stability, Delivery, Invoice Accuracy, Stock Accuracy, Payment Terms, Responsiveness, Quality | Implémenté |
| API scoring | `backend/api/supplier_scoring.py` | Implémenté |
| Page overview scoring | `frontend/src/features/intelligence/SupplierScoringOverviewPage.jsx` | Implémenté |
| Liste fournisseurs | `frontend/src/features/intelligence/SuppliersListPage.jsx` | Implémenté |
| Détails fournisseur | `frontend/src/features/intelligence/SupplierDetailsPage.jsx` | Implémenté |
| Critères scoring | `frontend/src/features/intelligence/ScoringCriteriaPage.jsx` | Implémenté |
| Alertes fournisseurs | `frontend/src/features/intelligence/SupplierAlertsPage.jsx` | Implémenté |
| Table scoring | `frontend/src/features/intelligence/components/SupplierScoringTable.jsx` | Implémenté |
| Modal détail | `frontend/src/features/intelligence/components/SupplierDetailModal.jsx` | Implémenté |
| Graphe historique | `frontend/src/features/intelligence/components/ScoreHistoryChart.jsx` | Implémenté |
| Panel critères | `frontend/src/features/intelligence/components/ScoringCriteriaPanel.jsx` | Implémenté |
| Widget alertes | `frontend/src/features/intelligence/components/SupplierAlertsWidget.jsx` | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| Comparateur fournisseurs | Side-by-side 2-3 fournisseurs | Haute |
| Génération rapport PDF | Fiche fournisseur pour négociation | Moyenne |
| Alerte dégradation score | Notification si score baisse > 10% | Moyenne |
| Objectifs négociation | Suggestions basées sur écarts | Basse |
| Intégration email | Envoyer rapport directement | Basse |

---

## 3. Composants UX Transversaux

### 3.1 Command Bar

#### Fonctionnalités Existantes

| Fonctionnalité | Fichier | État |
|----------------|---------|------|
| Composant CommandBar | `frontend/src/components/layout/CommandBar.jsx` | Implémenté |
| Context CommandBar | `frontend/src/contexts/CommandBarContext.jsx` | Implémenté |
| Hook suggestions live | `frontend/src/hooks/useCommandBarLiveSuggestions.js` | Implémenté |
| Raccourci Ctrl+K | Activation clavier | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| Actions contextuelles | Suggestions basées sur page active | Haute |
| Historique recherches | Dernières recherches utilisateur | Moyenne |
| Commandes rapides | "/import", "/scan", "/rapport" | Moyenne |

### 3.2 Système de Feedback

#### Fonctionnalités Existantes

| Fonctionnalité | Fichier | État |
|----------------|---------|------|
| Context Feedback | `frontend/src/contexts/FeedbackContext.jsx` | Implémenté |
| Loading Overlay | `frontend/src/components/feedback/LoadingOverlay.jsx` | Implémenté |
| Notification Center | `frontend/src/components/feedback/NotificationCenter.jsx` | Implémenté |
| Confirm Dialog | `frontend/src/components/feedback/ConfirmDialog.jsx` | Implémenté |
| Empty State | `frontend/src/components/feedback/EmptyState.jsx` | Implémenté |
| Error Boundary | `frontend/src/components/feedback/ErrorBoundary.jsx` | Implémenté |
| Retryable Error | `frontend/src/components/feedback/RetryableError.jsx` | Implémenté |
| Toast | `frontend/src/components/ui/Toast.jsx` | Implémenté |
| Skeleton | `frontend/src/components/ui/Skeleton.jsx` | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| Toast avec action Undo | Annuler action depuis toast | Moyenne |
| Progress bar opérations longues | Import avec % progression | Moyenne |
| Notifications push browser | Pour alertes critiques | Basse |

### 3.3 Accessibilité

#### Fonctionnalités Existantes

| Fonctionnalité | Fichier | État |
|----------------|---------|------|
| Skip Links | `frontend/src/components/accessibility/SkipLinks.jsx` | Implémenté |
| Accessible Modal | `frontend/src/components/accessibility/AccessibleModal.jsx` | Implémenté |
| Hook accessibilité | `frontend/src/hooks/useAccessibility.js` | Implémenté |
| Hook hotkeys | `frontend/src/hooks/useHotkeys.jsx` | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| Focus trap modals | Focus piégé dans modales | Haute |
| ARIA live regions | Annonces lecteur écran | Moyenne |
| Mode haut contraste | Option accessibilité | Basse |
| Navigation 100% clavier | Tous éléments accessibles | Moyenne |

### 3.4 Performance

#### Fonctionnalités Existantes

| Fonctionnalité | Fichier | État |
|----------------|---------|------|
| Hook optimistic | `frontend/src/hooks/useOptimistic.js` | Implémenté |
| Hook virtualization | `frontend/src/hooks/useVirtualization.jsx` | Implémenté |
| Hook prefetch | `frontend/src/hooks/usePrefetch.jsx` | Implémenté |
| Lazy loading routes | `frontend/src/app/routes.jsx` | Implémenté |
| Middleware performance | `backend/middleware/performance.py` | Implémenté |
| Rate limiter | `backend/middleware/rate_limiter.py` | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| Service Worker cache | Cache offline assets | Moyenne |
| Prefetch hover links | Précharger au survol | Basse |
| Bundle splitting avancé | Chunks par route | Basse |

### 3.5 Mobile

#### Fonctionnalités Existantes

| Fonctionnalité | Fichier | État |
|----------------|---------|------|
| Camera Scanner | `frontend/src/components/ui/MobileCameraScanner.jsx` | Implémenté |
| Mobile DataTable | `frontend/src/components/ui/MobileDataTable.jsx` | Implémenté |
| Swipeable Row | `frontend/src/components/ui/SwipeableRow.jsx` | Implémenté |
| Hook gestes | `frontend/src/hooks/useGestures.js` | Implémenté |
| Hook media query | `frontend/src/hooks/useMediaQuery.js` | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité | Statut |
|----------------|-------------|----------|--------|
| ~~PWA manifest~~ | ~~Installation mobile~~ | ~~Haute~~ | **FAIT** |
| ~~Mode offline~~ | ~~Fonctionnement déconnecté~~ | ~~Moyenne~~ | **FAIT** |
| ~~Scan code-barres~~ | ~~Scanner via caméra~~ | ~~Haute~~ | **FAIT** |
| ~~Navigation bottom bar~~ | ~~Menu mobile~~ | ~~Moyenne~~ | **FAIT** |

#### Nouveaux Fichiers Créés (Mobile)

| Fichier | Description |
|---------|-------------|
| `frontend/public/manifest.json` | Configuration PWA complète |
| `frontend/public/sw.js` | Service Worker avec cache offline |
| `frontend/src/hooks/usePWA.js` | Hook gestion PWA et installation |
| `frontend/src/components/pwa/InstallPWAButton.jsx` | Boutons d'installation PWA |
| `frontend/src/hooks/useOffline.js` | Détection statut online/offline |
| `frontend/src/contexts/OfflineContext.jsx` | Provider offline avec queue mutations |
| `frontend/src/services/offlineStorage.js` | Stockage IndexedDB pour cache offline |
| `frontend/src/components/feedback/OfflineBanner.jsx` | Bannière statut offline animée |
| `frontend/src/components/ui/BarcodeScanner.jsx` | Scanner code-barres avec caméra |
| `frontend/src/hooks/useBarcodeScanner.js` | Hook gestion scanner |
| `frontend/src/components/ui/BarcodeScannerModal.jsx` | Modal fullscreen scanner |
| `frontend/src/components/layout/MobileBottomNav.jsx` | Navigation bottom bar mobile |
| `frontend/src/components/layout/MobileMoreMenu.jsx` | Menu "Plus" slide-up |
| `frontend/src/hooks/useMobileNav.js` | Hook navigation mobile |

---

## 4. APIs Intelligence (Core)

### 4.1 Anomaly Detection

#### Fonctionnalités Existantes

| Type Anomalie | Description | Fichier |
|---------------|-------------|---------|
| AMOUNT_OUTLIER | Montant anormal (Z-score, IQR) | `core/finance/anomaly_detection.py` |
| DUPLICATE_TRANSACTION | Transaction en double | Implémenté |
| DUPLICATE_INVOICE | Facture en double | Implémenté |
| DEBIT_CREDIT_MISMATCH | Incohérence débit/crédit | Implémenté |
| UNUSUAL_FREQUENCY | Fréquence inhabituelle | Implémenté |
| UNUSUAL_TIME | Horaire suspect | Implémenté |
| MISSING_INVOICE | Facture manquante | Implémenté |
| PRICE_DISCREPANCY | Écart prix | Implémenté |
| ROUND_AMOUNT | Montant rond suspect | Implémenté |
| SEQUENCE_GAP | Numéro facture manquant | Implémenté |
| CATEGORY_MISMATCH | Catégorie incohérente | Implémenté |
| VELOCITY_SPIKE | Pic soudain transactions | Implémenté |

### 4.2 Forecasting

#### Fonctionnalités Existantes

| Méthode | Description | Fichier |
|---------|-------------|---------|
| MOVING_AVERAGE | Moyenne mobile | `core/finance/forecasting.py` |
| EXPONENTIAL_SMOOTHING | Lissage exponentiel | Implémenté |
| HOLT_WINTERS | Holt-Winters saisonnier | Implémenté |
| LINEAR_REGRESSION | Régression linéaire | Implémenté |
| SEASONAL_NAIVE | Naïf saisonnier | Implémenté |

#### Fonctionnalités Manquantes

| Fonctionnalité | Description | Priorité |
|----------------|-------------|----------|
| ARIMA | Modèle ARIMA complet | Moyenne |
| Prophet | Facebook Prophet | Basse |
| Ensemble methods | Combinaison de modèles | Basse |

### 4.3 Supplier Scoring

#### Fonctionnalités Existantes

| Dimension | Poids | Description |
|-----------|-------|-------------|
| PRICE_STABILITY | 25% | Volatilité des prix |
| DELIVERY_RELIABILITY | 20% | Ponctualité livraisons |
| INVOICE_ACCURACY | 15% | Taux erreurs factures |
| STOCK_ACCURACY | 15% | Écarts stock |
| PAYMENT_TERMS | 10% | Conditions paiement |
| RESPONSIVENESS | 10% | Réactivité |
| PRODUCT_QUALITY | 5% | Qualité produits |

---

## 5. Récapitulatif Priorisation

### 5.1 Priorité Haute (Sprint 1-2)

| Fonctionnalité | Scénario | Impact | Statut |
|----------------|----------|--------|--------|
| Extraction IA Ollama | S1 - Import Facture | Automatisation | En attente |
| ~~Fiche produit détaillée~~ | ~~S2 - Alerte Stock~~ | ~~Navigation~~ | **FAIT** |
| ~~Génération bon commande~~ | ~~S2 - Alerte Stock~~ | ~~Productivité~~ | **FAIT** |
| ~~Drawer détail anomalie~~ | ~~S3 - Anomalie Prix~~ | ~~UX~~ | **FAIT** |
| ~~Actions correctives inline~~ | ~~S3 - Anomalie Prix~~ | ~~Productivité~~ | **FAIT** |
| ~~Split view rapprochement~~ | ~~S4 - Rapprochement~~ | ~~UX~~ | **FAIT** |
| Graphe prévisions interactif | S5 - Prévisions | Visualisation | En attente |
| Recalcul auto prix plats | S6 - Food Cost | Automatisation | En attente |
| Comparateur fournisseurs | S7 - Scoring | Décision | En attente |
| ~~PWA manifest + scan mobile~~ | ~~Transversal~~ | ~~Mobile~~ | **FAIT** |

### 5.2 Priorité Moyenne (Sprint 3-4)

| Fonctionnalité | Scénario | Impact |
|----------------|----------|--------|
| Preview PDF inline | S1 - Import | UX |
| Matching produits amélioré | S1 - Import | Qualité |
| CTA Commander depuis alerte | S2 - Stock | Productivité |
| Feedback Rules Engine | S4 - Rapprochement | ML |
| Indicateurs progression | S4 - Rapprochement | Feedback |
| Simulation "what-if" | S5 - Prévisions | Analyse |
| Alerte marge < seuil | S6 - Food Cost | Alertes |
| Rapport PDF fournisseur | S7 - Scoring | Export |
| Focus trap modals | Accessibilité | A11y |
| Navigation 100% clavier | Accessibilité | A11y |

### 5.3 Priorité Basse (Backlog)

| Fonctionnalité | Scénario | Impact |
|----------------|----------|--------|
| Notification temps réel import | S1 - Import | Feedback |
| Simulation impact cash-flow | S2 - Stock | Analyse |
| Export anomalies PDF | S3 - Anomalie | Export |
| Undo rapprochement | S4 - Rapprochement | UX |
| Export prévisions CSV | S5 - Prévisions | Export |
| Export fiches techniques | S6 - Food Cost | Export |
| Intégration email | S7 - Scoring | Communication |
| ARIMA / Prophet | Forecasting | ML avancé |
| Service Worker cache | Performance | Offline |

---

## 6. Métriques de Succès

### 6.1 Quantitatifs

| Métrique | Actuel | Cible |
|----------|--------|-------|
| Lighthouse Performance | ~70 | > 90 |
| Lighthouse Accessibility | ~60 | > 95 |
| First Contentful Paint | ~2s | < 1s |
| Time to Interactive | ~3s | < 2s |
| Taux rapprochement auto | ~60% | > 85% |
| Confiance catégorisation | ~70% | > 90% |
| Temps import facture | ~30s | < 10s |

### 6.2 Qualitatifs

- Navigation 100% clavier possible
- Lecteur d'écran utilisable
- Aucun état "impasse" (toujours une action possible)
- Feedback en < 100ms pour chaque action
- Messages d'erreur toujours actionnables

---

**Document généré automatiquement - Décembre 2025**
