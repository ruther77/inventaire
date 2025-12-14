# Guide de déploiement NewCMS

## Prérequis

- Python 3.10+
- PostgreSQL 13+
- FastAPI application existante
- Tables: `plats`, `ingredients`, `plat_ingredients`, `mouvements_stock`

## Étapes de déploiement

### 1. Migration base de données

```bash
# Backup de la base
pg_dump -U postgres inventaire > backup_before_newcms.sql

# Exécuter la migration
psql -U postgres -d inventaire -f newCMS/migration_mobile_support.sql

# Vérifier les colonnes ajoutées
psql -U postgres -d inventaire -c "\d+ ingredients"
```

**Vérifie que:**
- `ingredients.code_barre` existe
- `ingredients.seuil_alerte` existe
- `mouvements_stock.source` existe
- Indexes sont créés

### 2. Ajout de données de test (optionnel)

```sql
-- Ajouter des codes-barres pour test
UPDATE ingredients
SET code_barre = '3245678901234', seuil_alerte = 10.0
WHERE nom = 'Tomate' AND tenant_id = 1;

UPDATE ingredients
SET code_barre = '3245678901235', seuil_alerte = 5.0
WHERE nom = 'Poulet' AND tenant_id = 1;

-- Vérifier
SELECT id, nom, code_barre, stock_actuel, seuil_alerte
FROM ingredients
WHERE tenant_id = 1 AND code_barre IS NOT NULL;
```

### 3. Intégration dans main.py

Ajouter dans `/home/ruuuzer/Documents/monprojet/backend/main.py`:

```python
# Import du router newCMS
from newCMS.backend.api import restaurant_router

# Après création de l'app
app = FastAPI(
    title="Inventaire API",
    version="2.0.0"
)

# Monter les routers existants
# ... vos routers existants ...

# Ajouter le router newCMS
app.include_router(restaurant_router)
```

### 4. Vérification des dépendances

```bash
# Vérifier que les modules sont importables
python -c "from newCMS.backend.api import restaurant_router; print('OK')"

# Vérifier les schemas
python -c "from newCMS.backend.schemas.restaurant import RestaurantOverviewResponse; print('OK')"
```

### 5. Tests

```bash
# Tests unitaires
python newCMS/test_endpoints.py

# Démarrer le serveur
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Dans un autre terminal, tester les endpoints
curl http://localhost:8000/docs
```

Vérifier que les endpoints apparaissent dans Swagger:
- GET `/newcms/restaurant/overview`
- GET `/newcms/mobile/inventory`
- POST `/newcms/mobile/scan`
- POST `/newcms/mobile/adjust`

### 6. Tests fonctionnels

#### Test 1: Restaurant Overview

```bash
TOKEN="your_jwt_token"

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/newcms/restaurant/overview | jq
```

Attendu:
- Status 200
- JSON avec metrics, plat_costs, stock_locations, ingredient_alerts

#### Test 2: Mobile Inventory

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/newcms/mobile/inventory?page=1&page_size=10" | jq
```

Attendu:
- Status 200
- Liste d'items avec id, nom, code_barre, stock_actuel

#### Test 3: Scan Barcode

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code_barre":"3245678901234"}' \
  http://localhost:8000/newcms/mobile/scan | jq
```

Attendu:
- Status 200
- `found: true` si code-barres existe
- Objet `product` avec détails

#### Test 4: Adjust Stock

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "adjustment": -1,
    "adjustment_type": "delta",
    "reason": "breakage",
    "notes": "Test adjustment"
  }' \
  http://localhost:8000/newcms/mobile/adjust | jq
```

Attendu:
- Status 200
- `old_stock` et `new_stock` différents
- Entrée créée dans `mouvements_stock`

### 7. Vérification audit trail

```sql
-- Vérifier que les ajustements sont enregistrés
SELECT
  id,
  produit_id,
  type,
  quantite,
  source,
  date_mvt
FROM mouvements_stock
WHERE source LIKE 'mobile_adjust:%'
ORDER BY date_mvt DESC
LIMIT 10;
```

### 8. Performance - Création des indexes

Si non créés par la migration:

```sql
-- Index pour scan barcode
CREATE INDEX IF NOT EXISTS idx_ingredients_code_barre
ON ingredients(code_barre)
WHERE code_barre IS NOT NULL;

-- Index pour alertes stock
CREATE INDEX IF NOT EXISTS idx_ingredients_stock_alert
ON ingredients(tenant_id, stock_actuel, seuil_alerte);

-- Index pour coûts plats
CREATE INDEX IF NOT EXISTS idx_plat_ingredients_plat_id
ON plat_ingredients(plat_id, tenant_id);

-- Vérifier les indexes
\d+ ingredients
\d+ plat_ingredients
```

### 9. Monitoring

#### Logs à surveiller

```bash
# Suivre les logs en temps réel
tail -f /var/log/inventaire/api.log | grep newcms
```

Surveiller:
- Erreurs 500 (bugs backend)
- Erreurs 404 (produit non trouvé au scan)
- Temps de réponse > 500ms (performance)

#### Métriques clés

```sql
-- Nombre d'ajustements par jour
SELECT
  DATE(date_mvt) as jour,
  COUNT(*) as ajustements
FROM mouvements_stock
WHERE source LIKE 'mobile_adjust:%'
GROUP BY DATE(date_mvt)
ORDER BY jour DESC
LIMIT 7;

-- Motifs d'ajustement les plus fréquents
SELECT
  SPLIT_PART(source, ':', 2) as reason,
  COUNT(*) as count
FROM mouvements_stock
WHERE source LIKE 'mobile_adjust:%'
GROUP BY reason
ORDER BY count DESC;
```

### 10. Rollback (si problème)

```bash
# Restaurer le backup
psql -U postgres -d inventaire < backup_before_newcms.sql

# Supprimer les colonnes ajoutées (si nécessaire)
psql -U postgres -d inventaire -c "
  ALTER TABLE ingredients DROP COLUMN IF EXISTS code_barre;
  ALTER TABLE ingredients DROP COLUMN IF EXISTS seuil_alerte;
  ALTER TABLE mouvements_stock DROP COLUMN IF EXISTS source;
"

# Supprimer les indexes
psql -U postgres -d inventaire -c "
  DROP INDEX IF EXISTS idx_ingredients_code_barre;
  DROP INDEX IF EXISTS idx_ingredients_stock_alert;
  DROP INDEX IF EXISTS idx_plat_ingredients_plat_id;
"

# Redémarrer l'app sans le router newCMS
# (commenter la ligne dans main.py)
```

## Configuration production

### 1. Variables d'environnement

```bash
# .env
NEWCMS_CACHE_ENABLED=true
NEWCMS_CACHE_TTL=300  # 5 minutes
NEWCMS_MAX_PAGE_SIZE=200
NEWCMS_SCAN_TIMEOUT=30000  # 30 secondes
```

### 2. Cache Redis (optionnel)

```python
# Dans restaurant.py, ajouter cache Redis
from redis import Redis
redis_client = Redis(host='localhost', port=6379, db=0)

@router.get("/restaurant/overview")
def get_restaurant_overview(tenant: Tenant = Depends(get_current_tenant)):
    cache_key = f"resto_overview:{tenant.id}"
    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    # ... logique existante ...

    redis_client.setex(cache_key, 300, json.dumps(result))
    return result
```

### 3. Rate limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/mobile/adjust")
@limiter.limit("10/minute")  # Max 10 ajustements par minute
def adjust_stock(...):
    # ...
```

### 4. Monitoring avec Prometheus

```python
from prometheus_client import Counter, Histogram

scan_counter = Counter('newcms_scans_total', 'Total barcode scans')
adjust_counter = Counter('newcms_adjustments_total', 'Total stock adjustments', ['reason'])
response_time = Histogram('newcms_response_time_seconds', 'Response time')

@router.post("/mobile/scan")
def scan_barcode(...):
    scan_counter.inc()
    # ...
```

## Checklist finale

- [ ] Migration SQL exécutée
- [ ] Indexes créés
- [ ] Router monté dans main.py
- [ ] Tests unitaires passent
- [ ] Endpoints accessibles dans /docs
- [ ] Test scan barcode fonctionnel
- [ ] Test ajustement stock fonctionnel
- [ ] Audit trail visible dans mouvements_stock
- [ ] Performance < 100ms pour scan
- [ ] Logs monitoring configurés
- [ ] Backup base de données créé

## Support

En cas de problème:
1. Vérifier les logs: `tail -f /var/log/inventaire/api.log`
2. Vérifier la base: `psql -U postgres -d inventaire`
3. Relancer les tests: `python newCMS/test_endpoints.py`
4. Consulter la doc: `newCMS/RESTAURANT_MOBILE_API.md`

## Prochaines étapes

Après déploiement réussi:
1. Former les utilisateurs au scan mobile
2. Collecter feedback sur UX mobile
3. Optimiser queries si nécessaire
4. Ajouter cache Redis pour performance
5. Implémenter WebSocket pour temps-réel
