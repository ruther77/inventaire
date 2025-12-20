# Mobile UX Features - Quick Start Guide

Get up and running with swipe-to-action and pull-to-refresh in 5 minutes.

## Installation

All dependencies are already installed. No additional setup required!

## Quick Integration

### 1. Add Swipe-to-Action to a List (2 minutes)

```jsx
import { SwipeableRow, SwipeableRowProvider } from '@/components/ui/SwipeableRow';
import { Trash2, Edit } from 'lucide-react';

// Wrap your list with SwipeableRowProvider
function MyList() {
  return (
    <SwipeableRowProvider>
      <div className="space-y-3">
        {items.map((item) => (
          <SwipeableRow
            key={item.id}
            id={`item-${item.id}`}
            leftActions={[
              {
                label: 'Delete',
                icon: Trash2,
                variant: 'danger',
                onAction: () => handleDelete(item),
              },
            ]}
            rightActions={[
              {
                label: 'Edit',
                icon: Edit,
                variant: 'primary',
                onAction: () => handleEdit(item),
              },
            ]}
          >
            {/* Your existing row content */}
            <div className="bg-white p-4 rounded-lg">
              {item.name}
            </div>
          </SwipeableRow>
        ))}
      </div>
    </SwipeableRowProvider>
  );
}
```

**That's it!** Your list now supports:
- Swipe left to delete
- Swipe right to edit
- Auto-close when opening another row

### 2. Add Pull-to-Refresh to a Page (1 minute)

```jsx
import PullToRefresh from '@/components/ui/PullToRefresh';

function MyPage() {
  const { refetch } = useQuery(); // Your data fetching hook

  return (
    <PullToRefresh onRefresh={refetch}>
      {/* Your existing page content */}
      <div className="p-4">
        <MyContent />
      </div>
    </PullToRefresh>
  );
}
```

**Done!** Your page now has pull-to-refresh.

### 3. Combine Both (3 minutes)

```jsx
import { SwipeableRow, SwipeableRowProvider } from '@/components/ui/SwipeableRow';
import PullToRefresh from '@/components/ui/PullToRefresh';
import { Trash2, Check } from 'lucide-react';

function TaskList() {
  const { data: tasks, refetch } = useTasks();

  return (
    <PullToRefresh onRefresh={refetch}>
      <SwipeableRowProvider>
        <div className="p-4 space-y-3">
          {tasks.map((task) => (
            <SwipeableRow
              key={task.id}
              id={`task-${task.id}`}
              leftActions={[
                {
                  label: 'Delete',
                  icon: Trash2,
                  variant: 'danger',
                  onAction: () => deleteTask(task.id),
                },
              ]}
              rightActions={[
                {
                  label: 'Complete',
                  icon: Check,
                  variant: 'success',
                  onAction: () => completeTask(task.id),
                },
              ]}
            >
              <div className="bg-white p-4 rounded-lg border">
                <h3 className="font-semibold">{task.title}</h3>
                <p className="text-sm text-slate-600">{task.description}</p>
              </div>
            </SwipeableRow>
          ))}
        </div>
      </SwipeableRowProvider>
    </PullToRefresh>
  );
}
```

**Perfect!** You now have:
- Swipeable rows with actions
- Pull-to-refresh
- Auto-close behavior
- Haptic feedback
- Smooth animations

## Common Patterns

### Pattern 1: Invoice List

```jsx
<SwipeableRowProvider>
  {invoices.map(invoice => (
    <SwipeableRow
      key={invoice.id}
      id={`invoice-${invoice.id}`}
      leftActions={[
        { label: 'Delete', icon: Trash2, variant: 'danger', onAction: () => del(invoice) }
      ]}
      rightActions={[
        { label: 'Edit', icon: Edit, variant: 'primary', onAction: () => edit(invoice) },
        { label: 'Archive', icon: Archive, variant: 'success', onAction: () => archive(invoice) }
      ]}
    >
      <InvoiceCard invoice={invoice} />
    </SwipeableRow>
  ))}
</SwipeableRowProvider>
```

### Pattern 2: Transaction List with Refresh

```jsx
function TransactionList() {
  const { data, refetch } = useTransactions();

  return (
    <PullToRefresh onRefresh={refetch}>
      <div className="space-y-2 p-4">
        {data.map(tx => (
          <TransactionCard key={tx.id} transaction={tx} />
        ))}
      </div>
    </PullToRefresh>
  );
}
```

### Pattern 3: Email-style List

```jsx
<SwipeableRowProvider>
  {emails.map(email => (
    <SwipeableRow
      key={email.id}
      id={`email-${email.id}`}
      leftActions={[
        { label: 'Archive', icon: Archive, variant: 'danger', onAction: () => archive(email) }
      ]}
      rightActions={[
        { label: email.read ? 'Unread' : 'Read', icon: Mail, variant: 'primary', onAction: () => toggleRead(email) }
      ]}
      longPressActions={[
        { label: 'Star', icon: Star, onAction: () => star(email) },
        { label: 'Forward', icon: Forward, onAction: () => forward(email) }
      ]}
    >
      <EmailCard email={email} />
    </SwipeableRow>
  ))}
</SwipeableRowProvider>
```

## Integration with Existing Pages

### Finance Pages

```jsx
// BankReconciliationPage.jsx
import PullToRefresh from '@/components/ui/PullToRefresh';

export function BankReconciliationPage() {
  const { refetch } = useBankReconciliation();

  return (
    <PullToRefresh onRefresh={refetch}>
      {/* Existing content */}
    </PullToRefresh>
  );
}
```

### Invoice Pages

```jsx
// InvoicesListPage.jsx
import { SwipeableRow, SwipeableRowProvider } from '@/components/ui/SwipeableRow';
import { Trash2, Edit, Download } from 'lucide-react';

export function InvoicesListPage() {
  return (
    <SwipeableRowProvider>
      {invoices.map(invoice => (
        <SwipeableRow
          key={invoice.id}
          id={`invoice-${invoice.id}`}
          leftActions={[
            { label: 'Delete', icon: Trash2, variant: 'danger', onAction: () => deleteInvoice(invoice) }
          ]}
          rightActions={[
            { label: 'Edit', icon: Edit, variant: 'primary', onAction: () => editInvoice(invoice) },
            { label: 'Download', icon: Download, variant: 'success', onAction: () => downloadInvoice(invoice) }
          ]}
        >
          <InvoiceCard invoice={invoice} />
        </SwipeableRow>
      ))}
    </SwipeableRowProvider>
  );
}
```

### Restaurant Pages

```jsx
// IngredientsPage.jsx
import PullToRefresh from '@/components/ui/PullToRefresh';
import { SwipeableRow, SwipeableRowProvider } from '@/components/ui/SwipeableRow';

export function IngredientsPage() {
  const { data, refetch } = useIngredients();

  return (
    <PullToRefresh onRefresh={refetch}>
      <SwipeableRowProvider>
        <div className="p-4 space-y-3">
          {data.map(ingredient => (
            <SwipeableRow
              key={ingredient.id}
              id={`ingredient-${ingredient.id}`}
              leftActions={[
                { label: 'Delete', icon: Trash2, variant: 'danger', onAction: () => del(ingredient) }
              ]}
              rightActions={[
                { label: 'Edit', icon: Edit, variant: 'primary', onAction: () => edit(ingredient) }
              ]}
            >
              <IngredientCard ingredient={ingredient} />
            </SwipeableRow>
          ))}
        </div>
      </SwipeableRowProvider>
    </PullToRefresh>
  );
}
```

## Customization

### Custom Colors

```jsx
// Use your brand colors for actions
leftActions={[
  {
    label: 'Delete',
    icon: Trash2,
    variant: 'danger', // bg-rose-500
    onAction: handleDelete
  }
]}

rightActions={[
  {
    label: 'Edit',
    icon: Edit,
    variant: 'primary', // bg-blue-500
    onAction: handleEdit
  },
  {
    label: 'Complete',
    icon: Check,
    variant: 'success', // bg-emerald-500
    onAction: handleComplete
  }
]}
```

### Custom Pull Indicator

```jsx
import { PULL_STATES } from '@/hooks/usePullToRefresh';

const MyIndicator = (state, progress) => (
  <div className="flex items-center gap-2">
    <div style={{ transform: `rotate(${progress * 360}deg)` }}>
      🔄
    </div>
    <span>{Math.round(progress * 100)}%</span>
  </div>
);

<PullToRefresh
  onRefresh={handleRefresh}
  renderIndicator={MyIndicator}
>
  <Content />
</PullToRefresh>
```

### Adjust Thresholds

```jsx
// More sensitive swipe
<SwipeableRow
  leftActions={actions}
  rightActions={actions}
  // Threshold is configured in the component constants
  // See SwipeableRow.jsx to adjust SWIPE_REVEAL_THRESHOLD
>

// Easier pull-to-refresh
<PullToRefresh
  onRefresh={handleRefresh}
  threshold={60}  // Default is 80
  maxPull={100}   // Default is 120
>
```

## Tips & Tricks

### 1. Memoize Handlers

```jsx
const handleDelete = useCallback((item) => {
  deleteItem(item.id);
}, []);

const handleEdit = useCallback((item) => {
  editItem(item.id);
}, []);
```

### 2. Conditional Actions

```jsx
leftActions={item.canDelete ? [
  { label: 'Delete', icon: Trash2, variant: 'danger', onAction: () => del(item) }
] : []}

rightActions={item.canEdit ? [
  { label: 'Edit', icon: Edit, variant: 'primary', onAction: () => edit(item) }
] : []}
```

### 3. Context Menu for More Actions

```jsx
<SwipeableRow
  leftActions={[/* primary actions */]}
  rightActions={[/* primary actions */]}
  longPressActions={[
    { label: 'Share', icon: Share, onAction: () => share(item) },
    { label: 'Duplicate', icon: Copy, onAction: () => duplicate(item) },
    { label: 'Archive', icon: Archive, onAction: () => archive(item) },
  ]}
>
```

### 4. Loading States

```jsx
function MyList() {
  const { data, isLoading, refetch } = useQuery();

  if (isLoading) return <Spinner />;

  return (
    <PullToRefresh onRefresh={refetch}>
      <List data={data} />
    </PullToRefresh>
  );
}
```

## Testing

### Manual Testing Checklist

On mobile device or Chrome DevTools mobile emulation:

- [ ] Swipe left reveals left actions
- [ ] Swipe right reveals right actions
- [ ] Quick swipe auto-executes first action
- [ ] Opening one row closes others
- [ ] Long press shows context menu (if configured)
- [ ] Pull down from top triggers refresh
- [ ] Pull indicator shows progress
- [ ] Refresh completes and resets
- [ ] Haptic feedback works (on real device)

### Testing in Chrome DevTools

1. Open Chrome DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Select mobile device (e.g., iPhone 12 Pro)
4. Test swipe gestures with mouse
5. Test pull-to-refresh by dragging down

## Performance

These components are production-ready and optimized:

- ✅ Uses Framer Motion's hardware-accelerated animations
- ✅ Minimal re-renders with proper memoization
- ✅ Touch event handling is optimized
- ✅ No layout thrashing
- ✅ Works smoothly on low-end devices

For very large lists (1000+ items), consider:
- Use virtualization (`useVirtualList` hook)
- Use `PullToRefreshSimple` instead of animated version
- Lazy load list items

## Troubleshooting

**Swipe not working?**
- Ensure `SwipeableRowProvider` wraps your list
- Check `id` prop is unique
- Verify actions array is not empty

**Pull-to-refresh not triggering?**
- Container must be scrollable
- Must be at scroll position 0 (top)
- `onRefresh` must return a Promise

**Animations janky?**
- Reduce list size or use virtualization
- Check for expensive renders in children
- Use `PullToRefreshSimple` for better performance

## Next Steps

1. ✅ Try the demo: `/frontend/src/examples/MobileUXDemo.jsx`
2. ✅ Read full docs: `/frontend/MOBILE_UX_FEATURES.md`
3. ✅ Integrate into your pages (start with one page)
4. ✅ Test on real mobile devices
5. ✅ Adjust thresholds to your preference

## Support

For issues or questions:
1. Check `/frontend/MOBILE_UX_FEATURES.md` for detailed API docs
2. Review demo examples in `/frontend/src/examples/MobileUXDemo.jsx`
3. Check existing usage in `MobileDataTable.jsx`

Happy swiping! 🚀
