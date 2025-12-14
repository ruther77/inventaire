import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import {
  EmptyTransactions,
  EmptyInvoices,
  EmptyProducts,
  EmptyAnomalies,
  EmptyForecasts,
  EmptySuppliers,
  EmptyReconciliation,
  EmptyStock,
  EmptyReports,
  EmptySearchResults,
  EmptyFilteredResults,
} from './ActionableEmptyStates';

describe('EmptyTransactions', () => {
  it('renders correctly', () => {
    render(<EmptyTransactions />);
    expect(screen.getByText('Aucune transaction')).toBeInTheDocument();
  });

  it('renders import button when onImport is provided', () => {
    const handleImport = vi.fn();
    render(<EmptyTransactions onImport={handleImport} />);
    expect(screen.getByRole('button', { name: /importer un relevé/i })).toBeInTheDocument();
  });

  it('renders refresh button when onRefresh is provided', () => {
    const handleRefresh = vi.fn();
    render(<EmptyTransactions onRefresh={handleRefresh} />);
    expect(screen.getByRole('button', { name: /rafraîchir/i })).toBeInTheDocument();
  });

  it('calls onImport when import button is clicked', async () => {
    const handleImport = vi.fn();
    render(<EmptyTransactions onImport={handleImport} />);

    await userEvent.click(screen.getByRole('button', { name: /importer/i }));
    expect(handleImport).toHaveBeenCalledTimes(1);
  });
});

describe('EmptyInvoices', () => {
  it('renders correctly', () => {
    render(<EmptyInvoices />);
    expect(screen.getByText('Aucune facture importée')).toBeInTheDocument();
  });

  it('renders upload button when onUpload is provided', () => {
    render(<EmptyInvoices onUpload={() => {}} />);
    expect(screen.getByRole('button', { name: /importer une facture/i })).toBeInTheDocument();
  });

  it('renders history button when onViewHistory is provided', () => {
    render(<EmptyInvoices onViewHistory={() => {}} />);
    expect(screen.getByRole('button', { name: /historique/i })).toBeInTheDocument();
  });
});

describe('EmptyProducts', () => {
  it('renders correctly', () => {
    render(<EmptyProducts />);
    expect(screen.getByText('Catalogue vide')).toBeInTheDocument();
  });

  it('renders add button when onAdd is provided', () => {
    render(<EmptyProducts onAdd={() => {}} />);
    expect(screen.getByRole('button', { name: /ajouter un produit/i })).toBeInTheDocument();
  });

  it('renders import button when onImport is provided', () => {
    render(<EmptyProducts onImport={() => {}} />);
    expect(screen.getByRole('button', { name: /importer depuis facture/i })).toBeInTheDocument();
  });

  it('calls both actions correctly', async () => {
    const handleAdd = vi.fn();
    const handleImport = vi.fn();
    render(<EmptyProducts onAdd={handleAdd} onImport={handleImport} />);

    await userEvent.click(screen.getByRole('button', { name: /ajouter/i }));
    expect(handleAdd).toHaveBeenCalledTimes(1);

    await userEvent.click(screen.getByRole('button', { name: /importer/i }));
    expect(handleImport).toHaveBeenCalledTimes(1);
  });
});

describe('EmptyAnomalies', () => {
  it('renders correctly with positive message', () => {
    render(<EmptyAnomalies />);
    expect(screen.getByText('Aucune anomalie détectée')).toBeInTheDocument();
    expect(screen.getByText(/activité est saine/i)).toBeInTheDocument();
  });

  it('renders configure button when onConfigure is provided', () => {
    render(<EmptyAnomalies onConfigure={() => {}} />);
    expect(screen.getByRole('button', { name: /configurer/i })).toBeInTheDocument();
  });
});

describe('EmptyForecasts', () => {
  it('renders correctly', () => {
    render(<EmptyForecasts />);
    expect(screen.getByText('Prévisions indisponibles')).toBeInTheDocument();
    expect(screen.getByText(/pas assez de données/i)).toBeInTheDocument();
  });

  it('renders refresh button when onRefresh is provided', () => {
    render(<EmptyForecasts onRefresh={() => {}} />);
    expect(screen.getByRole('button', { name: /actualiser/i })).toBeInTheDocument();
  });
});

describe('EmptySuppliers', () => {
  it('renders correctly', () => {
    render(<EmptySuppliers />);
    expect(screen.getByText('Aucun fournisseur référencé')).toBeInTheDocument();
  });

  it('renders import invoice button when onImportInvoice is provided', () => {
    render(<EmptySuppliers onImportInvoice={() => {}} />);
    expect(screen.getByRole('button', { name: /importer une facture/i })).toBeInTheDocument();
  });
});

describe('EmptyReconciliation', () => {
  it('renders correctly', () => {
    render(<EmptyReconciliation />);
    expect(screen.getByText('Rien à rapprocher')).toBeInTheDocument();
  });

  it('renders both import buttons when callbacks are provided', () => {
    render(
      <EmptyReconciliation
        onImportStatement={() => {}}
        onImportInvoice={() => {}}
      />
    );
    expect(screen.getByRole('button', { name: /importer relevé/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /importer facture/i })).toBeInTheDocument();
  });
});

describe('EmptyStock', () => {
  it('renders correctly', () => {
    render(<EmptyStock />);
    expect(screen.getByText('Stock vide')).toBeInTheDocument();
  });

  it('renders import invoice button when onImportInvoice is provided', () => {
    render(<EmptyStock onImportInvoice={() => {}} />);
    expect(screen.getByRole('button', { name: /importer une facture/i })).toBeInTheDocument();
  });
});

describe('EmptyReports', () => {
  it('renders correctly', () => {
    render(<EmptyReports />);
    expect(screen.getByText('Aucun rapport disponible')).toBeInTheDocument();
  });

  it('renders generate button when onGenerate is provided', () => {
    render(<EmptyReports onGenerate={() => {}} />);
    expect(screen.getByRole('button', { name: /générer/i })).toBeInTheDocument();
  });
});

describe('EmptySearchResults', () => {
  it('renders with query', () => {
    render(<EmptySearchResults query="test search" />);
    expect(screen.getByText(/aucun résultat pour "test search"/i)).toBeInTheDocument();
  });

  it('renders clear button when onClear is provided', () => {
    render(<EmptySearchResults query="test" onClear={() => {}} />);
    expect(screen.getByRole('button', { name: /effacer/i })).toBeInTheDocument();
  });

  it('calls onClear when clear button is clicked', async () => {
    const handleClear = vi.fn();
    render(<EmptySearchResults query="test" onClear={handleClear} />);

    await userEvent.click(screen.getByRole('button', { name: /effacer/i }));
    expect(handleClear).toHaveBeenCalledTimes(1);
  });
});

describe('EmptyFilteredResults', () => {
  it('renders correctly', () => {
    render(<EmptyFilteredResults />);
    expect(screen.getByText('Aucun résultat')).toBeInTheDocument();
    expect(screen.getByText(/filtres actuels/i)).toBeInTheDocument();
  });

  it('renders reset button when onReset is provided', () => {
    render(<EmptyFilteredResults onReset={() => {}} />);
    expect(screen.getByRole('button', { name: /réinitialiser/i })).toBeInTheDocument();
  });

  it('calls onReset when reset button is clicked', async () => {
    const handleReset = vi.fn();
    render(<EmptyFilteredResults onReset={handleReset} />);

    await userEvent.click(screen.getByRole('button', { name: /réinitialiser/i }));
    expect(handleReset).toHaveBeenCalledTimes(1);
  });
});
