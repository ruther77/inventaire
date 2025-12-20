# Mobile UX - Integration Examples

Real-world before/after examples showing how to integrate swipe-to-action and pull-to-refresh into existing pages.

## Example 1: Simple List Page

### Before

```jsx
// pages/InvoicesPage.jsx
export function InvoicesPage() {
  const { data: invoices } = useInvoices();

  return (
    <div className="p-4 space-y-3">
      {invoices.map(invoice => (
        <div key={invoice.id} className="bg-white rounded-lg border p-4">
          <div className="flex justify-between">
            <div>
              <h3 className="font-semibold">{invoice.number}</h3>
              <p className="text-sm text-slate-600">{invoice.supplier}</p>
            </div>
            <div className="text-lg font-bold">{invoice.amount}€</div>
          </div>

          {/* Action buttons take up space */}
          <div className="flex gap-2 mt-3">
            <button onClick={() => handleEdit(invoice)} className="btn-primary">
              Edit
            </button>
            <button onClick={() => handleDelete(invoice)} className="btn-danger">
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
```

### After - With Swipe Actions

```jsx
// pages/InvoicesPage.jsx
import { SwipeableRow, SwipeableRowProvider } from '@/components/ui/SwipeableRow';
import { Edit, Trash2 } from 'lucide-react';

export function InvoicesPage() {
  const { data: invoices } = useInvoices();

  return (
    <SwipeableRowProvider>
      <div className="p-4 space-y-3">
        {invoices.map(invoice => (
          <SwipeableRow
            key={invoice.id}
            id={`invoice-${invoice.id}`}
            leftActions={[
              { label: 'Delete', icon: Trash2, variant: 'danger', onAction: () => handleDelete(invoice) }
            ]}
            rightActions={[
              { label: 'Edit', icon: Edit, variant: 'primary', onAction: () => handleEdit(invoice) }
            ]}
          >
            <div className="bg-white rounded-lg border p-4">
              <div className="flex justify-between">
                <div>
                  <h3 className="font-semibold">{invoice.number}</h3>
                  <p className="text-sm text-slate-600">{invoice.supplier}</p>
                </div>
                <div className="text-lg font-bold">{invoice.amount}€</div>
              </div>
              {/* No more action buttons! Clean UI, more space */}
            </div>
          </SwipeableRow>
        ))}
      </div>
    </SwipeableRowProvider>
  );
}
```

**Benefits:**
- 🎨 Cleaner UI - no button clutter
- 📱 Native mobile feel
- ⚡ Faster actions - no need to tap small buttons
- 💾 More space for content

---

## Example 2: Data List with Refresh

### Before

```jsx
// pages/TransactionsPage.jsx
export function TransactionsPage() {
  const { data: transactions, isLoading, refetch } = useTransactions();

  return (
    <div>
      {/* Manual refresh button */}
      <div className="p-4 border-b">
        <button
          onClick={refetch}
          disabled={isLoading}
          className="btn-primary w-full"
        >
          {isLoading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      <div className="p-4 space-y-2">
        {transactions.map(tx => (
          <div key={tx.id} className="bg-white rounded-lg border p-4">
            <div className="flex justify-between">
              <span>{tx.description}</span>
              <span className="font-bold">{tx.amount}€</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### After - With Pull-to-Refresh

```jsx
// pages/TransactionsPage.jsx
import PullToRefresh from '@/components/ui/PullToRefresh';

export function TransactionsPage() {
  const { data: transactions, refetch } = useTransactions();

  return (
    <PullToRefresh onRefresh={refetch} className="min-h-screen">
      {/* No manual refresh button needed! */}
      <div className="p-4 space-y-2">
        {transactions.map(tx => (
          <div key={tx.id} className="bg-white rounded-lg border p-4">
            <div className="flex justify-between">
              <span>{tx.description}</span>
              <span className="font-bold">{tx.amount}€</span>
            </div>
          </div>
        ))}
      </div>
    </PullToRefresh>
  );
}
```

**Benefits:**
- 🔄 Native pull-to-refresh gesture
- 🎯 No button needed - more space
- 📱 Standard mobile pattern users expect
- ⚡ Visual feedback with progress indicator

---

## Example 3: Complex List with Multiple Actions

### Before

```jsx
// pages/EmailsPage.jsx
export function EmailsPage() {
  const [emails, setEmails] = useState([]);

  return (
    <div className="p-4 space-y-2">
      {emails.map(email => (
        <div key={email.id} className="bg-white rounded-lg border p-4">
          <div className="flex justify-between items-start mb-3">
            <div className="flex-1">
              <h3 className="font-semibold">{email.sender}</h3>
              <p className="text-sm">{email.subject}</p>
            </div>
            <span className="text-xs text-slate-500">{email.time}</span>
          </div>

          {/* Actions row takes space and looks cluttered */}
          <div className="flex gap-2">
            <button onClick={() => archive(email)} className="btn-sm">
              Archive
            </button>
            <button onClick={() => markRead(email)} className="btn-sm">
              {email.read ? 'Unread' : 'Read'}
            </button>
            <button onClick={() => star(email)} className="btn-sm">
              Star
            </button>
            <button onClick={() => forward(email)} className="btn-sm">
              Forward
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
```

### After - With Swipe + Long Press

```jsx
// pages/EmailsPage.jsx
import { SwipeableRow, SwipeableRowProvider } from '@/components/ui/SwipeableRow';
import { Archive, Mail, Star, Forward } from 'lucide-react';

export function EmailsPage() {
  const [emails, setEmails] = useState([]);

  return (
    <SwipeableRowProvider>
      <div className="p-4 space-y-2">
        {emails.map(email => (
          <SwipeableRow
            key={email.id}
            id={`email-${email.id}`}
            // Quick actions: swipe left/right
            leftActions={[
              { label: 'Archive', icon: Archive, variant: 'danger', onAction: () => archive(email) }
            ]}
            rightActions={[
              { label: email.read ? 'Unread' : 'Read', icon: Mail, variant: 'primary', onAction: () => markRead(email) }
            ]}
            // More actions: long press
            longPressActions={[
              { label: 'Star', icon: Star, onAction: () => star(email) },
              { label: 'Forward', icon: Forward, onAction: () => forward(email) }
            ]}
          >
            <div className="bg-white rounded-lg border p-4">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold">{email.sender}</h3>
                  <p className="text-sm">{email.subject}</p>
                </div>
                <span className="text-xs text-slate-500">{email.time}</span>
              </div>
              {/* Clean! No button row needed */}
            </div>
          </SwipeableRow>
        ))}
      </div>
    </SwipeableRowProvider>
  );
}
```

**Benefits:**
- 🎯 Primary actions via swipe (archive, read)
- 📱 Secondary actions via long press (star, forward)
- 🎨 Much cleaner UI
- ⚡ Faster interaction on mobile

---

## Example 4: Combined - Full Mobile Experience

### Before

```jsx
// pages/TasksPage.jsx
export function TasksPage() {
  const { data: tasks, isLoading, refetch } = useTasks();

  return (
    <div>
      <div className="p-4 border-b bg-white sticky top-0 z-10">
        <button onClick={refetch} disabled={isLoading} className="btn-primary w-full">
          {isLoading ? 'Loading...' : 'Refresh Tasks'}
        </button>
      </div>

      <div className="p-4 space-y-3">
        {tasks.map(task => (
          <div key={task.id} className="bg-white rounded-lg border p-4">
            <div className="flex items-start gap-3 mb-3">
              <input
                type="checkbox"
                checked={task.completed}
                onChange={() => toggle(task)}
              />
              <div className="flex-1">
                <h3 className={task.completed ? 'line-through' : ''}>
                  {task.title}
                </h3>
              </div>
            </div>

            <div className="flex gap-2">
              <button onClick={() => edit(task)} className="btn-sm btn-primary">
                Edit
              </button>
              <button onClick={() => del(task)} className="btn-sm btn-danger">
                Delete
              </button>
              <button onClick={() => complete(task)} className="btn-sm btn-success">
                {task.completed ? 'Undo' : 'Complete'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### After - Full Mobile UX

```jsx
// pages/TasksPage.jsx
import { SwipeableRow, SwipeableRowProvider } from '@/components/ui/SwipeableRow';
import PullToRefresh from '@/components/ui/PullToRefresh';
import { Trash2, Check, Edit, X } from 'lucide-react';

export function TasksPage() {
  const { data: tasks, refetch } = useTasks();

  return (
    <PullToRefresh onRefresh={refetch} className="min-h-screen">
      <SwipeableRowProvider>
        <div className="p-4 space-y-3">
          {tasks.map(task => (
            <SwipeableRow
              key={task.id}
              id={`task-${task.id}`}
              leftActions={[
                { label: 'Delete', icon: Trash2, variant: 'danger', onAction: () => del(task) }
              ]}
              rightActions={[
                {
                  label: task.completed ? 'Undo' : 'Complete',
                  icon: task.completed ? X : Check,
                  variant: 'success',
                  onAction: () => complete(task)
                }
              ]}
              longPressActions={[
                { label: 'Edit', icon: Edit, onAction: () => edit(task) }
              ]}
            >
              <div className="bg-white rounded-lg border p-4">
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    checked={task.completed}
                    onChange={() => toggle(task)}
                  />
                  <div className="flex-1">
                    <h3 className={task.completed ? 'line-through' : ''}>
                      {task.title}
                    </h3>
                  </div>
                </div>
                {/* No buttons! Clean design */}
              </div>
            </SwipeableRow>
          ))}
        </div>
      </SwipeableRowProvider>
    </PullToRefresh>
  );
}
```

**Benefits:**
- 🔄 Pull-to-refresh (no button needed)
- ⬅️ Swipe left to delete
- ➡️ Swipe right to complete
- 👆 Long press to edit
- 🎨 Minimal, clean UI
- 📱 Native mobile experience
- ⚡ Faster interactions

---

## Example 5: Existing MobileDataTable Enhancement

### Before

```jsx
// Using basic MobileDataTable
<MobileDataTable
  data={invoices}
  columns={[
    { key: 'number', header: 'Number' },
    { key: 'supplier', header: 'Supplier' },
    { key: 'amount', header: 'Amount' },
  ]}
  onRowClick={(invoice) => navigate(`/invoices/${invoice.id}`)}
/>
```

### After - With Swipe Actions

```jsx
// Enhanced with swipe actions
import { Trash2, Edit, Download } from 'lucide-react';

<MobileDataTable
  data={invoices}
  columns={[
    { key: 'number', header: 'Number' },
    { key: 'supplier', header: 'Supplier' },
    { key: 'amount', header: 'Amount' },
  ]}
  swipeActions={{
    left: [
      {
        label: 'Delete',
        icon: Trash2,
        variant: 'danger',
        onAction: (invoice) => deleteInvoice(invoice.id)
      }
    ],
    right: [
      {
        label: 'Edit',
        icon: Edit,
        variant: 'primary',
        onAction: (invoice) => navigate(`/invoices/${invoice.id}/edit`)
      },
      {
        label: 'Download',
        icon: Download,
        variant: 'success',
        onAction: (invoice) => downloadPDF(invoice.id)
      }
    ]
  }}
  onRowClick={(invoice) => navigate(`/invoices/${invoice.id}`)}
/>
```

**Benefits:**
- 🎯 Swipe actions without changing existing structure
- 📱 Mobile-friendly interaction
- ⚡ Quick access to common actions
- 🔄 Still supports row click for navigation

---

## Integration Patterns

### Pattern 1: Simple Enhancement

Just wrap existing content:

```jsx
// Minimal change
<SwipeableRowProvider>
  {items.map(item => (
    <SwipeableRow key={item.id} id={item.id} leftActions={[...]} rightActions={[...]}>
      <ExistingCard item={item} />
    </SwipeableRow>
  ))}
</SwipeableRowProvider>
```

### Pattern 2: Page-Level Refresh

Wrap entire page content:

```jsx
function MyPage() {
  const { refetch } = useData();

  return (
    <PullToRefresh onRefresh={refetch}>
      <ExistingPageContent />
    </PullToRefresh>
  );
}
```

### Pattern 3: Full Mobile Experience

Combine both features:

```jsx
function MyPage() {
  const { data, refetch } = useData();

  return (
    <PullToRefresh onRefresh={refetch}>
      <SwipeableRowProvider>
        {data.map(item => (
          <SwipeableRow key={item.id} id={item.id} {...actions}>
            <ItemCard item={item} />
          </SwipeableRow>
        ))}
      </SwipeableRowProvider>
    </PullToRefresh>
  );
}
```

---

## Migration Checklist

When migrating existing pages:

### For Lists
- [ ] Identify action buttons to move to swipe actions
- [ ] Choose primary actions for swipe (edit, delete, complete)
- [ ] Choose secondary actions for long press (share, duplicate)
- [ ] Add `SwipeableRowProvider` wrapper
- [ ] Wrap each item with `SwipeableRow`
- [ ] Remove action button rows
- [ ] Test swipe gestures

### For Pages with Refresh
- [ ] Identify refresh mechanism (button, auto-refresh)
- [ ] Add `PullToRefresh` wrapper
- [ ] Pass `refetch` function to `onRefresh`
- [ ] Remove manual refresh button
- [ ] Test pull-to-refresh gesture

### Testing
- [ ] Test on Chrome DevTools mobile emulation
- [ ] Test swipe left/right
- [ ] Test long press
- [ ] Test pull-to-refresh from top
- [ ] Test on real mobile device
- [ ] Verify haptic feedback works
- [ ] Check auto-close behavior

---

## Pro Tips

### 1. Gradual Migration

Don't migrate everything at once:

```jsx
// Week 1: Add to one page
<TasksPage /> // ✅ Migrated

// Week 2: Add to another page
<InvoicesPage /> // ✅ Migrated

// Week 3: Continue...
<TransactionsPage /> // ✅ Migrated
```

### 2. Feature Detection

Add gradually with feature flags:

```jsx
const useMobileGestures = useFeatureFlag('mobile-gestures');

return useMobileGestures ? (
  <SwipeableRow {...props}>
    <Content />
  </SwipeableRow>
) : (
  <Content />
);
```

### 3. Preserve Desktop Experience

Keep desktop buttons, add mobile gestures:

```jsx
<SwipeableRow {...actions}>
  <div className="card">
    <Content />

    {/* Desktop actions - hidden on mobile */}
    <div className="hidden md:flex gap-2">
      <button onClick={handleEdit}>Edit</button>
      <button onClick={handleDelete}>Delete</button>
    </div>
  </div>
</SwipeableRow>
```

### 4. Conditional Actions

Show different actions based on state:

```jsx
<SwipeableRow
  leftActions={item.canDelete ? [deleteAction] : []}
  rightActions={item.canEdit ? [editAction] : []}
>
  <Content />
</SwipeableRow>
```

---

## Common Issues & Solutions

### Issue: Too many actions

**Problem:** 5+ actions don't fit on swipe

**Solution:** Use primary actions for swipe, rest in long press menu

```jsx
<SwipeableRow
  leftActions={[/* 1-2 most important */]}
  rightActions={[/* 1-2 most important */]}
  longPressActions={[/* All other actions */]}
>
```

### Issue: Conflicts with existing click handlers

**Problem:** Row click conflicts with swipe

**Solution:** Differentiate tap vs swipe

```jsx
<SwipeableRow {...actions}>
  <div
    onClick={(e) => {
      // Only trigger if not swiping
      if (e.target === e.currentTarget) {
        handleClick(item);
      }
    }}
  >
    <Content />
  </div>
</SwipeableRow>
```

### Issue: Performance on large lists

**Problem:** Swipe animations slow on 1000+ items

**Solution:** Use virtualization

```jsx
import { useVirtualList } from '@/hooks';

const { virtualItems, containerRef } = useVirtualList({
  items: largeList,
  itemHeight: 80,
});

return (
  <div ref={containerRef}>
    {virtualItems.map(virtual => (
      <SwipeableRow key={virtual.key} {...}>
        <ItemCard item={largeList[virtual.index]} />
      </SwipeableRow>
    ))}
  </div>
);
```

---

## Summary

**Before:**
- Cluttered UI with action buttons
- Manual refresh buttons
- More taps needed
- Less mobile-friendly

**After:**
- Clean, minimal UI
- Native mobile gestures
- Faster interactions
- Better UX on mobile

**Migration is easy:**
1. Wrap list with `SwipeableRowProvider`
2. Wrap items with `SwipeableRow`
3. Wrap page with `PullToRefresh`
4. Remove old action buttons
5. Test & enjoy! 🎉
