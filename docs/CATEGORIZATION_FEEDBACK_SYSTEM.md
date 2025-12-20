# Système de Feedback de Catégorisation - Phase 4

## Vue d'ensemble

Le système de feedback de catégorisation permet de collecter les corrections faites par les utilisateurs sur les catégories automatiquement assignées aux transactions. Ces données sont stockées pour un apprentissage futur (ML) et permettent d'améliorer progressivement la précision du moteur de catégorisation.

## Architecture

### 1. Table de Feedback

**Table:** `finance_categorization_feedback`

```sql
CREATE TABLE finance_categorization_feedback (
    id BIGSERIAL PRIMARY KEY,
    transaction_id BIGINT NOT NULL REFERENCES finance_transactions(id),
    predicted_category_id BIGINT REFERENCES finance_categories(id),
    actual_category_id BIGINT NOT NULL REFERENCES finance_categories(id),
    confidence_score NUMERIC(4,3),
    user_id BIGINT,
    correction_source TEXT DEFAULT 'manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**Champs:**
- `transaction_id`: Transaction corrigée
- `predicted_category_id`: Catégorie prédite par le système (peut être NULL)
- `actual_category_id`: Catégorie correcte choisie par l'utilisateur
- `confidence_score`: Score de confiance de la prédiction (0.0-1.0)
- `user_id`: ID de l'utilisateur qui a fait la correction
- `correction_source`: Source de la correction
  - `manual`: Correction manuelle par l'utilisateur
  - `rule`: Correction via une nouvelle règle
  - `bulk_action`: Correction en masse

### 2. Moteur de Catégorisation

**Fichier:** `core/bank_import/categorizer.py`

Le `TransactionCategorizer` utilise un système de catégorisation par priorité:

1. **DB Rules (Priorité: 0.98)** - Règles de la table `finance_rules`
2. **Keywords statiques (Priorité: 0.7-1.0)** - Mots-clés définis dans `categories.py`
3. **Fallback** - Catégorie "à_categoriser" (confiance: 0.0)

**Exemple d'utilisation:**

```python
from core.bank_import.categorizer import TransactionCategorizer
from core.bank_import.models import ParsedTransaction, TransactionDirection

# Créer un categorizer
categorizer = TransactionCategorizer()

# Catégoriser une transaction
result = categorizer.categorize(transaction)

print(f"Catégorie: {result.category_code}")
print(f"Confiance: {result.confidence}")
print(f"Mot-clé matché: {result.matched_keyword}")
```

### 3. Enregistrement du Feedback

**Fonction:** `record_categorization_feedback()`

```python
from core.bank_import.categorizer import record_categorization_feedback

feedback_id = record_categorization_feedback(
    transaction_id=12345,
    predicted_category_id=5,  # Catégorie prédite
    actual_category_id=8,     # Catégorie correcte
    confidence_score=0.75,
    user_id=1,
    correction_source="manual"
)
```

## API Endpoints

### 1. Enregistrer une Correction

**Endpoint:** `POST /finance/transactions/{transaction_id}/feedback`

**Body:**
```json
{
  "actual_category_id": 8,
  "predicted_category_id": 5,
  "confidence_score": 0.75,
  "correction_source": "manual"
}
```

**Response:**
```json
{
  "id": 123,
  "transaction_id": 12345,
  "message": "Feedback enregistré avec succès"
}
```

**Exemple d'utilisation:**
```javascript
// Frontend - Correction d'une catégorie
async function correctCategory(transactionId, predictedCategoryId, actualCategoryId, confidence) {
  const response = await fetch(`/api/finance/transactions/${transactionId}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      actual_category_id: actualCategoryId,
      predicted_category_id: predictedCategoryId,
      confidence_score: confidence,
      correction_source: 'manual'
    })
  });

  return response.json();
}
```

### 2. Statistiques de Feedback

**Endpoint:** `GET /finance/categorization/feedback/stats`

**Response:**
```json
{
  "total_corrections": 150,
  "unique_transactions": 145,
  "categories_corrected_to": 12,
  "categories_corrected_from": 8,
  "avg_wrong_confidence": 0.65,
  "manual_corrections": 120,
  "rule_corrections": 20,
  "bulk_corrections": 10
}
```

**Utilité:**
- Évaluer la performance du système de catégorisation
- Identifier les axes d'amélioration
- Suivre l'évolution de la précision

### 3. Corrections Communes

**Endpoint:** `GET /finance/categorization/feedback/common-corrections?limit=20`

**Response:**
```json
[
  {
    "predicted_code": "alimentation",
    "predicted_name": "Alimentation",
    "actual_code": "fournitures",
    "actual_name": "Fournitures",
    "correction_count": 25,
    "avg_confidence": 0.68
  },
  {
    "predicted_code": "transport",
    "predicted_name": "Transport",
    "actual_code": "livraison",
    "actual_name": "Livraison",
    "correction_count": 18,
    "avg_confidence": 0.72
  }
]
```

**Utilité:**
- Identifier les patterns de correction récurrents
- Créer de nouvelles règles de catégorisation
- Améliorer les keywords existants

## Workflow d'Utilisation

### 1. Import de Transactions

```
1. Import CSV/PDF → finance_transactions
2. Auto-catégorisation via TransactionCategorizer
3. Stockage du score de confiance dans la transaction
```

### 2. Correction par l'Utilisateur

```
1. Utilisateur voit une transaction mal catégorisée
2. Utilisateur change la catégorie dans l'interface
3. Frontend envoie POST /transactions/{id}/feedback
4. Feedback stocké dans finance_categorization_feedback
```

### 3. Analyse et Amélioration

```
1. Analyse des statistiques de feedback
2. Identification des patterns de correction fréquents
3. Création de nouvelles règles dans finance_rules
4. Amélioration progressive de la précision
```

## Stratégie d'Apprentissage Futur (ML)

### Phase Actuelle (Phase 4)
- **Objectif:** Collecter les données de correction
- **Approche:** Stockage passif du feedback
- **Pas de ML actif** pour l'instant

### Phase Future (Phase 5+)
- **Objectif:** Utiliser les données pour entraîner un modèle ML
- **Approches possibles:**
  1. **Classification supervisée:** Utiliser les corrections comme labels
  2. **Feature engineering:** Extraire des features des libellés
  3. **Embeddings:** Utiliser des embeddings de texte (BERT, etc.)
  4. **Active Learning:** Demander des corrections sur les cas incertains

### Features Potentielles pour ML
```python
# Exemple de features à extraire
features = {
    'libelle_embedding': [...],  # Embedding du libellé
    'montant': 123.45,
    'jour_semaine': 2,
    'jour_mois': 15,
    'compte_id': 1,
    'confidence_actuelle': 0.75,
    'keywords_matched': ['restaurant', 'paris'],
    'banque': 'LCL'
}
```

## Métriques de Performance

### Métriques Actuelles
- Nombre total de corrections
- Taux de correction par catégorie
- Confiance moyenne des prédictions incorrectes
- Patterns de correction fréquents

### Métriques Futures (avec ML)
- Précision (Accuracy)
- Précision par catégorie (Precision)
- Rappel par catégorie (Recall)
- F1-Score
- Courbe d'apprentissage
- Réduction du taux de correction au fil du temps

## Installation et Configuration

### 1. Appliquer la Migration

```bash
# Méthode 1: Script automatique
cd /home/ruuuzer/Documents/monprojet
bash scripts/apply_categorization_feedback_migration.sh

# Méthode 2: Manuellement
psql -U postgres -d inventaire -f db/migrations/008_categorization_feedback.sql
```

### 2. Vérifier l'Installation

```sql
-- Vérifier la table
SELECT * FROM finance_categorization_feedback LIMIT 5;

-- Vérifier les index
\d finance_categorization_feedback
```

### 3. Test du Système

```python
# Test Python
from core.bank_import.categorizer import (
    record_categorization_feedback,
    get_feedback_stats,
    get_common_corrections
)

# Enregistrer un feedback de test
feedback_id = record_categorization_feedback(
    transaction_id=1,
    predicted_category_id=5,
    actual_category_id=8,
    confidence_score=0.75,
    user_id=1,
    correction_source="test"
)

# Vérifier les stats
stats = get_feedback_stats()
print(stats)

# Vérifier les corrections communes
corrections = get_common_corrections(limit=10)
print(corrections)
```

## Exemple d'Intégration Frontend

### React Component

```jsx
import React, { useState } from 'react';

function TransactionCategoryEditor({ transaction }) {
  const [saving, setSaving] = useState(false);

  const handleCategoryChange = async (newCategoryId) => {
    setSaving(true);

    try {
      // Enregistrer la nouvelle catégorie
      await fetch(`/api/finance/transactions/${transaction.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ category_id: newCategoryId })
      });

      // Enregistrer le feedback
      await fetch(`/api/finance/transactions/${transaction.id}/feedback`, {
        method: 'POST',
        body: JSON.stringify({
          actual_category_id: newCategoryId,
          predicted_category_id: transaction.category_id,
          confidence_score: transaction.category_confidence,
          correction_source: 'manual'
        })
      });

      toast.success('Catégorie mise à jour et feedback enregistré');
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
    } finally {
      setSaving(false);
    }
  };

  return (
    <CategorySelect
      value={transaction.category_id}
      onChange={handleCategoryChange}
      disabled={saving}
    />
  );
}
```

## FAQ

### Q: Dois-je enregistrer un feedback pour chaque changement de catégorie?
**R:** Oui, idéalement. Cela permet d'améliorer la précision du système. Si la catégorie était NULL ou "à_categoriser", vous pouvez laisser `predicted_category_id` à NULL.

### Q: Que faire avec les corrections en masse?
**R:** Utilisez `correction_source: "bulk_action"` et enregistrez un feedback pour chaque transaction corrigée.

### Q: Comment savoir quelles règles créer?
**R:** Utilisez l'endpoint `/categorization/feedback/common-corrections` pour identifier les patterns fréquents.

### Q: Le feedback affecte-t-il immédiatement la catégorisation?
**R:** Non, le feedback est stocké pour apprentissage futur. Pour un effet immédiat, créez une règle dans `finance_rules`.

### Q: Puis-je supprimer du feedback erroné?
**R:** Oui, vous pouvez supprimer directement dans la table `finance_categorization_feedback`.

## Prochaines Étapes

1. **Phase 4 (Actuelle):** Collecter les données de feedback ✓
2. **Phase 5:** Analyser les patterns de correction
3. **Phase 6:** Créer des règles automatiques basées sur les patterns
4. **Phase 7:** Implémenter un modèle ML simple (ex: Naive Bayes)
5. **Phase 8:** Modèle ML avancé avec embeddings
6. **Phase 9:** Active Learning pour optimiser les corrections

## Ressources

- **Migration SQL:** `/db/migrations/008_categorization_feedback.sql`
- **Code Categorizer:** `/core/bank_import/categorizer.py`
- **API Endpoints:** `/backend/api/finance.py`
- **Script Migration:** `/scripts/apply_categorization_feedback_migration.sh`
