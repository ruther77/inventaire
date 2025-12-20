# Ingredient Price Auto-Sync from Epicerie

## Overview

This feature automatically synchronizes restaurant ingredient prices from linked epicerie products. When epicerie product prices are updated (e.g., from invoice imports), restaurant ingredient costs can be automatically updated to reflect these changes.

## Architecture

### 1. Database Structure

The price sync relies on the existing link between restaurant ingredients and epicerie products:

```sql
-- restaurant_ingredients table
CREATE TABLE restaurant_ingredients (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL,
    nom TEXT NOT NULL,
    cout_unitaire NUMERIC(12,4) DEFAULT 0,  -- This is synced from epicerie
    produit_epicerie_id INT REFERENCES produits(id),  -- Link to epicerie product
    ratio_epicerie NUMERIC(12,4) DEFAULT 1.0  -- Unit conversion ratio
);

-- produits table (epicerie)
CREATE TABLE produits (
    id SERIAL PRIMARY KEY,
    nom TEXT NOT NULL,
    prix_achat NUMERIC(10,2)  -- This is the source of truth
);
```

### 2. Price Calculation

When syncing prices, the system applies the `ratio_epicerie` for unit conversion:

```
ingredient.cout_unitaire = produit.prix_achat × ingredient.ratio_epicerie
```

**Example:**
- Epicerie product: "Tomatoes" - 10€/kg
- Restaurant ingredient: "Tomatoes" with ratio 0.1 (for 100g portions)
- Synced price: 10€ × 0.1 = 1€ per 100g

### 3. Automatic Price History

The database trigger `trg_restaurant_ingredient_price_history` automatically records all price changes:

```sql
CREATE TRIGGER restaurant_ingredient_price_history_trigger
AFTER INSERT OR UPDATE ON restaurant_ingredients
FOR EACH ROW EXECUTE FUNCTION trg_restaurant_ingredient_price_history();
```

## Implementation Details

### Backend Service

**File:** `/home/ruuuzer/Documents/monprojet/backend/services/restaurant/price_sync.py`

#### Main Functions

1. **`sync_ingredient_prices_from_epicerie(tenant_id, force_update=False)`**
   - Syncs ingredient prices from epicerie products
   - Only updates ingredients with `produit_epicerie_id` set
   - Applies `ratio_epicerie` for unit conversion
   - Automatically triggers `refresh_plat_costs()` to update dish margins
   - Returns summary with updated count and price changes

2. **`get_ingredients_with_price_source(tenant_id)`**
   - Returns all ingredients with price source indicator
   - Fields: `price_source` ('epicerie' or 'manual'), `is_price_synced`, `price_diff`

3. **`get_price_sync_summary(tenant_id)`**
   - Returns overview of sync status across all ingredients
   - Useful for monitoring and alerting

### API Endpoints

**File:** `/home/ruuuzer/Documents/monprojet/backend/api/restaurant.py`

#### 1. Sync Prices (Manual Trigger)
```http
POST /api/restaurant/ingredients/sync-prices?force_update=false
```

**Query Parameters:**
- `force_update` (boolean): If true, update all linked ingredients. If false, only update when prices differ.

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

#### 2. Get Price Sync Status
```http
GET /api/restaurant/ingredients/price-sync-status
```

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

#### 3. List Ingredients with Price Source
```http
GET /api/restaurant/ingredients/with-price-source
```

Returns all ingredients with `price_source`, `is_price_synced`, and `price_diff` fields.

## Frontend Integration

### PlatDetailModal Component

**File:** `/home/ruuuzer/Documents/monprojet/frontend/src/features/restaurant/components/PlatDetailModal.jsx`

The modal now displays the price source for each ingredient:

- **Epicerie Badge (Violet)**: Price is synced from linked epicerie product
- **Manuel Badge (Gray)**: Price is manually maintained
- Shows linked epicerie product name below ingredient name

**Visual Example:**
```
Ingredient Name          Quantity    Unit Price    Source        Total
─────────────────────────────────────────────────────────────────────
Tomates                 0.5 kg      9.20€         [Epicerie]    4.60€
Tomate ronde (violet text)

Sel                     0.01 kg     2.00€         [Manuel]      0.02€
```

## Usage Workflows

### Workflow 1: Real-time Calculation (Current Implementation)

The `list_plats()` function already uses `COALESCE` to prefer epicerie prices:

```sql
SELECT
    pi.plat_id,
    SUM(
        pi.quantite *
        COALESCE(
            (SELECT prix_achat FROM produits WHERE id = ri.produit_epicerie_id),
            ri.cout_unitaire,
            0
        )
    ) AS cout_matiere
FROM restaurant_plat_ingredients pi
JOIN restaurant_ingredients ri ON ri.id = pi.ingredient_id
GROUP BY pi.plat_id
```

**Advantage:** Always uses latest epicerie price without needing sync
**Disadvantage:** Relies on database query each time

### Workflow 2: Scheduled Sync Job (Recommended)

Set up a periodic job (e.g., nightly or after invoice imports) to sync prices:

```python
# In a scheduled job or after invoice processing
from backend.services.restaurant.price_sync import sync_ingredient_prices_from_epicerie

# Sync prices for all tenants
result = sync_ingredient_prices_from_epicerie(tenant_id=1, force_update=False)

# Log results
if result['updated'] > 0:
    logger.info(f"Updated {result['updated']} ingredient prices")
    for change in result['price_changes']:
        logger.info(
            f"  {change['ingredient_nom']}: "
            f"{change['old_price']}€ → {change['new_price']}€ "
            f"({change['change_pct']:+.1f}%)"
        )
```

**Recommended Schedule:**
- After each invoice import completion
- Nightly at 2 AM (catches any manual price updates in epicerie)
- On-demand via admin interface

### Workflow 3: Event-Driven Sync (Future Enhancement)

Add a database trigger to sync prices when epicerie product prices change:

```sql
CREATE OR REPLACE FUNCTION trg_sync_restaurant_prices_on_epicerie_update()
RETURNS TRIGGER AS $$
BEGIN
    -- Update all linked restaurant ingredients
    UPDATE restaurant_ingredients
    SET cout_unitaire = NEW.prix_achat * ratio_epicerie
    WHERE produit_epicerie_id = NEW.id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER epicerie_price_update_trigger
AFTER UPDATE OF prix_achat ON produits
FOR EACH ROW EXECUTE FUNCTION trg_sync_restaurant_prices_on_epicerie_update();
```

## Monitoring and Alerts

### Price Sync Dashboard (Recommended Addition)

Create a monitoring dashboard showing:

1. **Sync Health Metrics:**
   - Total ingredients linked vs manual
   - Sync rate percentage
   - Last sync timestamp
   - Number of out-of-sync ingredients

2. **Price Change Alerts:**
   - Ingredients with significant price increases (>10%)
   - Dishes with margins below threshold after sync
   - Ingredients that need attention

3. **Historical Trends:**
   - Price evolution over time
   - Impact on dish margins

### Sample Monitoring Query

```sql
-- Find ingredients with prices significantly different from epicerie
SELECT
    ri.id,
    ri.nom AS ingredient,
    ri.cout_unitaire AS current_price,
    p.prix_achat AS epicerie_price,
    (p.prix_achat * ri.ratio_epicerie) AS synced_price_would_be,
    ROUND(
        ((p.prix_achat * ri.ratio_epicerie - ri.cout_unitaire) / ri.cout_unitaire * 100)::numeric,
        2
    ) AS price_diff_pct
FROM restaurant_ingredients ri
JOIN produits p ON p.id = ri.produit_epicerie_id
WHERE ri.produit_epicerie_id IS NOT NULL
  AND ABS(ri.cout_unitaire - (p.prix_achat * ri.ratio_epicerie)) > 0.01
ORDER BY price_diff_pct DESC;
```

## Best Practices

### 1. Linking Ingredients to Epicerie

When creating/editing ingredients, always link to epicerie products when possible:

```javascript
// Frontend - Create ingredient with epicerie link
await createIngredientMutation.mutateAsync({
  nom: "Tomates",
  unite_base: "kg",
  cout_unitaire: 0,  // Will be synced from epicerie
  produit_epicerie_id: 42,
  ratio_epicerie: 1.0
});
```

### 2. Setting the Ratio

The `ratio_epicerie` handles unit conversions:

- **Same unit:** ratio = 1.0 (kg → kg)
- **kg to 100g:** ratio = 0.1
- **kg to g:** ratio = 0.001
- **piece to kg:** ratio = (average weight in kg)

### 3. Manual vs Automatic Pricing

Use manual pricing (`produit_epicerie_id = NULL`) for:
- Prepared ingredients (e.g., homemade sauces)
- Labor costs
- Non-food items
- Ingredients not in epicerie catalog

Use epicerie pricing for:
- Raw ingredients
- Products purchased from suppliers
- Items with variable market prices

### 4. Price Sync Safety

The sync only updates when:
- Ingredient has `produit_epicerie_id` set
- Epicerie product has valid `prix_achat` > 0
- Price difference > 0.01€ (unless force_update=true)

This prevents accidental overwriting of manual prices.

## Testing

### Manual Test Scenario

1. **Setup:**
   ```sql
   -- Create test epicerie product
   INSERT INTO produits (nom, prix_achat) VALUES ('Test Tomato', 10.00);

   -- Create test ingredient linked to it
   INSERT INTO restaurant_ingredients (nom, cout_unitaire, produit_epicerie_id, ratio_epicerie)
   VALUES ('Test Ingredient', 8.00, (SELECT id FROM produits WHERE nom = 'Test Tomato'), 1.0);
   ```

2. **Update Epicerie Price:**
   ```sql
   UPDATE produits SET prix_achat = 12.00 WHERE nom = 'Test Tomato';
   ```

3. **Run Sync:**
   ```bash
   curl -X POST http://localhost:8000/api/restaurant/ingredients/sync-prices
   ```

4. **Verify:**
   ```sql
   SELECT cout_unitaire FROM restaurant_ingredients WHERE nom = 'Test Ingredient';
   -- Should return 12.00
   ```

## Future Enhancements

1. **Batch Import Integration:**
   - Automatically trigger price sync after invoice imports
   - Include sync summary in import results

2. **Price Approval Workflow:**
   - Flag significant price changes for review before applying
   - Admin approval for changes > X%

3. **Historical Price Analytics:**
   - Track price volatility by ingredient/supplier
   - Predict future costs based on trends

4. **Multi-Supplier Support:**
   - Link ingredient to multiple epicerie products
   - Choose best price or preferred supplier

5. **Recipe Cost Forecasting:**
   - Simulate dish costs with forecasted ingredient prices
   - Alert when margins will drop below threshold

## Troubleshooting

### Problem: Prices Not Syncing

**Check:**
1. Ingredient has `produit_epicerie_id` set:
   ```sql
   SELECT id, nom, produit_epicerie_id FROM restaurant_ingredients WHERE produit_epicerie_id IS NULL;
   ```

2. Epicerie product has valid price:
   ```sql
   SELECT p.id, p.nom, p.prix_achat
   FROM produits p
   JOIN restaurant_ingredients ri ON ri.produit_epicerie_id = p.id
   WHERE p.prix_achat IS NULL OR p.prix_achat <= 0;
   ```

3. Check sync status:
   ```bash
   curl http://localhost:8000/api/restaurant/ingredients/price-sync-status
   ```

### Problem: Incorrect Prices After Sync

**Likely cause:** Incorrect `ratio_epicerie` value

**Fix:**
```sql
-- Update ratio for specific ingredient
UPDATE restaurant_ingredients
SET ratio_epicerie = 0.1  -- Example: kg to 100g
WHERE id = 42;

-- Re-run sync
```

### Problem: Price History Not Recording

**Check trigger is installed:**
```sql
SELECT tgname FROM pg_trigger
WHERE tgname = 'restaurant_ingredient_price_history_trigger';
```

**Reinstall if missing:**
```sql
-- Run the trigger creation SQL from db/init.sql
```

## Summary

The ingredient price auto-sync feature provides:

✅ **Automatic price updates** from epicerie to restaurant ingredients
✅ **Unit conversion** via ratio_epicerie
✅ **Price history tracking** via database trigger
✅ **Frontend visibility** of price sources (epicerie vs manual)
✅ **Automatic margin recalculation** after sync
✅ **Monitoring and reporting** via API endpoints

The system is designed to work in three modes:
1. **Real-time** (via COALESCE in list_plats query)
2. **Scheduled** (via periodic sync job)
3. **On-demand** (via API endpoint)

All modes ensure that restaurant dish costs and margins stay accurate as supplier prices change.
