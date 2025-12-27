# Module inventory_utils - Documentation

## Vue d'ensemble

Le module `inventory_utils.py` fournit des fonctions essentielles pour la gestion d'inventaire et les calculs financiers. Il a été développé en s'inspirant des bonnes pratiques de :
- `/home/ruuuzer/Documents/monprojet/core/finance/margin_calculator.py`
- `/home/ruuuzer/Documents/monprojet/backend/api/inventory_intelligence.py`

## Fonctions disponibles

### 1. `calculate_pamp(purchases: List[dict]) -> Decimal`

**Prix d'Achat Moyen Pondéré (PAMP)**

Calcule le coût moyen pondéré des achats pour valoriser le stock de manière précise.

**Paramètres:**
- `purchases`: Liste de dictionnaires avec `quantity` et `unit_price`

**Retour:**
- Prix d'achat moyen pondéré (Decimal avec 2 décimales)

**Exemple:**
```python
from calculation import calculate_pamp

purchases = [
    {'quantity': 10, 'unit_price': 5.00},
    {'quantity': 20, 'unit_price': 6.00},
    {'quantity': 15, 'unit_price': 5.50}
]

pamp = calculate_pamp(purchases)
# Résultat: Decimal('5.67')
# Calcul: (10*5 + 20*6 + 15*5.5) / (10+20+15) = 5.67€
```

**Cas d'usage:**
- Valorisation du stock
- Calcul du coût des marchandises vendues (COGS)
- Analyse de rentabilité

---

### 2. `calculate_eoq(annual_demand: float, order_cost: float, holding_cost: float) -> float`

**Economic Order Quantity (Quantité Économique de Commande)**

Détermine la quantité optimale à commander pour minimiser les coûts totaux (commande + stockage).

**Formule de Wilson:**
```
EOQ = √((2 × D × S) / H)
```

**Paramètres:**
- `annual_demand`: Demande annuelle en unités
- `order_cost`: Coût fixe par commande (€)
- `holding_cost`: Coût de possession par unité par an (€)

**Retour:**
- Quantité économique de commande (float, arrondi)

**Exemple:**
```python
from calculation import calculate_eoq

eoq = calculate_eoq(
    annual_demand=1200,  # 1200 unités/an
    order_cost=50,       # 50€ par commande
    holding_cost=2       # 2€/unité/an
)
# Résultat: 245.0 unités
```

**Interprétation:**
- Commander 245 unités minimise les coûts totaux
- Nombre de commandes/an: 1200 / 245 ≈ 5 commandes

**Cas d'usage:**
- Optimisation des commandes
- Réduction des coûts de gestion de stock
- Planification des approvisionnements

---

### 3. `calculate_safety_stock(avg_demand: float, demand_std: float, lead_time: float, service_level: float = 0.95) -> float`

**Stock de Sécurité**

Calcule le stock tampon nécessaire pour se protéger contre les variations de demande et maintenir le niveau de service client.

**Formule:**
```
SS = Z × σd × √LT
```
où:
- Z = Z-score (loi normale) pour le niveau de service
- σd = Écart-type de la demande quotidienne
- LT = Lead time (délai de livraison)

**Paramètres:**
- `avg_demand`: Demande moyenne quotidienne
- `demand_std`: Écart-type de la demande quotidienne
- `lead_time`: Délai de livraison en jours
- `service_level`: Niveau de service (0-1), par défaut 0.95 (95%)

**Retour:**
- Quantité de stock de sécurité (float, arrondi)

**Exemple:**
```python
from calculation import calculate_safety_stock

safety_stock = calculate_safety_stock(
    avg_demand=50,      # 50 unités/jour en moyenne
    demand_std=10,      # Écart-type de 10 unités
    lead_time=5,        # 5 jours de délai
    service_level=0.95  # 95% de satisfaction
)
# Résultat: ~37 unités
```

**Niveaux de service courants:**
- 90% → Z = 1.28
- 95% → Z = 1.65 (recommandé)
- 99% → Z = 2.33

**Cas d'usage:**
- Éviter les ruptures de stock
- Garantir la disponibilité produit
- Gérer l'incertitude de la demande

---

### 4. `calculate_reorder_point(avg_demand: float, lead_time: float, safety_stock: float) -> float`

**Point de Réapprovisionnement**

Détermine le niveau de stock auquel déclencher une nouvelle commande.

**Formule:**
```
ROP = (Demande moyenne × Lead time) + Stock de sécurité
```

**Paramètres:**
- `avg_demand`: Demande moyenne quotidienne
- `lead_time`: Délai de livraison en jours
- `safety_stock`: Stock de sécurité calculé

**Retour:**
- Point de réapprovisionnement (float, arrondi)

**Exemple:**
```python
from calculation import calculate_safety_stock, calculate_reorder_point

# Calculer d'abord le stock de sécurité
safety_stock = calculate_safety_stock(
    avg_demand=50,
    demand_std=10,
    lead_time=5,
    service_level=0.95
)

# Puis le point de réapprovisionnement
reorder_point = calculate_reorder_point(
    avg_demand=50,      # 50 unités/jour
    lead_time=5,        # 5 jours
    safety_stock=safety_stock  # ~37 unités
)
# Résultat: 287 unités (50×5 + 37)
```

**Interprétation:**
- Quand le stock atteint 287 unités → passer commande
- La commande arrivera avant la rupture de stock

**Cas d'usage:**
- Automatisation des réapprovisionnements
- Alertes de stock bas
- Optimisation de la chaîne d'approvisionnement

---

### 5. `calculate_margin(revenue: Decimal, cost: Decimal) -> dict`

**Calcul de Marge**

Calcule la marge brute en montant et en pourcentage.

**Formule:**
```
Marge (€) = Prix de vente - Coût d'achat
Marge (%) = (Marge / Prix de vente) × 100
```

**Paramètres:**
- `revenue`: Prix de vente HT (Decimal)
- `cost`: Coût d'achat HT (Decimal)

**Retour:**
- Dictionnaire avec `margin_amount` et `margin_percent` (Decimal)

**Exemple:**
```python
from decimal import Decimal
from calculation import calculate_margin

margin = calculate_margin(
    revenue=Decimal('100'),  # 100€ de vente
    cost=Decimal('60')       # 60€ de coût
)
# Résultat: {
#   'margin_amount': Decimal('40.00'),
#   'margin_percent': Decimal('40.00')
# }
```

**Note importante:**
- Ne pas confondre avec le **taux de marque** (basé sur le coût)
- Marge brute = avant charges d'exploitation
- Une marge de 40% signifie que 40% du prix de vente est du bénéfice

**Cas d'usage:**
- Analyse de rentabilité produit
- Fixation des prix de vente
- Reporting financier

---

## Utilisation complète - Workflow d'inventaire

Voici un exemple complet utilisant toutes les fonctions ensemble :

```python
from decimal import Decimal
from calculation import (
    calculate_pamp,
    calculate_eoq,
    calculate_safety_stock,
    calculate_reorder_point,
    calculate_margin
)

# 1. Calculer le PAMP pour valoriser le stock
purchases = [
    {'quantity': 100, 'unit_price': 10.00},
    {'quantity': 150, 'unit_price': 9.50},
    {'quantity': 200, 'unit_price': 9.75}
]
pamp = calculate_pamp(purchases)
print(f"PAMP: {pamp}€")

# 2. Déterminer la quantité économique de commande
eoq = calculate_eoq(
    annual_demand=3650,  # 10 unités/jour × 365 jours
    order_cost=75,       # 75€ par commande
    holding_cost=pamp * 0.25  # 25% du coût unitaire
)
print(f"Quantité à commander: {eoq} unités")

# 3. Calculer le stock de sécurité
safety_stock = calculate_safety_stock(
    avg_demand=10,       # 10 unités/jour
    demand_std=3,        # Variabilité de ±3 unités
    lead_time=7,         # 1 semaine de délai
    service_level=0.95   # 95% de service
)
print(f"Stock de sécurité: {safety_stock} unités")

# 4. Définir le point de réapprovisionnement
reorder_point = calculate_reorder_point(
    avg_demand=10,
    lead_time=7,
    safety_stock=safety_stock
)
print(f"Commander quand stock ≤ {reorder_point} unités")

# 5. Analyser la marge
margin = calculate_margin(
    revenue=Decimal('15.00'),  # Prix de vente
    cost=pamp                   # Coût d'achat (PAMP)
)
print(f"Marge: {margin['margin_amount']}€ ({margin['margin_percent']}%)")
```

---

## Tests

Un fichier de test complet est disponible : `test_inventory_utils.py`

Pour l'exécuter :
```bash
cd /home/ruuuzer/Documents/bibliotheque-maison/python/calculation
python3 test_inventory_utils.py
```

---

## Gestion des erreurs

Toutes les fonctions incluent une validation des paramètres :

```python
# ValueError si liste vide
calculate_pamp([])  # ❌ ValueError

# ValueError si demande négative
calculate_eoq(annual_demand=-100, order_cost=50, holding_cost=2)  # ❌

# ValueError si niveau de service invalide
calculate_safety_stock(avg_demand=10, demand_std=2, lead_time=5, service_level=1.5)  # ❌
```

---

## Références

- **Formule de Wilson (EOQ)**: Wilson, R. H. (1934)
- **Stock de sécurité**: Distribution normale, Z-score
- **PAMP**: Méthode comptable standard (IFRS)
- **Code source**:
  - `/home/ruuuzer/Documents/monprojet/core/finance/margin_calculator.py`
  - `/home/ruuuzer/Documents/monprojet/backend/api/inventory_intelligence.py`

---

## Auteur

Module créé pour le projet bibliotheque-maison

Dernière mise à jour: 2025-12-21
