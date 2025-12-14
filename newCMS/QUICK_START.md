# Quick Start - NewCMS Restaurant & Mobile API

## Installation en 5 minutes

### 1. Migration BDD (30 secondes)

```bash
psql -U postgres -d inventaire -f newCMS/migration_mobile_support.sql
```

### 2. Intégration backend (1 minute)

Dans `backend/main.py`, ajouter:

```python
from newCMS.backend.api import restaurant_router

app.include_router(restaurant_router)
```

### 3. Redémarrer le serveur (30 secondes)

```bash
uvicorn backend.main:app --reload
```

### 4. Vérifier dans Swagger (1 minute)

Ouvrir http://localhost:8000/docs

Chercher tag **"newcms-restaurant"** avec 4 endpoints:
- GET `/newcms/restaurant/overview`
- GET `/newcms/mobile/inventory`
- POST `/newcms/mobile/scan`
- POST `/newcms/mobile/adjust`

### 5. Premier test (2 minutes)

```bash
# Obtenir un token
TOKEN=$(curl -X POST http://localhost:8000/auth/token \
  -d "username=test@example.com&password=password" | jq -r .access_token)

# Tester restaurant overview
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/newcms/restaurant/overview | jq

# Succès si vous voyez:
# {
#   "metrics": { ... },
#   "plat_costs": [ ... ],
#   "stock_locations": [ ... ],
#   "ingredient_alerts": [ ... ]
# }
```

## Test mobile complet (5 minutes)

### 1. Ajouter des codes-barres de test

```sql
UPDATE ingredients
SET code_barre = '3245678901234', seuil_alerte = 10.0
WHERE nom = 'Tomate' AND tenant_id = 1;
```

### 2. Scan barcode

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code_barre":"3245678901234"}' \
  http://localhost:8000/newcms/mobile/scan | jq
```

Attendu:
```json
{
  "found": true,
  "product": {
    "id": 1,
    "nom": "Tomate",
    "code_barre": "3245678901234",
    "stock_actuel": 15.5,
    "seuil_alerte": 10.0
  }
}
```

### 3. Ajuster le stock

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "adjustment": -1,
    "adjustment_type": "delta",
    "reason": "breakage",
    "notes": "Test"
  }' \
  http://localhost:8000/newcms/mobile/adjust | jq
```

Attendu:
```json
{
  "product_id": 1,
  "product_name": "Tomate",
  "old_stock": 15.5,
  "new_stock": 14.5,
  "adjustment": -1.0,
  "reason": "breakage"
}
```

### 4. Vérifier l'audit trail

```sql
SELECT * FROM mouvements_stock
WHERE source LIKE 'mobile_adjust:%'
ORDER BY date_mvt DESC
LIMIT 5;
```

## Import Postman (1 minute)

1. Ouvrir Postman
2. Import → Upload File → `newCMS/postman_collection.json`
3. Configurer variables:
   - `base_url`: http://localhost:8000
   - `access_token`: votre JWT token
4. Exécuter les requêtes dans l'ordre

## Tests automatisés (30 secondes)

```bash
python newCMS/test_endpoints.py
```

Attendu:
```
✓ Restaurant overview schema valid
✓ Mobile inventory schema valid
✓ Mobile scan schema valid
✓ Mobile adjust validation works
✓ All 7 tests passed!
```

## Utilisation client mobile

Voir `newCMS/mobile_client_example.tsx` pour:
- Scanner de codes-barres (React Native)
- Interface d'ajustement stock
- Gestion des motifs (casse, vol, etc.)

## Troubleshooting

### Erreur 404 sur /newcms/*

```bash
# Vérifier que le router est monté
grep "restaurant_router" backend/main.py

# Si absent, ajouter:
from newCMS.backend.api import restaurant_router
app.include_router(restaurant_router)
```

### Erreur "code_barre column does not exist"

```bash
# Relancer la migration
psql -U postgres -d inventaire -f newCMS/migration_mobile_support.sql
```

### Aucun produit trouvé au scan

```sql
-- Vérifier les codes-barres
SELECT id, nom, code_barre FROM ingredients WHERE code_barre IS NOT NULL;

-- Si vide, ajouter des codes-barres de test
UPDATE ingredients SET code_barre = '3245678901234' WHERE id = 1;
```

### Performance lente (> 500ms)

```sql
-- Vérifier les indexes
SELECT * FROM pg_indexes WHERE tablename = 'ingredients';

-- Si absents, les créer
CREATE INDEX idx_ingredients_code_barre ON ingredients(code_barre);
```

## Prochaines étapes

Après installation réussie:

1. **Former les utilisateurs**
   - Scan de codes-barres
   - Ajustements de stock
   - Motifs d'ajustement

2. **Configurer monitoring**
   - Logs ajustements
   - Performance scans
   - Erreurs 404 (produits non trouvés)

3. **Optimiser**
   - Ajouter cache Redis si > 100 plats
   - Batch updates pour inventaire complet
   - Photos pour justificatifs

4. **Étendre**
   - Stock par emplacement (bar/cuisine/cave)
   - Alertes push mobiles
   - Rapports automatiques

## Documentation complète

- **README.md** - Vue d'ensemble
- **RESTAURANT_MOBILE_API.md** - Documentation API détaillée
- **DEPLOYMENT.md** - Guide déploiement production
- **INTEGRATION_EXAMPLE.py** - Exemples d'intégration
- **test_endpoints.py** - Tests unitaires

## Support

Questions? Vérifier dans l'ordre:
1. Ce fichier Quick Start
2. README.md
3. RESTAURANT_MOBILE_API.md
4. Logs serveur
5. Tests unitaires

Bon déploiement! 🚀
