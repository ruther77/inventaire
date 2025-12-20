# NewCMS Intelligence Endpoints - Documentation de Test

## Endpoints créés

### 1. GET `/api/newcms/intelligence/overview`
**Description**: Vue d'ensemble de l'intelligence agrégée

**Réponse**:
```json
{
  "health_score": {
    "overall_score": 7.5,
    "stock_score": 8.0,
    "cash_score": 7.0,
    "anomaly_score": 9.0,
    "margin_score": 6.5,
    "grade": "B",
    "trend": "stable",
    "details": {}
  },
  "critical_anomalies": [
    {
      "id": "anomaly_123",
      "type": "amount_outlier",
      "severity": "critical",
      "description": "Transaction anormale de 5000€",
      "impact": 5000.0,
      "detected_at": "2025-12-11T10:00:00"
    }
  ],
  "key_forecasts": [
    {
      "type": "stockout",
      "date": "2025-12-15",
      "description": "Rupture prévue: Produit XYZ (3.2j)",
      "severity": "critical",
      "value": 10.0
    }
  ],
  "supplier_scoring": {
    "top": [
      {
        "supplier_name": "Fournisseur A",
        "score": 9.2,
        "grade": "A",
        "trend": "stable",
        "issues_count": 0
      }
    ],
    "bottom": [
      {
        "supplier_name": "Fournisseur Z",
        "score": 3.5,
        "grade": "D",
        "trend": "down",
        "issues_count": 5
      }
    ]
  },
  "recommendations": [
    {
      "id": "reorder_123_abc",
      "type": "reorder_stock",
      "priority": "critical",
      "title": "Réapprovisionner Produit XYZ",
      "description": "Stock critique: 10 unités restantes (3.2j)",
      "impact_estimate": "Éviter rupture, coût: 250€",
      "confidence": 0.9,
      "actions": [
        {
          "label": "Commander maintenant",
          "endpoint": "/api/orders/create",
          "method": "POST",
          "payload": {
            "product_id": 123,
            "quantity": 50,
            "estimated_cost": 250.0
          },
          "confirmation_required": true,
          "confirmation_message": "Commander 50 unités de Produit XYZ ?"
        }
      ],
      "metadata": {
        "product_id": 123,
        "current_stock": 10,
        "days_remaining": 3.2
      },
      "created_at": "2025-12-11T21:00:00",
      "expires_at": null
    }
  ],
  "generated_at": "2025-12-11T21:00:00"
}
```

### 2. GET `/api/newcms/intelligence/recommendations`
**Description**: Liste toutes les recommandations avec filtres

**Paramètres**:
- `priority` (optional): critical, high, medium, low
- `type` (optional): reorder_stock, change_supplier, adjust_price, reduce_stock, optimize_margin, resolve_anomaly, improve_cashflow, negotiate_terms
- `limit` (default: 20, max: 100)

**Réponse**:
```json
[
  {
    "id": "reorder_123_abc",
    "type": "reorder_stock",
    "priority": "critical",
    "title": "Réapprovisionner Produit XYZ",
    "description": "Stock critique: 10 unités restantes (3.2j)",
    "impact_estimate": "Éviter rupture, coût: 250€",
    "confidence": 0.9,
    "actions": [
      {
        "label": "Commander maintenant",
        "endpoint": "/api/orders/create",
        "method": "POST",
        "payload": {
          "product_id": 123,
          "quantity": 50
        },
        "confirmation_required": true
      }
    ],
    "metadata": {},
    "created_at": "2025-12-11T21:00:00"
  }
]
```

### 3. POST `/api/newcms/intelligence/recommendations/{recommendation_id}/apply`
**Description**: Applique une recommandation

**Paramètres**:
- `recommendation_id` (path): ID de la recommandation
- `action_index` (query, default: 0): Index de l'action à exécuter

**Réponse**:
```json
{
  "success": true,
  "recommendation_id": "reorder_123_abc",
  "action_taken": "Commander maintenant",
  "result": {
    "simulated": true,
    "endpoint": "/api/orders/create",
    "method": "POST",
    "payload": {
      "product_id": 123,
      "quantity": 50
    }
  },
  "message": "Action 'Commander maintenant' appliquée avec succès (simulé)"
}
```

### 4. GET `/api/newcms/intelligence/health-score`
**Description**: Retourne uniquement le score de santé global

**Réponse**:
```json
{
  "overall_score": 7.5,
  "stock_score": 8.0,
  "cash_score": 7.0,
  "anomaly_score": 9.0,
  "margin_score": 6.5,
  "grade": "B",
  "trend": "stable",
  "details": {}
}
```

### 5. GET `/api/newcms/intelligence/metrics/summary`
**Description**: Résumé des métriques pour dashboard

**Réponse**:
```json
{
  "health_score": {
    "overall": 7.5,
    "grade": "B",
    "breakdown": {
      "stock": 8.0,
      "cash": 7.0,
      "anomalies": 9.0,
      "margins": 6.5
    }
  },
  "alerts": {
    "critical_count": 3,
    "high_count": 5,
    "total": 12
  },
  "forecasts": {
    "stockouts_7d": 2,
    "cashflow_alerts": 1
  }
}
```

## Score de Santé - Formule

Score global = **30% stock + 30% cash + 20% anomalies + 20% marges**

### Score Stock (0-10)
- Basé sur: produits en rupture, stock mort, rotation
- Formule: `10 * (1 - (stockout + overstock) / (total * 2))`

### Score Cash (0-10)
- Basé sur: ratio entrées/sorties sur 30j
- Seuils:
  - ratio >= 1.2 → 10
  - ratio >= 1.0 → 7
  - ratio >= 0.8 → 5
  - ratio < 0.8 → 3

### Score Anomalies (0-10)
- Basé sur: nombre et sévérité des anomalies non résolues
- Formule: `10 - min(10, severity_weight / 5)`
- Poids: critical=3, high=2, medium=1, low=0

### Score Marges (0-10)
- Basé sur: marge brute moyenne, produits avec marge négative
- Seuils:
  - marge >= 30% → 10
  - marge >= 20% → 8
  - marge >= 15% → 6
  - marge >= 10% → 4
  - marge < 10% → 2
- Pénalité: -0.5 par produit avec marge négative

### Grade
- A: 9-10
- B: 7-9
- C: 5-7
- D: 3-5
- F: <3

## Types de Recommandations

### 1. REORDER_STOCK (critical/high)
Commander un produit en rupture imminente
- **Actions**: Commander maintenant
- **Payload**: product_id, quantity, estimated_cost

### 2. REDUCE_STOCK (medium)
Réduire stock mort
- **Actions**: Créer promotion, Retourner au fournisseur

### 3. OPTIMIZE_MARGIN (medium/high)
Optimiser marge faible
- **Actions**: Ajuster le prix

### 4. CHANGE_SUPPLIER (high/medium)
Revoir fournisseur avec score faible
- **Actions**: Voir alternatives, Négocier conditions

## Conventions

- **Priorités**: critical > high > medium > low
- **Recommandations actionnables**: Chaque recommandation a un payload prêt à l'emploi
- **Tenant mapping**:
  - Tenant intelligence (4) → épicerie (1) pour produits
  - Tenant intelligence (4) → restaurant (2) pour finance
- **Limites**: Max 10 recommandations par défaut, 50 anomalies

## Test Manuel

```bash
# 1. Overview complet
curl http://localhost:8000/api/newcms/intelligence/overview

# 2. Recommandations critical uniquement
curl "http://localhost:8000/api/newcms/intelligence/recommendations?priority=critical"

# 3. Recommandations de réapprovisionnement
curl "http://localhost:8000/api/newcms/intelligence/recommendations?type=reorder_stock"

# 4. Health score
curl http://localhost:8000/api/newcms/intelligence/health-score

# 5. Métriques summary
curl http://localhost:8000/api/newcms/intelligence/metrics/summary

# 6. Appliquer une recommandation (simulé)
curl -X POST "http://localhost:8000/api/newcms/intelligence/recommendations/reorder_123_abc/apply?action_index=0"
```
