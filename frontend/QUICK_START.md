# Quick Start - Tests E2E et Accessibilité

Guide de démarrage rapide pour utiliser les tests Cypress et les composants accessibles.

## 🚀 Installation

```bash
cd /home/ruuuzer/Documents/monprojet/frontend

# Installer les dépendances (inclut Cypress 13.6.2)
npm install
```

## ▶️ Lancer les Tests Cypress

### Mode Interactif (Recommandé pour développement)

```bash
# Terminal 1 : Lancer l'application
npm run dev

# Terminal 2 : Ouvrir Cypress
npm run cypress:open
```

Dans l'interface Cypress :
1. Choisir "E2E Testing"
2. Sélectionner un navigateur (Chrome, Firefox, Edge)
3. Cliquer sur `finance.cy.js` pour lancer les tests

### Mode Headless (CI/CD)

```bash
# Tous les tests
npm run test:e2e

# Ou manuellement
npm run cypress:run

# Sur un navigateur spécifique
npm run cypress:run:chrome
npm run cypress:run:firefox
```

## 📝 Utiliser les Composants Accessibles

### Select

```jsx
import Select from './components/ui/Select.jsx';

function MyForm() {
  const [category, setCategory] = useState('');
  const [error, setError] = useState('');

  return (
    <Select
      label="Catégorie"
      value={category}
      onChange={(e) => setCategory(e.target.value)}
      error={error}
      helperText="Sélectionnez la catégorie de la transaction"
      required
    >
      <option value="">Choisir...</option>
      <option value="food">Alimentation</option>
      <option value="transport">Transport</option>
      <option value="housing">Logement</option>
    </Select>
  );
}
```

### Modal

```jsx
import Modal from './components/ui/Modal.jsx';

function MyComponent() {
  const [isOpen, setIsOpen] = useState(false);

  const handleDelete = () => {
    // Logique de suppression
    setIsOpen(false);
  };

  return (
    <>
      <button onClick={() => setIsOpen(true)}>
        Supprimer
      </button>

      <Modal
        open={isOpen}
        onClose={() => setIsOpen(false)}
        title="Confirmer la suppression"
        description="Cette action est irréversible"
        size="sm"
        actions={[
          {
            label: 'Annuler',
            variant: 'ghost',
            onClick: () => setIsOpen(false)
          },
          {
            label: 'Supprimer',
            variant: 'destructive',
            onClick: handleDelete
          }
        ]}
      >
        <p>Êtes-vous sûr de vouloir supprimer cet élément ?</p>
      </Modal>
    </>
  );
}
```

### DataTable

```jsx
import { DataTable } from './components/ui/DataTable.jsx';

function TransactionsPage() {
  const [selectedRows, setSelectedRows] = useState([]);

  const columns = [
    {
      key: 'date',
      header: 'Date',
      sortable: true,
      render: (value) => new Date(value).toLocaleDateString('fr-FR')
    },
    {
      key: 'description',
      header: 'Description',
      searchable: true
    },
    {
      key: 'amount',
      header: 'Montant',
      align: 'right',
      sortable: true,
      render: (value) => `${value.toFixed(2)} €`
    },
  ];

  const bulkActions = [
    {
      id: 'categorize',
      label: 'Recatégoriser',
      onClick: (selectedData) => {
        console.log('Recategorizing:', selectedData);
      }
    }
  ];

  return (
    <DataTable
      data={transactions}
      columns={columns}
      selectable
      searchable
      sortable
      pagination
      pageSize={10}
      selectedRows={selectedRows}
      onSelectionChange={setSelectedRows}
      bulkActions={bulkActions}
      searchPlaceholder="Rechercher une transaction..."
    />
  );
}
```

## 🧪 Écrire de Nouveaux Tests

### Structure d'un test

```javascript
// cypress/e2e/my-feature.cy.js
describe('My Feature', () => {
  beforeEach(() => {
    // Setup avant chaque test
    cy.mockFinanceAPI();
    cy.visit('/my-page');
  });

  it('should do something', () => {
    // Arrange
    cy.get('[data-testid="my-element"]').should('exist');

    // Act
    cy.get('[data-testid="my-button"]').click();

    // Assert
    cy.contains('Success!').should('be.visible');
  });
});
```

### Commandes personnalisées disponibles

```javascript
// Authentification
cy.login('username', 'password');

// Mock API Finance
cy.mockFinanceAPI();

// Attendre le chargement d'une table
cy.waitForTable('transactions-table');

// Vérifier l'accessibilité de base
cy.checkA11y();
```

## ✅ Vérifier l'Accessibilité

### Tests Manuels

**Navigation clavier**
```
Tab          → Élément suivant
Shift+Tab    → Élément précédent
Enter/Space  → Activer
Escape       → Fermer modal
↑/↓          → Naviguer dans table
Home/End     → Première/dernière ligne
```

**Avec lecteur d'écran**
- Windows : NVDA (gratuit) - https://www.nvaccess.org/
- macOS : VoiceOver (Cmd+F5)

### Tests Automatisés

Les tests Cypress incluent des vérifications d'accessibilité :

```javascript
it('should be accessible', () => {
  cy.visit('/treasury/finance-transactions');

  // Vérifier ARIA labels
  cy.get('[aria-label]').should('exist');

  // Vérifier hiérarchie des titres
  cy.get('h1').should('have.length', 1);

  // Tester navigation clavier
  cy.get('body').tab();
  cy.focused().should('be.visible');
});
```

## 📂 Structure des Fichiers

```
frontend/
├── cypress/
│   ├── e2e/
│   │   └── finance.cy.js          # Tests Finance (643 lignes)
│   ├── fixtures/
│   │   ├── transactions.json      # Données de test
│   │   ├── large-transactions.json
│   │   ├── transactions.csv
│   │   ├── anomalies.json
│   │   └── rules.json
│   ├── support/
│   │   ├── commands.js            # Commandes personnalisées
│   │   └── e2e.js                 # Config globale
│   └── README.md                  # Documentation tests
├── src/
│   ├── components/ui/
│   │   ├── Select.jsx             # ✨ Amélioré (85 lignes)
│   │   ├── Modal.jsx              # ✨ Amélioré (258 lignes)
│   │   └── DataTable.jsx          # ✨ Amélioré (1149 lignes)
│   └── styles.css                 # + .sr-only
├── cypress.config.js              # Config Cypress
├── package.json                   # + scripts Cypress
├── ACCESSIBILITY.md               # Guide accessibilité (9.3KB)
├── TESTS_AND_ACCESSIBILITY_SUMMARY.md  # Résumé (11KB)
└── QUICK_START.md                 # Ce fichier
```

## 🔍 Debugging

### Dans les tests Cypress

```javascript
// Pause l'exécution
cy.pause();

// Log debug
cy.log('Debug message');

// Screenshot
cy.screenshot('my-screenshot');

// Ouvrir DevTools au debug
cy.debug();
```

### Dans l'application

```javascript
// Vérifier les ARIA attributes
console.log(element.getAttribute('aria-label'));

// Tester focus
document.activeElement.focus();

// Simuler navigation clavier
element.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
```

## 📚 Documentation Complète

Pour plus de détails, consulter :

- **Tests Cypress** : `/frontend/cypress/README.md` (5.3KB)
- **Accessibilité** : `/frontend/ACCESSIBILITY.md` (9.3KB)
- **Résumé complet** : `/frontend/TESTS_AND_ACCESSIBILITY_SUMMARY.md` (11KB)

## 🐛 Problèmes Courants

### Cypress ne démarre pas

```bash
# Vérifier l'installation
npx cypress verify

# Réinstaller si nécessaire
npm uninstall cypress
npm install --save-dev cypress@13.6.2
```

### Tests échouent avec erreur réseau

```bash
# Vérifier que l'app tourne sur le bon port
npm run dev  # Doit être sur localhost:5173

# Vérifier la config Cypress
cat cypress.config.js  # baseUrl: 'http://localhost:5173'
```

### Composants ne sont pas accessibles

```javascript
// Vérifier les ARIA attributes dans le navigateur
// Ouvrir DevTools > Accessibility Tree

// Ou utiliser l'extension
// axe DevTools : https://www.deque.com/axe/devtools/
```

## ✨ Prochaines Étapes

1. **Exécuter les tests** : `npm run cypress:open`
2. **Tester l'accessibilité** : Utiliser NVDA/VoiceOver
3. **Ajouter vos tests** : Créer `cypress/e2e/my-feature.cy.js`
4. **Utiliser les composants** : Importer Select, Modal, DataTable

## 💡 Conseils

- Toujours ajouter `data-testid` sur les éléments importants
- Utiliser les commandes personnalisées (`cy.mockFinanceAPI()`)
- Tester l'accessibilité dès le début du développement
- Documenter les nouveaux patterns accessibles
- Vérifier le contraste des couleurs (ratio 4.5:1)
- Tester avec un vrai lecteur d'écran

## 🆘 Support

- **Issues** : Créer une issue sur le dépôt
- **Documentation** : Lire les fichiers .md dans `/frontend`
- **Exemples** : Voir `finance.cy.js` pour des exemples de tests

---

**Tout est prêt à l'emploi !** 🎉

Les composants sont accessibles WCAG 2.1 AA et les tests E2E sont opérationnels.
