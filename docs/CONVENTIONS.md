# Guide d'Organisation
## Équipe Développement — Backend & Frontend
### Standards & Bonnes Pratiques 2025
**Version 2.0 — Décembre 2025**

---

## 1. Introduction

Ce document établit les règles, conventions et bonnes pratiques pour le travail collaboratif de notre équipe de développement, couvrant à la fois le backend et le frontend. L'objectif est d'assurer une cohérence maximale dans le code, faciliter l'onboarding des nouveaux membres, et maintenir une qualité élevée sur tous nos projets.

Chaque membre de l'équipe s'engage à respecter ces standards. Toute modification doit être discutée en équipe et documentée via une RFC (Request For Comments).

---

# PARTIE I — BACKEND

## 2. Conventions & Standards

### 2.1 Style Guide

Un style de code unifié est essentiel pour la lisibilité et la maintenabilité. Nous utilisons des outils automatisés pour éviter les débats de formatage.

- ESLint + Prettier ou Biome configurés dans chaque projet
- Configuration partagée via package @company/eslint-config
- Formatage automatique au pre-commit (Husky + lint-staged)
- Aucune exception : tout le code doit passer le lint

### 2.2 Naming Conventions

| Élément | Convention | Exemple |
|---------|------------|---------|
| Variables | camelCase | `userName`, `orderTotal` |
| Constantes | SCREAMING_SNAKE | `MAX_RETRY`, `API_URL` |
| Fonctions | camelCase (verbe) | `getUser()`, `createOrder()` |
| Classes | PascalCase | `UserService`, `OrderRepository` |
| Fichiers | kebab-case | `user-service.ts`, `order.dto.ts` |
| Endpoints API | kebab-case pluriel | `/api/v1/users`, `/api/v1/order-items` |

### 2.3 Conventional Commits

Format obligatoire pour tous les messages de commit :

```
<type>(<scope>): <description>
```

| Type | Usage | Exemple |
|------|-------|---------|
| feat | Nouvelle fonctionnalité | `feat(auth): add OAuth2 support` |
| fix | Correction de bug | `fix(api): handle null response` |
| refactor | Refactoring | `refactor(users): extract validation` |
| docs | Documentation | `docs(readme): update setup` |
| test | Tests | `test(orders): add unit tests` |
| style | CSS, formatage UI | `style(button): update hover state` |
| chore | Maintenance | `chore(deps): upgrade lodash` |

---

## 3. Git Workflow

### 3.1 Trunk-Based Development

Nous pratiquons le trunk-based development pour des intégrations fréquentes et des branches courtes.

- **Branche principale** : `main` (protégée)
- **Branches feature** : `feature/nom-court` (<24h idéalement)
- **Branches hotfix** : `hotfix/description`
- Merge via Pull Request uniquement
- Squash commits avant merge

### 3.2 Workflow Standard

1. Créer une branche depuis main : `git checkout -b feature/ma-feature`
2. Développer avec commits atomiques et messages conventionnels
3. Pousser la branche : `git push -u origin feature/ma-feature`
4. Ouvrir une Pull Request avec description complète
5. Attendre review et approbation (min. 1 reviewer)
6. Résoudre les commentaires si nécessaire
7. Squash & Merge une fois approuvé

### 3.3 Branch Protection Rules

- Pas de push direct sur `main`
- Minimum 1 approbation requise
- CI doit passer (tests, lint, build)
- Conversations résolues avant merge

---

## 4. Code Review

### 4.1 Principes

- **Feedback bienveillant** : critiquer le code, pas la personne
- **Reviews rapides** : objectif < 4h pour débloquer les collègues
- **PR atomiques** : une PR = une feature ou un fix
- **Pair programming** pour sujets complexes ou onboarding

### 4.2 Checklist Code Review

- [ ] Le code compile et les tests passent
- [ ] Les tests unitaires sont présents et pertinents
- [ ] Pas de secrets ou données sensibles exposés
- [ ] Validation des inputs côté serveur
- [ ] Gestion des erreurs appropriée
- [ ] Performance : pas de N+1, requêtes optimisées
- [ ] Logging structuré avec correlation ID
- [ ] Documentation mise à jour si nécessaire
- [ ] Conventions de nommage respectées

---

## 5. Documentation

### 5.1 Documentation Obligatoire

- **README.md** : Setup local en < 10 minutes
- **API Documentation** : OpenAPI/Swagger synchronisé
- **ADR** (Architecture Decision Records) : Choix techniques majeurs
- **Runbooks** : Procédures d'incident
- **CHANGELOG.md** : Historique des versions

### 5.2 ADR Format

```markdown
# ADR-001: [Titre de la décision]

## Statut
Accepté | Proposé | Déprécié

## Contexte
[Pourquoi cette décision est nécessaire]

## Décision
[Ce qui a été décidé]

## Conséquences
[Impacts positifs et négatifs]
```

---

## 6. Testing Backend

### 6.1 Pyramide de Tests

- **Tests unitaires (70%)** : Rapides, isolés, mockés
- **Tests d'intégration (20%)** : API, database
- **Tests E2E (10%)** : Parcours critiques uniquement

### 6.2 Standards

- Coverage minimum : 80% bloquant en CI
- Nommage : `describe('UserService')`, `it('should create user when valid data')`
- Pattern : Given/When/Then (Arrange/Act/Assert)
- Fixtures partagées et factories pour les données de test

---

## 7. CI/CD & Automatisation

### 7.1 Pipeline Standard

1. Lint & Format check
2. Tests unitaires
3. Tests d'intégration
4. Build
5. Security scan (Snyk/Trivy)
6. Deploy staging (auto sur main)
7. Deploy production (manual approval)

### 7.2 Pre-commit Hooks

- Lint (ESLint/Biome)
- Format (Prettier)
- Type check (TypeScript)
- Tests affectés (Jest/Vitest --findRelatedTests)
- Commit message format (commitlint)

### 7.3 Feature Flags

- Nouvelles features derrière un flag par défaut
- Activation progressive : 1% → 10% → 50% → 100%
- Rollback instantané en cas de problème
- Nettoyage des flags après stabilisation (< 30 jours)

---

## 8. Environnement de Développement

### 8.1 Setup Standard

- Docker Compose pour tous les services locaux
- Dev Containers recommandés pour uniformité
- Node.js LTS (version définie dans `.nvmrc`)

### 8.2 Variables d'Environnement

- `.env.example` versionné avec toutes les variables
- `.env` jamais versionné (dans `.gitignore`)
- Secrets via Vault/AWS Secrets Manager en prod
- Validation des env vars au démarrage de l'app

---

# PARTIE II — FRONTEND & UI/UX

## 9. Design System

### 9.1 Principes Fondamentaux

Un Design System partagé est la base de la cohérence UI/UX. Il sert de source unique de vérité entre designers et développeurs.

- **Single Source of Truth** : Figma synchronisé avec le code
- **Tokens Design** : Variables partagées (couleurs, typographie, spacing)
- **Documentation vivante** : Storybook comme référence des composants
- **Versioning** : Le Design System est versionné (semver)
- **Changelog Design** : Toute modification documentée

### 9.2 Design Tokens

| Catégorie | Token | Valeur |
|-----------|-------|--------|
| Couleurs | `--color-primary-500` | `#3182CE` |
| Spacing | `--space-4` | `16px (1rem)` |
| Typography | `--font-size-lg` | `18px (1.125rem)` |
| Border Radius | `--radius-md` | `8px` |
| Shadows | `--shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` |

### 9.3 Structure Design System

```
design-system/
├── tokens/
│   ├── colors.ts
│   ├── typography.ts
│   ├── spacing.ts
│   └── index.ts
├── components/
│   ├── Button/
│   ├── Input/
│   ├── Modal/
│   └── ...
├── patterns/
│   ├── forms/
│   ├── navigation/
│   └── layouts/
└── docs/
    └── storybook/
```

---

## 10. Architecture Composants

### 10.1 Atomic Design

Nous suivons la méthodologie Atomic Design pour structurer nos composants UI.

| Niveau | Description | Exemples |
|--------|-------------|----------|
| Atoms | Éléments de base indivisibles | Button, Input, Label, Icon |
| Molecules | Groupes d'atoms fonctionnels | SearchBar, FormField, Card |
| Organisms | Sections UI complexes | Header, Sidebar, ProductList |
| Templates | Layouts de page | DashboardLayout, AuthLayout |
| Pages | Instances avec données réelles | HomePage, ProfilePage |

### 10.2 Conventions de Composants

- Un composant = un dossier (`Component/index.tsx`, `Component.styles.ts`, `Component.test.tsx`)
- Props typées avec TypeScript (`interface ComponentProps`)
- Composants purs et sans side effects quand possible
- Composition over inheritance
- Exports nommés (pas de default export sauf pages)

### 10.3 Structure Fichier Composant

```tsx
// Button/index.tsx
import { type ButtonProps } from './Button.types';
import { StyledButton } from './Button.styles';

export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading,
  ...props
}: ButtonProps) => {
  return (
    <StyledButton
      variant={variant}
      size={size}
      disabled={isLoading}
      {...props}
    >
      {isLoading ? <Spinner /> : children}
    </StyledButton>
  );
};
```

### 10.4 Naming Conventions Frontend

| Élément | Convention | Exemple |
|---------|------------|---------|
| Composants | PascalCase | `UserCard`, `SearchInput` |
| Hooks | camelCase (use*) | `useAuth`, `useDebounce` |
| Utilitaires | camelCase | `formatDate`, `parseQuery` |
| Constantes | SCREAMING_SNAKE | `API_ROUTES`, `BREAKPOINTS` |
| Types/Interfaces | PascalCase | `UserProps`, `ApiResponse` |
| CSS Classes | kebab-case ou BEM | `card-header`, `btn--primary` |

---

## 11. Accessibilité (a11y)

### 11.1 Standards WCAG 2.2

L'accessibilité n'est pas optionnelle. Nous visons la conformité WCAG 2.2 niveau AA minimum.

- **Perceivable** : Contenu accessible à tous les sens
- **Operable** : Navigation clavier complète
- **Understandable** : Interface prévisible et compréhensible
- **Robust** : Compatible avec les technologies d'assistance

### 11.2 Checklist Accessibilité

- [ ] Contraste minimum 4.5:1 pour le texte normal
- [ ] Focus visible sur tous les éléments interactifs
- [ ] Labels associés à tous les inputs (`htmlFor`/`id`)
- [ ] Alt text sur toutes les images informatives
- [ ] Hiérarchie des headings respectée (h1 → h2 → h3)
- [ ] ARIA labels pour les éléments complexes
- [ ] Skip links pour la navigation
- [ ] Pas de contenu uniquement visuel critique
- [ ] Formulaires avec messages d'erreur explicites
- [ ] Tests avec lecteur d'écran (VoiceOver, NVDA)

### 11.3 Outils de Validation

- **axe DevTools** : Extension navigateur pour audit a11y
- **Lighthouse** : Audit automatisé en CI
- **jest-axe** : Tests unitaires d'accessibilité
- **Storybook a11y addon** : Validation dans le catalogue

---

## 12. Performance Frontend

### 12.1 Core Web Vitals

Objectifs de performance mesurés en production :

| Métrique | Objectif | Description |
|----------|----------|-------------|
| LCP | < 2.5s | Largest Contentful Paint |
| INP | < 200ms | Interaction to Next Paint |
| CLS | < 0.1 | Cumulative Layout Shift |
| TTFB | < 800ms | Time to First Byte |
| FCP | < 1.8s | First Contentful Paint |

### 12.2 Bonnes Pratiques Performance

- **Code splitting** : Lazy loading des routes et composants lourds
- **Tree shaking** : Import spécifiques (pas d'`import *`)
- **Images optimisées** : WebP/AVIF, srcset, lazy loading natif
- **Fonts** : Preload, `font-display: swap`, subset
- **Bundle analysis** : Surveiller la taille des chunks
- **Caching** : Service Worker, HTTP cache headers
- **Prefetch** : Anticipation du chargement des pages suivantes

### 12.3 Optimisation React/Vue

- **Mémoïsation** : `useMemo`, `useCallback`, `React.memo` avec parcimonie
- **Virtualisation** : `react-window` pour longues listes
- **Debounce/Throttle** : Sur les handlers fréquents
- **Suspense + lazy** : Chargement progressif
- **Server Components (RSC)** : Quand applicable (Next.js 14+)

---

## 13. State Management

### 13.1 Hiérarchie du State

Choisir le bon niveau de state selon la portée :

| Type | Usage | Outils |
|------|-------|--------|
| Local | UI temporaire (modals, forms) | `useState`, `useReducer` |
| Shared | Partagé entre composants proches | Context, Zustand, Jotai |
| Server | Données API avec cache | TanStack Query, SWR |
| Global | Auth, theme, préférences | Zustand, Redux Toolkit |
| URL | Filtres, pagination, search | nuqs, `useSearchParams` |

### 13.2 Règles de State

- **Server State First** : TanStack Query pour toutes les données API
- **Colocation** : State au plus proche de son utilisation
- **Single Source of Truth** : Pas de duplication de state
- **Derive don't store** : Calculer plutôt que stocker quand possible
- **URL as State** : Synchroniser filtres/search avec l'URL

### 13.3 Pattern TanStack Query

```tsx
// hooks/useUsers.ts
export const useUsers = (filters: UserFilters) => {
  return useQuery({
    queryKey: ['users', filters],
    queryFn: () => userApi.getUsers(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000,   // 30 minutes
  });
};

// Mutation avec invalidation
export const useCreateUser = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: userApi.createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};
```

---

## 14. Styling & CSS

### 14.1 Approche Recommandée 2025

Ordre de préférence pour le styling :

1. **Tailwind CSS** : Utility-first, excellent DX, tree-shaking natif
2. **CSS Modules** : Scoping automatique, proche du CSS standard
3. **Vanilla Extract** : Type-safe, zero-runtime
4. **Styled Components** : Si besoin de theming dynamique avancé

### 14.2 Conventions Tailwind

- Classes ordonnées : Layout → Spacing → Sizing → Typography → Visual → States
- Extraction en composants plutôt que `@apply` excessif
- Configuration centralisée dans `tailwind.config.ts`
- Plugin `prettier-plugin-tailwindcss` pour l'ordre des classes
- Variants consistants : `hover:`, `focus:`, `dark:`, `sm:`, `md:`, `lg:`

### 14.3 Exemple Tailwind

```html
<button
  className="
    flex items-center justify-center gap-2
    px-4 py-2
    w-full md:w-auto
    text-sm font-medium text-white
    bg-blue-600 rounded-lg shadow-sm
    hover:bg-blue-700 focus:ring-2 focus:ring-blue-500
    disabled:opacity-50 disabled:cursor-not-allowed
    transition-colors
  "
>
  Submit
</button>
```

### 14.4 Variables CSS Custom

- Utiliser les CSS custom properties pour le theming
- Préfixer les variables : `--color-*`, `--space-*`, `--font-*`
- Dark mode via classe `.dark` ou `prefers-color-scheme`

---

## 15. Responsive Design

### 15.1 Breakpoints Standards

| Breakpoint | Valeur | Devices |
|------------|--------|---------|
| xs | < 640px | Mobile portrait |
| sm | ≥ 640px | Mobile landscape, petites tablettes |
| md | ≥ 768px | Tablettes |
| lg | ≥ 1024px | Desktop, laptops |
| xl | ≥ 1280px | Large desktop |
| 2xl | ≥ 1536px | Extra large screens |

### 15.2 Mobile-First Approach

- Styles de base pour mobile, puis media queries pour écrans plus grands
- Touch targets minimum 44x44px sur mobile
- Pas de hover-only interactions sur mobile
- Container queries pour composants vraiment réutilisables

### 15.3 Patterns Responsive

- **Stack to Grid** : Éléments empilés sur mobile, grille sur desktop
- **Off-canvas** : Navigation cachée sur mobile (hamburger menu)
- **Progressive disclosure** : Moins de contenu visible sur petit écran
- **Fluid typography** : `clamp()` pour tailles de police adaptatives

---

## 16. Testing Frontend

### 16.1 Stratégie de Tests

| Type | Coverage | Outils |
|------|----------|--------|
| Unit | 60% | Vitest, Jest, Testing Library |
| Integration | 25% | Testing Library, MSW |
| E2E | 10% | Playwright, Cypress |
| Visual | 5% | Chromatic, Percy |

### 16.2 Testing Library Principles

- **Test behavior, not implementation** : Tester ce que l'utilisateur voit
- **Queries par rôle** : `getByRole` > `getByTestId`
- **User events** : `userEvent` > `fireEvent`
- **Async par défaut** : `findBy*` pour les éléments asynchrones

### 16.3 Exemple Test Composant

```tsx
describe('LoginForm', () => {
  it('should submit credentials when form is valid', async () => {
    const onSubmit = vi.fn();
    render(<LoginForm onSubmit={onSubmit} />);

    await userEvent.type(
      screen.getByLabelText(/email/i),
      'user@example.com'
    );
    await userEvent.type(
      screen.getByLabelText(/password/i),
      'password123'
    );
    await userEvent.click(
      screen.getByRole('button', { name: /sign in/i })
    );

    expect(onSubmit).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'password123',
    });
  });
});
```

### 16.4 Visual Regression Testing

- Storybook + Chromatic pour les composants UI
- Snapshots visuels sur les parcours critiques
- Review obligatoire des changements visuels

---

## 17. Collaboration Design / Dev

### 17.1 Workflow Design-to-Code

1. **Discovery** : Designer et dev alignés sur les besoins
2. **Design** : Maquettes Figma avec composants du Design System
3. **Review Design** : Validation technique avant dev
4. **Handoff** : Specs claires, tokens utilisés, edge cases documentés
5. **Implementation** : Dev avec composants existants
6. **QA Design** : Designer valide l'implémentation

### 17.2 Outils de Collaboration

| Outil | Usage |
|-------|-------|
| Figma | Design, prototypage, Design System source |
| Storybook | Documentation composants, playground, tests visuels |
| Tokens Studio | Sync tokens Figma ↔ Code |
| Zeplin / Figma Dev Mode | Specs, assets export, inspection |
| Linear / Jira | Tickets avec liens vers maquettes |

### 17.3 Checklist Handoff Design

- [ ] Maquettes pour tous les breakpoints (mobile, tablet, desktop)
- [ ] États des composants (default, hover, focus, disabled, loading, error)
- [ ] Empty states et états d'erreur
- [ ] Animations et transitions spécifiées
- [ ] Tokens utilisés (pas de valeurs hardcodées)
- [ ] Textes et copys finaux
- [ ] Assets exportés (icônes, images)
- [ ] Annotations pour comportements complexes

---

## 18. UX Patterns & Bonnes Pratiques

### 18.1 Feedback Utilisateur

- **Loading states** : Skeleton screens plutôt que spinners seuls
- **Optimistic updates** : UI mise à jour avant confirmation serveur
- **Toast notifications** : Feedback non-bloquant pour les actions
- **Inline validation** : Feedback immédiat sur les formulaires
- **Progress indicators** : Pour les actions longues (upload, etc.)

### 18.2 Navigation & Information Architecture

- **Breadcrumbs** : Pour les hiérarchies profondes (> 2 niveaux)
- **Deep linking** : Chaque état significatif a une URL unique
- **Preserving state** : Ne pas perdre le travail utilisateur
- **Consistent navigation** : Menu identique sur toutes les pages

### 18.3 Forms & Inputs

- Labels toujours visibles (pas de placeholder-only)
- Autofocus sur le premier champ
- Validation à la perte de focus (onBlur)
- Messages d'erreur clairs et actionnables
- Auto-save quand approprié
- Confirmation avant actions destructives

### 18.4 Error Handling UX

- **Error boundaries** : Crash gracieux avec options de recovery
- **Retry mechanisms** : Permettre de réessayer facilement
- **Offline support** : Message clair et queue des actions
- **404 pages** : Utiles avec suggestions de navigation

---

# PARTIE III — ORGANISATION ÉQUIPE

## 19. Communication & Ownership

### 19.1 Code Owners

```
# CODEOWNERS
* @team-dev
/src/api/ @team-backend
/src/components/ @team-frontend
/src/design-system/ @team-frontend @team-design
/infrastructure/ @team-devops
```

### 19.2 Processus RFC

1. Créer un document RFC dans `/docs/rfcs/`
2. Partager sur Slack #architecture pour discussion
3. Période de commentaires : 3-5 jours
4. Décision finale par consensus ou vote

### 19.3 Post-Mortems Blameless

- Timeline factuelle des événements
- Analyse des causes racines (5 Whys)
- Actions correctives avec owners et deadlines
- Partage des learnings avec l'équipe

---

## 20. Onboarding

### 20.1 Checklist Premier Jour

- [ ] Accès GitHub/GitLab avec 2FA activé
- [ ] Accès Slack (canaux #dev, #frontend, #design, #incidents)
- [ ] Accès Figma (viewer ou editor selon rôle)
- [ ] Accès outils : Jira/Linear, Notion/Confluence
- [ ] Clone des repos principaux
- [ ] Setup environnement local (README)
- [ ] Lecture de ce guide d'organisation
- [ ] Rencontre avec le buddy/mentor assigné

### 20.2 Checklist Première Semaine

- [ ] Premier commit mergé (fix simple ou doc)
- [ ] Première code review effectuée
- [ ] Navigation dans Storybook et le Design System
- [ ] Compréhension de l'architecture globale
- [ ] Session de pair programming avec un senior

---

## 21. Stack & Outils 2025

### 21.1 Backend

| Catégorie | Outils |
|-----------|--------|
| Langage | TypeScript (strict mode) |
| Runtime | Node.js LTS, Bun |
| Framework | NestJS, Fastify, Hono |
| Database | PostgreSQL, Prisma, Drizzle |
| Tests | Vitest, Jest |
| API Docs | Swagger/OpenAPI |

### 21.2 Frontend

| Catégorie | Outils |
|-----------|--------|
| Framework | React 19, Next.js 15, Vue 3, Nuxt 3 |
| State | TanStack Query, Zustand, Jotai |
| Styling | Tailwind CSS, CSS Modules |
| UI Components | shadcn/ui, Radix UI, Headless UI |
| Forms | React Hook Form, Zod |
| Tests | Vitest, Testing Library, Playwright |
| Documentation | Storybook 8 |

### 21.3 Outils Transverses

| Catégorie | Outils |
|-----------|--------|
| Lint/Format | Biome, ESLint + Prettier |
| CI/CD | GitHub Actions, GitLab CI |
| Monorepo | Turborepo, Nx |
| Design | Figma, Tokens Studio |
| Observabilité | Sentry, OpenTelemetry, Grafana |
| Gestion Projet | Linear, Jira, Notion |

---

## 22. Annexes

### 22.1 Ressources

- *Clean Architecture* — Robert C. Martin
- *Atomic Design* — Brad Frost
- *Refactoring UI* — Adam Wathan & Steve Schoger
- *Don't Make Me Think* — Steve Krug
- *Web Content Accessibility Guidelines (WCAG) 2.2*

### 22.2 Liens

- **Conventional Commits** : conventionalcommits.org
- **Tailwind CSS** : tailwindcss.com
- **Storybook** : storybook.js.org
- **Testing Library** : testing-library.com
- **Web.dev** : web.dev/learn

### 22.3 Équipe

| Rôle | Nom | Contact |
|------|-----|---------|
| Chef de Projet | ruuuzer | rdsk0v3rrid3@gmail.com |
| Développeur IA | Claude IA | Anthropic |
| Développeur IA | OpenAI | OpenAI |

---

> Ce document est vivant et doit évoluer avec l'équipe. Toute suggestion d'amélioration est bienvenue via RFC ou discussion en équipe.
