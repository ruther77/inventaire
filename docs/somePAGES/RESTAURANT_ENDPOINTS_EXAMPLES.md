# Restaurant Overview & Food Cost - Exemples d'utilisation

## Configuration initiale

### 1. Obtenir un token d'authentification

```bash
# Requête d'authentification
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"

# Réponse
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

# Stocker le token dans une variable
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Exemples d'appels API

### 1. Vue d'ensemble restaurant

```bash
# GET /restaurant/overview - Période 30 jours
curl -X GET "http://localhost:8000/restaurant/overview?period=30d" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq

# Avec période de 7 jours
curl -X GET "http://localhost:8000/restaurant/overview?period=7d" \
  -H "Authorization: Bearer $TOKEN" | jq

# Réponse (wrappée automatiquement par ResponseWrapper)
{
  "success": true,
  "data": {
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
    "generated_at": "2025-12-12T15:30:00"
  },
  "error": null,
  "meta": {
    "request_id": "abc-123",
    "duration_ms": 45.23
  }
}
```

---

### 2. Liste paginée des plats

```bash
# GET /restaurant/plats/list - Tous les plats (page 1)
curl -X GET "http://localhost:8000/restaurant/plats/list" \
  -H "Authorization: Bearer $TOKEN" | jq

# Avec pagination
curl -X GET "http://localhost:8000/restaurant/plats/list?page=2&page_size=20" \
  -H "Authorization: Bearer $TOKEN" | jq

# Filtrer par catégorie
curl -X GET "http://localhost:8000/restaurant/plats/list?categorie=Burgers" \
  -H "Authorization: Bearer $TOKEN" | jq

# Filtrer par plats actifs uniquement
curl -X GET "http://localhost:8000/restaurant/plats/list?actif=true" \
  -H "Authorization: Bearer $TOKEN" | jq

# Filtrer par marge minimale (plats avec marge >= 60%)
curl -X GET "http://localhost:8000/restaurant/plats/list?min_margin_pct=60" \
  -H "Authorization: Bearer $TOKEN" | jq

# Trier par marge décroissante
curl -X GET "http://localhost:8000/restaurant/plats/list?sort_by=margin_pct&sort_desc=true" \
  -H "Authorization: Bearer $TOKEN" | jq

# Combinaison de filtres
curl -X GET "http://localhost:8000/restaurant/plats/list?categorie=Burgers&actif=true&min_margin_pct=65&sort_by=margin_pct&sort_desc=true" \
  -H "Authorization: Bearer $TOKEN" | jq

# Réponse
{
  "success": true,
  "data": {
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
  },
  "error": null,
  "meta": {...}
}
```

---

### 3. Détails d'un plat

```bash
# GET /restaurant/plats/{plat_id}/detail
curl -X GET "http://localhost:8000/restaurant/plats/15/detail" \
  -H "Authorization: Bearer $TOKEN" | jq

# Réponse
{
  "success": true,
  "data": {
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
  },
  "error": null,
  "meta": {...}
}
```

---

### 4. Décomposition du coût d'un plat

```bash
# GET /restaurant/plats/{plat_id}/cost-breakdown
curl -X GET "http://localhost:8000/restaurant/plats/15/cost-breakdown" \
  -H "Authorization: Bearer $TOKEN" | jq

# Réponse
{
  "success": true,
  "data": {
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
      },
      {
        "ingredient_id": 5,
        "nom": "Pain burger",
        "cost": 0.35,
        "cost_percentage": 8.3,
        "price_trend_30d": null
      }
    ]
  },
  "error": null,
  "meta": {...}
}
```

---

### 5. Liste des ingrédients

```bash
# GET /restaurant/ingredients/list
curl -X GET "http://localhost:8000/restaurant/ingredients/list" \
  -H "Authorization: Bearer $TOKEN" | jq

# Réponse
{
  "success": true,
  "data": [
    {
      "id": 12,
      "nom": "Viande hachée",
      "unit": "kg",
      "unit_price": 12.00,
      "stock_qty": 25.5,
      "main_supplier": null,
      "price_trend_30d": null
    },
    {
      "id": 8,
      "nom": "Fromage cheddar",
      "unit": "kg",
      "unit_price": 8.50,
      "stock_qty": 12.3,
      "main_supplier": null,
      "price_trend_30d": null
    }
  ],
  "error": null,
  "meta": {...}
}
```

---

### 6. Historique des prix d'un ingrédient

```bash
# GET /restaurant/ingredients/{ingredient_id}/price-history-detail
curl -X GET "http://localhost:8000/restaurant/ingredients/12/price-history-detail" \
  -H "Authorization: Bearer $TOKEN" | jq

# Réponse
{
  "success": true,
  "data": {
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
  },
  "error": null,
  "meta": {...}
}
```

---

### 7. Analyse du food cost

```bash
# GET /restaurant/food-cost/analysis - Période 30 jours, cible 30%
curl -X GET "http://localhost:8000/restaurant/food-cost/analysis?period=30d&target_food_cost=30.0" \
  -H "Authorization: Bearer $TOKEN" | jq

# Avec cible plus stricte (25%)
curl -X GET "http://localhost:8000/restaurant/food-cost/analysis?period=90d&target_food_cost=25.0" \
  -H "Authorization: Bearer $TOKEN" | jq

# Réponse
{
  "success": true,
  "data": {
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
      }
    ]
  },
  "error": null,
  "meta": {...}
}
```

---

### 8. Simulation de changement de prix

```bash
# POST /restaurant/plats/{plat_id}/simulate-price
# Option 1: Simuler avec un nouveau prix
curl -X POST "http://localhost:8000/restaurant/plats/15/simulate-price" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_price": 13.50,
    "target_margin_pct": null
  }' | jq

# Option 2: Simuler pour atteindre une marge cible
curl -X POST "http://localhost:8000/restaurant/plats/15/simulate-price" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_price": null,
    "target_margin_pct": 70.0
  }' | jq

# Réponse
{
  "success": true,
  "data": {
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
  },
  "error": null,
  "meta": {...}
}
```

---

### 9. Liste des alertes

```bash
# GET /restaurant/alerts/detailed - Toutes les alertes
curl -X GET "http://localhost:8000/restaurant/alerts/detailed" \
  -H "Authorization: Bearer $TOKEN" | jq

# Filtrer par type d'alerte
curl -X GET "http://localhost:8000/restaurant/alerts/detailed?alert_type=plat_margin" \
  -H "Authorization: Bearer $TOKEN" | jq

# Filtrer par sévérité
curl -X GET "http://localhost:8000/restaurant/alerts/detailed?severity=critical" \
  -H "Authorization: Bearer $TOKEN" | jq

# Combinaison de filtres
curl -X GET "http://localhost:8000/restaurant/alerts/detailed?alert_type=plat_margin&severity=warning" \
  -H "Authorization: Bearer $TOKEN" | jq

# Réponse
{
  "success": true,
  "data": [
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
  ],
  "error": null,
  "meta": {...}
}
```

---

## Script de test complet

```bash
#!/bin/bash

# Configuration
BASE_URL="http://localhost:8000"
USERNAME="admin"
PASSWORD="admin"

echo "=== Test des endpoints Restaurant Overview & Food Cost ==="
echo ""

# 1. Obtenir un token
echo "1. Authentification..."
TOKEN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" = "null" ]; then
  echo "❌ Erreur d'authentification"
  exit 1
fi

echo "✅ Token obtenu"
echo ""

# 2. Test overview
echo "2. Test de l'overview restaurant..."
curl -s -X GET "$BASE_URL/restaurant/overview?period=30d" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.metrics'
echo ""

# 3. Test liste plats
echo "3. Test de la liste paginée des plats..."
curl -s -X GET "$BASE_URL/restaurant/plats/list?page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN" | jq '.data | {total, page, items_count: (.items | length)}'
echo ""

# 4. Test détail plat (ID 1)
echo "4. Test détails d'un plat..."
curl -s -X GET "$BASE_URL/restaurant/plats/1/detail" \
  -H "Authorization: Bearer $TOKEN" | jq '.data | {nom, cost, selling_price, margin_pct}'
echo ""

# 5. Test cost breakdown
echo "5. Test décomposition des coûts..."
curl -s -X GET "$BASE_URL/restaurant/plats/1/cost-breakdown" \
  -H "Authorization: Bearer $TOKEN" | jq '.data | {plat_nom, total_cost, ingredients_count: (.items | length)}'
echo ""

# 6. Test liste ingrédients
echo "6. Test liste des ingrédients..."
curl -s -X GET "$BASE_URL/restaurant/ingredients/list" \
  -H "Authorization: Bearer $TOKEN" | jq '.data | length'
echo ""

# 7. Test food cost analysis
echo "7. Test analyse food cost..."
curl -s -X GET "$BASE_URL/restaurant/food-cost/analysis?period=30d&target_food_cost=30.0" \
  -H "Authorization: Bearer $TOKEN" | jq '.data | {global_food_cost_pct, target_food_cost_pct, recommendations_count: (.recommendations | length)}'
echo ""

# 8. Test simulation de prix
echo "8. Test simulation de prix..."
curl -s -X POST "$BASE_URL/restaurant/plats/1/simulate-price" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_price": 15.0}' | jq '.data.impact'
echo ""

# 9. Test alertes
echo "9. Test liste des alertes..."
curl -s -X GET "$BASE_URL/restaurant/alerts/detailed" \
  -H "Authorization: Bearer $TOKEN" | jq '.data | length'
echo ""

echo "=== Tests terminés ==="
```

---

## Gestion des erreurs

### Exemple d'erreur: Plat non trouvé

```bash
curl -X GET "http://localhost:8000/restaurant/plats/99999/detail" \
  -H "Authorization: Bearer $TOKEN" | jq

# Réponse
{
  "success": false,
  "data": null,
  "error": {
    "code": "NOT_FOUND",
    "message": "Plat 99999 not found",
    "suggestion": "Vérifiez que l'ID du plat existe"
  },
  "meta": {
    "request_id": "xyz-789",
    "duration_ms": 12.34
  }
}
```

### Exemple d'erreur: Validation

```bash
curl -X POST "http://localhost:8000/restaurant/plats/1/simulate-price" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_price": -5.0}' | jq

# Réponse
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Données invalides",
    "field_errors": {
      "new_price": ["must be >= 0"]
    }
  },
  "meta": {...}
}
```

---

## Monitoring & Performance

Tous les endpoints incluent des métriques de performance:

```json
{
  "meta": {
    "request_id": "abc-123",
    "duration_ms": 45.23
  }
}
```

Pour consulter les statistiques globales de performance:

```bash
curl -X GET "http://localhost:8000/metrics" \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Notes importantes

1. **Multi-tenant**: Toutes les requêtes sont automatiquement filtrées par `tenant_id` extrait du JWT
2. **Format de réponse**: Le `ResponseWrapperMiddleware` wrappe automatiquement toutes les réponses
3. **Authentification**: Tous les endpoints nécessitent un token JWT valide
4. **Pagination**: Les listes utilisent la pagination pour éviter les réponses trop volumineuses
5. **Données mockées**: Certaines données (sales_count, revenue) sont actuellement mockées en attendant l'intégration de la table des ventes

---

## Prochaines étapes

1. Tester les endpoints avec des données réelles
2. Intégrer la table `restaurant_sales` pour les vraies ventes
3. Implémenter le frontend React pour consommer ces APIs
4. Ajouter des graphiques de visualisation des tendances

---

**Documentation générée le**: 2025-12-12
**Version**: 1.0.0
