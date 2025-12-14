# NewCMS Finance - Exemples d'Utilisation

## Quick Start

### Lancer le serveur

```bash
cd /home/ruuuzer/Documents/monprojet
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Accéder à la documentation interactive

```
http://localhost:8000/docs
```

---

## Exemples d'Appels API

### 1. Vue d'ensemble Finance

**Requête:**
```bash
curl -X GET "http://localhost:8000/api/newcms/finance/overview" \
  -H "Accept: application/json"
```

**Réponse (exemple):**
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
    },
    {
      "suggestion_id": "ai-1235-1702334568.456",
      "transaction_id": 1235,
      "transaction_date": "2024-12-09",
      "transaction_amount": 234.50,
      "transaction_label": "VIR LECLERC DRIVE",
      "matched_invoice_ids": [568, 569],
      "matched_invoices_info": [
        {
          "id": 568,
          "invoice_number": "FA-2024-1235",
          "supplier_name": "E.Leclerc",
          "amount": 134.50,
          "date": "2024-12-08"
        },
        {
          "id": 569,
          "invoice_number": "FA-2024-1236",
          "supplier_name": "E.Leclerc",
          "amount": 100.00,
          "date": "2024-12-08"
        }
      ],
      "confidence": 0.82,
      "match_type": "multi_line",
      "total_matched_amount": 234.50,
      "difference": 0.0,
      "explanation": "Match multi_line avec confiance 82%"
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
    },
    {
      "id": 1233,
      "date": "2024-12-09",
      "amount": 1500.00,
      "label": "VIREMENT SALAIRE",
      "direction": "IN",
      "category": null,
      "reconciled": true
    }
  ],
  "generated_at": "2024-12-11T21:30:00Z"
}
```

---

### 2. Liste des Transactions

#### 2.1 Liste basique (page 1, 50 résultats)

```bash
curl -X GET "http://localhost:8000/api/newcms/finance/transactions" \
  -H "Accept: application/json"
```

#### 2.2 Recherche par texte

```bash
curl -X GET "http://localhost:8000/api/newcms/finance/transactions?q=METRO" \
  -H "Accept: application/json"
```

#### 2.3 Filtrage par plage de dates

```bash
curl -X GET "http://localhost:8000/api/newcms/finance/transactions?date_from=2024-12-01&date_to=2024-12-11" \
  -H "Accept: application/json"
```

#### 2.4 Filtrage par plage de montants

```bash
curl -X GET "http://localhost:8000/api/newcms/finance/transactions?amount_min=100&amount_max=500" \
  -H "Accept: application/json"
```

#### 2.5 Combinaison de filtres avec pagination

```bash
curl -X GET "http://localhost:8000/api/newcms/finance/transactions?q=LECLERC&amount_min=50&amount_max=1000&date_from=2024-11-01&page=1&size=20" \
  -H "Accept: application/json"
```

**Réponse (exemple):**
```json
{
  "transactions": [
    {
      "id": 1235,
      "date": "2024-12-09",
      "amount": -234.50,
      "label": "VIR LECLERC DRIVE",
      "direction": "OUT",
      "category": null,
      "reconciled": false
    },
    {
      "id": 1200,
      "date": "2024-11-28",
      "amount": -189.20,
      "label": "CARTE LECLERC",
      "direction": "OUT",
      "category": "Alimentation",
      "reconciled": true
    }
  ],
  "total": 12,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

---

### 3. Application d'un Rapprochement

#### 3.1 Rapprochement simple (1 transaction ↔ 1 facture)

```bash
curl -X POST "http://localhost:8000/api/newcms/finance/reconciliation/apply" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "suggestion_id": "ai-1234-1702334567.123",
    "transaction_id": 1234,
    "invoice_ids": [567],
    "user_comment": "Match validé - METRO"
  }'
```

#### 3.2 Rapprochement multi-lignes (1 transaction ↔ N factures)

```bash
curl -X POST "http://localhost:8000/api/newcms/finance/reconciliation/apply" \
  -H "Accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "suggestion_id": "ai-1235-1702334568.456",
    "transaction_id": 1235,
    "invoice_ids": [568, 569],
    "user_comment": "Rapprochement multi-factures validé"
  }'
```

**Réponse (exemple):**
```json
{
  "success": true,
  "transaction_id": 1234,
  "invoice_ids": [567],
  "reconciled_at": "2024-12-11T21:35:00Z",
  "message": "Rapprochement appliqué avec succès: 1 facture(s) rapprochée(s)"
}
```

---

## Scénarios d'Utilisation

### Scénario 1: Morning Brief Finance

**Objectif:** Obtenir un aperçu rapide de la situation financière du matin.

```bash
# 1. Récupérer l'overview
curl -X GET "http://localhost:8000/api/newcms/finance/overview" | jq

# Analyser:
# - Taux de rapprochement (target: >90%)
# - Cash-flow net sur 30j (positif/négatif?)
# - Nombre de suggestions IA en attente
# - Solde actuel
```

**Indicateurs clés:**
- ✅ Rapprochement > 90% = Situation saine
- ⚠️ Rapprochement < 80% = Attention requise
- 🚨 Rapprochement < 60% = Action urgente

---

### Scénario 2: Traitement des Suggestions IA

**Objectif:** Valider les suggestions de rapprochement en masse.

```bash
# 1. Récupérer l'overview pour les suggestions
OVERVIEW=$(curl -s "http://localhost:8000/api/newcms/finance/overview")

# 2. Parser les suggestions avec confiance > 0.9
echo $OVERVIEW | jq '.ai_suggestions[] | select(.confidence > 0.9)'

# 3. Appliquer les suggestions haute confiance
for suggestion in $(echo $OVERVIEW | jq -c '.ai_suggestions[] | select(.confidence > 0.9)'); do
  SUGGESTION_ID=$(echo $suggestion | jq -r '.suggestion_id')
  TRANSACTION_ID=$(echo $suggestion | jq -r '.transaction_id')
  INVOICE_IDS=$(echo $suggestion | jq -c '.matched_invoice_ids')

  curl -X POST "http://localhost:8000/api/newcms/finance/reconciliation/apply" \
    -H "Content-Type: application/json" \
    -d "{
      \"suggestion_id\": \"$SUGGESTION_ID\",
      \"transaction_id\": $TRANSACTION_ID,
      \"invoice_ids\": $INVOICE_IDS,
      \"user_comment\": \"Auto-validé - Confiance > 0.9\"
    }"
done
```

---

### Scénario 3: Audit des Grosses Transactions

**Objectif:** Analyser les transactions > 500€ non rapprochées.

```bash
# 1. Récupérer les transactions > 500€
curl -X GET "http://localhost:8000/api/newcms/finance/transactions?amount_min=500&size=100" \
  | jq '.transactions[] | select(.reconciled == false)'

# 2. Pour chaque transaction non rapprochée, chercher les factures correspondantes
# (logique métier dans le frontend ou script)
```

---

### Scénario 4: Rapport Mensuel Cash-Flow

**Objectif:** Analyser l'évolution du cash-flow sur plusieurs périodes.

```bash
# Récupérer l'overview actuel (30j)
curl -X GET "http://localhost:8000/api/newcms/finance/overview" \
  | jq '{
    period: .cashflow_30d.period_days,
    inflow: .cashflow_30d.total_inflow,
    outflow: .cashflow_30d.total_outflow,
    net: .cashflow_30d.net_cashflow,
    balance: .cashflow_30d.current_balance
  }'
```

**Indicateurs:**
- **Ratio IN/OUT**: > 1.0 = Positif, < 1.0 = Déficit
- **Avg daily outflow**: Estimation dépenses quotidiennes
- **Runway**: Nombre de jours restants avec le solde actuel

---

### Scénario 5: Recherche de Transactions Spécifiques

**Objectif:** Retrouver toutes les transactions liées à un fournisseur.

```bash
# Exemple: Toutes les transactions METRO de novembre
curl -X GET "http://localhost:8000/api/newcms/finance/transactions?q=METRO&date_from=2024-11-01&date_to=2024-11-30&size=100" \
  | jq '{
    total: .total,
    total_amount: [.transactions[].amount] | add,
    transactions: .transactions
  }'
```

---

## Python Requests (pour Scripts)

### Exemple avec requests

```python
import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/newcms/finance"

# 1. Overview
response = requests.get(f"{BASE_URL}/overview")
overview = response.json()

print(f"Taux de rapprochement: {overview['reconciliation_stats']['matched_percentage']}%")
print(f"Solde actuel: {overview['cashflow_30d']['current_balance']}€")
print(f"Suggestions IA: {len(overview['ai_suggestions'])}")

# 2. Transactions filtrées
today = date.today()
date_from = (today - timedelta(days=7)).isoformat()

params = {
    "q": "METRO",
    "date_from": date_from,
    "amount_min": 100,
    "page": 1,
    "size": 50,
}

response = requests.get(f"{BASE_URL}/transactions", params=params)
transactions = response.json()

print(f"\nTransactions trouvées: {transactions['total']}")
for tx in transactions['transactions']:
    print(f"  - {tx['date']} | {tx['amount']:>8.2f}€ | {tx['label']}")

# 3. Appliquer un rapprochement
if overview['ai_suggestions']:
    suggestion = overview['ai_suggestions'][0]

    payload = {
        "suggestion_id": suggestion['suggestion_id'],
        "transaction_id": suggestion['transaction_id'],
        "invoice_ids": suggestion['matched_invoice_ids'],
        "user_comment": "Validé automatiquement",
    }

    response = requests.post(f"{BASE_URL}/reconciliation/apply", json=payload)
    result = response.json()

    if result['success']:
        print(f"\n✅ Rapprochement appliqué: {result['message']}")
    else:
        print(f"\n❌ Erreur: {result.get('message', 'Unknown error')}")
```

---

## JavaScript/TypeScript (Frontend)

### Exemple avec fetch

```typescript
const BASE_URL = 'http://localhost:8000/api/newcms/finance';

// 1. Récupérer l'overview
async function getFinanceOverview() {
  const response = await fetch(`${BASE_URL}/overview`);
  const data = await response.json();

  console.log('Taux de rapprochement:', data.reconciliation_stats.matched_percentage + '%');
  console.log('Solde actuel:', data.cashflow_30d.current_balance + '€');

  return data;
}

// 2. Récupérer les transactions avec filtres
async function getTransactions(filters: {
  q?: string;
  dateFrom?: string;
  dateTo?: string;
  amountMin?: number;
  amountMax?: number;
  page?: number;
  size?: number;
}) {
  const params = new URLSearchParams();

  if (filters.q) params.append('q', filters.q);
  if (filters.dateFrom) params.append('date_from', filters.dateFrom);
  if (filters.dateTo) params.append('date_to', filters.dateTo);
  if (filters.amountMin !== undefined) params.append('amount_min', filters.amountMin.toString());
  if (filters.amountMax !== undefined) params.append('amount_max', filters.amountMax.toString());
  if (filters.page) params.append('page', filters.page.toString());
  if (filters.size) params.append('size', filters.size.toString());

  const response = await fetch(`${BASE_URL}/transactions?${params}`);
  return await response.json();
}

// 3. Appliquer un rapprochement
async function applyReconciliation(
  suggestionId: string,
  transactionId: number,
  invoiceIds: number[],
  comment?: string
) {
  const response = await fetch(`${BASE_URL}/reconciliation/apply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      suggestion_id: suggestionId,
      transaction_id: transactionId,
      invoice_ids: invoiceIds,
      user_comment: comment,
    }),
  });

  return await response.json();
}

// Utilisation
(async () => {
  const overview = await getFinanceOverview();

  // Appliquer les suggestions haute confiance
  for (const suggestion of overview.ai_suggestions) {
    if (suggestion.confidence > 0.9) {
      const result = await applyReconciliation(
        suggestion.suggestion_id,
        suggestion.transaction_id,
        suggestion.matched_invoice_ids,
        `Auto-validé - Confiance ${(suggestion.confidence * 100).toFixed(0)}%`
      );

      console.log('Rapprochement appliqué:', result.message);
    }
  }

  // Rechercher les transactions METRO
  const metroTransactions = await getTransactions({
    q: 'METRO',
    amountMin: 100,
    page: 1,
    size: 20,
  });

  console.log(`Transactions METRO: ${metroTransactions.total}`);
})();
```

---

## Tests avec pytest

```bash
# Lancer tous les tests
pytest tests/test_newcms_finance_integration.py -v

# Lancer un test spécifique
pytest tests/test_newcms_finance_integration.py::TestFinanceOverview::test_overview_structure -v

# Avec coverage
pytest tests/test_newcms_finance_integration.py --cov=backend.api.newcms.finance --cov-report=html
```

---

## Monitoring & Debugging

### Logs backend

```bash
# Suivre les logs en temps réel
tail -f logs/backend.log | grep "newcms.finance"

# Filtrer les erreurs
tail -f logs/backend.log | grep "ERROR.*finance"
```

### Performance

```bash
# Mesurer le temps de réponse
time curl -X GET "http://localhost:8000/api/newcms/finance/overview"

# Avec httpie (plus lisible)
http GET "http://localhost:8000/api/newcms/finance/overview"
```

---

## Troubleshooting

### Erreur 404: Transaction non trouvée

```bash
# Vérifier que la transaction existe
psql -d inventaire -c "SELECT id, label, amount FROM finance_transactions WHERE id = 1234;"
```

### Erreur 500: Suggestions IA

```bash
# Vérifier les logs
tail -f logs/backend.log | grep "BankReconciliationEngine"

# Vérifier les tables générées
psql -d inventaire -c "\dt *reconciliation*"
```

### Performances lentes

```bash
# Vérifier les index
psql -d inventaire -c "\d finance_transactions"

# Analyser une requête
psql -d inventaire -c "EXPLAIN ANALYZE SELECT * FROM finance_transactions WHERE entity_id = 2 LIMIT 50;"
```

---

## Ressources

- **Documentation API**: http://localhost:8000/docs
- **Code source**: `/backend/api/newcms/finance.py`
- **Documentation complète**: `/backend/api/newcms/README.md`
- **Rapport d'implémentation**: `/IMPLEMENTATION_NEWCMS_FINANCE.md`
- **Tests**: `/tests/test_newcms_finance_integration.py`
