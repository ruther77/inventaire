# Guide des Notifications Push PWA

Ce guide explique comment utiliser les notifications push dans l'application PWA Inventaire Épicerie.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Installation et configuration](#installation-et-configuration)
4. [Utilisation](#utilisation)
5. [API de référence](#api-de-référence)
6. [Backend](#backend)
7. [Exemples](#exemples)
8. [Dépannage](#dépannage)

## Vue d'ensemble

Les notifications push permettent d'envoyer des messages aux utilisateurs même lorsque l'application n'est pas ouverte. Cette fonctionnalité est particulièrement utile pour :

- Alerter sur des anomalies financières
- Notifier de nouvelles factures
- Rappeler des tâches en attente
- Signaler des problèmes de stock
- Envoyer des rappels personnalisés

## Architecture

### Composants

```
frontend/
├── public/
│   └── sw.js                          # Service Worker avec gestionnaires push
├── src/
    ├── hooks/
    │   ├── usePushNotifications.js    # Hook pour gérer les notifications push
    │   └── index.js                   # Export du hook
    └── components/
        └── pwa/
            ├── NotificationPermissionButton.jsx  # Composant UI pour permissions
            ├── PushNotificationsDemo.jsx         # Démonstration complète
            └── index.js                          # Exports des composants PWA
```

### Flux de données

```
1. Utilisateur → Demande de permission
2. Navigateur → Affiche le prompt natif
3. Utilisateur → Accepte/refuse
4. Service Worker → Souscrit au service push
5. Backend → Reçoit les informations de souscription
6. Backend → Envoie une notification push
7. Service Worker → Reçoit la notification
8. Service Worker → Affiche la notification
9. Utilisateur → Clique sur la notification
10. Application → S'ouvre et navigue vers la page appropriée
```

## Installation et configuration

### 1. Générer les clés VAPID

Les clés VAPID (Voluntary Application Server Identification) sont nécessaires pour l'authentification des notifications push.

```bash
# Installer web-push en dépendance de développement
npm install web-push --save-dev

# Générer les clés VAPID
npx web-push generate-vapid-keys
```

Vous obtiendrez quelque chose comme :

```
=======================================

Public Key:
BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U

Private Key:
p6YVD7fXGFg8hNb3bVqNz_QN3xS7dK4mN1qW9pR2tYc

=======================================
```

### 2. Configurer la clé publique

Ouvrez `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/usePushNotifications.js` et remplacez la clé VAPID_PUBLIC_KEY par votre clé publique :

```javascript
const VAPID_PUBLIC_KEY = 'VOTRE_CLE_PUBLIQUE_ICI';
```

### 3. Configurer les variables d'environnement backend

Créez ou mettez à jour votre fichier `.env` côté backend :

```env
VAPID_PUBLIC_KEY=BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U
VAPID_PRIVATE_KEY=p6YVD7fXGFg8hNb3bVqNz_QN3xS7dK4mN1qW9pR2tYc
VAPID_EMAIL=mailto:votre-email@example.com
```

## Utilisation

### Option 1: Utiliser le composant NotificationPermissionButton

#### Variante compacte (pour les barres d'outils)

```jsx
import { NotificationPermissionButton } from '@/components/pwa';

function Toolbar() {
  const handleSubscriptionChange = (subscription) => {
    if (subscription) {
      // Envoyer au backend
      fetch('/api/push/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(subscription),
      });
    }
  };

  return (
    <div className="toolbar">
      <NotificationPermissionButton
        variant="compact"
        onSubscriptionChange={handleSubscriptionChange}
      />
    </div>
  );
}
```

#### Variante complète (pour les pages de paramètres)

```jsx
import { NotificationPermissionButton } from '@/components/pwa';

function SettingsPage() {
  return (
    <div className="settings">
      <h2>Notifications</h2>
      <NotificationPermissionButton
        variant="full"
        onSubscriptionChange={(subscription) => {
          console.log('Nouvelle souscription:', subscription);
        }}
      />
    </div>
  );
}
```

### Option 2: Utiliser directement le hook

```jsx
import { usePushNotifications } from '@/hooks';

function MyComponent() {
  const {
    permission,
    isSubscribed,
    isLoading,
    subscribe,
    unsubscribe,
    sendTestNotification,
  } = usePushNotifications();

  const handleSubscribe = async () => {
    const result = await subscribe();

    if (result.success) {
      // Envoyer au backend
      await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result.subscription),
      });

      console.log('Souscrit avec succès!');
    } else {
      console.error('Échec de la souscription:', result.error);
    }
  };

  return (
    <div>
      <p>Permission: {permission}</p>
      <p>Souscrit: {isSubscribed ? 'Oui' : 'Non'}</p>

      {!isSubscribed && (
        <button onClick={handleSubscribe} disabled={isLoading}>
          Activer les notifications
        </button>
      )}

      {isSubscribed && (
        <>
          <button onClick={unsubscribe} disabled={isLoading}>
            Désactiver les notifications
          </button>
          <button onClick={sendTestNotification}>
            Tester
          </button>
        </>
      )}
    </div>
  );
}
```

## API de référence

### Hook `usePushNotifications`

#### États retournés

```typescript
{
  // États
  permission: 'default' | 'granted' | 'denied' | 'unsupported',
  subscription: PushSubscription | null,
  isLoading: boolean,
  error: Error | null,
  isSupported: boolean,
  isSubscribed: boolean,

  // Méthodes
  requestPermission: () => Promise<{success: boolean, permission: string}>,
  subscribe: () => Promise<{success: boolean, subscription?: object, error?: string}>,
  unsubscribe: () => Promise<{success: boolean, error?: string}>,
  sendTestNotification: () => Promise<{success: boolean, error?: string}>,
  getSubscriptionInfo: () => {endpoint: string, keys: object, expirationTime: number} | null,
  urlBase64ToUint8Array: (base64: string) => Uint8Array,
}
```

#### Méthodes

**`requestPermission()`**
- Demande la permission pour les notifications
- Retourne: `{success: boolean, permission: string}`

**`subscribe()`**
- Souscrit aux notifications push
- Demande automatiquement la permission si nécessaire
- Retourne: `{success: boolean, subscription?: object, error?: string}`

**`unsubscribe()`**
- Se désabonne des notifications push
- Retourne: `{success: boolean, error?: string}`

**`sendTestNotification()`**
- Envoie une notification de test locale (ne passe pas par le backend)
- Retourne: `{success: boolean, error?: string}`

**`getSubscriptionInfo()`**
- Récupère les informations de la souscription actuelle
- Retourne: Objet avec endpoint, keys, et expirationTime ou null

### Composant `NotificationPermissionButton`

#### Props

```typescript
{
  variant?: 'compact' | 'full',           // Type d'affichage (défaut: 'full')
  onSubscriptionChange?: (subscription: object | null) => void,  // Callback lors de changement
  className?: string,                     // Classes CSS additionnelles
}
```

## Backend

### Configuration Node.js avec web-push

#### 1. Installer les dépendances

```bash
npm install web-push
```

#### 2. Configurer web-push

```javascript
const webpush = require('web-push');

webpush.setVapidDetails(
  process.env.VAPID_EMAIL,
  process.env.VAPID_PUBLIC_KEY,
  process.env.VAPID_PRIVATE_KEY
);
```

#### 3. Endpoint pour sauvegarder la souscription

```javascript
// POST /api/push/subscribe
app.post('/api/push/subscribe', async (req, res) => {
  try {
    const subscription = req.body;
    const userId = req.user.id; // Récupéré depuis l'auth

    // Sauvegarder en base de données
    await db.query(
      'INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth) VALUES ($1, $2, $3, $4) ON CONFLICT (user_id, endpoint) DO UPDATE SET p256dh = $3, auth = $4',
      [
        userId,
        subscription.endpoint,
        subscription.keys.p256dh,
        subscription.keys.auth
      ]
    );

    res.json({ success: true });
  } catch (error) {
    console.error('Erreur lors de la sauvegarde de la souscription:', error);
    res.status(500).json({ error: error.message });
  }
});
```

#### 4. Fonction pour envoyer une notification

```javascript
async function sendPushNotification(userId, notificationData) {
  try {
    // Récupérer les souscriptions de l'utilisateur
    const subscriptions = await db.query(
      'SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = $1',
      [userId]
    );

    // Payload de la notification
    const payload = JSON.stringify({
      title: notificationData.title,
      body: notificationData.body,
      icon: '/icon-192.png',
      badge: '/icon-192.png',
      url: notificationData.url || '/',
      tag: notificationData.tag || 'default',
      data: notificationData.data || {},
    });

    // Envoyer à toutes les souscriptions de l'utilisateur
    const promises = subscriptions.rows.map(async (sub) => {
      const pushSubscription = {
        endpoint: sub.endpoint,
        keys: {
          p256dh: sub.p256dh,
          auth: sub.auth,
        },
      };

      try {
        await webpush.sendNotification(pushSubscription, payload);
        console.log('Notification envoyée:', sub.endpoint);
      } catch (error) {
        if (error.statusCode === 410) {
          // Souscription expirée, la supprimer
          await db.query(
            'DELETE FROM push_subscriptions WHERE endpoint = $1',
            [sub.endpoint]
          );
          console.log('Souscription expirée supprimée:', sub.endpoint);
        } else {
          console.error('Erreur lors de l\'envoi:', error);
        }
      }
    });

    await Promise.all(promises);
    return { success: true };
  } catch (error) {
    console.error('Erreur lors de l\'envoi des notifications:', error);
    return { success: false, error: error.message };
  }
}
```

#### 5. Exemples d'utilisation

```javascript
// Notifier une nouvelle facture
await sendPushNotification(userId, {
  title: 'Nouvelle facture',
  body: 'Facture #12345 de 150.00€',
  url: '/invoices/12345',
  tag: 'invoice-12345',
  data: {
    type: 'invoice',
    invoiceId: '12345',
  },
});

// Notifier une anomalie
await sendPushNotification(userId, {
  title: 'Anomalie détectée',
  body: 'Transaction suspecte de 500.00€',
  url: '/intelligence/anomalies',
  tag: 'anomaly-alert',
  requireInteraction: true,
  data: {
    type: 'anomaly',
    severity: 'high',
  },
});

// Notifier un stock faible
await sendPushNotification(userId, {
  title: 'Stock faible',
  body: 'Tomates: seulement 5 unités restantes',
  url: '/restaurant/ingredients',
  tag: 'low-stock',
  data: {
    type: 'inventory',
    ingredientId: '789',
  },
});
```

### Configuration Python (FastAPI)

#### 1. Installer les dépendances

```bash
pip install pywebpush
```

#### 2. Endpoint pour sauvegarder la souscription

```python
from fastapi import APIRouter, Depends, HTTPException
from pywebpush import webpush, WebPushException
from pydantic import BaseModel
import json
import os

router = APIRouter()

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict

@router.post("/api/push/subscribe")
async def subscribe_push(
    subscription: PushSubscription,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    try:
        # Sauvegarder en base de données
        query = """
        INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id, endpoint)
        DO UPDATE SET p256dh = $3, auth = $4
        """
        await db.execute(
            query,
            current_user.id,
            subscription.endpoint,
            subscription.keys['p256dh'],
            subscription.keys['auth']
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 3. Fonction pour envoyer une notification

```python
async def send_push_notification(user_id: int, notification_data: dict):
    try:
        # Récupérer les souscriptions
        query = "SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = $1"
        subscriptions = await db.fetch_all(query, user_id)

        # Payload
        payload = json.dumps({
            "title": notification_data.get("title"),
            "body": notification_data.get("body"),
            "icon": "/icon-192.png",
            "url": notification_data.get("url", "/"),
            "tag": notification_data.get("tag", "default"),
            "data": notification_data.get("data", {}),
        })

        # VAPID claims
        vapid_claims = {
            "sub": os.getenv("VAPID_EMAIL")
        }

        vapid_private_key = os.getenv("VAPID_PRIVATE_KEY")

        # Envoyer à toutes les souscriptions
        for sub in subscriptions:
            subscription_info = {
                "endpoint": sub["endpoint"],
                "keys": {
                    "p256dh": sub["p256dh"],
                    "auth": sub["auth"]
                }
            }

            try:
                webpush(
                    subscription_info=subscription_info,
                    data=payload,
                    vapid_private_key=vapid_private_key,
                    vapid_claims=vapid_claims
                )
            except WebPushException as e:
                if e.response.status_code == 410:
                    # Souscription expirée
                    delete_query = "DELETE FROM push_subscriptions WHERE endpoint = $1"
                    await db.execute(delete_query, sub["endpoint"])
                else:
                    print(f"Erreur push: {e}")

        return {"success": True}
    except Exception as e:
        print(f"Erreur notification: {e}")
        return {"success": False, "error": str(e)}
```

## Exemples

### Exemple 1: Notification simple

```javascript
await sendPushNotification(userId, {
  title: 'Bonjour!',
  body: 'Ceci est une notification simple',
});
```

### Exemple 2: Notification avec URL

```javascript
await sendPushNotification(userId, {
  title: 'Nouvelle facture',
  body: 'Facture #12345 créée',
  url: '/invoices/12345',
});
```

### Exemple 3: Notification avec actions

```javascript
const payload = JSON.stringify({
  title: 'Confirmer la livraison',
  body: 'Livraison de 10 unités de tomates',
  url: '/deliveries/123',
  actions: [
    {
      action: 'confirm',
      title: 'Confirmer',
      icon: '/icon-confirm.png'
    },
    {
      action: 'reject',
      title: 'Rejeter',
      icon: '/icon-reject.png'
    }
  ],
  data: {
    deliveryId: '123',
  }
});
```

### Exemple 4: Notification avec image

```javascript
await sendPushNotification(userId, {
  title: 'Nouveau plat ajouté',
  body: 'Salade César disponible',
  image: '/images/caesar-salad.jpg',
  url: '/restaurant/plats',
});
```

## Dépannage

### La permission est refusée

Si l'utilisateur a refusé la permission, il doit la réactiver manuellement dans les paramètres du navigateur :

**Chrome:**
1. Cliquer sur l'icône de cadenas dans la barre d'adresse
2. Paramètres du site → Notifications → Autoriser

**Firefox:**
1. Cliquer sur l'icône d'information dans la barre d'adresse
2. Autorisations → Notifications → Autoriser

**Safari:**
1. Safari → Préférences → Sites web → Notifications
2. Trouver le site et autoriser

### Les notifications ne s'affichent pas

1. Vérifiez que les notifications sont activées au niveau du système d'exploitation
2. Vérifiez que le Service Worker est actif (DevTools → Application → Service Workers)
3. Vérifiez la console pour les erreurs
4. Testez avec `sendTestNotification()`

### Les souscriptions expirent

Les souscriptions push peuvent expirer. Le backend doit gérer les erreurs 410 (Gone) et supprimer les souscriptions expirées de la base de données.

### VAPID : clé invalide

Assurez-vous que :
1. La clé publique dans le frontend correspond à la clé privée dans le backend
2. Les clés sont au bon format (base64 URL-safe)
3. L'email VAPID est au format `mailto:email@example.com`

### Notifications non reçues sur iOS

Les notifications push sur iOS nécessitent que l'application soit ajoutée à l'écran d'accueil. Assurez-vous que :
1. L'application est installée (ajoutée à l'écran d'accueil)
2. Les notifications sont activées dans les paramètres iOS
3. Le mode Ne pas déranger est désactivé

## Ressources

- [Push API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Push_API)
- [Notifications API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API)
- [Web Push Protocol](https://datatracker.ietf.org/doc/html/rfc8030)
- [web-push (npm)](https://www.npmjs.com/package/web-push)
- [pywebpush (PyPI)](https://pypi.org/project/pywebpush/)
