# Phase 4 - Système de Catégorisation avec Feedback Loop

> Système intelligent de catégorisation de transactions bancaires avec apprentissage continu pour amélioration ML future.

**Status:** ✓ COMPLÉTÉ | **Date:** 2025-12-19 | **Version:** 1.0

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Appliquer la migration SQL
cd /home/ruuuzer/Documents/monprojet
bash scripts/apply_categorization_feedback_migration.sh

# 2. Vérifier l'installation
curl http://localhost:8000/api/finance/categorization/feedback/stats

# 3. Tester un feedback
curl -X POST http://localhost:8000/api/finance/transactions/1/feedback \
  -H "Content-Type: application/json" \
  -d '{"actual_category_id": 8, "predicted_category_id": 5}'

# 4. Analyser les performances
python scripts/analyze_categorization_performance.py
```

**Documentation complète:** [QUICK_START_CATEGORIZATION_FEEDBACK.md](./QUICK_START_CATEGORIZATION_FEEDBACK.md)

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Composants](#composants)
4. [Installation](#installation)
5. [Utilisation](#utilisation)
6. [Documentation](#documentation)
7. [Amélioration Continue](#amélioration-continue)
8. [Roadmap ML](#roadmap-ml)

---

## 🎯 Vue d'Ensemble

### Objectif

Améliorer progressivement la précision de la catégorisation automatique des transactions bancaires en collectant et analysant les corrections faites par les utilisateurs.

### Fonctionnalités Principales

- ✓ **Catégorisation automatique** avec score de confiance
- ✓ **Enregistrement des corrections** utilisateur
- ✓ **Statistiques en temps réel** sur la précision
- ✓ **Identification des patterns** de correction fréquents
- ✓ **API REST complète** pour intégration
- ✓ **Composants React** prêts à l'emploi
- ✓ **Scripts d'analyse** de performance

### Métriques de Succès

| Période | Corrections | Précision | Règles |
|---------|------------|-----------|--------|
| 1 mois  | > 100      | > 70%     | 3-5    |
| 3 mois  | > 500      | > 85%     | 10+    |
| 6 mois  | > 2000     | > 90%     | ML actif |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                        │
│  - TransactionCategoryEditor                                │
│  - FeedbackStatsPanel                                       │
│  - BatchCategoryEditor                                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP REST
┌─────────────────────▼───────────────────────────────────────┐
│                  BACKEND API (FastAPI)                      │
│  POST /transactions/{id}/feedback                           │
│  GET  /categorization/feedback/stats                        │
│  GET  /categorization/feedback/common-corrections           │
└─────────────────────┬───────────────────────────────────────┘
                      │ Python Functions
┌─────────────────────▼───────────────────────────────────────┐
│                  CORE LOGIC (Python)                        │
│  - TransactionCategorizer                                   │
│  - record_categorization_feedback()                         │
│  - get_feedback_stats()                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │ SQL
┌─────────────────────▼───────────────────────────────────────┐
│                DATABASE (PostgreSQL)                        │
│  - finance_categorization_feedback                          │
│  - finance_transactions                                     │
│  - finance_categories                                       │
└─────────────────────────────────────────────────────────────┘
```

**Documentation:** [CATEGORIZATION_FEEDBACK_SYSTEM.md](./docs/CATEGORIZATION_FEEDBACK_SYSTEM.md)

---

## 📦 Composants

### Backend (Python)

#### API Endpoints

1. **POST /finance/transactions/{id}/feedback** - Enregistrer une correction
   ```json
   {
     "actual_category_id": 8,
     "predicted_category_id": 5,
     "confidence_score": 0.75
   }
   ```

2. **GET /finance/categorization/feedback/stats** - Statistiques globales
   ```json
   {
     "total_corrections": 150,
     "avg_wrong_confidence": 0.65,
     "manual_corrections": 120
   }
   ```

3. **GET /finance/categorization/feedback/common-corrections** - Patterns fréquents
   ```json
   [{
     "predicted_name": "Alimentation",
     "actual_name": "Fournitures",
     "correction_count": 25
   }]
   ```

#### Core Functions

```python
from core.bank_import.categorizer import (
    TransactionCategorizer,
    record_categorization_feedback,
    get_feedback_stats,
    get_common_corrections
)

# Catégoriser
categorizer = TransactionCategorizer(load_db_rules=True)
result = categorizer.categorize(transaction)

# Enregistrer feedback
feedback_id = record_categorization_feedback(
    transaction_id=12345,
    predicted_category_id=5,
    actual_category_id=8
)

# Stats
stats = get_feedback_stats()
```

### Frontend (React)

```jsx
import {
  TransactionCategoryEditor,
  FeedbackStatsPanel,
  BatchCategoryEditor
} from './examples/CategorizationFeedbackExample';

// Éditeur de catégorie avec feedback automatique
<TransactionCategoryEditor
  transaction={transaction}
  categories={categories}
  onUpdate={handleUpdate}
/>

// Panneau de statistiques
<FeedbackStatsPanel />

// Correction en masse
<BatchCategoryEditor
  transactions={transactions}
  categories={categories}
  onUpdate={handleUpdate}
/>
```

### Database

**Table:** `finance_categorization_feedback`

| Colonne | Type | Description |
|---------|------|-------------|
| id | BIGSERIAL | ID unique |
| transaction_id | BIGINT | Transaction corrigée |
| predicted_category_id | BIGINT | Catégorie prédite |
| actual_category_id | BIGINT | Catégorie correcte |
| confidence_score | NUMERIC | Score de confiance |
| user_id | BIGINT | Utilisateur |
| correction_source | TEXT | 'manual', 'rule', 'bulk_action' |
| created_at | TIMESTAMPTZ | Date de création |

**Index:** 4 index pour performance optimale

---

## 🔧 Installation

### 1. Migration SQL

```bash
# Option 1: Script automatique (recommandé)
bash scripts/apply_categorization_feedback_migration.sh

# Option 2: Manuelle
psql -U postgres -d inventaire -f db/migrations/008_categorization_feedback.sql
```

### 2. Vérification

```bash
# Vérifier la table
psql -U postgres -d inventaire -c "SELECT COUNT(*) FROM finance_categorization_feedback;"

# Tester les endpoints
curl http://localhost:8000/api/finance/categorization/feedback/stats
```

### 3. Frontend (Optionnel)

```bash
cd frontend
npm install  # Si pas déjà fait

# Les composants sont dans:
# frontend/src/examples/CategorizationFeedbackExample.jsx
```

**Documentation complète:** [Installation Section](./QUICK_START_CATEGORIZATION_FEEDBACK.md#installation-5-minutes)

---

## 💻 Utilisation

### Scénario 1: Catégoriser une Transaction

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
    direction=TransactionDirection.OUT
)

# Catégoriser
categorizer = TransactionCategorizer(load_db_rules=True)
result = categorizer.categorize(transaction)

print(f"Catégorie: {result.category_name}")
print(f"Confiance: {result.confidence:.1%}")
print(f"Mot-clé: {result.matched_keyword}")
```

### Scénario 2: Corriger une Catégorie

```python
from core.bank_import.categorizer import record_categorization_feedback

# L'utilisateur corrige la catégorie
feedback_id = record_categorization_feedback(
    transaction_id=12345,
    predicted_category_id=5,  # Alimentation
    actual_category_id=8,     # Fournitures
    confidence_score=0.75,
    user_id=1,
    correction_source="manual"
)

print(f"Feedback enregistré: {feedback_id}")
```

### Scénario 3: Analyser les Performances

```bash
# Rapport complet
python scripts/analyze_categorization_performance.py --format all

# Graphiques
python scripts/analyze_categorization_performance.py --plot --days 30

# JSON pour intégration
python scripts/analyze_categorization_performance.py --format json
```

### Scénario 4: Frontend

```jsx
function TransactionsPage() {
  const [transaction, setTransaction] = useState(null);
  const [categories, setCategories] = useState([]);

  return (
    <div>
      <TransactionCategoryEditor
        transaction={transaction}
        categories={categories}
        onUpdate={(updated) => {
          // Transaction mise à jour et feedback enregistré automatiquement
          setTransaction(updated);
        }}
      />
    </div>
  );
}
```

---

## 📚 Documentation

### Guides Principaux

| Document | Description | Audience |
|----------|-------------|----------|
| [QUICK_START_CATEGORIZATION_FEEDBACK.md](./QUICK_START_CATEGORIZATION_FEEDBACK.md) | Installation et premiers pas | Tous |
| [CATEGORIZATION_FEEDBACK_SYSTEM.md](./docs/CATEGORIZATION_FEEDBACK_SYSTEM.md) | Architecture et référence API | Développeurs |
| [CATEGORIZATION_CONTINUOUS_IMPROVEMENT.md](./docs/CATEGORIZATION_CONTINUOUS_IMPROVEMENT.md) | Guide d'amélioration | Product Owners |
| [PHASE4_CATEGORISATION_SUMMARY.md](./PHASE4_CATEGORISATION_SUMMARY.md) | Résumé de l'implémentation | Tech Leads |

### Référence Technique

| Document | Description |
|----------|-------------|
| [PHASE4_FILES_INDEX.md](./PHASE4_FILES_INDEX.md) | Index de tous les fichiers |
| [PHASE4_VISUAL_SUMMARY.txt](./PHASE4_VISUAL_SUMMARY.txt) | Résumé visuel ASCII |
| [PHASE4_VERIFICATION_CHECKLIST.md](./PHASE4_VERIFICATION_CHECKLIST.md) | Checklist de vérification |

### Code Source

| Fichier | Description |
|---------|-------------|
| `backend/api/finance.py` | Endpoints API |
| `core/bank_import/categorizer.py` | Moteur de catégorisation |
| `tests/test_categorization_feedback.py` | Tests unitaires |
| `frontend/src/examples/CategorizationFeedbackExample.jsx` | Composants React |

---

## 🔄 Amélioration Continue

### Workflow Hebdomadaire

#### Lundi: Analyse
```bash
# Générer le rapport
python scripts/analyze_categorization_performance.py --format all
```

#### Mardi-Mercredi: Création de Règles
```sql
-- Identifier les patterns
SELECT * FROM finance_categorization_feedback
WHERE ...;

-- Créer une règle
INSERT INTO finance_rules (name, category_id, keywords)
VALUES ('Nouvelle règle', 8, ARRAY['keyword1', 'keyword2']);
```

#### Jeudi: Test
```python
# Tester la nouvelle règle
categorizer = TransactionCategorizer(load_db_rules=True)
result = categorizer.categorize(test_transaction)
```

#### Vendredi: Mesure
```bash
# Comparer les performances
python scripts/analyze_categorization_performance.py
```

**Guide complet:** [CATEGORIZATION_CONTINUOUS_IMPROVEMENT.md](./docs/CATEGORIZATION_CONTINUOUS_IMPROVEMENT.md)

---

## 🔮 Roadmap ML

### Phase 4 (Actuelle) ✓ COMPLÉTÉ

- ✓ Stockage du feedback
- ✓ API endpoints
- ✓ Stats & analytics
- ✓ Pas de ML actif (juste collecte)

### Phase 5 (Futur) - Analyse des Patterns

**Déclencheur:** 500+ corrections collectées

**Actions:**
- Identifier patterns récurrents
- Créer règles automatiques
- Suggestions intelligentes

**Durée:** 1-2 mois

### Phase 6 (Futur) - ML Simple

**Déclencheur:** 1000+ corrections collectées

**Actions:**
- Naive Bayes classifier
- TF-IDF features
- Validation croisée

**Objectif:** 90% de précision

**Durée:** 2-3 mois

### Phase 7 (Futur) - ML Avancé

**Déclencheur:** 2000+ corrections collectées

**Actions:**
- BERT embeddings
- Neural networks
- Active learning

**Objectif:** 95% de précision

**Durée:** 3-6 mois

---

## 📊 Métriques et KPIs

### Métriques Collectées

- **Total corrections** - Nombre de corrections
- **Précision** - % de prédictions correctes
- **Confiance moyenne** - Score moyen des erreurs
- **Taux de correction** - % de transactions corrigées

### Dashboard

```bash
# Voir toutes les métriques
python scripts/analyze_categorization_performance.py --format text

# Export pour BI tools
python scripts/analyze_categorization_performance.py --format json
```

### Objectifs

| KPI | 1 mois | 3 mois | 6 mois |
|-----|--------|--------|--------|
| Corrections | 100+ | 500+ | 2000+ |
| Précision | 70% | 85% | 90% |
| Règles créées | 3-5 | 10+ | 20+ |
| Réduction corrections | - | -20% | -40% |

---

## 🛠️ Scripts Utiles

### Migration

```bash
# Appliquer la migration
bash scripts/apply_categorization_feedback_migration.sh
```

### Analyse

```bash
# Rapport texte
python scripts/analyze_categorization_performance.py

# Rapport JSON
python scripts/analyze_categorization_performance.py --format json

# Graphiques
python scripts/analyze_categorization_performance.py --plot --days 30

# CSV pour Excel
python scripts/analyze_categorization_performance.py --format csv
```

### Tests

```bash
# Tests unitaires
pytest tests/test_categorization_feedback.py -v

# Tests d'un module spécifique
pytest tests/test_categorization_feedback.py::TestTransactionCategorizer -v
```

---

## 🐛 Troubleshooting

### Problème: Table n'existe pas

```bash
# Vérifier
psql -U postgres -d inventaire -c "\dt finance_categorization_feedback"

# Appliquer migration
bash scripts/apply_categorization_feedback_migration.sh
```

### Problème: Endpoint 404

```bash
# Vérifier que le backend a redémarré
docker-compose restart backend

# Vérifier les logs
docker-compose logs backend | grep categorization
```

### Problème: Import échoue

```python
# Vérifier PYTHONPATH
import sys
print(sys.path)

# Ajouter au path si nécessaire
sys.path.insert(0, '/home/ruuuzer/Documents/monprojet')
```

**Guide complet:** [Troubleshooting Section](./QUICK_START_CATEGORIZATION_FEEDBACK.md#troubleshooting)

---

## 👥 Contribution

### Structure du Code

```
/home/ruuuzer/Documents/monprojet/
├── backend/api/finance.py          # API endpoints
├── core/bank_import/
│   └── categorizer.py              # Moteur de catégorisation
├── db/migrations/
│   └── 008_categorization_feedback.sql  # Migration
├── frontend/src/examples/
│   └── CategorizationFeedbackExample.jsx  # Composants React
├── scripts/
│   ├── apply_categorization_feedback_migration.sh
│   └── analyze_categorization_performance.py
├── tests/
│   └── test_categorization_feedback.py
└── docs/
    ├── CATEGORIZATION_FEEDBACK_SYSTEM.md
    └── CATEGORIZATION_CONTINUOUS_IMPROVEMENT.md
```

### Tests

```bash
# Ajouter un nouveau test
# Éditer: tests/test_categorization_feedback.py

# Lancer les tests
pytest tests/test_categorization_feedback.py -v
```

---

## 📞 Support

### Documentation

- **Guide système:** [CATEGORIZATION_FEEDBACK_SYSTEM.md](./docs/CATEGORIZATION_FEEDBACK_SYSTEM.md)
- **Quick start:** [QUICK_START_CATEGORIZATION_FEEDBACK.md](./QUICK_START_CATEGORIZATION_FEEDBACK.md)
- **Amélioration:** [CATEGORIZATION_CONTINUOUS_IMPROVEMENT.md](./docs/CATEGORIZATION_CONTINUOUS_IMPROVEMENT.md)

### Tests

```bash
pytest tests/test_categorization_feedback.py -v
```

### Logs

```bash
# Backend
docker-compose logs backend | grep categorization

# Database
psql -U postgres -d inventaire -c "SELECT * FROM finance_categorization_feedback LIMIT 5;"
```

---

## 🎉 Conclusion

La Phase 4 - Système de Catégorisation avec Feedback Loop est **complète et opérationnelle**.

### Ce qui a été livré

✓ Table de feedback SQL
✓ Moteur de catégorisation amélioré
✓ API REST complète (3 endpoints)
✓ Composants React prêts
✓ Scripts d'analyse
✓ Documentation extensive
✓ Tests complets
✓ Guide d'amélioration continue

### Prochaines Étapes

1. **Déployer en production**
2. **Intégrer les composants frontend**
3. **Former les utilisateurs**
4. **Collecter des données (objectif: 500+ corrections)**
5. **Analyser et créer des règles**
6. **Planifier Phase 5 (ML)**

---

**Date de création:** 2025-12-19
**Auteur:** Claude Opus 4.5
**Version:** 1.0
**Status:** ✓ READY FOR PRODUCTION

---

*Pour toute question ou suggestion, consultez la documentation ou créez une issue.*
