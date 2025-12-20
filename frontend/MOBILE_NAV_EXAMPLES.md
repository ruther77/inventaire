# Exemples d'utilisation - Mobile Navigation

## Table des matières

1. [Usage basique](#usage-basique)
2. [Utiliser le hook useMobileNav](#utiliser-le-hook-usemobilenav)
3. [Personnalisation](#personnalisation)
4. [Intégration avec d'autres composants](#intégration-avec-dautres-composants)
5. [Cas d'usage avancés](#cas-dusage-avancés)

---

## Usage basique

### Déjà intégré!

La bottom nav est déjà active dans votre application. Aucune configuration nécessaire.

```jsx
// src/app/AppShell.jsx - Déjà fait!
import BottomNav from '../components/layout/BottomNav.jsx';

export default function AppShell() {
  return (
    <div className="flex min-h-screen">
      {/* ... sidebar, content ... */}

      {/* Bottom Nav - Automatiquement visible sur mobile */}
      <BottomNav />
    </div>
  );
}
```

---

## Utiliser le hook useMobileNav

### Exemple 1: Afficher l'item actif

```jsx
import { useMobileNav } from '@/hooks';

function PageHeader() {
  const { activeItem } = useMobileNav();

  return (
    <div className="flex items-center gap-2">
      {activeItem?.section?.icon && (
        <activeItem.section.icon className="w-5 h-5" />
      )}
      <h1>{activeItem?.label || 'Page'}</h1>
    </div>
  );
}
```

### Exemple 2: Navigation programmatique

```jsx
import { useMobileNav } from '@/hooks';
import { useNavigate } from 'react-router-dom';

function QuickActions() {
  const { primaryItems } = useMobileNav();
  const navigate = useNavigate();

  const goToOperations = () => {
    const opsItem = primaryItems.find(item => item.id === 'operations');
    if (opsItem) {
      navigate(opsItem.path);
    }
  };

  return (
    <button onClick={goToOperations}>
      Aller aux Opérations
    </button>
  );
}
```

### Exemple 3: Indicateur personnalisé

```jsx
import { useMobileNav } from '@/hooks';

function CustomBreadcrumb() {
  const { activeItem, primaryItems, secondaryItems } = useMobileNav();

  const allItems = [...primaryItems, ...secondaryItems];

  return (
    <nav className="flex items-center gap-2 text-sm">
      <span className="text-slate-500">Vous êtes ici:</span>
      {allItems.map((item, index) => (
        <span
          key={item.id}
          className={item.id === activeItem?.id ? 'text-white font-medium' : 'text-slate-600'}
        >
          {item.label}
          {index < allItems.length - 1 && ' / '}
        </span>
      ))}
    </nav>
  );
}
```

### Exemple 4: Contrôler le menu Plus

```jsx
import { useMobileNav } from '@/hooks';

function FloatingActionButton() {
  const { isMoreMenuOpen, toggleMoreMenu } = useMobileNav();

  return (
    <button
      onClick={toggleMoreMenu}
      className={`
        fixed bottom-20 right-4 w-14 h-14 rounded-full
        ${isMoreMenuOpen ? 'bg-blue-500' : 'bg-slate-700'}
      `}
    >
      {isMoreMenuOpen ? '✕' : '+'}
    </button>
  );
}
```

### Exemple 5: Badge de notifications

```jsx
import { useMobileNav } from '@/hooks';

function NavWithNotifications() {
  const { primaryItems, isItemActive } = useMobileNav();

  const notifications = {
    operations: 3,
    finances: 1,
  };

  return (
    <div className="flex gap-2">
      {primaryItems.map((item) => {
        const count = notifications[item.id];
        const active = isItemActive(item.path);

        return (
          <div key={item.id} className="relative">
            <NavLink to={item.path}>
              {item.label}
            </NavLink>
            {count > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {count}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
```

---

## Personnalisation

### Exemple 6: Ajouter un item principal

```jsx
// src/hooks/useMobileNav.js

// 1. Ajouter l'item dans primaryItems
const primaryItems = useMemo(() => {
  return [
    {
      id: 'cockpit',
      label: 'Cockpit',
      path: '/',
      section: navigationSections.find(s => s.id === 'cockpit'),
    },
    {
      id: 'operations',
      label: 'Ops',
      path: '/operations',
      section: navigationSections.find(s => s.id === 'operations'),
    },
    // ... autres items
    {
      id: 'analytics', // NOUVEAU
      label: 'Analytics',
      path: '/analytics',
      section: navigationSections.find(s => s.id === 'analytics'),
    },
  ];
}, []);
```

```jsx
// src/components/layout/MobileBottomNav.jsx

// 2. Ajouter l'icône SVG
const IconAnalytics = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor">
    <path d="M3 3v18h18" strokeWidth="2" />
    <path d="M18 17V9M13 17V5M8 17v-3" strokeWidth="2" />
  </svg>
);

// 3. Ajouter au mapping
const iconMap = {
  'cockpit': IconGauge,
  'operations': IconShoppingBag,
  'finances': IconWallet,
  'restaurant': IconUtensils,
  'analytics': IconAnalytics, // NOUVEAU
};
```

```jsx
// 4. Ajuster la grid (si besoin de plus de 5 items)
<div className="grid grid-cols-6 h-16"> {/* au lieu de cols-5 */}
```

### Exemple 7: Personnaliser les animations

```jsx
// src/components/layout/MobileBottomNav.jsx

// Animation tap personnalisée
const tapAnimation = {
  scale: 0.88, // Plus prononcé
  rotate: 5,   // Légère rotation
  transition: {
    type: 'spring',
    stiffness: 600, // Plus rapide
    damping: 20,    // Plus rebondi
  },
};

// Pulse effect personnalisé
<motion.div
  animate={{
    opacity: [0.7, 0], // Plus visible
    scale: [1, 1.4],   // Plus grand
  }}
  transition={{
    duration: 2,      // Plus lent
    repeat: Infinity,
  }}
/>
```

### Exemple 8: Thème personnalisé

```jsx
// Créer un fichier de configuration
// src/config/mobileNavTheme.js

export const mobileNavTheme = {
  // Hauteur de la barre
  height: 'h-20', // au lieu de h-16

  // Taille des icônes
  iconSize: 'w-6 h-6', // au lieu de w-5 h-5

  // Background
  background: 'bg-slate-950/98', // au lieu de slate-900/95

  // Bordure
  border: 'border-t-2 border-blue-500/20', // au lieu de border-white/10

  // Labels
  labelSize: 'text-sm', // au lieu de text-xs
};

// Utiliser dans MobileBottomNav.jsx
import { mobileNavTheme } from '@/config/mobileNavTheme.js';

<nav className={`lg:hidden fixed bottom-0 inset-x-0 z-50 ${mobileNavTheme.border} ${mobileNavTheme.background}`}>
  <div className={`grid grid-cols-5 ${mobileNavTheme.height}`}>
    {/* ... */}
  </div>
</nav>
```

---

## Intégration avec d'autres composants

### Exemple 9: Intégration avec Command Bar (⌘K)

```jsx
import { useMobileNav } from '@/hooks';
import { useCommandBar } from '@/contexts/CommandBarContext';

function MobileCommandBarTrigger() {
  const { activeItem } = useMobileNav();
  const { openCommandBar } = useCommandBar();

  return (
    <button
      onClick={openCommandBar}
      className="fixed top-4 right-4 lg:hidden"
    >
      <span className="text-sm">⌘K</span>
      {activeItem && (
        <span className="ml-2 text-xs text-slate-400">
          {activeItem.label}
        </span>
      )}
    </button>
  );
}
```

### Exemple 10: Swipe gestures pour ouvrir/fermer le menu

```jsx
import { useMobileNav } from '@/hooks';
import { useSwipeable } from 'react-swipeable'; // npm install react-swipeable

function SwipeableBottomNav() {
  const { isMoreMenuOpen, openMoreMenu, closeMoreMenu } = useMobileNav();

  const handlers = useSwipeable({
    onSwipedUp: () => {
      if (!isMoreMenuOpen) {
        openMoreMenu();
      }
    },
    onSwipedDown: () => {
      if (isMoreMenuOpen) {
        closeMoreMenu();
      }
    },
    preventDefaultTouchmoveEvent: true,
    trackMouse: true,
  });

  return (
    <div {...handlers}>
      <MobileBottomNav />
    </div>
  );
}
```

### Exemple 11: Haptic feedback (iOS)

```jsx
import { useMobileNav } from '@/hooks';

function HapticBottomNav() {
  const { toggleMoreMenu } = useMobileNav();

  const handleToggle = () => {
    // Haptic feedback sur iOS
    if (window.navigator.vibrate) {
      window.navigator.vibrate(10); // Courte vibration
    }

    // Alternative pour iOS (nécessite un user gesture)
    if (typeof window.AudioContext !== 'undefined') {
      const context = new AudioContext();
      const oscillator = context.createOscillator();
      oscillator.frequency.value = 50;
      oscillator.connect(context.destination);
      oscillator.start(0);
      oscillator.stop(context.currentTime + 0.01);
    }

    toggleMoreMenu();
  };

  return (
    <button onClick={handleToggle}>
      Plus
    </button>
  );
}
```

---

## Cas d'usage avancés

### Exemple 12: Navigation avec confirmation

```jsx
import { useMobileNav } from '@/hooks';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

function ConfirmableNavigation() {
  const { primaryItems } = useMobileNav();
  const navigate = useNavigate();
  const [pendingNav, setPendingNav] = useState(null);

  const hasUnsavedChanges = true; // Votre logique

  const handleNavigate = (path) => {
    if (hasUnsavedChanges) {
      setPendingNav(path);
    } else {
      navigate(path);
    }
  };

  const confirmNavigation = () => {
    if (pendingNav) {
      navigate(pendingNav);
      setPendingNav(null);
    }
  };

  return (
    <>
      {/* Navigation buttons */}
      {primaryItems.map((item) => (
        <button
          key={item.id}
          onClick={() => handleNavigate(item.path)}
        >
          {item.label}
        </button>
      ))}

      {/* Confirmation modal */}
      {pendingNav && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg">
            <p>Vous avez des modifications non sauvegardées</p>
            <button onClick={confirmNavigation}>Continuer</button>
            <button onClick={() => setPendingNav(null)}>Annuler</button>
          </div>
        </div>
      )}
    </>
  );
}
```

### Exemple 13: Analytics tracking

```jsx
import { useMobileNav } from '@/hooks';
import { useEffect } from 'react';

function AnalyticsTrackedNav() {
  const { activeItem } = useMobileNav();

  useEffect(() => {
    if (activeItem) {
      // Google Analytics
      if (window.gtag) {
        window.gtag('event', 'mobile_nav_change', {
          section: activeItem.id,
          label: activeItem.label,
          path: activeItem.path,
        });
      }

      // Custom analytics
      fetch('/api/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event: 'navigation',
          section: activeItem.id,
          timestamp: new Date().toISOString(),
        }),
      });
    }
  }, [activeItem]);

  return <MobileBottomNav />;
}
```

### Exemple 14: Badge dynamique avec données en temps réel

```jsx
import { useMobileNav } from '@/hooks';
import { useQuery } from '@tanstack/react-query';

function RealtimeBadges() {
  const { primaryItems } = useMobileNav();

  // Fetch notifications en temps réel
  const { data: notifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => fetch('/api/notifications').then(r => r.json()),
    refetchInterval: 10000, // Toutes les 10s
  });

  return (
    <div className="relative">
      {primaryItems.map((item) => {
        const count = notifications?.[item.id] || 0;

        return (
          <div key={item.id} className="relative">
            <NavLink to={item.path}>
              {item.label}
            </NavLink>

            {count > 0 && (
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center"
              >
                {count > 99 ? '99+' : count}
              </motion.span>
            )}
          </div>
        );
      })}
    </div>
  );
}
```

### Exemple 15: Mode compact pour petits écrans

```jsx
import { useMobileNav } from '@/hooks';
import { useMediaQuery } from '@/hooks';

function ResponsiveBottomNav() {
  const { primaryItems } = useMobileNav();
  const isSmallScreen = useMediaQuery('(max-width: 380px)'); // iPhone SE

  return (
    <nav className={`fixed bottom-0 inset-x-0 z-50 ${isSmallScreen ? 'h-14' : 'h-16'}`}>
      <div className="grid grid-cols-5 h-full">
        {primaryItems.map((item) => {
          const Icon = iconMap[item.id];

          return (
            <NavLink key={item.id} to={item.path}>
              <div className={`flex flex-col items-center justify-center gap-${isSmallScreen ? '0' : '1'}`}>
                <div className={`${isSmallScreen ? 'h-7 w-7' : 'h-9 w-9'}`}>
                  <Icon className={isSmallScreen ? 'h-4 w-4' : 'h-5 w-5'} />
                </div>
                {!isSmallScreen && (
                  <span className="text-xs">{item.label}</span>
                )}
              </div>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}
```

### Exemple 16: Prévenir la navigation (formulaire non sauvegardé)

```jsx
import { useMobileNav } from '@/hooks';
import { useBlocker } from 'react-router-dom';

function FormWithUnsavedWarning() {
  const [isDirty, setIsDirty] = useState(false);

  // Bloquer la navigation si formulaire modifié
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      isDirty && currentLocation.pathname !== nextLocation.pathname
  );

  return (
    <>
      <form onChange={() => setIsDirty(true)}>
        {/* Champs du formulaire */}
      </form>

      {blocker.state === 'blocked' && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100]">
          <div className="bg-white p-6 rounded-lg max-w-sm">
            <h3 className="font-bold mb-4">Modifications non sauvegardées</h3>
            <p className="text-sm text-slate-600 mb-6">
              Voulez-vous vraiment quitter cette page ?
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => blocker.proceed()}
                className="flex-1 bg-red-500 text-white px-4 py-2 rounded"
              >
                Quitter
              </button>
              <button
                onClick={() => blocker.reset()}
                className="flex-1 bg-slate-200 px-4 py-2 rounded"
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
```

---

## Tips & Tricks

### Performance

```jsx
// Optimiser les re-renders avec memo
import { memo } from 'react';

const MobileNavItem = memo(({ item, isActive }) => {
  return (
    <NavLink to={item.path}>
      {/* Contenu */}
    </NavLink>
  );
});
```

### Debugging

```jsx
// Hook de debug pour la navigation mobile
function useDebugMobileNav() {
  const nav = useMobileNav();

  useEffect(() => {
    console.log('Mobile Nav State:', {
      activeItem: nav.activeItem?.label,
      isMoreMenuOpen: nav.isMoreMenuOpen,
      isSecondaryActive: nav.isSecondaryActive,
    });
  }, [nav.activeItem, nav.isMoreMenuOpen, nav.isSecondaryActive]);

  return nav;
}
```

### Testing

```jsx
// Test avec React Testing Library
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import MobileBottomNav from './MobileBottomNav';

test('opens more menu on Plus button click', () => {
  render(
    <BrowserRouter>
      <MobileBottomNav />
    </BrowserRouter>
  );

  const plusButton = screen.getByLabelText("Plus d'options");
  fireEvent.click(plusButton);

  expect(screen.getByText('Intelligence')).toBeInTheDocument();
});
```

---

**Pour plus d'informations**, voir:
- [MOBILE_NAVIGATION.md](./MOBILE_NAVIGATION.md) - Documentation complète
- [MOBILE_NAV_VISUAL_GUIDE.md](./MOBILE_NAV_VISUAL_GUIDE.md) - Guide visuel
- [CHANGELOG_MOBILE_NAV.md](./CHANGELOG_MOBILE_NAV.md) - Changelog détaillé
