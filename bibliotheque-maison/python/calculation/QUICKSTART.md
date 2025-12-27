# Quick Start - Module inventory_utils

## Installation

Aucune installation nécessaire ! Le module fait partie de votre bibliothèque.

## Utilisation basique

### 1. Import des fonctions

```python
from calculation import (
    calculate_pamp,
    calculate_eoq,
    calculate_safety_stock,
    calculate_reorder_point,
    calculate_margin
)
```

### 2. Exemple simple - Calcul PAMP

```python
from decimal import Decimal
from calculation import calculate_pamp

# Historique d'achats
achats = [
    {'quantity': 10, 'unit_price': 5.00},
    {'quantity': 20, 'unit_price': 6.00}
]

pamp = calculate_pamp(achats)
print(f"PAMP: {pamp}€")  # Output: PAMP: 5.67€
```

### 3. Exemple - Quantité économique de commande

```python
from calculation import calculate_eoq

eoq = calculate_eoq(
    annual_demand=1200,  # 1200 unités/an
    order_cost=50,       # 50€ par commande
    holding_cost=2       # 2€/unité/an
)
print(f"Commander: {eoq} unités")  # Output: 245.0 unités
```

### 4. Exemple - Stock de sécurité

```python
from calculation import calculate_safety_stock

stock_securite = calculate_safety_stock(
    avg_demand=50,       # 50 unités/jour
    demand_std=10,       # Écart-type 10
    lead_time=5,         # 5 jours
    service_level=0.95   # 95% de service
)
print(f"Stock de sécurité: {stock_securite} unités")
```

### 5. Exemple - Point de réapprovisionnement

```python
from calculation import calculate_reorder_point

point = calculate_reorder_point(
    avg_demand=50,
    lead_time=5,
    safety_stock=37  # Calculé précédemment
)
print(f"Commander quand stock ≤ {point} unités")
```

### 6. Exemple - Calcul de marge

```python
from decimal import Decimal
from calculation import calculate_margin

marge = calculate_margin(
    revenue=Decimal('100'),  # Prix de vente
    cost=Decimal('60')       # Coût d'achat
)
print(f"Marge: {marge['margin_amount']}€ ({marge['margin_percent']}%)")
# Output: Marge: 40.00€ (40.00%)
```

## Workflow complet

```python
from decimal import Decimal
from calculation import *

# 1. Calculer le PAMP
achats = [
    {'quantity': 100, 'unit_price': 8.50},
    {'quantity': 150, 'unit_price': 8.20}
]
pamp = calculate_pamp(achats)

# 2. Déterminer l'EOQ
demande_annuelle = 365 * 15  # 15 unités/jour
eoq = calculate_eoq(
    annual_demand=demande_annuelle,
    order_cost=85,
    holding_cost=float(pamp) * 0.25
)

# 3. Calculer le stock de sécurité
stock_securite = calculate_safety_stock(
    avg_demand=15,
    demand_std=4,
    lead_time=7,
    service_level=0.95
)

# 4. Définir le point de réapprovisionnement
point_reappro = calculate_reorder_point(
    avg_demand=15,
    lead_time=7,
    safety_stock=stock_securite
)

# 5. Analyser la marge
marge = calculate_margin(
    revenue=Decimal('12.90'),
    cost=pamp
)

# Afficher les résultats
print(f"PAMP: {pamp}€")
print(f"Quantité à commander: {eoq} unités")
print(f"Point de réapprovisionnement: {point_reappro} unités")
print(f"Stock de sécurité: {stock_securite} unités")
print(f"Marge: {marge['margin_amount']}€ ({marge['margin_percent']}%)")
```

## Tests

Exécuter les tests:
```bash
cd /home/ruuuzer/Documents/bibliotheque-maison/python/calculation
python3 test_inventory_utils.py
```

## Exemples détaillés

Voir le fichier complet d'exemples:
```bash
python3 example_usage.py
```

## Documentation complète

Consultez `INVENTORY_UTILS_README.md` pour:
- Explications détaillées de chaque fonction
- Formules mathématiques
- Cas d'usage avancés
- Troubleshooting

## Support

En cas de problème, vérifier que:
1. Les paramètres sont du bon type (Decimal pour PAMP et marge)
2. Les valeurs sont positives (pas de demande négative)
3. Le niveau de service est entre 0 et 1 (ex: 0.95 pour 95%)

## Fichiers du module

```
calculation/
├── __init__.py                    # Exports du module
├── inventory_utils.py             # Code principal ⭐
├── tax_utils.py                   # Module existant (taxes)
├── test_inventory_utils.py        # Tests unitaires
├── example_usage.py               # Exemples pratiques
├── INVENTORY_UTILS_README.md      # Documentation complète
├── CHANGELOG.md                   # Historique des modifications
└── QUICKSTART.md                  # Ce fichier
```

## Aide-mémoire des formules

| Fonction | Formule | Utilité |
|----------|---------|---------|
| **PAMP** | Σ(Qté × Prix) / Σ(Qté) | Valorisation du stock |
| **EOQ** | √((2×D×S) / H) | Quantité optimale de commande |
| **Safety Stock** | Z × σd × √LT | Protection contre ruptures |
| **Reorder Point** | (D×LT) + SS | Quand commander |
| **Margin** | (Vente - Coût) / Vente | Rentabilité |

---

**Version:** 1.0
**Date:** 2025-12-21
**Auteur:** bibliotheque-maison
