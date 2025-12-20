# Système de Notification de Progression d'Import

## Vue d'ensemble

Le système de notification de progression d'import offre une expérience utilisateur fluide pour les imports de factures en arrière-plan. Il combine :

- **Polling automatique** des jobs asynchrones
- **Notifications visuelles** avec barre de progression
- **Étapes visuelles** (Extraction → Analyse → Import)
- **Animations fluides** avec Framer Motion
- **Intégration flexible** avec le système de toast existant

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    useImportProgress                     │
│  (Hook principal - Gère polling + toast standalone)      │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ ImportProgress│  │ API Polling  │  │ Portal Toast │
│    Toast      │  │  (2s inter.) │  │   Rendering  │
└──────────────┘  └──────────────┘  └──────────────┘

Alternative:
┌─────────────────────────────────────────────────────────┐
│            useZeroClickJobWithProgress                   │
│  (Hook simplifié - Pour intégration Toast existant)     │
└─────────────────────────────────────────────────────────┘
```

## Composants

### 1. ImportProgressToast.jsx

Composant visuel autonome qui affiche :
- Icon de statut (Loader / Success / Error)
- Nom du fichier
- Étapes de progression avec icônes
- Barre de progression animée
- Messages contextuels
- Bouton d'annulation / fermeture

**Props:**
```jsx
<ImportProgressToast
  jobStatus={{
    status: 'processing' | 'completed' | 'failed',
    progress: 0-100,
    summary: { movements_created, quantity_total, products_created },
    error: 'message d\'erreur'
  }}
  fileName="facture-metro-2025.pdf"
  onCancel={() => {...}}
  onDismiss={() => {...}}
  canCancel={true}
/>
```

### 2. ToastImportProgress.jsx

Composant compact pour intégration dans le système Toast existant.

**Features:**
- Version compacte du composant principal
- S'intègre dans le ToastProvider
- Affichage mini des étapes
- Barre de progression

### 3. useImportProgress (Hook principal)

Hook tout-en-un qui gère :
- Le lancement du job
- Le polling automatique
- L'affichage du toast via portal
- Les callbacks de succès/erreur

**Usage:**
```jsx
import { useImportProgress } from '@/hooks/useImportProgress';

function MyComponent() {
  const { startImport, isImporting, ToastPortal } = useImportProgress({
    onSuccess: (summary) => {
      console.log('Import réussi:', summary);
    },
    onError: (error) => {
      console.error('Import échoué:', error);
    },
    onCancel: () => {
      console.log('Import annulé');
    }
  });

  const handleUpload = (file) => {
    startImport({
      file,
      marginPercent: 40,
      supplierHint: 'Metro',
      autoConfirm: true
    });
  };

  return (
    <>
      <button onClick={() => handleUpload(myFile)}>
        Importer
      </button>
      {ToastPortal && <ToastPortal />}
    </>
  );
}
```

### 4. useZeroClickJobWithProgress (Hook simplifié)

Version simplifiée sans le portail de toast. Pour intégration manuelle.

**Usage:**
```jsx
import { useZeroClickJobWithProgress } from '@/hooks/useImportProgress';
import { useToast } from '@/components/ui/Toast';

function MyComponent() {
  const { toast } = useToast();
  const { startJob, jobStatus } = useZeroClickJobWithProgress({
    onSuccess: (status) => {
      toast.success('Import terminé!');
    }
  });

  // Gérer l'affichage du toast manuellement
  useEffect(() => {
    if (jobStatus) {
      // Mettre à jour le toast
    }
  }, [jobStatus]);

  return <button onClick={() => startJob({ file })}>Import</button>;
}
```

## Exemples d'intégration

### Option 1: Toast Standalone (Recommandé pour nouvelles pages)

Utilise `ImportProgressToast` en mode portal. Toast indépendant du ToastProvider.

**Fichier:** `InvoiceZeroClickUpload.jsx`

**Avantages:**
- Totalement autonome
- Design sur-mesure
- Pas de conflit avec autres toasts
- Contrôle total sur le cycle de vie

**Utilisation:**
```jsx
import InvoiceZeroClickUpload from '@/features/invoices/components/InvoiceZeroClickUpload';

<InvoiceZeroClickUpload
  onImportSuccess={(summary) => {
    console.log('Import terminé:', summary);
  }}
/>
```

### Option 2: Intégration ToastProvider (Recommandé pour cohérence)

Utilise `ToastImportProgress` avec le ToastProvider existant.

**Fichier:** `InvoiceImportWithToast.jsx`

**Avantages:**
- Cohérence avec l'application
- Gestion centralisée
- Queue de notifications automatique
- Moins de code dupliqué

**Utilisation:**
```jsx
import InvoiceImportWithToast from '@/features/invoices/components/InvoiceImportWithToast';

<InvoiceImportWithToast
  onImportSuccess={(summary) => {
    console.log('Import terminé:', summary);
  }}
/>
```

## API Backend

Le système attend les endpoints suivants:

### POST `/api/invoices/zero-click/jobs`

Lance un job d'import asynchrone.

**Request:**
```
FormData {
  file: File,
  margin_percent: number,
  supplier_hint?: string,
  auto_confirm: boolean
}
```

**Response:**
```json
{
  "job_id": "uuid-v4",
  "status": "pending"
}
```

### GET `/api/invoices/zero-click/jobs/:jobId`

Récupère le statut d'un job.

**Response (Processing):**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "progress": 45,
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Response (Completed):**
```json
{
  "job_id": "uuid",
  "status": "completed",
  "progress": 100,
  "summary": {
    "movements_created": 42,
    "quantity_total": 156,
    "products_created": 3
  },
  "completed_at": "2025-01-15T10:32:45Z"
}
```

**Response (Failed):**
```json
{
  "job_id": "uuid",
  "status": "failed",
  "error": "Format de fichier invalide",
  "failed_at": "2025-01-15T10:31:20Z"
}
```

## Personnalisation

### Modifier les étapes

Éditer `ImportSteps` dans `ImportProgressToast.jsx`:

```jsx
const ImportSteps = {
  EXTRACTION: {
    id: 'extraction',
    label: 'Extraction',
    icon: FileText,
    description: 'Lecture du fichier...',
  },
  // Ajouter d'autres étapes
  VALIDATION: {
    id: 'validation',
    label: 'Validation',
    icon: CheckCircle,
    description: 'Vérification des données...',
  },
};
```

### Modifier la fréquence de polling

Dans `useImportProgress.js`:

```jsx
// Ligne 71 - Changer l'intervalle (actuellement 2000ms)
pollingIntervalRef.current = setInterval(() => {
  refetch();
}, 3000); // 3 secondes au lieu de 2
```

### Modifier les couleurs

Le système utilise les classes Tailwind. Pour changer les couleurs:

**Succès:** Rechercher `emerald-` et remplacer par `green-`
**Erreur:** Rechercher `rose-` et remplacer par `red-`
**En cours:** Rechercher `blue-` et remplacer par la couleur souhaitée

### Ajouter des sons

Dans `useImportProgress.js`, ajouter:

```jsx
useEffect(() => {
  if (jobStatus?.status === 'completed') {
    const audio = new Audio('/sounds/success.mp3');
    audio.play();
  }
}, [jobStatus]);
```

## Animations

Toutes les animations utilisent Framer Motion:

- **Apparition du toast:** `slide-in-from-right` + `fade-in`
- **Progression:** Transition `ease-out` sur `width`
- **Icônes:** Rotation pour loader, scale pour success/error
- **Messages:** Fade croisé entre les messages

Pour désactiver les animations:

```jsx
// Dans ImportProgressToast.jsx, remplacer motion.div par div
<div className="..." /> // Au lieu de <motion.div />
```

## Tests

### Test manuel

1. Créer une page de test
2. Utiliser un fichier PDF de facture
3. Observer les transitions d'état
4. Vérifier le polling (Network tab)
5. Tester l'annulation

### Test avec mock

```jsx
// MockImportProgress.jsx
const mockJobStatus = {
  status: 'processing',
  progress: 45
};

<ImportProgressToast
  jobStatus={mockJobStatus}
  fileName="test.pdf"
/>
```

## Performance

- **Polling:** 2 secondes (optimisé pour équilibre UX/charge serveur)
- **Progression simulée:** Si le backend ne fournit pas `progress`
- **Cleanup:** Intervals nettoyés automatiquement
- **Memory leaks:** Prévention via `useEffect` cleanup

## Accessibilité

- `role="alert"` sur les notifications
- `aria-label` sur les boutons
- Support clavier (Escape pour fermer)
- Contraste couleurs conforme WCAG AA
- Textes alternatifs pour les icônes

## Troubleshooting

### Le toast ne s'affiche pas
- Vérifier que `<ToastPortal />` est bien rendu
- Vérifier la z-index (défaut: 200)

### Le polling ne démarre pas
- Vérifier que `jobId` est bien défini
- Vérifier les logs réseau (onglet Network)
- Vérifier que l'endpoint retourne les bonnes données

### La progression reste bloquée
- Le backend doit retourner `progress` (0-100)
- Sinon, progression simulée utilisée (max 95%)

### Les animations sont saccadées
- Vérifier que Framer Motion est bien installé
- Réduire la complexité des animations
- Utiliser `will-change` CSS si nécessaire

## Migration depuis Sonner

Si vous utilisez déjà `sonner`, voici comment migrer:

### Avant:
```jsx
import { toast } from 'sonner';

toast.loading('Import en cours...');
```

### Après:
```jsx
import { useImportProgress } from '@/hooks/useImportProgress';

const { startImport, ToastPortal } = useImportProgress();

// Dans le JSX
{ToastPortal && <ToastPortal />}
```

## Roadmap

- [ ] Support du mode dark
- [ ] Annulation côté serveur (endpoint DELETE)
- [ ] Historique des imports
- [ ] Notifications browser (Web Notifications API)
- [ ] Support multi-fichiers (queue d'imports)
- [ ] Compression des toasts multiples
- [ ] Export des logs d'import

## Support

Pour toute question ou bug:
1. Vérifier cette documentation
2. Consulter les exemples d'intégration
3. Contacter l'équipe dev
