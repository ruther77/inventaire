# Mobile UX Architecture

Visual guide to understand how the components work together.

## Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Your App / Page                          │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │           PullToRefresh                            │   │
│  │  (Wraps entire scrollable content)                 │   │
│  │                                                     │   │
│  │  ┌───────────────────────────────────────────┐    │   │
│  │  │    SwipeableRowProvider                   │    │   │
│  │  │    (Context for auto-close behavior)      │    │   │
│  │  │                                            │    │   │
│  │  │  ┌──────────────────────────────────┐    │    │   │
│  │  │  │   SwipeableRow (Item 1)          │    │    │   │
│  │  │  │   - id: "item-1"                 │    │    │   │
│  │  │  │   - leftActions: [Delete]        │    │    │   │
│  │  │  │   - rightActions: [Edit]         │    │    │   │
│  │  │  │                                   │    │    │   │
│  │  │  │   ┌─────────────────────────┐   │    │    │   │
│  │  │  │   │   Your Content          │   │    │    │   │
│  │  │  │   │   (Card, Row, etc.)     │   │    │    │   │
│  │  │  │   └─────────────────────────┘   │    │    │   │
│  │  │  └──────────────────────────────────┘    │    │   │
│  │  │                                            │    │   │
│  │  │  ┌──────────────────────────────────┐    │    │   │
│  │  │  │   SwipeableRow (Item 2)          │    │    │   │
│  │  │  │   - id: "item-2"                 │    │    │   │
│  │  │  │   - leftActions: [Delete]        │    │    │   │
│  │  │  │   - rightActions: [Edit]         │    │    │   │
│  │  │  │                                   │    │    │   │
│  │  │  │   ┌─────────────────────────┐   │    │    │   │
│  │  │  │   │   Your Content          │   │    │    │   │
│  │  │  │   └─────────────────────────┘   │    │    │   │
│  │  │  └──────────────────────────────────┘    │    │   │
│  │  │                                            │    │   │
│  │  └───────────────────────────────────────────┘    │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Swipe Gesture Flow

```
User Touch
    │
    ├─ onTouchStart
    │      │
    │      └─> Store touch start position
    │
    ├─ onTouchMove
    │      │
    │      ├─> Calculate deltaX (horizontal movement)
    │      ├─> Apply resistance factor
    │      └─> Update x position (animate)
    │
    └─ onTouchEnd
           │
           ├─> Calculate final deltaX and velocity
           │
           ├─ deltaX > SWIPE_CONFIRM_THRESHOLD ?
           │      │
           │      └─ YES → Execute first action immediately
           │      │
           │      └─ NO  → deltaX > SWIPE_REVEAL_THRESHOLD ?
           │                  │
           │                  └─ YES → Reveal actions
           │                  │       └─> Set activeRowId in context
           │                  │            └─> Other rows auto-close
           │                  │
           │                  └─ NO  → Reset to idle
           │
           └─> User taps action button
                   │
                   └─> Execute action
                        └─> Reset position
```

### Pull-to-Refresh Flow

```
User Pull Down
    │
    ├─ Check scroll position = 0 ?
    │      │
    │      └─ NO  → Ignore gesture (let scroll work)
    │      │
    │      └─ YES → Continue
    │
    ├─ onTouchStart
    │      │
    │      └─> Store start Y position
    │
    ├─ onTouchMove
    │      │
    │      ├─> Calculate deltaY (downward pull)
    │      ├─> Apply resistance (natural feel)
    │      ├─> pullDistance = min(deltaY * resistance, maxPull)
    │      ├─> pullProgress = pullDistance / threshold (0-1)
    │      │
    │      └─> pullDistance >= threshold ?
    │             │
    │             ├─ YES → State: READY
    │             │        └─> Haptic feedback
    │             │
    │             └─ NO  → State: PULLING
    │
    └─ onTouchEnd
           │
           └─> State === READY ?
                  │
                  ├─ YES → State: REFRESHING
                  │        └─> Call onRefresh()
                  │             └─> await completion
                  │                  └─> State: DONE
                  │                       └─> setTimeout → State: IDLE
                  │
                  └─ NO  → State: IDLE
```

## State Management

### SwipeableRow States

```javascript
// Internal Component State
{
  offset: 0,              // Current X offset in pixels
  isRevealed: false,      // Are actions visible?
  revealedSide: null,     // 'left' | 'right' | null
  isDragging: false,      // Is user currently dragging?
  showContextMenu: false  // Is long press menu visible?
}

// Context State (shared across all rows)
{
  activeRowId: null       // ID of currently open row
}
```

### PullToRefresh States

```javascript
// Hook State
{
  pullState: 'idle',      // 'idle' | 'pulling' | 'ready' | 'refreshing' | 'done'
  pullProgress: 0,        // 0 to 1 (percentage)
  pullDistance: 0,        // Pixels pulled
}

// State Transitions
idle → pulling → ready → refreshing → done → idle
  └─────────────────┘                └──────┘
   (can go back to idle anytime)    (auto after 500ms)
```

## Hook Dependencies

```
usePullToRefresh.js
    │
    ├─ useState (React)
    ├─ useRef (React)
    ├─ useCallback (React)
    └─ useEffect (React)

SwipeableRow.jsx
    │
    ├─ framer-motion
    │   ├─ motion
    │   ├─ AnimatePresence
    │   ├─ useMotionValue
    │   ├─ useTransform
    │   └─ useSpring
    │
    ├─ useGestures (custom hook)
    │   └─ Provides: onSwipeLeft, onSwipeRight, onLongPress
    │
    └─ SwipeableRowContext (React Context)
        └─ Manages: activeRowId state
```

## Animation Strategy

### SwipeableRow Animations

```javascript
// Position Animation (Framer Motion)
<motion.div
  drag="x"
  dragConstraints={{ left: -150, right: 150 }}
  dragElastic={0.2}
  style={{
    x: isDragging ? x : springX,  // Raw during drag, spring after
    backgroundColor: backgroundColorTransform
  }}
/>

// Spring Configuration
useSpring(x, {
  stiffness: 300,   // How "tight" the spring is
  damping: 30,      // How much oscillation to reduce
  mass: 0.8         // Weight of the object
})

// Color Transform (Framer Motion)
useTransform(x, [-200, -80, 0, 80, 200], [
  'rgba(239, 68, 68, 0.25)',  // Strong red (far left)
  'rgba(239, 68, 68, 0.1)',   // Light red
  'rgba(0, 0, 0, 0)',         // Transparent (center)
  'rgba(59, 130, 246, 0.1)',  // Light blue
  'rgba(59, 130, 246, 0.25)'  // Strong blue (far right)
])
```

### PullToRefresh Animations

```javascript
// Indicator Height Animation
<motion.div
  animate={{
    height: pullDistance,      // Grows as you pull
    opacity: pullDistance > 0 ? 1 : 0
  }}
  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
/>

// Icon Rotation Animation
<motion.div
  animate={{
    rotate: state === 'pulling' ? progress * 180 : 0,
    scale: state === 'refreshing' ? 1 : progress * 1.2
  }}
/>
```

## Event Handling

### Touch Events (Mobile)

```javascript
// Touch Event Flow
onTouchStart   → Initialize gesture tracking
    ↓
onTouchMove    → Update position in real-time
    ↓           (fires ~60 times per second)
onTouchEnd     → Finalize action
    ↓
onTouchCancel  → Reset if interrupted
```

### Mouse Events (Desktop Fallback)

```javascript
// Framer Motion handles mouse → touch conversion
drag="x"  → Works with both touch and mouse
    ↓
onDragStart   → Mouse down
onDrag        → Mouse move
onDragEnd     → Mouse up
```

## Context Management

### SwipeableRowProvider Context

```javascript
// Context Definition
const SwipeableRowContext = createContext({
  activeRowId: null,
  setActiveRowId: () => {}
});

// Provider Implementation
<SwipeableRowProvider>
  {/* All child SwipeableRows share this state */}
  <SwipeableRow id="row-1" />  ← Can set activeRowId
  <SwipeableRow id="row-2" />  ← Will auto-close if row-1 opens
  <SwipeableRow id="row-3" />  ← Will auto-close if row-1 opens
</SwipeableRowProvider>

// Auto-Close Logic
useEffect(() => {
  if (context.activeRowId !== null && context.activeRowId !== id && isRevealed) {
    resetPosition(); // Close this row
  }
}, [context.activeRowId, id, isRevealed]);
```

## Performance Optimization

### Rendering Optimization

```javascript
// 1. Memoize callbacks
const handleDelete = useCallback((item) => {
  deleteItem(item.id);
}, []);

// 2. Prevent unnecessary re-renders
const actions = useMemo(() => [
  { label: 'Delete', icon: Trash, onAction: handleDelete }
], [handleDelete]);

// 3. Use motion values (don't trigger re-render)
const x = useMotionValue(0);  // Changes don't cause re-render
const springX = useSpring(x);  // Smooth animation without re-renders
```

### Animation Performance

```javascript
// Hardware-accelerated properties only
{
  transform: 'translateX()',  // ✅ GPU accelerated
  opacity: 0.5,              // ✅ GPU accelerated
  backgroundColor: '#fff',   // ⚠️  Can be slow on old devices
  width: '100px'             // ❌ Causes layout recalc
}

// Use Framer Motion transforms
style={{ x: springX }}  // ✅ Optimized by Framer Motion
```

## Integration Patterns

### Pattern 1: Minimal Integration

```jsx
// Just add swipe to existing list
<SwipeableRowProvider>
  {items.map(item => (
    <SwipeableRow key={item.id} id={item.id} {...actions}>
      <ExistingCard item={item} />
    </SwipeableRow>
  ))}
</SwipeableRowProvider>
```

### Pattern 2: Full Mobile Experience

```jsx
// Add both swipe and pull-to-refresh
<PullToRefresh onRefresh={refetch}>
  <SwipeableRowProvider>
    {items.map(item => (
      <SwipeableRow key={item.id} id={item.id} {...actions}>
        <Card item={item} />
      </SwipeableRow>
    ))}
  </SwipeableRowProvider>
</PullToRefresh>
```

### Pattern 3: Custom Implementation

```jsx
// Use hooks directly for custom UI
const { pullState, pullProgress, handlers, containerRef } = usePullToRefresh({
  onRefresh: async () => await fetchData()
});

return (
  <div ref={containerRef} {...handlers}>
    <CustomIndicator state={pullState} progress={pullProgress} />
    <CustomContent />
  </div>
);
```

## Testing Strategy

### Unit Testing Approach

```javascript
// Test SwipeableRow
describe('SwipeableRow', () => {
  test('reveals actions on swipe', () => {
    // Simulate touch events
    // Assert actions become visible
  });

  test('auto-closes when another row opens', () => {
    // Open row 1
    // Open row 2
    // Assert row 1 is closed
  });
});

// Test usePullToRefresh
describe('usePullToRefresh', () => {
  test('triggers refresh on pull', async () => {
    // Simulate pull gesture
    // Assert onRefresh called
  });

  test('shows progress during pull', () => {
    // Simulate partial pull
    // Assert progress is correct
  });
});
```

### Manual Testing Flow

```
1. Desktop (Chrome DevTools)
   └─> Toggle device mode
       └─> Test with mouse drag
           └─> Verify animations

2. Mobile (Real Device)
   └─> Test touch gestures
       └─> Verify haptic feedback
           └─> Check 60fps animations
               └─> Test on low-end device
```

## Common Issues & Solutions

### Issue: Swipe conflicts with scroll

**Solution:** Use proper touch-action CSS

```css
/* On swipeable container */
.swipeable-row {
  touch-action: pan-y; /* Allow vertical scroll, horizontal for swipe */
}
```

### Issue: Pull-to-refresh on iOS Safari

**Solution:** Disable default pull-to-refresh

```css
/* Prevent iOS Safari default pull-to-refresh */
body {
  overscroll-behavior-y: contain;
}
```

### Issue: Performance on large lists

**Solution:** Use virtualization

```jsx
import { useVirtualList } from '@/hooks';

const { virtualItems } = useVirtualList({
  items: largeArray,
  itemHeight: 80
});

// Only render visible items
{virtualItems.map(virtual => (
  <SwipeableRow key={virtual.key}>
    <ItemCard item={items[virtual.index]} />
  </SwipeableRow>
))}
```

## File Size Impact

```
Component Sizes (gzipped):
- SwipeableRow.jsx:      ~3.5 KB
- PullToRefresh.jsx:     ~2.8 KB
- usePullToRefresh.js:   ~2.1 KB
- MobileUXDemo.jsx:      ~6.5 KB (dev only)

Total Production Impact:  ~8.4 KB gzipped

Dependencies (already installed):
- framer-motion:         ~36 KB gzipped
- lucide-react:          ~1.2 KB per icon

Total Bundle Impact:     ~8.4 KB (new code only)
```

## Summary

### Component Relationships

```
PullToRefresh
    │
    └─> usePullToRefresh (hook)
        └─> Manages pull state

SwipeableRow
    │
    ├─> useGestures (hook)
    │   └─> Detects swipes
    │
    ├─> SwipeableRowContext
    │   └─> Auto-close coordination
    │
    └─> Framer Motion
        └─> Animations
```

### Key Concepts

1. **Context for Coordination:** SwipeableRowProvider ensures only one row is open
2. **Physics-Based Animation:** Spring animations for natural feel
3. **State Machine:** Clear state transitions for pull-to-refresh
4. **Touch Optimization:** Proper event handling for 60fps
5. **Progressive Enhancement:** Works on desktop with mouse fallback

### Next Steps

1. Review this architecture
2. Try the demo (`/frontend/src/examples/MobileUXDemo.jsx`)
3. Integrate into one page
4. Test on mobile device
5. Expand to more pages

---

**Architecture Reference**
- Version: 1.0
- Last Updated: December 17, 2025
- Status: Production Ready
