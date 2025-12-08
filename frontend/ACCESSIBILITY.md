# Guide d'Accessibilité

Ce document détaille les améliorations d'accessibilité implémentées dans l'application, conformément aux standards WCAG 2.1 Level AA.

## Vue d'ensemble

Tous les composants UI ont été améliorés pour offrir une expérience accessible à tous les utilisateurs, y compris ceux utilisant des technologies d'assistance (lecteurs d'écran, navigation clavier, etc.).

## Composants Améliorés

### 1. Select.jsx

#### Améliorations apportées

**ARIA Attributes**
- `aria-label` : Label pour les selects sans label visible
- `aria-describedby` : Association avec les messages d'erreur et textes d'aide
- `aria-invalid` : Indique les champs en erreur
- `aria-required` : Indique les champs obligatoires

**Fonctionnalités**
- Labels visuels avec `htmlFor` correct
- Indicateur visuel et sémantique pour champs requis (*)
- Messages d'erreur avec `role="alert"` et `aria-live="polite"`
- Support des états disabled avec styles visuels appropriés
- Texte d'aide contextuel

**Exemple d'utilisation**
```jsx
<Select
  label="Catégorie"
  error={errors.category}
  helperText="Sélectionnez la catégorie de la transaction"
  required
  aria-label="Sélecteur de catégorie"
>
  <option value="">Choisir...</option>
  <option value="food">Alimentation</option>
</Select>
```

### 2. Modal.jsx

#### Améliorations apportées

**ARIA Attributes**
- `role="dialog"` : Définit le composant comme dialogue
- `aria-modal="true"` : Indique que c'est un modal
- `aria-labelledby` : Référence le titre du modal
- `aria-describedby` : Référence la description (si présente)

**Focus Management**
- Focus trap : Le focus reste dans le modal (Tab/Shift+Tab)
- Focus automatique sur le modal à l'ouverture
- Restauration du focus sur l'élément précédent à la fermeture
- Exclusion des éléments disabled du focus trap

**Keyboard Navigation**
- Escape : Ferme le modal
- Tab/Shift+Tab : Navigation circulaire dans le modal

**Autres fonctionnalités**
- Bouton fermer avec taille minimale tactile (44x44px)
- Body scroll lock compatible iOS
- Animations respectant `prefers-reduced-motion`

**Exemple d'utilisation**
```jsx
<Modal
  open={isOpen}
  onClose={handleClose}
  title="Confirmer l'action"
  description="Cette action est irréversible"
  actions={[
    { label: 'Annuler', variant: 'ghost', onClick: handleClose },
    { label: 'Confirmer', variant: 'primary', onClick: handleConfirm }
  ]}
>
  <p>Êtes-vous sûr de vouloir continuer ?</p>
</Modal>
```

### 3. DataTable.jsx

#### Améliorations apportées

**ARIA Attributes pour Table**
- `role="table"` ou `role="grid"` : Définit la table (grid si sélectionnable)
- `role="rowgroup"` : Pour thead et tbody
- `role="row"` : Pour chaque ligne
- `role="columnheader"` : Pour les en-têtes de colonnes
- `role="cell"` ou `role="gridcell"` : Pour les cellules
- `aria-sort` : Indique l'état de tri (ascending/descending/none)
- `aria-selected` : Indique les lignes sélectionnées
- `aria-rowindex` / `aria-colindex` : Position des lignes/colonnes
- `aria-rowcount` / `aria-colcount` : Nombre total de lignes/colonnes
- `scope="col"` : Pour les en-têtes de colonnes

**Keyboard Navigation**
- ↑/↓ : Navigation entre les lignes
- Home : Première ligne
- End : Dernière ligne
- Space/Enter : Sélectionner une ligne (si sélectionnable)
- Tab : Navigation entre éléments interactifs

**Screen Reader Support**
- `aria-live="polite"` : Annonces pour le nombre de résultats
- Labels descriptifs pour tous les contrôles
- Messages d'état pour les filtres actifs
- Annonces pour les sélections multiples

**Recherche et Filtres**
- Input de recherche avec `role="searchbox"`
- Label visuel caché avec `sr-only`
- `aria-controls` reliant la recherche au tableau
- Bouton clear avec label accessible

**Pagination**
- Boutons avec labels descriptifs
- États disabled appropriés
- Information sur la pagination (X-Y sur Z résultats)

**Exemple d'utilisation**
```jsx
<DataTable
  data={transactions}
  columns={[
    { key: 'date', header: 'Date', sortable: true },
    { key: 'description', header: 'Description' },
    { key: 'amount', header: 'Montant', align: 'right' }
  ]}
  selectable
  searchable
  sortable
  pagination
  onSelectionChange={handleSelection}
/>
```

## Styles d'Accessibilité

### Screen Reader Only (.sr-only)

Classe pour masquer visuellement du contenu tout en le gardant accessible aux lecteurs d'écran.

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

**Utilisation**
```jsx
<label htmlFor="search" className="sr-only">
  Rechercher dans le tableau
</label>
<input id="search" type="search" placeholder="Rechercher..." />
```

### Focus Visible

Indicateurs de focus personnalisés pour une meilleure visibilité.

```css
:focus-visible {
  outline: 2px solid theme('colors.brand.500');
  outline-offset: 2px;
}
```

### Tailles Tactiles Minimales

Zones tactiles minimales conformes aux standards (44x44px).

```css
.tactile-target {
  @apply min-w-[44px] min-h-[44px] flex items-center justify-center;
}
```

## Support des Préférences Utilisateur

### Reduced Motion

Respect de la préférence `prefers-reduced-motion` pour désactiver les animations.

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### High Contrast

Support du mode contraste élevé avec bordures renforcées.

```css
@media (prefers-contrast: more) {
  button,
  input,
  select {
    @apply border-2;
  }
}
```

## Tests d'Accessibilité

### Tests Manuels

**Navigation Clavier**
1. Tester Tab/Shift+Tab sur toute la page
2. Vérifier que le focus est toujours visible
3. Vérifier l'ordre logique de navigation
4. Tester les raccourcis clavier (Escape, Enter, etc.)

**Lecteur d'écran**
1. Tester avec NVDA (Windows) ou VoiceOver (Mac)
2. Vérifier que tous les éléments sont annoncés correctement
3. Vérifier les labels et descriptions
4. Tester les annonces dynamiques (aria-live)

**Contraste**
1. Vérifier un ratio de contraste minimum de 4.5:1 pour le texte
2. Vérifier un ratio de 3:1 pour les éléments UI
3. Utiliser des outils comme WebAIM Contrast Checker

### Tests Automatisés (Cypress)

Les tests Cypress incluent des vérifications d'accessibilité de base :

```javascript
it('should be accessible', () => {
  cy.visit('/treasury/finance-transactions');

  // Vérifier les ARIA labels
  cy.get('[aria-label]').should('exist');

  // Vérifier la hiérarchie des titres
  cy.get('h1').should('have.length', 1);

  // Tester la navigation clavier
  cy.get('body').tab();
  cy.focused().should('be.visible');
});
```

## Checklist WCAG 2.1 Level AA

### Principe 1 : Perceptible

- [x] 1.1.1 Contenu non textuel (A) - Tous les contrôles ont des labels
- [x] 1.3.1 Information et relations (A) - Structure sémantique correcte
- [x] 1.3.2 Ordre séquentiel logique (A) - Tab order correct
- [x] 1.4.1 Utilisation de la couleur (A) - Pas de dépendance à la couleur seule
- [x] 1.4.3 Contraste minimum (AA) - Ratio 4.5:1 respecté
- [x] 1.4.11 Contraste du contenu non textuel (AA) - Ratio 3:1 pour UI

### Principe 2 : Utilisable

- [x] 2.1.1 Clavier (A) - Toutes les fonctions au clavier
- [x] 2.1.2 Pas de piège au clavier (A) - Focus trap dans modals uniquement
- [x] 2.4.3 Parcours du focus (A) - Ordre logique
- [x] 2.4.6 En-têtes et étiquettes (AA) - Labels descriptifs
- [x] 2.4.7 Focus visible (AA) - Indicateurs de focus visibles
- [x] 2.5.3 Label dans le nom (A) - Labels accessibles
- [x] 2.5.5 Taille de la zone cible (AAA) - 44x44px minimum

### Principe 3 : Compréhensible

- [x] 3.1.1 Langue de la page (A) - lang="fr" sur html
- [x] 3.2.1 Au focus (A) - Pas de changement de contexte au focus
- [x] 3.2.2 À la saisie (A) - Pas de changement au changement de valeur
- [x] 3.3.1 Identification des erreurs (A) - Messages d'erreur clairs
- [x] 3.3.2 Étiquettes ou instructions (A) - Labels et instructions présents
- [x] 3.3.3 Suggestion d'erreur (AA) - Aide contextuelle

### Principe 4 : Robuste

- [x] 4.1.2 Nom, rôle et valeur (A) - ARIA roles et attributes corrects
- [x] 4.1.3 Messages d'état (AA) - aria-live pour annonces

## Ressources

### Documentation

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)

### Outils

- [axe DevTools](https://www.deque.com/axe/devtools/) - Extension navigateur
- [WAVE](https://wave.webaim.org/) - Outil d'évaluation
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [NVDA](https://www.nvaccess.org/) - Lecteur d'écran Windows
- [VoiceOver](https://www.apple.com/accessibility/voiceover/) - Lecteur d'écran macOS

### Lecteurs d'écran

**Windows**
- NVDA (gratuit et open source)
- JAWS (commercial)

**macOS**
- VoiceOver (intégré)

**Linux**
- Orca (intégré dans GNOME)

**Mobile**
- VoiceOver (iOS)
- TalkBack (Android)

## Support et Contribution

Pour toute question ou suggestion d'amélioration de l'accessibilité, merci de créer une issue sur le dépôt du projet.
