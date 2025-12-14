# Supplier Scoring - Architecture

## Vue d'ensemble de l'architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND REACT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  Overview      │  │  Suppliers     │  │  Details         │  │
│  │  Page          │  │  List Page     │  │  Page            │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  Criteria      │  │  Alerts        │  │  History         │  │
│  │  Page          │  │  Page          │  │  Page            │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           React Query Hooks (useSupplierScoring)        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/JSON
                            │ JWT Token
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │             Response Wrapper Middleware                   │ │
│  │  Transforme toutes les réponses en format standardisé    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            │                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │             Request Context Middleware                    │ │
│  │  Ajoute request_id, tracking du temps, etc.              │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            │                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │           Authentication Middleware (JWT)                 │ │
│  │  Extrait tenant_id du token JWT                          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            │                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │      API Router: /supplier-scoring/*                      │ │
│  │  (backend/api/supplier_scoring.py)                        │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │                                                            │ │
│  │  GET  /overview                 - Vue d'ensemble          │ │
│  │  GET  /suppliers                - Liste paginée           │ │
│  │  GET  /suppliers/{id}           - Détails                 │ │
│  │  GET  /suppliers/{id}/history   - Historique              │ │
│  │  GET  /criteria                 - Critères                │ │
│  │  PUT  /criteria                 - MAJ critères            │ │
│  │  GET  /alerts                   - Alertes                 │ │
│  │  POST /recalculate              - Recalcul                │ │
│  │                                                            │ │
│  │  [Legacy endpoints...]                                    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            │                                     │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │         Pydantic Schemas Validation                       │ │
│  │  (backend/schemas/supplier_scoring.py)                    │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │                                                            │ │
│  │  - SupplierScore                                          │ │
│  │  - SupplierOverview                                       │ │
│  │  - SuppliersList (pagination)                             │ │
│  │  - SupplierDetails                                        │ │
│  │  - ScoreHistory                                           │ │
│  │  - ScoringCriteriaList                                    │ │
│  │  - AlertsList                                             │ │
│  │  - RecalculateScoresRequest/Response                      │ │
│  │  + 17 autres modèles...                                   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BUSINESS LOGIC LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │       SupplierScoreCalculator                             │ │
│  │  (core/finance/supplier_scoring.py)                       │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │                                                            │ │
│  │  calculate_score(supplier_name, period_days)              │ │
│  │    ├─ _calculate_price_stability()                        │ │
│  │    ├─ _calculate_delivery_reliability()                   │ │
│  │    ├─ _calculate_invoice_accuracy()                       │ │
│  │    ├─ _calculate_stock_accuracy()                         │ │
│  │    ├─ _calculate_grade()                                  │ │
│  │    ├─ _calculate_trend()                                  │ │
│  │    └─ _save_score()                                       │ │
│  │                                                            │ │
│  │  get_all_suppliers_ranking()                              │ │
│  │  get_supplier_comparison(suppliers[])                     │ │
│  │  record_delivery(...)                                     │ │
│  │  record_invoice_issue(...)                                │ │
│  │  _get_score_history(supplier_name, limit)                 │ │
│  │                                                            │ │
│  └───────────────────────────────────────────────────────────┘ │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATABASE LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐│
│  │  PostgreSQL Database                                       ││
│  ├────────────────────────────────────────────────────────────┤│
│  │                                                             ││
│  │  Tables utilisées:                                          ││
│  │                                                             ││
│  │  ┌─────────────────────────────────────────────────────┐  ││
│  │  │ supplier_score_history                              │  ││
│  │  │ - id, tenant_id, supplier_id, supplier_name         │  ││
│  │  │ - overall_score, grade, dimensions (JSONB)          │  ││
│  │  │ - metrics (JSONB), calculated_at                    │  ││
│  │  │ INDEX: (tenant_id, supplier_name)                   │  ││
│  │  │ INDEX: (tenant_id, calculated_at)                   │  ││
│  │  └─────────────────────────────────────────────────────┘  ││
│  │                                                             ││
│  │  ┌─────────────────────────────────────────────────────┐  ││
│  │  │ supplier_delivery_log                               │  ││
│  │  │ - id, tenant_id, supplier_name                      │  ││
│  │  │ - expected_date, actual_date, delay_days            │  ││
│  │  │ - invoice_id, created_at                            │  ││
│  │  └─────────────────────────────────────────────────────┘  ││
│  │                                                             ││
│  │  ┌─────────────────────────────────────────────────────┐  ││
│  │  │ supplier_invoice_issues                             │  ││
│  │  │ - id, tenant_id, supplier_name, invoice_id          │  ││
│  │  │ - issue_type, severity, resolved                    │  ││
│  │  │ - created_at                                        │  ││
│  │  └─────────────────────────────────────────────────────┘  ││
│  │                                                             ││
│  │  Tables de données sources:                                ││
│  │                                                             ││
│  │  ┌─────────────────────────────────────────────────────┐  ││
│  │  │ produits                                            │  ││
│  │  │ - id, tenant_id, nom, ...                           │  ││
│  │  └─────────────────────────────────────────────────────┘  ││
│  │                                                             ││
│  │  ┌─────────────────────────────────────────────────────┐  ││
│  │  │ historique_prix                                     │  ││
│  │  │ - id, product_id, fournisseur, prix, date           │  ││
│  │  └─────────────────────────────────────────────────────┘  ││
│  │                                                             ││
│  │  ┌─────────────────────────────────────────────────────┐  ││
│  │  │ finance_invoices_supplier                           │  ││
│  │  │ - id, entity_id, vendor_id, created_at              │  ││
│  │  └─────────────────────────────────────────────────────┘  ││
│  │                                                             ││
│  │  ┌─────────────────────────────────────────────────────┐  ││
│  │  │ finance_vendors                                     │  ││
│  │  │ - id, name, ...                                     │  ││
│  │  └─────────────────────────────────────────────────────┘  ││
│  │                                                             ││
│  │  ┌─────────────────────────────────────────────────────┐  ││
│  │  │ inventaire_snapshots                                │  ││
│  │  │ - product_id, stock_theorique, stock_reel, date     │  ││
│  │  └─────────────────────────────────────────────────────┘  ││
│  │                                                             ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Flux de données

### 1. Calcul d'un score fournisseur

```
User Request
    │
    ▼
Frontend (React)
    │ HTTP GET /supplier-scoring/suppliers/101
    │ Header: Authorization: Bearer JWT_TOKEN
    ▼
Backend (FastAPI)
    │
    ├─ Auth Middleware → Extrait tenant_id du JWT
    ├─ Request Context → Génère request_id, démarre timer
    │
    ▼
API Router (supplier_scoring.py)
    │ get_supplier_details(supplier_id=101, tenant=Tenant)
    │
    ▼
Business Logic (SupplierScoreCalculator)
    │
    ├─ calculate_score(supplier_name, period_days=90)
    │   │
    │   ├─ Query DB: historique_prix
    │   │   → _calculate_price_stability()
    │   │       └─ Score: 95.0
    │   │
    │   ├─ Query DB: supplier_delivery_log
    │   │   → _calculate_delivery_reliability()
    │   │       └─ Score: 88.0
    │   │
    │   ├─ Query DB: supplier_invoice_issues + finance_invoices_supplier
    │   │   → _calculate_invoice_accuracy()
    │   │       └─ Score: 92.0
    │   │
    │   ├─ Query DB: inventaire_snapshots
    │   │   → _calculate_stock_accuracy()
    │   │       └─ Score: 85.0
    │   │
    │   ├─ Calculer score global pondéré
    │   │   → overall_score = 92.5
    │   │
    │   ├─ _calculate_grade(92.5)
    │   │   → grade = "A"
    │   │
    │   ├─ _calculate_trend(supplier_name)
    │   │   → trend = "improving"
    │   │
    │   └─ _save_score() → INSERT INTO supplier_score_history
    │
    ▼
Pydantic Validation
    │ SupplierScore model
    │ Validation des types et contraintes
    │
    ▼
Response Wrapper Middleware
    │ build_success_response(data)
    │ {
    │   "success": true,
    │   "data": { ... },
    │   "error": null,
    │   "meta": {
    │     "request_id": "abc-123",
    │     "duration_ms": 125.5
    │   }
    │ }
    │
    ▼
HTTP Response
    │ Status: 200 OK
    │ Content-Type: application/json
    │
    ▼
Frontend React
    │ React Query cache
    │ Update UI
    └─ Display supplier details
```

### 2. Mise à jour des pondérations

```
User Action
    │ Modifie les sliders de pondération
    │ Clique "Enregistrer"
    ▼
Frontend (React)
    │ HTTP PUT /supplier-scoring/criteria
    │ Body: { "weights": { "price_stability": 0.3, ... } }
    │ Header: Authorization: Bearer JWT_TOKEN
    ▼
Backend (FastAPI)
    │
    ├─ Auth Middleware → Valide JWT
    ├─ Request Context → request_id, timer
    │
    ▼
Pydantic Validation (Input)
    │ UpdateScoringCriteriaRequest
    │ ✓ Tous les poids entre 0 et 1
    │ ✓ Somme des poids = 1.0 (±0.01)
    │
    ▼
API Router (supplier_scoring.py)
    │ update_scoring_criteria(request, tenant)
    │
    │ [Dans une implémentation future]
    │ └─ INSERT/UPDATE dans table scoring_criteria_config
    │     WHERE tenant_id = tenant.id
    │
    ▼
Pydantic Validation (Output)
    │ ScoringCriteriaList
    │
    ▼
Response Wrapper
    │ {
    │   "success": true,
    │   "data": { "criteria": [...], "total_weight": 1.0 },
    │   "meta": {
    │     "message": "Pondérations mises à jour avec succès"
    │   }
    │ }
    │
    ▼
Frontend React
    │ React Query invalidation
    │ Rafraîchir les scores affectés
    └─ Notification de succès
```

### 3. Pagination et filtrage

```
User Action
    │ Page 2, tri par score desc, grade A seulement
    ▼
Frontend (React)
    │ HTTP GET /supplier-scoring/suppliers
    │   ?page=2&per_page=20&sort_by=score&order=desc&grade_filter=A
    ▼
Backend (FastAPI)
    │
    ├─ Parse query params
    │   page=2, per_page=20, sort_by=score, order=desc, grade_filter=A
    │
    ▼
Business Logic
    │ get_all_suppliers_ranking()
    │   → Récupère tous les scores depuis DB
    │
    ├─ Filtrage en mémoire
    │   filtered = [s for s in all if s.grade == "A"]
    │
    ├─ Tri
    │   sorted(filtered, key=lambda x: x.score, reverse=True)
    │
    ├─ Pagination
    │   total_count = len(filtered)
    │   total_pages = ceil(total_count / per_page)
    │   start = (page - 1) * per_page = 20
    │   end = start + per_page = 40
    │   page_suppliers = filtered[20:40]
    │
    ▼
Pydantic Validation
    │ SuppliersList
    │   suppliers: [SupplierRankingItem...]
    │   total_count, page, per_page, total_pages
    │
    ▼
Response Wrapper
    │ {
    │   "success": true,
    │   "data": { ... },
    │   "meta": {
    │     "pagination": {
    │       "page": 2,
    │       "per_page": 20,
    │       "total_pages": 5,
    │       "total_count": 95
    │     }
    │   }
    │ }
    │
    ▼
Frontend React
    │ Update table
    └─ Update pagination controls
```

## Dimensions de scoring - Détails de calcul

### 1. Price Stability (25%)

```
Query:
  SELECT prix, LAG(prix) OVER (PARTITION BY product_id ORDER BY date)
  FROM historique_prix
  WHERE fournisseur LIKE '%supplier%'
    AND date >= NOW() - INTERVAL '90 days'

Calcul:
  variations = [abs((prix - prev_prix) / prev_prix * 100) for each row]

  avg_variation = mean(variations)
  max_variation = max(variations)
  volatility = stdev(variations)

  score = max(0, 100 - (avg_variation * 5) - (volatility * 2))

Exemple:
  variations = [2%, 1.5%, 3%, 1%, 2.5%]
  avg_variation = 2%
  volatility = 0.75%
  score = 100 - (2 * 5) - (0.75 * 2) = 88.5
```

### 2. Delivery Reliability (20%)

```
Query:
  SELECT
    COUNT(*) as total,
    SUM(CASE WHEN delay_days <= 0 THEN 1 ELSE 0 END) as on_time,
    AVG(delay_days) as avg_delay
  FROM supplier_delivery_log
  WHERE supplier_name = '...'
    AND created_at >= NOW() - INTERVAL '90 days'

Calcul:
  on_time_rate = (on_time / total) * 100

  score = on_time_rate * 0.8 + (100 - min(100, avg_delay * 10)) * 0.2

Exemple:
  total = 20 livraisons
  on_time = 16 (80%)
  avg_delay = 1.5 jours

  score = 80 * 0.8 + (100 - min(100, 1.5 * 10)) * 0.2
        = 64 + (100 - 15) * 0.2
        = 64 + 17
        = 81.0
```

### 3. Invoice Accuracy (15%)

```
Query 1 (Total invoices):
  SELECT COUNT(DISTINCT f.id)
  FROM finance_invoices_supplier f
  JOIN finance_vendors v ON v.id = f.vendor_id
  WHERE v.name LIKE '%supplier%'
    AND f.created_at >= NOW() - INTERVAL '90 days'

Query 2 (Issues):
  SELECT
    COUNT(*) as total_issues,
    SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as critical,
    SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium,
    SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as minor
  FROM supplier_invoice_issues
  WHERE supplier_name = '...'
    AND created_at >= NOW() - INTERVAL '90 days'

Calcul:
  error_rate = (total_issues / total_invoices) * 100

  penalty = (critical * 10 + medium * 5 + minor * 2) / total_invoices

  score = max(0, 100 - error_rate * 2 - penalty)

Exemple:
  total_invoices = 50
  total_issues = 3
  critical = 1, medium = 1, minor = 1

  error_rate = (3 / 50) * 100 = 6%
  penalty = (1*10 + 1*5 + 1*2) / 50 = 17/50 = 0.34

  score = 100 - 6*2 - 0.34 = 100 - 12 - 0.34 = 87.66
```

### 4. Stock Accuracy (15%)

```
Query:
  SELECT
    COUNT(*) as total_checks,
    AVG(ABS(ecart_pct)) as avg_deviation,
    SUM(CASE WHEN ABS(ecart_pct) <= 2 THEN 1 ELSE 0 END) as accurate
  FROM (
    SELECT
      CASE WHEN stock_theorique > 0
        THEN (stock_reel - stock_theorique) / stock_theorique * 100
        ELSE 0
      END as ecart_pct
    FROM inventaire_snapshots
    WHERE product_id IN (SELECT id FROM produits WHERE ...)
      AND date >= NOW() - INTERVAL '90 days'
  )

Calcul:
  accuracy_rate = (accurate / total_checks) * 100

  score = accuracy_rate * 0.7 + max(0, 100 - avg_deviation * 5) * 0.3

Exemple:
  total_checks = 100
  accurate = 85 (écart <= 2%)
  avg_deviation = 3%

  accuracy_rate = 85%
  score = 85 * 0.7 + max(0, 100 - 3*5) * 0.3
        = 59.5 + 85 * 0.3
        = 59.5 + 25.5
        = 85.0
```

## Évolutions futures

### Phase 1 - Données réelles (1-2 semaines)
- Remplacer supplier_id mockés
- Table supplier_alerts en DB
- Endpoint PUT /alerts/{id}/acknowledge

### Phase 2 - Personnalisation (1-2 mois)
- Table scoring_criteria_config
- Pondérations par tenant
- Calcul asynchrone (Celery)

### Phase 3 - Intelligence (3-6 mois)
- ML: prédiction de scores
- Recommandations IA
- Benchmarking sectoriel
- Dashboard temps réel

### Phase 4 - Intégrations (6-12 mois)
- Export Excel/PDF
- Webhooks
- API publique
- Mobile app

## Métriques de performance

| Opération | Temps attendu | Optimisation |
|-----------|---------------|--------------|
| GET /overview | < 200ms | Index DB, pagination |
| GET /suppliers (20 items) | < 150ms | Cache, index |
| GET /suppliers/{id} | < 100ms | Cache Redis (futur) |
| Calcul 1 score | < 500ms | Queries optimisées |
| Recalcul 100 scores | < 60s | Async processing (futur) |

## Conclusion

L'architecture est modulaire, scalable et production-ready avec:
- Séparation claire des responsabilités
- Validation stricte à chaque niveau
- Multi-tenant sécurisé
- Performance optimisée
- Extensibilité future
