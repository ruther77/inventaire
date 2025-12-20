# Push Notifications for PWA - Complete Implementation

## Overview

This directory contains a complete implementation of Push Notifications for the Inventaire Épicerie PWA. The implementation allows users to receive real-time notifications even when the app is not open.

## What's Included

### ✅ Core Implementation
- Enhanced Service Worker with push event handlers
- React hook for managing push notifications (`usePushNotifications`)
- Ready-to-use UI components (compact & full variants)
- Complete error handling and state management

### ✅ Documentation
- Comprehensive implementation guide
- Quick start guide (5 minutes)
- Visual guide with component previews
- Integration examples
- Backend setup instructions (Node.js & Python)

### ✅ Testing & Examples
- Demo page with all features
- Multiple integration examples
- Test file template
- Real-world use cases

## Quick Start

### 1. Generate VAPID Keys (2 min)

```bash
npx web-push generate-vapid-keys
```

### 2. Update Frontend Config (1 min)

Edit `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/usePushNotifications.js`:

```javascript
const VAPID_PUBLIC_KEY = 'YOUR_PUBLIC_KEY_HERE';
```

### 3. Add to Your UI (1 min)

```jsx
import { NotificationPermissionButton } from '@/components/pwa';

function Settings() {
  return <NotificationPermissionButton variant="full" />;
}
```

### 4. Test (1 min)

1. Open the app
2. Click "Activer les notifications"
3. Accept permission
4. Click "Tester"

Done! 🎉

## File Structure

```
frontend/
├── public/
│   └── sw.js                                      ← Enhanced push handlers
├── src/
│   ├── hooks/
│   │   ├── usePushNotifications.js                ← Main hook
│   │   └── index.js                               ← Hook export
│   ├── components/
│   │   └── pwa/
│   │       ├── NotificationPermissionButton.jsx   ← UI component
│   │       ├── PushNotificationsDemo.jsx          ← Demo page
│   │       ├── NotificationPermissionButton.test.jsx  ← Tests
│   │       └── index.js                           ← Component exports
│   └── examples/
│       └── PushNotificationsExample.jsx           ← Integration examples
├── PUSH_NOTIFICATIONS_GUIDE.md                    ← Complete guide
├── PUSH_NOTIFICATIONS_QUICKSTART.md               ← 5-min setup
├── PUSH_NOTIFICATIONS_VISUAL_GUIDE.md             ← Visual examples
└── PUSH_NOTIFICATIONS_README.md                   ← This file
```

## Documentation Files

| File | Purpose | Read Time |
|------|---------|-----------|
| **QUICKSTART.md** | Get started in 5 minutes | 5 min |
| **GUIDE.md** | Complete reference with backend setup | 30 min |
| **VISUAL_GUIDE.md** | See what components look like | 10 min |
| **README.md** | This overview | 5 min |

## Features

### Frontend Hook (`usePushNotifications`)

```javascript
const {
  permission,        // 'default' | 'granted' | 'denied'
  isSubscribed,      // boolean
  isLoading,         // boolean
  error,             // Error | null
  subscribe,         // Subscribe to notifications
  unsubscribe,       // Unsubscribe
  sendTestNotification,  // Send test notification
} = usePushNotifications();
```

### UI Components

**Compact Variant** - For toolbars/navigation:
```jsx
<NotificationPermissionButton variant="compact" />
```

**Full Variant** - For settings pages:
```jsx
<NotificationPermissionButton 
  variant="full"
  onSubscriptionChange={(subscription) => {
    // Save to backend
  }}
/>
```

### Service Worker

Automatically handles:
- Push events from server
- Notification display
- Click handling
- URL navigation
- Window management

## Usage Examples

### Basic Settings Page

```jsx
import { NotificationPermissionButton } from '@/components/pwa';

function SettingsPage() {
  return (
    <div>
      <h2>Notifications</h2>
      <NotificationPermissionButton variant="full" />
    </div>
  );
}
```

### Custom Implementation

```jsx
import { usePushNotifications } from '@/hooks';

function CustomNotifications() {
  const { isSubscribed, subscribe, unsubscribe } = usePushNotifications();

  return (
    <button onClick={isSubscribed ? unsubscribe : subscribe}>
      {isSubscribed ? 'Disable' : 'Enable'} Notifications
    </button>
  );
}
```

### Save Subscription to Backend

```jsx
const handleSubscriptionChange = async (subscription) => {
  if (subscription) {
    await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(subscription),
    });
  }
};

<NotificationPermissionButton 
  onSubscriptionChange={handleSubscriptionChange}
/>
```

## Backend Integration (Optional)

### Node.js Example

```javascript
const webpush = require('web-push');

webpush.setVapidDetails(
  'mailto:your-email@example.com',
  process.env.VAPID_PUBLIC_KEY,
  process.env.VAPID_PRIVATE_KEY
);

// Send notification
await webpush.sendNotification(subscription, JSON.stringify({
  title: 'New Invoice',
  body: 'Invoice #12345 created',
  url: '/invoices/12345',
}));
```

### Python (FastAPI) Example

```python
from pywebpush import webpush

webpush(
    subscription_info=subscription,
    data=json.dumps({
        "title": "New Invoice",
        "body": "Invoice #12345 created",
        "url": "/invoices/12345"
    }),
    vapid_private_key=os.getenv("VAPID_PRIVATE_KEY"),
    vapid_claims={"sub": "mailto:your-email@example.com"}
)
```

## Browser Support

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome 42+ | ✅ Full | Best support |
| Firefox 44+ | ✅ Full | Full support |
| Safari 16+ | ✅ Limited | Requires PWA installation |
| Edge 17+ | ✅ Full | Chromium-based |
| Opera 29+ | ✅ Full | Chromium-based |

## Testing Checklist

- [ ] Generate VAPID keys
- [ ] Update public key in code
- [ ] Test permission request
- [ ] Test subscription
- [ ] Test local test notification
- [ ] Test unsubscribe
- [ ] Test on mobile device
- [ ] Test notification click navigation
- [ ] Backend: Save subscription
- [ ] Backend: Send notification
- [ ] Backend: Handle expired subscriptions

## Common Issues

### Permission Denied
**Solution**: User must enable in browser settings manually.

### Notifications Not Showing
**Check**:
1. System notifications enabled?
2. Service Worker active?
3. Console for errors?

### iOS Not Working
**Requirements**:
1. App must be installed (added to home screen)
2. iOS 16.4+ required
3. System notifications enabled

## Next Steps

1. **Now**: Configure VAPID keys and test frontend
2. **Soon**: Implement backend subscription storage
3. **Later**: Add notification preferences, scheduling, analytics

## Resources

- [Web Push API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [web-push npm package](https://www.npmjs.com/package/web-push)
- [Service Worker Cookbook](https://serviceworke.rs/)

## Support

For detailed information:
1. Read `PUSH_NOTIFICATIONS_QUICKSTART.md` for setup
2. Read `PUSH_NOTIFICATIONS_GUIDE.md` for complete reference
3. Check examples in `src/examples/PushNotificationsExample.jsx`
4. View demo at `src/components/pwa/PushNotificationsDemo.jsx`

---

**Implementation Status**: ✅ Complete - Ready to use

**Last Updated**: 2025-12-17
