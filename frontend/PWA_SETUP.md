# PWA Setup - Inventaire Épicerie

## Vue d'ensemble

L'application Inventaire Épicerie est maintenant une Progressive Web App (PWA) complète, permettant :
- Installation sur mobile et desktop
- Fonctionnement offline
- Mise en cache intelligente des ressources
- Notifications push (préparé)
- Partage de fichiers
- Expérience native

## Fichiers créés

### 1. Manifest PWA
**Fichier:** `/frontend/public/manifest.json`

Configuration complète du PWA avec :
- Métadonnées de l'application (nom, description, icônes)
- Configuration d'affichage (standalone, theme color)
- Catégories et raccourcis
- Support du partage de fichiers (Share Target API)

### 2. Service Worker
**Fichier:** `/frontend/public/sw.js`

Service Worker avec stratégies de cache :
- **Cache-first** pour les assets statiques (JS, CSS, images)
- **Network-first** pour les appels API (avec fallback cache)
- **Navigation handler** pour le routing SPA
- Support des mises à jour automatiques
- Gestion des notifications push
- Background sync

### 3. Hook usePWA
**Fichier:** `/frontend/src/hooks/usePWA.js`

Hook React pour gérer le PWA :
```javascript
const {
  // États
  isInstallable,      // L'app peut être installée
  isInstalled,        // L'app est déjà installée
  isStandalone,       // L'app est en mode standalone
  updateAvailable,    // Une mise à jour est disponible
  isPWASupported,     // Le navigateur supporte les PWA

  // Actions
  promptInstall,      // Affiche le prompt d'installation
  activateUpdate,     // Active une mise à jour disponible
  share,              // Partage du contenu (Web Share API)

  // Informations
  getDeviceCapabilities, // Obtient les capacités de l'appareil
} = usePWA();
```

### 4. Composant d'installation
**Fichier:** `/frontend/src/components/pwa/InstallPWAButton.jsx`

Composants pour promouvoir l'installation :
- `<InstallPWAButton variant="banner|button|floating" />` - Bouton d'installation
- `<InstalledPWABadge />` - Badge "Application installée"
- `<StandaloneIndicator />` - Indicateur mode PWA

### 5. Icônes
**Fichiers:** `/frontend/public/icon-192.png` et `/frontend/public/icon-512.png`

Icônes SVG placeholders avec design moderne :
- Dégradé bleu (brand colors)
- Icône de panier avec checkmark
- Format PNG pour compatibilité maximale

### 6. Index HTML mis à jour
**Fichier:** `/frontend/index.html`

Ajouts :
- Lien vers manifest.json
- Meta tags PWA (theme-color, apple-mobile-web-app-capable, etc.)
- Viewport optimisé pour mobile
- Support iOS et Android
- Meta tags SEO

### 7. Enregistrement du Service Worker
**Fichier:** `/frontend/src/main.jsx`

Le Service Worker est automatiquement enregistré au démarrage de l'application.

## Utilisation

### Installation de l'app

#### Sur mobile (iOS/Android)
1. Ouvrir l'app dans le navigateur
2. Un banner "Installer l'application" apparaît automatiquement
3. Cliquer sur "Installer"
4. L'icône est ajoutée à l'écran d'accueil

**Alternative iOS:** Partager > Ajouter à l'écran d'accueil

#### Sur desktop (Chrome, Edge)
1. Une icône d'installation apparaît dans la barre d'adresse
2. Cliquer sur l'icône ou le banner
3. Confirmer l'installation
4. L'app s'ouvre dans une fenêtre dédiée

### Composant d'installation personnalisé

```jsx
import { InstallPWAButton } from '@/components/pwa/InstallPWAButton';

function MyComponent() {
  return (
    <div>
      {/* Banner en bas de l'écran */}
      <InstallPWAButton
        variant="banner"
        onInstall={() => console.log('App installée!')}
        onDismiss={() => console.log('Banner fermé')}
      />

      {/* Bouton simple */}
      <InstallPWAButton variant="button" />

      {/* Bouton flottant */}
      <InstallPWAButton variant="floating" />
    </div>
  );
}
```

### Utilisation du hook usePWA

```jsx
import { usePWA } from '@/hooks/usePWA';

function MyComponent() {
  const {
    isInstallable,
    isStandalone,
    promptInstall,
    share,
    getDeviceCapabilities,
  } = usePWA();

  const handleInstall = async () => {
    const result = await promptInstall();
    if (result.outcome === 'accepted') {
      console.log('User accepted installation');
    }
  };

  const handleShare = async () => {
    await share({
      title: 'Inventaire Épicerie',
      text: 'Découvrez cette app de gestion!',
      url: window.location.href,
    });
  };

  const capabilities = getDeviceCapabilities();
  console.log('Device capabilities:', capabilities);

  return (
    <div>
      {isInstallable && (
        <button onClick={handleInstall}>
          Installer l'application
        </button>
      )}

      {isStandalone && (
        <p>Application en mode PWA</p>
      )}

      <button onClick={handleShare}>
        Partager
      </button>
    </div>
  );
}
```

### Gestion du mode offline

Le contexte `OfflineContext` (déjà existant) gère automatiquement :
- Détection online/offline
- Queue de mutations en attente
- Synchronisation automatique au retour de connexion
- Cache des données essentielles

```jsx
import { useOfflineContext } from '@/contexts/OfflineContext';

function MyComponent() {
  const {
    isOnline,
    pendingMutations,
    syncPendingMutations,
    isSyncing,
  } = useOfflineContext();

  return (
    <div>
      {!isOnline && (
        <div className="offline-banner">
          Mode hors ligne - {pendingMutations.length} actions en attente
        </div>
      )}

      {pendingMutations.length > 0 && (
        <button
          onClick={syncPendingMutations}
          disabled={isSyncing}
        >
          {isSyncing ? 'Synchronisation...' : 'Synchroniser maintenant'}
        </button>
      )}
    </div>
  );
}
```

## Stratégies de cache

### Cache-First (Assets statiques)
- Fichiers JS, CSS, fonts, images
- Cherche d'abord dans le cache
- Réseau en fallback
- Mise à jour du cache en arrière-plan

### Network-First (API)
- Appels API
- Essaie le réseau d'abord
- Cache en fallback si offline
- Garantit les données fraîches quand online

### Navigation Handler
- Routes de l'application
- Network-first avec fallback vers index.html
- Support du routing côté client (React Router)

## Mises à jour

Le Service Worker vérifie automatiquement les mises à jour :
- À chaque chargement de l'application
- Toutes les heures en arrière-plan
- Affiche un prompt de confirmation avant mise à jour

Pour forcer la vérification :
```javascript
const { activateUpdate } = usePWA();
activateUpdate();
```

## Configuration Vite

Le fichier `vite.config.js` doit copier les fichiers du dossier `public` :

```javascript
export default defineConfig({
  publicDir: 'public', // Par défaut dans Vite
  build: {
    rollupOptions: {
      // Le manifest.json et sw.js seront automatiquement copiés
    }
  }
});
```

## Test en local

### Développement
```bash
npm run dev
```

Le Service Worker fonctionne en mode développement.
Pour le désactiver temporairement, décommenter dans `main.jsx` :
```javascript
if (import.meta.env.DEV) {
  console.log('[PWA] Service Worker disabled in development mode');
  return null;
}
```

### Production
```bash
npm run build
npm run preview
```

### Test HTTPS en local
Le PWA nécessite HTTPS (sauf localhost). Pour tester avec HTTPS :

```bash
# Installer mkcert
npm install -g mkcert

# Créer un certificat local
mkcert -install
mkcert localhost

# Vite avec HTTPS
npm run dev -- --host --https
```

## Débogage

### Chrome DevTools
1. Ouvrir DevTools (F12)
2. Onglet "Application"
3. Sections :
   - **Manifest** : Voir le manifest.json et tester l'installation
   - **Service Workers** : État, mises à jour, désinstallation
   - **Cache Storage** : Contenu des caches
   - **IndexedDB** : Mutations en attente (via OfflineContext)

### Commandes utiles

```javascript
// Désinstaller le SW
const { unregister } = usePWA();
await unregister();

// Vider tous les caches
const { clearCaches } = usePWA();
await clearCaches();

// Obtenir les infos de cache
const { getCacheInfo } = usePWA();
const info = await getCacheInfo();
console.log(info);
```

### DevTools - Lighthouse
1. DevTools > Lighthouse
2. Sélectionner "Progressive Web App"
3. Générer le rapport
4. Score PWA et recommandations

## Déploiement

### Prérequis
- HTTPS obligatoire (Let's Encrypt, Cloudflare, etc.)
- Serveur doit servir le manifest.json avec le bon Content-Type
- Headers de cache appropriés

### Nginx (exemple)
```nginx
location / {
  root /var/www/inventaire;
  try_files $uri $uri/ /index.html;

  # Cache des assets
  location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }

  # Pas de cache pour HTML et manifest
  location ~* \.(html|json)$ {
    expires -1;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
  }

  # Service Worker - pas de cache
  location = /sw.js {
    expires -1;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
  }

  # Manifest avec bon Content-Type
  location = /manifest.json {
    default_type application/manifest+json;
    expires -1;
  }
}
```

### Variables d'environnement
```bash
VITE_APP_NAME="Inventaire Épicerie"
VITE_APP_SHORT_NAME="Inventaire"
VITE_APP_THEME_COLOR="#0f172a"
```

## Fonctionnalités avancées (préparées)

### Notifications Push
Le Service Worker est prêt pour les notifications push.
Configuration nécessaire :
1. Obtenir les clés VAPID du backend
2. Demander la permission à l'utilisateur
3. S'abonner aux notifications

```javascript
// Demander la permission
const permission = await Notification.requestPermission();

if (permission === 'granted') {
  // S'abonner aux notifications
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: 'YOUR_VAPID_PUBLIC_KEY'
  });

  // Envoyer la subscription au backend
  await api.post('/notifications/subscribe', subscription);
}
```

### Background Sync
Déjà géré par `OfflineContext` pour les mutations.

### Share Target API
Configuration dans manifest.json pour recevoir des partages :
- Images
- PDFs
- Factures

## Prochaines étapes recommandées

1. **Remplacer les icônes SVG** par de vraies icônes PNG/SVG optimisées
2. **Ajouter des screenshots** dans `/public/` pour le manifest
3. **Configurer les notifications push** si nécessaire
4. **Personnaliser les couleurs** du manifest selon la charte graphique
5. **Tester sur différents appareils** (iOS, Android, Desktop)
6. **Optimiser la stratégie de cache** selon les besoins métier
7. **Configurer le serveur web** pour les headers appropriés
8. **Mettre en place l'analytics** PWA (installations, usage offline, etc.)

## Ressources

- [MDN - Progressive Web Apps](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
- [web.dev - PWA](https://web.dev/progressive-web-apps/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Web App Manifest](https://developer.mozilla.org/en-US/docs/Web/Manifest)
- [Workbox](https://developers.google.com/web/tools/workbox) - Alternative au SW custom

## Support

Pour toute question ou problème concernant le PWA :
1. Vérifier les logs de la console : `[PWA]`, `[SW]`
2. Vérifier l'onglet Application dans DevTools
3. Tester en navigation privée (cache frais)
4. Vérifier que HTTPS est actif en production
