# Background Sync Quick Start Guide

## What is Background Sync?

Background Sync allows your PWA to queue mutations (create, update, delete operations) when offline and automatically synchronize them with the server when the network connection is restored - even if the app is closed!

## How It Works

```
User Action (Offline) → Queue in IndexedDB → Network Restored → Service Worker Syncs → Server Updated
```

## Using Background Sync in Your Code

### 1. Basic Usage with useOfflineMutation Hook

```javascript
import { useOfflineCreate } from '../hooks/useOfflineMutation';
import { useQueryClient } from '@tanstack/react-query';
import api from '../api/client';

function MyComponent() {
  const queryClient = useQueryClient();

  const createProduct = useOfflineCreate({
    endpoint: '/products',
    mutationFn: (data) => api.post('/products', data),
    onSuccess: () => {
      // This callback is called when sync succeeds (online or later)
      queryClient.invalidateQueries(['products']);
      console.log('Product created successfully!');
    },
    onError: (error) => {
      console.error('Failed to create product:', error);
    },
  });

  const handleSubmit = (formData) => {
    createProduct.mutate(formData);
    // If offline, this will queue the mutation
    // If online, this will execute immediately
  };

  return (
    <button onClick={() => handleSubmit({ name: 'New Product' })}>
      Create Product
    </button>
  );
}
```

### 2. Update Operations

```javascript
import { useOfflineUpdate } from '../hooks/useOfflineMutation';

const updateProduct = useOfflineUpdate({
  endpoint: '/products/123',
  mutationFn: (data) => api.put('/products/123', data),
  onSuccess: () => {
    queryClient.invalidateQueries(['products', 123]);
  },
});

updateProduct.mutate({ name: 'Updated Name', price: 29.99 });
```

### 3. Delete Operations

```javascript
import { useOfflineDelete } from '../hooks/useOfflineMutation';

const deleteProduct = useOfflineDelete({
  endpoint: '/products/123',
  mutationFn: () => api.delete('/products/123'),
  onSuccess: () => {
    queryClient.invalidateQueries(['products']);
  },
});

deleteProduct.mutate();
```

### 4. Patch Operations

```javascript
import { useOfflinePatch } from '../hooks/useOfflineMutation';

const updatePrice = useOfflinePatch({
  endpoint: '/products/123',
  mutationFn: (data) => api.patch('/products/123', data),
  metadata: {
    description: 'Update product price',
  },
});

updatePrice.mutate({ price: 39.99 });
```

## Checking Sync Status

### Monitor Pending Mutations

```javascript
import { useOfflineContext } from '../contexts/OfflineContext';

function SyncStatus() {
  const {
    isOnline,
    pendingMutations,
    isSyncing,
    syncError,
  } = useOfflineContext();

  return (
    <div>
      <div>Status: {isOnline ? 'Online' : 'Offline'}</div>
      <div>Pending: {pendingMutations.length} mutations</div>
      {isSyncing && <div>Syncing...</div>}
      {syncError && <div>Error: {syncError}</div>}
    </div>
  );
}
```

### Manual Sync Trigger

```javascript
import { useOfflineContext } from '../contexts/OfflineContext';

function SyncButton() {
  const { syncPendingMutations, isSyncing } = useOfflineContext();

  return (
    <button
      onClick={syncPendingMutations}
      disabled={isSyncing}
    >
      {isSyncing ? 'Syncing...' : 'Sync Now'}
    </button>
  );
}
```

## Listening to Sync Events

```javascript
import { useEffect } from 'react';

function MyComponent() {
  useEffect(() => {
    // Listen for sync messages from service worker
    const handleMessage = (event) => {
      if (event.data.type === 'SYNC_SUCCESS') {
        console.log('Mutation synced:', event.data.mutationId);
        // Refresh data or show notification
      }

      if (event.data.type === 'SYNC_ERROR') {
        console.error('Sync failed:', event.data.error);
        // Show error notification
      }
    };

    navigator.serviceWorker?.addEventListener('message', handleMessage);

    return () => {
      navigator.serviceWorker?.removeEventListener('message', handleMessage);
    };
  }, []);

  return <div>My Component</div>;
}
```

## Advanced Usage

### Custom Mutation with Metadata

```javascript
const createWithMetadata = useOfflineMutation({
  endpoint: '/invoices',
  method: 'POST',
  mutationType: 'CREATE',
  mutationFn: (data) => api.post('/invoices', data),
  metadata: {
    source: 'mobile-app',
    importance: 'high',
    userId: currentUser.id,
  },
  onSuccess: (data) => {
    console.log('Invoice created:', data);
  },
});
```

### Batch Operations

```javascript
const batchUpdate = useOfflineMutation({
  endpoint: '/products/batch',
  method: 'POST',
  mutationType: 'UPDATE',
  mutationFn: (products) => api.post('/products/batch', { products }),
  onSuccess: () => {
    queryClient.invalidateQueries(['products']);
  },
});

// Update multiple products
batchUpdate.mutate([
  { id: 1, price: 10 },
  { id: 2, price: 20 },
  { id: 3, price: 30 },
]);
```

## Best Practices

### 1. Always Provide Feedback

```javascript
const createProduct = useOfflineCreate({
  endpoint: '/products',
  mutationFn: (data) => api.post('/products', data),
  onSuccess: (data) => {
    if (data.queued) {
      toast.info('Product will be created when online');
    } else {
      toast.success('Product created successfully!');
    }
  },
  onError: (error) => {
    toast.error('Failed to create product');
  },
});
```

### 2. Handle Optimistic Updates

```javascript
const updateProduct = useOfflineUpdate({
  endpoint: `/products/${productId}`,
  mutationFn: (data) => api.put(`/products/${productId}`, data),

  // Optimistic update
  onMutate: async (newData) => {
    await queryClient.cancelQueries(['products', productId]);

    const previousData = queryClient.getQueryData(['products', productId]);

    queryClient.setQueryData(['products', productId], (old) => ({
      ...old,
      ...newData,
    }));

    return { previousData };
  },

  // Rollback on error
  onError: (err, newData, context) => {
    queryClient.setQueryData(['products', productId], context.previousData);
  },

  // Refetch on success
  onSuccess: () => {
    queryClient.invalidateQueries(['products', productId]);
  },
});
```

### 3. Show Sync Status in UI

```javascript
function AppHeader() {
  const { isOnline, pendingMutations, isSyncing } = useOfflineContext();

  return (
    <header>
      <h1>My App</h1>
      {!isOnline && (
        <div className="offline-banner">
          You are offline. Changes will sync when connection is restored.
        </div>
      )}
      {isSyncing && (
        <div className="syncing-banner">
          Syncing {pendingMutations.length} changes...
        </div>
      )}
    </header>
  );
}
```

### 4. Implement Idempotent Operations

Make sure your API endpoints can handle duplicate requests safely:

```javascript
// Backend (FastAPI example)
@app.post("/products")
async def create_product(product: ProductCreate, request_id: str = Header(None)):
    # Check if request was already processed
    if request_id:
        existing = await db.get_by_request_id(request_id)
        if existing:
            return existing  # Return existing instead of creating duplicate

    # Create new product
    new_product = await db.create_product(product)
    if request_id:
        await db.store_request_id(request_id, new_product.id)

    return new_product
```

```javascript
// Frontend - add request ID
const createProduct = useOfflineCreate({
  endpoint: '/products',
  mutationFn: (data) => {
    const requestId = generateUUID();
    return api.post('/products', data, {
      headers: { 'X-Request-ID': requestId },
    });
  },
});
```

## Testing

### Simulate Offline Mode

1. **Chrome DevTools:**
   - Open DevTools (F12)
   - Go to Network tab
   - Click dropdown next to "No throttling"
   - Select "Offline"

2. **Programmatically:**
```javascript
// For testing only
if (import.meta.env.DEV) {
  window.simulateOffline = () => {
    // Disconnect service worker (this is a simulation)
    console.log('Simulating offline mode');
  };
}
```

### Test Background Sync

1. Set app to offline mode
2. Perform mutations (create, update, delete)
3. Check IndexedDB (DevTools → Application → IndexedDB → inventaire-offline → mutations)
4. Go back online
5. Watch console for sync logs
6. Verify mutations disappeared from IndexedDB
7. Verify server received the requests

## Troubleshooting

### Mutations Not Queuing

**Problem:** Mutations execute immediately even when offline.

**Solution:**
```javascript
import { useOfflineContext } from '../contexts/OfflineContext';

const { isOnline } = useOfflineContext();

// Check if context is working
console.log('Online status:', isOnline);
```

### Sync Not Happening

**Problem:** Mutations stay in queue when online.

**Solutions:**
1. Check service worker is registered: `navigator.serviceWorker.controller`
2. Manually trigger sync: `syncPendingMutations()`
3. Check browser console for errors
4. Verify sync event is registered in service worker

### Authentication Errors (401)

**Problem:** Sync fails with 401 Unauthorized.

**Solutions:**
1. Ensure cookies are not expired
2. Check `credentials: 'include'` is set in fetch
3. Implement token refresh logic
4. Clear queue if session is invalid

### Duplicate Requests

**Problem:** Same mutation executed multiple times.

**Solutions:**
1. Implement idempotent API endpoints
2. Use request IDs
3. Check for duplicate entries before creating

## Browser Support

| Browser | Background Sync | Fallback |
|---------|----------------|----------|
| Chrome 49+ | ✅ Yes | - |
| Edge 79+ | ✅ Yes | - |
| Firefox | ⚠️ Flag required | Manual sync |
| Safari | ❌ No | Manual sync |
| Opera 36+ | ✅ Yes | - |

## Performance Tips

1. **Limit Queue Size:** Keep pending mutations under 100
2. **Compress Large Payloads:** Use gzip for requests >1KB
3. **Batch Similar Operations:** Group related mutations
4. **Clean Up Failed Mutations:** Remove old failed mutations periodically
5. **Monitor Storage:** Check IndexedDB size regularly

## Security Considerations

1. **Never Store Sensitive Data:** Passwords, credit cards, etc.
2. **Encrypt Payloads:** If needed, encrypt before storing
3. **Validate on Server:** Always validate mutations server-side
4. **Use HTTPS:** Required for service workers
5. **Implement CSRF Protection:** Use tokens for state-changing operations

## Next Steps

- Implement UI indicators for sync status
- Add conflict resolution logic
- Create admin panel to view failed mutations
- Set up monitoring/analytics for sync success rates
- Implement priority queue for critical mutations

## Resources

- [Background Sync API Spec](https://wicg.github.io/background-sync/spec/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [IndexedDB API](https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API)
