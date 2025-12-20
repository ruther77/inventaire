# Background Sync Implementation

## Overview

This document describes the Background Sync functionality implemented in the PWA service worker. Background Sync allows offline mutations to be automatically synchronized with the server when the network connection is restored.

## Implementation Details

### Location
- **File**: `/home/ruuuzer/Documents/monprojet/frontend/public/sw.js`
- **Function**: `syncData()`

### Architecture

#### 1. Sync Event Handler (Lines 252-258)
```javascript
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);

  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});
```

The service worker listens for the `sync` event with the tag `sync-data` and triggers the synchronization process.

#### 2. Main Sync Function: `syncData()` (Lines 264-388)

**Key Features:**

- **Database Access**: Opens IndexedDB and retrieves pending mutations
- **Mutation Processing**: Iterates through each pending mutation in order (oldest first)
- **Retry Logic**: Implements exponential backoff with configurable max retries
- **Status Management**: Updates mutation status (pending → processing → completed/failed)
- **Client Notification**: Sends messages to active clients about sync results

**Flow:**
1. Open IndexedDB connection
2. Retrieve all pending mutations (status = 'pending')
3. For each mutation:
   - Check if max retries exceeded (default: 5)
   - Calculate retry delay with exponential backoff
   - Skip if retry delay not elapsed
   - Mark as 'processing'
   - Execute HTTP request with proper headers and credentials
   - On success: Delete mutation and notify clients
   - On failure: Mark as 'failed', increment attempts, notify clients
4. Close database connection
5. Log summary (success/failure counts)
6. Throw error if all mutations failed (triggers automatic retry by browser)

### Helper Functions

#### `openIndexedDB()` (Lines 394-408)
Opens the IndexedDB database `inventaire-offline`.

#### `getPendingMutationsFromDB(db)` (Lines 415-437)
Retrieves all mutations with status='pending', sorted by timestamp (oldest first).

#### `updateMutationStatusInDB(db, id, status, error)` (Lines 447-483)
Updates the status of a mutation and increments the attempts counter.

#### `deleteMutationFromDB(db, id)` (Lines 491-504)
Removes a successfully synchronized mutation from IndexedDB.

#### `calculateRetryDelay(attempts)` (Lines 511-521)
**Exponential Backoff Strategy:**
- Base delay: 1 second
- Max delay: 30 seconds
- Formula: `min(1000 * 2^attempts, 30000) + jitter`
- Jitter: Random 0-1000ms to avoid thundering herd

**Retry Schedule:**
- Attempt 0: ~1s
- Attempt 1: ~2s
- Attempt 2: ~4s
- Attempt 3: ~8s
- Attempt 4: ~16s
- Attempt 5+: ~30s

#### `notifyClients(message)` (Lines 528-541)
Sends messages to all connected browser tabs/windows.

**Message Types:**
- `SYNC_SUCCESS`: Mutation synchronized successfully
- `SYNC_ERROR`: Mutation failed to synchronize

## Integration with Existing Code

### IndexedDB Structure
The implementation uses the existing IndexedDB structure defined in:
- **File**: `/home/ruuuzer/Documents/monprojet/frontend/src/services/offlineStorage.js`
- **Database**: `inventaire-offline`
- **Store**: `mutations`

**Mutation Object Structure:**
```javascript
{
  id: number,              // Auto-increment primary key
  type: string,            // CREATE, UPDATE, DELETE
  endpoint: string,        // API endpoint (e.g., '/products')
  method: string,          // HTTP method (POST, PUT, PATCH, DELETE)
  payload: object,         // Request body
  metadata: object,        // Additional data (callbacks, etc.)
  timestamp: number,       // Creation timestamp
  status: string,          // pending, processing, completed, failed
  attempts: number,        // Retry attempt counter
  lastAttempt: number,     // Last attempt timestamp
  error: string,           // Error message if failed
  createdAt: string        // ISO date string
}
```

### OfflineContext Integration
The Background Sync works in conjunction with:
- **File**: `/home/ruuuzer/Documents/monprojet/frontend/src/contexts/OfflineContext.jsx`
- **Hook**: `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useOfflineMutation.js`

**Flow:**
1. User performs action while offline
2. `useOfflineMutation` hook detects offline state
3. Mutation queued in IndexedDB via `queueMutation()`
4. Browser registers sync event when online
5. Service worker's `syncData()` executes mutations
6. OfflineContext receives notifications and updates UI

## HTTP Request Configuration

### Headers
```javascript
{
  'Content-Type': 'application/json'
}
```

### Credentials
```javascript
credentials: 'include'  // Sends HTTP-Only cookies for authentication
```

### URL Construction
```javascript
const baseURL = self.location.origin;
const apiPath = mutation.endpoint.startsWith('/') ? mutation.endpoint : `/${mutation.endpoint}`;
const fullURL = `${baseURL}/api${apiPath}`;
```

Example: `https://example.com/api/products`

## Error Handling

### Max Retries
- Default: 5 attempts
- After 5 failed attempts, mutation is marked as 'failed' and no longer retried
- Failed mutations remain in IndexedDB for manual inspection/cleanup

### Error Propagation
- If **all** mutations fail, an error is thrown to trigger browser's automatic retry
- If **some** mutations succeed, no error is thrown (partial success)

### Network Errors
Common scenarios handled:
- 401 Unauthorized: Likely session expired
- 403 Forbidden: Permission denied
- 404 Not Found: Endpoint doesn't exist
- 500 Server Error: Backend issue
- Network timeout
- DNS resolution failure

## Client Notifications

### Success Notification
```javascript
{
  type: 'SYNC_SUCCESS',
  mutationId: number,
  mutationType: string  // CREATE, UPDATE, DELETE
}
```

### Error Notification
```javascript
{
  type: 'SYNC_ERROR',
  mutationId: number,
  mutationType: string,
  error: string  // Error message
}
```

## Testing the Implementation

### Manual Testing

1. **Setup:**
   ```bash
   cd /home/ruuuzer/Documents/monprojet/frontend
   npm run dev
   ```

2. **Test Offline Mutation:**
   - Open DevTools → Application → Service Workers
   - Check "Offline" to simulate offline mode
   - Perform a mutation (create, update, delete)
   - Verify mutation queued in IndexedDB (Application → IndexedDB → inventaire-offline → mutations)

3. **Test Sync:**
   - Uncheck "Offline" to go back online
   - In Service Workers panel, click "Sync" or wait for automatic sync
   - Check Console for sync logs
   - Verify mutations disappear from IndexedDB
   - Verify server received the mutations

### Console Logs to Watch

```
[SW] Background sync: sync-data
[SW] Synchronisation des données en arrière-plan
[SW] 3 mutation(s) à synchroniser
[SW] Envoi de la mutation 1: POST https://example.com/api/products
[SW] Mutation 1 synchronisée avec succès
[SW] Envoi de la mutation 2: PUT https://example.com/api/products/123
[SW] Mutation 2 synchronisée avec succès
[SW] Envoi de la mutation 3: DELETE https://example.com/api/products/456
[SW] Mutation 3 synchronisée avec succès
[SW] Synchronisation terminée: 3 réussie(s), 0 échouée(s)
```

## Browser Compatibility

Background Sync API is supported in:
- Chrome/Edge 49+
- Opera 36+
- Firefox (behind flag)
- Safari (not supported)

For unsupported browsers, the app falls back to:
- Immediate sync when connection detected (via OfflineContext)
- Manual sync trigger in UI

## Performance Considerations

### Batch Processing
- Mutations are processed sequentially to maintain order
- Consider batching similar mutations in future optimization

### Network Usage
- Each mutation = 1 HTTP request
- Large payloads may take time on slow connections
- Consider compression for large payloads

### Battery Impact
- Background Sync is battery-friendly
- Browser controls when to run sync (may delay on low battery)

## Security Considerations

1. **Authentication**: Uses HTTP-Only cookies (more secure than localStorage)
2. **CSRF Protection**: Cookies automatically include CSRF tokens
3. **Payload Validation**: Server should validate all mutations
4. **Idempotency**: Mutations should be idempotent (safe to retry)

## Future Enhancements

1. **Batch API**: Group similar mutations into single request
2. **Conflict Resolution**: Handle server-side conflicts (e.g., optimistic locking)
3. **Priority Queue**: High-priority mutations sync first
4. **Size Limits**: Prevent IndexedDB from growing too large
5. **Analytics**: Track sync success/failure rates
6. **User Notification**: Toast/banner showing sync progress

## Troubleshooting

### Sync Not Triggering
- Check service worker registration
- Verify sync event listener is active
- Check browser console for errors
- Ensure mutations in IndexedDB have status='pending'

### Mutations Failing
- Check network connectivity
- Verify API endpoints are correct
- Check authentication status (cookies valid)
- Review server logs for errors
- Check mutation payload format

### Performance Issues
- Too many pending mutations (>100)
- Large payload sizes (>1MB)
- Slow network connection
- Server processing delays

## Related Files

- `/home/ruuuzer/Documents/monprojet/frontend/public/sw.js` - Service Worker
- `/home/ruuuzer/Documents/monprojet/frontend/src/services/offlineStorage.js` - IndexedDB utilities
- `/home/ruuuzer/Documents/monprojet/frontend/src/contexts/OfflineContext.jsx` - Offline state management
- `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/useOfflineMutation.js` - Offline mutation hook
- `/home/ruuuzer/Documents/monprojet/frontend/src/api/client.js` - API client configuration

## Support

For issues or questions about the Background Sync implementation, check:
1. Browser console for service worker logs
2. DevTools → Application → IndexedDB for mutation queue
3. Network tab for failed requests
4. Server logs for backend errors
