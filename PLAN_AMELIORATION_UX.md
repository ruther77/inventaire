# Plan d'Amélioration Backend & Frontend

## Vision
Transformer l'application d'un outil fonctionnel en une **expérience fluide et invisible** où l'utilisateur accomplit ses tâches sans friction cognitive.

---

# PHASE 1 : FONDATIONS (Priorité Haute)

## 1.1 Backend : Standardisation des Réponses

### Problème actuel
- Réponses API incohérentes (dict vs Pydantic, formats variés)
- Gestion d'erreurs fragmentée
- Logs insuffisants pour le debug

### Actions

#### A. Créer un format de réponse unifié
```python
# backend/schemas/common.py
class APIResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[ErrorDetail] = None
    meta: Optional[dict] = None  # pagination, timing

class ErrorDetail(BaseModel):
    code: str           # "VALIDATION_ERROR", "NOT_FOUND"
    message: str        # Message user-friendly en français
    details: dict = {}  # Contexte technique
    suggestions: list[str] = []  # Actions correctives
```

#### B. Middleware de logging centralisé
- Logger chaque requête avec timing
- Capturer les erreurs avec context
- Tracer les requêtes par request_id

#### C. Handlers d'exception globaux
- Convertir toutes les exceptions en `APIResponse`
- Mapper les codes HTTP aux codes d'erreur internes
- Enrichir les messages d'erreur avec des suggestions

### Critères de succès
- [ ] 100% des endpoints retournent `APIResponse`
- [ ] Temps de réponse moyen loggé
- [ ] Taux d'erreur par endpoint visible

---

## 1.2 Backend : Validation Renforcée

### Problème actuel
- Certains endpoints acceptent `dict` non typé
- Pas de validation des longueurs de chaînes
- Validation côté serveur uniquement

### Actions

#### A. Schémas stricts pour tous les payloads
```python
# Avant
@router.patch("/rules/{rule_id}")
def update_rule(payload: dict): ...

# Après
@router.patch("/rules/{rule_id}")
def update_rule(payload: RuleUpdateRequest): ...
```

#### B. Contraintes sur les champs
```python
class ProductCreate(BaseModel):
    nom: str = Field(..., min_length=2, max_length=200)
    prix_vente: Decimal = Field(..., ge=0, le=999999.99)
    code_barre: str = Field(..., pattern=r"^\d{8,14}$")
```

#### C. Validation métier explicite
- Vérifier les références (fournisseur existe, catégorie valide)
- Rejeter les doublons avec message clair
- Valider les dates (pas de date future pour factures)

### Critères de succès
- [ ] Zéro endpoint avec `dict` non typé
- [ ] Messages d'erreur de validation en français
- [ ] Chaque contrainte expliquée dans l'erreur

---

## 1.3 Frontend : Système de Feedback Unifié

### Problème actuel
- États de chargement incohérents entre pages
- Pas de feedback pour les actions longues
- Toast notifications sans contexte

### Actions

#### A. Provider de feedback global
```jsx
// contexts/FeedbackContext.jsx
const FeedbackContext = createContext({
  showLoading: (message) => {},
  hideLoading: () => {},
  showSuccess: (message, action) => {},
  showError: (error, retryFn) => {},
});
```

#### B. Composant LoadingOverlay intelligent
- Afficher après 300ms (éviter le flash)
- Message contextuel ("Importation en cours...")
- Barre de progression si possible
- Bouton annuler si applicable

#### C. Toast améliorés avec actions
```jsx
// Avant
toast.success("Produit créé");

// Après
toast.success({
  title: "Produit créé",
  description: "WHISKY CHIVAS ajouté au catalogue",
  action: { label: "Voir", onClick: () => navigate(`/products/${id}`) },
  undo: () => deleteProduct(id),
});
```

### Critères de succès
- [ ] Pattern de chargement identique sur toutes les pages
- [ ] Chaque action destructive a un "Annuler"
- [ ] Feedback visible en < 100ms après action

---

# PHASE 2 : ÉTATS CRITIQUES

## 2.1 États Vides Actionnables

### Principe UX
> "Un état vide n'est pas une impasse, c'est une opportunité de guider l'utilisateur."

### Actions

#### A. Composant EmptyState enrichi
```jsx
<EmptyState
  icon={<PackageIcon />}
  title="Aucun produit dans le catalogue"
  description="Commencez par importer une facture fournisseur ou créez manuellement vos produits."
  primaryAction={{ label: "Importer une facture", onClick: goToImport }}
  secondaryAction={{ label: "Créer un produit", onClick: openCreateModal }}
  hint="Astuce : L'import automatique reconnaît Metro, Promocash et Brake."
/>
```

#### B. États vides contextuels par page
| Page | Message | Action primaire |
|------|---------|-----------------|
| Catalogue | "Aucun produit" | Importer facture |
| Historique prix | "Pas d'historique" | Importer factures PDF |
| Transactions | "Aucune transaction" | Importer relevé bancaire |
| Alertes | "Aucune alerte" | (Message positif) |

#### C. Illustrations légères
- SVG minimalistes cohérents avec le design system
- Animation subtile au hover
- Palette cohérente (slate-300 pour les illustrations)

### Critères de succès
- [ ] Chaque liste vide a une action claire
- [ ] Zéro message "Aucune donnée" sans contexte
- [ ] L'utilisateur sait toujours quoi faire ensuite

---

## 2.2 États d'Erreur Récupérables

### Principe UX
> "Error Prevention > Error Recovery. Mais quand l'erreur survient, guidez la résolution."

### Actions

#### A. Composant ErrorState avec diagnostic
```jsx
<ErrorState
  type="network"  // network | validation | permission | server
  title="Connexion au serveur impossible"
  description="Vérifiez votre connexion internet ou réessayez dans quelques instants."
  actions={[
    { label: "Réessayer", onClick: retry, primary: true },
    { label: "Mode hors-ligne", onClick: enableOffline },
  ]}
  technical={process.env.DEV && error.stack}
/>
```

#### B. Retry automatique avec backoff
```jsx
const { data, error, refetch } = useQuery({
  queryKey: ['products'],
  queryFn: fetchProducts,
  retry: 3,
  retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30000),
});
```

#### C. Dégradation gracieuse
- Si une section échoue, ne pas bloquer toute la page
- Afficher les données en cache si disponibles
- Indicateur "Données de X minutes" si stale

### Critères de succès
- [ ] Aucune erreur sans bouton "Réessayer"
- [ ] Erreurs réseau distinguées des erreurs métier
- [ ] Mode dégradé fonctionnel sur chaque page

---

## 2.3 États de Chargement Progressifs

### Principe UX
> "La performance perçue est aussi importante que la performance réelle."

### Actions

#### A. Skeleton screens cohérents
- Utiliser les Skeletons existants systématiquement
- Matcher la structure exacte du contenu final
- Animation shimmer fluide (déjà implémenté)

#### B. Chargement progressif
```jsx
// Afficher le header immédiatement, puis le contenu
<PageHeader title="Catalogue" /> {/* Immédiat */}
<Suspense fallback={<ProductGridSkeleton />}>
  <ProductGrid />  {/* Lazy loaded */}
</Suspense>
```

#### C. Indicateurs de progression
- Barre de progression pour imports (% complété)
- Compteur d'éléments traités
- Estimation du temps restant si > 5s

### Critères de succès
- [ ] Skeleton visible en < 50ms
- [ ] Contenu utile affiché en < 1s
- [ ] Progression visible pour opérations > 2s

---

# PHASE 3 : ACCESSIBILITÉ (WCAG 2.1 AA)

## 3.1 Navigation Clavier

### Actions

#### A. Focus management
```jsx
// Modal avec focus trap
const Modal = ({ open, onClose, children }) => {
  const firstFocusable = useRef();
  const lastFocusable = useRef();

  useEffect(() => {
    if (open) {
      firstFocusable.current?.focus();
      // Trap focus, restore on close
    }
  }, [open]);
};
```

#### B. Skip links
```jsx
<a href="#main-content" className="sr-only focus:not-sr-only">
  Aller au contenu principal
</a>
```

#### C. Raccourcis clavier
| Raccourci | Action |
|-----------|--------|
| `Ctrl+K` | Recherche globale |
| `Ctrl+N` | Nouveau produit |
| `Escape` | Fermer modal/dropdown |
| `?` | Afficher aide raccourcis |

### Critères de succès
- [ ] Navigation complète au clavier
- [ ] Focus visible sur tous les éléments interactifs
- [ ] Ordre de tabulation logique

---

## 3.2 Attributs ARIA

### Actions

#### A. Régions live pour updates dynamiques
```jsx
<div aria-live="polite" aria-atomic="true">
  {loading ? "Chargement des produits..." : `${products.length} produits`}
</div>
```

#### B. Labels explicites
```jsx
// Avant
<button><TrashIcon /></button>

// Après
<button aria-label="Supprimer le produit WHISKY CHIVAS">
  <TrashIcon aria-hidden="true" />
</button>
```

#### C. États dynamiques
```jsx
<button
  aria-expanded={isOpen}
  aria-controls="dropdown-menu"
  aria-haspopup="listbox"
>
```

### Critères de succès
- [ ] Score Lighthouse Accessibility > 95
- [ ] Test avec lecteur d'écran (NVDA/VoiceOver)
- [ ] Audit axe-core sans erreurs critiques

---

## 3.3 Contrastes et Lisibilité

### Actions

#### A. Audit des couleurs
- Vérifier ratio 4.5:1 pour texte normal
- Vérifier ratio 3:1 pour grand texte et icônes
- Ne jamais utiliser la couleur seule pour transmettre l'info

#### B. Indicateurs non-couleur
```jsx
// Avant : rouge seul pour erreur
<span className="text-red-500">{error}</span>

// Après : icône + texte + couleur
<span className="text-red-600 flex items-center gap-2">
  <ExclamationIcon aria-hidden="true" />
  {error}
</span>
```

#### C. Mode sombre (optionnel futur)
- Préparer les variables CSS
- Respecter les mêmes ratios de contraste

---

# PHASE 4 : PERFORMANCE PERÇUE

## 4.1 Optimistic Updates

### Principe
> "Montrer le résultat attendu immédiatement, corriger si erreur."

### Actions

```jsx
const createProduct = useMutation({
  mutationFn: api.createProduct,
  onMutate: async (newProduct) => {
    await queryClient.cancelQueries(['products']);
    const previous = queryClient.getQueryData(['products']);

    // Ajout optimiste
    queryClient.setQueryData(['products'], (old) => [
      ...old,
      { ...newProduct, id: 'temp-' + Date.now(), _optimistic: true }
    ]);

    return { previous };
  },
  onError: (err, newProduct, context) => {
    // Rollback
    queryClient.setQueryData(['products'], context.previous);
    toast.error("Échec de la création");
  },
  onSettled: () => {
    queryClient.invalidateQueries(['products']);
  },
});
```

### Critères de succès
- [ ] Actions CRUD semblent instantanées
- [ ] Rollback invisible si succès
- [ ] Rollback explicite avec message si échec

---

## 4.2 Prefetching Intelligent

### Actions

#### A. Prefetch au hover
```jsx
<Link
  to={`/products/${id}`}
  onMouseEnter={() => queryClient.prefetchQuery(['product', id], () => fetchProduct(id))}
>
```

#### B. Prefetch des pages adjacentes
```jsx
// Sur la liste paginée, prefetch page suivante
useEffect(() => {
  if (hasNextPage) {
    queryClient.prefetchQuery(['products', page + 1], () => fetchProducts(page + 1));
  }
}, [page, hasNextPage]);
```

#### C. Stale-while-revalidate
```jsx
useQuery({
  queryKey: ['products'],
  queryFn: fetchProducts,
  staleTime: 5 * 60 * 1000,  // 5 min
  cacheTime: 30 * 60 * 1000, // 30 min
});
```

---

## 4.3 Code Splitting

### Actions

```jsx
// Routes lazy-loaded
const FinanceModule = lazy(() => import('./features/finance'));
const RestaurantModule = lazy(() => import('./features/restaurant'));

// Composants lourds
const RichTextEditor = lazy(() => import('./components/RichTextEditor'));
const ChartDashboard = lazy(() => import('./components/ChartDashboard'));
```

---

# PHASE 5 : MICRO-INTERACTIONS

## 5.1 Feedback Tactile

### Actions

#### A. Transitions cohérentes
```css
/* Design tokens */
--transition-fast: 150ms ease-out;
--transition-normal: 200ms ease-out;
--transition-slow: 300ms ease-out;

/* Usage */
.button { transition: all var(--transition-fast); }
.modal { transition: opacity var(--transition-normal), transform var(--transition-normal); }
```

#### B. Hover states expressifs
```jsx
// Bouton avec feedback multi-niveaux
<button className="
  transition-all duration-150
  hover:bg-brand-600 hover:shadow-md hover:-translate-y-0.5
  active:bg-brand-700 active:shadow-sm active:translate-y-0
  focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2
">
```

#### C. Animations de succès
```jsx
// Check animé après action réussie
<motion.div
  initial={{ scale: 0 }}
  animate={{ scale: 1 }}
  transition={{ type: "spring", stiffness: 500, damping: 30 }}
>
  <CheckCircleIcon className="text-emerald-500" />
</motion.div>
```

---

## 5.2 Affordance Intelligente

### Actions

#### A. Drag handles explicites
```jsx
<div className="flex items-center gap-2 cursor-grab active:cursor-grabbing">
  <GripVerticalIcon className="text-slate-400" />
  <span>{item.name}</span>
</div>
```

#### B. Zones cliquables généreuses
```jsx
// 44x44px minimum pour touch targets
<button className="min-w-[44px] min-h-[44px] p-3">
  <Icon className="w-5 h-5" />
</button>
```

#### C. États disabled explicites
```jsx
<button
  disabled={!canSubmit}
  className="disabled:opacity-50 disabled:cursor-not-allowed"
  title={!canSubmit ? "Complétez tous les champs requis" : undefined}
>
```

---

# PHASE 6 : DENSITÉ INFORMATIONNELLE

## 6.1 Progressive Disclosure

### Principe
> "Révéler l'information graduellement selon le contexte."

### Actions

#### A. Détails à la demande
```jsx
// Tableau avec row expansion
<DataTable
  expandable
  renderExpanded={(row) => (
    <ProductDetails product={row} />
  )}
/>
```

#### B. Filtres avancés cachés
```jsx
<div>
  <BasicFilters />
  <Collapsible trigger="Filtres avancés">
    <AdvancedFilters />
  </Collapsible>
</div>
```

#### C. Tooltips contextuels
```jsx
<Tooltip content="Marge calculée : (Prix vente - Prix achat) / Prix vente × 100">
  <span className="underline decoration-dotted cursor-help">
    Marge: 35%
  </span>
</Tooltip>
```

---

## 6.2 Zoom Sémantique

### Actions

#### A. Vues alternatives
```jsx
<ViewToggle>
  <ViewToggle.Option value="grid" icon={<GridIcon />} label="Grille" />
  <ViewToggle.Option value="list" icon={<ListIcon />} label="Liste" />
  <ViewToggle.Option value="compact" icon={<RowsIcon />} label="Compact" />
</ViewToggle>
```

#### B. Colonnes configurables
```jsx
<DataTable
  columns={allColumns}
  visibleColumns={userPreferences.columns}
  onColumnsChange={savePreferences}
/>
```

---

# MÉTRIQUES DE SUCCÈS GLOBALES

## Quantitatifs
| Métrique | Actuel | Cible |
|----------|--------|-------|
| Lighthouse Performance | ~70 | > 90 |
| Lighthouse Accessibility | ~60 | > 95 |
| First Contentful Paint | ~2s | < 1s |
| Time to Interactive | ~3s | < 2s |
| Taux d'erreur API | ? | < 0.1% |
| Temps moyen par tâche | ? | -30% |

## Qualitatifs
- [ ] Navigation 100% clavier possible
- [ ] Lecteur d'écran utilisable
- [ ] Aucun état "impasse" (toujours une action possible)
- [ ] Feedback en < 100ms pour chaque action
- [ ] Messages d'erreur toujours actionnables

---

# ORDRE D'IMPLÉMENTATION RECOMMANDÉ

## Sprint 1 (Semaine 1-2)
1. ✅ Corriger les bugs critiques (prix history - FAIT)
2. Standardiser les réponses API (1.1)
3. Implémenter le système de feedback unifié (1.3)

## Sprint 2 (Semaine 3-4)
4. États vides actionnables (2.1)
5. États d'erreur récupérables (2.2)
6. Validation renforcée backend (1.2)

## Sprint 3 (Semaine 5-6)
7. Navigation clavier (3.1)
8. Attributs ARIA (3.2)
9. États de chargement progressifs (2.3)

## Sprint 4 (Semaine 7-8)
10. Optimistic updates (4.1)
11. Micro-interactions (5.1, 5.2)
12. Progressive disclosure (6.1)

## Continu
- Tests accessibilité à chaque PR
- Monitoring performance
- Feedback utilisateurs

---

# RESSOURCES

## Outils de test
- axe DevTools (accessibilité)
- Lighthouse CI (performance)
- React DevTools Profiler
- Chrome DevTools Network throttling

## Documentation
- WCAG 2.1 Guidelines
- React Query Best Practices
- Radix UI Primitives (accessibilité)

## Design System
- Étendre le système existant (`components/ui/`)
- Documenter avec Storybook (optionnel)
- Tokens CSS pour cohérence
