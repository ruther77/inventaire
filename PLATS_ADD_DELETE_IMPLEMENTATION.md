# Implementation Summary: Add and Delete Plats Feature

## Overview
This document describes the implementation of the ability to ADD and DELETE plats (dishes) in the restaurant module, maintaining consistency with the existing dark theme design.

## Backend Changes

### 1. API Endpoints (`/backend/api/restaurant.py`)

#### Added DELETE endpoint (line 332-338)
```python
@router.delete("/plats/{plat_id}")
def delete_plat(plat_id: int, tenant: Tenant = Depends(get_restaurant_tenant)):
    """Supprimer un plat et ses ingrédients associés."""
    try:
        return restaurant_service.delete_plat(tenant.id, plat_id)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Features:**
- DELETE `/restaurant/plats/{plat_id}` endpoint
- Cascades deletion to `restaurant_plat_ingredients`
- Returns error if plat not found
- Tenant-scoped for security

#### Existing POST endpoint (line 327-329)
```python
@router.post("/plats", response_model=RestaurantPlat)
def create_plat(payload: RestaurantPlatCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.create_plat(tenant.id, payload.dict())
```

### 2. Service Layer (`/backend/services/restaurant/ingredients.py`)

#### Added `delete_plat` function (lines 641-670)
```python
def delete_plat(tenant_id: int, plat_id: int) -> dict[str, Any]:
    """Delete a plat and cascade to restaurant_plat_ingredients."""
    with get_engine().begin() as conn:
        # First delete all ingredient links (cascade)
        conn.execute(
            text("""
                DELETE FROM restaurant_plat_ingredients
                WHERE tenant_id = :tenant AND plat_id = :plat_id
            """),
            {"tenant": tenant_id, "plat_id": plat_id},
        )

        # Then delete the plat itself
        result = conn.execute(
            text("""
                DELETE FROM restaurant_plats
                WHERE tenant_id = :tenant AND id = :plat_id
                RETURNING id, nom
            """),
            {"tenant": tenant_id, "plat_id": plat_id},
        ).fetchone()

        if not result:
            raise RuntimeError(f"Plat {plat_id} introuvable")

    return {"deleted": True, "id": result.id, "nom": result.nom}
```

**Features:**
- Two-step deletion process (ingredients first, then plat)
- Transaction-safe (uses `begin()` context)
- Returns deleted plat info
- Raises error if plat doesn't exist

### 3. Service Exports (`/backend/services/restaurant/__init__.py`)

Added `delete_plat` to imports and `__all__` exports (lines 55 and 130).

## Frontend Changes

### 1. React Hooks (`/frontend/src/hooks/useRestaurant.js`)

#### Added `useDeleteRestaurantPlat` hook (lines 151-164)
```javascript
export const useDeleteRestaurantPlat = () => {
  const queryClient = useQueryClient();
  return useOfflineDelete({
    endpoint: (variables) => `/restaurant/plats/${variables}`,
    mutationFn: (platId) => api.delete(`/restaurant/plats/${platId}`),
    onSuccess: () => {
      queryClient.invalidateQueries(['restaurant', 'plats']);
      queryClient.invalidateQueries(['restaurant', 'dashboard']);
    },
    metadata: {
      description: 'Suppression d\'un plat',
    },
  });
};
```

**Features:**
- Uses `useOfflineDelete` for offline support
- Invalidates relevant queries on success
- Metadata for offline queue description

#### Existing `useCreateRestaurantPlat` hook (lines 136-149)
Already existed and functional.

### 2. Plats Catalog Page (`/frontend/src/features/restaurant/PlatsCatalogPage.jsx`)

#### Added "Nouveau plat" button (lines 234-240)
```jsx
<Button
  onClick={() => setShowCreateModal(true)}
  className="bg-gradient-to-r from-violet-600 to-pink-600 hover:from-violet-500 hover:to-pink-500 text-white font-medium px-6 py-2.5 rounded-xl flex items-center gap-2 border-0"
>
  <Plus className="w-4 h-4" />
  Nouveau plat
</Button>
```

#### Added Create Plat Modal (lines 325-420)
**Features:**
- Dark theme modal with violet/pink gradient accents
- Form fields:
  - Nom du plat (required)
  - Catégorie (dropdown with existing categories + defaults)
  - Prix de vente TTC
  - Actif checkbox
- Validation and error handling
- Loading states during submission
- Auto-closes on successful creation
- Resets form state

**Form Handler (lines 182-198):**
```javascript
const handleCreatePlat = async (e) => {
  e.preventDefault();
  if (!newPlat.nom.trim()) return;

  try {
    await createPlatMutation.mutateAsync({
      nom: newPlat.nom,
      categorie: newPlat.categorie || null,
      prix_vente_ttc: parseFloat(newPlat.prix_vente_ttc) || 0,
      actif: newPlat.actif,
    });
    setShowCreateModal(false);
    setNewPlat({ nom: '', categorie: '', prix_vente_ttc: '', actif: true });
  } catch (error) {
    console.error('Error creating plat:', error);
  }
};
```

### 3. Plat Detail Modal (`/frontend/src/features/restaurant/components/PlatDetailModal.jsx`)

#### Added Delete Button with Confirmation (lines 602-638)
**Features:**
- Two-state UI: normal and confirmation
- Warning icon and message
- Disabled state during deletion
- Cancel option
- Closes modal on successful deletion
- Error handling with banner

**Delete Handler (lines 258-267):**
```javascript
const handleDeletePlat = async () => {
  setError(null);
  try {
    await deletePlatMutation.mutateAsync(id);
    onClose();
  } catch (err) {
    setError(`Erreur suppression plat: ${err.message}`);
    setShowDeletePlatConfirm(false);
  }
};
```

**UI States:**
- Normal: Shows "Supprimer ce plat" button (rose theme)
- Confirmation: Shows warning icon, confirmation message, "Oui, supprimer" and "Annuler" buttons
- Loading: Button shows "Suppression..." and is disabled

## User Flow

### Creating a Plat
1. User clicks "Nouveau plat" button in header
2. Modal opens with form
3. User fills in:
   - Nom (required)
   - Catégorie (optional)
   - Prix de vente TTC (optional, defaults to 0)
   - Actif checkbox (defaults to true)
4. User clicks "Créer le plat"
5. Modal closes, plat appears in table
6. Dashboard stats refresh automatically

### Deleting a Plat
1. User clicks "Détails" on a plat row
2. Detail modal opens
3. User clicks "Supprimer ce plat" button (bottom left)
4. Confirmation UI appears with warning
5. User clicks "Oui, supprimer" to confirm or "Annuler" to cancel
6. On confirmation:
   - Plat and its ingredients are deleted
   - Modal closes
   - Table refreshes
   - Dashboard stats refresh

## Design Consistency

All UI elements follow the dark theme design system:
- Background: slate-800 with white/5-10 opacity overlays
- Borders: white/10 opacity
- Text: white (primary), slate-400 (secondary)
- Accents: violet-pink gradient for primary actions
- Rose theme for destructive actions
- Rounded corners (xl = 12px)
- Hover states with opacity changes
- Focus rings with violet/pink colors

## Database Schema Compatibility

The implementation assumes the following schema:

```sql
-- restaurant_plats table
CREATE TABLE restaurant_plats (
  id SERIAL PRIMARY KEY,
  tenant_id INT NOT NULL,
  restaurant_id INT,
  nom VARCHAR(255) NOT NULL,
  categorie VARCHAR(100),
  prix_vente_ttc DECIMAL(10,2) DEFAULT 0,
  actif BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- restaurant_plat_ingredients table (cascade delete handled manually)
CREATE TABLE restaurant_plat_ingredients (
  id SERIAL PRIMARY KEY,
  tenant_id INT NOT NULL,
  plat_id INT NOT NULL REFERENCES restaurant_plats(id),
  ingredient_id INT NOT NULL REFERENCES restaurant_ingredients(id),
  quantite DECIMAL(10,3),
  unite VARCHAR(50),
  UNIQUE(plat_id, ingredient_id)
);
```

## Testing Checklist

### Backend
- [x] DELETE endpoint compiles without syntax errors
- [ ] DELETE endpoint returns 200 on success
- [ ] DELETE endpoint returns 400 if plat not found
- [ ] Cascade delete removes all related plat_ingredients
- [ ] POST endpoint creates plat with correct fields
- [ ] Tenant isolation works correctly

### Frontend
- [ ] "Nouveau plat" button opens modal
- [ ] Form validation works (nom required)
- [ ] Creating plat refreshes table and dashboard
- [ ] Delete button shows confirmation UI
- [ ] Deleting plat closes modal and refreshes data
- [ ] Error messages display correctly
- [ ] Loading states work during mutations
- [ ] Dark theme styling is consistent
- [ ] Offline queue works (if offline)

## Files Modified

### Backend
1. `/backend/api/restaurant.py` - Added DELETE endpoint
2. `/backend/services/restaurant/ingredients.py` - Added delete_plat function
3. `/backend/services/restaurant/__init__.py` - Exported delete_plat

### Frontend
1. `/frontend/src/hooks/useRestaurant.js` - Added useDeleteRestaurantPlat hook
2. `/frontend/src/features/restaurant/PlatsCatalogPage.jsx` - Added create modal and button
3. `/frontend/src/features/restaurant/components/PlatDetailModal.jsx` - Added delete button with confirmation

## Next Steps / Improvements

1. Add bulk delete functionality
2. Add duplicate plat feature
3. Add plat export/import
4. Add audit log for plat deletions
5. Add undo functionality for accidental deletions
6. Add search/filter in create modal category dropdown
7. Add validation for duplicate plat names
8. Add toast notifications for success/error messages
