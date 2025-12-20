# PWA Quick Start Guide

## 🚀 Démarrage rapide

Votre application est maintenant une PWA complète ! Suivez ces étapes pour commencer.

## 1️⃣ Vérifier l'installation

Tous les fichiers PWA ont été créés :

```
frontend/
├── public/
│   ├── manifest.json          ✅ Manifest PWA
│   ├── sw.js                  ✅ Service Worker
│   ├── icon-192.png          ✅ Icône 192x192 (placeholder SVG)
│   └── icon-512.png          ✅ Icône 512x512 (placeholder SVG)
├── src/
│   ├── hooks/
│   │   └── usePWA.js         ✅ Hook React PWA
│   ├── components/
│   │   └── pwa/
│   │       └── InstallPWAButton.jsx  ✅ Composants UI
│   └── contexts/
│       └── OfflineContext.jsx ✅ Gestion offline
├── index.html                 ✅ Meta tags PWA
└── main.jsx                   ✅ Service Worker enregistré
```

## 2️⃣ Lancer l'application

```bash
cd /home/ruuuzer/Documents/monprojet/frontend
npm run dev
```

L'application démarre sur `http://localhost:5173`

## 3️⃣ Tester le PWA

### Option A : Avec Chrome DevTools

1. Ouvrir Chrome DevTools (F12)
2. Aller dans l'onglet **Application**
3. Section **Manifest** : Vérifier le manifest.json
4. Section **Service Workers** : Vérifier qu'il est actif
5. Cliquer sur **"Add to home screen"** pour installer

### Option B : Banner automatique

Le banner d'installation s'affiche automatiquement si :
- L'app n'est pas déjà installée
- Tous les critères PWA sont remplis
- Le navigateur supporte l'installation

### Option C : Ajouter le banner manuellement

Dans votre `App.jsx` ou layout principal :

```jsx
import { InstallPWAButton } from '@/components/pwa/InstallPWAButton';

function App() {
  return (
    <>
      {/* Votre app */}
      <YourContent />

      {/* Banner d'installation PWA (s'affiche automatiquement si installable) */}
      <InstallPWAButton variant="banner" />
    </>
  );
}
```

## 4️⃣ Tester le mode offline

1. Ouvrir DevTools > Network
2. Cocher "Offline"
3. Recharger la page
4. L'app devrait fonctionner grâce au cache

## 5️⃣ Personnaliser (optionnel mais recommandé)

### Remplacer les icônes

Les icônes actuelles sont des placeholders SVG. Remplacez-les par de vraies icônes :

```bash
# Remplacer ces fichiers :
frontend/public/icon-192.png
frontend/public/icon-512.png
```

**Recommandations :**
- Format : PNG avec fond transparent ou couleur de marque
- Tailles : Exactement 192x192 et 512x512 pixels
- Design : Simple, reconnaissable même en petit
- Safe zone : 40% central pour maskable icons

**Outils gratuits :**
- [Favicon.io](https://favicon.io/) - Générateur d'icônes
- [PWA Builder](https://www.pwabuilder.com/imageGenerator) - Image generator
- [Maskable.app](https://maskable.app/) - Testeur d'icônes maskable

### Ajuster les couleurs

Modifier dans `public/manifest.json` :

```json
{
  "theme_color": "#0f172a",       // Couleur de la barre d'adresse
  "background_color": "#0f172a"   // Couleur de fond au lancement
}
```

Et dans `index.html` :

```html
<meta name="theme-color" content="#0f172a" />
```

### Ajouter des screenshots (optionnel)

Pour améliorer le prompt d'installation :

1. Créer des screenshots :
   - Mobile : 390x844 pixels
   - Desktop : 1920x1080 pixels

2. Les placer dans `public/` :
   ```
   public/screenshot-mobile.png
   public/screenshot-desktop.png
   ```

3. Ils sont déjà référencés dans le manifest !

## 6️⃣ Utiliser le hook usePWA

Le hook `usePWA` vous donne accès à toutes les fonctionnalités :

```jsx
import { usePWA } from '@/hooks/usePWA';

function MyComponent() {
  const {
    isInstallable,      // true si l'app peut être installée
    isInstalled,        // true si l'app est déjà installée
    isStandalone,       // true si l'app est en mode PWA
    promptInstall,      // Fonction pour afficher le prompt d'installation
    share,              // Fonction pour partager du contenu
  } = usePWA();

  return (
    <div>
      {isInstallable && (
        <button onClick={promptInstall}>
          Installer l'application
        </button>
      )}

      {isStandalone && (
        <p>Vous utilisez l'application installée !</p>
      )}
    </div>
  );
}
```

## 7️⃣ Gérer le mode offline

Le contexte `OfflineContext` gère automatiquement :

```jsx
import { useOfflineContext } from '@/contexts/OfflineContext';

function MyComponent() {
  const {
    isOnline,              // État de connexion
    pendingMutations,      // Mutations en attente
    syncPendingMutations,  // Fonction pour synchroniser
  } = useOfflineContext();

  return (
    <div>
      {!isOnline && (
        <div className="offline-banner">
          Mode hors ligne
        </div>
      )}

      {pendingMutations.length > 0 && (
        <button onClick={syncPendingMutations}>
          Synchroniser {pendingMutations.length} actions
        </button>
      )}
    </div>
  );
}
```

## 8️⃣ Build et déploiement

### Build de production

```bash
npm run build
```

Les fichiers sont générés dans `dist/` avec :
- Manifest et Service Worker copiés automatiquement
- Assets optimisés et cachables
- Code minifié

### Preview local

```bash
npm run preview
```

Test du build en local sur `http://localhost:5173`

### Déploiement

**IMPORTANT :** HTTPS est obligatoire pour les PWA en production !

Options de déploiement :
- Vercel (HTTPS automatique)
- Netlify (HTTPS automatique)
- Cloudflare Pages (HTTPS automatique)
- VPS avec Let's Encrypt

Configuration Nginx minimale :

```nginx
server {
    listen 443 ssl http2;
    server_name votre-domaine.com;

    ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;

    root /var/www/inventaire/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Pas de cache pour SW et manifest
    location ~ ^/(sw\.js|manifest\.json)$ {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # Cache long pour assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## 9️⃣ Vérifier avec Lighthouse

1. Ouvrir Chrome DevTools (F12)
2. Onglet **Lighthouse**
3. Cocher "Progressive Web App"
4. Cliquer "Generate report"

**Score attendu :** > 90/100

Si le score est bas, vérifier :
- HTTPS actif
- Service Worker enregistré
- Manifest valide
- Icônes présentes
- Offline fonctionnel

## 🔟 Exemples complets

Consultez le fichier `PWA_INTEGRATION_EXAMPLE.jsx` pour :
- Banner d'installation complet
- Indicateur de statut offline
- Page de paramètres PWA
- Bouton de partage
- Hook personnalisé simplifié

## 📚 Documentation complète

- **PWA_SETUP.md** - Guide détaillé complet
- **PWA_INTEGRATION_EXAMPLE.jsx** - Exemples de code
- **PWA_CHECKLIST.md** - Checklist de vérification
- **PWA_QUICK_START.md** - Ce guide (démarrage rapide)

## ❓ Problèmes courants

### "PWA not installable"
- Vérifier HTTPS en production
- Vérifier que le manifest est accessible : `/manifest.json`
- Vérifier que le SW est enregistré : DevTools > Application > Service Workers

### "Service Worker not updating"
- Fermer tous les onglets de l'app
- Faire Ctrl+Shift+R (hard refresh)
- Vérifier la console pour les erreurs

### "Offline mode not working"
- Vérifier que le SW est actif
- Vérifier la console pour les erreurs de cache
- Tester avec DevTools > Network > Offline

## 🎉 C'est tout !

Votre application est maintenant une PWA complète avec :
- ✅ Installation sur mobile et desktop
- ✅ Fonctionnement offline
- ✅ Cache intelligent
- ✅ Mises à jour automatiques
- ✅ Synchronisation des données
- ✅ Partage de contenu

**Prochaine étape recommandée :** Remplacer les icônes SVG par de vraies icônes PNG

---

**Besoin d'aide ?** Consultez `PWA_SETUP.md` pour plus de détails.
