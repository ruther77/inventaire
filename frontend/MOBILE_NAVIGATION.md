# Navigation Mobile - Bottom Bar

## Vue d'ensemble

Implémentation d'une navigation mobile moderne avec bottom bar pour l'application Inventaire Pro.

## Architecture

### Fichiers créés

1. **`src/hooks/useMobileNav.js`**
   - Hook personnalisé pour gérer l'état de la navigation mobile
   - Détecte la route active
   - Gère l'ouverture/fermeture du menu "Plus"
   - Sépare les items principaux (4) et secondaires (2)

2. **`src/components/layout/MobileBottomNav.jsx`**
   - Composant principal de la bottom bar
   - Affiche 4 items principaux + bouton "Plus"
   - Animations Framer Motion (tap, scale, spring)
   - Icônes SVG inline optimisées
   - Safe area padding pour iPhone avec notch
   - Indicateurs visuels pour l'item actif

3. **`src/components/layout/MobileMoreMenu.jsx`**
   - Menu slide-up depuis le bottom nav
   - Affiche Intelligence et Paramètres
   - Backdrop semi-transparent
   - Animation entrée/sortie fluide
   - Fermeture au tap outside

### Fichiers modifiés

1. **`src/components/layout/BottomNav.jsx`**
   - Simplifié pour utiliser le nouveau composant MobileBottomNav
   - Garde la compatibilité avec AppShell

2. **`src/hooks/index.js`**
   - Export du hook useMobileNav pour utilisation dans l'app

## Fonctionnalités

### Bottom Navigation Bar

- **4 items principaux visibles**:
  - Cockpit (Gauge icon)
  - Opérations (ShoppingBag icon)
  - Finances (Wallet icon)
  - Restaurant (Utensils icon)

- **1 bouton "Plus"**:
  - Affiche un menu avec les items secondaires
  - Icône: MoreHorizontal (rotation 90° à l'ouverture)
  - Indicateur visuel si un item secondaire est actif

### Items secondaires (menu Plus)

- Intelligence (Brain)
- Paramètres (Settings)

### Animations

- **Tap animation**: Scale 0.92 avec spring
- **Active indicator**: Barre en haut de l'item avec gradient
- **Pulse effect**: Animation continue quand l'item est actif
- **Active dot**: Point lumineux en haut à droite de l'icône
- **Menu slide-up**: Spring animation pour l'ouverture du menu Plus

### Indicateurs visuels

- **Active item**:
  - Barre gradient en haut
  - Icône avec gradient background
  - Pulse effect continu
  - Dot indicateur
  - Label en blanc

- **Inactive item**:
  - Icône avec fond semi-transparent
  - Label en gris

### Responsive

- Visible uniquement sur mobile (< lg breakpoint)
- Masqué sur desktop (affiche la sidebar classique)
- Safe area padding pour iPhone X et ultérieurs

## Usage

Le composant est déjà intégré dans `AppShell.jsx`. Rien à faire!

```jsx
import BottomNav from '../components/layout/BottomNav.jsx';

// Dans AppShell
<BottomNav />
```

### Utiliser le hook useMobileNav

Si vous avez besoin d'accéder à l'état de la navigation mobile dans un autre composant:

```jsx
import { useMobileNav } from '@/hooks';

function MyComponent() {
  const {
    primaryItems,      // 4 items principaux
    secondaryItems,    // 2 items secondaires
    activeItem,        // Item actif actuellement
    isMoreMenuOpen,    // État du menu Plus
    isSecondaryActive, // Un item secondaire est-il actif?
    toggleMoreMenu,    // Toggle le menu Plus
    isItemActive,      // Function: vérifie si un path est actif
  } = useMobileNav();

  // ...
}
```

## Personnalisation

### Ajouter un item principal

Modifier `useMobileNav.js`:

```js
const primaryItems = useMemo(() => {
  return [
    // ... items existants
    {
      id: 'nouvel-item',
      label: 'Label',
      path: '/chemin',
      section: navigationSections.find(s => s.id === 'section-id'),
    },
  ];
}, []);
```

Et ajouter l'icône correspondante dans `MobileBottomNav.jsx`:

```js
const iconMap = {
  // ... icônes existantes
  'nouvel-item': IconName,
};
```

### Modifier les couleurs

Les couleurs sont définies dans les sections de navigation (`routes.jsx`):

```js
{
  id: 'section-id',
  gradient: 'from-blue-500 to-purple-600',
  color: 'blue',
  // ...
}
```

## Performance

- **SVG icons inline**: Évite les requêtes HTTP supplémentaires
- **Framer Motion**: Animations GPU-accelerated
- **Safe area CSS**: `env(safe-area-inset-bottom)`
- **Backdrop filter**: Hardware-accelerated blur
- **Touch optimizations**: `touchAction`, `WebkitTapHighlightColor`

## Accessibilité

- Labels aria pour les boutons
- Touch targets minimums (40px+)
- Keyboard navigation support (via NavLink)
- Reduced motion support (via Framer Motion)

## Compatibilité

- iOS 12+ (safe-area-inset)
- Android 5+ (backdrop-filter avec fallback)
- Tous les navigateurs modernes
