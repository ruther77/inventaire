# Changelog - Module Calculation

## [2025-12-21] - Ajout du module inventory_utils

### Ajouté

#### Nouveau fichier: `inventory_utils.py` (257 lignes)
Fonctions de gestion d'inventaire pour optimiser les stocks et marges:

1. **`calculate_pamp(purchases: List[dict]) -> Decimal`**
   - Calcul du Prix d'Achat Moyen Pondéré
   - Valorisation précise du stock
   - Support de multiples achats à prix différents
   - Précision décimale pour calculs financiers

2. **`calculate_eoq(annual_demand: float, order_cost: float, holding_cost: float) -> float`**
   - Quantité Économique de Commande (formule de Wilson)
   - Optimisation des coûts de commande et de stockage
   - Détermine la quantité optimale à commander

3. **`calculate_safety_stock(avg_demand: float, demand_std: float, lead_time: float, service_level: float = 0.95) -> float`**
   - Calcul du stock de sécurité
   - Protection contre les ruptures de stock
   - Utilise la distribution normale (Z-score)
   - Niveau de service configurable (défaut: 95%)

4. **`calculate_reorder_point(avg_demand: float, lead_time: float, safety_stock: float) -> float`**
   - Point de réapprovisionnement optimal
   - Intègre la demande durant le lead time
   - Inclut le stock de sécurité

5. **`calculate_margin(revenue: Decimal, cost: Decimal) -> dict`**
   - Calcul de marge brute (montant et pourcentage)
   - Retourne `{'margin_amount': Decimal, 'margin_percent': Decimal}`
   - Support des marges négatives (pertes)

#### Nouveau fichier: `test_inventory_utils.py` (181 lignes)
Suite de tests complète:
- Tests unitaires pour chaque fonction
- Tests de cas limites et validation d'erreurs
- Vérification des calculs mathématiques
- 6 fonctions de test + validation complète

#### Nouveau fichier: `example_usage.py` (292 lignes)
Exemples pratiques d'utilisation:
- Exemple complet sur un produit (Huile d'olive)
- Comparaison de 3 scénarios (rotation rapide/standard/lente)
- Analyse de marges multi-produits
- Workflow complet de gestion d'inventaire

#### Nouveau fichier: `INVENTORY_UTILS_README.md`
Documentation complète du module:
- Description détaillée de chaque fonction
- Explications mathématiques des formules
- Exemples d'utilisation pour chaque fonction
- Cas d'usage et recommandations
- Section troubleshooting

### Modifié

#### `__init__.py`
- Ajout de l'import des 5 nouvelles fonctions
- Mise à jour de `__all__` pour exporter les fonctions
- Organisation par catégories (Tax utilities / Inventory utilities)
- Documentation du module mise à jour

### Références

Code inspiré de:
- `/home/ruuuzer/Documents/monprojet/core/finance/margin_calculator.py`
  - Méthode de calcul PAMP
  - Structure des calculs de marge

- `/home/ruuuzer/Documents/monprojet/backend/api/inventory_intelligence.py`
  - Formules EOQ et Safety Stock
  - Implémentation des calculs probabilistes

### Détails techniques

**Dépendances ajoutées:**
- `decimal.Decimal` pour précision financière
- `statistics.NormalDist` pour calculs de Z-score
- `math.sqrt` pour EOQ
- `typing` pour type hints

**Standards appliqués:**
- Docstrings format Google
- Type hints sur tous les paramètres
- Validation stricte des entrées
- Gestion d'erreurs avec `ValueError`
- Précision décimale (2 décimales pour montants)

**Formules mathématiques implémentées:**
```
PAMP = Σ(Quantité × Prix) / Σ(Quantité)

EOQ = √((2 × D × S) / H)
  où D = demande annuelle, S = coût commande, H = coût possession

Safety Stock = Z × σd × √LT
  où Z = Z-score, σd = écart-type demande, LT = lead time

Reorder Point = (Demande moyenne × Lead time) + Safety Stock

Marge % = ((Revenue - Cost) / Revenue) × 100
```

### Validation

- ✅ Compilation Python réussie
- ✅ Imports fonctionnels
- ✅ Exports du module vérifiés
- ✅ Type hints valides
- ✅ Docstrings conformes

### Statistiques

- **Fichiers créés:** 4
- **Fichiers modifiés:** 1
- **Lignes de code:** ~730 lignes (code + tests + exemples)
- **Fonctions:** 5
- **Tests:** 6 fonctions de test

### Migration

Pas d'impact sur le code existant. Les fonctions sont additives uniquement.

Pour utiliser les nouvelles fonctions:
```python
from calculation import (
    calculate_pamp,
    calculate_eoq,
    calculate_safety_stock,
    calculate_reorder_point,
    calculate_margin
)
```

### Notes

Les fonctions peuvent être utilisées indépendamment ou ensemble dans un workflow complet de gestion d'inventaire (voir `example_usage.py`).

---

## Historique antérieur

### [Avant 2025-12-21]

Module `tax_utils.py` existant avec:
- `infer_tva()`
- `calculate_ht_from_ttc()`
- `calculate_ttc_from_ht()`
- `calculate_tva_amount()`
- `infer_category()`
- `categorize_product()`
