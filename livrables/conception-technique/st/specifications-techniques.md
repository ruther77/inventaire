# Specifications techniques (ST)

## 1. Conventions API
- Base URL: / (ou /api pour newCMS).
- JSON UTF-8, dates ISO-8601.
- Erreurs: 400, 401, 403, 404, 422, 500.
- Pagination: page, size + header X-Total-Count.
- Correlation ID: X-Request-Id.

## 2. Authentification / Autorisation
- OAuth2 + JWT.
- Header Authorization: Bearer <token>.
- RBAC par module.

## 3. Prefixes d’API par domaine (alignes avec backend/main.py)
### Opérations
- /catalog/*
- /stock/*
- /invoices/*
- /prices/*
- /supply/*
- /audit/*
- /reports/*
- /maintenance/*
- /eurociel/*
- /data-quality/*

### Restaurant
- /restaurant/*

### Finance
- /finance/*
- /bank-reconciliation/*
- /rules-engine/*
- /audit-trail/*
- /capital/*
- /analytics/*

### Intelligence
- /inventory-intelligence/*
- /forecasting/*
- /anomaly-detection/*
- /margins/*

### Tableau de bord
- /cockpit/*
- /dashboard/*

### Admin
- /admin/*

### NewCMS (demo)
- /api/finance/*
- /api/operations/*
- /api/intelligence/*
- /api/cockpit/*

## 4. Endpoints generiques exposes
- GET /health
- GET /metrics/performance
- GET /metrics/cache
- POST /cache/invalidate/{pattern}
- GET /products
- PATCH /products/{product_id}
- GET /inventory/summary
- POST /pos/checkout

## 5. Regles techniques transverses
- Multi-tenant via tenant_id cote serveur.
- Idempotency-Key pour operations critiques (ex: factures).
- Validation stricte des schemas Pydantic.

## 6. Schema d’erreur
```
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Champ manquant",
    "details": [{"field":"name","issue":"required"}]
  }
}
```

## 7. Taches asynchrones
- Import factures : extraction -> rapprochement -> validation.
- Notation fournisseurs : recalcul periodique.
- Previsions : regeneration cache.
- Anomalies : detection batch.

## 8. Observabilite
- Journaux structures par module et tenant.
- Metriques performance par endpoint.
