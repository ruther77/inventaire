# Quick Start - Système de Feedback de Catégorisation

Guide rapide pour mettre en place et utiliser le système de feedback de catégorisation.

## Installation (5 minutes)

### Étape 1: Appliquer la Migration SQL

```bash
cd /home/ruuuzer/Documents/monprojet

# Vérifier que la base de données est accessible
psql -U postgres -d inventaire -c "SELECT version();"

# Appliquer la migration
bash scripts/apply_categorization_feedback_migration.sh
```

**Résultat attendu:**
```
✓ Table finance_categorization_feedback already exists.
ou
✓ Migration applied successfully!
```

### Étape 2: Vérifier l'Installation

```bash
# Vérifier que la table existe
psql -U postgres -d inventaire -c "\d finance_categorization_feedback"
```

### Étape 3: Redémarrer le Backend

```bash
# Si le backend est en cours d'exécution
# Redémarrer pour charger les nouveaux endpoints
docker-compose restart backend
# ou
systemctl restart backend
```

## Test Rapide (2 minutes)

### Test 1: Tester les Endpoints API

```bash
# 1. Stats de feedback (devrait retourner 0 au début)
curl http://localhost:8000/api/finance/categorization/feedback/stats

# 2. Corrections communes (devrait retourner [])
curl http://localhost:8000/api/finance/categorization/feedback/common-corrections
```

### Test 2: Enregistrer un Feedback Test

```bash
# Remplacer 1 par un ID de transaction existant
curl -X POST http://localhost:8000/api/finance/transactions/1/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "actual_category_id": 8,
    "predicted_category_id": 5,
    "confidence_score": 0.75,
    "correction_source": "manual"
  }'
```

**Résultat attendu:**
```json
{
  "id": 1,
  "transaction_id": 1,
  "message": "Feedback enregistré avec succès"
}
```

### Test 3: Vérifier en Base de Données

```bash
psql -U postgres -d inventaire -c "SELECT * FROM finance_categorization_feedback LIMIT 5;"
```

## Utilisation Basique

### Scenario 1: Corriger une Catégorie d'une Transaction

```python
from core.bank_import.categorizer import record_categorization_feedback

# Enregistrer une correction
feedback_id = record_categorization_feedback(
    transaction_id=12345,        # ID de la transaction
    predicted_category_id=5,     # Catégorie prédite (optionnel)
    actual_category_id=8,        # Catégorie correcte
    confidence_score=0.75,       # Score de confiance (optionnel)
    user_id=1,                   # ID de l'utilisateur
    correction_source="manual"   # Type: manual, rule, bulk_action
)

print(f"Feedback enregistré: {feedback_id}")
```

### Scenario 2: Catégoriser une Transaction

```python
from core.bank_import.categorizer import TransactionCategorizer
from core.bank_import.models import ParsedTransaction, TransactionDirection
from datetime import date
from decimal import Decimal

# Créer une transaction
transaction = ParsedTransaction(
    date_operation=date(2025, 1, 15),
    date_valeur=date(2025, 1, 15),
    libelle="RESTAURANT LE BISTROT",
    montant=Decimal("45.80"),
    direction=TransactionDirection.OUT,
)

# Catégoriser
categorizer = TransactionCategorizer(load_db_rules=True)
result = categorizer.categorize(transaction)

print(f"Catégorie: {result.category_code}")
print(f"Nom: {result.category_name}")
print(f"Confiance: {result.confidence:.2%}")
print(f"Mot-clé: {result.matched_keyword}")
```

### Scenario 3: Voir les Statistiques

```python
from core.bank_import.categorizer import get_feedback_stats, get_common_corrections

# Stats globales
stats = get_feedback_stats()
print(f"Total corrections: {stats['total_corrections']}")
print(f"Confiance moyenne (erreurs): {stats['avg_wrong_confidence']:.2%}")

# Corrections fréquentes
corrections = get_common_corrections(limit=5)
for c in corrections:
    print(f"{c['predicted_name']} → {c['actual_name']}: {c['correction_count']} fois")
```

## Intégration Frontend

### Composant Simple

```jsx
import React, { useState } from 'react';

function CategoryEditor({ transaction, categories }) {
  const [saving, setSaving] = useState(false);

  const handleChange = async (newCategoryId) => {
    setSaving(true);
    try {
      // 1. Update transaction
      await fetch(`/api/finance/transactions/${transaction.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category_id: newCategoryId })
      });

      // 2. Record feedback
      await fetch(`/api/finance/transactions/${transaction.id}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          actual_category_id: newCategoryId,
          predicted_category_id: transaction.category_id,
          confidence_score: transaction.category_confidence
        })
      });

      alert('✓ Catégorie mise à jour avec feedback');
    } catch (error) {
      alert('✗ Erreur: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <select
      onChange={(e) => handleChange(parseInt(e.target.value))}
      disabled={saving}
    >
      {categories.map(c => (
        <option key={c.id} value={c.id}>{c.name}</option>
      ))}
    </select>
  );
}
```

## API Reference (Rapide)

### 1. Enregistrer un Feedback

**POST** `/api/finance/transactions/{id}/feedback`

```json
{
  "actual_category_id": 8,
  "predicted_category_id": 5,
  "confidence_score": 0.75,
  "correction_source": "manual"
}
```

### 2. Voir les Stats

**GET** `/api/finance/categorization/feedback/stats`

Response:
```json
{
  "total_corrections": 150,
  "avg_wrong_confidence": 0.65,
  "manual_corrections": 120
}
```

### 3. Corrections Communes

**GET** `/api/finance/categorization/feedback/common-corrections?limit=10`

Response:
```json
[
  {
    "predicted_name": "Alimentation",
    "actual_name": "Fournitures",
    "correction_count": 25,
    "avg_confidence": 0.68
  }
]
```

## Exemples d'Usage Réel

### Import CSV avec Auto-Catégorisation

```python
from core.bank_import.csv_parser import parse_csv_file
from core.bank_import.categorizer import TransactionCategorizer

# 1. Parser le CSV
transactions = parse_csv_file("statements.csv")

# 2. Catégoriser automatiquement
categorizer = TransactionCategorizer(load_db_rules=True)
categorized, uncategorized = categorizer.apply_categories(transactions)

print(f"✓ {categorized} catégorisées")
print(f"⚠ {uncategorized} à catégoriser")

# 3. Sauvegarder en DB
for txn in transactions:
    save_transaction(txn)  # Inclut category et confidence
```

### Correction en Masse

```python
from core.bank_import.categorizer import record_categorization_feedback

# Liste des transactions à corriger
transaction_ids = [101, 102, 103, 104]
target_category_id = 8  # Nouvelle catégorie

# Appliquer la correction
for txn_id in transaction_ids:
    # Update transaction
    update_transaction_category(txn_id, target_category_id)

    # Record feedback
    record_categorization_feedback(
        transaction_id=txn_id,
        predicted_category_id=get_old_category(txn_id),
        actual_category_id=target_category_id,
        user_id=1,
        correction_source="bulk_action"
    )

print(f"✓ {len(transaction_ids)} transactions corrigées")
```

### Créer une Règle depuis un Pattern

```python
from core.bank_import.categorizer import get_common_corrections

# 1. Identifier les patterns fréquents
corrections = get_common_corrections(limit=10)

# 2. Sélectionner un pattern à transformer en règle
pattern = corrections[0]  # Le plus fréquent
print(f"Pattern: {pattern['predicted_name']} → {pattern['actual_name']}")
print(f"Occurrences: {pattern['correction_count']}")

# 3. Créer une règle manuelle (pour l'instant)
# Dans un SQL client ou via API:
"""
INSERT INTO finance_rules (name, category_id, keywords, is_active)
VALUES (
    'Auto-règle: Restaurant → Repas équipe',
    8,  -- ID de "Repas équipe"
    ARRAY['restaurant', 'bistrot', 'brasserie'],
    true
);
"""
```

## Troubleshooting

### Problème: Table n'existe pas

```bash
# Vérifier que la migration a été appliquée
psql -U postgres -d inventaire -c "\dt finance_categorization_feedback"

# Si pas trouvé, appliquer:
psql -U postgres -d inventaire -f db/migrations/008_categorization_feedback.sql
```

### Problème: Endpoint 404

```bash
# Vérifier que le backend a redémarré
docker-compose logs backend | grep -i "categorization"

# Redémarrer si nécessaire
docker-compose restart backend
```

### Problème: Permission denied

```bash
# Vérifier les permissions DB
psql -U postgres -d inventaire -c "GRANT ALL ON finance_categorization_feedback TO your_user;"
```

### Problème: Import échoue

```python
# Vérifier que le module est accessible
try:
    from core.bank_import.categorizer import record_categorization_feedback
    print("✓ Import OK")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    # Vérifier PYTHONPATH
```

## Next Steps

1. **Collecter des Données**
   - Utiliser le système pendant quelques semaines
   - Laisser les utilisateurs corriger les catégories
   - Le feedback sera automatiquement enregistré

2. **Analyser les Patterns**
   ```bash
   # Voir les corrections communes
   curl http://localhost:8000/api/finance/categorization/feedback/common-corrections?limit=20
   ```

3. **Créer des Règles**
   - Identifier les patterns fréquents
   - Créer des règles dans `finance_rules`
   - Améliorer la précision

4. **Monitorer les Stats**
   ```bash
   # Dashboard de stats
   curl http://localhost:8000/api/finance/categorization/feedback/stats
   ```

5. **Planifier ML (Future)**
   - Attendre d'avoir ~500 corrections
   - Entraîner un modèle simple (Naive Bayes)
   - Évaluer la précision

## Ressources

- **Documentation complète:** `docs/CATEGORIZATION_FEEDBACK_SYSTEM.md`
- **Résumé d'implémentation:** `PHASE4_CATEGORISATION_SUMMARY.md`
- **Tests:** `tests/test_categorization_feedback.py`
- **Exemples frontend:** `frontend/src/examples/CategorizationFeedbackExample.jsx`

## Support

Pour toute question:
1. Consulter la documentation complète
2. Vérifier les logs: `docker-compose logs backend`
3. Tester les endpoints manuellement avec `curl`

---

**Durée d'installation:** ~5 minutes
**Prérequis:** PostgreSQL, Python 3.8+, FastAPI
**Status:** ✓ Production Ready
