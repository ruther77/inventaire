# Push Notifications - Quick Start

Guide rapide pour mettre en place les notifications push en 5 minutes.

## Étape 1: Générer les clés VAPID (2 min)

```bash
# Installer web-push
npm install web-push --save-dev

# Générer les clés
npx web-push generate-vapid-keys
```

Vous obtiendrez :
```
Public Key: BEl62iUYgUivxIkv...
Private Key: p6YVD7fXGFg8hNb3...
```

## Étape 2: Configurer le frontend (1 min)

Ouvrir `/home/ruuuzer/Documents/monprojet/frontend/src/hooks/usePushNotifications.js` :

```javascript
// Ligne ~46, remplacer par votre clé publique
const VAPID_PUBLIC_KEY = 'VOTRE_CLE_PUBLIQUE_ICI';
```

## Étape 3: Ajouter le bouton dans votre UI (1 min)

```jsx
import { NotificationPermissionButton } from '@/components/pwa';

function MyPage() {
  return (
    <div>
      <h1>Mes Paramètres</h1>

      {/* Variante complète pour page de paramètres */}
      <NotificationPermissionButton variant="full" />

      {/* OU variante compacte pour toolbar */}
      <NotificationPermissionButton variant="compact" />
    </div>
  );
}
```

## Étape 4: Tester (1 min)

1. Ouvrez l'application dans votre navigateur
2. Cliquez sur "Activer les notifications"
3. Acceptez la permission
4. Cliquez sur "Tester" pour envoyer une notification de test

C'est tout ! Les notifications fonctionnent côté client.

## Étape 5 (Optionnel): Configurer le backend

Pour envoyer des notifications depuis le backend, voir le guide complet : `PUSH_NOTIFICATIONS_GUIDE.md`

### Exemple minimal Node.js

```javascript
const webpush = require('web-push');

webpush.setVapidDetails(
  'mailto:your-email@example.com',
  'VOTRE_CLE_PUBLIQUE',
  'VOTRE_CLE_PRIVEE'
);

// Envoyer une notification
await webpush.sendNotification(
  subscription, // Reçu du frontend
  JSON.stringify({
    title: 'Test',
    body: 'Notification de test',
    url: '/',
  })
);
```

## Démo complète

Pour voir une démonstration complète avec tous les cas d'usage :

```jsx
import { PushNotificationsDemo } from '@/components/pwa';

function DemoPage() {
  return <PushNotificationsDemo />;
}
```

## Ressources

- Guide complet: `/frontend/PUSH_NOTIFICATIONS_GUIDE.md`
- Code source du hook: `/frontend/src/hooks/usePushNotifications.js`
- Code source du composant: `/frontend/src/components/pwa/NotificationPermissionButton.jsx`
- Service Worker: `/frontend/public/sw.js`
