# Guide d'utilisation : Preview PDF Inline

## Vue d'ensemble

La fonctionnalité "Preview PDF inline" permet d'afficher un aperçu du PDF d'une facture côte à côte avec l'éditeur de lignes, offrant une expérience de split-view pour faciliter la vérification et l'édition des données extraites.

## Architecture

### Composants créés

1. **PDFPreview.jsx** (`/components/ui/PDFPreview.jsx`)
   - Composant de base utilisant `<iframe>` pour afficher le PDF
   - Contrôles de zoom (50% - 200%)
   - Mode plein écran
   - Téléchargement du PDF
   - Collapsible sur mobile

2. **PDFPreviewAdvanced.jsx** (`/components/ui/PDFPreviewAdvanced.jsx`)
   - Version avancée avec Canvas
   - Support du text highlighting
   - Rotation du document
   - Sélection de texte et annotations

3. **PDFViewerWrapper.jsx** (`/components/pdf/PDFViewerWrapper.jsx`)
   - Wrapper intelligent qui choisit automatiquement le meilleur mode de rendu
   - Détection du navigateur et des capacités
   - Optimisations mobile

4. **InvoicePDFWorkspace.jsx** (`/features/invoices/components/InvoicePDFWorkspace.jsx`)
   - Workspace complet avec PDF + Éditeur
   - Mode highlighting pour lier le texte PDF aux lignes
   - Gestion des annotations

5. **usePDFFile.js** (`/hooks/usePDFFile.js`)
   - Hook custom pour gérer l'état du fichier PDF
   - Génération et cleanup d'URL blob
   - Métadonnées du fichier

## Utilisation

### Utilisation basique dans ImportPage

La page d'import utilise déjà automatiquement le split-view quand un PDF est chargé :

```jsx
import PDFPreview from '../../components/ui/PDFPreview.jsx';
import { usePDFFileFromUpload } from '../../hooks/usePDFFile.js';

// Dans le composant
const pdfFile = usePDFFileFromUpload();

// Dans le render
<InvoiceUploadCard
  onFileUpload={(file) => pdfFile.setPDFFile(file)}
  // ... autres props
/>

{pdfFile.hasFile && lines.length > 0 && (
  <div className="grid lg:grid-cols-12 gap-6">
    {/* PDF Preview - 40% width */}
    <div className="lg:col-span-5">
      <PDFPreview
        file={pdfFile.file}
        fileName={pdfFile.fileMetadata?.name || 'Facture'}
        collapsible={true}
        defaultCollapsed={false}
        className="sticky top-6 h-[calc(100vh-200px)]"
      />
    </div>

    {/* Editor - 60% width */}
    <div className="lg:col-span-7">
      <InvoiceLinesEditor lines={lines} onLinesChange={setLines} />
    </div>
  </div>
)}
```

### Utilisation avec highlighting

Pour utiliser le mode highlighting avancé :

```jsx
import PDFViewerWrapper, { useHighlights } from '../../components/pdf/PDFViewerWrapper.jsx';

function MyComponent() {
  const { highlights, addHighlight, clearHighlights } = useHighlights();

  const handleTextHighlight = (highlightData) => {
    addHighlight({
      text: highlightData.text,
      timestamp: highlightData.timestamp,
      linkedToLine: selectedLineIndex,
    });
  };

  return (
    <PDFViewerWrapper
      file={pdfFile}
      fileName="Facture.pdf"
      enableHighlight={true}
      onTextHighlight={handleTextHighlight}
      highlights={highlights}
    />
  );
}
```

### Utilisation du workspace complet

Pour une expérience complète avec linking PDF ↔ Lignes :

```jsx
import InvoicePDFWorkspace from './components/InvoicePDFWorkspace.jsx';

<InvoicePDFWorkspace
  pdfFile={pdfFile.file}
  pdfFileName={pdfFile.fileMetadata?.name}
  lines={lines}
  onLinesChange={setLines}
  onDownloadCsv={handleDownloadCsv}
/>
```

## Fonctionnalités

### Contrôles de base
- **Zoom** : 50% → 200% (boutons +/- ou clic sur le pourcentage)
- **Plein écran** : Bouton Maximize/Minimize
- **Téléchargement** : Bouton Download
- **Collapse** : Réduire le preview (utile sur mobile)

### Mode Highlighting (version avancée)
1. Activer le mode highlight
2. Sélectionner du texte dans le PDF
3. Le texte est automatiquement surligné et enregistré
4. Possibilité de lier les highlights à des lignes spécifiques

### Responsive Design
- **Desktop (>1024px)** : Split-view 40/60
- **Tablet (768-1024px)** : Split-view vertical
- **Mobile (<768px)** : PDF collapsible, éditeur en pleine largeur

## API du hook usePDFFile

```jsx
const {
  file,              // File object ou URL
  fileUrl,           // URL blob générée
  fileMetadata,      // { name, size, type, lastModified }
  setPDFFile,        // (file) => void
  clearPDFFile,      // () => void
  formatFileSize,    // (bytes) => string
  hasFile,           // boolean
} = usePDFFile();
```

## Personnalisation

### Ajuster la hauteur du preview

```jsx
<PDFPreview
  className="h-[600px]"  // Hauteur fixe
  // ou
  className="h-[calc(100vh-200px)]"  // Hauteur relative au viewport
/>
```

### Désactiver le collapse

```jsx
<PDFPreview
  collapsible={false}  // Toujours affiché
/>
```

### Commencer collapsed

```jsx
<PDFPreview
  defaultCollapsed={true}  // Commence réduit
/>
```

## Performance

### Optimisations implémentées
- Cleanup automatique des URL blob (pas de memory leak)
- Rendu conditionnel (split-view uniquement si PDF + lignes)
- Mode iframe par défaut (plus léger que Canvas)
- Détection mobile pour version allégée

### Bonnes pratiques
- Ne pas créer de PDF preview si pas de fichier
- Utiliser `sticky` positioning pour garder le PDF visible pendant le scroll
- Limiter la hauteur du preview avec `max-h-[...]` pour éviter les scrolls infinis

## Dépendances

Aucune dépendance externe nécessaire ! Le projet utilise :
- `framer-motion` (déjà présent) pour les animations
- `lucide-react` (déjà présent) pour les icônes
- API native du navigateur pour l'affichage PDF

## Compatibilité navigateurs

### Méthode iframe (par défaut)
- ✅ Chrome/Edge 90+
- ✅ Safari 14+
- ✅ Firefox 90+
- ⚠️ Mobile : Support variable, fallback sur téléchargement

### Méthode Canvas (si activée)
- ✅ Tous les navigateurs modernes
- ⚠️ Nécessite PDF.js pour le rendu (non implémenté dans ce MVP)

## Évolutions futures

### À implémenter si besoin
1. **Intégration PDF.js complète**
   - Meilleur contrôle du rendu
   - Text layer natif pour sélection
   - Support multi-pages amélioré

2. **Annotations persistantes**
   - Sauvegarder les highlights dans la DB
   - Partager les annotations entre utilisateurs

3. **OCR en temps réel**
   - Highlight automatique des zones détectées
   - Sync visuel entre extraction et PDF

4. **Comparaison side-by-side**
   - Afficher plusieurs factures
   - Comparaison des prix

## Troubleshooting

### Le PDF ne s'affiche pas
- Vérifier que le fichier est bien un PDF valide
- Vérifier que `file` n'est pas null/undefined
- Regarder la console pour les erreurs

### Performance lente
- Utiliser la version iframe (par défaut) au lieu de Canvas
- Limiter le nombre de highlights affichés simultanément
- Réduire la hauteur du preview

### Problèmes de zoom
- Le zoom n'affecte que le contenu, pas les contrôles
- Utiliser `handleResetZoom()` pour revenir à 100%
- Sur mobile, désactiver le zoom du navigateur

## Support

Pour toute question ou bug, consultez :
- Le code source des composants dans `/components/ui/`
- Les exemples d'utilisation dans `ImportPage.jsx`
- La documentation des hooks dans `/hooks/usePDFFile.js`
