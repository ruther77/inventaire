# Migration Guide - Utiliser le PDF Preview ailleurs dans le projet

## Introduction

Ce guide explique comment intégrer la fonctionnalité PDF Preview dans d'autres parties de votre application.

## Scénarios d'utilisation

### Scénario 1: Affichage simple d'un PDF

**Use case:** Vous voulez juste afficher un PDF, sans fonctionnalités avancées.

**Code:**
```jsx
import { PDFPreview } from '@/components/pdf';

function MyDocumentPage() {
  const [pdfUrl, setPdfUrl] = useState(null);

  return (
    <div className="p-6">
      <PDFPreview
        file={pdfUrl}
        fileName="Document.pdf"
        className="h-[600px]"
      />
    </div>
  );
}
```

**Effort:** 5 minutes

---

### Scénario 2: Upload + Preview

**Use case:** Permettre à l'utilisateur d'uploader un PDF et le prévisualiser.

**Code:**
```jsx
import { PDFPreview } from '@/components/pdf';
import { usePDFFile } from '@/hooks';

function MyUploadPage() {
  const { file, setPDFFile, hasFile, fileMetadata } = usePDFFile();

  const handleFileSelect = (event) => {
    const file = event.target.files?.[0];
    if (file) setPDFFile(file);
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <label className="block mb-2 text-sm font-medium">
          Uploader un document
        </label>
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          className="block w-full text-sm"
        />
      </div>

      {hasFile && (
        <>
          <div className="text-sm text-slate-600">
            Fichier: {fileMetadata?.name} ({fileMetadata?.size} bytes)
          </div>
          <PDFPreview
            file={file}
            fileName={fileMetadata?.name}
            className="h-[600px]"
          />
        </>
      )}
    </div>
  );
}
```

**Effort:** 15 minutes

---

### Scénario 3: Split-view avec éditeur

**Use case:** Afficher un PDF à gauche et un formulaire/éditeur à droite.

**Code:**
```jsx
import { PDFPreview } from '@/components/pdf';
import { usePDFFile } from '@/hooks';

function MyEditorPage() {
  const { file, setPDFFile } = usePDFFile();
  const [formData, setFormData] = useState({});

  return (
    <div className="grid lg:grid-cols-12 gap-6 p-6">
      {/* PDF - 40% */}
      <div className="lg:col-span-5">
        <PDFPreview
          file={file}
          fileName="Document.pdf"
          className="sticky top-6 h-[calc(100vh-200px)]"
        />
      </div>

      {/* Editor - 60% */}
      <div className="lg:col-span-7 space-y-4">
        <h2 className="text-xl font-bold">Formulaire</h2>
        <form>
          {/* Vos champs de formulaire */}
          <input
            type="text"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            className="w-full p-2 border rounded"
          />
          {/* ... autres champs */}
        </form>
      </div>
    </div>
  );
}
```

**Effort:** 30 minutes

---

### Scénario 4: Highlighting de texte

**Use case:** Permettre aux utilisateurs de surligner du texte dans le PDF.

**Code:**
```jsx
import { PDFViewerWrapper, useHighlights } from '@/components/pdf';

function MyAnnotationPage() {
  const { file } = usePDFFile();
  const { highlights, addHighlight, clearHighlights } = useHighlights();
  const [highlightMode, setHighlightMode] = useState(false);

  const handleTextHighlight = (highlightData) => {
    addHighlight({
      text: highlightData.text,
      timestamp: highlightData.timestamp,
      note: '', // Optionnel: ajouter une note
    });
  };

  return (
    <div className="p-6">
      {/* Contrôles */}
      <div className="flex gap-4 mb-4">
        <button
          onClick={() => setHighlightMode(!highlightMode)}
          className="px-4 py-2 bg-yellow-500 text-white rounded"
        >
          {highlightMode ? 'Désactiver' : 'Activer'} Highlighting
        </button>
        <button
          onClick={clearHighlights}
          className="px-4 py-2 bg-gray-500 text-white rounded"
        >
          Effacer ({highlights.length})
        </button>
      </div>

      {/* Viewer */}
      <PDFViewerWrapper
        file={file}
        fileName="Document.pdf"
        enableHighlight={highlightMode}
        onTextHighlight={handleTextHighlight}
        highlights={highlights}
        className="h-[600px]"
      />

      {/* Liste des highlights */}
      <div className="mt-4 space-y-2">
        {highlights.map((h) => (
          <div key={h.id} className="p-3 bg-yellow-50 rounded">
            <p className="text-sm">{h.text}</p>
            <p className="text-xs text-gray-500">
              {new Date(h.timestamp).toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Effort:** 45 minutes

---

### Scénario 5: Comparaison de PDFs

**Use case:** Afficher 2 PDFs côte à côte pour comparaison.

**Code:**
```jsx
import { PDFPreview } from '@/components/pdf';
import { usePDFFile } from '@/hooks';

function MyComparisonPage() {
  const pdfLeft = usePDFFile();
  const pdfRight = usePDFFile();

  return (
    <div className="grid grid-cols-2 gap-6 p-6">
      {/* PDF 1 */}
      <div>
        <h3 className="mb-2 font-bold">Document 1</h3>
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) pdfLeft.setPDFFile(file);
          }}
          className="mb-4"
        />
        <PDFPreview
          file={pdfLeft.file}
          fileName="Document 1"
          className="h-[calc(100vh-250px)]"
        />
      </div>

      {/* PDF 2 */}
      <div>
        <h3 className="mb-2 font-bold">Document 2</h3>
        <input
          type="file"
          accept=".pdf"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) pdfRight.setPDFFile(file);
          }}
          className="mb-4"
        />
        <PDFPreview
          file={pdfRight.file}
          fileName="Document 2"
          className="h-[calc(100vh-250px)]"
        />
      </div>
    </div>
  );
}
```

**Effort:** 30 minutes

---

## Migration depuis une solution existante

### Si vous utilisez déjà un viewer PDF

#### Option 1: Remplacement direct
```jsx
// Avant
import OldPDFViewer from 'old-library';

<OldPDFViewer src={pdfUrl} />

// Après
import { PDFPreview } from '@/components/pdf';

<PDFPreview file={pdfUrl} fileName="Document.pdf" />
```

#### Option 2: Migration progressive
```jsx
// Garder l'ancien et tester le nouveau
import OldPDFViewer from 'old-library';
import { PDFPreview } from '@/components/pdf';

const useNewViewer = true; // Toggle pour tester

{useNewViewer ? (
  <PDFPreview file={pdfUrl} fileName="Document.pdf" />
) : (
  <OldPDFViewer src={pdfUrl} />
)}
```

---

## Checklist de migration

### Préparation
- [ ] Lire la documentation complète (`PDF_PREVIEW_GUIDE.md`)
- [ ] Consulter les exemples (`INTEGRATION_EXAMPLE.jsx`)
- [ ] Identifier le use case le plus proche

### Implémentation
- [ ] Importer les composants nécessaires
- [ ] Ajouter le hook `usePDFFile` si upload requis
- [ ] Configurer le layout (simple/split-view)
- [ ] Ajouter les contrôles si nécessaire

### Test
- [ ] Tester l'affichage du PDF
- [ ] Tester les contrôles (zoom, fullscreen)
- [ ] Tester sur mobile
- [ ] Vérifier la performance
- [ ] Vérifier les erreurs console

### Optimisation
- [ ] Ajuster la hauteur du viewer
- [ ] Optimiser le chargement
- [ ] Ajouter les états de loading/error
- [ ] Améliorer l'UX

---

## Erreurs courantes et solutions

### Erreur 1: "Cannot read property 'file' of undefined"

**Cause:** Le hook `usePDFFile` n'est pas appelé.

**Solution:**
```jsx
// Mauvais
<PDFPreview file={undefined} />

// Bon
const { file } = usePDFFile();
<PDFPreview file={file} />
```

---

### Erreur 2: Le PDF ne s'affiche pas

**Cause:** Le fichier n'est pas un PDF valide ou l'URL est incorrecte.

**Solution:**
```jsx
// Vérifier le type
const handleFileSelect = (event) => {
  const file = event.target.files?.[0];
  if (!file) return;

  if (file.type !== 'application/pdf') {
    alert('Veuillez sélectionner un PDF');
    return;
  }

  setPDFFile(file);
};
```

---

### Erreur 3: Memory leak après plusieurs uploads

**Cause:** Les URL blob ne sont pas nettoyées.

**Solution:**
```jsx
// Utiliser le hook (cleanup automatique)
const { file, setPDFFile, clearPDFFile } = usePDFFile();

// Nettoyer quand le composant unmount
useEffect(() => {
  return () => clearPDFFile();
}, []);
```

---

### Erreur 4: Le layout est cassé sur mobile

**Cause:** Pas de breakpoints responsifs.

**Solution:**
```jsx
// Utiliser les classes Tailwind responsive
<div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
  <div className="lg:col-span-5">
    <PDFPreview collapsible={true} />
  </div>
  <div className="lg:col-span-7">
    {/* Editor */}
  </div>
</div>
```

---

## Best practices

### Performance
```jsx
// ✅ Bon: Rendu conditionnel
{hasFile && <PDFPreview file={file} />}

// ❌ Mauvais: Toujours rendu
<PDFPreview file={file} />
```

### Accessibilité
```jsx
// ✅ Bon: Labels descriptifs
<input
  type="file"
  accept=".pdf"
  aria-label="Sélectionner un document PDF"
/>

// ❌ Mauvais: Pas de label
<input type="file" />
```

### État de chargement
```jsx
// ✅ Bon: Afficher un loader
{isLoading ? (
  <div>Chargement du PDF...</div>
) : (
  <PDFPreview file={file} />
)}

// ❌ Mauvais: Rien pendant le chargement
<PDFPreview file={file} />
```

---

## Support TypeScript

Si votre projet utilise TypeScript, voici les types :

```typescript
// types/pdf.d.ts
declare module '@/components/pdf' {
  export interface PDFPreviewProps {
    file: File | string | null;
    fileName?: string;
    collapsible?: boolean;
    defaultCollapsed?: boolean;
    className?: string;
  }

  export const PDFPreview: React.FC<PDFPreviewProps>;

  export interface UsePDFFileReturn {
    file: File | string | null;
    fileUrl: string | null;
    fileMetadata: {
      name: string;
      size: number;
      type: string;
      lastModified: Date | null;
    } | null;
    setPDFFile: (file: File | string) => void;
    clearPDFFile: () => void;
    formatFileSize: (bytes: number) => string;
    hasFile: boolean;
  }

  export function usePDFFile(): UsePDFFileReturn;
}
```

---

## Ressources

### Documentation
- Guide complet: `/frontend/src/features/invoices/PDF_PREVIEW_GUIDE.md`
- Exemples: `/frontend/src/features/invoices/INTEGRATION_EXAMPLE.jsx`
- Tests: `/frontend/src/features/invoices/TESTING_CHECKLIST.md`

### Code source
- Composants: `/frontend/src/components/ui/PDF*.jsx`
- Hook: `/frontend/src/hooks/usePDFFile.js`
- Wrapper: `/frontend/src/components/pdf/PDFViewerWrapper.jsx`

### Support
1. Consulter la documentation
2. Vérifier les exemples
3. Lire le code source (bien commenté)

---

## Conclusion

La migration/intégration du PDF Preview dans votre code est simple :

1. **Import** - 1 ligne
2. **Hook** - 1 ligne (si upload)
3. **Composant** - 3-5 lignes
4. **Styling** - Classes Tailwind existantes

**Temps total:** 5-45 minutes selon le use case

Pour tout problème, consultez d'abord la documentation complète !
