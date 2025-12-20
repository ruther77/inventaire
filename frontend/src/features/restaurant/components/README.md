# Restaurant Components - Food Cost & Overview

Composants React pour le module Restaurant Overview & Food Cost.

## Composants disponibles

### RestaurantKPICards
Cartes KPI avec indicateurs colorés (CA, Food Cost %, Marge, Plats actifs).

```jsx
import { RestaurantKPICards } from './components';

<RestaurantKPICards
  data={{
    chiffre_affaire: 45000,
    food_cost_pct: 32.5,
    marge_moyenne: 58.3,
    plats_actifs: 42,
    ca_evolution: 5.2,
    food_cost_evolution: -1.3
  }}
  isLoading={false}
/>
```

### FoodCostAnalysisPanel
Panneau d'analyse avec graphique d'évolution et breakdown par catégorie.

```jsx
import { FoodCostAnalysisPanel } from './components';

<FoodCostAnalysisPanel
  data={{
    evolution: [{date: '2025-12-01', food_cost_pct: 31.2}],
    current: 32.5,
    objectif: 30,
    by_category: [{category: 'Entrées', food_cost_pct: 28.5, count: 12}]
  }}
  isLoading={false}
/>
```

### RestaurantAlertsWidget
Widget d'alertes en temps réel avec sévérité colorée.

```jsx
import { RestaurantAlertsWidget } from './components';

<RestaurantAlertsWidget
  alerts={[
    {
      id: '1',
      type: 'low_margin',
      severity: 'critical',
      title: 'Marge critique',
      description: 'Burger Classic a une marge de 25%',
      value: '25%'
    }
  ]}
  isLoading={false}
/>
```

### CostBreakdownChart
Graphique pie chart de décomposition des coûts.

```jsx
import { CostBreakdownChart } from './components';

<CostBreakdownChart
  data={[
    {name: 'Pain burger', value: 0.85, percentage: 20.2, unite: 'unité'}
  ]}
  title="Décomposition des coûts"
  isLoading={false}
/>
```

### PriceSimulatorPanel
Simulateur de prix avec 2 modes (nouveau prix ou marge cible).

```jsx
import { PriceSimulatorPanel } from './components';

<PriceSimulatorPanel
  platData={{
    id: 'plat_123',
    prix_vente_ttc: 12.50,
    cout_matiere: 4.20,
    marge_pct: 66.4,
    food_cost_pct: 33.6
  }}
  onApply={async (newPrice) => {
    await updatePrice(newPrice);
  }}
/>
```

### PlatDetailModal
Modal complet avec 3 onglets (fiche, historique, simulateur).

Supporte l'édition des ingrédients via les mutations :
- POST `/restaurant/plats/{platId}/ingredients`
- PATCH `/restaurant/plats/{platId}/ingredients/{ingredientId}`
- DELETE `/restaurant/plats/{platId}/ingredients/{ingredientId}`

Les ingrédients consomment `unit_price` et `total_cost` (fallback calculé si absents) pour éviter les NaN.

```jsx
import { PlatDetailModal } from './components';

<PlatDetailModal
  plat={{
    id: 'plat_123',
    nom: 'Burger Classic',
    prix_vente_ttc: 12.50,
    ingredients: [...],
    price_history: [...]
  }}
  isOpen={true}
  onClose={() => setOpen(false)}
  onUpdatePrice={async (id, price) => {
    await updatePrice(id, price);
  }}
/>
```

## Import

```javascript
import {
  RestaurantKPICards,
  FoodCostAnalysisPanel,
  RestaurantAlertsWidget,
  CostBreakdownChart,
  PriceSimulatorPanel,
  PlatDetailModal,
} from '@/features/restaurant/components';
```

## Design

### Colorisation

**Food Cost:**
- Vert (<30%): Excellent
- Jaune (30-35%): Acceptable
- Rouge (>35%): À surveiller

**Marge:**
- Vert (>60%): Très bon
- Jaune (40-60%): Correct
- Rouge (<40%): Faible

**Alertes:**
- Critical: Rouge
- Warning: Jaune
- Info: Bleu

## Dépendances

- `@tanstack/react-query` - Gestion état serveur
- `recharts` - Graphiques
- `lucide-react` - Icônes
- `@/components/ui` - Composants de base

## Documentation

Voir `/RESTAURANT_FOOD_COST_COMPONENTS.md` pour documentation complète.
