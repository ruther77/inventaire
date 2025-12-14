"""
Example: How to integrate newCMS restaurant API into main FastAPI app.

Add this code to your backend/main.py
"""

# ============================================================================
# 1. Import the router
# ============================================================================
from newCMS.backend.api import restaurant_router

# ============================================================================
# 2. Include router in FastAPI app
# ============================================================================
# In your main.py, after creating the FastAPI app instance:

# app = FastAPI(title="Inventaire API")
# ... existing routers ...

app.include_router(restaurant_router)  # Add newCMS restaurant & mobile endpoints

# ============================================================================
# 3. Verify routes are mounted
# ============================================================================
# Run the app and check:
# - http://localhost:8000/docs
# - Look for "newcms-restaurant" tag
# - Endpoints:
#   - GET /newcms/restaurant/overview
#   - GET /newcms/mobile/inventory
#   - POST /newcms/mobile/scan
#   - POST /newcms/mobile/adjust

# ============================================================================
# 4. Database indexes (recommended for performance)
# ============================================================================
"""
-- Fast barcode lookup for mobile scanning
CREATE INDEX IF NOT EXISTS idx_ingredients_code_barre
ON ingredients(code_barre) WHERE code_barre IS NOT NULL;

-- Fast ingredient stock alerts
CREATE INDEX IF NOT EXISTS idx_ingredients_stock_alert
ON ingredients(tenant_id, stock_actuel, seuil_alerte);

-- Fast plat costs calculation
CREATE INDEX IF NOT EXISTS idx_plat_ingredients_plat_id
ON plat_ingredients(plat_id, tenant_id);
"""

# ============================================================================
# 5. Optional: Add caching for restaurant overview
# ============================================================================
from functools import lru_cache
from datetime import datetime, timedelta

# Cache restaurant overview for 5 minutes
CACHE_TTL = timedelta(minutes=5)
_cache = {}

def get_cached_restaurant_overview(tenant_id: int):
    """Cache wrapper for restaurant overview (optional optimization)."""
    now = datetime.utcnow()
    cache_key = f"resto_overview_{tenant_id}"

    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if now - timestamp < CACHE_TTL:
            return data

    # Call actual endpoint logic here
    # data = get_restaurant_overview_data(tenant_id)
    # _cache[cache_key] = (data, now)
    # return data
    pass

# ============================================================================
# 6. Mobile app authentication example
# ============================================================================
"""
// Mobile app (React Native / Flutter)
const scanProduct = async (barcode) => {
  const response = await fetch('https://api.example.com/newcms/mobile/scan', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ code_barre: barcode }),
  });

  const result = await response.json();
  if (result.found) {
    console.log('Product:', result.product);
    // Show adjustment UI
  } else {
    console.log('Not found:', result.message);
  }
};

const adjustStock = async (productId, delta, reason) => {
  const response = await fetch('https://api.example.com/newcms/mobile/adjust', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      product_id: productId,
      adjustment: delta,
      adjustment_type: 'delta',
      reason: reason,
      notes: '',
    }),
  });

  return await response.json();
};
"""
