# Advanced Mobile UX Features

Production-ready mobile gesture components with swipe-to-action and pull-to-refresh functionality.

## Features Implemented

### 1. SwipeableRow - Swipe-to-Action Component

Advanced swipeable row component with gesture support and smooth animations.

**Key Features:**
- ✅ Swipe left/right to reveal actions (edit, delete, archive, etc.)
- ✅ Spring animations with Framer Motion for natural feel
- ✅ Touch-friendly with configurable thresholds
- ✅ Auto-close when another row is swiped
- ✅ Haptic feedback support
- ✅ Long press for context menu
- ✅ Visual feedback during swipe
- ✅ Quick swipe detection for instant actions
- ✅ Configurable swipe thresholds and velocity
- ✅ Multiple actions per direction

**Files:**
- `/frontend/src/components/ui/SwipeableRow.jsx`
- `/frontend/src/hooks/useGestures.js` (existing, enhanced)

### 2. PullToRefresh - Pull-to-Refresh Component

Native-feeling pull-to-refresh with gesture detection and animated indicators.

**Key Features:**
- ✅ Pull down gesture detection
- ✅ Animated loading spinner with progress
- ✅ Callback for async refresh action
- ✅ Works with any scrollable content
- ✅ Proper iOS/Android feel with natural physics
- ✅ Customizable indicators
- ✅ Haptic feedback
- ✅ Progress tracking (0-1)
- ✅ State management (idle, pulling, ready, refreshing, done)
- ✅ Simple variant for better performance

**Files:**
- `/frontend/src/components/ui/PullToRefresh.jsx`
- `/frontend/src/hooks/usePullToRefresh.js`

### 3. Enhanced Gesture System

The existing `useGestures` hook has been integrated and exported for reuse.

**Features:**
- Swipe detection (left, right, up, down)
- Long press detection
- Velocity-based gesture recognition
- Configurable thresholds

## Usage Examples

### SwipeableRow - Basic Usage

```jsx
import { SwipeableRow, SwipeableRowProvider } from '@/components/ui/SwipeableRow';
import { Trash2, Edit } from 'lucide-react';

function InvoiceList() {
  const handleDelete = (invoice) => {
    console.log('Delete:', invoice);
  };

  const handleEdit = (invoice) => {
    console.log('Edit:', invoice);
  };

  return (
    <SwipeableRowProvider>
      <div className="space-y-3">
        {invoices.map((invoice) => (
          <SwipeableRow
            key={invoice.id}
            id={`invoice-${invoice.id}`}
            leftActions={[
              {
                label: 'Delete',
                icon: Trash2,
                variant: 'danger',
                onAction: () => handleDelete(invoice),
              },
            ]}
            rightActions={[
              {
                label: 'Edit',
                icon: Edit,
                variant: 'primary',
                onAction: () => handleEdit(invoice),
              },
            ]}
          >
            <div className="bg-white rounded-lg border p-4">
              <h3>{invoice.title}</h3>
              <p>{invoice.amount}</p>
            </div>
          </SwipeableRow>
        ))}
      </div>
    </SwipeableRowProvider>
  );
}
```

### SwipeableRow - With Long Press

```jsx
<SwipeableRow
  id="row-1"
  leftActions={[/* ... */]}
  rightActions={[/* ... */]}
  longPressActions={[
    {
      label: 'Archive',
      icon: Archive,
      onAction: () => handleArchive(item),
    },
    {
      label: 'Share',
      icon: Share,
      onAction: () => handleShare(item),
    },
  ]}
>
  <div>Row content</div>
</SwipeableRow>
```

### PullToRefresh - Basic Usage

```jsx
import PullToRefresh from '@/components/ui/PullToRefresh';

function DataList() {
  const [data, setData] = useState([]);

  const handleRefresh = async () => {
    const newData = await fetchData();
    setData(newData);
  };

  return (
    <PullToRefresh
      onRefresh={handleRefresh}
      className="h-screen"
    >
      <div className="p-4 space-y-3">
        {data.map(item => (
          <div key={item.id}>{item.name}</div>
        ))}
      </div>
    </PullToRefresh>
  );
}
```

### PullToRefresh - Custom Indicator

```jsx
import { PULL_STATES } from '@/hooks/usePullToRefresh';

const customIndicator = (state, progress) => (
  <div>
    <div style={{ transform: `rotate(${progress * 360}deg)` }}>
      🔄
    </div>
    <span>
      {state === PULL_STATES.PULLING && `${Math.round(progress * 100)}%`}
      {state === PULL_STATES.READY && 'Release to refresh'}
      {state === PULL_STATES.REFRESHING && 'Loading...'}
    </span>
  </div>
);

<PullToRefresh
  onRefresh={handleRefresh}
  renderIndicator={customIndicator}
>
  <Content />
</PullToRefresh>
```

### PullToRefresh - Using Hook Directly

```jsx
import { usePullToRefresh } from '@/hooks';

function CustomComponent() {
  const {
    pullState,
    pullProgress,
    pullDistance,
    handlers,
    containerRef,
  } = usePullToRefresh({
    onRefresh: async () => {
      await fetchData();
    },
    threshold: 80,
  });

  return (
    <div ref={containerRef} {...handlers} className="overflow-auto">
      {/* Custom indicator */}
      {pullDistance > 0 && (
        <div style={{ height: pullDistance }}>
          Loading... {Math.round(pullProgress * 100)}%
        </div>
      )}

      {/* Your content */}
      <YourContent />
    </div>
  );
}
```

### Combined - Swipeable List with Pull to Refresh

```jsx
import { SwipeableRow, SwipeableRowProvider } from '@/components/ui/SwipeableRow';
import PullToRefresh from '@/components/ui/PullToRefresh';

function TaskList() {
  const [tasks, setTasks] = useState([]);

  const handleRefresh = async () => {
    const newTasks = await fetchTasks();
    setTasks(newTasks);
  };

  return (
    <PullToRefresh onRefresh={handleRefresh}>
      <SwipeableRowProvider>
        <div className="space-y-3">
          {tasks.map(task => (
            <SwipeableRow
              key={task.id}
              id={`task-${task.id}`}
              leftActions={[/* ... */]}
              rightActions={[/* ... */]}
            >
              <div className="bg-white p-4 rounded-lg">
                {task.title}
              </div>
            </SwipeableRow>
          ))}
        </div>
      </SwipeableRowProvider>
    </PullToRefresh>
  );
}
```

## API Reference

### SwipeableRow Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `id` | string | required | Unique identifier for this row |
| `leftActions` | Action[] | `[]` | Actions revealed on left swipe |
| `rightActions` | Action[] | `[]` | Actions revealed on right swipe |
| `longPressActions` | Action[] | `[]` | Actions shown in context menu |
| `onLongPress` | function | - | Callback for long press |
| `disabled` | boolean | `false` | Disable all gestures |
| `className` | string | - | Container class name |
| `innerClassName` | string | - | Content wrapper class name |
| `onSwipeStart` | function | - | Callback when swipe starts |
| `onSwipeEnd` | function | - | Callback when swipe ends |

### Action Object

```typescript
{
  label: string;           // Action label
  icon?: Component;        // Icon component (from lucide-react)
  variant?: string;        // 'danger' | 'primary' | 'success'
  onAction: () => void;    // Action callback
}
```

### PullToRefresh Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `onRefresh` | async function | required | Refresh callback (returns Promise) |
| `threshold` | number | `80` | Pull distance to trigger refresh (px) |
| `maxPull` | number | `120` | Maximum pull distance (px) |
| `disabled` | boolean | `false` | Disable pull to refresh |
| `className` | string | - | Container class name |
| `contentClassName` | string | - | Content wrapper class name |
| `indicatorClassName` | string | - | Indicator class name |
| `renderIndicator` | function | - | Custom indicator renderer |
| `showText` | boolean | `true` | Show text in default indicator |

### usePullToRefresh Hook

```typescript
const {
  pullState,        // Current state: 'idle' | 'pulling' | 'ready' | 'refreshing' | 'done'
  pullProgress,     // Progress from 0 to 1
  pullDistance,     // Pull distance in pixels
  isRefreshing,     // Boolean: is currently refreshing
  isPulling,        // Boolean: is currently being pulled
  isReady,          // Boolean: ready to refresh (past threshold)
  isDone,           // Boolean: refresh complete
  handlers,         // Touch event handlers to spread on element
  containerRef,     // Ref to attach to scrollable container
  refresh,          // Manual refresh function
  reset,            // Manual reset function
} = usePullToRefresh({
  onRefresh,        // async function
  threshold,        // number (default: 80)
  maxPull,          // number (default: 120)
  resistance,       // number 0-1 (default: 0.5)
  disabled,         // boolean (default: false)
  hapticFeedback,   // boolean (default: true)
});
```

### Pull States

```javascript
import { PULL_STATES } from '@/hooks/usePullToRefresh';

PULL_STATES.IDLE        // Not pulling
PULL_STATES.PULLING     // Currently pulling down
PULL_STATES.READY       // Pulled past threshold, ready to refresh
PULL_STATES.REFRESHING  // Currently refreshing
PULL_STATES.DONE        // Refresh complete
```

## Configuration

### Swipe Thresholds

You can customize swipe behavior by modifying constants in `SwipeableRow.jsx`:

```javascript
const SWIPE_REVEAL_THRESHOLD = 80;   // pixels to reveal actions
const SWIPE_CONFIRM_THRESHOLD = 150; // pixels to auto-execute
const SWIPE_VELOCITY_THRESHOLD = 0.5; // velocity for quick swipe
```

### Pull to Refresh Settings

Configure pull behavior in `usePullToRefresh.js`:

```javascript
const PULL_THRESHOLD = 80;       // pixels to trigger refresh
const MAX_PULL = 120;            // maximum pull distance
const RESISTANCE_FACTOR = 0.5;   // resistance (0-1, lower = more resistance)
```

## Best Practices

### Performance

1. **Use SwipeableRowProvider** at the list level, not per row
2. **Memoize action handlers** to prevent unnecessary re-renders
3. **Use PullToRefreshSimple** for large lists if performance is critical
4. **Avoid heavy computations** in render functions

```jsx
// Good ✅
const handleDelete = useCallback((item) => {
  deleteItem(item.id);
}, []);

// Bad ❌
<SwipeableRow
  leftActions={[{
    onAction: () => deleteItem(item.id) // Creates new function on each render
  }]}
/>
```

### Accessibility

1. Provide keyboard alternatives for swipe actions
2. Add ARIA labels to action buttons
3. Ensure sufficient color contrast
4. Test with screen readers

### UX Guidelines

1. **SwipeableRow:**
   - Left swipe (→) for destructive actions (delete)
   - Right swipe (←) for primary actions (edit, complete)
   - Long press for secondary menu
   - Provide visual feedback (haptic + animation)
   - Auto-close other rows when opening new one

2. **PullToRefresh:**
   - Only works at scroll position 0 (top)
   - Show progress indicator
   - Provide haptic feedback at threshold
   - Brief "done" state before resetting
   - Don't trigger on small accidental pulls

## Integration with Existing Components

### MobileDataTable

The `MobileDataTable` component already uses `SwipeableRow`. You can enhance it:

```jsx
<MobileDataTable
  data={data}
  columns={columns}
  swipeActions={{
    left: [{ label: 'Delete', icon: Trash2, variant: 'danger', onAction: handleDelete }],
    right: [{ label: 'Edit', icon: Edit, variant: 'primary', onAction: handleEdit }],
  }}
/>
```

### Adding PullToRefresh to Existing Pages

Wrap your page content:

```jsx
import PullToRefresh from '@/components/ui/PullToRefresh';

function InvoicesPage() {
  const { refetch } = useInvoices();

  return (
    <PullToRefresh onRefresh={refetch}>
      <InvoicesList />
    </PullToRefresh>
  );
}
```

## Demo

A comprehensive demo is available at:
- **File:** `/frontend/src/examples/MobileUXDemo.jsx`

The demo includes:
1. Basic swipeable row
2. Email-style list with quick actions
3. Basic pull-to-refresh
4. Custom indicator example
5. Combined swipe + pull-to-refresh
6. Custom hook usage

To run the demo, import and render `MobileUXDemo` component in your app.

## Browser Support

- ✅ iOS Safari 13+
- ✅ Chrome Mobile 90+
- ✅ Firefox Mobile 90+
- ✅ Samsung Internet 14+
- ✅ Desktop browsers (with mouse drag)

## Dependencies

All dependencies are already installed:
- `framer-motion` - Animations
- `lucide-react` - Icons
- `clsx` - Class name utilities

## Troubleshooting

### Swipe not working

1. Ensure `SwipeableRowProvider` wraps the list
2. Check that `id` prop is unique for each row
3. Verify actions array is not empty
4. Check for conflicting CSS (`touch-action` property)

### Pull-to-refresh not triggering

1. Ensure element is scrollable
2. Check scroll position is at top (0)
3. Verify `onRefresh` is an async function
4. Check `threshold` value (default 80px)

### Performance issues

1. Use `PullToRefreshSimple` for large lists
2. Memoize callbacks with `useCallback`
3. Reduce animation complexity
4. Check for excessive re-renders

## Future Enhancements

Potential additions:
- [ ] Swipe to dismiss (e.g., notifications)
- [ ] Swipe between views (carousel)
- [ ] Pinch to zoom gesture
- [ ] Multi-finger gestures
- [ ] Gesture recording/replay for testing
- [ ] Analytics integration

## Testing

Manual testing checklist:
- [ ] Swipe left reveals left actions
- [ ] Swipe right reveals right actions
- [ ] Quick swipe executes action
- [ ] Long press shows context menu
- [ ] Opening row closes other rows
- [ ] Pull down triggers refresh
- [ ] Pull indicator shows progress
- [ ] Haptic feedback works (on supported devices)
- [ ] Works with keyboard (Tab + Enter)
- [ ] Screen reader announces actions

## License

Part of the main project. See project LICENSE file.
