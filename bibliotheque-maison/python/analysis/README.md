# Module Analysis - Classification ABC/XYZ

Module d'analyse pour la gestion d'inventaire avec classification ABC/XYZ selon la méthode Pareto.

## Installation

Le module est standalone et ne nécessite que Python 3.8+. NumPy est optionnel mais recommandé pour de meilleures performances.

```bash
# Optionnel mais recommandé
pip install numpy
```

## Fonctionnalités

### 1. Calcul du Coefficient de Variation

```python
from analysis import calculate_coefficient_variation

# Demande quotidienne sur 7 jours
demandes = [100, 105, 98, 102, 100, 103, 99]
cv = calculate_coefficient_variation(demandes)
print(f"CV = {cv:.3f}")  # CV = 0.024 (très stable)
```

### 2. Classification ABC (Pareto)

Classifie les items selon leur contribution à la valeur totale:
- **Classe A**: Items contribuant aux premiers 80% de la valeur (critiques)
- **Classe B**: Items contribuant de 80% à 95% (moyens)
- **Classe C**: Items contribuant aux derniers 5% (faibles)

```python
from analysis import classify_abc

produits = [
    {'sku': 'PROD-001', 'value': 15000},
    {'sku': 'PROD-002', 'value': 12000},
    {'sku': 'PROD-003', 'value': 8000},
    {'sku': 'PROD-004', 'value': 5000},
    {'sku': 'PROD-005', 'value': 3000},
]

result = classify_abc(produits, value_key='value')

# result = {
#     'A': [{'sku': 'PROD-001', ...}, {'sku': 'PROD-002', ...}],
#     'B': [...],
#     'C': [...]
# }
```

### 3. Classification XYZ (Variabilité)

Classifie les items selon la variabilité de leur demande:
- **Classe X**: Demande stable (CV < 0.5)
- **Classe Y**: Demande variable (0.5 ≤ CV < 1.0)
- **Classe Z**: Demande très variable (CV ≥ 1.0)

```python
from analysis import classify_xyz

produits = [
    {'sku': 'PROD-001', 'cv': 0.15},   # Stable
    {'sku': 'PROD-002', 'cv': 0.60},   # Variable
    {'sku': 'PROD-003', 'cv': 1.20},   # Très variable
]

result = classify_xyz(produits, cv_key='cv')

# result = {
#     'X': [{'sku': 'PROD-001', ...}],
#     'Y': [{'sku': 'PROD-002', ...}],
#     'Z': [{'sku': 'PROD-003', ...}]
# }
```

### 4. Classification ABC-XYZ Combinée

Combine les deux classifications pour obtenir 9 catégories:

| | X (Stable) | Y (Variable) | Z (Erratique) |
|---|---|---|---|
| **A (Critique)** | AX | AY | AZ |
| **B (Moyen)** | BX | BY | BZ |
| **C (Faible)** | CX | CY | CZ |

```python
from analysis import classify_abc_xyz

produits = [
    {'sku': 'PROD-001', 'value': 15000, 'cv': 0.15},  # AX
    {'sku': 'PROD-002', 'value': 12000, 'cv': 0.60},  # AY
    {'sku': 'PROD-003', 'value': 8000, 'cv': 1.20},   # AZ
    # ...
]

result = classify_abc_xyz(produits, value_key='value', cv_key='cv')

# result = {
#     'AX': [...], 'AY': [...], 'AZ': [...],
#     'BX': [...], 'BY': [...], 'BZ': [...],
#     'CX': [...], 'CY': [...], 'CZ': [...]
# }
```

## Recommandations de Gestion

### Catégories Critiques (A)
- **AX**: Items critiques à demande stable
  - Gestion simple, stock de sécurité important
  - Réapprovisionnement régulier et planifié

- **AY**: Items critiques à demande variable
  - Surveillance régulière et prévisions fines
  - Ajustements fréquents des paramètres

- **AZ**: Items critiques à demande erratique
  - Analyse détaillée au cas par cas
  - Stock de sécurité important ou relation fournisseur privilégiée

### Catégories Moyennes (B)
- **BX**: Gestion standard, réapprovisionnement régulier
- **BY**: Revue périodique, ajustements selon tendances
- **BZ**: Gestion réactive, stock minimal avec suivi

### Catégories Faibles (C)
- **CX**: Stock minimum, commandes espacées
- **CY**: Approvisionnement sur demande
- **CZ**: Stock minimal ou approvisionnement uniquement sur commande

## Workflow Complet

```python
from analysis import (
    calculate_coefficient_variation,
    classify_abc_xyz
)

# 1. Calculer le CV à partir des demandes historiques
demandes_historiques = {
    'PROD-001': [100, 105, 98, 102, 100],
    'PROD-002': [50, 150, 80, 120, 100],
}

produits = []
for sku, demandes in demandes_historiques.items():
    cv = calculate_coefficient_variation(demandes)
    valeur = sum(demandes) * prix_unitaire

    produits.append({
        'sku': sku,
        'value': valeur,
        'cv': cv
    })

# 2. Classifier
result = classify_abc_xyz(produits, value_key='value', cv_key='cv')

# 3. Analyser et agir
for classe, items in result.items():
    if items:
        print(f"Catégorie {classe}: {len(items)} produits")
        # Appliquer les recommandations selon la classe
```

## Paramètres Personnalisables

### Seuils ABC
```python
# Par défaut: A=80%, B=95%
classify_abc(items, thresholds=(0.8, 0.95))

# Plus restrictif: A=70%, B=90%
classify_abc(items, thresholds=(0.7, 0.9))
```

### Seuils XYZ
```python
# Par défaut: X<0.5, Y<1.0
classify_xyz(items, thresholds=(0.5, 1.0))

# Plus strict pour X: X<0.25, Y<0.75
classify_xyz(items, thresholds=(0.25, 0.75))
```

### Clés Personnalisées
```python
# Utiliser d'autres noms de clés
classify_abc(items, value_key='annual_consumption')
classify_xyz(items, cv_key='variability_coefficient')
```

## Tests

```bash
# Exécuter les tests
python3 -m pytest tests/test_analysis_classification.py -v

# Avec couverture
python3 -m pytest tests/test_analysis_classification.py --cov=analysis
```

## Exemples

Voir le fichier `example_usage.py` pour des exemples complets d'utilisation.

```bash
# Exécuter les exemples (depuis le répertoire python)
PYTHONPATH=. python3 analysis/example_usage.py
```

## Performance

- **Sans NumPy**: Utilise des calculs Python purs (plus lent mais compatible partout)
- **Avec NumPy**: Utilise des opérations vectorisées (recommandé pour > 1000 items)

Le module détecte automatiquement la présence de NumPy et utilise l'implémentation optimale.

## API Reference

### `calculate_coefficient_variation(values: List[float]) -> float`

Calcule le coefficient de variation (écart-type / moyenne).

**Paramètres:**
- `values`: Liste de valeurs numériques

**Retourne:**
- Coefficient de variation (float)
- `float('inf')` si la moyenne est ≤ 0

**Lève:**
- `ValueError`: Si la liste est vide

---

### `classify_abc(items: List[dict], value_key: str = 'value', thresholds: tuple = (0.8, 0.95)) -> Dict[str, List[dict]]`

Classification ABC selon la valeur cumulative.

**Paramètres:**
- `items`: Liste de dictionnaires
- `value_key`: Nom de la clé contenant la valeur
- `thresholds`: Tuple (seuil_A, seuil_B) en décimal

**Retourne:**
- Dictionnaire avec clés 'A', 'B', 'C'
- Chaque item enrichi avec 'abc_class', 'share', 'cumul'

---

### `classify_xyz(items: List[dict], cv_key: str = 'cv', thresholds: tuple = (0.5, 1.0)) -> Dict[str, List[dict]]`

Classification XYZ selon la variabilité.

**Paramètres:**
- `items`: Liste de dictionnaires
- `cv_key`: Nom de la clé contenant le CV
- `thresholds`: Tuple (seuil_X, seuil_Y)

**Retourne:**
- Dictionnaire avec clés 'X', 'Y', 'Z'
- Chaque item enrichi avec 'xyz_class'

---

### `classify_abc_xyz(items: List[dict], value_key: str = 'value', cv_key: str = 'cv', ...) -> Dict[str, List[dict]]`

Classification combinée ABC-XYZ.

**Paramètres:**
- `items`: Liste de dictionnaires
- `value_key`: Clé de la valeur (ABC)
- `cv_key`: Clé du CV (XYZ)
- `abc_thresholds`: Seuils ABC (défaut: 0.8, 0.95)
- `xyz_thresholds`: Seuils XYZ (défaut: 0.5, 1.0)

**Retourne:**
- Dictionnaire avec 9 clés (AX, AY, AZ, BX, BY, BZ, CX, CY, CZ)
- Chaque item enrichi avec 'abc_class', 'xyz_class', 'abc_xyz_class'

## Licence

Partie de la bibliothèque maison. Utilisation libre.

## Auteur

Basé sur `/home/ruuuzer/Documents/monprojet/core/inventory_classification.py`
Adapté en module standalone.
