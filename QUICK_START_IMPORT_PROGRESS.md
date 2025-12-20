# Quick Start - Import Progress Notifications

## Installation en 3 étapes

### Étape 1: Copier les fichiers

Les fichiers suivants ont été créés dans votre projet:

```
✅ frontend/src/components/ui/ImportProgressToast.jsx
✅ frontend/src/components/ui/ToastImportProgress.jsx
✅ frontend/src/hooks/useImportProgress.js
✅ frontend/src/features/invoices/components/InvoiceZeroClickUpload.jsx
✅ frontend/src/features/invoices/components/InvoiceImportWithToast.jsx
```

### Étape 2: Utilisation de base

Ajoutez simplement le composant dans votre page:

```jsx
import InvoiceZeroClickUpload from './features/invoices/components/InvoiceZeroClickUpload';

function MyImportPage() {
  return (
    <div>
      <h1>Import de factures</h1>

      <InvoiceZeroClickUpload
        onImportSuccess={(summary) => {
          console.log('Succès!', summary);
          // Rafraîchir vos données ici
        }}
      />
    </div>
  );
}
```

### Étape 3: Tester

1. Uploader un fichier PDF de facture
2. Observer le toast de progression qui apparaît
3. Voir les étapes: Extraction → Analyse → Import
4. Toast devient vert et affiche le résumé

**C'est tout!** Le système est prêt à l'emploi.

## Options avancées

### Option A: Hook personnalisé

Pour plus de contrôle:

```jsx
import { useImportProgress } from './hooks/useImportProgress';

function MyComponent() {
  const { startImport, isImporting, ToastPortal } = useImportProgress({
    onSuccess: (summary) => console.log('Done!', summary),
    onError: (error) => console.error('Failed:', error)
  });

  const handleFileUpload = (file) => {
    startImport({
      file,
      marginPercent: 40,
      supplierHint: 'Metro'
    });
  };

  return (
    <>
      <input type="file" onChange={(e) => handleFileUpload(e.target.files[0])} />
      {ToastPortal && <ToastPortal />}
    </>
  );
}
```

### Option B: Intégration avec ToastProvider existant

```jsx
import InvoiceImportWithToast from './features/invoices/components/InvoiceImportWithToast';

function MyPage() {
  return <InvoiceImportWithToast onImportSuccess={handleSuccess} />;
}
```

## Visualiser la démo

Pour voir tous les états du composant:

1. Créer une route dans votre app:
```jsx
import ImportProgressToastDemo from './components/ui/ImportProgressToast.demo';

<Route path="/demo/import-progress" element={<ImportProgressToastDemo />} />
```

2. Naviguer vers `/demo/import-progress`
3. Tester les différents scénarios

## Customisation rapide

### Changer les couleurs

Éditer `/frontend/src/components/ui/ImportProgressToast.jsx`:

```jsx
// Ligne 364: Couleur de succès
className="bg-emerald-50 border-emerald-200"  // → bg-green-50 border-green-200

// Ligne 365: Couleur d'erreur
className="bg-rose-50 border-rose-200"  // → bg-red-50 border-red-200

// Ligne 366: Couleur en cours
className="bg-white border-slate-200"  // → bg-blue-50 border-blue-200
```

### Changer l'intervalle de polling

Éditer `/frontend/src/hooks/useImportProgress.js`, ligne 71:

```jsx
pollingIntervalRef.current = setInterval(() => {
  refetch();
}, 2000);  // ← Changer ici (en millisecondes)
```

### Modifier les étapes

Éditer `/frontend/src/components/ui/ImportProgressToast.jsx`, ligne 21:

```jsx
const ImportSteps = {
  EXTRACTION: {
    id: 'extraction',
    label: 'Extraction',
    icon: FileText,
    description: 'Lecture du fichier...',
  },
  // Ajouter vos étapes ici
};
```

## Backend requis

Le système attend ces endpoints:

### 1. Lancer un job
```
POST /api/invoices/zero-click/jobs
Body: FormData { file, margin_percent, supplier_hint, auto_confirm }
Response: { job_id: "uuid", status: "pending" }
```

### 2. Récupérer le statut
```
GET /api/invoices/zero-click/jobs/:jobId
Response: {
  job_id: "uuid",
  status: "processing" | "completed" | "failed",
  progress: 0-100,  // optionnel
  summary: { movements_created, quantity_total, products_created },  // si completed
  error: "message"  // si failed
}
```

## Vérification

Checklist pour vérifier que tout fonctionne:

- [ ] Les fichiers sont bien copiés
- [ ] Aucune erreur dans la console
- [ ] Le composant s'affiche correctement
- [ ] L'upload de fichier fonctionne
- [ ] Le toast apparaît lors de l'upload
- [ ] La barre de progression s'anime
- [ ] Les étapes changent visuellement
- [ ] Le toast devient vert en cas de succès
- [ ] Le résumé s'affiche correctement

## Troubleshooting rapide

### Le toast ne s'affiche pas
→ Vérifier que `{ToastPortal && <ToastPortal />}` est bien dans le JSX

### Erreur "Cannot find module"
→ Vérifier les chemins d'import (ajuster si nécessaire)

### Le polling ne démarre pas
→ Vérifier que le backend retourne bien un `job_id`

### La progression reste bloquée
→ Vérifier que le backend retourne `status: 'completed'` à la fin

## Prochaines étapes

1. **Tester avec un vrai fichier**: Uploader une facture PDF
2. **Personnaliser les couleurs**: Adapter à votre charte graphique
3. **Ajouter des analytics**: Logger les événements d'import
4. **Gérer les erreurs**: Afficher des messages spécifiques

## Support

📚 Documentation complète: `/frontend/src/components/ui/IMPORT_PROGRESS_DOCUMENTATION.md`
📖 README détaillé: `/IMPORT_PROGRESS_README.md`

## Exemple complet minimal

```jsx
import { useImportProgress } from './hooks/useImportProgress';

export default function QuickImportPage() {
  const { startImport, ToastPortal } = useImportProgress();

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Import Facture</h1>

      <input
        type="file"
        accept=".pdf"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) startImport({ file });
        }}
        className="border p-2 rounded"
      />

      {ToastPortal && <ToastPortal />}
    </div>
  );
}
```

**Copiez ce code, testez, et c'est prêt!** 🚀
