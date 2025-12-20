# Plats Add/Delete Feature - Flow Diagrams

## Create Plat Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     PlatsCatalogPage.jsx                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ User clicks "Nouveau plat"
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Create Modal Opens                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Form Fields:                                             │  │
│  │  • Nom du plat (required)                                 │  │
│  │  • Catégorie (dropdown)                                   │  │
│  │  • Prix de vente TTC                                      │  │
│  │  • Actif (checkbox)                                       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ User submits form
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              useCreateRestaurantPlat (Hook)                      │
│  • useOfflineCreate wrapper                                     │
│  • Queues mutation if offline                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ POST /restaurant/plats
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Backend: /api/restaurant.py                         │
│  @router.post("/plats")                                         │
│  • Validates payload (RestaurantPlatCreate)                     │
│  • Calls restaurant_service.create_plat()                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│       Backend: /services/restaurant/ingredients.py               │
│  def create_plat(tenant_id, payload):                           │
│  1. Get restaurant_id for tenant                                │
│  2. INSERT INTO restaurant_plats                                │
│  3. Calculate initial costs (0.0)                               │
│  4. Call refresh_plat_costs()                                   │
│  5. Return plat with margins                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Returns created plat
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Success Actions                      │
│  • Close modal                                                  │
│  • Reset form state                                             │
│  • Invalidate queries: ['restaurant', 'plats']                  │
│  • Invalidate queries: ['restaurant', 'dashboard']              │
│  • Table auto-refreshes                                         │
│  • Stats update                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Delete Plat Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     PlatsCatalogPage.jsx                         │
│  User clicks "Détails" on a plat                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PlatDetailModal.jsx                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Header: Plat name, category, status                     │  │
│  │  KPIs: Prix TTC, Coût matière, Marge, Food Cost         │  │
│  │  Tabs: Fiche technique | Historique | Simulateur         │  │
│  │  Footer: [Supprimer ce plat]           [Fermer]          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ User clicks "Supprimer ce plat"
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Confirmation UI Appears                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  ⚠️ Confirmer la suppression ?                           │  │
│  │  [Oui, supprimer]  [Annuler]                             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ User confirms deletion
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              useDeleteRestaurantPlat (Hook)                      │
│  • useOfflineDelete wrapper                                     │
│  • Queues mutation if offline                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ DELETE /restaurant/plats/{plat_id}
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Backend: /api/restaurant.py                         │
│  @router.delete("/plats/{plat_id}")                             │
│  • Validates plat_id                                            │
│  • Calls restaurant_service.delete_plat()                       │
│  • Catches RuntimeError if not found                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│       Backend: /services/restaurant/ingredients.py               │
│  def delete_plat(tenant_id, plat_id):                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Transaction (conn.begin()):                             │   │
│  │                                                          │   │
│  │ Step 1: Delete related ingredients                      │   │
│  │ DELETE FROM restaurant_plat_ingredients                  │   │
│  │ WHERE plat_id = :plat_id                                │   │
│  │                                                          │   │
│  │ Step 2: Delete the plat itself                          │   │
│  │ DELETE FROM restaurant_plats                             │   │
│  │ WHERE id = :plat_id                                     │   │
│  │ RETURNING id, nom                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│  • Raises RuntimeError if not found                            │
│  • Returns {deleted: true, id, nom}                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Returns deletion result
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Success Actions                      │
│  • Close detail modal                                           │
│  • Invalidate queries: ['restaurant', 'plats']                  │
│  • Invalidate queries: ['restaurant', 'dashboard']              │
│  • Table auto-refreshes (plat removed)                          │
│  • Stats update                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

```
PlatsCatalogPage.jsx (Main Page)
├── Header Section
│   ├── Title & Description
│   └── Stats Cards + [Nouveau plat] Button ◄── CREATE TRIGGER
│
├── Filters Card
│   ├── Search Input
│   ├── Category Filter
│   ├── Margin Filter
│   └── Status Filter
│
├── SmartTable (Plats List)
│   ├── Columns: Nom, Prix TTC, Coût matière, Marge, Food Cost, Statut
│   └── Actions: [Détails] Button ◄── Opens Detail Modal
│
├── PlatDetailModal ◄── DETAIL + DELETE
│   ├── Header (Plat info)
│   ├── KPIs Row
│   ├── Tabs (Fiche technique, Historique, Simulateur)
│   ├── Content Area
│   │   ├── Ingredients List
│   │   ├── Add Ingredient Form
│   │   └── Charts
│   └── Footer
│       ├── [Supprimer ce plat] ◄── DELETE TRIGGER
│       └── [Fermer]
│
└── Create Modal ◄── CREATE FORM
    ├── Header
    ├── Form Fields
    │   ├── Nom (required)
    │   ├── Catégorie (dropdown)
    │   ├── Prix de vente TTC
    │   └── Actif (checkbox)
    └── Actions
        ├── [Annuler]
        └── [Créer le plat]
```

## Data Flow & State Management

```
React Query Cache Structure:
│
├── ['restaurant', 'plats'] ◄── Main plats list
│   └── Invalidated on: CREATE, DELETE
│
├── ['restaurant', 'dashboard'] ◄── Dashboard stats
│   └── Invalidated on: CREATE, DELETE
│
├── ['restaurant', 'ingredients'] ◄── Ingredients for dropdown
│   └── Used in: PlatDetailModal ingredient search
│
└── ['epicerie', 'products'] ◄── Epicerie products
    └── Used in: PlatDetailModal ingredient search

Local Component State:
│
PlatsCatalogPage:
├── search (filter state)
├── categoryFilter
├── marginFilter
├── statusFilter
├── selectedPlat (for detail modal)
├── showCreateModal (modal visibility)
└── newPlat (form state)

PlatDetailModal:
├── currentPlat (local copy)
├── activeTab (fiche/history/simulator)
├── newIngredient (add ingredient form)
├── editingIngredient (inline edit state)
├── deleteConfirm (ingredient delete confirm)
├── showDeletePlatConfirm ◄── DELETE PLAT CONFIRM
└── error (error messages)
```

## API Endpoints Summary

```
POST   /restaurant/plats
       • Creates new plat
       • Body: { nom, categorie?, prix_vente_ttc?, actif? }
       • Returns: RestaurantPlat with calculated margins

DELETE /restaurant/plats/{plat_id}
       • Deletes plat and cascades to ingredients
       • Returns: { deleted: true, id, nom }
       • Error: 400 if not found

GET    /restaurant/plats
       • Lists all plats with margins
       • Returns: RestaurantPlat[]
```

## Mutation Hooks

```javascript
// CREATE
useCreateRestaurantPlat()
  → useOfflineCreate()
    → api.post('/restaurant/plats', payload)
      → Invalidates: ['restaurant', 'plats'], ['restaurant', 'dashboard']

// DELETE
useDeleteRestaurantPlat()
  → useOfflineDelete()
    → api.delete('/restaurant/plats/${platId}')
      → Invalidates: ['restaurant', 'plats'], ['restaurant', 'dashboard']
```

## Error Handling

```
Frontend:
├── Form Validation
│   └── Nom required (native HTML5 validation)
│
├── Mutation Errors
│   ├── Network errors (offline queue)
│   ├── 400 errors (plat not found)
│   └── 500 errors (server errors)
│
└── UI Feedback
    ├── Loading states (buttons disabled, text changes)
    ├── Error banner (with dismiss button)
    └── Success feedback (modal close, data refresh)

Backend:
├── DELETE endpoint
│   ├── RuntimeError → 400 if plat not found
│   └── Generic Exception → 500
│
└── Service layer
    ├── Database transaction rollback on error
    └── Descriptive error messages
```

## UI States & Transitions

```
Create Modal States:
┌──────────┐
│  Closed  │
└────┬─────┘
     │ Click "Nouveau plat"
     ▼
┌──────────┐     Submit form
│   Open   ├──────────────────┐
│ (Idle)   │                  │
└────┬─────┘                  ▼
     │                  ┌──────────┐
     │ Cancel          │ Loading  │
     │                  └────┬─────┘
     │                       │ Success
     │                       ▼
     └─────────────────┌──────────┐
                       │  Closed  │
                       │(Refresh) │
                       └──────────┘

Delete Button States:
┌──────────────┐
│    Normal    │ "Supprimer ce plat"
└──────┬───────┘
       │ Click
       ▼
┌──────────────┐
│ Confirmation │ "⚠️ Confirmer ?"
│              │ [Oui] [Annuler]
└──────┬───────┘
       │ Confirm
       ▼
┌──────────────┐
│   Loading    │ "Suppression..."
└──────┬───────┘
       │ Success
       ▼
┌──────────────┐
│Modal Closed  │
│Data Refreshed│
└──────────────┘
```
