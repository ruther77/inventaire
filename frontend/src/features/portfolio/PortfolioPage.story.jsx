import PortfolioPage from './PortfolioPage.jsx';

const demoData = {
  tenants: [
    {
      tenant_id: 1,
      code: 'epicerie',
      name: 'Épicerie HQ',
      stock_value: 12000,
      bank_balance: 3500,
      cash_balance: 450,
      total_assets: 15950,
      snapshot_date: '2025-11-13T02:46:00Z',
    },
    {
      tenant_id: 2,
      code: 'restaurant',
      name: 'Restaurant HQ',
      stock_value: 8500,
      bank_balance: 1200,
      cash_balance: 150,
      total_assets: 9850,
      snapshot_date: '2025-11-13T02:46:05Z',
    },
  ],
  global_summary: {
    stock_value: 20500,
    bank_balance: 4700,
    cash_balance: 600,
    total_assets: 25800,
    snapshot_date: '2025-11-13T02:46:10Z',
  },
  latest_prices: [
    {
      code: 'EAN-001',
      fournisseur: 'Fournisseur A',
      prix_achat: 12.5,
      quantite: 4,
      facture_date: '2025-11-10T10:00:00Z',
      source_context: 'Facture',
      created_at: '2025-11-10T10:00:00Z',
    },
    {
      code: 'EAN-002',
      fournisseur: 'Fournisseur B',
      prix_achat: 8,
      quantite: 10,
      facture_date: '2025-11-11T20:30:00Z',
      source_context: 'Import',
      created_at: '2025-11-11T20:30:00Z',
    },
  ],
};

export const PortfolioPageDemo = () => <PortfolioPage initialData={demoData} />;

export default PortfolioPageDemo;
