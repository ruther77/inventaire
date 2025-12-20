# NewCMS Cockpit API - Morning Brief

Documentation des endpoints `/newcms/cockpit` pour le Morning Brief agrégé.

## Endpoints créés

### 1. GET `/newcms/cockpit`
**Description**: Vue agrégée complète du Morning Brief - toutes les données en un seul appel

**Paramètres query**:
- `days_forecast` (optional, default: 7): Horizon de prévision en jours (1-30)
- `top_anomalies_limit` (optional, default: 5): Nombre d'anomalies à afficher (1-20)

**Exemple requête**:
```bash
curl -X GET "http://localhost:8000/newcms/cockpit?days_forecast=7&top_anomalies_limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Réponse** (format ResponseWrapper):
```json
{
  "success": true,
  "data": {
    "timestamp": "2025-12-11T21:30:00",
    "tenant_id": 1,
    "tenant_name": "Epicerie",
    "kpis": {
      "stock_value": {
        "key": "stock_value",
        "label": "Valeur Stock",
        "value": 15234.50,
        "unit": "EUR",
        "status": "info",
        "icon": "warehouse",
        "description": "245 references"
      },
      "stock_alerts": {
        "key": "stock_alerts",
        "label": "Alertes Stock",
        "value": 12,
        "status": "warning",
        "icon": "alert-triangle",
        "description": "3 ruptures, 9 bas"
      },
      "margin_avg": {
        "key": "margin_avg",
        "label": "Marge Moyenne",
        "value": 28.5,
        "unit": "%",
        "status": "warning",
        "icon": "trending-up",
        "description": "15 alertes"
      },
      "cash_flow_7d": {
        "key": "cash_flow_7d",
        "label": "Flux Net 7j",
        "value": 2345.80,
        "unit": "EUR",
        "status": "success",
        "icon": "dollar-sign",
        "description": "Entrees: 5600 EUR"
      },
      "anomalies_count": {
        "key": "anomalies_count",
        "label": "Anomalies",
        "value": 8,
        "status": "warning",
        "icon": "alert-circle",
        "description": "2 critiques"
      },
      "match_rate": {
        "key": "match_rate",
        "label": "Rapprochement",
        "value": 82.5,
        "unit": "%",
        "status": "warning",
        "icon": "check-circle",
        "description": "35 en attente"
      }
    },
    "alerts": [
      {
        "id": "stock-outage-1702334567.123",
        "severity": "critical",
        "category": "stock",
        "title": "Ruptures de stock",
        "message": "3 produits en rupture de stock",
        "entity_type": null,
        "entity_id": null,
        "created_at": "2025-12-11T21:00:00",
        "acknowledged": false,
        "action_url": "/inventory?status=critical",
        "impact_value": null
      },
      {
        "id": "margin-low-1702334567.456",
        "severity": "warning",
        "category": "margin",
        "title": "Marges faibles",
        "message": "15 produits avec marge < 20%",
        "entity_type": null,
        "entity_id": null,
        "created_at": "2025-12-11T21:00:00",
        "acknowledged": false,
        "action_url": "/intelligence/margins",
        "impact_value": null
      }
    ],
    "alerts_summary": {
      "critical": 2,
      "warning": 5,
      "info": 1
    },
    "top_anomalies": [
      {
        "id": "anomaly-tx-123",
        "type": "amount_outlier",
        "severity": "high",
        "description": "Transaction de 5000 EUR (3x la moyenne)",
        "impact": 5000.0,
        "detected_at": "2025-12-11T20:00:00",
        "entity_type": "transaction",
        "entity_id": 123
      },
      {
        "id": "anomaly-inv-456",
        "type": "duplicate",
        "severity": "medium",
        "description": "Facture potentiellement en double",
        "impact": 234.50,
        "detected_at": "2025-12-11T19:30:00",
        "entity_type": "invoice",
        "entity_id": 456
      }
    ],
    "cash_flow_forecast_7d": {
      "period_start": "2025-12-12",
      "period_end": "2025-12-18",
      "predictions": [
        {
          "date": "2025-12-12",
          "value": 250.50,
          "lower_bound": 225.45,
          "upper_bound": 275.55
        },
        {
          "date": "2025-12-13",
          "value": 310.20,
          "lower_bound": 279.18,
          "upper_bound": 341.22
        }
      ],
      "total_inflows": 3500.0,
      "total_outflows": 2800.0,
      "net_flow": 700.0,
      "ending_balance": 5200.0,
      "alerts": []
    },
    "stock_depletion_forecast": [
      {
        "product_id": 42,
        "product_name": "Lait demi-écrémé",
        "current_stock": 8,
        "days_until_depletion": 3.2,
        "predicted_depletion_date": "2025-12-14",
        "recommended_reorder_date": "2025-12-12",
        "confidence": 0.85
      },
      {
        "product_id": 78,
        "product_name": "Pain complet",
        "current_stock": 12,
        "days_until_depletion": 5.5,
        "predicted_depletion_date": "2025-12-16",
        "recommended_reorder_date": "2025-12-13",
        "confidence": 0.78
      }
    ],
    "ai_suggestions": [
      {
        "id": "reorder-urgent-1702334567.789",
        "type": "reorder",
        "priority": "high",
        "title": "Réapprovisionnement urgent",
        "description": "3 produits en rupture nécessitent une commande immédiate",
        "impact_estimate": "Éviter 150 EUR de ventes perdues",
        "action_url": "/inventory?status=critical",
        "confidence": 0.9,
        "created_at": "2025-12-11T21:30:00"
      },
      {
        "id": "reconciliation-1702334567.012",
        "type": "reconciliation",
        "priority": "high",
        "title": "Rapprochement bancaire en retard",
        "description": "35 transactions non rapprochées",
        "impact_estimate": "Améliorer la visibilité trésorerie",
        "action_url": "/tresorerie/anomalies",
        "confidence": 0.95,
        "created_at": "2025-12-11T21:30:00"
      },
      {
        "id": "dead-stock-1702334567.345",
        "type": "dead_stock",
        "priority": "medium",
        "title": "Stock mort à liquider",
        "description": "25 produits immobilisés (3200 EUR)",
        "impact_estimate": "Récupérer 2240 EUR de trésorerie",
        "action_url": "/intelligence/inventory",
        "confidence": 0.85,
        "created_at": "2025-12-11T21:30:00"
      }
    ],
    "health_score": 78.5,
    "health_status": "warning"
  },
  "error": null,
  "meta": {
    "request_id": "req_abc123",
    "duration_ms": 342.5
  }
}
```

**Contenu de la réponse**:
- **kpis**: 6 métriques clés (stock_value, stock_alerts, margin_avg, cash_flow_7d, anomalies_count, match_rate)
- **alerts**: Top 10 alertes actives triées par sévérité
- **alerts_summary**: Résumé par niveau (critical, warning, info)
- **top_anomalies**: Top 5 anomalies détectées
- **cash_flow_forecast_7d**: Prévision trésorerie 7 jours
- **stock_depletion_forecast**: Produits en épuisement imminent (<7j)
- **ai_suggestions**: Top 5 suggestions IA actionnables
- **health_score**: Score global 0-100
- **health_status**: Status (healthy, warning, critical)

---

### 2. GET `/newcms/cockpit/actions`
**Description**: Liste des Call-to-Actions (CTAs) pour l'utilisateur

**Paramètres query**:
- `category` (optional): Filtrer par catégorie (urgent|important|suggested)

**Exemple requêtes**:
```bash
# Toutes les actions
curl -X GET "http://localhost:8000/newcms/cockpit/actions" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Uniquement les urgentes
curl -X GET "http://localhost:8000/newcms/cockpit/actions?category=urgent" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Réponse** (format ResponseWrapper):
```json
{
  "success": true,
  "data": {
    "timestamp": "2025-12-11T21:30:00",
    "total_actions": 6,
    "urgent_count": 2,
    "important_count": 2,
    "suggested_count": 2,
    "actions": [
      {
        "id": "urgent-reorder-1702334567.123",
        "type": "reorder_product",
        "category": "urgent",
        "title": "Commander produits en rupture",
        "description": "3 produits en rupture nécessitent une commande urgente",
        "action_url": "/inventory?status=critical",
        "action_label": "Commander maintenant",
        "entity_type": "stock",
        "entity_id": null,
        "deadline": "2025-12-12T21:30:00",
        "estimated_duration": "5 min"
      },
      {
        "id": "urgent-anomalies-1702334567.456",
        "type": "acknowledge_alert",
        "category": "urgent",
        "title": "Traiter anomalies critiques",
        "description": "2 anomalies critiques détectées",
        "action_url": "/intelligence/anomalies?severity=critical",
        "action_label": "Voir les anomalies",
        "entity_type": "anomaly",
        "entity_id": null,
        "deadline": "2025-12-13T21:30:00",
        "estimated_duration": "10 min"
      },
      {
        "id": "important-reconcile-1702334567.789",
        "type": "reconcile_transaction",
        "category": "important",
        "title": "Rapprocher transactions bancaires",
        "description": "35 transactions en attente de rapprochement",
        "action_url": "/tresorerie/anomalies",
        "action_label": "Rapprocher",
        "entity_type": "finance",
        "entity_id": null,
        "deadline": "2025-12-18T21:30:00",
        "estimated_duration": "15 min"
      },
      {
        "id": "important-import-invoices-1702334567.012",
        "type": "import_invoice",
        "category": "important",
        "title": "Importer factures en attente",
        "description": "8 factures à importer (1250 EUR)",
        "action_url": "/invoices/import",
        "action_label": "Importer",
        "entity_type": "invoice",
        "entity_id": null,
        "deadline": null,
        "estimated_duration": "10 min"
      },
      {
        "id": "suggested-dead-stock-1702334567.345",
        "type": "reorder_product",
        "category": "suggested",
        "title": "Liquider stock mort",
        "description": "25 produits immobilisés (3200 EUR)",
        "action_url": "/intelligence/inventory",
        "action_label": "Voir le stock mort",
        "entity_type": "stock",
        "entity_id": null,
        "deadline": null,
        "estimated_duration": "20 min"
      },
      {
        "id": "suggested-optimize-margins-1702334567.678",
        "type": "acknowledge_alert",
        "category": "suggested",
        "title": "Optimiser les marges",
        "description": "15 produits avec marge < 20%",
        "action_url": "/intelligence/margins",
        "action_label": "Analyser",
        "entity_type": "margin",
        "entity_id": null,
        "deadline": null,
        "estimated_duration": "15 min"
      }
    ]
  },
  "error": null,
  "meta": {
    "request_id": "req_xyz789",
    "duration_ms": 125.3
  }
}
```

**Catégories d'actions**:
- **urgent**: À traiter immédiatement (ruptures stock, anomalies critiques)
- **important**: Important mais non bloquant (rapprochement, import factures)
- **suggested**: Suggestions d'amélioration (stock mort, optimisation marges)

**Types d'actions**:
- `reorder_product`: Réapprovisionner un produit
- `acknowledge_alert`: Acquitter/traiter une alerte
- `import_invoice`: Importer des factures
- `reconcile_transaction`: Rapprocher des transactions

---

## Services Réutilisés

Le module **newCMS Cockpit** réutilise les services existants:

### Backend Services
- `backend.api.cockpit._get_stock_summary()` - Résumé stock
- `backend.api.cockpit._get_margin_summary()` - Résumé marges
- `backend.api.cockpit._get_treasury_summary()` - Résumé trésorerie
- `backend.api.cockpit._get_intelligence_summary()` - Résumé intelligence
- `backend.api.cockpit._build_alerts()` - Construction alertes
- `backend.api.cockpit._calculate_health_score()` - Score santé
- `backend.api.anomaly_detection.scan_for_anomalies()` - Détection anomalies
- `backend.api.forecasting.forecast_cash_flow()` - Prévision trésorerie
- `backend.api.forecasting.forecast_stock_depletion()` - Prévision stock

### Avantages
- **Pas de duplication SQL** - Maintenance simplifiée
- **Cohérence** - Mêmes calculs partout
- **Performance** - Services déjà optimisés
- **Évolutivité** - Modifications propagées automatiquement

---

## Format ResponseWrapper

Toutes les réponses suivent le format standardisé:

```json
{
  "success": true,           // Boolean - succès ou échec
  "data": { ... },          // Object - données métier
  "error": null,            // Object | null - détails erreur
  "meta": {                 // Object - métadonnées
    "request_id": "...",    // String - ID unique requête
    "duration_ms": 123.45   // Number - temps de traitement
  }
}
```

### En cas d'erreur:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Paramètre invalide",
    "suggestion": "Vérifiez les paramètres de la requête"
  },
  "meta": {
    "request_id": "req_error_123",
    "duration_ms": 5.2
  }
}
```

---

## Conventions de Nommage

### Endpoints
- **kebab-case**: `/newcms/cockpit`, `/cockpit/actions`

### JSON keys
- **snake_case**: `stock_value`, `cash_flow_7d`, `ai_suggestions`

### Status KPI
- `success` - Vert (bon)
- `warning` - Orange (attention)
- `error` - Rouge (critique)
- `info` - Bleu (information)

### Sévérité Alertes
- `critical` - Critique (rouge)
- `warning` - Avertissement (orange)
- `info` - Information (bleu)

### Catégories Actions
- `urgent` - À traiter immédiatement
- `important` - Important mais pas bloquant
- `suggested` - Suggestion d'amélioration

### Priorités Suggestions
- `high` - Priorité haute
- `medium` - Priorité moyenne
- `low` - Priorité basse

---

## Tests Manuels

```bash
# 1. Obtenir un token
TOKEN=$(curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret" \
  | jq -r '.access_token')

# 2. Morning Brief complet (défaut: 7j forecast, top 5 anomalies)
curl -X GET "http://localhost:8000/newcms/cockpit" \
  -H "Authorization: Bearer $TOKEN" \
  | jq .

# 3. Morning Brief avec paramètres personnalisés
curl -X GET "http://localhost:8000/newcms/cockpit?days_forecast=14&top_anomalies_limit=10" \
  -H "Authorization: Bearer $TOKEN" \
  | jq .

# 4. Toutes les actions
curl -X GET "http://localhost:8000/newcms/cockpit/actions" \
  -H "Authorization: Bearer $TOKEN" \
  | jq .

# 5. Actions urgentes uniquement
curl -X GET "http://localhost:8000/newcms/cockpit/actions?category=urgent" \
  -H "Authorization: Bearer $TOKEN" \
  | jq .

# 6. Actions importantes
curl -X GET "http://localhost:8000/newcms/cockpit/actions?category=important" \
  -H "Authorization: Bearer $TOKEN" \
  | jq .

# 7. Suggestions
curl -X GET "http://localhost:8000/newcms/cockpit/actions?category=suggested" \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
```

### Avec httpie (plus lisible)
```bash
# Morning Brief
http GET localhost:8000/newcms/cockpit \
  Authorization:"Bearer $TOKEN"

# Actions urgentes
http GET localhost:8000/newcms/cockpit/actions \
  category==urgent \
  Authorization:"Bearer $TOKEN"
```

---

## Performance

### Objectifs
- **< 500ms** pour `/newcms/cockpit`
- **< 150ms** pour `/newcms/cockpit/actions`

### Optimisations
- Réutilisation services existants (pas de requêtes SQL supplémentaires)
- Limitation des résultats (top 10 alertes, top 5 anomalies)
- Pas de cache (pour données temps réel)
- Exécution séquentielle des helper functions (à optimiser en parallèle si besoin)

### Recommandations Frontend
- **Refresh toutes les 60s** pour le Morning Brief
- **Cache local** côté frontend (30-60s)
- **Polling** plutôt que WebSocket (pour v1)
- **Lazy loading** des graphiques

---

## Évolutions Futures

### Version 2.0
- [ ] Cache Redis pour améliorer les performances
- [ ] Exécution parallèle des helper functions (asyncio.gather)
- [ ] WebSocket pour updates temps réel
- [ ] Notifications push pour actions urgentes
- [ ] Personnalisation des KPIs affichés

### Version 3.0
- [ ] Export PDF du Morning Brief
- [ ] Dashboard builder personnalisé
- [ ] ML/AI pour améliorer prévisions
- [ ] Automatisation des actions (règles)
- [ ] Multi-langue (i18n)

---

**Dernière mise à jour**: 2025-12-11
**Version**: 1.0.0
**Auteur**: Expert Backend Cockpit
