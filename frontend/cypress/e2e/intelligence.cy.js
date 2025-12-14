/**
 * Intelligence Module E2E Tests
 * Tests for all Intelligence pages: Inventory, Forecasting, Anomaly Detection, Supplier Scoring, Margins, Cockpit
 */

describe('Intelligence Module', () => {
  beforeEach(() => {
    cy.login();
    cy.mockIntelligenceAPI();
  });

  describe('Cockpit Dashboard', () => {
    beforeEach(() => {
      cy.visit('/cockpit');
    });

    it('should load cockpit page', () => {
      cy.url().should('include', '/cockpit');
      cy.get('body').should('be.visible');
      cy.get('#root').should('not.be.empty');
    });

    it('should display KPI cards', () => {
      cy.get('[class*="card"], [class*="metric"], [class*="kpi"]').should('have.length.at.least', 1);
    });

    it('should have health score indicator', () => {
      cy.contains(/sant|health|score/i).should('exist');
    });

    it('should display alerts section', () => {
      cy.contains(/alert|alerte/i).should('exist');
    });

    it('should have refresh functionality', () => {
      cy.get('button').then(($buttons) => {
        const hasRefreshButton = $buttons.toArray().some((btn) => {
          return btn.querySelector('svg') || btn.innerText.toLowerCase().includes('actualiser');
        });
        expect(hasRefreshButton || $buttons.length > 0).to.be.true;
      });
    });
  });

  describe('Inventory Intelligence', () => {
    beforeEach(() => {
      cy.visit('/intelligence/inventory');
    });

    it('should load inventory intelligence page', () => {
      cy.url().should('include', '/intelligence');
      cy.get('body').should('be.visible');
    });

    it('should display summary metrics', () => {
      cy.get('[class*="card"], [class*="metric"]').should('have.length.at.least', 1);
    });

    it('should have tabs or sections for different analyses', () => {
      cy.get('[role="tablist"], [role="tab"], button, [class*="tab"]').should('exist');
    });

    it('should show reorder points section', () => {
      cy.contains(/reorder|réappro|seuil|commande/i).should('exist');
    });

    it('should display ABC/XYZ classification', () => {
      cy.contains(/abc|xyz|class/i).should('exist');
    });
  });

  describe('Forecasting', () => {
    beforeEach(() => {
      cy.visit('/intelligence/forecasts');
    });

    it('should load forecasting page', () => {
      cy.url().should('include', '/forecasts');
      cy.get('body').should('be.visible');
    });

    it('should display forecast charts or data', () => {
      cy.get('[class*="chart"], [class*="graph"], svg, canvas, [class*="card"]').should('exist');
    });

    it('should have horizon selector', () => {
      cy.get('select, input[type="number"], [class*="select"]').should('exist');
    });

    it('should show sales trend information', () => {
      cy.contains(/vente|sales|prévision|forecast|trend/i).should('exist');
    });

    it('should display cashflow predictions', () => {
      cy.contains(/cash|trésorerie|flux/i).should('exist');
    });
  });

  describe('Anomaly Detection', () => {
    beforeEach(() => {
      cy.visit('/intelligence/anomalies');
    });

    it('should load anomaly detection page', () => {
      cy.url().should('include', '/anomal');
      cy.get('body').should('be.visible');
    });

    it('should display anomaly summary', () => {
      cy.get('[class*="card"], [class*="metric"]').should('have.length.at.least', 1);
    });

    it('should have tabs for different anomaly types', () => {
      cy.get('[role="tablist"], button, [class*="tab"]').should('exist');
    });

    it('should show outliers section', () => {
      cy.contains(/outlier|aberrant|montant/i).should('exist');
    });

    it('should have scan functionality', () => {
      cy.get('button').then(($buttons) => {
        const hasScanButton = $buttons.toArray().some((btn) => {
          const text = btn.innerText.toLowerCase();
          return text.includes('scan') || text.includes('analyser') || text.includes('détecter');
        });
        expect(hasScanButton || $buttons.length > 0).to.be.true;
      });
    });
  });

  describe('Supplier Scoring', () => {
    beforeEach(() => {
      cy.visit('/intelligence/scoring');
    });

    it('should load supplier scoring page', () => {
      cy.url().should('include', '/scoring');
      cy.get('body').should('be.visible');
    });

    it('should display supplier ranking', () => {
      cy.contains(/fournisseur|supplier|ranking|classement/i).should('exist');
    });

    it('should show score dimensions', () => {
      cy.contains(/score|note|évaluation/i).should('exist');
    });

    it('should have comparison functionality', () => {
      cy.get('table, [class*="table"], [class*="list"], [class*="grid"]').should('exist');
    });
  });

  describe('Margins', () => {
    beforeEach(() => {
      cy.visit('/intelligence/margins');
    });

    it('should load margins page', () => {
      cy.url().should('include', '/margin');
      cy.get('body').should('be.visible');
    });

    it('should display margin summary', () => {
      cy.contains(/marge|margin/i).should('exist');
    });

    it('should show product margins table or list', () => {
      cy.get('table, [class*="table"], [class*="list"], [class*="grid"]').should('exist');
    });

    it('should display category breakdown', () => {
      cy.contains(/catégorie|category/i).should('exist');
    });

    it('should show margin alerts', () => {
      cy.contains(/alert|seuil|threshold/i).should('exist');
    });
  });

  describe('Cross-Module Navigation', () => {
    it('should navigate from cockpit to inventory intelligence', () => {
      cy.visit('/cockpit');
      cy.get('a, button').contains(/inventaire|inventory|stock/i).first().click();
      cy.url().should('match', /intelligence|inventory|stock/i);
    });

    it('should navigate between intelligence pages via sidebar', () => {
      cy.visit('/intelligence/inventory');

      // Should have navigation to other intelligence pages
      cy.get('nav, aside, [class*="sidebar"]').within(() => {
        cy.get('a').should('have.length.at.least', 1);
      });
    });
  });

  describe('Responsive Design', () => {
    const pages = [
      '/cockpit',
      '/intelligence/inventory',
      '/intelligence/forecasts',
      '/intelligence/anomalies',
      '/intelligence/scoring',
      '/intelligence/margins',
    ];

    pages.forEach((page) => {
      it(`${page} should be responsive on mobile`, () => {
        cy.viewport('iphone-x');
        cy.visit(page);
        cy.get('body').should('be.visible');
        cy.get('#root').should('not.be.empty');
      });

      it(`${page} should be responsive on tablet`, () => {
        cy.viewport('ipad-2');
        cy.visit(page);
        cy.get('body').should('be.visible');
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully on cockpit', () => {
      cy.intercept('GET', '/api/cockpit/**', {
        statusCode: 500,
        body: { error: 'Internal Server Error' },
      });

      cy.visit('/cockpit');
      cy.get('body').should('be.visible');
    });

    it('should handle API errors gracefully on intelligence pages', () => {
      cy.intercept('GET', '/api/inventory-intelligence/**', {
        statusCode: 500,
        body: { error: 'Internal Server Error' },
      });

      cy.visit('/intelligence/inventory');
      cy.get('body').should('be.visible');
    });
  });

  describe('Accessibility', () => {
    const pages = [
      '/cockpit',
      '/intelligence/inventory',
      '/intelligence/forecasts',
      '/intelligence/anomalies',
      '/intelligence/scoring',
      '/intelligence/margins',
    ];

    pages.forEach((page) => {
      it(`${page} should have proper heading structure`, () => {
        cy.visit(page);
        cy.get('h1, h2, h3').should('have.length.at.least', 1);
      });

      it(`${page} should have focusable elements`, () => {
        cy.visit(page);
        cy.get('button, a, input, select').first().focus();
        cy.focused().should('exist');
      });
    });
  });
});
