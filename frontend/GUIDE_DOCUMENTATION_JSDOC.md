# Guide de Documentation JSDoc - Frontend React

## Vue d'ensemble

Ce guide fournit les templates et bonnes pratiques pour documenter **TOUS** les fichiers JavaScript/JSX du projet frontend.

**État de la documentation:**
- ✅ **9 hooks essentiels documentés** (useAuth, useFinance, useInvoiceImport, useStock, useDebounce, useLocalStorage, useClickOutside, useCategories, useProducts, useDashboard, useSuppliers)
- ⏳ **411 fichiers restants à documenter**

---

## 1. Templates pour Hooks React

### Hook simple (Query)

```javascript
/**
 * Module de hooks pour [DESCRIPTION DU DOMAINE].
 *
 * @module hooks/[NOM_DU_HOOK]
 */

/**
 * Hook pour [ACTION / RÉCUPÉRATION DE DONNÉES].
 *
 * [Description détaillée du rôle et comportement]
 * [Informations sur le cache, rafraîchissement, etc.]
 *
 * @param {Object} [params] - Paramètres optionnels
 * @param {number} [params.xxx] - Description du paramètre
 *
 * @returns {Object} Query TanStack
 * @property {Array|Object} data - Données retournées
 * @property {boolean} isLoading - Indique si chargement initial
 * @property {boolean} isError - Indique si erreur
 * @property {Function} refetch - Recharge les données
 *
 * @example
 * const { data, isLoading } = useExemple({ xxx: 42 });
 *
 * if (isLoading) return <Skeleton />;
 * return <div>{data.map(...)}</div>;
 */
export function useExemple(params = {}) {
  return useQuery({
    queryKey: ['exemple', params],
    queryFn: () => fetchExemple(params),
    staleTime: 60_000, // 1 minute
  });
}
```

### Hook de mutation (Create/Update/Delete)

```javascript
/**
 * Hook pour [CRÉER/MODIFIER/SUPPRIMER] [RESSOURCE].
 *
 * [Description de l'opération et effets de bord]
 * Affiche automatiquement un toast de succès/erreur.
 * Invalide le cache [LISTE DES CACHES INVALIDÉS].
 *
 * @returns {Object} Mutation TanStack
 * @property {Function} mutate - Fonction pour lancer la mutation
 * @property {boolean} isPending - Indique si mutation en cours
 * @property {boolean} isSuccess - Indique si mutation réussie
 *
 * @example
 * const { mutate: createItem, isPending } = useCreateItem();
 *
 * const handleSubmit = (formData) => {
 *   createItem({
 *     name: formData.name,
 *     description: formData.description
 *   });
 * };
 */
export function useCreateItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: createItem,
    onSuccess: () => {
      toast.success('Élément créé');
      queryClient.invalidateQueries({ queryKey: ['items'] });
    },
    onError: (error) => {
      toast.error(error?.response?.data?.detail || 'Erreur');
    },
  });
}
```

### Hook complexe avec état et effets

```javascript
/**
 * Hook pour [FONCTIONNALITÉ COMPLEXE].
 *
 * Ce hook gère [DESCRIPTION DU WORKFLOW]:
 * 1. [ÉTAPE 1]
 * 2. [ÉTAPE 2]
 * 3. [ÉTAPE 3]
 *
 * @returns {Object} État et contrôles
 * @property {any} value - État actuel
 * @property {Function} action1 - Première action
 * @property {Function} action2 - Deuxième action
 * @property {boolean} isXXX - Indicateur d'état
 *
 * @example
 * const { value, action1, action2, isXXX } = useComplexHook();
 *
 * // Utilisation
 * action1(params);
 */
export function useComplexHook() {
  // États locaux
  const [state, setState] = useState(initialValue);

  // Logique métier avec commentaires inline
  const action1 = useCallback(() => {
    // Explication de la logique
  }, [deps]);

  return {
    value: state,
    action1,
    // ...
  };
}
```

---

## 2. Templates pour Composants React

### Composant Page

```javascript
/**
 * Page [NOM DE LA PAGE].
 *
 * Cette page permet de [FONCTIONNALITÉ PRINCIPALE].
 * Elle affiche:
 * - [ÉLÉMENT 1]
 * - [ÉLÉMENT 2]
 * - [ÉLÉMENT 3]
 *
 * @component
 *
 * @example
 * <ExemplePage />
 */
export default function ExemplePage() {
  // État local
  const [filters, setFilters] = useState({});

  // Chargement des données
  const { data, isLoading } = useData(filters);

  // Gestion des événements
  /**
   * Gère le changement de filtre.
   * @param {string} key - Clé du filtre
   * @param {any} value - Nouvelle valeur
   */
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  if (isLoading) return <Skeleton />;

  return (
    <PageLayout>
      {/* Contenu */}
    </PageLayout>
  );
}
```

### Composant réutilisable avec props

```javascript
/**
 * Composant [NOM DU COMPOSANT].
 *
 * [Description du rôle et utilisation]
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {string} props.title - Titre affiché
 * @param {Array} props.items - Liste des éléments
 * @param {Function} [props.onSelect] - Callback lors de la sélection
 * @param {string} [props.variant='default'] - Variante visuelle
 *
 * @example
 * <ExempleComponent
 *   title="Mon titre"
 *   items={[1, 2, 3]}
 *   onSelect={(item) => console.log(item)}
 *   variant="primary"
 * />
 */
export default function ExempleComponent({
  title,
  items,
  onSelect,
  variant = 'default'
}) {
  /**
   * Gère le clic sur un élément.
   * @param {any} item - Élément cliqué
   */
  const handleClick = (item) => {
    onSelect?.(item);
  };

  return (
    <div className={`component-${variant}`}>
      <h2>{title}</h2>
      {items.map(item => (
        <button key={item} onClick={() => handleClick(item)}>
          {item}
        </button>
      ))}
    </div>
  );
}
```

### Composant avec sous-composants

```javascript
/**
 * Composant de liste complexe.
 *
 * @component
 */
export default function ComplexList({ items }) {
  return (
    <div>
      {items.map(item => (
        <ListItem key={item.id} item={item} />
      ))}
    </div>
  );
}

/**
 * Élément de liste individuel.
 * Sous-composant de ComplexList.
 *
 * @component
 * @private
 *
 * @param {Object} props
 * @param {Object} props.item - Données de l'élément
 */
function ListItem({ item }) {
  return <div>{item.name}</div>;
}
```

---

## 3. Templates pour Utilitaires et Helpers

### Fonction utilitaire

```javascript
/**
 * [Description de la fonction].
 *
 * @param {type} param1 - Description
 * @param {type} param2 - Description
 * @returns {type} Description du retour
 *
 * @example
 * const result = utilityFunction(arg1, arg2);
 */
export function utilityFunction(param1, param2) {
  // Implémentation
}
```

### Constantes et configuration

```javascript
/**
 * Configuration des tokens de design.
 *
 * Définit les couleurs, espacements, typographie
 * utilisés dans l'application.
 *
 * @constant
 * @type {Object}
 */
export const designTokens = {
  colors: {
    primary: '#3B82F6',
    // ...
  },
  // ...
};
```

---

## 4. Bonnes pratiques

### Commentaires inline

Utilisez des commentaires inline pour expliquer la **logique complexe**:

```javascript
export function useComplexLogic() {
  const [state, setState] = useState(null);

  useEffect(() => {
    // Démarrer le polling toutes les 2 secondes
    const interval = setInterval(() => {
      refetch();
    }, 2000);

    // Cleanup: arrêter le polling au démontage
    return () => clearInterval(interval);
  }, [refetch]);

  // Calculer le score de confiance basé sur plusieurs critères
  const confidenceScore = useMemo(() => {
    const matchScore = data.match_ratio * 0.4;
    const historyScore = data.history_matches * 0.3;
    const userScore = data.user_confirmations * 0.3;
    return matchScore + historyScore + userScore;
  }, [data]);

  return { state, confidenceScore };
}
```

### Documenter les effets de bord

Précisez toujours:
- Les mutations de cache (invalidation)
- Les toasts affichés
- Les redirections
- Les appels API

```javascript
/**
 * Hook pour supprimer un produit.
 *
 * ⚠️ Effets de bord:
 * - Invalide le cache des produits
 * - Invalide le cache du stock
 * - Affiche un toast de confirmation
 * - Peut échouer si produit lié à des factures
 */
```

### Documenter les états de chargement

```javascript
/**
 * Hook pour charger les données du dashboard.
 *
 * États possibles:
 * - isLoading: Premier chargement
 * - isFetching: Rafraîchissement en arrière-plan
 * - isError: Erreur de chargement
 * - isSuccess: Données disponibles
 */
```

---

## 5. Priorités de documentation

### HAUTE PRIORITÉ (documenter en premier)

1. **Hooks métier** (`hooks/*.js`):
   - ✅ useAuth.js
   - ✅ useFinance.js
   - ✅ useInvoiceImport.js
   - ✅ useStock.js
   - ✅ useCategories.js
   - ✅ useProducts.js
   - ✅ useDashboard.js
   - ✅ useSuppliers.js
   - ⏳ useRestaurant.js
   - ⏳ useCheckout.js
   - ⏳ useCatalogMutations.js
   - ⏳ (etc. - 45 hooks restants)

2. **Pages principales** (`features/*/[Page].jsx`):
   - ⏳ DashboardPage.jsx
   - ⏳ FinanceTransactionsPage.jsx
   - ⏳ ImportPage.jsx (invoices)
   - ⏳ CatalogPage.jsx
   - ⏳ StockPage.jsx

3. **API Client** (`api/*.js`):
   - ⏳ client.js (toutes les fonctions d'API)

### PRIORITÉ MOYENNE

4. **Composants features** (`features/**/*.jsx`):
   - Composants métier spécifiques
   - Formulaires complexes
   - Tableaux avec logique

5. **Composants layout** (`components/layout/*.jsx`):
   - PageLayout
   - SidebarNav
   - TopBar

### PRIORITÉ BASSE

6. **Composants UI** (`components/ui/*.jsx`):
   - Beaucoup ont déjà des commentaires basiques
   - Button, Card, Input, Modal, etc.

7. **Utilitaires** (`utils/*.js`, `lib/*.js`):
   - Helpers et fonctions pures

---

## 6. Checklist par fichier

Pour chaque fichier, vérifier:

- [ ] En-tête de module `@module`
- [ ] Description générale du fichier
- [ ] Chaque fonction/hook documenté avec:
  - [ ] Description claire
  - [ ] Tous les `@param` avec types
  - [ ] `@returns` avec type et description
  - [ ] Au moins un `@example` concret
- [ ] Commentaires inline pour logique complexe
- [ ] Documentation des effets de bord
- [ ] Documentation des états de chargement

---

## 7. Outils et validation

### Génération de documentation

```bash
# Installer JSDoc
npm install -D jsdoc

# Générer la doc HTML
npx jsdoc -c jsdoc.json
```

### Configuration jsdoc.json

```json
{
  "source": {
    "include": ["frontend/src"],
    "includePattern": ".+\\.(js|jsx)$"
  },
  "opts": {
    "destination": "./docs/jsdoc",
    "recurse": true
  },
  "plugins": ["plugins/markdown"],
  "templates": {
    "cleverLinks": true,
    "monospaceLinks": true
  }
}
```

### Validation avec ESLint

Ajouter le plugin `eslint-plugin-jsdoc`:

```bash
npm install -D eslint-plugin-jsdoc
```

---

## 8. Fichiers documentés

### Hooks (9/54)

✅ **Complètement documentés:**
1. `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useAuth.js`
2. `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useFinance.js`
3. `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useInvoiceImport.js`
4. `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useStock.js`
5. `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useCategories.js`
6. `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useProducts.js`
7. `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useDashboard.js`
8. `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useSuppliers.js`

✅ **Déjà bien documentés (vérifiés):**
9. `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useDebounce.js`
10. `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useLocalStorage.js`
11. `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useClickOutside.js`

⏳ **Hooks à documenter (43 restants)**

---

## 9. Template rapide (copier-coller)

Pour gagner du temps, utilisez ce template et adaptez:

```javascript
/**
 * Module [DESCRIPTION].
 * @module [PATH]
 */

/**
 * [FONCTION].
 *
 * [DÉTAILS]
 *
 * @param {Object} [params] - Paramètres
 * @returns {Object} Résultat
 *
 * @example
 * const result = maFonction();
 */
export function maFonction(params = {}) {
  // Implémentation
}
```

---

## Contact et Support

Pour toute question sur la documentation:
- Référez-vous aux exemples dans les 9 hooks déjà documentés
- Suivez les templates de ce guide
- Maintenez la cohérence avec la documentation existante

**Objectif:** 420 fichiers documentés à 100% en français avec JSDoc exhaustif.
