# Quick Start: Restaurant Ingredient Price Sync

## TL;DR

Restaurant ingredient prices can automatically sync from epicerie product prices. Three modes available:

1. **Real-time** (already working) - Uses epicerie price in SQL queries
2. **Scheduled** (recommended) - Periodic batch sync job
3. **On-demand** - Manual API trigger

## 5-Minute Integration

### 1. Link Ingredient to Epicerie Product

```python
# Backend
from backend.services.restaurant.ingredients import link_ingredient_to_epicerie

link_ingredient_to_epicerie(
    tenant_id=1,
    ingredient_id=42,
    produit_epicerie_id=123,
    ratio=1.0  # Unit conversion ratio
)
```

```javascript
// Frontend
await linkIngredientToEpicerie({
  ingredientId: 42,
  payload: {
    produit_epicerie_id: 123,
    ratio: 1.0
  }
});
```

### 2. Sync Prices

#### Option A: API Call (On-demand)

```bash
# Sync all ingredients with price changes
curl -X POST http://localhost:8000/api/restaurant/ingredients/sync-prices

# Force update all linked ingredients
curl -X POST http://localhost:8000/api/restaurant/ingredients/sync-prices?force_update=true
```

#### Option B: Python (Scheduled Job)

```python
from backend.services.restaurant.price_sync import sync_ingredient_prices_from_epicerie

result = sync_ingredient_prices_from_epicerie(tenant_id=1, force_update=False)

print(f"Updated {result['updated']} ingredients")
for change in result['price_changes']:
    print(f"{change['ingredient_nom']}: {change['old_price']}€ → {change['new_price']}€")
```

#### Option C: After Invoice Import

```python
# Add to your invoice import workflow
from backend.services.restaurant.price_sync import sync_ingredient_prices_from_epicerie

# After invoice processing updates epicerie prices
result = sync_ingredient_prices_from_epicerie(tenant_id=tenant_id)
logger.info(f"Auto-synced {result['updated']} ingredient prices after invoice import")
```

### 3. Monitor Sync Status

```bash
# Get sync health metrics
curl http://localhost:8000/api/restaurant/ingredients/price-sync-status
```

Response:
```json
{
  "total_ingredients": 50,
  "linked_to_epicerie": 35,
  "synced": 33,
  "out_of_sync": 2,
  "manual": 15,
  "sync_rate_pct": 94.3,
  "needs_attention": [...]
}
```

## Common Use Cases

### Use Case 1: Setup New Ingredient with Epicerie Link

```python
# Step 1: Create ingredient with epicerie link
ingredient = create_ingredient(tenant_id=1, payload={
    "nom": "Tomates",
    "unite_base": "kg",
    "cout_unitaire": 0,  # Will be synced from epicerie
    "produit_epicerie_id": 42,
    "ratio_epicerie": 1.0
})

# Step 2: Sync price immediately
result = sync_ingredient_prices_from_epicerie(tenant_id=1)
# ingredient.cout_unitaire is now = produits[42].prix_achat
```

### Use Case 2: Convert Units (kg to 100g)

```python
# Epicerie sells tomatoes by kg (10€/kg)
# Restaurant uses 100g portions
link_ingredient_to_epicerie(
    tenant_id=1,
    ingredient_id=42,
    produit_epicerie_id=123,
    ratio=0.1  # 1kg → 10 × 100g, so price/100g = price/kg × 0.1
)

# After sync: ingredient.cout_unitaire = 10€ × 0.1 = 1€ per 100g
```

### Use Case 3: Nightly Sync Job

```python
# In your scheduler (cron, APScheduler, Celery, etc.)
from backend.services.restaurant.price_sync import sync_ingredient_prices_from_epicerie
import logging

def nightly_price_sync_job():
    logger = logging.getLogger(__name__)

    for tenant_id in [1, 2]:  # For each tenant
        try:
            result = sync_ingredient_prices_from_epicerie(tenant_id, force_update=False)

            if result['updated'] > 0:
                logger.info(f"[Tenant {tenant_id}] Synced {result['updated']} prices")

                # Log significant changes
                for change in result['price_changes']:
                    if abs(change['change_pct']) > 10:
                        logger.warning(
                            f"Significant price change: {change['ingredient_nom']} "
                            f"{change['change_pct']:+.1f}%"
                        )

            if result['errors']:
                logger.error(f"[Tenant {tenant_id}] Sync errors: {result['errors']}")

        except Exception as e:
            logger.error(f"[Tenant {tenant_id}] Sync failed: {e}")

# Schedule to run every night at 2 AM
```

### Use Case 4: Check What Needs Syncing

```python
from backend.services.restaurant.price_sync import get_price_sync_summary

summary = get_price_sync_summary(tenant_id=1)

print(f"Sync rate: {summary['sync_rate_pct']}%")

if summary['needs_attention']:
    print("Ingredients with price differences:")
    for ing in summary['needs_attention']:
        print(f"  {ing['nom']}: {ing['current_price']}€ vs {ing['epicerie_price']}€")
```

## Frontend Integration

### Display Price Source in UI

The `PlatDetailModal` component now shows price sources:

```jsx
// Already implemented in PlatDetailModal.jsx
{priceSource === 'epicerie' ? (
  <span className="badge badge-violet">Epicerie</span>
) : (
  <span className="badge badge-gray">Manuel</span>
)}
```

### Add Sync Button to Admin Page

```jsx
import { useState } from 'react';
import { Button } from '@/components/ui';

function IngredientPriceSyncButton() {
  const [syncing, setSyncing] = useState(false);
  const [result, setResult] = useState(null);

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await fetch('/api/restaurant/ingredients/sync-prices', {
        method: 'POST'
      });
      const data = await res.json();
      setResult(data);

      if (data.updated > 0) {
        toast.success(`Synced ${data.updated} ingredient prices`);
      } else {
        toast.info('All prices are up to date');
      }
    } catch (err) {
      toast.error('Sync failed: ' + err.message);
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div>
      <Button onClick={handleSync} disabled={syncing}>
        {syncing ? 'Syncing...' : 'Sync Prices from Epicerie'}
      </Button>

      {result && result.price_changes.length > 0 && (
        <div className="mt-4">
          <h4>Price Changes:</h4>
          <ul>
            {result.price_changes.map(change => (
              <li key={change.ingredient_id}>
                {change.ingredient_nom}: {change.old_price}€ → {change.new_price}€
                ({change.change_pct > 0 ? '+' : ''}{change.change_pct.toFixed(1)}%)
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
```

## SQL Queries for Verification

### Check Sync Status

```sql
-- Ingredients linked to epicerie with price differences
SELECT
    ri.id,
    ri.nom AS ingredient,
    ri.cout_unitaire AS current_price,
    p.prix_achat AS epicerie_price,
    (p.prix_achat * ri.ratio_epicerie) AS should_be,
    ABS(ri.cout_unitaire - (p.prix_achat * ri.ratio_epicerie)) AS diff
FROM restaurant_ingredients ri
JOIN produits p ON p.id = ri.produit_epicerie_id
WHERE ri.tenant_id = 1
  AND ABS(ri.cout_unitaire - (p.prix_achat * ri.ratio_epicerie)) > 0.01;
```

### Check Price History

```sql
-- Recent price changes for an ingredient
SELECT
    h.cout_unitaire,
    h.changed_at,
    LAG(h.cout_unitaire) OVER (ORDER BY h.changed_at) AS previous_price,
    h.cout_unitaire - LAG(h.cout_unitaire) OVER (ORDER BY h.changed_at) AS change
FROM restaurant_ingredient_price_history h
WHERE h.ingredient_id = 42
ORDER BY h.changed_at DESC
LIMIT 10;
```

### List Ingredients by Price Source

```sql
-- Group ingredients by price source
SELECT
    CASE
        WHEN ri.produit_epicerie_id IS NOT NULL THEN 'epicerie'
        ELSE 'manual'
    END AS price_source,
    COUNT(*) AS count
FROM restaurant_ingredients ri
WHERE ri.tenant_id = 1
GROUP BY price_source;
```

## API Reference

### POST /api/restaurant/ingredients/sync-prices

Sync ingredient prices from epicerie.

**Query Params:**
- `force_update` (boolean, default: false) - Update all linked ingredients

**Response:**
```json
{
  "updated": 5,
  "skipped": 0,
  "errors": [],
  "price_changes": [
    {
      "ingredient_id": 42,
      "ingredient_nom": "Tomates",
      "produit_epicerie_nom": "Tomate ronde",
      "old_price": 8.5,
      "new_price": 9.2,
      "change_pct": 8.24,
      "ratio": 1.0
    }
  ]
}
```

### GET /api/restaurant/ingredients/price-sync-status

Get sync health metrics.

**Response:**
```json
{
  "total_ingredients": 50,
  "linked_to_epicerie": 35,
  "synced": 33,
  "out_of_sync": 2,
  "manual": 15,
  "sync_rate_pct": 94.3,
  "needs_attention": [
    {
      "id": 12,
      "nom": "Poulet",
      "current_price": 5.5,
      "epicerie_price": 6.0,
      "price_diff": -0.5,
      "produit_epicerie_nom": "Poulet entier"
    }
  ]
}
```

### GET /api/restaurant/ingredients/with-price-source

List ingredients with price source indicators.

**Response:**
```json
[
  {
    "id": 42,
    "nom": "Tomates",
    "cout_unitaire": 9.2,
    "produit_epicerie_id": 123,
    "produit_epicerie_nom": "Tomate ronde",
    "produit_epicerie_prix": 9.2,
    "price_source": "epicerie",
    "is_price_synced": true,
    "price_diff": 0.0,
    "ratio_epicerie": 1.0
  },
  {
    "id": 43,
    "nom": "Sel",
    "cout_unitaire": 2.0,
    "produit_epicerie_id": null,
    "price_source": "manual",
    "is_price_synced": true,
    "price_diff": null,
    "ratio_epicerie": 1.0
  }
]
```

## Troubleshooting

### Problem: Price not syncing

**Check 1:** Ingredient linked to epicerie?
```sql
SELECT produit_epicerie_id FROM restaurant_ingredients WHERE id = 42;
-- Should return a number, not NULL
```

**Check 2:** Epicerie product has valid price?
```sql
SELECT prix_achat FROM produits WHERE id = 123;
-- Should return a number > 0, not NULL
```

**Check 3:** Price difference significant enough?
```sql
-- Sync only updates if difference > 0.01€ (unless force_update=true)
SELECT
    ri.cout_unitaire,
    p.prix_achat,
    ABS(ri.cout_unitaire - p.prix_achat) AS diff
FROM restaurant_ingredients ri
JOIN produits p ON p.id = ri.produit_epicerie_id
WHERE ri.id = 42;
```

### Problem: Wrong price after sync

**Likely cause:** Incorrect `ratio_epicerie`

**Fix:**
```python
# Update ratio
update_ingredient_ratio(tenant_id=1, ingredient_id=42, ratio=0.1)

# Re-sync
sync_ingredient_prices_from_epicerie(tenant_id=1, force_update=True)
```

### Problem: Price history not recording

**Check trigger:**
```sql
SELECT tgname FROM pg_trigger WHERE tgrelid = 'restaurant_ingredients'::regclass;
-- Should show 'restaurant_ingredient_price_history_trigger'
```

**Re-install trigger if missing:**
```sql
-- Run the trigger SQL from db/init.sql lines 560-574
```

## Key Files

- **Backend Service:** `/backend/services/restaurant/price_sync.py`
- **API Endpoints:** `/backend/api/restaurant.py` (lines 197-239)
- **Frontend Component:** `/frontend/src/features/restaurant/components/PlatDetailModal.jsx` (lines 344-407)
- **Database Schema:** `/db/init.sql` (lines 380-393, 560-574)
- **Documentation:** `/INGREDIENT_PRICE_SYNC_GUIDE.md`

## Next Steps

1. Test manually: Update epicerie price → Sync → Verify ingredient price
2. Set up scheduled job (nightly or after invoice imports)
3. Add sync button to admin UI (optional)
4. Monitor sync health metrics
5. Train team on linking ingredients to epicerie products

For detailed documentation, see `INGREDIENT_PRICE_SYNC_GUIDE.md`.
