# Testing Checklist - PDF Preview Inline

## Checklist de vérification

### Installation et Build
- [ ] `npm install` - Aucune nouvelle dépendance requise
- [ ] `npm run build` - Build sans erreur
- [ ] `npm run dev` - Serveur de dev démarre correctement

### Tests fonctionnels basiques

#### 1. Upload de fichier
- [ ] Glisser-déposer un PDF fonctionne
- [ ] Sélectionner un fichier via le bouton fonctionne
- [ ] La barre de progression s'affiche
- [ ] L'extraction de texte se lance

#### 2. Affichage du PDF
- [ ] Le PDF s'affiche à gauche (desktop)
- [ ] Le PDF est lisible et bien rendu
- [ ] Les contrôles sont visibles et fonctionnels
- [ ] Le header avec le nom du fichier est affiché

#### 3. Contrôles de zoom
- [ ] Bouton "Zoom +" augmente la taille
- [ ] Bouton "Zoom -" diminue la taille
- [ ] Clic sur le pourcentage réinitialise à 100%
- [ ] Zoom min = 50%, max = 200%

#### 4. Split-view layout
- [ ] PDF occupe 40% de la largeur (desktop)
- [ ] Éditeur occupe 60% de la largeur (desktop)
- [ ] Le PDF reste visible en scrollant (sticky)
- [ ] Gap de 1.5rem entre les colonnes

#### 5. Mode plein écran
- [ ] Bouton plein écran fonctionne
- [ ] Le PDF occupe tout l'écran
- [ ] Bouton pour quitter le plein écran est visible
- [ ] ESC quitte le plein écran

#### 6. Téléchargement
- [ ] Bouton télécharger fonctionne
- [ ] Le fichier téléchargé s'ouvre correctement
- [ ] Le nom du fichier est correct

#### 7. Collapse (mobile)
- [ ] Sur mobile (<768px), le PDF commence collapsed
- [ ] Cliquer sur le header affiche le PDF
- [ ] Cliquer sur le bouton collapse réduit le PDF
- [ ] L'état persiste pendant l'édition

### Tests responsive

#### Desktop (>1024px)
- [ ] Split-view 40/60 fonctionne
- [ ] Sticky positioning fonctionne
- [ ] Tous les contrôles sont visibles
- [ ] Pas de scroll horizontal

#### Tablet (768-1024px)
- [ ] Split-view s'adapte
- [ ] Contrôles restent accessibles
- [ ] Le PDF est lisible

#### Mobile (<768px)
- [ ] PDF collapsed par défaut
- [ ] Éditeur en pleine largeur
- [ ] Boutons adaptés à la taille tactile
- [ ] Scroll vertical fluide

### Tests de performance

#### Memory
- [ ] Pas de memory leak après upload multiple
- [ ] URL blob est bien nettoyée (vérifier dans DevTools)
- [ ] Performance stable après 5+ uploads

#### Rendering
- [ ] Le PDF s'affiche en <2 secondes
- [ ] Pas de freeze de l'UI pendant le chargement
- [ ] Les animations sont fluides (60fps)

### Tests d'intégration

#### Avec InvoiceUploadCard
- [ ] L'upload déclenche l'affichage du PDF
- [ ] Les données extraites sont synchronisées
- [ ] Le fichier est passé correctement au hook

#### Avec InvoiceLinesEditor
- [ ] Les lignes s'affichent à droite
- [ ] L'édition des lignes fonctionne
- [ ] Pas de conflit de scroll

#### Avec InvoiceProcessingCard
- [ ] La carte de traitement s'affiche correctement
- [ ] Pas de chevauchement avec le PDF

### Tests de compatibilité navigateur

#### Chrome/Edge
- [ ] PDF s'affiche via iframe natif
- [ ] Tous les contrôles fonctionnent
- [ ] Performance optimale

#### Firefox
- [ ] PDF s'affiche correctement
- [ ] Zoom fonctionne
- [ ] Pas d'erreur console

#### Safari
- [ ] PDF s'affiche (support natif)
- [ ] Contrôles fonctionnent
- [ ] Animations fluides

### Tests edge cases

#### Fichiers
- [ ] PDF de 1 page fonctionne
- [ ] PDF de 50+ pages fonctionne
- [ ] PDF de 10MB+ se charge (avec patience)
- [ ] PDF corrompu affiche un message d'erreur
- [ ] Fichier non-PDF est rejeté

#### État vide
- [ ] Aucun fichier = placeholder affiché
- [ ] Message approprié "Aucun PDF sélectionné"
- [ ] Pas d'erreur console

#### Upload multiple
- [ ] Uploader un 2ème PDF remplace le 1er
- [ ] Pas de fuite de mémoire
- [ ] L'ancien URL blob est révoqué

### Tests d'accessibilité

#### Keyboard
- [ ] Tab pour naviguer entre les contrôles
- [ ] Enter pour activer les boutons
- [ ] Esc pour quitter le plein écran

#### Screen reader
- [ ] Les labels des boutons sont descriptifs
- [ ] Le nom du fichier est annoncé
- [ ] Les états (collapsed/expanded) sont communiqués

#### Contraste
- [ ] Les contrôles sont visibles sur fond clair/foncé
- [ ] Le texte a un ratio de contraste ≥ 4.5:1
- [ ] Les icônes sont reconnaissables

### Tests de régression

#### Fonctionnalités existantes
- [ ] L'upload sans PDF fonctionne toujours
- [ ] L'extraction de texte collé fonctionne
- [ ] Les autres composants ne sont pas affectés
- [ ] Les routes existantes fonctionnent

#### Performance globale
- [ ] La page se charge aussi vite qu'avant
- [ ] Pas de ralentissement général
- [ ] Le bundle size augmente de <30KB

## Tests avancés (optionnels)

### Highlighting (si activé)
- [ ] Le mode highlighting s'active
- [ ] La sélection de texte fonctionne
- [ ] Les highlights sont sauvegardés
- [ ] Les highlights sont effaçables

### InvoicePDFWorkspace
- [ ] Le workspace complet fonctionne
- [ ] Le mode linking fonctionne
- [ ] Les highlights sont liés aux lignes

## Commandes de test

```bash
# Test de build
npm run build

# Test de dev
npm run dev

# Test des composants (si Storybook configuré)
npm run storybook

# Linter
npm run lint
```

## Vérifications DevTools

### Console
- [ ] Aucune erreur
- [ ] Aucun warning critique
- [ ] Les logs de debug sont appropriés

### Network
- [ ] Le PDF n'est téléchargé qu'une fois
- [ ] Pas de requêtes inutiles
- [ ] Taille du bundle est raisonnable

### Memory
- [ ] Heap size stable après 10 uploads
- [ ] Pas de détached DOM nodes
- [ ] Les listeners sont bien nettoyés

### Performance
- [ ] First Contentful Paint < 2s
- [ ] Time to Interactive < 3s
- [ ] Layout shifts minimaux

## Bugs connus / Limitations

### Limitations connues
- Navigation multi-pages basique (utilise le viewer natif)
- Pas de text layer natif pour sélection avancée
- Highlighting nécessite la version avancée

### Workarounds
- Pour multi-pages avancé: utiliser PDF.js (non inclus)
- Pour sélection précise: utiliser PDFPreviewAdvanced
- Pour annotations persistantes: stocker en DB (à implémenter)

## Résultats attendus

### ✅ Tous les tests passent
- Fonctionnalités de base opérationnelles
- Responsive design fonctionne
- Performance acceptable
- Pas d'erreur console

### ⚠️ Warnings acceptables
- "Using iframe for PDF" (info, pas une erreur)
- "Mobile detected, using simplified view" (comportement voulu)

### ❌ Erreurs bloquantes
- "Failed to create blob URL" → Vérifier le fichier
- "Cannot read property 'file'" → Vérifier le state
- "PDF failed to load" → Vérifier le format du fichier

## Rapport de test

Date: _________________
Testeur: _________________

### Résumé
- Tests passés: ______ / ______
- Tests échoués: ______
- Bugs critiques: ______
- Bugs mineurs: ______

### Commentaires
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

### Recommandations
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

### Validation finale
- [ ] Approuvé pour production
- [ ] Nécessite des corrections
- [ ] Retour en développement
