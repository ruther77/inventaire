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

// Custom command to intercept Intelligence API calls
Cypress.Commands.add('mockIntelligenceAPI', () => {
  // Cockpit
  cy.intercept('GET', '/api/cockpit/overview*', {
    fixture: 'cockpit.json',
    delayMs: 100,
  }).as('getCockpitOverview');

  cy.intercept('GET', '/api/cockpit/kpis/live*', {
    body: { revenue_today: 2450, orders_today: 45, avg_ticket: 54.44, stock_alerts: 3 },
  }).as('getCockpitKPIs');

  cy.intercept('GET', '/api/cockpit/alerts*', {
    fixture: 'cockpit.json',
    delayMs: 50,
  }).as('getCockpitAlerts');

  cy.intercept('GET', '/api/cockpit/health*', {
    body: { score: 85, components: { stock: 78, margins: 92, cashflow: 88 } },
  }).as('getCockpitHealth');

  // Inventory Intelligence
  cy.intercept('GET', '/api/inventory-intelligence/summary*', {
    fixture: 'intelligence.json',
  }).as('getInventorySummary');

  cy.intercept('GET', '/api/inventory-intelligence/reorder-points*', {
    fixture: 'intelligence.json',
  }).as('getReorderPoints');

  cy.intercept('GET', '/api/inventory-intelligence/stockout-predictions*', {
    fixture: 'intelligence.json',
  }).as('getStockoutPredictions');

  cy.intercept('GET', '/api/inventory-intelligence/dead-stock*', {
    fixture: 'intelligence.json',
  }).as('getDeadStock');

  cy.intercept('GET', '/api/inventory-intelligence/abc-xyz*', {
    fixture: 'intelligence.json',
  }).as('getABCXYZ');

  cy.intercept('GET', '/api/inventory-intelligence/reorder-suggestions*', {
    fixture: 'intelligence.json',
  }).as('getReorderSuggestions');

  // Forecasting
  cy.intercept('GET', '/api/forecasting/summary*', {
    fixture: 'forecasting.json',
  }).as('getForecastingSummary');

  cy.intercept('GET', '/api/forecasting/cash-flow*', {
    fixture: 'forecasting.json',
  }).as('getCashFlowForecast');

  cy.intercept('GET', '/api/forecasting/stock-depletion*', {
    fixture: 'forecasting.json',
  }).as('getStockDepletion');

  cy.intercept('POST', '/api/forecasting/sales*', {
    fixture: 'forecasting.json',
  }).as('forecastSales');

  // Anomaly Detection
  cy.intercept('GET', '/api/anomaly-detection/summary*', {
    fixture: 'anomaly-detection.json',
  }).as('getAnomalySummary');

  cy.intercept('GET', '/api/anomaly-detection/transactions/outliers*', {
    fixture: 'anomaly-detection.json',
  }).as('getOutliers');

  cy.intercept('GET', '/api/anomaly-detection/invoices/duplicates*', {
    fixture: 'anomaly-detection.json',
  }).as('getDuplicates');

  cy.intercept('GET', '/api/anomaly-detection/transactions/round-amounts*', {
    fixture: 'anomaly-detection.json',
  }).as('getRoundAmounts');

  cy.intercept('GET', '/api/anomaly-detection/scan*', {
    fixture: 'anomaly-detection.json',
  }).as('scanAnomalies');

  // Supplier Scoring
  cy.intercept('GET', '/api/supplier-scoring/ranking*', {
    fixture: 'supplier-scoring.json',
  }).as('getSuppliersRanking');

  cy.intercept('GET', '/api/supplier-scoring/dimensions*', {
    fixture: 'supplier-scoring.json',
  }).as('getScoringDimensions');

  cy.intercept('GET', '/api/supplier-scoring/score/*', {
    fixture: 'supplier-scoring.json',
  }).as('getSupplierScore');

  // Margins
  cy.intercept('GET', '/api/margins/summary*', {
    fixture: 'margins.json',
  }).as('getMarginSummary');

  cy.intercept('GET', '/api/margins/products*', {
    fixture: 'margins.json',
  }).as('getProductMargins');

  cy.intercept('GET', '/api/margins/categories*', {
    fixture: 'margins.json',
  }).as('getCategoryMargins');

  cy.intercept('GET', '/api/margins/alerts*', {
    fixture: 'margins.json',
  }).as('getMarginAlerts');
});

// Custom command to mock Dashboard API calls
Cypress.Commands.add('mockDashboardAPI', () => {
  cy.intercept('GET', '/api/dashboard/metrics*', {
    fixture: 'dashboard.json',
  }).as('getDashboardMetrics');

  cy.intercept('GET', '/api/dashboard/recent-movements*', {
    fixture: 'dashboard.json',
  }).as('getRecentMovements');

  cy.intercept('GET', '/api/dashboard/top-products*', {
    fixture: 'dashboard.json',
  }).as('getTopProducts');

  cy.intercept('GET', '/api/dashboard/alerts*', {
    fixture: 'dashboard.json',
  }).as('getDashboardAlerts');
});

// Custom command to mock Products/Catalog API calls
Cypress.Commands.add('mockProductsAPI', () => {
  cy.intercept('GET', '/api/catalog/products*', {
    fixture: 'products.json',
  }).as('getProducts');

  cy.intercept('GET', '/api/catalog/categories*', {
    body: { categories: ['Fruits & Légumes', 'Épicerie', 'Boulangerie', 'Crémerie', 'Boissons'] },
  }).as('getCategories');

  cy.intercept('GET', '/api/catalog/vendors*', {
    body: { vendors: ['Metro', 'Pomona', 'Lactalis', 'Boulangerie Locale'] },
  }).as('getVendors');

  cy.intercept('POST', '/api/catalog/products', {
    statusCode: 201,
    body: { id: 100, message: 'Product created' },
  }).as('createProduct');

  cy.intercept('PUT', '/api/catalog/products/*', {
    statusCode: 200,
    body: { message: 'Product updated' },
  }).as('updateProduct');
});

// Custom command to mock Invoices API calls
Cypress.Commands.add('mockInvoicesAPI', () => {
  cy.intercept('GET', '/api/invoices*', {
    fixture: 'invoices.json',
  }).as('getInvoices');

  cy.intercept('GET', '/api/invoices/history*', {
    fixture: 'invoices.json',
  }).as('getInvoicesHistory');

  cy.intercept('GET', '/api/invoices/summary*', {
    fixture: 'invoices.json',
  }).as('getInvoicesSummary');

  cy.intercept('POST', '/api/invoices/import', {
    statusCode: 200,
    body: { success: true, imported: 1, invoice_id: 101 },
    delayMs: 500,
  }).as('importInvoice');

  cy.intercept('POST', '/api/invoices/validate/*', {
    statusCode: 200,
    body: { message: 'Invoice validated' },
  }).as('validateInvoice');
});

// Custom command to mock Stock API calls
Cypress.Commands.add('mockStockAPI', () => {
  cy.intercept('GET', '/api/stock/summary*', {
    fixture: 'stock.json',
  }).as('getStockSummary');

  cy.intercept('GET', '/api/stock/movements*', {
    fixture: 'stock.json',
  }).as('getStockMovements');

  cy.intercept('GET', '/api/stock/movements/timeseries*', {
    fixture: 'stock.json',
  }).as('getStockTimeseries');

  cy.intercept('GET', '/api/stock/alerts*', {
    fixture: 'stock.json',
  }).as('getStockAlerts');

  cy.intercept('POST', '/api/stock/adjustment', {
    statusCode: 200,
    body: { success: true, movement_id: 100 },
  }).as('createAdjustment');
});

// Custom command to mock Reports API calls
Cypress.Commands.add('mockReportsAPI', () => {
  cy.intercept('GET', '/api/reports/overview*', {
    fixture: 'reports.json',
  }).as('getReportsOverview');

  cy.intercept('GET', '/api/reports/available*', {
    fixture: 'reports.json',
  }).as('getAvailableReports');

  cy.intercept('GET', '/api/reports/exports*', {
    fixture: 'reports.json',
  }).as('getRecentExports');

  cy.intercept('POST', '/api/reports/generate/*', {
    statusCode: 200,
    body: { job_id: 'job-123', status: 'processing' },
    delayMs: 300,
  }).as('generateReport');

  cy.intercept('GET', '/api/reports/exports/*', {
    statusCode: 200,
    headers: { 'Content-Type': 'application/octet-stream' },
    body: new Blob(['test']),
  }).as('downloadReport');
});

// Custom command to mock Bank Reconciliation API calls
Cypress.Commands.add('mockBankReconciliationAPI', () => {
  cy.intercept('GET', '/api/bank-reconciliation/summary*', {
    fixture: 'bank-reconciliation.json',
  }).as('getBankRecoSummary');

  cy.intercept('GET', '/api/bank-reconciliation/unmatched*', {
    fixture: 'bank-reconciliation.json',
  }).as('getUnmatchedTransactions');

  cy.intercept('GET', '/api/bank-reconciliation/aliases*', {
    fixture: 'bank-reconciliation.json',
  }).as('getSupplierAliases');

  cy.intercept('POST', '/api/bank-reconciliation/match', {
    statusCode: 200,
    body: { success: true, match_id: 100 },
  }).as('createMatch');

  cy.intercept('POST', '/api/bank-reconciliation/aliases', {
    statusCode: 201,
    body: { success: true, alias_id: 10 },
  }).as('createAlias');
});

// Custom command to mock Audit Trail API calls
Cypress.Commands.add('mockAuditTrailAPI', () => {
  cy.intercept('GET', '/api/audit-trail/summary*', {
    fixture: 'audit-trail.json',
  }).as('getAuditSummary');

  cy.intercept('GET', '/api/audit-trail/entries*', {
    fixture: 'audit-trail.json',
  }).as('getAuditEntries');

  cy.intercept('GET', '/api/audit-trail/security-events*', {
    fixture: 'audit-trail.json',
  }).as('getSecurityEvents');

  cy.intercept('GET', '/api/audit-trail/user-activity*', {
    fixture: 'audit-trail.json',
  }).as('getUserActivity');
});

// Combined command to mock all APIs at once
Cypress.Commands.add('mockAllAPIs', () => {
  cy.mockFinanceAPI();
  cy.mockIntelligenceAPI();
  cy.mockDashboardAPI();
  cy.mockProductsAPI();
  cy.mockInvoicesAPI();
  cy.mockStockAPI();
  cy.mockReportsAPI();
  cy.mockBankReconciliationAPI();
  cy.mockAuditTrailAPI();
});
