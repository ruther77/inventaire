// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************

// Custom command to login - uses cy.session to persist auth across visits
Cypress.Commands.add('login', (username = 'admin', role = 'admin') => {
  cy.session(
    [username, role],
    () => {
      const mockSession = {
        token: 'mock-jwt-token-for-cypress-tests',
        user: {
          id: 1,
          username: username,
          role: role,
          tenant_id: 1,
          tenant_code: 'epicerie',
        },
      };

      // Set localStorage directly
      window.localStorage.setItem('auth/session', JSON.stringify(mockSession));
      window.localStorage.setItem('tenant/current', 'epicerie');
    },
    {
      validate() {
        // Validate session exists
        const session = window.localStorage.getItem('auth/session');
        return session !== null;
      },
    }
  );
});

// Custom command to intercept API calls
Cypress.Commands.add('mockFinanceAPI', () => {
  cy.intercept('GET', '/api/finance/transactions*', {
    fixture: 'transactions.json',
  }).as('getTransactions');

  cy.intercept('GET', '/api/finance/anomalies*', {
    fixture: 'anomalies.json',
  }).as('getAnomalies');

  cy.intercept('GET', '/api/finance/rules*', {
    fixture: 'rules.json',
  }).as('getRules');
});

// Custom command to check accessibility
Cypress.Commands.add('checkA11y', (context = null, options = null) => {
  // This would integrate with cypress-axe if installed
  // For now, we'll do basic checks
  cy.get('[role]').should('exist');
});

// Custom command to wait for data table to load
Cypress.Commands.add('waitForTable', (testId = 'data-table') => {
  cy.get(`[data-testid="${testId}"]`).should('exist');
  cy.get('.animate-spin').should('not.exist'); // Wait for loading to finish
});
