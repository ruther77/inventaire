# Guide d'Amélioration Continue - Catégorisation Automatique

Ce guide explique comment utiliser le système de feedback pour améliorer progressivement la précision de la catégorisation automatique.

## Table des Matières

1. [Workflow Hebdomadaire](#workflow-hebdomadaire)
2. [Identifier les Opportunités d'Amélioration](#identifier-les-opportunités-damélioration)
3. [Créer des Règles Efficaces](#créer-des-règles-efficaces)
4. [Mesurer le Succès](#mesurer-le-succès)
5. [Planification ML](#planification-ml)

---

## Workflow Hebdomadaire

### Lundi: Collecte et Analyse

```bash
# 1. Générer le rapport hebdomadaire
cd /home/ruuuzer/Documents/monprojet
python scripts/analyze_categorization_performance.py --format all --plot

# 2. Consulter les statistiques
curl http://localhost:8000/api/finance/categorization/feedback/stats

# 3. Voir les corrections communes
curl http://localhost:8000/api/finance/categorization/feedback/common-corrections?limit=20
```

**Questions à se poser:**
- Combien de corrections ont été faites cette semaine?
- Quelle est la confiance moyenne des erreurs?
- Quels sont les patterns qui reviennent le plus?

### Mardi-Mercredi: Création de Règles

#### Étape 1: Identifier les Patterns

```python
from core.bank_import.categorizer import get_common_corrections

# Obtenir les 10 corrections les plus fréquentes
corrections = get_common_corrections(limit=10)

for c in corrections:
    if c['correction_count'] >= 5:  # Au moins 5 occurrences
        print(f"Pattern trouvé: {c['predicted_name']} → {c['actual_name']}")
        print(f"  Occurrences: {c['correction_count']}")
        print(f"  Confiance: {c['avg_confidence']:.1%}")
        print()
```

#### Étape 2: Analyser les Transactions Concernées

```sql
-- Trouver les transactions concernées par un pattern
SELECT
    ft.id,
    ft.libelle,
    ft.montant,
    fc_pred.name as categorie_predite,
    fc_actual.name as categorie_correcte
FROM finance_categorization_feedback cf
JOIN finance_transactions ft ON ft.id = cf.transaction_id
LEFT JOIN finance_categories fc_pred ON fc_pred.id = cf.predicted_category_id
JOIN finance_categories fc_actual ON fc_actual.id = cf.actual_category_id
WHERE fc_pred.code = 'alimentation'
  AND fc_actual.code = 'fournitures'
ORDER BY cf.created_at DESC
LIMIT 20;
```

#### Étape 3: Extraire les Mots-Clés Communs

```python
# Exemple d'extraction de mots-clés
transactions = [
    "FOURNITURE PAPIER A4",
    "FOURNITURE BUREAU STAPLES",
    "FOURNITURE ENCRE IMPRIMANTE",
]

# Mots communs: FOURNITURE, PAPIER, BUREAU, IMPRIMANTE
keywords = ['fourniture', 'papier', 'bureau', 'imprimante', 'encre']
```

#### Étape 4: Créer la Règle

```sql
-- Créer une nouvelle règle de catégorisation
INSERT INTO finance_rules (
    name,
    category_id,
    keywords,
    is_active,
    priority,
    created_at
) VALUES (
    'Fournitures de bureau',
    (SELECT id FROM finance_categories WHERE code = 'fournitures'),
    ARRAY['fourniture', 'papier', 'bureau', 'imprimante', 'encre'],
    true,
    100,  -- Priorité moyenne
    NOW()
);
```

### Jeudi: Test et Validation

#### Tester la Nouvelle Règle

```python
from core.bank_import.categorizer import TransactionCategorizer
from core.bank_import.models import ParsedTransaction, TransactionDirection
from datetime import date
from decimal import Decimal

# Créer un nouveau categorizer (recharge les règles DB)
categorizer = TransactionCategorizer(load_db_rules=True)

# Tester avec des exemples
test_cases = [
    "FOURNITURE PAPIER A4",
    "FOURNITURE BUREAU STAPLES",
    "FOURNITURE ENCRE HP",
]

for libelle in test_cases:
    txn = ParsedTransaction(
        date_operation=date.today(),
        date_valeur=date.today(),
        libelle=libelle,
        montant=Decimal("50.00"),
        direction=TransactionDirection.OUT,
    )

    result = categorizer.categorize(txn)
    print(f"{libelle}")
    print(f"  → {result.category_name} (conf: {result.confidence:.1%})")
    print(f"  Rule ID: {result.rule_id}")
    print()
```

#### Valider sur l'Historique

```sql
-- Appliquer la nouvelle règle sur l'historique
UPDATE finance_transactions
SET
    category_id = (SELECT id FROM finance_categories WHERE code = 'fournitures'),
    updated_at = NOW()
WHERE
    libelle ILIKE '%fourniture%'
    AND category_id = (SELECT id FROM finance_categories WHERE code = 'alimentation')
    AND updated_at > NOW() - INTERVAL '30 days';

-- Enregistrer le feedback en masse
INSERT INTO finance_categorization_feedback (
    transaction_id,
    predicted_category_id,
    actual_category_id,
    confidence_score,
    correction_source
)
SELECT
    id,
    (SELECT id FROM finance_categories WHERE code = 'alimentation'),
    (SELECT id FROM finance_categories WHERE code = 'fournitures'),
    0.75,
    'rule'
FROM finance_transactions
WHERE
    libelle ILIKE '%fourniture%'
    AND category_id = (SELECT id FROM finance_categories WHERE code = 'fournitures')
    AND updated_at = (SELECT MAX(updated_at) FROM finance_transactions);
```

### Vendredi: Mesure et Documentation

```bash
# Générer un nouveau rapport
python scripts/analyze_categorization_performance.py --format all

# Comparer avec le rapport du lundi
# Vérifier l'amélioration de la précision
```

**Métriques à suivre:**
- Baisse du taux d'erreur
- Augmentation de la précision
- Réduction des corrections manuelles pour ce pattern

---

## Identifier les Opportunités d'Amélioration

### 1. Catégories avec Fort Taux d'Erreur

```sql
-- Top 10 catégories les plus corrigées
SELECT
    fc.code,
    fc.name,
    COUNT(*) as corrections,
    AVG(cf.confidence_score) as avg_confidence
FROM finance_categorization_feedback cf
JOIN finance_categories fc ON fc.id = cf.predicted_category_id
GROUP BY fc.code, fc.name
ORDER BY COUNT(*) DESC
LIMIT 10;
```

**Action:** Créer des règles spécifiques pour ces catégories.

### 2. Patterns de Confusion

```sql
-- Trouver les paires de catégories souvent confondues
SELECT
    fc_pred.name as predite,
    fc_actual.name as correcte,
    COUNT(*) as count
FROM finance_categorization_feedback cf
JOIN finance_categories fc_pred ON fc_pred.id = cf.predicted_category_id
JOIN finance_categories fc_actual ON fc_actual.id = cf.actual_category_id
GROUP BY fc_pred.name, fc_actual.name
ORDER BY COUNT(*) DESC
LIMIT 20;
```

**Action:** Affiner les mots-clés pour éviter la confusion.

### 3. Transactions avec Faible Confiance

```sql
-- Transactions catégorisées avec faible confiance
SELECT
    id,
    libelle,
    montant,
    category_id,
    category_confidence
FROM finance_transactions
WHERE
    category_confidence < 0.7
    AND category_id IS NOT NULL
ORDER BY category_confidence ASC
LIMIT 50;
```

**Action:** Vérifier manuellement et créer des règles si nécessaire.

---

## Créer des Règles Efficaces

### Principes de Base

#### 1. Soyez Spécifique

**❌ Mauvais:**
```sql
keywords: ARRAY['restaurant']  -- Trop général
```

**✓ Bon:**
```sql
keywords: ARRAY['restaurant', 'bistrot', 'brasserie', 'cafeteria']
```

#### 2. Utilisez des Regex pour les Patterns Complexes

**Exemple:** Numéros de facture

```sql
INSERT INTO finance_rules (name, category_id, regex_pattern)
VALUES (
    'Factures fournisseur',
    (SELECT id FROM finance_categories WHERE code = 'fournitures'),
    'FACTURE?\s+N°?\s*\d{4,}'  -- FACTURE N°1234, FACT 5678, etc.
);
```

#### 3. Testez avant de Déployer

```python
import re

# Tester votre regex
pattern = r'FACTURE?\s+N°?\s*\d{4,}'
test_cases = [
    "FACTURE N°1234",
    "FACT 5678",
    "FACTURE 9012",
]

for test in test_cases:
    match = re.search(pattern, test, re.IGNORECASE)
    print(f"{test}: {'✓' if match else '✗'}")
```

#### 4. Utilisez les Priorités

```sql
-- Règle spécifique (haute priorité)
INSERT INTO finance_rules (name, keywords, priority)
VALUES ('Restaurant équipe', ARRAY['restaurant', 'equipe'], 200);

-- Règle générale (basse priorité)
INSERT INTO finance_rules (name, keywords, priority)
VALUES ('Restaurant', ARRAY['restaurant'], 100);
```

### Templates de Règles Courantes

#### Template 1: Fournisseur Spécifique

```sql
INSERT INTO finance_rules (name, category_id, keywords)
VALUES (
    'Fournisseur: METRO',
    (SELECT id FROM finance_categories WHERE code = 'alimentation'),
    ARRAY['metro', 'metro cash']
);
```

#### Template 2: Type de Dépense

```sql
INSERT INTO finance_rules (name, category_id, keywords)
VALUES (
    'Frais bancaires',
    (SELECT id FROM finance_categories WHERE code = 'frais_bancaires'),
    ARRAY['commission', 'frais', 'cotisation', 'agios']
);
```

#### Template 3: Pattern de Libellé

```sql
INSERT INTO finance_rules (name, category_id, regex_pattern)
VALUES (
    'Virements salaires',
    (SELECT id FROM finance_categories WHERE code = 'salaires'),
    'VIR(EMENT)?\s+SALAIRE'
);
```

---

## Mesurer le Succès

### KPIs à Suivre

#### 1. Taux de Précision

```python
from scripts.analyze_categorization_performance import calculate_accuracy_metrics

metrics = calculate_accuracy_metrics()
print(f"Précision: {metrics['accuracy']:.2%}")
print(f"Taux d'erreur: {metrics['error_rate']:.2%}")
```

**Objectif:** > 85% de précision après 3 mois

#### 2. Réduction des Corrections Manuelles

```sql
-- Comparer les corrections manuelles mois par mois
SELECT
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as corrections
FROM finance_categorization_feedback
WHERE correction_source = 'manual'
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC;
```

**Objectif:** -20% de corrections manuelles par mois

#### 3. Confiance Moyenne

```sql
-- Évolution de la confiance moyenne
SELECT
    DATE_TRUNC('week', created_at) as week,
    AVG(confidence_score) as avg_confidence
FROM finance_categorization_feedback
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week DESC;
```

**Objectif:** Confiance moyenne > 0.80

#### 4. Couverture des Règles

```sql
-- Pourcentage de transactions catégorisées par règles DB
SELECT
    COUNT(CASE WHEN category_source = 'db_rule' THEN 1 END) * 100.0 / COUNT(*) as rule_coverage
FROM finance_transactions
WHERE category_id IS NOT NULL;
```

**Objectif:** > 60% des catégories via règles DB

---

## Planification ML

### Phase 1: Collecte de Données (Actuel)

**Objectif:** 500+ corrections
**Durée:** 2-3 mois
**Actions:**
- Utiliser le système normalement
- Encourager les corrections
- Analyser les patterns

### Phase 2: ML Simple (Futur)

**Déclencheur:** 500+ corrections collectées

**Algorithme:** Naive Bayes ou Logistic Regression

```python
# Pseudo-code pour Phase 2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# 1. Charger les données de feedback
feedback_data = load_feedback_data()

# 2. Préparer les features
vectorizer = TfidfVectorizer(max_features=1000)
X = vectorizer.fit_transform(feedback_data['libelle'])
y = feedback_data['actual_category_id']

# 3. Entraîner le modèle
model = MultinomialNB()
model.fit(X, y)

# 4. Évaluer
from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5)
print(f"Accuracy: {scores.mean():.2%}")

# 5. Utiliser pour prédire
new_libelle = "RESTAURANT LE BISTROT"
X_new = vectorizer.transform([new_libelle])
prediction = model.predict(X_new)
```

### Phase 3: ML Avancé (Futur)

**Déclencheur:** 2000+ corrections collectées

**Algorithme:** BERT embeddings + Neural Network

```python
# Pseudo-code pour Phase 3
from transformers import BertTokenizer, BertModel
import torch

# 1. Utiliser BERT pour les embeddings
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
bert_model = BertModel.from_pretrained('bert-base-uncased')

# 2. Créer les embeddings
def get_embedding(text):
    inputs = tokenizer(text, return_tensors='pt')
    outputs = bert_model(**inputs)
    return outputs.last_hidden_state.mean(dim=1)

# 3. Entraîner un classifieur
# ... (Neural network avec PyTorch ou TensorFlow)
```

### Critères de Succès pour Passer au ML

- ✓ Au moins 500 corrections collectées
- ✓ Taux de correction stable (pas d'augmentation)
- ✓ Patterns récurrents identifiés
- ✓ Règles DB couvrent 60%+ des cas
- ✓ Confiance moyenne > 0.75

---

## Checklist Mensuelle

### Début du Mois

- [ ] Générer le rapport mensuel
- [ ] Analyser les métriques de performance
- [ ] Identifier les 5 patterns les plus fréquents
- [ ] Planifier les règles à créer

### Mi-Mois

- [ ] Créer 3-5 nouvelles règles
- [ ] Tester les règles sur l'historique
- [ ] Valider avec l'équipe
- [ ] Déployer les règles en production

### Fin de Mois

- [ ] Mesurer l'impact des nouvelles règles
- [ ] Documenter les changements
- [ ] Partager les résultats avec l'équipe
- [ ] Planifier les améliorations pour le mois suivant

---

## Ressources

- **Script d'analyse:** `scripts/analyze_categorization_performance.py`
- **Documentation système:** `docs/CATEGORIZATION_FEEDBACK_SYSTEM.md`
- **Quick start:** `QUICK_START_CATEGORIZATION_FEEDBACK.md`
- **Résumé Phase 4:** `PHASE4_CATEGORISATION_SUMMARY.md`

---

**Date de création:** 2025-12-19
**Version:** 1.0
**Auteur:** Claude Opus 4.5
