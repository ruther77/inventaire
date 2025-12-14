# NewCMS - Restaurant & Mobile API

## Vue d'ensemble

Module API optimisé pour le nouveau CMS restaurant et l'application mobile de gestion des stocks. Conçu pour des réponses rapides et une expérience mobile fluide.

## Architecture

```
newCMS/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── restaurant.py          # Endpoints restaurant & mobile
│   └── schemas/
│       ├── __init__.py
│       └── restaurant.py          # Pydantic schemas
├── RESTAURANT_MOBILE_API.md       # Documentation API complète
├── INTEGRATION_EXAMPLE.py         # Exemple d'intégration
├── migration_mobile_support.sql   # Migration BDD
├── test_endpoints.py              # Tests unitaires
└── README.md                      # Ce fichier
```

## Endpoints

### Restaurant

**GET `/newcms/restaurant/overview`**
- Agrège coûts plats (food cost %), alertes ingrédients, stock par emplacement
- Top 5 plats par marge
- Optimisé pour dashboard restaurant

### Mobile

**GET `/newcms/mobile/inventory`**
- Liste paginée items scannables
- Recherche par nom ou code-barres
- ~50-100ms par requête

**POST `/newcms/mobile/scan`**
- Lookup code-barres ultra-rapide
- Retourne produit + stock actuel
- ~10-30ms par scan

**POST `/newcms/mobile/adjust`**
- Ajustement stock avec motif (casse, vol, erreur, péremption)
- Transaction atomique (FOR UPDATE)
- Audit trail complet

## Installation

### 1. Migration BDD

```bash
psql -U postgres -d inventaire -f newCMS/migration_mobile_support.sql
```

Cette migration ajoute:
- `ingredients.code_barre` pour scan mobile
- `ingredients.seuil_alerte` pour alertes
- `mouvements_stock.source` pour audit trail
- Indexes pour performance

### 2. Intégration dans main.py

```python
from newCMS.backend.api import restaurant_router

app.include_router(restaurant_router)
```

### 3. Vérifier les routes

```bash
# Démarrer le serveur
uvicorn backend.main:app --reload

# Ouvrir http://localhost:8000/docs
# Chercher tag "newcms-restaurant"
```

## Tests

### Tests unitaires

```bash
python newCMS/test_endpoints.py
```

### Tests manuels (curl)

```bash
# Restaurant overview
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/newcms/restaurant/overview

# Mobile inventory
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/newcms/mobile/inventory?page=1&page_size=20"

# Scan barcode
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code_barre":"3245678901234"}' \
  http://localhost:8000/newcms/mobile/scan

# Adjust stock
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id":42,"adjustment":-1,"adjustment_type":"delta","reason":"breakage"}' \
  http://localhost:8000/newcms/mobile/adjust
```

## Performance

| Endpoint | Temps moyen | Optimisations |
|----------|-------------|---------------|
| `/restaurant/overview` | 200-500ms | Cache 5min recommandé |
| `/mobile/inventory` | 50-100ms | Pagination + index |
| `/mobile/scan` | 10-30ms | Index sur code_barre |
| `/mobile/adjust` | 50-100ms | Transaction atomique |

### Indexes requis

```sql
-- Scan mobile ultra-rapide
CREATE INDEX idx_ingredients_code_barre ON ingredients(code_barre);

-- Alertes stock rapides
CREATE INDEX idx_ingredients_stock_alert ON ingredients(tenant_id, stock_actuel, seuil_alerte);

-- Calcul coûts plats rapide
CREATE INDEX idx_plat_ingredients_plat_id ON plat_ingredients(plat_id, tenant_id);
```

## Schémas de données

### Restaurant Overview Response

```json
{
  "metrics": {
    "total_plats": 42,
    "avg_food_cost_pct": 32.5,
    "alerts_count": 8,
    "top_plats": [...]
  },
  "plat_costs": [...],
  "stock_locations": [...],
  "ingredient_alerts": [...]
}
```

### Mobile Scan Response

```json
{
  "found": true,
  "product": {
    "id": 42,
    "nom": "Tomate",
    "code_barre": "3245678901234",
    "stock_actuel": 15.5,
    "seuil_alerte": 10.0,
    "categorie": "ingredient"
  }
}
```

### Mobile Adjust Response

```json
{
  "product_id": 42,
  "product_name": "Tomate",
  "old_stock": 15.5,
  "new_stock": 14.5,
  "adjustment": -1.0,
  "reason": "breakage",
  "timestamp": "2025-12-11T14:32:15.123456"
}
```

## Conventions

### Motifs d'ajustement

- `breakage`: Casse
- `theft`: Vol
- `error`: Erreur inventaire
- `expiry`: Péremption
- `other`: Autre

### Types d'ajustement

- `delta`: Relatif (+1, -1, etc.)
- `absolute`: Absolu (recompte complet)

### Statuts alertes

- `rupture`: Stock = 0
- `alerte`: Stock < seuil_alerte
- `ok`: Stock >= seuil_alerte

## Sécurité

- **Authentification**: JWT via `get_current_tenant`
- **Isolation**: Requêtes filtrées par `tenant_id`
- **Validation**: Pydantic schemas stricts
- **SQL Injection**: Requêtes paramétrées (SQLAlchemy)
- **Stock négatif**: Impossible (max(0, stock))
- **Concurrence**: FOR UPDATE lock sur ajustements

## Roadmap

### Phase 1 (Actuel)
- [x] Restaurant overview endpoint
- [x] Mobile inventory list
- [x] Barcode scan
- [x] Stock adjustments with reasons
- [x] Audit trail

### Phase 2 (Q1 2026)
- [ ] WebSocket pour scans temps-réel
- [ ] Batch adjustments (plusieurs produits)
- [ ] Photos pour justificatifs (casse/péremption)
- [ ] Stock locations réels (bar, cuisine, cave)
- [ ] Cache Redis pour overview

### Phase 3 (Q2 2026)
- [ ] Synchronisation offline (PWA mobile)
- [ ] Dashboard mobile temps-réel
- [ ] Alertes push mobile
- [ ] Rapports d'inventaire automatiques
- [ ] Export Excel ajustements

## Support

Pour questions ou problèmes:
1. Lire la [documentation API complète](RESTAURANT_MOBILE_API.md)
2. Vérifier les [exemples d'intégration](INTEGRATION_EXAMPLE.py)
3. Exécuter les [tests](test_endpoints.py)
4. Vérifier les logs serveur

## Licence

Propriétaire - Usage interne uniquement
