# Architecture Diagram - PDF Preview Feature

## Flow complet de l'utilisateur

```
┌─────────────────────────────────────────────────────────────────┐
│                     1. UTILISATEUR                              │
│                                                                 │
│  Action: Upload PDF ou Colle texte                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  2. INVOICE UPLOAD CARD                         │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Input: File (PDF/DOCX) ou Texte brut                   │ │
│  │  Processing: Validation + Upload                          │ │
│  │  Callback: onFileUpload(file) → Parent                   │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ├─────────────────┬──────────────────────┐
                         ▼                 ▼                      ▼
         ┌───────────────────────┐  ┌──────────────┐  ┌─────────────────┐
         │  3a. PDF FILE HOOK    │  │ 3b. API CALL │  │ 3c. PROCESSING  │
         │                       │  │              │  │     SNAPSHOT    │
         │  setPDFFile(file)     │  │ POST /extract│  │                 │
         │  → Generate blob URL  │  │ → Get lines  │  │  setProcessing  │
         │  → Store metadata     │  │              │  │  Snapshot(...)  │
         └───────────┬───────────┘  └──────┬───────┘  └────────┬────────┘
                     │                     │                   │
                     └─────────────────────┴───────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     4. IMPORT PAGE                              │
│                                                                 │
│  State:                                                         │
│  - pdfFile.file (File object)                                  │
│  - pdfFile.fileUrl (blob URL)                                  │
│  - lines[] (extracted invoice lines)                           │
│  - processingSnapshot (OCR status)                             │
│                                                                 │
│  Condition: if (pdfFile.hasFile && lines.length > 0)          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  5. SPLIT-VIEW RENDER                           │
│                                                                 │
│  ┌─────────────────────────┬──────────────────────────────────┐│
│  │  LEFT (40%)             │  RIGHT (60%)                     ││
│  │  ┌──────────────────┐   │  ┌──────────────────────────┐   ││
│  │  │  PDF PREVIEW     │   │  │  PROCESSING CARD         │   ││
│  │  │                  │   │  │  - OCR status            │   ││
│  │  │  - Zoom controls │   │  │  - Matching status       │   ││
│  │  │  - Fullscreen    │   │  │  - Anomalies             │   ││
│  │  │  - Download      │   │  └──────────────────────────┘   ││
│  │  │  - Collapse      │   │                                  ││
│  │  │                  │   │  ┌──────────────────────────┐   ││
│  │  │  [PDF Content]   │   │  │  INVOICE LINES EDITOR    │   ││
│  │  │                  │   │  │                          │   ││
│  │  │  (Sticky)        │   │  │  - Table editable        │   ││
│  │  │                  │   │  │  - Add/Remove lines      │   ││
│  │  │                  │   │  │  - Match suggestions     │   ││
│  │  │                  │   │  │  - CSV export            │   ││
│  │  └──────────────────┘   │  └──────────────────────────┘   ││
│  │                         │                                  ││
│  │                         │  ┌──────────────────────────┐   ││
│  │                         │  │  INVOICE ACTIONS         │   ││
│  │                         │  │                          │   ││
│  │                         │  │  - Supplier select       │   ││
│  │                         │  │  - Date picker           │   ││
│  │                         │  │  - Import button         │   ││
│  │                         │  └──────────────────────────┘   ││
│  └─────────────────────────┴──────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture des composants

```
┌─────────────────────────────────────────────────────────────────┐
│                       ImportPage.jsx                            │
│                    (Orchestrateur principal)                    │
└────────────┬───────────────────────────────────┬────────────────┘
             │                                   │
    ┌────────▼────────┐                ┌────────▼─────────┐
    │  usePDFFile()   │                │ useState(lines)  │
    │                 │                │                  │
    │  Returns:       │                │  Manages:        │
    │  - file         │                │  - Extracted     │
    │  - fileUrl      │                │    invoice lines │
    │  - metadata     │                │  - User edits    │
    │  - setPDFFile   │                │                  │
    └────────┬────────┘                └────────┬─────────┘
             │                                   │
             │                                   │
    ┌────────▼───────────────────────────────────▼────────┐
    │              Conditional Render                     │
    │   if (pdfFile.hasFile && lines.length > 0)         │
    └────────┬────────────────────────────────────────────┘
             │
             ├─────────────────────┬──────────────────────┐
             ▼                     ▼                      ▼
   ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
   │  PDFPreview     │  │ InvoiceLinesEditor│  │ InvoiceActions  │
   │                 │  │                  │  │                 │
   │  Props:         │  │  Props:          │  │  Props:         │
   │  - file         │  │  - lines[]       │  │  - supplier     │
   │  - fileName     │  │  - onLinesChange │  │  - invoiceDate  │
   │  - collapsible  │  │  - onDownloadCsv │  │  - onImport     │
   │  - className    │  │                  │  │                 │
   └─────────────────┘  └──────────────────┘  └─────────────────┘
```

---

## Hiérarchie des composants PDF

```
PDFViewerWrapper (Smart Component)
│
├─ Détection:
│  ├─ Browser support PDF natif?
│  ├─ Highlighting requis?
│  └─ Mobile device?
│
├─ Render (si iframe)
│  └─ PDFPreview
│      │
│      ├─ Header (contrôles)
│      │  ├─ Zoom +/-
│      │  ├─ Fullscreen toggle
│      │  ├─ Download button
│      │  └─ Collapse button
│      │
│      ├─ Body (viewer)
│      │  └─ <iframe src={pdfUrl} />
│      │
│      └─ Footer (optionnel)
│         └─ Page navigation
│
└─ Render (si canvas)
   └─ PDFPreviewAdvanced
       │
       ├─ Header (contrôles avancés)
       │  ├─ Zoom +/-
       │  ├─ Rotate button
       │  ├─ Highlight mode toggle
       │  └─ Fullscreen toggle
       │
       ├─ Body (canvas viewer)
       │  ├─ <canvas> (PDF render)
       │  ├─ Text layer (selection)
       │  └─ Highlight overlays
       │
       └─ Footer (highlights list)
          └─ Selected text + actions
```

---

## Data Flow

### Upload et affichage

```
User Upload File
      │
      ▼
InvoiceUploadCard.processFile(file)
      │
      ├─────────────────────┬──────────────────────┐
      │                     │                      │
      ▼                     ▼                      ▼
onFileUpload(file)    API.extract(file)    onProcessingSnapshot()
      │                     │                      │
      ▼                     ▼                      │
pdfFile.setPDFFile()  onExtractionSuccess()       │
      │                     │                      │
      ├─────────────────────┴──────────────────────┘
      │
      ▼
ImportPage re-render
      │
      ├─ pdfFile.hasFile = true
      ├─ lines.length > 0
      │
      ▼
Split-view displayed
```

### Édition et sync

```
User edits line in editor
      │
      ▼
InvoiceLinesEditor.handleFieldChange()
      │
      ▼
onLinesChange(nextLines)
      │
      ▼
ImportPage.setLines(nextLines)
      │
      ├─ Update local state
      ├─ Sync with documents[]
      │
      ▼
UI updates automatically
```

---

## Hook usePDFFile - Internal Flow

```
usePDFFile()
      │
      ├─ useState(file)
      ├─ useState(fileUrl)
      └─ useState(fileMetadata)
      │
      ▼
useEffect(() => {
  if (!file) {
    cleanup previous URL
    return
  }

  if (file instanceof File) {
    url = URL.createObjectURL(file)
    setFileUrl(url)
    extractMetadata(file)

    return () => URL.revokeObjectURL(url)  ← Cleanup
  }

  if (typeof file === 'string') {
    setFileUrl(file)
  }
}, [file])
      │
      ▼
Return {
  file,
  fileUrl,          ← Utilisable dans <iframe src={fileUrl} />
  fileMetadata,
  setPDFFile,
  clearPDFFile,
  hasFile
}
```

---

## Responsive Behavior

### Desktop (>= 1024px)

```
┌──────────────────────────────────────────────────────────┐
│  ImportPage                                              │
│  ┌────────────────────────┬───────────────────────────┐ │
│  │  PDF (40%)             │  Editor (60%)             │ │
│  │  lg:col-span-5         │  lg:col-span-7            │ │
│  │                        │                           │ │
│  │  Sticky top-6          │  Normal scroll            │ │
│  │  h-[calc(100vh-200px)] │  space-y-6                │ │
│  └────────────────────────┴───────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Mobile (< 768px)

```
┌────────────────────┐
│  ImportPage        │
│                    │
│  ┌──────────────┐  │
│  │ PDF Preview  │  │   ← Collapsed by default
│  │ (Click ↓)    │  │     collapsible={true}
│  └──────────────┘  │     defaultCollapsed={false}
│                    │
│  ┌──────────────┐  │
│  │              │  │
│  │   Editor     │  │   ← Full width
│  │   (100%)     │  │     Stack vertical
│  │              │  │
│  └──────────────┘  │
└────────────────────┘
```

---

## State Management

### ImportPage state

```javascript
{
  // PDF
  pdfFile: {
    file: File | string,
    fileUrl: string,
    fileMetadata: {
      name: string,
      size: number,
      type: string,
      lastModified: Date
    },
    hasFile: boolean
  },

  // Extraction
  lines: [
    {
      nom: string,
      codes: string,
      quantite: number,
      prix_achat: number,
      tva: number,
      produit_id: number | null,
      ...
    }
  ],

  // Documents (multi-invoices)
  documents: [
    {
      invoice_id: string,
      facture_date: string,
      items: [...lines],
      pdf_path: string
    }
  ],

  // Processing
  processingSnapshot: {
    isProcessing: boolean,
    fileName: string,
    steps: [
      { id: 'ocr', status: 'completed', result: string },
      { id: 'matching', status: 'processing', ... },
      ...
    ],
    attentionItems: [...],
    summary: { totalHT, tva, totalTTC, lineCount }
  },

  // UI
  selectedDocumentId: string | null,
  marginPercent: number,
  supplier: string,
  invoiceDate: string,
  drawerOpen: boolean
}
```

---

## Performance Optimizations

### 1. Conditional rendering

```jsx
// ❌ Bad: Always render (even if no file)
<PDFPreview file={pdfFile.file} />

// ✅ Good: Render only when needed
{pdfFile.hasFile && <PDFPreview file={pdfFile.file} />}

// ✅ Better: Render only with data
{pdfFile.hasFile && lines.length > 0 && (
  <div className="grid lg:grid-cols-12 gap-6">
    <PDFPreview file={pdfFile.file} />
    <InvoiceLinesEditor lines={lines} />
  </div>
)}
```

### 2. Cleanup URLs

```javascript
// usePDFFile hook
useEffect(() => {
  if (file instanceof File) {
    const url = URL.createObjectURL(file);
    setFileUrl(url);

    // Cleanup to prevent memory leak
    return () => {
      URL.revokeObjectURL(url);
    };
  }
}, [file]);
```

### 3. Sticky positioning (not fixed)

```jsx
// ✅ Good: Sticky (GPU accelerated, better performance)
<PDFPreview className="sticky top-6" />

// ❌ Bad: Fixed (re-renders, bad scroll)
<PDFPreview className="fixed top-6" />
```

### 4. Lazy loading

```jsx
// Import dynamically if needed
const PDFPreview = lazy(() => import('@/components/pdf/PDFPreview'));

<Suspense fallback={<div>Loading PDF viewer...</div>}>
  <PDFPreview file={file} />
</Suspense>
```

---

## Bundle Structure

```
frontend/dist/
├── assets/
│   ├── index-[hash].js              ← Main bundle
│   ├── PDFPreview-[hash].js         ← PDF components (~12KB)
│   ├── PDFPreviewAdvanced-[hash].js ← Advanced (~10KB)
│   └── vendor-[hash].js             ← Dependencies
│
└── index.html
```

**Impact:**
- Main bundle: +0KB (lazy loaded)
- PDF bundle: +29KB (minified), ~9KB (gzipped)
- Load time: +50-100ms (first PDF render only)

---

## Error Handling Flow

```
Error occurs
      │
      ├─ File upload failed?
      │  └─ Display error in InvoiceUploadCard
      │     └─ "Erreur lors de l'extraction"
      │
      ├─ PDF invalid/corrupted?
      │  └─ PDFPreview shows fallback
      │     └─ "Impossible de charger le PDF"
      │
      ├─ Network error?
      │  └─ Retry mechanism
      │     └─ Show retry button
      │
      └─ Unknown error?
         └─ Log to console
            └─ Show generic error message
```

---

## Extension Points

### Where to add new features

1. **New PDF controls** → Modify `PDFPreview.jsx` header
2. **Advanced highlighting** → Use `PDFPreviewAdvanced.jsx`
3. **Multi-page thumbnails** → Add to `PDFPreview.jsx` footer
4. **PDF annotations** → Extend `useHighlights()` hook
5. **Custom viewer** → Create new component using `usePDFFile()`

### How to extend

```jsx
// Example: Add rotation control
import { RotateCw } from 'lucide-react';

function MyCustomPDFViewer() {
  const { file } = usePDFFile();
  const [rotation, setRotation] = useState(0);

  return (
    <div>
      <button onClick={() => setRotation((r) => (r + 90) % 360)}>
        <RotateCw />
      </button>
      <iframe
        src={file}
        style={{ transform: `rotate(${rotation}deg)` }}
      />
    </div>
  );
}
```

---

## Conclusion

L'architecture est conçue pour être:

✅ **Modulaire** - Composants indépendants et réutilisables
✅ **Performante** - Cleanup auto, rendu conditionnel, lazy loading
✅ **Extensible** - Facile d'ajouter des fonctionnalités
✅ **Responsive** - Adapté à toutes les tailles d'écran
✅ **Maintenable** - Code clair, bien documenté, bien testé

Pour plus de détails, consultez les autres guides !
