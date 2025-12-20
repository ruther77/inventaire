# Guide d'intégration du Scanner de Code-Barres

## Fichiers créés

### 1. Hook principal
- **`/frontend/src/hooks/useBarcodeScanner.js`**
  - Hook personnalisé pour la détection de codes-barres
  - Utilise la BarcodeDetector API native
  - Gestion des états, permissions, et callbacks

### 2. Composants UI
- **`/frontend/src/components/ui/BarcodeScanner.jsx`**
  - Composant de base avec caméra et overlay
  - Feedback visuel et sonore
  - Contrôles (lampe torche, changement de caméra)

- **`/frontend/src/components/ui/BarcodeScannerModal.jsx`**
  - Modal fullscreen pour le scan
  - Interface optimisée mobile
  - Auto-confirmation optionnelle

- **`/frontend/src/components/ui/BarcodeScannerDemo.jsx`**
  - Page de démonstration interactive
  - Configuration en temps réel
  - Historique des scans

### 3. Pages d'exemple
- **`/frontend/src/features/inventory/ProductScannerPage.jsx`**
  - Exemple complet d'intégration
  - Recherche de produits par code-barres
  - Actions rapides (ajustement stock, détails)
  - Historique des scans

- **`/frontend/src/features/inventory/ProductDetailPage.jsx`** (modifié)
  - Ajout du bouton "Scanner" dans le header
  - Recherche de produits via code-barres
  - Navigation automatique vers le produit trouvé

### 4. Documentation
- **`/frontend/src/components/ui/BARCODE_SCANNER_README.md`**
  - Documentation complète des composants
  - Exemples d'utilisation
  - Guide de troubleshooting
  - API reference

## Installation

Aucune dépendance supplémentaire nécessaire ! Le scanner utilise l'API native du navigateur.

## Ajout des routes (optionnel)

Pour ajouter les nouvelles pages à votre application, modifiez `/frontend/src/app/routes.jsx` :

```javascript
import { ProductScannerPage } from '../features/inventory';
import BarcodeScannerDemo from '../components/ui/BarcodeScannerDemo.jsx';

// Ajoutez ces routes dans votre configuration
const routes = [
  // ... autres routes

  // Route principale du scanner
  {
    path: '/inventory/scanner',
    element: <ProductScannerPage />,
  },

  // Route de démo (pour développement)
  {
    path: '/demo/barcode-scanner',
    element: <BarcodeScannerDemo />,
  },
];
```

## Utilisation rapide

### Option 1 : Modal dans une page existante

```javascript
import { useState } from 'react';
import BarcodeScannerModal from '../components/ui/BarcodeScannerModal.jsx';
import Button from '../components/ui/Button.jsx';

function MyPage() {
  const [showScanner, setShowScanner] = useState(false);

  const handleScan = async (code, format) => {
    console.log('Code scanné:', code, format);
    // Votre logique ici
  };

  return (
    <>
      <Button onClick={() => setShowScanner(true)}>
        Scanner un code-barres
      </Button>

      <BarcodeScannerModal
        isOpen={showScanner}
        onClose={() => setShowScanner(false)}
        onConfirm={handleScan}
        title="Scanner un produit"
        autoConfirm={true}
      />
    </>
  );
}
```

### Option 2 : Composant direct

```javascript
import BarcodeScanner from '../components/ui/BarcodeScanner.jsx';

function MyPage() {
  const handleDetected = (code, format) => {
    console.log('Détecté:', code, format);
  };

  return (
    <div className="w-full h-screen">
      <BarcodeScanner
        onDetected={handleDetected}
        continuous={false}
        showTorchButton={true}
      />
    </div>
  );
}
```

### Option 3 : Hook seul (avancé)

```javascript
import { useRef, useEffect } from 'react';
import { useBarcodeScanner } from '../hooks';

function MyCustomScanner() {
  const videoRef = useRef(null);

  const { startScanning, detectedCode, isScanning } = useBarcodeScanner({
    onDetected: (code, format) => {
      console.log('Code:', code, format);
    },
    continuous: true,
  });

  useEffect(() => {
    if (videoRef.current) {
      startScanning(videoRef.current);
    }
  }, [startScanning]);

  return (
    <video ref={videoRef} autoPlay playsInline muted />
  );
}
```

## Exemples d'intégration métier

### 1. Recherche de produit

```javascript
const handleProductSearch = async (barcode) => {
  try {
    const { data } = await api.get('/catalog/products/search', {
      params: { barcode },
    });

    if (data) {
      navigate(`/inventory/products/${data.id}`);
    } else {
      toast.error('Produit non trouvé');
    }
  } catch (err) {
    toast.error('Erreur de recherche');
  }
};

<BarcodeScannerModal
  isOpen={isScanning}
  onClose={() => setIsScanning(false)}
  onConfirm={handleProductSearch}
  title="Rechercher un produit"
  autoConfirm={true}
/>
```

### 2. Inventaire rapide (mode continu)

```javascript
const [scannedItems, setScannedItems] = useState([]);

const handleInventoryScan = async (barcode) => {
  const product = await fetchProduct(barcode);

  if (product) {
    setScannedItems(prev => [...prev, {
      barcode,
      product,
      timestamp: Date.now(),
    }]);
    toast.success(`${product.nom} ajouté`);
  }
};

<BarcodeScannerModal
  isOpen={isScanning}
  onClose={() => setIsScanning(false)}
  onScan={handleInventoryScan}  // Note: onScan, pas onConfirm
  title="Inventaire rapide"
  continuous={true}  // Mode continu
/>
```

### 3. Validation de commande

```javascript
const [expectedItems, setExpectedItems] = useState([
  { barcode: '1234567890123', name: 'Produit A', qty: 5 },
  { barcode: '9876543210987', name: 'Produit B', qty: 3 },
]);

const handleOrderValidation = (barcode) => {
  const item = expectedItems.find(i => i.barcode === barcode);

  if (item) {
    // Marquer comme scanné
    toast.success(`${item.name} validé`);
    setExpectedItems(prev =>
      prev.map(i => i.barcode === barcode
        ? { ...i, scanned: true }
        : i
      )
    );
  } else {
    toast.error('Article non attendu');
  }
};

<BarcodeScannerModal
  isOpen={isScanning}
  onClose={() => setIsScanning(false)}
  onScan={handleOrderValidation}
  title="Validation de commande"
  subtitle={`${expectedItems.filter(i => i.scanned).length}/${expectedItems.length} articles`}
  continuous={true}
/>
```

## Configuration recommandée par cas d'usage

| Use Case | continuous | autoConfirm | autoConfirmDelay |
|----------|-----------|-------------|------------------|
| Recherche simple | ❌ | ✅ | 1000ms |
| Inventaire | ✅ | ❌ | - |
| Validation commande | ✅ | ❌ | - |
| Ajustement stock | ❌ | ✅ | 1500ms |
| Scan unique | ❌ | ❌ | - |

## Support navigateurs

### ✅ Supporté
- Chrome for Android 83+
- Edge for Android 83+
- Samsung Internet 14+

### ❌ Non supporté (actuellement)
- Safari iOS (toutes versions)
- Firefox Android/Desktop

Le composant détecte automatiquement la disponibilité de l'API et affiche un message approprié.

## Permissions requises

### Caméra
L'application demande automatiquement l'autorisation d'accès à la caméra.

**Important**: L'accès à la caméra nécessite HTTPS (sauf sur localhost).

### Vérifier les permissions

```javascript
const { checkPermission } = useBarcodeScanner();
const state = await checkPermission();
// 'granted', 'denied', 'prompt'
```

## Formats supportés

Par défaut, tous les formats sont acceptés :
- EAN-13, EAN-8 (codes-barres produits Europe)
- UPC-A, UPC-E (codes-barres produits USA)
- Code 128, 39, 93 (codes industriels)
- QR Code

Pour limiter à certains formats :

```javascript
<BarcodeScannerModal
  formats={['ean_13', 'ean_8', 'qr_code']}
  // ...
/>
```

## Troubleshooting

### Le scanner ne s'ouvre pas
1. Vérifiez que vous êtes en HTTPS (ou localhost)
2. Vérifiez les permissions caméra dans le navigateur
3. Vérifiez la console pour les erreurs

### Rien n'est détecté
1. Améliorez l'éclairage
2. Vérifiez que le navigateur supporte l'API (Chrome/Edge Android)
3. Essayez d'activer la lampe torche
4. Vérifiez que le code-barres est dans le bon format

### Détections multiples
C'est normal en mode continu. Le système évite les duplicates immédiats.

## Tests

Pour tester rapidement :

1. Accédez à `/demo/barcode-scanner` (après avoir ajouté la route)
2. Ou utilisez la page `/inventory/scanner`
3. Ou testez dans ProductDetailPage (bouton "Scanner" ajouté)

### Codes-barres de test

Vous pouvez générer des codes-barres de test sur :
- https://barcode.tec-it.com/
- https://www.barcodesinc.com/generator/

Formats recommandés pour test :
- EAN-13: `9780201379624` (ISBN)
- QR Code: n'importe quel texte

## Performance

### Optimisations appliquées
- Scan par intervalle (300ms par défaut)
- Cleanup automatique des ressources
- Évitement des duplicates
- Arrêt automatique en mode simple

### Ajuster la performance

```javascript
<BarcodeScanner
  onDetected={handleDetected}
  scanInterval={500}  // Augmenter pour réduire CPU
/>
```

## Prochaines étapes

1. **Polyfill pour iOS**: Ajouter ZXing ou Quagga.js pour Safari
2. **Vibration**: Ajouter feedback haptique
3. **Historique persisté**: Sauvegarder les scans dans IndexedDB
4. **Export**: Permettre l'export CSV des scans
5. **Offline**: Support scan hors ligne avec sync

## Support

Pour toute question ou problème :
1. Consultez `/frontend/src/components/ui/BARCODE_SCANNER_README.md`
2. Vérifiez la console navigateur
3. Testez sur un appareil Android avec Chrome
