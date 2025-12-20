# Guide Visuel - Bottom Navigation Mobile

## Vue d'ensemble de l'interface

```
┌─────────────────────────────────────────┐
│  TopBar (logo, menu burger, etc.)       │
├─────────────────────────────────────────┤
│                                          │
│                                          │
│                                          │
│         CONTENU DE LA PAGE               │
│                                          │
│                                          │
│                                          │
│                                          │
│                                          │
├─────────────────────────────────────────┤
│  ┌─────┬─────┬─────┬─────┬─────┐        │
│  │ 🏠  │ 📦  │ 💰  │ 🍴  │ ⋯   │        │ <- Bottom Nav
│  │Home │ Ops │Finc │Resto│Plus │        │
│  └─────┴─────┴─────┴─────┴─────┘        │
└─────────────────────────────────────────┘
        Safe area (iPhone notch)
```

## Bottom Nav - État normal

```
┌───────────────────────────────────────────────────────────┐
│                                                             │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐      │
│  │  ━━━   │         │         │         │         │      │ <- Active indicator
│  │  ┌───┐ │  ┌───┐  │  ┌───┐  │  ┌───┐  │  ┌───┐  │      │
│  │  │ 🏠│ │  │ 📦│  │  │ 💰│  │  │ 🍴│  │  │ ⋯ │  │      │
│  │  └───┘ │  └───┘  │  └───┘  │  └───┘  │  └───┘  │      │
│  │   ●    │         │         │         │         │      │ <- Active dot
│  │ Cockpit│  Ops    │ Finance │  Resto  │  Plus   │      │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘      │
│                                                             │
└───────────────────────────────────────────────────────────┘
```

### Détails d'un item actif

```
┌─────────┐
│  ━━━   │  <- Barre gradient (40% width, glow effect)
│  ┌───┐  │
│  │ 🏠│●│  <- Dot lumineux (top-right, 2px)
│  └───┘  │
│         │  <- Pulse animation sur le fond
│ Cockpit │  <- Label en blanc
└─────────┘

Background: gradient from-blue-500 to-cyan-400
Shadow: 0 0 10px color-accent
```

### Détails d'un item inactif

```
┌─────────┐
│         │  <- Pas de barre
│  ┌───┐  │
│  │ 📦│  │  <- Pas de dot
│  └───┘  │
│         │  <- Background: white/5
│   Ops   │  <- Label en slate-500
└─────────┘
```

## Menu "Plus" ouvert

```
┌───────────────────────────────────────────────────────────┐
│ █████████████████████████████████████████████████████████ │ <- Backdrop
│ ███                                                    ███ │    (black/60 + blur)
│ ███  ┌──────────────────────────────────────────┐    ███ │
│ ███  │  Plus d'options                     ✕   │    ███ │ <- Header
│ ███  ├──────────────────────────────────────────┤    ███ │
│ ███  │  ━━━                                     │    ███ │
│ ███  │  ┌────┐  Intelligence                   │    ███ │
│ ███  │  │ 🧠 │  IA & Analytics              ●  │    ███ │
│ ███  │  └────┘                                  │    ███ │
│ ███  │                                          │    ███ │
│ ███  │  ┌────┐  Paramètres                     │    ███ │
│ ███  │  │ ⚙️  │  Configuration                  │    ███ │
│ ███  │  └────┘                                  │    ███ │
│ ███  └──────────────────────────────────────────┘    ███ │
│ ███                                                    ███ │
│ ███████████████████████████████████████████████████████████ │
│                                                             │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐      │
│  │   🏠   │   📦   │   💰   │   🍴   │   ⋯    │      │
│  │ Cockpit│  Ops   │ Finance│  Resto │  Plus  │      │
│  └─────────┴─────────┴─────────┴─────────┴─────────┘      │
└───────────────────────────────────────────────────────────┘

Animation: slide-up spring (stiffness: 400, damping: 35)
Position: bottom-16 (au-dessus de la bottom nav)
```

## Animations

### Tap Animation

```
Normal:         Pressed:        Release:
┌───────┐      ┌──────┐        ┌───────┐
│  🏠  │      │  🏠 │        │  🏠  │
└───────┘      └──────┘        └───────┘
scale: 1       scale: 0.92     scale: 1

Duration: spring (stiffness: 500, damping: 30)
```

### Pulse Effect (item actif)

```
Frame 1:       Frame 2:        Frame 3:
┌─────┐       ┌──────┐        ┌───────┐
│ 🏠 │       │ ░🏠░│        │ ░░🏠░░│
└─────┘       └──────┘        └───────┘
opacity: 0.5   opacity: 0.3    opacity: 0

Duration: 1.5s infinite
```

### Menu Slide-up

```
Hidden:                      Visible:
                            ┌──────────┐
                            │ Plus     │
                            │ options  │
                            │          │
┌──────────────┐            ┌──────────┐
│ Bottom Nav   │            │ Bottom   │
└──────────────┘            └──────────┘

translateY: 100% -> 0
opacity: 0 -> 1
```

## États et interactions

### 1. Navigation normale
```
User taps "Ops"
  ↓
Scale animation (0.92)
  ↓
Router navigates to /operations
  ↓
Active indicator moves to "Ops"
  ↓
Gradient background + pulse + dot appear
```

### 2. Ouverture menu Plus
```
User taps "Plus"
  ↓
toggleMoreMenu()
  ↓
isMoreMenuOpen = true
  ↓
Backdrop fades in (0.2s)
  ↓
Menu slides up (spring)
  ↓
Items stagger in (0.05s delay each)
```

### 3. Navigation item secondaire
```
User taps "Intelligence" in menu
  ↓
Scale animation
  ↓
closeMoreMenu()
  ↓
Router navigates to /intelligence
  ↓
Menu slides down + backdrop fades out
  ↓
"Plus" button shows active indicator
```

### 4. Fermeture au tap outside
```
User taps backdrop
  ↓
closeMoreMenu()
  ↓
Menu slides down
  ↓
Backdrop fades out
  ↓
isMoreMenuOpen = false
```

## Responsive breakpoints

```
Mobile (< 768px):           Desktop (≥ 1024px):
┌──────────────┐            ┌─────────┬──────────────┐
│   Content    │            │ Sidebar │   Content    │
│              │            │         │              │
│              │            │  ┌───┐  │              │
│              │            │  │🏠 │  │              │
├──────────────┤            │  └───┘  │              │
│ Bottom Nav   │            │ Cockpit │              │
└──────────────┘            │         │              │
                            │  ┌───┐  │              │
Bottom Nav visible          │  │📦 │  │              │
Sidebar hidden              │  └───┘  │              │
                            │   Ops   │              │
                            └─────────┴──────────────┘

                            Bottom Nav hidden
                            Sidebar visible
```

## Safe area (iPhone)

```
iPhone sans notch:          iPhone avec notch:

┌──────────────┐            ┌──────────────┐
│              │            │              │
│   Content    │            │   Content    │
│              │            │              │
├──────────────┤            ├──────────────┤
│ Bottom Nav   │            │ Bottom Nav   │
└──────────────┘            │              │ <- Safe area padding
 ↑ 64px (h-16)              └──────────────┘
                             ↑ 64px + env(safe-area-inset-bottom)

CSS: padding-bottom: env(safe-area-inset-bottom)
```

## Z-index layers

```
Layer                Z-index   Composant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Menu Panel           70        MobileMoreMenu panel
Backdrop             60        MobileMoreMenu backdrop
Bottom Nav           50        MobileBottomNav
Content              auto      Page content
```

## Couleurs par section

```
Cockpit:        Operations:     Finances:
━━━━━━━━        ━━━━━━━━        ━━━━━━━━
from-blue-500   from-emerald    from-violet
to-cyan-400     to-teal-400     to-purple-400

Restaurant:     Intelligence:   Paramètres:
━━━━━━━━        ━━━━━━━━        ━━━━━━━━
from-orange     from-pink-500   from-slate-500
to-amber-400    to-rose-400     to-slate-400
```

## Icônes SVG inline

Toutes les icônes principales sont en SVG inline pour:
- Pas de requêtes HTTP supplémentaires
- Contrôle total du styling
- Performance optimale

```jsx
const IconGauge = ({ className }) => (
  <svg viewBox="0 0 24 24" stroke="currentColor">
    {/* SVG paths */}
  </svg>
);
```

Seule `MoreHorizontal` vient de Lucide React car elle est déjà optimisée.

## Touch targets

```
Minimum touch target: 40px × 40px
Actual icon size:     20px (h-5 w-5)
Container size:       36px (h-9 w-9)
Label:                text-xs

Total tap area ≈ 60px × 60px (confortable)
```

## Performance optimisations

1. **GPU-accelerated animations**
   - transform (scale, translateY)
   - opacity
   - filter (backdrop-blur)

2. **No layout shifts**
   - Fixed positioning
   - Absolute positioning for indicators

3. **Minimal re-renders**
   - useMemo for items lists
   - useCallback for handlers
   - React Router's NavLink optimization

4. **Bundle size**
   - SVG inline (pas de icon library complète)
   - Tree-shaking compatible
   - Lazy loading ready

## Debug checklist

✓ Bottom nav visible sur mobile (<1024px)
✓ Bottom nav masquée sur desktop (≥1024px)
✓ Indicateur actif sur le bon item
✓ Menu Plus s'ouvre/ferme correctement
✓ Backdrop ferme le menu au tap
✓ Navigation fonctionne pour tous les items
✓ Animations fluides (60fps)
✓ Safe area padding sur iPhone
✓ Pas de scroll bloqué
✓ Touch targets suffisamment grands
