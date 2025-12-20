# Swipe Actions Reference - Finance Transactions Mobile

## Visual Guide

```
┌─────────────────────────────────────────────┐
│  TRANSACTION CARD (CENTER POSITION)         │
│  ┌─────────────────────────────────────┐   │
│  │ 15/12/2024         -125.50 €        │   │
│  │ Carrefour Market                    │   │
│  │ 🏷 Alimentation    🤖 95%           │   │
│  │ Compte Courant     [Rapproché]      │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘

⬅️ SWIPE LEFT (reveals left action on right side)
┌─────────────────────────────────────────────┐
│  TRANSACTION CARD                  ┌────────┤
│  ┌─────────────────────────┐      │ Caté-  │
│  │ 15/12/2024   -125.50 €  │      │ gori-  │
│  │ Carrefour Market        │      │ ser    │
│  │ 🏷 Alimentation 🤖 95%  │      │ 🏷     │
│  │ Compte Courant [Rapp.]  │      │        │
│  └─────────────────────────┘      └────────┤
│                              [BLUE BUTTON]  │
└─────────────────────────────────────────────┘

➡️ SWIPE RIGHT (reveals right action on left side)
┌─────────────────────────────────────────────┐
│ ┌────────┐  TRANSACTION CARD                │
│ │ Dét-   │      ┌─────────────────────────┐ │
│ │ ails   │      │ 15/12/2024   -125.50 €  │ │
│ │ ℹ️      │      │ Carrefour Market        │ │
│ │        │      │ 🏷 Alimentation 🤖 95%  │ │
│ │        │      │ Compte Courant [Rapp.]  │ │
│ └────────┤      └─────────────────────────┘ │
│  [BLUE BUTTON]                              │
└─────────────────────────────────────────────┘
```

## Action Details

### Left Swipe → Catégoriser
- **Icon**: Tag (🏷)
- **Color**: Blue (primary)
- **Action**: Opens category selection modal
- **Use Case**: Quick categorization of transactions
- **Modal Shows**:
  - Transaction details (label, amount)
  - Category dropdown
  - Auto-saves on selection

### Right Swipe → Détails
- **Icon**: Info (ℹ️)
- **Color**: Blue (primary)
- **Action**: Opens transaction detail modal
- **Use Case**: View full transaction information
- **Modal Shows**:
  - Complete transaction data
  - All fields (date, amount, category, account, status)
  - AI confidence badge if applicable
  - Quick action buttons

## Gesture Thresholds

```javascript
SWIPE_REVEAL_THRESHOLD = 80px   // Reveals action button
SWIPE_CONFIRM_THRESHOLD = 150px // Auto-executes action
SWIPE_VELOCITY_THRESHOLD = 0.5  // For quick swipes
```

## Visual Feedback

### Background Colors (Dynamic)
- **Left Swipe**: Blue gradient (0-25% opacity)
- **Right Swipe**: Blue gradient (0-25% opacity)
- **Strong Swipe**: Intensified color (25% opacity)

### Animation
- **Spring Physics**: Natural, bouncy feel
- **Auto-close**: Other rows close when one is swiped
- **Haptic**: Vibration feedback (if device supports)

## Touch Targets

All interactive elements meet WCAG 2.1 Level AAA:
- ✅ Buttons: 44px minimum height
- ✅ Swipe cards: Full height (80px+)
- ✅ Modal controls: 44px minimum
- ✅ Category selector: 44px minimum

## Pull-to-Refresh

```
    ↓ PULL DOWN ↓
┌─────────────────────────────────┐
│    ⟳ Tirez pour rafraîchir      │ ← Indicator appears
│    ▓▓▓▓▓▓▓░░░░░░░░              │ ← Progress bar
├─────────────────────────────────┤
│  Transaction cards below...     │
└─────────────────────────────────┘

    ↓ RELEASE ↓
┌─────────────────────────────────┐
│    ⟳ Chargement...              │ ← Loading state
│    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓             │ ← Full bar
├─────────────────────────────────┤
│  [Content refreshing]           │
└─────────────────────────────────┘

    COMPLETE
┌─────────────────────────────────┐
│    ✓ Rafraîchi !                │ ← Success state
│    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓             │ ← Green bar
├─────────────────────────────────┤
│  [Updated content]              │
└─────────────────────────────────┘
```

## States

### Pull States
1. **IDLE**: No interaction
2. **PULLING**: User dragging down
3. **READY**: Threshold reached, ready to refresh
4. **REFRESHING**: Loading data
5. **DONE**: Success feedback

### Swipe States
1. **IDLE**: No swipe
2. **DRAGGING**: User swiping
3. **REVEALED**: Action button visible
4. **CONFIRMED**: Action executing

## Accessibility

- ✅ Touch targets: 44x44px minimum
- ✅ Visual feedback: Color and animation
- ✅ Haptic feedback: Vibration when available
- ✅ Clear labels: "Catégoriser", "Détails"
- ✅ Fallback: Buttons also in detail modal
- ✅ Keyboard: Modal accessible via keyboard (desktop)

## Performance

- Optimized re-renders with `useCallback`
- Memoized card component
- Efficient state management
- Spring animations (GPU accelerated)
- No layout thrashing
- Smooth 60fps gestures

## Browser Support

- ✅ Chrome (Android/Desktop)
- ✅ Safari (iOS/macOS)
- ✅ Firefox (Android/Desktop)
- ✅ Edge (Desktop)
- ⚠️ Touch events required for gestures
- ⚠️ Framer Motion for animations

## Code Example

```jsx
// Left swipe reveals categorize
leftActions={[
  {
    label: 'Catégoriser',
    icon: Tag,
    variant: 'primary',
    onAction: () => handleOpenCategoryModal(transaction),
  },
]}

// Right swipe reveals details
rightActions={[
  {
    label: 'Détails',
    icon: Info,
    variant: 'primary',
    onAction: () => handleOpenDetailModal(transaction),
  },
]}
```

## Testing Checklist

- [ ] Left swipe reveals blue "Catégoriser" button
- [ ] Right swipe reveals blue "Détails" button
- [ ] Quick swipe auto-executes action
- [ ] Other rows close when swiping new row
- [ ] Haptic feedback works (on supported devices)
- [ ] Pull-to-refresh triggers data reload
- [ ] Category modal saves correctly
- [ ] Detail modal shows all transaction info
- [ ] Touch targets are all 44px+
- [ ] Animations are smooth (60fps)
- [ ] Works on iOS Safari
- [ ] Works on Android Chrome
