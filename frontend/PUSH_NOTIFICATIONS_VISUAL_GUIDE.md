# Push Notifications - Visual Guide

This guide shows what the notification components look like in different states.

## NotificationPermissionButton - Compact Variant

The compact variant is perfect for toolbars and navigation bars.

### States

#### 1. Default State (Permission not requested)
```
┌─────────┐
│   🔔    │  ← Click to enable notifications
└─────────┘
```

#### 2. Granted but not subscribed
```
┌─────────┐
│   🔔    │  ← Click to subscribe
└─────────┘
```

#### 3. Subscribed (Active)
```
┌─────────┐
│   🔔    │  ← Click to unsubscribe (filled bell icon)
└─────────┘
```

#### 4. Permission Denied
```
┌─────────┐
│   🔕    │  ← Disabled, greyed out
└─────────┘
```

#### 5. Not Supported
```
┌─────────┐
│   🚫    │  ← Disabled, not supported
└─────────┘
```

### Visual Example

```jsx
<nav className="toolbar">
  <button>Dashboard</button>
  <button>Factures</button>
  <NotificationPermissionButton variant="compact" />
  <button>Profil</button>
</nav>
```

Renders as:
```
┌────────────────────────────────────────────────────┐
│  Dashboard  │  Factures  │  🔔  │  Profil          │
└────────────────────────────────────────────────────┘
```

---

## NotificationPermissionButton - Full Variant

The full variant is ideal for settings pages with detailed controls.

### State: Not Subscribed

```
┌─────────────────────────────────────────────────────────┐
│  🔔  Notifications Push                                 │
│       Statut: Non demandée                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────────────────────────┐  ┌─────────────────┐   │
│  │ Autoriser les notifications │  │ Voir les détails│   │
│  └────────────────────────────┘  └─────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### State: Permission Granted, Not Subscribed

```
┌─────────────────────────────────────────────────────────┐
│  🔔  Notifications Push                                 │
│       Statut: Autorisées (non souscrit)                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────────────────────────┐  ┌─────────────────┐   │
│  │ Activer les notifications  │  │ Voir les détails│   │
│  └────────────────────────────┘  └─────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### State: Subscribed (Active)

```
┌─────────────────────────────────────────────────────────┐
│  🔔  Notifications Push                                 │
│       Statut: Activées                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────┐  ┌────────┐  ┌──────┐ │
│  │ Désactiver les notifications│  │ Tester │  │Détails│ │
│  └─────────────────────────────┘  └────────┘  └──────┘ │
│                                                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ✓ Notifications activées avec succès               │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### State: With Details Expanded

```
┌─────────────────────────────────────────────────────────┐
│  🔔  Notifications Push                                 │
│       Statut: Activées                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────┐  ┌────────┐  ┌──────┐ │
│  │ Désactiver les notifications│  │ Tester │  │Détails│ │
│  └─────────────────────────────┘  └────────┘  └──────┘ │
│                                                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │                     DÉTAILS                        │ │
│  │                                                    │ │
│  │  Support:        Oui                               │ │
│  │  Permission:     granted                           │ │
│  │  Souscrit:       Oui                               │ │
│  │  Endpoint:       https://fcm.googleapis.com/...    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### State: Permission Denied

```
┌─────────────────────────────────────────────────────────┐
│  🔕  Notifications Push                                 │
│       Statut: Refusée                                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────────────────────────┐  ┌─────────────────┐   │
│  │  Permission refusée        │  │ Voir les détails│   │
│  │  (disabled)                │  └─────────────────┘   │
│  └────────────────────────────┘                        │
│                                                         │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ⚠️ Pour activer les notifications, vous devez      │ │
│  │    modifier les paramètres de votre navigateur.   │ │
│  │    Consultez l'aide de votre navigateur pour plus │ │
│  │    d'informations.                                 │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Push Notification Display

### Basic Notification

When a push notification is received, it appears as:

```
┌────────────────────────────────────────┐
│  🏪 Inventaire Épicerie                │
│                                        │
│  Nouvelle facture                      │
│  Facture #12345 de 150.00€             │
│                                        │
│  ┌──────────┐  ┌──────────┐           │
│  │  Ouvrir  │  │  Fermer  │           │
│  └──────────┘  └──────────┘           │
└────────────────────────────────────────┘
```

### Notification with Image

```
┌────────────────────────────────────────┐
│  🏪 Inventaire Épicerie                │
│                                        │
│  Nouveau plat ajouté                   │
│  Salade César disponible               │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │                                  │  │
│  │     [Image: Salade César]        │  │
│  │                                  │  │
│  └──────────────────────────────────┘  │
│                                        │
│  ┌──────────┐  ┌──────────┐           │
│  │  Ouvrir  │  │  Fermer  │           │
│  └──────────┘  └──────────┘           │
└────────────────────────────────────────┘
```

### Notification with Custom Actions

```
┌────────────────────────────────────────┐
│  🏪 Inventaire Épicerie                │
│                                        │
│  Confirmer la livraison                │
│  Livraison de 10 unités de tomates     │
│                                        │
│  ┌───────────┐  ┌──────────┐          │
│  │ Confirmer │  │  Rejeter │          │
│  └───────────┘  └──────────┘          │
└────────────────────────────────────────┘
```

---

## Demo Page

The PushNotificationsDemo component renders a complete demonstration page:

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Démonstration des Notifications Push                     │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │               STATUT ACTUEL                        │   │
│  │                                                    │   │
│  │  Support:        ✓ Supporté                       │   │
│  │  Permission:     ⚠ default                        │   │
│  │  Souscription:   ⚠ Inactif                        │   │
│  │  Chargement:     Prêt                             │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │               BOUTON COMPACT                       │   │
│  │  Idéal pour les barres d'outils et les menus      │   │
│  │                                                    │   │
│  │  🔔                                                │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │               BOUTON COMPLET                       │   │
│  │  Avec détails et options avancées                 │   │
│  │                                                    │   │
│  │  [Full NotificationPermissionButton here]         │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │        EXEMPLE D'UTILISATION DANS LE CODE          │   │
│  │                                                    │   │
│  │  import { NotificationPermissionButton }          │   │
│  │    from '@/components/pwa';                       │   │
│  │                                                    │   │
│  │  function MyComponent() {                         │   │
│  │    return (                                        │   │
│  │      <NotificationPermissionButton                │   │
│  │        variant="full"                             │   │
│  │      />                                            │   │
│  │    );                                              │   │
│  │  }                                                 │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Integration Examples

### Example 1: Settings Page

```
┌────────────────────────────────────────────────────────────┐
│  ⚙️  Paramètres                                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Compte                                                    │
│  ├─ Profil                                                 │
│  ├─ Sécurité                                               │
│  └─ Préférences                                            │
│                                                            │
│  Notifications                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Recevez des alertes pour les anomalies, nouvelles  │ │
│  │  factures, et rappels importants.                   │ │
│  │                                                      │ │
│  │  [NotificationPermissionButton Full Variant]        │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Apparence                                                 │
│  └─ Thème                                                  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Example 2: Dashboard Banner

```
┌────────────────────────────────────────────────────────────┐
│  📊 Tableau de bord                                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 🔔  Restez informé                      ┌──────────┐ │ │
│  │                                         │  Activer │ │ │
│  │     Activez les notifications pour     └──────────┘ │ │
│  │     recevoir des alertes en temps réel              │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Ventes    │  │  Achats     │  │   Marge     │       │
│  │   12,450€   │  │  8,320€     │  │   33.2%     │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Example 3: Navbar with Compact Button

```
┌────────────────────────────────────────────────────────────┐
│  🏪 Inventaire Épicerie                                    │
│                                                            │
│  Dashboard  │  Factures  │  Restaurant  │  🔔  │  Profile  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Browser Permission Prompts

### Chrome/Edge

```
┌───────────────────────────────────────┐
│  inventaire-epicerie.com              │
│  veut                                 │
│                                       │
│  Afficher des notifications           │
│                                       │
│  ┌──────────┐         ┌─────────┐    │
│  │ Bloquer  │         │ Autoriser│    │
│  └──────────┘         └─────────┘    │
└───────────────────────────────────────┘
```

### Firefox

```
┌───────────────────────────────────────┐
│  inventaire-epicerie.com souhaite     │
│  afficher des notifications.          │
│                                       │
│  ┌──────────┐  ┌─────────────┐       │
│  │ Refuser  │  │ Toujours    │       │
│  │          │  │ recevoir    │       │
│  └──────────┘  └─────────────┘       │
│                                       │
│  Ne plus me demander pour ce site     │
└───────────────────────────────────────┘
```

### Safari (iOS)

```
┌───────────────────────────────────────┐
│  "Inventaire Épicerie" souhaite       │
│  vous envoyer des notifications       │
│                                       │
│           ┌──────────┐                │
│           │ Autoriser │                │
│           └──────────┘                │
│                                       │
│           ┌──────────┐                │
│           │ Ne pas   │                │
│           │ autoriser│                │
│           └──────────┘                │
└───────────────────────────────────────┘
```

---

## Color Scheme

The components use CSS variables for easy theming:

### Light Mode (Default)
- Primary: `#2563eb` (Blue)
- Success: `#059669` (Green)
- Warning: `#d97706` (Orange)
- Error: `#dc2626` (Red)
- Background: `#ffffff` (White)
- Text: `#1a1a1a` (Dark)

### Dark Mode (If enabled)
- Primary: `#3b82f6` (Lighter Blue)
- Success: `#10b981` (Lighter Green)
- Warning: `#f59e0b` (Lighter Orange)
- Error: `#ef4444` (Lighter Red)
- Background: `#1a1a1a` (Dark)
- Text: `#f9fafb` (Light)

---

## Accessibility

All components include:
- ✓ ARIA labels
- ✓ Keyboard navigation
- ✓ Focus indicators
- ✓ Screen reader support
- ✓ High contrast mode support
- ✓ Reduced motion support

---

## Responsive Design

### Desktop (> 768px)
- Full button: 600px max width
- Compact button: 40px × 40px
- Large touch targets

### Tablet (768px - 1024px)
- Full button: 100% width
- Compact button: 40px × 40px
- Medium touch targets

### Mobile (< 768px)
- Full button: 100% width
- Compact button: 44px × 44px (iOS recommended)
- Large touch targets for fingers

---

## Animation

### Button Hover
```
Scale: 1.0 → 1.05
Duration: 0.2s
Easing: ease
```

### Notification Appear
```
Transform: translateX(400px) → translateX(0)
Opacity: 0 → 1
Duration: 0.3s
Easing: ease
```

### Success Message
```
Background: pulse animation
Duration: 2s
```

---

## Best Practices

1. **Placement**
   - Compact: Toolbar, navigation bar, header
   - Full: Settings page, preferences panel

2. **Timing**
   - Don't ask immediately on first visit
   - Wait for user engagement
   - Ask in context (after user performs related action)

3. **Messaging**
   - Explain the benefits
   - Be clear about what notifications they'll receive
   - Provide easy opt-out

4. **Testing**
   - Always test on actual devices
   - Test both granted and denied states
   - Test notification click behavior
   - Verify notifications appear correctly
