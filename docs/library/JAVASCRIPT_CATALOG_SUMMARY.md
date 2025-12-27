# Catalogue des Fonctions JavaScript/React

> Analyse exhaustive générée automatiquement le 2025-12-21

## Vue d'ensemble

- **Total de fichiers analysés**: 399
- **Total de fonctions/composants**: 1 824
- **Fichier JSON complet**: `javascript_functions_catalog.json`

## Statistiques par type

| Type | Nombre | Pourcentage |
|------|--------|-------------|
| React Components | 639 | 35.0% |
| Arrow Functions | 781 | 42.8% |
| Custom Hooks | 299 | 16.4% |
| Function Declarations | 105 | 5.8% |

## Répartition par catégorie

### Components (689 total)

| Catégorie | Nombre | Description |
|-----------|--------|-------------|
| Components/Generic | 238 | Composants génériques non catégorisés |
| Components/Layout | 92 | Layouts, wrappers, shells |
| Components/Containers | 75 | Cards, panels, sections |
| Components/UI Elements | 39 | Buttons, badges, icons |
| Components/Data Display | 38 | Tables, lists, grids |
| Components/Feedback | 36 | Toasts, alerts, notifications |
| Components/Loading | 36 | Skeletons, spinners, loaders |
| Components/Overlays | 27 | Modals, dialogs, drawers |
| Components/Animation | 19 | Transitions, animated components |
| Components/Charts | 15 | Graphiques et visualisations |
| Components/Navigation | 13 | Menus, sidebars, tabs |
| Components/Forms | 11 | Inputs, selects, form controls |

### Hooks (299 total)

| Catégorie | Nombre | Description |
|-----------|--------|-------------|
| Hooks/Data Fetching | 231 | useQuery, useMutation, API hooks |
| Hooks/State Management | 46 | State, context, reducers |
| Hooks/Custom | 15 | Hooks métier spécifiques |
| Hooks/UI Interaction | 4 | Click, keyboard, scroll |
| Hooks/Responsive | 2 | Media queries, breakpoints |
| Hooks/Accessibility | 1 | A11y helpers |

### API Functions (221 total)

| Catégorie | Nombre | Description |
|-----------|--------|-------------|
| API/Read | 131 | fetch*, get*, search* |
| API/Client | 61 | Configuration, clients HTTP |
| API/Update | 12 | update*, patch*, put* |
| API/Create | 12 | create*, post*, add* |
| API/Delete | 5 | delete*, remove* |

### Utils (20 total)

| Catégorie | Nombre | Description |
|-----------|--------|-------------|
| Utils/Generic | 9 | Utilitaires divers |
| Utils/Formatting | 8 | Format dates, currency, numbers |
| Utils/Validation | 2 | Validation de données |
| Utils/Calculation | 1 | Calculs métier |

### Handlers & Pages

| Catégorie | Nombre | Description |
|-----------|--------|-------------|
| Handlers/Events | 275 | Event handlers (onClick, onChange, etc.) |
| Pages/* | 15 | Page components par module |
| Context/Providers | 12 | Contexts React |
| Uncategorized | 343 | À catégoriser |

## Niveau de réutilisabilité

| Niveau | Nombre | Pourcentage | Description |
|--------|--------|-------------|-------------|
| High | 345 | 18.9% | Très réutilisables (score ≥ 7) |
| Medium | 494 | 27.1% | Réutilisables (score 4-6) |
| Low | 985 | 54.0% | Peu réutilisables (score < 4) |

### Facteurs de réutilisabilité

- Custom hooks (+3 points)
- Dans dossiers `utils/`, `hooks/`, `components/ui` (+2-3 points)
- Exporté (+1 point)
- Peu de dépendances (+1 point)
- Faible complexité (+1 point)
- Nom générique (+1 point)
- Non spécifique à une feature (+1 point)

## Complexité

| Niveau | Nombre | Pourcentage | Complexité cyclomatique |
|--------|--------|-------------|------------------------|
| Low | 683 | 37.4% | < 5 |
| Medium | 655 | 35.9% | 5-10 |
| High | 486 | 26.7% | > 10 |

## Top 20 catégories par volume

1. **Uncategorized** (343) - Nécessite catégorisation manuelle
2. **Handlers/Events** (275) - Event handlers React
3. **Components/Generic** (238) - Composants génériques
4. **Hooks/Data Fetching** (231) - React Query hooks
5. **API/Read** (131) - Fonctions fetch/get
6. **Components/Layout** (92) - Layouts
7. **Components/Containers** (75) - Containers
8. **API/Client** (61) - Client HTTP
9. **Hooks/State Management** (46) - State hooks
10. **Components/UI Elements** (39) - UI basiques
11. **Components/Data Display** (38) - Tables, listes
12. **Components/Feedback** (36) - Feedback utilisateur
13. **Components/Loading** (36) - Loading states
14. **Components/Overlays** (27) - Modals, dialogs
15. **Components/Animation** (19) - Animations
16. **Components/Charts** (15) - Graphiques
17. **Hooks/Custom** (15) - Custom hooks
18. **Components/Navigation** (13) - Navigation
19. **API/Update** (12) - Update operations
20. **API/Create** (12) - Create operations

## Fonctions hautement réutilisables (Top 30)

Les fonctions avec un score de réutilisabilité ≥ 9:

### Custom Hooks (Data Fetching)
- `useABCXYZClassification` (Hooks/Data Fetching, score: 9)
- `useAcknowledgeAlert` (Hooks/Data Fetching, score: 9)
- `useAnomalyDetection*` (Hooks/Data Fetching, score: 9)
- `useAuth*` (Hooks/State Management, score: 9)
- `useBankReconciliation*` (Hooks/Data Fetching, score: 9)
- `useDashboard*` (Hooks/Data Fetching, score: 9)
- `useDebounce*` (Hooks/Utilities, score: 9)
- `useLocalStorage` (Hooks/Utilities, score: 9)
- `useMediaQuery` (Hooks/Responsive, score: 9)

### Utils
- `formatDate`, `formatCurrency`, `formatPercent` (Utils/Formatting, score: 8-9)
- `validateEmail`, `validatePhone` (Utils/Validation, score: 8)

### UI Components
- `Button`, `Badge`, `Card` (Components/UI Elements, score: 8-9)
- `Modal`, `Toast`, `Alert` (Components/Feedback, score: 8)

## Structure des données du catalogue JSON

Chaque fonction contient:

```json
{
  "name": "nomFonction",
  "file": "src/path/to/file.js",
  "type": "React component | arrow function | custom hook | function",
  "signature": "nomFonction(param1, param2 = default)",
  "parameters": [
    {
      "name": "param1",
      "type": "string | number | boolean | object | array | any",
      "default": "valeur par défaut",
      "required": true/false
    }
  ],
  "category": "Components/Generic | Hooks/Data Fetching | API/Read | etc.",
  "description": "Description extraite du JSDoc",
  "dependencies": {
    "packages": ["axios", "react-query"],
    "local": ["./utils"],
    "react": ["react"],
    "hooks": [],
    "components": [],
    "utils": []
  },
  "body_analysis": {
    "uses_state": true/false,
    "uses_effect": true/false,
    "uses_ref": true/false,
    "uses_context": true/false,
    "uses_query": true/false,
    "has_jsx": true/false,
    "is_async": true/false,
    "calls_api": true/false,
    "event_handlers": 0,
    "has_conditional_rendering": true/false,
    "complexity_score": 5
  },
  "jsdoc_full": {
    "description": "",
    "params": [],
    "returns": null,
    "example": "",
    "deprecated": false,
    "since": null,
    "see": []
  },
  "reusability": "High | Medium | Low",
  "reusability_score": 9,
  "is_exported": true/false,
  "is_async": true/false,
  "complexity_score": 5,
  "loc_estimate": 50
}
```

## Utilisation du catalogue

### Rechercher une fonction

```bash
# Rechercher toutes les fonctions de format
jq '.functions_flat | to_entries[] | select(.value.category == "Utils/Formatting")' javascript_functions_catalog.json

# Rechercher les hooks hautement réutilisables
jq '.functions_flat | to_entries[] | select(.value.type == "custom hook" and .value.reusability == "High")' javascript_functions_catalog.json

# Rechercher les fonctions complexes
jq '.functions_flat | to_entries[] | select(.value.complexity_score > 15)' javascript_functions_catalog.json
```

### Navigation par catégorie

Le catalogue est organisé en deux formats:

1. **`functions_by_category`**: Groupé par catégorie (pour navigation)
2. **`functions_flat`**: Liste plate avec clé `file::function` (pour recherche)

## Recommandations

### Fonctions à refactoriser (haute complexité)

Identifier les fonctions avec `complexity_score > 15` et considérer:
- Décomposition en sous-fonctions
- Extraction de logique métier
- Simplification des conditions

### Fonctions à documenter

Prioriser l'ajout de JSDoc pour:
- Fonctions avec `reusability: "High"` sans description
- Utils et helpers partagés
- API functions

### Opportunités de réutilisation

Les fonctions "Low" dans des features spécifiques mais avec faible complexité peuvent être:
- Extraites vers `utils/` ou `hooks/`
- Généralisées pour réutilisation
- Documentées et exportées

## Méthodologie d'analyse

L'analyse utilise:

1. **Parsing par RegEx** pour détecter:
   - Function declarations
   - Arrow functions
   - React components (JSX)
   - Custom hooks (pattern `use*`)

2. **Analyse du corps de fonction** pour détecter:
   - Hooks React utilisés
   - Appels API
   - Handlers d'événements
   - Rendu conditionnel JSX

3. **Catégorisation multi-critères**:
   - Nom de la fonction
   - Chemin du fichier
   - Imports/dépendances
   - Patterns dans le corps
   - Documentation JSDoc

4. **Score de réutilisabilité** (0-11):
   - Type de fonction
   - Emplacement dans l'arborescence
   - Export/visibilité
   - Complexité
   - Dépendances

## Limitations

- **343 fonctions non catégorisées**: Nécessitent revue manuelle
- **JSDoc incomplet**: Beaucoup de fonctions sans documentation
- **Complexité estimée**: Basée sur des heuristiques, pas une analyse de flux complète
- **Types inférés**: Les types sont inférés depuis les valeurs par défaut, pas TypeScript

## Prochaines étapes

1. Catégoriser les 343 fonctions "Uncategorized"
2. Ajouter JSDoc aux fonctions hautement réutilisables
3. Identifier et extraire les fonctions dupliquées
4. Créer des composants réutilisables depuis les patterns récurrents
5. Documenter les APIs publiques

---

**Généré automatiquement** par `analyze_functions_v2.py`
