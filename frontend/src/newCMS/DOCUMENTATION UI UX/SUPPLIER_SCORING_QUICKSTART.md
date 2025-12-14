# Supplier Scoring - Quick Start Guide

## Démarrage rapide en 5 minutes

### Prérequis

- Backend FastAPI en cours d'exécution
- Token JWT valide
- PostgreSQL avec les tables nécessaires

---

## 1. Vérifier que tout est en place

```bash
# Vérifier que les fichiers existent
ls backend/api/supplier_scoring.py
ls backend/schemas/supplier_scoring.py
ls tests/test_supplier_scoring_api.py

# Tous doivent retourner les chemins sans erreur
```

---

## 2. Lancer le serveur Backend

```bash
# Si ce n'est pas déjà fait
cd /home/ruuuzer/Documents/monprojet

# Option 1: Uvicorn directement
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Docker Compose (si configuré)
docker-compose up backend
```

Le serveur démarre sur: `http://localhost:8000`

---

## 3. Obtenir un token JWT

```bash
# Exemple: Se connecter pour obtenir un token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "votre_username",
    "password": "votre_password"
  }'

# Réponse attendue:
# {
#   "success": true,
#   "data": {
#     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#     "token_type": "bearer"
#   }
# }

# Sauvegarder le token dans une variable
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 4. Tester les endpoints principaux

### 4.1 Vue d'ensemble

```bash
curl -X GET http://localhost:8000/supplier-scoring/overview \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse attendue:**
```json
{
  "success": true,
  "data": {
    "total_suppliers": 0,
    "average_score": 0.0,
    "score_distribution": {
      "A": 0,
      "B": 0,
      "C": 0,
      "D": 0,
      "F": 0
    },
    "top_suppliers": [],
    "bottom_suppliers": [],
    "trends": {
      "message": "Aucune donnée disponible"
    },
    "alerts_summary": {
      "info": 0,
      "warning": 0,
      "critical": 0
    }
  },
  "error": null,
  "meta": {
    "request_id": "...",
    "duration_ms": 50.25
  }
}
```

---

### 4.2 Liste des fournisseurs (paginée)

```bash
curl -X GET "http://localhost:8000/supplier-scoring/suppliers?page=1&per_page=20&sort_by=score&order=desc" \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse attendue:**
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
          ...
        },
        "last_updated": "2025-12-11T10:30:00Z",
        "trend": "stable"
      }
    ],
    "total_count": 0,
    "page": 1,
    "per_page": 20,
    "total_pages": 0
  },
  "meta": {
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total_pages": 0,
      "total_count": 0
    }
  }
}
```

---

### 4.3 Détails d'un fournisseur

```bash
curl -X GET http://localhost:8000/supplier-scoring/suppliers/101 \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse attendue:**
```json
{
  "success": true,
  "data": {
    "supplier_id": 101,
    "supplier_name": "Supplier_101",
    "current_score": {
      "supplier_id": 101,
      "supplier_name": "Supplier_101",
      "overall_score": 80.0,
      "grade": "B",
      "delivery_score": 80.0,
      "quality_score": 80.0,
      "price_score": 80.0,
      "reliability_score": 80.0,
      "trend": "stable",
      "last_updated": "2025-12-11T10:45:00Z",
      "dimensions": { ... },
      "metrics": { ... }
    },
    "history": [ ... ],
    "recent_deliveries": [ ... ],
    "recent_issues": [ ... ],
    "alerts": [ ... ],
    "statistics": { ... },
    "recommendations": [ ... ]
  }
}
```

---

### 4.4 Critères de scoring

```bash
curl -X GET http://localhost:8000/supplier-scoring/criteria \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse attendue:**
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
      },
      ...
    ],
    "total_weight": 1.0
  }
}
```

---

### 4.5 Alertes

```bash
curl -X GET "http://localhost:8000/supplier-scoring/alerts?severity=critical&acknowledged=false" \
  -H "Authorization: Bearer $TOKEN"
```

**Réponse attendue:**
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
    "total_count": 1,
    "unacknowledged_count": 1
  }
}
```

---

## 5. Tester les mutations

### 5.1 Mettre à jour les pondérations

```bash
curl -X PUT http://localhost:8000/supplier-scoring/criteria \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "weights": {
      "price_stability": 0.30,
      "delivery_reliability": 0.25,
      "invoice_accuracy": 0.15,
      "stock_accuracy": 0.10,
      "payment_terms": 0.10,
      "responsiveness": 0.05,
      "product_quality": 0.05
    }
  }'
```

**Réponse attendue:**
```json
{
  "success": true,
  "data": {
    "criteria": [ ... ],
    "total_weight": 1.0
  },
  "meta": {
    "message": "Pondérations mises à jour avec succès"
  }
}
```

---

### 5.2 Recalculer les scores

```bash
curl -X POST http://localhost:8000/supplier-scoring/recalculate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_names": null,
    "period_days": 90,
    "force": false
  }'
```

**Réponse attendue:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "suppliers_processed": 0,
    "suppliers_failed": 0,
    "duration_seconds": 0.5,
    "errors": []
  },
  "meta": {
    "message": "Recalcul terminé: 0 fournisseurs traités"
  }
}
```

---

### 5.3 Enregistrer une livraison

```bash
curl -X POST http://localhost:8000/supplier-scoring/delivery \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_name": "Fournisseur Test",
    "expected_date": "2025-12-10",
    "actual_date": "2025-12-11",
    "invoice_id": 1001
  }'
```

**Réponse attendue:**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "message": "Livraison enregistrée",
    "delay_days": 1,
    "on_time": false
  }
}
```

---

### 5.4 Enregistrer un incident

```bash
curl -X POST http://localhost:8000/supplier-scoring/issue \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_name": "Fournisseur Test",
    "issue_type": "price_error",
    "severity": "medium",
    "invoice_id": 1001,
    "description": "Prix incorrect sur la facture"
  }'
```

**Réponse attendue:**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "message": "Problème enregistré"
  }
}
```

---

## 6. Tester avec la documentation Swagger

### 6.1 Ouvrir Swagger UI

Naviguer vers: `http://localhost:8000/docs`

### 6.2 S'authentifier

1. Cliquer sur "Authorize" en haut à droite
2. Entrer: `Bearer YOUR_TOKEN_HERE`
3. Cliquer "Authorize"

### 6.3 Tester les endpoints

1. Ouvrir la section "Supplier Scoring"
2. Sélectionner un endpoint (ex: `GET /supplier-scoring/overview`)
3. Cliquer "Try it out"
4. Cliquer "Execute"
5. Voir la réponse

---

## 7. Exécuter les tests automatisés

```bash
# Tous les tests
pytest tests/test_supplier_scoring_api.py -v

# Test spécifique
pytest tests/test_supplier_scoring_api.py::test_get_overview_returns_wrapper_format -v

# Avec couverture
pytest tests/test_supplier_scoring_api.py --cov=backend.api.supplier_scoring --cov-report=html

# Voir le rapport de couverture
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## 8. Vérifier les logs

```bash
# Logs du serveur
tail -f logs/backend.log

# Ou si Docker
docker-compose logs -f backend
```

---

## 9. Résolution des problèmes courants

### Problème 1: "401 Unauthorized"
**Cause:** Token JWT invalide ou expiré
**Solution:**
```bash
# Régénérer un nouveau token
curl -X POST http://localhost:8000/auth/login ...
export TOKEN="nouveau_token"
```

---

### Problème 2: "404 Not Found"
**Cause:** Route non enregistrée
**Solution:**
```bash
# Vérifier que le router est bien enregistré
grep "supplier_scoring" backend/api/routes.py

# Devrait afficher:
# from backend.api import supplier_scoring
# app.include_router(supplier_scoring.router)
```

---

### Problème 3: "422 Validation Error"
**Cause:** Données invalides dans le body
**Solution:**
```bash
# Vérifier la structure de la requête
# Exemple pour update criteria:
{
  "weights": {
    "price_stability": 0.25,  # Doit être entre 0 et 1
    "delivery_reliability": 0.20,
    ...
  }
  # La somme doit faire 1.0
}
```

---

### Problème 4: "500 Internal Server Error"
**Cause:** Erreur côté serveur
**Solution:**
```bash
# Vérifier les logs
tail -f logs/backend.log

# Vérifier que les tables DB existent
# La classe SupplierScoreCalculator crée les tables automatiquement
# au premier appel (_ensure_tables)
```

---

## 10. Prochaines étapes

### Pour continuer

1. **Lire la documentation complète:**
   - `docs/SUPPLIER_SCORING_API.md` - Détails de tous les endpoints

2. **Intégrer le Frontend:**
   - `docs/SUPPLIER_SCORING_FRONTEND_INTEGRATION.md` - Guide complet

3. **Comprendre l'architecture:**
   - `docs/SUPPLIER_SCORING_ARCHITECTURE.md` - Diagrammes et flux

4. **Voir les statistiques:**
   - `SUPPLIER_SCORING_SUMMARY.md` - Résumé exécutif

---

## Ressources

### Documentation
- API: `docs/SUPPLIER_SCORING_API.md`
- Frontend: `docs/SUPPLIER_SCORING_FRONTEND_INTEGRATION.md`
- Architecture: `docs/SUPPLIER_SCORING_ARCHITECTURE.md`
- Implémentation: `SUPPLIER_SCORING_IMPLEMENTATION.md`
- Résumé: `SUPPLIER_SCORING_SUMMARY.md`
- Index: `SUPPLIER_SCORING_FILES.md`

### Code
- Schémas: `backend/schemas/supplier_scoring.py`
- API Router: `backend/api/supplier_scoring.py`
- Business Logic: `core/finance/supplier_scoring.py`
- Tests: `tests/test_supplier_scoring_api.py`

### Swagger
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Support

### En cas de problème

1. Vérifier les logs: `tail -f logs/backend.log`
2. Consulter la documentation: `docs/SUPPLIER_SCORING_API.md`
3. Lancer les tests: `pytest tests/test_supplier_scoring_api.py -v`
4. Vérifier Swagger: `http://localhost:8000/docs`

---

## Checklist de démarrage rapide

- [ ] Serveur Backend lancé (`http://localhost:8000`)
- [ ] Token JWT obtenu et sauvegardé
- [ ] Endpoint `/overview` testé avec succès
- [ ] Endpoint `/suppliers` testé avec succès
- [ ] Endpoint `/criteria` testé avec succès
- [ ] Documentation Swagger accessible (`/docs`)
- [ ] Tests automatisés exécutés avec succès

**Si toutes les cases sont cochées: ✅ Vous êtes prêt!**

---

**Date:** 2025-12-11
**Version:** 1.0.0
**Statut:** Quick Start Guide
