# NewCMS Finance API

## Vue d'ensemble

Module d'endpoints agrégés pour le nouveau CMS, offrant une vue consolidée des données financières avec intelligence artificielle pour le rapprochement bancaire.

## Architecture

```
/newcms/finance/
├── overview              GET   - Vue d'ensemble finance complète
├── transactions          GET   - Liste paginée des transactions
└── reconciliation/apply  POST  - Application d'une suggestion IA
```

## Endpoints

### GET /newcms/finance/overview

Vue d'ensemble finance agrégée retournant:

1. **Stats de rapprochement** (60 derniers jours)
   - Nombre de transactions matched/pending/unmatched
   - Pourcentages de rapprochement
   - Montants totaux

2. **Cash-flow sur 30 jours**
   - Total entrées/sorties
   - Cash-flow net
   - Moyennes quotidiennes
   - Solde actuel

3. **Top 5 suggestions IA de rapprochement**
   - Matching automatique transactions ↔ factures
   - Score de confiance IA
   - Type de match (exact, fuzzy, multi_line, alias)
   - Explication du match

4. **5 dernières transactions**
   - Date, montant, libellé
   - Direction (IN/OUT/TRANSFER)
   - Statut de rapprochement

#### Exemple de réponse

```json
{
  "reconciliation_stats": {
    "matched_count": 42,
    "pending_count": 0,
    "unmatched_count": 8,
    "matched_percentage": 84.0,
    "pending_percentage": 0.0,
    "unmatched_percentage": 16.0,
    "total_amount_matched": 12450.50,
    "total_amount_pending": 0.0
  },
  "cashflow_30d": {
    "period_days": 30,
    "total_inflow": 25000.00,
    "total_outflow": 18500.00,
    "net_cashflow": 6500.00,
    "avg_daily_inflow": 833.33,
    "avg_daily_outflow": 616.67,
    "current_balance": 45230.75
  },
  "ai_suggestions": [
    {
      "suggestion_id": "ai-1234-1702334567.123",
      "transaction_id": 1234,
      "transaction_date": "2024-12-10",
      "transaction_amount": 156.80,
      "transaction_label": "PRELEVEMENT METRO",
      "matched_invoice_ids": [567],
      "matched_invoices_info": [
        {
          "id": 567,
          "invoice_number": "FA-2024-1234",
          "supplier_name": "METRO France",
          "amount": 156.80,
          "date": "2024-12-09"
        }
      ],
      "confidence": 0.95,
      "match_type": "exact",
      "total_matched_amount": 156.80,
      "difference": 0.0,
      "explanation": "Match exact avec confiance 95%"
    }
  ],
  "recent_transactions": [
    {
      "id": 1234,
      "date": "2024-12-10",
      "amount": -156.80,
      "label": "PRELEVEMENT METRO",
      "direction": "OUT",
      "category": null,
      "reconciled": false
    }
  ],
  "generated_at": "2024-12-11T21:30:00Z"
}
```

### GET /newcms/finance/transactions

Liste paginée des transactions avec filtres avancés.

#### Paramètres de requête

- `q` (optional): Recherche texte sur le libellé
- `date_from` (optional): Date de début (format: YYYY-MM-DD)
- `date_to` (optional): Date de fin (format: YYYY-MM-DD)
- `amount_min` (optional): Montant minimum (€)
- `amount_max` (optional): Montant maximum (€)
- `category` (optional): Filtrage par catégorie
- `page` (default: 1): Numéro de page
- `size` (default: 50, max: 500): Taille de page

#### Exemple de requête

```
GET /newcms/finance/transactions?q=METRO&amount_min=100&amount_max=500&page=1&size=20
```

#### Exemple de réponse

```json
{
  "transactions": [
    {
      "id": 1234,
      "date": "2024-12-10",
      "amount": -156.80,
      "label": "PRELEVEMENT METRO",
      "direction": "OUT",
      "category": null,
      "reconciled": false
    }
  ],
  "total": 42,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

### POST /newcms/finance/reconciliation/apply

Applique une suggestion de rapprochement IA.

#### Corps de la requête

```json
{
  "suggestion_id": "ai-1234-1702334567.123",
  "transaction_id": 1234,
  "invoice_ids": [567],
  "user_comment": "Rapprochement validé manuellement"
}
```

#### Réponse

```json
{
  "success": true,
  "transaction_id": 1234,
  "invoice_ids": [567],
  "reconciled_at": "2024-12-11T21:30:00Z",
  "message": "Rapprochement appliqué avec succès: 1 facture(s) rapprochée(s)"
}
```

## Intelligence Artificielle

Le module utilise `BankReconciliationEngine` pour le matching automatique:

### Types de Match

1. **EXACT**: Montant et date identiques (±3 jours)
   - Confiance: 0.98

2. **FUZZY_AMOUNT**: Montant approximatif (±3%), date proche
   - Confiance: 0.70 - 0.90

3. **MULTI_LINE**: Plusieurs factures pour une transaction
   - Confiance: 0.75

4. **ALIAS**: Reconnaissance via alias fournisseur
   - Confiance: 0.90

### Critères de Matching

- **Tolérance montant**: ±3% (fuzzy), ±0.5% (exact)
- **Écart de date**: Maximum 45 jours
- **Score de confiance minimum**: 0.5 pour suggestion, 0.7 pour auto-application

## Mapping Tenant/Entity

Le module gère la conversion tenant → entity pour `finance_transactions`:

- Tenant Intelligence (4) → Entity Epicerie Groupe (2)
- Autres tenants → Même ID d'entity

## Base de Données

### Tables utilisées

- `finance_transactions` - Transactions bancaires (entity_id)
- `finance_reconciliations` - Rapprochements transaction↔facture
- `finance_invoices_supplier` - Factures fournisseurs (entity_id)
- `finance_vendors` - Fournisseurs
- Tables générées par `BankReconciliationEngine`:
  - `bank_reconciliation`
  - `supplier_aliases`
  - `reconciliation_patterns`
  - `reconciliation_alerts`

## Dépendances

- `core.finance.bank_reconciliation.BankReconciliationEngine` - Moteur IA
- `core.data_repository` - Accès données
- `backend.dependencies.tenant` - Gestion multi-tenant

## Conventions

### ResponseWrapper

Toutes les réponses suivent le standard ResponseWrapper (sauf exclusions middleware).

### Gestion des erreurs

- 404: Resource non trouvée
- 400: Validation échouée
- 500: Erreur interne avec logging détaillé

### Vue Groupe vs Comptes Individuels

Par défaut, les stats agrègent sur l'entity (Epicerie groupe = 2), permettant une vue consolidée pour le tenant Intelligence (4).

## Tests

```bash
# Tester les imports
python test_newcms_finance.py

# Tester les endpoints (avec serveur lancé)
curl http://localhost:8000/newcms/finance/overview

# Tester avec filtres
curl "http://localhost:8000/newcms/finance/transactions?q=METRO&amount_min=100"
```

## Performance

- Les suggestions IA sont calculées à la volée (pas de cache)
- Limite de 5 suggestions pour l'overview
- Pagination recommandée pour les transactions (max 500/page)
- Considérer un cache Redis pour les stats de rapprochement si volume élevé

## Évolutions futures

1. Cache des suggestions IA (Redis)
2. Webhooks pour notifications de rapprochement
3. Export CSV/Excel des transactions
4. Graphiques de cash-flow prédictif
5. Intégration API bancaire (DSP2) pour import automatique
