# Cypress E2E Tests

Tests end-to-end automatisés pour le module Finance/Trésorerie.

## Installation

```bash
# Installer Cypress si ce n'est pas déjà fait
npm install --save-dev cypress

# Ouvrir Cypress en mode interactif
npm run cypress:open

# Exécuter les tests en mode headless
npm run test:e2e
```

## Structure des Tests

```
cypress/
├── e2e/
│   └── finance.cy.js          # Tests du module Finance
├── fixtures/
│   ├── transactions.json      # Données de test (transactions)
│   ├── transactions.csv       # Fichier CSV de test
│   ├── large-transactions.json # Dataset large pour tests de performance
│   ├── anomalies.json         # Données de test (anomalies)
│   └── rules.json             # Données de test (règles)
├── support/
│   ├── commands.js            # Commandes Cypress personnalisées
│   └── e2e.js                 # Configuration globale
└── README.md
```

## Tests Couverts

### Module Finance (finance.cy.js)

#### 1. Treasury Dashboard
- Chargement de la page de trésorerie
- Affichage des métriques financières
- Navigation entre sections
- Tests d'accessibilité

#### 2. Transactions Page
- Chargement de la table des transactions
- Filtrage par recherche
- Tri par colonnes
- Sélection de lignes (individuelle et en masse)
- Actions groupées (recatégorisation)
- Pagination
- Export de données
- Gestion des états vides

#### 3. Imports Page
- Affichage du stepper d'import
- Upload de fichier CSV
- Mapping des colonnes
- Validation des données importées

#### 4. Anomalies Page
- Navigation entre onglets
- Filtrage par sévérité
- Résolution d'anomalies
- Ignorer des anomalies

#### 5. Rules Page
- Création de règles de catégorisation
- Édition de règles existantes
- Activation/désactivation de règles
- Suppression de règles
- Test de règles

#### 6. Accessibilité
- Navigation clavier
- ARIA labels
- Hiérarchie des titres
- Indicateurs de focus
- Annonces pour lecteurs d'écran

#### 7. Gestion des Erreurs
- Erreurs API
- Erreurs réseau
- Validation de formulaires

#### 8. Performance
- Temps de chargement
- Gestion de datasets volumineux

## Commandes Personnalisées

### cy.login(username, password)
Authentifie l'utilisateur et crée une session.

```javascript
cy.login('admin', 'password');
```

### cy.mockFinanceAPI()
Mock les appels API du module Finance avec des fixtures.

```javascript
cy.mockFinanceAPI();
```

### cy.waitForTable(testId)
Attend que la table de données soit chargée.

```javascript
cy.waitForTable('transactions-table');
```

### cy.checkA11y(context, options)
Vérifie l'accessibilité de la page (basique).

```javascript
cy.checkA11y();
```

## Bonnes Pratiques

### 1. Utiliser des data-testid
```html
<table data-testid="transactions-table">
```

### 2. Éviter les sélecteurs CSS fragiles
```javascript
// ❌ Mauvais
cy.get('.btn-primary').click();

// ✅ Bon
cy.get('[data-testid="submit-button"]').click();
cy.contains('button', 'Soumettre').click();
```

### 3. Attendre les actions asynchrones
```javascript
// Utiliser les aliases
cy.intercept('GET', '/api/transactions').as('getTransactions');
cy.wait('@getTransactions');

// Ou attendre un élément
cy.get('[data-testid="transactions-table"]').should('exist');
```

### 4. Nettoyer l'état entre les tests
```javascript
beforeEach(() => {
  cy.mockFinanceAPI();
  cy.visit('/treasury');
});
```

### 5. Tester l'accessibilité
```javascript
// Vérifier les ARIA labels
cy.get('button').should('have.attr', 'aria-label');

// Vérifier la navigation clavier
cy.get('body').tab();
cy.focused().should('be.visible');
```

## Exécution des Tests

### Mode Interactif (Développement)
```bash
npm run cypress:open
```
- Interface graphique
- Rechargement automatique
- Time-travel debugging
- Screenshots et vidéos

### Mode Headless (CI/CD)
```bash
npm run test:e2e
```
- Exécution rapide
- Pas d'interface graphique
- Génération de rapports
- Screenshots des échecs

### Tests Spécifiques
```bash
# Un fichier spécifique
npx cypress run --spec "cypress/e2e/finance.cy.js"

# Un test spécifique
npx cypress run --spec "cypress/e2e/finance.cy.js" --grep "should load transactions"
```

## Configuration

Le fichier `cypress.config.js` contient la configuration principale :

```javascript
{
  e2e: {
    baseUrl: 'http://localhost:5173',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: false,
    screenshotOnRunFailure: true
  }
}
```

## Debugging

### 1. Mode Debug
```javascript
cy.debug(); // Pause et ouvre les DevTools
cy.pause(); // Pause l'exécution
```

### 2. Logs
```javascript
cy.log('Message de debug');
console.log('Variable:', myVar);
```

### 3. Screenshots
```javascript
cy.screenshot('screenshot-name');
```

## Intégration CI/CD

### GitHub Actions
```yaml
- name: Run E2E Tests
  run: |
    npm ci
    npm run build
    npm run test:e2e
```

### GitLab CI
```yaml
test:e2e:
  script:
    - npm ci
    - npm run build
    - npm run test:e2e
```

## Ressources

- [Documentation Cypress](https://docs.cypress.io)
- [Best Practices](https://docs.cypress.io/guides/references/best-practices)
- [API Reference](https://docs.cypress.io/api/table-of-contents)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
