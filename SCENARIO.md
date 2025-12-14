### Scénarios Utilisateur

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SCÉNARIO 1: Import Facture → Stock → Finance             │
└─────────────────────────────────────────────────────────────────────────────┘

   1. Import Facture PDF                    2. Extraction automatique
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  /operations/       │                 │  Core: invoice_     │
   │  factures/import    │ ───────────────▶│  extractor.py       │
   │                     │                 │                     │
   │  [Drop PDF]         │                 │  → Lignes extraites │
   │                     │                 │  → Produits matchés │
   └─────────────────────┘                 └──────────┬──────────┘
                                                      │
                                                      ▼
   3. Mise à jour Stock                    4. Catégorisation Finance
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  Event:             │                 │  Rules Engine:      │
   │  INVOICE_IMPORTED   │ ───────────────▶│  Catégorisation     │
   │                     │                 │  automatique        │
   │  → +Stock reçu      │                 │                     │
   │  → Prix MAJ         │                 │  → 94% confiance    │
   │  → Alerte si écart  │                 │  → Auto-validé      │
   └─────────────────────┘                 └──────────┬──────────┘
                                                      │
                                                      ▼
   5. Notification Cockpit                 6. Récapitulatif
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  AlertsPanel:       │                 │  Toast:             │
   │  "Facture METRO     │                 │  "✓ Facture METRO   │
   │   importée"         │                 │   traitée           │
   │                     │                 │   - 12 produits     │
   │  → Voir détail      │                 │   - Stock MAJ       │
   │  → Corriger         │                 │   - Catégorisé"     │
   └─────────────────────┘                 └─────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│               SCÉNARIO 2: Alerte Stock → Commande → Prévision               │
└─────────────────────────────────────────────────────────────────────────────┘

   1. Alerte Cockpit                       2. Détail Produit
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  AlertsPanel:       │                 │  /operations/       │
   │  "⚠️ Stock critique │ ───────────────▶│  inventaire/        │
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
   │  "Commander 50kg    │ ───────────────▶│  Créer bon de       │
   │   chez METRO        │                 │  commande           │
   │   (EOQ optimal)"    │                 │                     │
   │                     │                 │  → Pré-rempli       │
   │  Score METRO: 8.5   │                 │  → Fournisseur      │
   │  Score SYSCO: 7.2   │                 │  → Quantité EOQ     │
   └─────────────────────┘                 └─────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│            SCÉNARIO 3: Anomalie Prix → Investigation → Action               │
└─────────────────────────────────────────────────────────────────────────────┘

   1. Détection Anomalie                   2. Alerte Intelligence
   ┌─────────────────────┐                 ┌─────────────────────┐
   │  Core:              │                 │  /intelligence/     │
   │  anomaly_detection  │ ───────────────▶│  anomalies          │
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
   │  - Comparatif       │ ───────────────▶│  □ Négocier prix    │
   │    fournisseurs     │                 │  □ Produit subst.   │
   │  - Impact marge     │                 │  □ Ignorer (motif)  │
   │                     │                 │                     │
   │  [Voir détail]      │                 │  [Appliquer]        │
   └─────────────────────┘                 └─────────────────────┘
```

---

## 6. Phase 4 - Refonte UX/Navigation

### 6.1 Nouvelle Structure de Navigation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NOUVELLE NAVIGATION                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  HEADER                                                                      │
│  [Logo] [Tenant Selector] ──────────────────── [Alerts] [User] [Settings]   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┬──────────────────────────────────────────────────────────┐
│                  │                                                          │
│  SIDEBAR         │  MAIN CONTENT                                            │
│                  │                                                          │
│  ┌────────────┐  │  ┌──────────────────────────────────────────────────┐   │
│  │ COCKPIT    │  │  │                                                   │   │
│  │ Vue 360°   │◀─┼──│  Dashboard/Page active                            │   │
│  └────────────┘  │  │                                                   │   │
│                  │  │                                                   │   │
│  ┌────────────┐  │  │                                                   │   │
│  │ OPÉRATIONS │  │  │                                                   │   │
│  │ ▼          │  │  └──────────────────────────────────────────────────┘   │
│  │  Épicerie  │  │                                                          │
│  │  Restaurant│  │  ┌──────────────────────────────────────────────────┐   │
│  │  Inventaire│  │  │  CONTEXTUAL PANEL (optionnel)                    │   │
│  │  Factures  │  │  │  - Détails item sélectionné                      │   │
│  └────────────┘  │  │  - Actions rapides                               │   │
│                  │  │  - Historique                                     │   │
│  ┌────────────┐  │  └──────────────────────────────────────────────────┘   │
│  │ FINANCES   │  │                                                          │
│  │ ▼          │  │                                                          │
│  │  Trésorerie│  │                                                          │
│  │  Marges    │  │                                                          │
│  │  Rapproch. │  │                                                          │
│  │  Analytique│  │                                                          │
│  └────────────┘  │                                                          │
│                  │                                                          │
│  ┌────────────┐  │                                                          │
│  │ INTELLIGENCE│ │                                                          │
│  │ ▼          │  │                                                          │
│  │  Prévisions│  │                                                          │
│  │  Anomalies │  │                                                          │
│  │  Scoring   │  │                                                          │
│  │  Insights  │  │                                                          │
│  └────────────┘  │                                                          │
│                  │                                                          │
│  ┌────────────┐  │                                                          │
│  │ PARAMÈTRES │  │                                                          │
│  └────────────┘  │                                                          │
│                  │                                                          │
└──────────────────┴──────────────────────────────────────────────────────────┘

---

## 7. Scénarios "New Generation" (cross-modules)

### NG-1 : Prévisions → Appro → Cash (boucle fermée)

```
1) Prévision ventes (Intelligence)
   - Page: /intelligence/forecast
   - Appel: POST /forecasting/sales (horizon 30j)
   - Résultat: courbe + tendance + intervalle confiance

2) Besoin stock (Operations + Inventory Intelligence)
   - Calcul: /inventory-intelligence/reorder-suggestions
   - Entrées: prévisions + stock actuel + lead time
   - Sortie: quantité recommandée + date commande

3) Impact trésorerie (Finance)
   - Appel: GET /forecasting/cash-flow?horizon_days=30
   - Projection solde après commandes recommandées
   - Alertes: solde négatif, marge compressée

4) Action unifiée (Cockpit)
   - Carte cockpit: "Commander avant rupture" + CTA
   - Actions rapides: créer bon de commande, ajuster budget
```

### NG-2 : Anomalie prix → Négociation → Suivi marge

```
1) Détection (Intelligence)
   - Core: anomaly_detection.py -> type ROUND_AMOUNT ou PRICE_SPIKE
   - UI: /intelligence/anomalies (sévérité, impact €/mois)

2) Analyse (Finance + Supplier Scoring)
   - Context: historique prix, PAMP, scoring fournisseurs
   - Reco: "Négocier avec METRO (score 8.5) ou basculer SYSCO"

3) Action (Operations)
   - CTA: mettre à jour prix d'achat + notifier catalogue
   - Event: PRICE_UPDATED -> recalcul marges

4) Suivi (Finance)
   - Dashboard marges: variation avant/après
   - Audit trail: log décision + motif
```

### NG-3 : Anomalie transaction → Rapprochement assisté

```
1) Détection (Rules Engine + Anomaly)
   - /finance/transactions flag "SEQUENCE_GAP" ou "DUPLICATE"
   - Suggestion catégorie via ML + règles

2) Rapprochement (Bank Reconciliation)
   - Appel: POST /bank-reconciliation/run
   - UI: /finance/reconciliation avec suggestions préremplies

3) Validation (User + Audit)
   - Utilisateur choisit match ou ignore (motif)
   - Audit: EVENT bank_transaction.categorized + feedback

4) Feedback loop
   - Rules Engine learn_from_feedback
   - Diminution anomalies similaires (tracking cockpit)
```

### NG-4 : Résilience multi-tenant (Restaurant ↔ Intelligence)

```
1) Tenant routing
   - intelligence (4) ↔ restaurant (2) pour ventes
   - Mapping entity_id pour finance: restaurant=2, trésorerie=3

2) Tableau de bord unifié
   - /cockpit combine ventes (restaurant_sales) + cash-flow
   - Filtres par tenant, consolidation multi-tenant

3) Alertes contextualisées
   - Alerte stock (tenant épicerie) + prévision ventes (tenant resto)
   - CTA unique: ouvrir Forecast + créer commande fournisseur
```

---

## 8. Modélisation précise des pages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           /cockpit — Vue 360°                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────┬─────────────────────────────────────────────────────────────┐
│ HEADER        │  KPI Cards (CA 7/30j | Cash dispo | Ruptures | Alertes)     │
│ Alerts/User   └─────────────────────────────────────────────────────────────┘
│ Tenant switch │
├───────────────┴─────────────────────────────────────────────────────────────┐
│ SIDEBAR (nav) │  DASHBOARD                                                   │
│ Cockpit/ops…  │  - Graph cash in/out jour                                   │
│               │  - Tuiles alertes critiques                                 │
├───────────────┬─────────────────────────────────────────────────────────────┤
│ CONTEXT PANEL │  MAIN PANEL                                                 │
│ (détail item) │  - AlertsPanel temps réel                                   │
│ - historique  │  - Quick actions: commander, importer facture, rapprocher   │
│ - CTA ouvrir  │  - Liste cards anomalies/ruptures                           │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     /operations/factures/import                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────┬─────────────────────────────────────────────────────────────┐
│ SIDEBAR       │  DROPZONE + STATUS                                          │
│ Prévisual PDF │  - Drag & drop PDF/CSV                                      │
│ Erreurs lignes│  - Barre de progression parsing                             │
├───────────────┼─────────────────────────────────────────────────────────────┤
│ MAPPING       │  RÉSUMÉ LIGNES EXTRACTÉES                                   │
│ Produit/TVA   │  - Table: produit détecté, quantité, prix, TVA              │
│ Override manu │  - Actions: forcer produit, éditer TVA, supprimer ligne     │
├───────────────┴─────────────────────────────────────────────────────────────┤
│ FOOTER CTA    │  [Valider & mettre à jour stock]  [Annuler]                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                /operations/inventaire/produit/:id                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────┬─────────────────────────────────────────────────────────────┐
│ HEADER        │  FICHE PRODUIT                                              │
│ Nom / SKU     │  - Stock actuel, prix achat/vente, ventes 30j               │
│ Badges actif  │  - Graph mouvements récents                                 │
├───────────────┼─────────────────────────────────────────────────────────────┤
│ PREDICTION    │  ACTIONS RAPIDES                                            │
│ - Rupture ETA │  - Créer commande (EOQ préremplie)                          │
│ - EOQ qty     │  - Ajuster stock                                            │
│ - Fournisseur │  - Historique prix                                          │
├───────────────┼─────────────────────────────────────────────────────────────┤
│ TIMELINE      │  - Events: imports facture, corrections, alertes            │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      /intelligence/forecast                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Controls: [Ventes | Trésorerie | Stock]  [Horizon 7/30/90j]  [Actualiser]   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Graph prévisions (aire + intervalle confiance)                              │
│ - Tooltip date / valeur / bornes                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ Résumé : Total prévu | Confiance | Tendance | Points de données             │
├─────────────────────────────────────────────────────────────────────────────┤
│ État erreur si données insuffisantes (<7j)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     /intelligence/anomalies                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────┬─────────────────────────────────────────────────────────────┐
│ FILTRES       │  TABLEAU ANOMALIES                                          │
│ Sévérité/type │  - Colonnes: type, impact €/mois, fournisseur, statut        │
│ Période       │  - Badges sévérité                                          │
├───────────────┴─────────────────────────────────────────────────────────────┤
│ FICHE ANOMALIE (drawer/modal)                                               │
│ - Historique prix/transactions                                              │
│ - Comparatif fournisseurs, PAMP                                             │
│ - Actions: négocier, MAJ prix, ignorer (motif)                              │
│ - Audit trail + feedback Rules Engine                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    /finance/reconciliation                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Toolbar: filtres (date, compte, statut) | Actions bulk (rapprocher, ignorer)│
├─────────────────────────────────────────────────────────────────────────────┤
│ Tableau transactions non rapprochées                                        │
│ - Suggestion match (facture, relevé) affichée en ligne                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Panneau contexte (split)                                                    │
│ - Détail transaction + candidat facture                                     │
│ - Justification/notes + CTA valider                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ Indicateurs: taux rapprochement, séquence gaps, doublons                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     /finance/transactions                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Filtres (date, montant, catégorie, fournisseur) + CTA exporter/analyser     │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tableau transactions                                                        │
│ - Suggestion catégorie (Rules Engine) + bouton corriger/feedback            │
│ - Sélection multiple pour classifier/ignorer                                │
├─────────────────────────────────────────────────────────────────────────────┤
│ Graph cash-in/out jour + tendance trésorerie                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│          /inventory-intelligence/reorder-suggestions                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ Filtres: service level, lead time, budget plafond                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tableau recommandations                                                     │
│ - Produit, stock, conso/j, rupture ETA, fournisseur suggéré, quantité EOQ   │
│ - Badge risque (critical/high/low)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ CTA: [Créer commande] préremplie + simulation impact cash-flow              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Parcours Navigation "New Generation" (multi-pages)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ NG-NAV-1 : Cockpit → Forecast → Reorder → CashFlow                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 1. COCKPIT    │ Carte alerte: "Ruptures prévues + cash tendu"               │
│ (/cockpit)    │ CTA: "Voir prévisions"                                      │
└───────┬───────┴─────────────────────────────────────────────────────────────┘
        ▼
┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 2. FORECAST   │ /intelligence/forecast?type=stock                           │
│ (Stock)       │ - Horizon 30j, prédictions rupture                          │
│               │ - CTA: "Voir recommandations" (service_level=95%, LT=5)     │
└───────┬───────┴─────────────────────────────────────────────────────────────┘
        ▼
┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 3. REORDER    │ /inventory-intelligence/reorder-suggestions                 │
│ Suggestions   │ - Quantité EOQ, fournisseur suggéré                         │
│               │ - Sélection → "Créer commande"                              │
└───────┬───────┴─────────────────────────────────────────────────────────────┘
        ▼
┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 4. CASH FLOW  │ /intelligence/forecast?type=cashflow                        │
│ Simulation    │ - Projection solde incluant commandes                       │
│               │ - Alertes solde négatif / options d'étalement               │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ NG-NAV-2 : Anomalie Prix → Fiche Produit → Négociation → Marges              │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 1. ANOMALIES  │ /intelligence/anomalies                                     │
│               │ - Filtre PRICE_SPIKE, sévérité HAUTE                        │
│               │ - Sélection "Huile d'olive +35%"                            │
└───────┬───────┴─────────────────────────────────────────────────────────────┘
        ▼
┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 2. FICHE PROD │ /operations/inventaire/produit/:id                          │
│               │ - Historique prix + comparatif fournisseurs                 │
│               │ - CTA "Négocier / MAJ prix"                                 │
└───────┬───────┴─────────────────────────────────────────────────────────────┘
        ▼
┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 3. NÉGOCIATION│ Modal                                                       │
│               │ - Choix fournisseur, nouveau prix, motif                    │
│               │ - Enregistrer → EVENT PRICE_UPDATED                         │
└───────┬───────┴─────────────────────────────────────────────────────────────┘
        ▼
┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 4. MARGES     │ /finance/margins                                            │
│               │ - Graphe marge avant/après                                  │
│               │ - Audit trail lien décision                                 │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ NG-NAV-3 : Transactions → Reco Assistée → Feedback Rules Engine              │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 1. TXNS       │ /finance/transactions                                       │
│               │ - Vue "non rapprochées" + badge suggestion ML               │
│               │ - Sélection multiple → "Lancer rapprochement"               │
└───────┬───────┴─────────────────────────────────────────────────────────────┘
        ▼
┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 2. RECO       │ /finance/reconciliation                                     │
│ Assistée      │ - Suggestions affichées en ligne                            │
│               │ - CTA bulk: valider ou ignorer (motif)                      │
└───────┬───────┴─────────────────────────────────────────────────────────────┘
        ▼
┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 3. FEEDBACK   │ Inline                                                      │
│ Rules Engine  │ - Prompt "Catégorie correcte ?" Oui/Non                     │
│               │ - Envoi feedback -> learn_from_feedback                     │
└───────┬───────┴─────────────────────────────────────────────────────────────┘
        ▼
┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 4. ANOMALIES  │ /intelligence/anomalies?type=SEQUENCE_GAP                   │
│ Finance       │ - Suivi gaps restants, taux rapprochement                   │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ NG-NAV-4 : Import Facture → Stock → Forecast Ventes                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 1. IMPORT     │ /operations/factures/import                                 │
│ Facture       │ - Dropzone → parse lignes                                   │
│               │ - CTA: "Valider & MAJ stock"                                │
└───────┬───────┴─────────────────────────────────────────────────────────────┘
        ▼
┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 2. FICHE PROD │ (optionnel auto-open)                                       │
│               │ - Vérifier stock et prix mis à jour                         │
└───────┬───────┴─────────────────────────────────────────────────────────────┘
        ▼
┌───────────────┬─────────────────────────────────────────────────────────────┐
│ 3. FORECAST   │ /intelligence/forecast?type=sales                           │
│ Ventes        │ - Recalcul prévisions ventes 30j                            │
│               │ - Alerte si tendance baissière ou données insuffisantes     │
└───────────────┴─────────────────────────────────────────────────────────────┘
```
