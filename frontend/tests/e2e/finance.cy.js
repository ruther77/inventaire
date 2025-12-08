// Cypress e2e minimal: vérifie qu'on peut charger l'overview finance et la page règles (smoke).

describe('Finance UI smoke', () => {
  it('Charge overview et règles', () => {
    cy.visit('http://localhost:5175');
    // Supposer auth déjà gérée (token en localstorage) ou page login
    cy.contains('Trésorerie', { timeout: 10000 });
    cy.visit('http://localhost:5175/finance-rules');
    cy.contains('Gestion des règles');
    cy.visit('http://localhost:5175/finance-anomalies');
    cy.contains('Anomalies & matches');
    cy.visit('http://localhost:5175/finance-imports');
    cy.contains('Historique des imports');
  });
});
