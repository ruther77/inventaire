# Scanner de Code-Barres - Documentation

## Vue d'ensemble

Système complet de scan de codes-barres via la caméra mobile, utilisant la BarcodeDetector API native avec fallback gracieux.

## Composants

### 1. `useBarcodeScanner` (Hook)

Hook personnalisé pour gérer la détection de codes-barres.

**Localisation**: `/frontend/src/hooks/useBarcodeScanner.js`

**Features**:
- Détection en temps réel via BarcodeDetector API
- Support des formats: EAN-13, EAN-8, Code128, QR Code, UPC, etc.
- Modes: continu ou single-scan
- Gestion des permissions caméra
- Feedback sonore configurable
- Callbacks pour détection et erreurs

**Utilisation**:

```javascript
import { useBarcodeScanner } from '../../hooks/useBarcodeScanner.js';

const {
  isScanning,
  detectedCode,
  startScanning,
  stopScanning,
  resetDetection,
  error,
  isSupported,
} = useBarcodeScanner({
  onDetected: (code, format) => {
    console.log('Code détecté:', code, format);
  },
  continuous: false,
  formats: ['ean_13', 'ean_8', 'qr_code'],
  beepOnDetection: true,
});
```

**Options**:

| Option | Type | Défaut | Description |
|--------|------|--------|-------------|
| `onDetected` | function | - | Callback appelé lors de la détection |
| `onError` | function | - | Callback appelé en cas d'erreur |
| `continuous` | boolean | `false` | Mode continu (multiples scans) |
| `formats` | array | `DEFAULT_FORMATS` | Formats de codes-barres à détecter |
| `scanInterval` | number | `300` | Intervalle entre scans (ms) |
| `beepOnDetection` | boolean | `true` | Son lors de la détection |

---

### 2. `BarcodeScanner` (Composant)

Composant de base pour le scan de codes-barres avec caméra.

**Localisation**: `/frontend/src/components/ui/BarcodeScanner.jsx`

**Features**:
- Accès à la caméra arrière/avant
- Overlay visuel avec zone de scan animée
- Feedback visuel et sonore
- Bouton lampe torche (si disponible)
- Bouton changement de caméra
- Gestion des permissions

**Utilisation**:

```javascript
import BarcodeScanner from './BarcodeScanner.jsx';

<BarcodeScanner
  onDetected={(code, format) => {
    console.log('Scanné:', code, format);
  }}
  continuous={false}
  facingMode="environment"
  showTorchButton={true}
  showCameraSwitch={true}
/>
```

**Props**:

| Prop | Type | Défaut | Description |
|------|------|--------|-------------|
| `onDetected` | function | - | Callback lors de la détection |
| `onError` | function | - | Callback en cas d'erreur |
| `continuous` | boolean | `false` | Mode continu |
| `formats` | array | - | Formats à détecter |
| `facingMode` | string | `'environment'` | Caméra (`'user'` ou `'environment'`) |
| `showTorchButton` | boolean | `true` | Afficher bouton lampe |
| `showCameraSwitch` | boolean | `true` | Afficher bouton changement caméra |

---

### 3. `BarcodeScannerModal` (Composant)

Modal fullscreen pour le scan de codes-barres.

**Localisation**: `/frontend/src/components/ui/BarcodeScannerModal.jsx`

**Features**:
- Interface fullscreen optimisée mobile
- Header personnalisable
- Affichage du code scanné avec format
- Boutons d'action (confirmer/rescanner)
- Animations d'entrée/sortie
- Auto-confirmation configurable

**Utilisation**:

```javascript
import BarcodeScannerModal from './BarcodeScannerModal.jsx';

const [isOpen, setIsOpen] = useState(false);

<BarcodeScannerModal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  onConfirm={(code, format) => {
    console.log('Confirmé:', code, format);
    handleProductSearch(code);
  }}
  title="Scanner un produit"
  subtitle="Scannez le code-barres pour rechercher"
  continuous={false}
  autoConfirm={true}
  autoConfirmDelay={1500}
/>
```

**Props**:

| Prop | Type | Défaut | Description |
|------|------|--------|-------------|
| `isOpen` | boolean | `false` | État du modal |
| `onClose` | function | - | Callback fermeture |
| `onConfirm` | function | - | Callback confirmation |
| `onScan` | function | - | Callback scan (avant confirmation) |
| `title` | string | `'Scanner un code-barres'` | Titre du modal |
| `subtitle` | string | - | Sous-titre |
| `continuous` | boolean | `false` | Mode continu |
| `formats` | array | - | Formats à détecter |
| `confirmButtonText` | string | `'Confirmer'` | Texte bouton confirmer |
| `autoConfirm` | boolean | `false` | Confirmation automatique |
| `autoConfirmDelay` | number | `1000` | Délai auto-confirmation (ms) |
| `showTorchButton` | boolean | `true` | Afficher bouton lampe |
| `showCameraSwitch` | boolean | `true` | Afficher bouton changement caméra |

---

## Exemples d'intégration

### Exemple 1: Recherche de produit simple

```javascript
import { useState } from 'react';
import BarcodeScannerModal from './BarcodeScannerModal.jsx';
import Button from './Button.jsx';
import api from '../../api/client.js';

function ProductSearch() {
  const [isScanning, setIsScanning] = useState(false);

  const handleBarcodeScanned = async (code, format) => {
    try {
      const { data } = await api.get(`/catalog/products/search`, {
        params: { barcode: code },
      });

      if (data) {
        console.log('Produit trouvé:', data);
        // Naviguer vers la page produit, afficher détails, etc.
      }
    } catch (err) {
      console.error('Erreur recherche:', err);
    }
  };

  return (
    <>
      <Button onClick={() => setIsScanning(true)}>
        Scanner un produit
      </Button>

      <BarcodeScannerModal
        isOpen={isScanning}
        onClose={() => setIsScanning(false)}
        onConfirm={handleBarcodeScanned}
        title="Rechercher un produit"
        autoConfirm={true}
      />
    </>
  );
}
```

### Exemple 2: Ajustement de stock en continu

```javascript
import { useState } from 'react';
import BarcodeScannerModal from './BarcodeScannerModal.jsx';
import { toast } from 'sonner';

function StockAdjustment() {
  const [isScanning, setIsScanning] = useState(false);
  const [scannedItems, setScannedItems] = useState([]);

  const handleScan = async (code, format) => {
    // Mode continu : chaque scan ajoute à la liste
    const product = await searchProduct(code);

    if (product) {
      setScannedItems(prev => [...prev, { code, product, timestamp: Date.now() }]);
      toast.success(`${product.nom} ajouté`);
    }
  };

  return (
    <>
      <Button onClick={() => setIsScanning(true)}>
        Scanner l'inventaire
      </Button>

      <BarcodeScannerModal
        isOpen={isScanning}
        onClose={() => setIsScanning(false)}
        onScan={handleScan}  // Note: onScan au lieu de onConfirm
        title="Inventaire rapide"
        continuous={true}      // Mode continu activé
        autoConfirm={false}
      />

      {/* Liste des articles scannés */}
      <div>
        {scannedItems.map((item, i) => (
          <div key={i}>{item.product.nom}</div>
        ))}
      </div>
    </>
  );
}
```

### Exemple 3: Intégration dans ProductDetailPage

Voir `/frontend/src/features/inventory/ProductDetailPage.jsx` pour un exemple complet.

### Exemple 4: Page dédiée au scan

Voir `/frontend/src/features/inventory/ProductScannerPage.jsx` pour un exemple complet avec historique et actions.

---

## Support des navigateurs

### BarcodeDetector API

L'API BarcodeDetector est supportée nativement sur:

- ✅ Chrome for Android (83+)
- ✅ Edge for Android (83+)
- ✅ Samsung Internet (14+)
- ❌ Safari iOS (non supporté)
- ❌ Firefox (non supporté)

### Fallback recommandé

Pour les navigateurs non supportés, vous pouvez:

1. Utiliser une bibliothèque alternative (ZXing, Quagga.js)
2. Afficher un message d'erreur gracieux
3. Proposer une saisie manuelle

Le composant détecte automatiquement si l'API est disponible et affiche un message d'avertissement.

---

## Formats supportés

Formats détectables (si supportés par le navigateur):

- **EAN-13** - Code-barres produits (Europe)
- **EAN-8** - Code-barres produits court
- **UPC-A** - Code-barres produits (USA)
- **UPC-E** - Code-barres produits court (USA)
- **Code 128** - Code-barres industriel
- **Code 39** - Code-barres industriel
- **Code 93** - Code-barres industriel
- **QR Code** - Code 2D

Pour vérifier les formats supportés:

```javascript
const { getSupportedFormats } = useBarcodeScanner();
const formats = await getSupportedFormats();
console.log('Formats supportés:', formats);
```

---

## Permissions

### Caméra

Le composant demande automatiquement l'autorisation d'accès à la caméra.

**Messages d'erreur courants**:

- `NotAllowedError` - Permission refusée par l'utilisateur
- `NotFoundError` - Aucune caméra disponible
- `NotReadableError` - Caméra utilisée par une autre app

**Vérification des permissions**:

```javascript
const { checkPermission } = useBarcodeScanner();
const state = await checkPermission(); // 'granted', 'denied', 'prompt'
```

---

## Optimisations

### Performance

- Intervalle de scan ajustable (`scanInterval`)
- Arrêt automatique en mode single-scan
- Cleanup des ressources caméra

### UX

- Feedback visuel (overlay animé)
- Feedback sonore (beep configurable)
- Affichage du code détecté
- Vibration (à ajouter si nécessaire)

### Accessibilité

- Support clavier (ESC pour fermer)
- Labels ARIA
- Focus management

---

## Troubleshooting

### Le scanner ne détecte rien

1. Vérifier que le navigateur supporte l'API
2. Vérifier les permissions caméra
3. Améliorer l'éclairage
4. Réduire `scanInterval` pour scanner plus fréquemment

### Détections multiples du même code

- C'est normal en mode continu
- Le hook évite les duplicates via `lastDetectedRef`
- Ajuster `scanInterval` si nécessaire

### Caméra ne démarre pas

1. Vérifier les permissions
2. Vérifier que la caméra n'est pas utilisée ailleurs
3. Essayer de redémarrer le navigateur
4. Vérifier les contraintes de sécurité (HTTPS requis)

---

## Prochaines améliorations

- [ ] Polyfill pour Safari iOS (via ZXing)
- [ ] Support de la vibration haptique
- [ ] Historique des scans persisté
- [ ] Export des scans en CSV
- [ ] Mode batch avec validation
- [ ] Support des codes-barres endommagés
- [ ] Zoom manuel
- [ ] Capture d'image pour debug
- [ ] Statistiques de performance

---

## Ressources

- [BarcodeDetector API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/BarcodeDetector)
- [Shape Detection API - W3C](https://wicg.github.io/shape-detection-api/)
- [Can I Use - BarcodeDetector](https://caniuse.com/mdn-api_barcodedetector)
