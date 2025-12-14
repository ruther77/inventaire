# Composants Frontend React - Restaurant Overview & Food Cost

## Vue d'ensemble

Ce document décrit les nouveaux composants React créés pour le module Restaurant Overview & Food Cost (Scénario UX 4.7).

## Structure des fichiers

```
frontend/src/features/restaurant/
├── RestaurantOverviewPage.jsx       # Dashboard principal
├── PlatsCatalogPage.jsx             # Catalogue des plats
├── IngredientsPage.jsx              # Liste des ingrédients
└── components/
    ├── index.js                      # Exports centralisés
    ├── RestaurantKPICards.jsx        # Cartes KPI
    ├── FoodCostAnalysisPanel.jsx     # Analyse food cost
    ├── RestaurantAlertsWidget.jsx    # Widget alertes
    ├── CostBreakdownChart.jsx        # Graphique décomposition coûts
    ├── PriceSimulatorPanel.jsx       # Simulateur de prix
    └── PlatDetailModal.jsx           # Modal détails plat
```

## Pages principales

### 1. RestaurantOverviewPage.jsx

**Path:** `/restaurant/overview`

**Description:** Dashboard principal pour le suivi du food cost et de la rentabilité restaurant.

**Fonctionnalités:**
- KPIs principaux (CA, Food Cost %, Marge moyenne, Plats actifs)
- Graphique d'évolution du food cost vs objectif
- Analyse par catégorie
- Top 5 plats rentables / non rentables
- Alertes en temps réel
- Export CSV

**APIs utilisées:**
- `GET /restaurant/overview` - Données générales
- `GET /restaurant/alerts` - Alertes
- `GET /restaurant/food-cost/analysis` - Analyse food cost

---

### 2. PlatsCatalogPage.jsx

**Path:** `/restaurant/plats`

**Description:** Catalogue complet des plats avec filtres et vue détaillée.

**Fonctionnalités:**
- Table interactive avec tous les plats
- Filtres: recherche, catégorie, marge, statut
- Indicateurs visuels colorés (vert/jaune/rouge)
- Actions: voir détails, simuler prix
- Modal détails plat complet

**Colonnes table:**
- Nom du plat + catégorie
- Prix vente TTC
- Coût matière
- Marge % (avec badge coloré)
- Food Cost % (avec badge coloré)
- Statut (Actif/Inactif)
- Actions

**Colorisation:**
- Marge: Vert >60%, Jaune 40-60%, Rouge <40%
- Food Cost: Vert <30%, Jaune 30-35%, Rouge >35%

---

### 3. IngredientsPage.jsx

**Path:** `/restaurant/ingredients`

**Description:** Liste des ingrédients avec tendances prix et stocks.

**Fonctionnalités:**
- Table avec tous les ingrédients
- Filtres: recherche, fournisseur, catégorie, tendance
- Sparklines pour tendances prix (30 jours)
- Indicateurs de stock (critique/bas/OK)
- Badges tendance prix (hausse/baisse/stable)

**Colonnes table:**
- Ingrédient + catégorie + fournisseur
- Prix unitaire
- Stock actuel + badge
- Tendance prix
- Sparkline évolution 30j
- Actions

---

## Composants réutilisables

### 1. RestaurantKPICards.jsx

**Props:**
```javascript
{
  data: {
    chiffre_affaire: number,
    food_cost_pct: number,
    marge_moyenne: number,
    plats_actifs: number,
    ca_evolution: number,
    food_cost_evolution: number
  },
  isLoading: boolean
}
```

**Description:** Affiche 4 cartes KPI avec indicateurs visuels colorés.

---

### 2. FoodCostAnalysisPanel.jsx

**Props:**
```javascript
{
  data: {
    evolution: Array<{date, food_cost_pct, objectif}>,
    current: number,
    objectif: number,
    by_category: Array<{category, food_cost_pct, count}>
  },
  isLoading: boolean
}
```

**Description:** Panneau d'analyse du food cost avec:
- Graphique d'évolution avec ligne objectif
- Écart par rapport à l'objectif
- Tendance (hausse/baisse)
- Breakdown par catégorie

**Graphique:** LineChart (Recharts) avec ligne de référence pour l'objectif.

---

### 3. RestaurantAlertsWidget.jsx

**Props:**
```javascript
{
  alerts: Array<{
    id: string,
    type: 'low_margin' | 'high_food_cost' | 'price_increase' | 'stock_alert' | 'rupture',
    severity: 'critical' | 'warning' | 'info',
    title: string,
    description: string,
    value: string
  }>,
  isLoading: boolean
}
```

**Description:** Widget d'alertes avec:
- Groupement par sévérité
- Icônes et badges colorés
- Scroll si > 5 alertes
- État "Aucune alerte" avec icône success

---

### 4. CostBreakdownChart.jsx

**Props:**
```javascript
{
  data: Array<{
    name: string,
    value: number,
    percentage: number,
    unite: string
  }>,
  title: string,
  isLoading: boolean
}
```

**Description:** Graphique en camembert (pie chart) avec:
- PieChart Recharts
- 10 couleurs distinctes
- Légende détaillée à droite
- Tooltip personnalisé avec montant et %

---

### 5. PriceSimulatorPanel.jsx

**Props:**
```javascript
{
  platData: {
    id: string,
    prix_vente_ttc: number,
    cout_matiere: number,
    marge_pct: number,
    food_cost_pct: number
  },
  onSimulate: (newPrice, targetMargin) => void,
  onApply: (newPrice) => Promise<void>,
  isSimulating: boolean
}
```

**Description:** Simulateur de prix avec 2 modes:
- **Mode "Nouveau prix":** Saisir un nouveau prix → calcul marge
- **Mode "Marge cible":** Saisir une marge → calcul prix

**Affichage:**
- Avant/Après (prix, marge, food cost)
- Impact (évolutions en %)
- Avertissements si marge <40% ou food cost >35%
- Boutons "Appliquer" et "Réinitialiser"

**Formules:**
- `marge_pct = (prix - cout) / prix * 100`
- `food_cost_pct = cout / prix * 100`
- `prix = cout / (1 - marge_pct/100)`

---

### 6. PlatDetailModal.jsx

**Props:**
```javascript
{
  plat: {
    id: string,
    nom: string,
    categorie: string,
    prix_vente_ttc: number,
    cout_matiere: number,
    marge_brute: number,
    marge_pct: number,
    food_cost_pct: number,
    actif: boolean,
    ingredients: Array<{
      nom: string,
      quantite: number,
      unite: string,
      prix_unitaire: number,
      cout_total: number
    }>,
    price_history: Array<{
      date: string,
      prix: number,
      evolution: number
    }>
  },
  isOpen: boolean,
  onClose: () => void,
  onUpdatePrice: (platId, newPrice) => Promise<void>
}
```

**Description:** Modal complet avec 3 onglets:

**Onglet 1: Fiche technique**
- Liste des ingrédients avec quantités et coûts
- Total coût matière
- Graphique décomposition (CostBreakdownChart)

**Onglet 2: Historique prix**
- LineChart évolution prix
- Table historique avec dates et évolutions

**Onglet 3: Simulateur**
- PriceSimulatorPanel intégré
- Bouton "Appliquer" pour mise à jour

**Taille:** `xl` (max-width: 1200px)

---

## API Endpoints

### Nouveaux endpoints ajoutés dans `client.js`

```javascript
// Restaurant Overview
export const fetchRestaurantOverview = async (filters = {})
  // GET /restaurant/overview?date_from=...&date_to=...

// Détails plat
export const fetchRestaurantPlatDetails = async (platId)
  // GET /restaurant/plats/:platId/detail

// Ingrédients plat
export const fetchRestaurantPlatIngredients = async (platId)
  // GET /restaurant/plats/:platId/cost-breakdown

// Simulation prix
export const simulatePlatPrice = async (platId, payload)
  // POST /restaurant/plats/:platId/simulate-price

// Alertes
export const fetchRestaurantAlerts = async (filters = {})
  // GET /restaurant/alerts?type=...&severity=...

// Analyse food cost
export const fetchRestaurantFoodCostAnalysis = async (filters = {})
  // GET /restaurant/food-cost/analysis?date_from=...&granularity=...
```

---

## Hooks React Query

### Nouveaux hooks ajoutés dans `useRestaurant.js`

```javascript
// Overview
export const useRestaurantOverview = (filters = {})

// Détails plat
export const useRestaurantPlatDetails = (platId)

// Ingrédients plat
export const useRestaurantPlatIngredients = (platId)

// Simulation prix
export const useSimulatePlatPrice = ()

// Alertes
export const useRestaurantAlerts = (filters = {})

// Analyse food cost
export const useRestaurantFoodCostAnalysis = (filters = {})
```

---

## Routes

### Nouvelles routes ajoutées dans `routes.jsx`

```javascript
{
  path: '/restaurant/overview',
  label: 'Overview',
  description: 'Food Cost & Rentabilité',
  icon: Gauge,
  element: <RestaurantOverviewPage />
},
{
  path: '/restaurant/plats',
  label: 'Catalogue Plats',
  description: 'Marges & prix',
  icon: Utensils,
  element: <PlatsCatalogPage />
},
{
  path: '/restaurant/ingredients',
  label: 'Ingrédients',
  description: 'Prix & stocks',
  icon: Package,
  element: <IngredientsPage />
}
```

---

## Design System

### Couleurs utilisées

**Food Cost:**
- Vert (<30%): `emerald-600`
- Jaune (30-35%): `amber-600`
- Rouge (>35%): `rose-600`

**Marge:**
- Vert (>60%): `emerald-600`
- Jaune (40-60%): `amber-600`
- Rouge (<40%): `rose-600`

**Alertes:**
- Critical: `rose` (rouge)
- Warning: `amber` (jaune)
- Info: `blue` (bleu)

### Composants UI utilisés

- `Card`, `CardHeader`, `CardContent` - Conteneurs
- `Button` - Actions
- `Input`, `Select` - Formulaires
- `DataTable` - Tables de données
- `Badge` - Indicateurs statuts
- `Modal` - Fenêtres modales
- `MetricCard`, `MetricCardGroup` - KPIs
- `Sparkline`, `MiniChart` - Graphiques miniatures
- Recharts: `LineChart`, `BarChart`, `PieChart` - Graphiques

---

## États et gestion

### États de chargement

Tous les composants gèrent 3 états:
- **Loading:** Spinner/skeleton
- **Empty:** Message "Aucune donnée"
- **Success:** Affichage des données

### Gestion des erreurs

- Utilisation de React Query pour cache et retry
- Messages d'erreur contextuels
- Fallback gracieux sur données vides

### Performance

- Lazy loading des modals
- Mémoisation des calculs (useMemo)
- Filtres côté client pour réactivité
- Debounce sur recherche (à implémenter si nécessaire)

---

## TODO Backend

Pour que ces composants fonctionnent, le backend doit implémenter:

1. **GET /restaurant/overview** - Données overview avec KPIs
2. **GET /restaurant/alerts** - Alertes restaurant
3. **GET /restaurant/food-cost/analysis** - Analyse food cost
4. **GET /restaurant/plats/:id/details** - Détails complets plat
5. **GET /restaurant/plats/:id/ingredients** - Ingrédients plat
6. **POST /restaurant/plats/:id/simulate-price** - Simulation prix

### Format de données attendu

Voir les props des composants ci-dessus pour les structures de données.

---

## Utilisation

### Import des composants

```javascript
// Pages
import RestaurantOverviewPage from '@/features/restaurant/RestaurantOverviewPage.jsx';
import PlatsCatalogPage from '@/features/restaurant/PlatsCatalogPage.jsx';
import IngredientsPage from '@/features/restaurant/IngredientsPage.jsx';

// Composants réutilisables
import {
  RestaurantKPICards,
  FoodCostAnalysisPanel,
  RestaurantAlertsWidget,
  CostBreakdownChart,
  PriceSimulatorPanel,
  PlatDetailModal,
} from '@/features/restaurant/components';
```

### Exemple d'utilisation

```javascript
// Dans une page custom
import { RestaurantKPICards, FoodCostAnalysisPanel } from '@/features/restaurant/components';
import { useRestaurantOverview, useRestaurantFoodCostAnalysis } from '@/hooks/useRestaurant';

function MyCustomPage() {
  const { data: overview } = useRestaurantOverview();
  const { data: foodCost } = useRestaurantFoodCostAnalysis();

  return (
    <div>
      <RestaurantKPICards data={overview?.kpis} />
      <FoodCostAnalysisPanel data={foodCost} />
    </div>
  );
}
```

---

## Responsive Design

Tous les composants sont **mobile-first** avec breakpoints:
- `md:` 768px+
- `lg:` 1024px+
- `xl:` 1280px+

Grids adaptatives:
- Mobile: 1 colonne
- Tablet: 2 colonnes
- Desktop: 3-4 colonnes

---

## Tests

### Tests à implémenter

1. **RestaurantKPICards.test.jsx** - Affichage KPIs, colorisation
2. **FoodCostAnalysisPanel.test.jsx** - Graphiques, calculs
3. **PriceSimulatorPanel.test.jsx** - Simulation, formules
4. **PlatDetailModal.test.jsx** - Onglets, navigation

### Tests d'intégration

- Navigation entre pages
- Ouverture/fermeture modals
- Filtres et recherche
- Mutations (update prix)

---

## Maintenance

### Points d'attention

- Garder les formules de calcul synchronisées backend/frontend
- Vérifier les seuils de colorisation (30%, 35%, 40%, 60%)
- Maintenir les types d'alertes cohérents
- Documenter les nouveaux endpoints API

### Évolutions futures

- Export PDF des rapports
- Graphiques comparatifs multi-périodes
- Recommandations IA sur prix optimaux
- Historique complet des simulations
- Notifications push sur alertes critiques

---

**Créé le:** 2025-12-12
**Version:** 1.0
**Auteur:** Claude Sonnet 4.5
