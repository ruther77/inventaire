# Restaurant Overview & Food Cost - Endpoints Documentation

## Vue d'ensemble

Implémentation des endpoints Backend pour le **Scénario UX 4.7: Restaurant Overview & Food Cost**.

Cette documentation décrit les 9 nouveaux endpoints créés pour la gestion du restaurant, avec calculs de marges, food cost, et analyses avancées.

---

## Architecture

### Fichiers modifiés/créés

1. **`backend/schemas/restaurant.py`** - Nouveaux schémas Pydantic pour les endpoints
2. **`backend/api/restaurant.py`** - 9 nouveaux endpoints REST
3. **`backend/services/restaurant/overview.py`** - Logique métier (NOUVEAU fichier)
4. **`backend/services/restaurant/__init__.py`** - Exports des nouvelles fonctions
5. **`core/restaurant_costs.py`** - Déjà existant, utilisé pour calculs de base

### Pattern utilisé

- **Multi-tenant**: Tous les endpoints filtrent par `tenant_id` extrait du JWT token
- **ResponseWrapper**: Format de réponse standardisé automatique via middleware
  ```json
  {
    "success": true,
    "data": {...},
    "error": null,
    "meta": {"request_id": "...", "duration_ms": 123}
  }
  ```
- **Pagination**: Pour les listes longues
- **Filtres & Tri**: Flexibles pour l'UX

---

## Endpoints implémentés

### 1. GET `/restaurant/overview`

**Description**: Vue d'ensemble du restaurant avec métriques clés

**Query Parameters**:
- `period` (string, default: "30d"): Période d'analyse (7d, 30d, 90d, 1y)

**Response Schema**: `RestaurantOverview`
```json
{
  "period": "30d",
  "metrics": {
    "revenue": 16500.0,
    "food_cost_pct": 28.5,
    "active_plats_count": 42,
    "total_plats_count": 58,
    "avg_margin_pct": 71.5
  },
  "top_plats": [
    {
      "plat_id": 15,
      "nom": "Burger classique",
      "sales_count": 50,
      "revenue": 625.0,
      "margin_pct": 68.2
    }
  ],
  "alerts": [
    {
      "alert_type": "plat_margin",
      "severity": "warning",
      "message": "Marge 32.1% sous le seuil 35.0%",
      "count": 3
    }
  ],
  "generated_at": "2025-12-12T..."
}
```

**Use Case**: Dashboard principal du module restaurant

---

### 2. GET `/restaurant/plats/list`

**Description**: Liste paginée des plats avec filtres et tri

**Query Parameters**:
- `page` (int, default: 1, min: 1)
- `page_size` (int, default: 50, min: 1, max: 200)
- `categorie` (string, optional): Filtrer par catégorie
- `actif` (bool, optional): Filtrer par statut actif/inactif
- `min_margin_pct` (float, optional): Marge minimale en %
- `sort_by` (string, default: "nom"): Champ de tri (nom, margin_pct, sales_count, prix_vente_ttc)
- `sort_desc` (bool, default: false): Tri descendant si true

**Response Schema**: `PlatListResponse`
```json
{
  "items": [
    {
      "id": 15,
      "nom": "Burger classique",
      "categorie": "Burgers",
      "selling_price": 12.50,
      "cost": 4.20,
      "margin": 8.30,
      "margin_pct": 66.4,
      "food_cost_pct": 33.6,
      "is_active": true,
      "sales_count": null
    }
  ],
  "total": 58,
  "page": 1,
  "page_size": 50
}
```

**Use Case**: Liste complète des plats avec possibilité de filtrer par marge faible

---

### 3. GET `/restaurant/plats/{plat_id}/detail`

**Description**: Détails complets d'un plat avec fiche technique

**Path Parameters**:
- `plat_id` (int, required): ID du plat

**Response Schema**: `PlatDetail`
```json
{
  "id": 15,
  "nom": "Burger classique",
  "categorie": "Burgers",
  "selling_price": 12.50,
  "cost": 4.20,
  "margin": 8.30,
  "margin_pct": 66.4,
  "food_cost_pct": 33.6,
  "is_active": true,
  "ingredients": [
    {
      "ingredient_id": 5,
      "nom": "Pain burger",
      "quantite": 1.0,
      "unite": "unité",
      "unit_price": 0.35,
      "total_cost": 0.35,
      "cost_percentage": 8.3
    },
    {
      "ingredient_id": 12,
      "nom": "Viande hachée",
      "quantite": 0.150,
      "unite": "kg",
      "unit_price": 12.00,
      "total_cost": 1.80,
      "cost_percentage": 42.9
    }
  ],
  "price_history": [
    {
      "id": 234,
      "plat_id": 15,
      "plat_nom": "Burger classique",
      "prix_vente_ttc": 12.50,
      "changed_at": "2025-11-15T10:23:00"
    }
  ]
}
```

**Use Case**: Page de détail d'un plat pour analyse approfondie

---

### 4. GET `/restaurant/plats/{plat_id}/cost-breakdown`

**Description**: Décomposition détaillée du coût par ingrédient

**Path Parameters**:
- `plat_id` (int, required): ID du plat

**Response Schema**: `CostBreakdownResponse`
```json
{
  "plat_id": 15,
  "plat_nom": "Burger classique",
  "total_cost": 4.20,
  "items": [
    {
      "ingredient_id": 12,
      "nom": "Viande hachée",
      "cost": 1.80,
      "cost_percentage": 42.9,
      "price_trend_30d": null
    },
    {
      "ingredient_id": 8,
      "nom": "Fromage cheddar",
      "cost": 0.65,
      "cost_percentage": 15.5,
      "price_trend_30d": null
    }
  ]
}
```

**Use Case**: Analyse détaillée pour optimiser le coût d'un plat

---

### 5. GET `/restaurant/ingredients/list`

**Description**: Liste enrichie des ingrédients avec tendances prix

**Response Schema**: `List[IngredientListItem]`
```json
[
  {
    "id": 12,
    "nom": "Viande hachée",
    "unit": "kg",
    "unit_price": 12.00,
    "stock_qty": 25.5,
    "main_supplier": null,
    "price_trend_30d": null
  }
]
```

**Use Case**: Gestion des ingrédients avec vue sur les coûts

---

### 6. GET `/restaurant/ingredients/{ingredient_id}/price-history-detail`

**Description**: Historique détaillé des prix d'un ingrédient

**Path Parameters**:
- `ingredient_id` (int, required): ID de l'ingrédient

**Response Schema**: `IngredientPriceHistoryResponse`
```json
{
  "ingredient_id": 12,
  "ingredient_nom": "Viande hachée",
  "history": [
    {
      "id": 456,
      "ingredient_id": 12,
      "ingredient_nom": "Viande hachée",
      "cout_unitaire": 12.00,
      "changed_at": "2025-12-01T09:15:00"
    },
    {
      "id": 432,
      "ingredient_id": 12,
      "ingredient_nom": "Viande hachée",
      "cout_unitaire": 11.50,
      "changed_at": "2025-11-01T14:30:00"
    }
  ]
}
```

**Use Case**: Suivi de l'évolution des prix pour négociation fournisseurs

---

### 7. GET `/restaurant/food-cost/analysis`

**Description**: Analyse complète du food cost avec recommandations IA

**Query Parameters**:
- `period` (string, default: "30d"): Période d'analyse (7d, 30d, 90d, 1y)
- `target_food_cost` (float, default: 30.0, min: 0, max: 100): Food cost cible en %

**Response Schema**: `FoodCostAnalysis`
```json
{
  "period": "30d",
  "global_food_cost_pct": 32.5,
  "target_food_cost_pct": 30.0,
  "by_category": [
    {
      "categorie": "Burgers",
      "avg_food_cost_pct": 35.2,
      "plat_count": 12,
      "total_revenue": 0.0
    },
    {
      "categorie": "Salades",
      "avg_food_cost_pct": 28.1,
      "plat_count": 8,
      "total_revenue": 0.0
    }
  ],
  "trend": [
    {
      "period": "M-5",
      "food_cost_pct": 31.0,
      "revenue": 0.0
    },
    {
      "period": "M-4",
      "food_cost_pct": 31.5,
      "revenue": 0.0
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "cost",
      "message": "Food cost 2.5% au-dessus de la cible. Revoyez les prix d'achat ou augmentez les prix de vente.",
      "estimated_impact": null
    },
    {
      "priority": "medium",
      "category": "pricing",
      "message": "Catégorie 'Burgers': food cost élevé à 35.2%",
      "estimated_impact": null
    }
  ]
}
```

**Use Case**: Dashboard analytique du food cost avec insights actionnables

---

### 8. POST `/restaurant/plats/{plat_id}/simulate-price`

**Description**: Simulation de l'impact d'un changement de prix

**Path Parameters**:
- `plat_id` (int, required): ID du plat

**Request Body**: `PriceSimulationInput`
```json
{
  "new_price": 13.50,
  "target_margin_pct": null
}
```
OU
```json
{
  "new_price": null,
  "target_margin_pct": 70.0
}
```

**Response Schema**: `PriceSimulation`
```json
{
  "plat_id": 15,
  "plat_nom": "Burger classique",
  "current": {
    "selling_price": 12.50,
    "cost": 4.20,
    "margin": 8.30,
    "margin_pct": 66.4,
    "food_cost_pct": 33.6
  },
  "simulated": {
    "selling_price": 13.50,
    "cost": 4.20,
    "margin": 9.30,
    "margin_pct": 68.9,
    "food_cost_pct": 31.1
  },
  "impact": {
    "margin_change": 1.00,
    "margin_pct_change": 2.5,
    "food_cost_change": -2.5,
    "annual_impact": 600.0
  }
}
```

**Use Case**: Outil de simulation pour décider des ajustements de prix

---

### 9. GET `/restaurant/alerts/detailed`

**Description**: Liste détaillée des alertes restaurant avec filtres

**Query Parameters**:
- `alert_type` (string, optional): plat_margin, ingredient_price, stock_rupture
- `severity` (string, optional): critical, warning, info

**Response Schema**: `List[RestaurantAlertDetail]`
```json
[
  {
    "id": 123,
    "alert_type": "plat_margin",
    "severity": "warning",
    "message": "Marge 32.1% sous le seuil 35.0%",
    "plat_id": 18,
    "plat_nom": "Salade César",
    "ingredient_id": null,
    "ingredient_nom": null,
    "current_value": 32.1,
    "threshold": 35.0,
    "created_at": "2025-12-10T15:30:00"
  }
]
```

**Use Case**: Centre de notification pour les anomalies et points d'attention

---

## Formules de calcul

### Food Cost %
```
food_cost_pct = (cost / selling_price) * 100
```

### Marge %
```
margin_pct = ((selling_price - cost) / selling_price) * 100
```

### Marge brute (€)
```
margin = selling_price - cost
```

### Coût matière
```
cost = SUM(ingredient.quantite * ingredient.unit_price)
```

---

## Configuration requise

### Tables de base de données

Les endpoints s'appuient sur les tables existantes:
- `plats`
- `ingredients`
- `plat_ingredients`
- `restaurant_plat_costs` (table de cache pour les coûts calculés)
- `restaurant_alerts` (alertes générées)
- `restaurant_plat_price_history` (historique prix plats)
- `restaurant_ingredient_price_history` (historique prix ingrédients)

### Middleware

Le `ResponseWrapperMiddleware` est déjà configuré dans `backend/main.py`:
```python
app.add_middleware(
    ResponseWrapperMiddleware,
    exclude_paths=["/health", "/docs", "/redoc", "/openapi.json", "/metrics"],
    wrap_errors_only=False,
)
```

Toutes les réponses sont automatiquement wrappées au format:
```json
{
  "success": true,
  "data": {...},
  "error": null,
  "meta": {
    "request_id": "abc-123",
    "duration_ms": 45.23
  }
}
```

---

## Authentification & Sécurité

Tous les endpoints requièrent:
1. **JWT Token valide** via header `Authorization: Bearer <token>`
2. **Extraction du tenant_id** depuis le token
3. **Filtrage automatique** de toutes les requêtes SQL par `tenant_id`

Pattern utilisé dans tous les endpoints:
```python
@router.get("/overview", response_model=RestaurantOverview)
def get_restaurant_overview(
    period: str = Query("30d"),
    tenant: Tenant = Depends(get_current_tenant),  # <-- Injection du tenant
):
    payload = restaurant_service.get_restaurant_overview(tenant.id, period=period)
    return RestaurantOverview(**payload)
```

---

## Données mockées vs réelles

**Actuellement mockées** (à implémenter avec vraies données):
- `sales_count`: Nombre de ventes par plat (nécessite table `restaurant_sales`)
- `revenue`: Chiffre d'affaires (nécessite agrégation des ventes)
- `main_supplier`: Fournisseur principal (nécessite mapping ingrédient-fournisseur)
- `price_trend_30d`: Tendance prix sur 30j (calculable depuis historique existant)

**Déjà réelles**:
- Coûts matière (calculés depuis `plat_ingredients` et `ingredients`)
- Marges et food cost (calculés en temps réel)
- Prix actuels (depuis `plats` et `ingredients`)
- Historique des prix (depuis tables `*_price_history`)
- Alertes de marge (générées par `core/restaurant_costs.py`)

---

## Tests recommandés

### Tests unitaires
```bash
# Tester les calculs de marge
pytest tests/test_restaurant_overview.py::test_margin_calculation

# Tester la simulation de prix
pytest tests/test_restaurant_overview.py::test_price_simulation
```

### Tests d'intégration
```bash
# Tester les endpoints avec authentification
pytest tests/integration/test_restaurant_api.py
```

### Tests manuels avec curl
```bash
# 1. Obtenir un token
TOKEN=$(curl -X POST http://localhost:8000/auth/token \
  -d "username=admin&password=admin" | jq -r .access_token)

# 2. Tester l'overview
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/restaurant/overview?period=30d" | jq

# 3. Tester la liste paginée
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/restaurant/plats/list?page=1&min_margin_pct=60" | jq

# 4. Tester la simulation de prix
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_price": 15.0}' \
  "http://localhost:8000/restaurant/plats/1/simulate-price" | jq
```

---

## Prochaines étapes

### Phase 2: Intégration données réelles
1. Créer table `restaurant_sales` pour tracker les ventes
2. Implémenter agrégations de CA par période
3. Mapper ingrédients → fournisseurs
4. Calculer tendances de prix depuis historique

### Phase 3: Features avancées
1. Alertes automatiques sur hausse de prix ingrédients
2. Prévisions de rupture de stock
3. Recommandations IA optimisées (ML)
4. Export PDF des analyses food cost

### Phase 4: Frontend
1. Dashboard Restaurant Overview (React)
2. Liste interactive des plats avec DataTable
3. Simulateur de prix visuel
4. Graphiques de tendances food cost

---

## Support

Pour toute question sur cette implémentation:
- Consulter le code source: `backend/api/restaurant.py`
- Voir la logique métier: `backend/services/restaurant/overview.py`
- Schémas de données: `backend/schemas/restaurant.py`

**Auteur**: Claude Opus 4.5
**Date**: 2025-12-12
**Version**: 1.0.0
