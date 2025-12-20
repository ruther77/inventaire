# PWA Components

Composants React pour gérer l'installation et les fonctionnalités PWA.

## Composants disponibles

### InstallPWAButton

Bouton/Banner pour installer l'application en mode PWA.

**Props:**
- `variant` : Style d'affichage
  - `"banner"` : Banner en bas de l'écran (recommandé)
  - `"button"` : Bouton simple
  - `"floating"` : Bouton flottant
- `onInstall` : Callback appelé après installation réussie
- `onDismiss` : Callback appelé quand l'utilisateur ferme le banner

**Comportement:**
- S'affiche automatiquement si l'app est installable
- Se cache si l'app est déjà installée
- Respecte le choix de l'utilisateur (localStorage)
- Compatible iOS et Android

**Exemple:**

```jsx
import { InstallPWAButton } from '@/components/pwa/InstallPWAButton';

function App() {
  return (
    <>
      <YourContent />

      <InstallPWAButton
        variant="banner"
        onInstall={() => console.log('App installée!')}
        onDismiss={() => console.log('Banner fermé')}
      />
    </>
  );
}
```

### InstalledPWABadge

Badge affichant "Application installée" quand l'app est en mode PWA.

**Exemple:**

```jsx
import { InstalledPWABadge } from '@/components/pwa/InstallPWAButton';

function Settings() {
  return (
    <div>
      <h1>Paramètres</h1>
      <InstalledPWABadge />
    </div>
  );
}
```

### StandaloneIndicator

Indicateur discret affiché quand l'app est en mode standalone.

**Exemple:**

```jsx
import { StandaloneIndicator } from '@/components/pwa/InstallPWAButton';

function App() {
  return (
    <>
      <StandaloneIndicator />
      <YourContent />
    </>
  );
}
```

## Usage recommandé

### Dans le layout principal

```jsx
// App.jsx ou Layout.jsx
import { InstallPWAButton } from '@/components/pwa/InstallPWAButton';

export function App() {
  return (
    <div className="app">
      <Header />
      <MainContent />
      <Footer />

      {/* Banner d'installation */}
      <InstallPWAButton variant="banner" />
    </div>
  );
}
```

### Dans une page de paramètres

```jsx
// Settings.jsx
import { InstalledPWABadge } from '@/components/pwa/InstallPWAButton';
import { usePWA } from '@/hooks/usePWA';

export function SettingsPage() {
  const { isInstallable, promptInstall, updateAvailable, activateUpdate } = usePWA();

  return (
    <div>
      <h1>Paramètres</h1>

      <div className="pwa-section">
        <h2>Application</h2>

        <InstalledPWABadge />

        {isInstallable && (
          <button onClick={promptInstall}>
            Installer l'application
          </button>
        )}

        {updateAvailable && (
          <button onClick={activateUpdate}>
            Mettre à jour maintenant
          </button>
        )}
      </div>
    </div>
  );
}
```

## Personnalisation

Les composants utilisent Tailwind CSS. Vous pouvez les personnaliser :

### Modifier les couleurs

```jsx
// Exemple : Banner avec couleurs personnalisées
<div className="fixed bottom-0 left-0 right-0 z-50 bg-gradient-to-r from-purple-600 to-purple-700">
  {/* Contenu du banner */}
</div>
```

### Créer votre propre composant

```jsx
import { usePWA } from '@/hooks/usePWA';

export function CustomInstallButton() {
  const { isInstallable, promptInstall } = usePWA();

  if (!isInstallable) return null;

  return (
    <button
      onClick={async () => {
        const result = await promptInstall();
        if (result.outcome === 'accepted') {
          console.log('Installed!');
        }
      }}
      className="your-custom-styles"
    >
      Installer
    </button>
  );
}
```

## Voir aussi

- `/src/hooks/usePWA.js` - Hook PWA complet
- `/PWA_INTEGRATION_EXAMPLE.jsx` - Exemples d'intégration
- `/PWA_SETUP.md` - Documentation complète
