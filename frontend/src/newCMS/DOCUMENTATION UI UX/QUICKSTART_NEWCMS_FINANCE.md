# NewCMS Finance - Quick Start Guide

## Démarrage Rapide (5 minutes)

### Étape 1: Lancer le serveur

```bash
cd /home/ruuuzer/Documents/monprojet
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Attendez le message:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

### Étape 2: Vérifier que ça fonctionne

Ouvrez dans votre navigateur:

```
http://localhost:8000/docs
```

Vous devriez voir la documentation Swagger avec les nouveaux endpoints:
- `GET /api/newcms/finance/overview`
- `GET /api/newcms/finance/transactions`
- `POST /api/newcms/finance/reconciliation/apply`

---

### Étape 3: Premier appel API

Dans un nouveau terminal:

```bash
curl http://localhost:8000/api/newcms/finance/overview | jq
```

Ou directement dans Swagger UI:
1. Cliquez sur `GET /api/newcms/finance/overview`
2. Cliquez sur "Try it out"
3. Cliquez sur "Execute"

**Réponse attendue:**
```json
{
  "reconciliation_stats": { ... },
  "cashflow_30d": { ... },
  "ai_suggestions": [ ... ],
  "recent_transactions": [ ... ],
  "generated_at": "2024-12-11T..."
}
```

---

## Commandes Utiles

### Lancer les Tests

```bash
# Tous les tests
pytest tests/test_newcms_finance_integration.py -v

# Test spécifique
pytest tests/test_newcms_finance_integration.py::TestFinanceOverview -v

# Avec coverage
pytest tests/test_newcms_finance_integration.py --cov=backend.api.newcms.finance
```

---

### Validation des Imports

```bash
python test_newcms_finance.py
```

**Sortie attendue:**
```
✓ Module backend.api.newcms.finance importé avec succès
✓ Router finance existe
Routes disponibles:
  - /newcms/finance/overview
  - /newcms/finance/transactions
  - /newcms/finance/reconciliation/apply
✓ Route /newcms/finance/overview trouvée
✓ Route /newcms/finance/transactions trouvée
✓ Route /newcms/finance/reconciliation/apply trouvée
✓ Tous les schémas Pydantic sont importables
✅ Tous les tests réussis!
```

---

### Exemples d'Appels API

#### 1. Overview

```bash
curl http://localhost:8000/api/newcms/finance/overview | jq
```

#### 2. Transactions filtrées

```bash
# Recherche "METRO"
curl "http://localhost:8000/api/newcms/finance/transactions?q=METRO" | jq

# Montant entre 100€ et 500€
curl "http://localhost:8000/api/newcms/finance/transactions?amount_min=100&amount_max=500" | jq

# Combinaison de filtres
curl "http://localhost:8000/api/newcms/finance/transactions?q=LECLERC&amount_min=50&date_from=2024-11-01&page=1&size=20" | jq
```

#### 3. Application d'un rapprochement

```bash
curl -X POST http://localhost:8000/api/newcms/finance/reconciliation/apply \
  -H "Content-Type: application/json" \
  -d '{
    "suggestion_id": "ai-1234-1702334567.123",
    "transaction_id": 1234,
    "invoice_ids": [567],
    "user_comment": "Test rapprochement"
  }' | jq
```

---

## Vérifications Post-Déploiement

### 1. Santé du serveur

```bash
curl http://localhost:8000/health
```

**Attendu:** `{"status":"ok"}`

---

### 2. Endpoints NewCMS Finance

```bash
# Overview
curl -I http://localhost:8000/api/newcms/finance/overview

# Transactions
curl -I http://localhost:8000/api/newcms/finance/transactions

# Réconciliation (HEAD n'est pas supporté pour POST)
```

**Attendu:** `HTTP/1.1 200 OK`

---

### 3. Performance

```bash
# Mesurer le temps de réponse
time curl -s http://localhost:8000/api/newcms/finance/overview > /dev/null

# Avec httpie (plus lisible)
http GET http://localhost:8000/api/newcms/finance/overview --print=hH
```

**Attendu:** < 5 secondes

---

## Debugging

### Logs Backend

```bash
# Suivre les logs en temps réel
tail -f logs/backend.log

# Filtrer les logs finance
tail -f logs/backend.log | grep "newcms.finance"

# Filtrer les erreurs
tail -f logs/backend.log | grep "ERROR"
```

---

### Vérifier la Base de Données

```bash
# Connexion PostgreSQL
psql -U postgres -d inventaire

# Vérifier les transactions
SELECT COUNT(*) FROM finance_transactions;

# Vérifier les rapprochements
SELECT COUNT(*) FROM finance_reconciliations;

# Vérifier les factures
SELECT COUNT(*) FROM finance_invoices_supplier;
```

---

### Python Interactive

```python
# Lancer Python
python

# Tester les imports
from backend.api.newcms.finance import router, FinanceOverviewResponse
print(router.routes)

# Tester BankReconciliationEngine
from core.finance.bank_reconciliation import BankReconciliationEngine
engine = BankReconciliationEngine(tenant_id=1)
status = engine.get_reconciliation_status()
print(status)
```

---

## Troubleshooting

### Erreur: Module 'backend.api.newcms.finance' not found

**Solution:**
```bash
# Vérifier que le fichier existe
ls -la /home/ruuuzer/Documents/monprojet/backend/api/newcms/finance.py

# Vérifier le PYTHONPATH
export PYTHONPATH=/home/ruuuzer/Documents/monprojet:$PYTHONPATH
```

---

### Erreur: Table 'finance_transactions' does not exist

**Solution:**
```bash
# Vérifier les migrations
alembic current

# Appliquer les migrations
alembic upgrade head

# Vérifier les tables
psql -d inventaire -c "\dt finance*"
```

---

### Erreur: 500 Internal Server Error

**Solution:**
```bash
# Vérifier les logs
tail -20 logs/backend.log

# Tester directement la fonction
python -c "
from backend.api.newcms.finance import _get_reconciliation_stats
print(_get_reconciliation_stats(tenant_id=1))
"
```

---

### Erreur: Suggestions IA vides

**Cause possible:** Pas de transactions non rapprochées

**Vérification:**
```bash
psql -d inventaire -c "
SELECT COUNT(*) as total,
       COUNT(*) FILTER (WHERE fr.id IS NOT NULL) as matched,
       COUNT(*) FILTER (WHERE fr.id IS NULL) as unmatched
FROM finance_transactions ft
LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
WHERE ft.entity_id = 2
  AND ft.date_operation >= CURRENT_DATE - INTERVAL '60 days'
  AND ft.direction = 'OUT';
"
```

---

## Scripts Utiles

### Script 1: Morning Brief Finance

```bash
#!/bin/bash
# morning_brief_finance.sh

echo "=== Morning Brief Finance ==="
echo ""

OVERVIEW=$(curl -s http://localhost:8000/api/newcms/finance/overview)

# Taux de rapprochement
MATCHED_PCT=$(echo $OVERVIEW | jq -r '.reconciliation_stats.matched_percentage')
echo "✓ Taux de rapprochement: $MATCHED_PCT%"

# Solde
BALANCE=$(echo $OVERVIEW | jq -r '.cashflow_30d.current_balance')
echo "✓ Solde actuel: $BALANCE€"

# Suggestions IA
AI_COUNT=$(echo $OVERVIEW | jq '.ai_suggestions | length')
echo "✓ Suggestions IA en attente: $AI_COUNT"

# Transactions non rapprochées
UNMATCHED=$(echo $OVERVIEW | jq -r '.reconciliation_stats.unmatched_count')
echo "⚠ Transactions non rapprochées: $UNMATCHED"

echo ""
echo "=== Top 3 Suggestions IA ==="
echo $OVERVIEW | jq -r '.ai_suggestions[0:3] | .[] | "- Transaction #\(.transaction_id) | \(.transaction_label) | Confiance: \(.confidence*100)%"'
```

**Utilisation:**
```bash
chmod +x morning_brief_finance.sh
./morning_brief_finance.sh
```

---

### Script 2: Auto-Validation Haute Confiance

```bash
#!/bin/bash
# auto_validate_high_confidence.sh

OVERVIEW=$(curl -s http://localhost:8000/api/newcms/finance/overview)

echo "=== Auto-Validation Suggestions Confiance > 90% ==="

echo $OVERVIEW | jq -c '.ai_suggestions[] | select(.confidence > 0.9)' | while read suggestion; do
  SUGGESTION_ID=$(echo $suggestion | jq -r '.suggestion_id')
  TRANSACTION_ID=$(echo $suggestion | jq -r '.transaction_id')
  INVOICE_IDS=$(echo $suggestion | jq -c '.matched_invoice_ids')
  CONFIDENCE=$(echo $suggestion | jq -r '.confidence')

  echo "Validation: Transaction #$TRANSACTION_ID (Confiance: $(echo "$CONFIDENCE * 100" | bc)%)"

  curl -s -X POST http://localhost:8000/api/newcms/finance/reconciliation/apply \
    -H "Content-Type: application/json" \
    -d "{
      \"suggestion_id\": \"$SUGGESTION_ID\",
      \"transaction_id\": $TRANSACTION_ID,
      \"invoice_ids\": $INVOICE_IDS,
      \"user_comment\": \"Auto-validé - Confiance > 90%\"
    }" | jq '.message'
done
```

**Utilisation:**
```bash
chmod +x auto_validate_high_confidence.sh
./auto_validate_high_confidence.sh
```

---

## Monitoring Production

### Métriques à Surveiller

1. **Taux de rapprochement**
   - Objectif: > 90%
   - Alerte: < 80%

2. **Temps de réponse**
   - Overview: < 5s
   - Transactions: < 10s

3. **Nombre de suggestions IA**
   - Tendance: Décroissante (amélioration au fil du temps)

4. **Erreurs 500**
   - Objectif: 0
   - Alerte: > 5/jour

---

### Dashboard Grafana (Exemple)

```bash
# Métriques Prometheus
curl http://localhost:8000/metrics/performance | grep finance

# Exemple de métriques
finance_overview_requests_total
finance_overview_response_time_seconds
finance_reconciliation_success_total
finance_reconciliation_error_total
```

---

## Support

### Fichiers de Documentation

1. **README Technique**: `/backend/api/newcms/README.md`
2. **Implémentation**: `/IMPLEMENTATION_NEWCMS_FINANCE.md`
3. **Exemples**: `/NEWCMS_FINANCE_EXAMPLES.md`
4. **Summary**: `/NEWCMS_FINANCE_SUMMARY.md`
5. **Quick Start**: Ce fichier

---

### Commandes de Diagnostic

```bash
# Version Python
python --version

# Dépendances installées
pip list | grep -E "(fastapi|pydantic|sqlalchemy)"

# Vérifier le fichier finance.py
wc -l /home/ruuuzer/Documents/monprojet/backend/api/newcms/finance.py

# Vérifier les routes
grep "^@router" /home/ruuuzer/Documents/monprojet/backend/api/newcms/finance.py
```

---

## Next Steps

Une fois le Quick Start réussi:

1. ✅ Lire la documentation complète: `/backend/api/newcms/README.md`
2. ✅ Tester les exemples: `/NEWCMS_FINANCE_EXAMPLES.md`
3. ✅ Lancer les tests: `pytest tests/test_newcms_finance_integration.py`
4. ✅ Intégrer au frontend React
5. ✅ Configurer le monitoring
6. ✅ Déployer en production

---

**Temps estimé:** 5-10 minutes
**Prérequis:** Python 3.9+, PostgreSQL, dépendances installées

🚀 **Bon déploiement!**
