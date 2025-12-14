# NewCMS Restaurant & Mobile API

## Overview

API endpoints optimisés pour le nouveau CMS restaurant et l'application mobile de gestion des stocks.

**Base Path:** `/newcms`

---

## Restaurant Overview

### GET `/newcms/restaurant/overview`

Agrège les données clés du restaurant : coûts plats, alertes ingrédients, stock par emplacement, top plats.

**Response:**
```json
{
  "metrics": {
    "total_plats": 42,
    "avg_food_cost_pct": 32.5,
    "alerts_count": 8,
    "top_plats": [
      {
        "plat_id": 15,
        "nom": "Burger Signature",
        "marge_pct": 68.5,
        "prix_vente_ttc": 12.50,
        "cout_matiere": 3.94
      }
    ]
  },
  "plat_costs": [
    {
      "plat_id": 1,
      "nom": "Salade César",
      "food_cost_pct": 28.0,
      "marge_pct": 72.0,
      "prix_vente_ttc": 9.50,
      "cout_matiere": 2.66
    }
  ],
  "stock_locations": [
    {
      "location": "cuisine",
      "count": 42,
      "valeur": 1250.00
    }
  ],
  "ingredient_alerts": [
    {
      "ingredient_id": 23,
      "nom": "Poulet",
      "stock_actuel": 2.5,
      "seuil_alerte": 5.0,
      "status": "alerte"
    }
  ]
}
```

**Features:**
- Food cost % par plat (coût matière / prix de vente)
- Alertes ingrédients (rupture/alerte)
- Stock agrégé par emplacement (bar, cuisine, cave)
- Top 5 plats par marge

---

## Mobile Endpoints

### GET `/newcms/mobile/inventory`

Liste paginée des items scannables avec stock actuel.

**Query Parameters:**
- `page` (int, default: 1): Numéro de page
- `page_size` (int, default: 50, max: 200): Items par page
- `search` (string, optional): Recherche par nom ou code-barres

**Response:**
```json
{
  "items": [
    {
      "id": 42,
      "nom": "Tomate",
      "code_barre": "3245678901234",
      "stock_actuel": 15.5,
      "seuil_alerte": 10.0,
      "categorie": "ingredient"
    }
  ],
  "total": 156,
  "page": 1,
  "page_size": 50
}
```

**Optimizations:**
- Réponse légère (< 1 KB par item)
- Pagination efficace
- Recherche rapide

---

### POST `/newcms/mobile/scan`

Lookup code-barres pour scanner un produit.

**Request:**
```json
{
  "code_barre": "3245678901234"
}
```

**Response (found):**
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
  },
  "message": null
}
```

**Response (not found):**
```json
{
  "found": false,
  "product": null,
  "message": "Aucun produit trouvé pour le code-barres: 3245678901234"
}
```

**Features:**
- Réponse ultra-rapide (< 100ms)
- Support scan caméra mobile
- Retourne stock + seuil alerte

---

### POST `/newcms/mobile/adjust`

Ajustement de stock depuis mobile avec motif.

**Request:**
```json
{
  "product_id": 42,
  "adjustment": -1,
  "adjustment_type": "delta",
  "reason": "breakage",
  "notes": "Cassé pendant transport"
}
```

**Adjustment Types:**
- `delta`: Ajustement relatif (+1, -1, etc.)
- `absolute`: Valeur absolue (recompte complet)

**Reasons:**
- `breakage`: Casse
- `theft`: Vol
- `error`: Erreur inventaire
- `expiry`: Péremption
- `other`: Autre

**Response:**
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

**Features:**
- Transaction atomique (FOR UPDATE)
- Création automatique de mouvement_stock
- Audit trail complet (reason + notes)
- Stock ne peut pas être négatif (min: 0)

---

## Integration

### 1. Monter le router dans `main.py`

```python
from newCMS.backend.api import restaurant_router

app.include_router(restaurant_router)
```

### 2. Tables utilisées

**Restaurant:**
- `plats` (id, nom, prix_vente_ttc, actif)
- `ingredients` (id, nom, stock_actuel, seuil_alerte, code_barre)
- `plat_ingredients` (plat_id, ingredient_id, quantite_batch)

**Mobile:**
- `ingredients` (stock restaurant séparé par tenant_id)
- `mouvements_stock` (audit trail ajustements)

### 3. Conventions

**Stock Restaurant vs Épicerie:**
- Restaurant: `tenant_id = restaurant`
- Épicerie: `tenant_id = epicerie`

**Motifs d'ajustement:**
- Toujours enregistrés dans `mouvements_stock.source`
- Format: `mobile_adjust:{reason}:{notes}`

---

## Performance

**Restaurant Overview:**
- 3 requêtes SQL
- ~200-500ms pour 50 plats
- Cache recommandé (5 min)

**Mobile Inventory:**
- 2 requêtes SQL (list + count)
- ~50-100ms pour 50 items
- Pagination efficace

**Mobile Scan:**
- 1 requête SQL avec index sur code_barre
- ~10-30ms
- Index requis: `CREATE INDEX idx_ingredients_code_barre ON ingredients(code_barre)`

**Mobile Adjust:**
- Transaction atomique
- FOR UPDATE lock
- ~50-100ms
- Garantit cohérence stock

---

## Sécurité

- Authentification: `get_current_tenant` (JWT)
- Authorization: tenant_id isolation
- Validation: Pydantic schemas
- SQL Injection: Parameterized queries (SQLAlchemy)
- Stock négatif: Impossible (max(0, stock))

---

## Tests

```bash
# Test restaurant overview
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/newcms/restaurant/overview

# Test mobile inventory
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/newcms/mobile/inventory?page=1&page_size=20"

# Test scan
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code_barre":"3245678901234"}' \
  http://localhost:8000/newcms/mobile/scan

# Test adjust
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id":42,"adjustment":-1,"adjustment_type":"delta","reason":"breakage"}' \
  http://localhost:8000/newcms/mobile/adjust
```

---

## Roadmap

- [ ] WebSocket pour scans temps-réel
- [ ] Batch adjustments (ajuster plusieurs produits)
- [ ] Photos pour ajustements (preuve casse/péremption)
- [ ] Stock locations réels (bar, cuisine, cave)
- [ ] Synchronisation offline (PWA mobile)
- [ ] Dashboard mobile temps-réel
