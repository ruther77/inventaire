# Supplier Scoring API - Documentation

## Vue d'ensemble

L'API Supplier Scoring fournit un système complet de notation et d'évaluation des fournisseurs basé sur des métriques multi-dimensionnelles.

## Endpoints Implémentés

### 1. GET /supplier-scoring/overview

**Description:** Vue d'ensemble des scores fournisseurs

**Réponse:**
```json
{
  "success": true,
  "data": {
    "total_suppliers": 45,
    "average_score": 78.5,
    "score_distribution": {
      "A": 10,
      "B": 15,
      "C": 12,
      "D": 5,
      "F": 3
    },
    "top_suppliers": [...],
    "bottom_suppliers": [...],
    "trends": {
      "overall_trend": "stable",
      "improving_count": 12,
      "declining_count": 8
    },
    "alerts_summary": {
      "score_drop": 2,
      "delivery_issues": 1,
      "quality_degradation": 0,
      "price_spike": 3
    }
  },
  "error": null,
  "meta": {
    "request_id": "...",
    "duration_ms": 125.5
  }
}
```

### 2. GET /supplier-scoring/suppliers

**Description:** Liste paginée des fournisseurs avec scores

**Paramètres:**
- `page` (int): Numéro de page (défaut: 1)
- `per_page` (int): Résultats par page (défaut: 20, max: 100)
- `sort_by` (str): Tri par score, name ou grade (défaut: score)
- `order` (str): Ordre asc ou desc (défaut: desc)
- `min_score` (float, optional): Score minimum
- `grade_filter` (str, optional): Filtrer par grade (A, B, C, D, F)

**Réponse:**
```json
{
  "success": true,
  "data": {
    "suppliers": [
      {
        "rank": 1,
        "supplier_id": 101,
        "supplier_name": "Fournisseur Alpha",
        "score": 92.5,
        "grade": "A",
        "dimensions": {
          "price_stability": 95.0,
          "delivery_reliability": 90.0,
          "invoice_accuracy": 88.0,
          "stock_accuracy": 92.0,
          "payment_terms": 90.0,
          "responsiveness": 95.0,
          "product_quality": 93.0
        },
        "last_updated": "2025-12-11T10:30:00Z",
        "trend": "stable"
      }
    ],
    "total_count": 45,
    "page": 1,
    "per_page": 20,
    "total_pages": 3
  },
  "error": null,
  "meta": {
    "request_id": "...",
    "duration_ms": 85.2,
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total_pages": 3,
      "total_count": 45
    }
  }
}
```

### 3. GET /supplier-scoring/suppliers/{supplier_id}

**Description:** Détails complets d'un fournisseur

**Réponse:**
```json
{
  "success": true,
  "data": {
    "supplier_id": 101,
    "supplier_name": "Fournisseur Alpha",
    "current_score": {
      "supplier_id": 101,
      "supplier_name": "Fournisseur Alpha",
      "overall_score": 92.5,
      "grade": "A",
      "delivery_score": 90.0,
      "quality_score": 93.0,
      "price_score": 95.0,
      "reliability_score": 88.0,
      "trend": "improving",
      "last_updated": "2025-12-11T10:30:00Z",
      "dimensions": {...},
      "metrics": {...}
    },
    "history": [
      {
        "date": "2025-12-01T00:00:00Z",
        "score": 90.0,
        "grade": "A",
        "breakdown": {}
      }
    ],
    "recent_deliveries": [...],
    "recent_issues": [...],
    "alerts": [...],
    "statistics": {
      "total_orders": 156,
      "total_invoices": 234,
      "average_order_value": 1250.50,
      "partnership_duration_days": 365
    },
    "recommendations": [
      "Améliorer la ponctualité des livraisons"
    ]
  },
  "error": null,
  "meta": {
    "request_id": "...",
    "duration_ms": 150.3
  }
}
```

### 4. GET /supplier-scoring/suppliers/{supplier_id}/history

**Description:** Historique des scores d'un fournisseur

**Paramètres:**
- `limit` (int): Nombre d'entrées (défaut: 20, max: 100)

**Réponse:**
```json
{
  "success": true,
  "data": {
    "supplier_id": 101,
    "supplier_name": "Fournisseur Alpha",
    "history": [
      {
        "date": "2025-12-10T00:00:00Z",
        "score": 92.5,
        "grade": "A",
        "breakdown": {}
      },
      {
        "date": "2025-12-03T00:00:00Z",
        "score": 91.0,
        "grade": "A",
        "breakdown": {}
      }
    ],
    "trend_analysis": {
      "direction": "improving",
      "average_score": 91.5,
      "recent_average": 92.5,
      "variation": 1.0
    }
  },
  "error": null,
  "meta": {
    "request_id": "...",
    "duration_ms": 45.8
  }
}
```

### 5. GET /supplier-scoring/criteria

**Description:** Critères de scoring configurables

**Réponse:**
```json
{
  "success": true,
  "data": {
    "criteria": [
      {
        "criterion_id": "price_stability",
        "name": "Stabilité des prix",
        "weight": 0.25,
        "description": "Volatilité et tendance des prix pratiqués",
        "enabled": true
      },
      {
        "criterion_id": "delivery_reliability",
        "name": "Fiabilité livraisons",
        "weight": 0.20,
        "description": "Ponctualité et respect des dates de livraison",
        "enabled": true
      }
    ],
    "total_weight": 1.0
  },
  "error": null,
  "meta": {
    "request_id": "...",
    "duration_ms": 12.5
  }
}
```

### 6. PUT /supplier-scoring/criteria

**Description:** Mettre à jour les pondérations des critères

**Corps de requête:**
```json
{
  "weights": {
    "price_stability": 0.30,
    "delivery_reliability": 0.25,
    "invoice_accuracy": 0.15,
    "stock_accuracy": 0.10,
    "payment_terms": 0.10,
    "responsiveness": 0.05,
    "product_quality": 0.05
  }
}
```

**Validation:**
- Chaque poids doit être entre 0 et 1
- La somme des poids doit être égale à 1.0 (±0.01)

**Réponse:**
```json
{
  "success": true,
  "data": {
    "criteria": [...],
    "total_weight": 1.0
  },
  "error": null,
  "meta": {
    "request_id": "...",
    "duration_ms": 25.3,
    "message": "Pondérations mises à jour avec succès"
  }
}
```

### 7. GET /supplier-scoring/alerts

**Description:** Alertes sur les scores fournisseurs dégradés

**Paramètres:**
- `severity` (str, optional): Filtrer par sévérité (info, warning, critical)
- `acknowledged` (bool, optional): Filtrer par état d'acquittement
- `limit` (int): Nombre maximum d'alertes (défaut: 50, max: 200)

**Réponse:**
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "alert_id": "alert_001",
        "supplier_id": 101,
        "supplier_name": "Fournisseur Alpha",
        "alert_type": "score_drop",
        "message": "Score global en baisse de 15 points ce mois",
        "severity": "critical",
        "created_at": "2025-12-10T15:30:00Z",
        "acknowledged": false,
        "details": {
          "previous_score": 85.0,
          "current_score": 70.0
        }
      }
    ],
    "total_count": 6,
    "unacknowledged_count": 4
  },
  "error": null,
  "meta": {
    "request_id": "...",
    "duration_ms": 35.6
  }
}
```

### 8. POST /supplier-scoring/recalculate

**Description:** Recalculer tous les scores fournisseurs

**Corps de requête:**
```json
{
  "supplier_names": ["Fournisseur A", "Fournisseur B"],
  "period_days": 90,
  "force": false
}
```

**Réponse:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "suppliers_processed": 45,
    "suppliers_failed": 0,
    "duration_seconds": 12.5,
    "errors": []
  },
  "error": null,
  "meta": {
    "request_id": "...",
    "duration_ms": 12500.0,
    "message": "Recalcul terminé: 45 fournisseurs traités"
  }
}
```

## Endpoints Legacy (rétrocompatibilité)

Les endpoints suivants sont conservés pour la rétrocompatibilité mais marqués comme `[LEGACY]`:

- `GET /supplier-scoring/score/{supplier_name}` - Utiliser `/suppliers/{supplier_id}` à la place
- `GET /supplier-scoring/ranking` - Utiliser `/suppliers` avec pagination à la place
- `GET /supplier-scoring/dimensions` - Utiliser `/criteria` à la place
- `GET /supplier-scoring/history/{supplier_name}` - Utiliser `/suppliers/{supplier_id}/history` à la place

Les endpoints suivants restent actifs:
- `POST /supplier-scoring/compare` - Comparaison de fournisseurs
- `POST /supplier-scoring/delivery` - Enregistrer une livraison
- `POST /supplier-scoring/issue` - Enregistrer un incident

## Structure des données

### SupplierScore
```typescript
{
  supplier_id: number | null,
  supplier_name: string,
  overall_score: number,        // 0-100
  grade: string,                 // A, B, C, D, F
  delivery_score: number,        // 0-100
  quality_score: number,         // 0-100
  price_score: number,           // 0-100
  reliability_score: number,     // 0-100
  trend: "improving" | "stable" | "declining" | "up" | "down",
  last_updated: string,          // ISO datetime
  dimensions: {
    [key: string]: number
  },
  metrics: {
    [key: string]: any
  }
}
```

### ScoreHistoryItem
```typescript
{
  date: string,                  // ISO datetime
  score: number,                 // 0-100
  grade: string,                 // A, B, C, D, F
  breakdown: {
    [dimension: string]: number
  }
}
```

### SupplierAlert
```typescript
{
  alert_id: string,
  supplier_id: number | null,
  supplier_name: string,
  alert_type: "score_drop" | "delivery_issues" | "quality_degradation" | "price_spike",
  message: string,
  severity: "info" | "warning" | "critical",
  created_at: string,            // ISO datetime
  acknowledged: boolean,
  details?: {
    [key: string]: any
  }
}
```

## Dimensions de scoring

### 1. price_stability (25%)
- Volatilité des prix
- Tendance (hausse/baisse)
- Score: 100 - (variation_avg * 5) - (volatilité * 2)

### 2. delivery_reliability (20%)
- Ponctualité des livraisons
- Taux de livraisons à temps
- Score: taux_à_temps * 0.8 + (100 - min(100, délai_moyen * 10)) * 0.2

### 3. invoice_accuracy (15%)
- Taux d'erreurs sur factures
- Pénalités par sévérité (critical: 10, medium: 5, low: 2)
- Score: 100 - taux_erreur * 2 - pénalité

### 4. stock_accuracy (15%)
- Écarts stock théorique/réel
- Taux de précision (écart ≤ 2%)
- Score: taux_précision * 0.7 + max(0, 100 - écart_moyen * 5) * 0.3

### 5. payment_terms (10%)
- Flexibilité des délais de paiement
- Actuellement: score par défaut 80.0

### 6. responsiveness (10%)
- Rapidité de réponse aux demandes
- Actuellement: score par défaut 75.0

### 7. product_quality (5%)
- Qualité générale des produits
- Actuellement: score par défaut 80.0

## Calcul du grade

- **A**: Score ≥ 90
- **B**: 80 ≤ Score < 90
- **C**: 70 ≤ Score < 80
- **D**: 60 ≤ Score < 70
- **F**: Score < 60

## Format de réponse standardisé

Tous les endpoints utilisent le format ResponseWrapper:

```json
{
  "success": true | false,
  "data": {...} | null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Message d'erreur",
    "suggestion": "Action recommandée",
    "details": {...},
    "field_errors": {...}
  } | null,
  "meta": {
    "request_id": "uuid",
    "duration_ms": 123.45,
    "pagination": {...},
    "...": "..."
  }
}
```

## Gestion des erreurs

### Codes d'erreur communs

- `OVERVIEW_ERROR`: Erreur lors de la récupération de la vue d'ensemble
- `LIST_ERROR`: Erreur lors de la récupération de la liste
- `DETAILS_ERROR`: Erreur lors de la récupération des détails
- `HISTORY_ERROR`: Erreur lors de la récupération de l'historique
- `CRITERIA_ERROR`: Erreur liée aux critères de scoring
- `UPDATE_ERROR`: Erreur lors de la mise à jour
- `ALERTS_ERROR`: Erreur lors de la récupération des alertes
- `RECALCULATE_ERROR`: Erreur lors du recalcul des scores
- `SCORE_ERROR`: Erreur lors du calcul du score
- `RANKING_ERROR`: Erreur lors du classement
- `COMPARISON_ERROR`: Erreur lors de la comparaison
- `DELIVERY_ERROR`: Erreur lors de l'enregistrement d'une livraison
- `ISSUE_ERROR`: Erreur lors de l'enregistrement d'un incident

## Sécurité et multi-tenancy

- Tous les endpoints utilisent `get_current_tenant()` pour extraire le `tenant_id` du JWT token
- Les données sont automatiquement filtrées par `tenant_id`
- Aucun fournisseur d'un autre tenant n'est accessible

## Performance

- Les endpoints de liste utilisent la pagination pour éviter les surcharges
- Le recalcul des scores peut être lancé en arrière-plan pour les gros volumes
- Les historiques sont limités à 100 entrées maximum par requête

## Tests

Pour tester l'API:

```bash
# Vue d'ensemble
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/supplier-scoring/overview

# Liste paginée
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/supplier-scoring/suppliers?page=1&per_page=20&sort_by=score&order=desc"

# Détails d'un fournisseur
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/supplier-scoring/suppliers/101

# Critères de scoring
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/supplier-scoring/criteria

# Mettre à jour les critères
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"weights": {"price_stability": 0.3, ...}}' \
  http://localhost:8000/supplier-scoring/criteria

# Alertes
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/supplier-scoring/alerts?severity=critical&acknowledged=false"

# Recalculer les scores
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"period_days": 90, "force": false}' \
  http://localhost:8000/supplier-scoring/recalculate
```

## Fichiers créés/modifiés

1. **backend/schemas/supplier_scoring.py** - Schémas Pydantic complets
2. **backend/api/supplier_scoring.py** - Tous les endpoints avec ResponseWrapper
3. **core/finance/supplier_scoring.py** - Logique métier (existante, inchangée)

## Prochaines étapes

1. Implémenter la récupération réelle des fournisseurs depuis la DB (actuellement mockée)
2. Ajouter une table de configuration pour les pondérations personnalisées par tenant
3. Implémenter un système d'alertes persistant en DB
4. Ajouter des endpoints pour acquitter les alertes
5. Créer des hooks pour recalculer automatiquement les scores après certains événements
6. Ajouter des graphiques de tendance dans la réponse
7. Implémenter un cache Redis pour les scores fréquemment consultés
