import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Package, Search, AlertTriangle } from 'lucide-react';
import EmptyState, {
  EmptySearch,
  EmptyList,
  EmptyError,
  EmptyData,
} from './EmptyState';

describe('EmptyState', () => {
  it('renders with default props', () => {
    render(<EmptyState />);
    expect(screen.getByText('Aucun élément')).toBeInTheDocument();
  });

  it('renders custom title', () => {
    render(<EmptyState title="No Results Found" />);
    expect(screen.getByText('No Results Found')).toBeInTheDocument();
  });

  it('renders description', () => {
    render(<EmptyState description="Try adjusting your filters" />);
    expect(screen.getByText('Try adjusting your filters')).toBeInTheDocument();
  });

  it('renders custom icon', () => {
    const CustomIcon = ({ className }) => (
      <span data-testid="custom-icon" className={className}>Icon</span>
    );
    render(<EmptyState icon={CustomIcon} />);
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
  });

  it('renders action buttons', async () => {
    const handleClick = vi.fn();
    render(
      <EmptyState
        title="No Items"
        actions={[{ label: 'Add Item', onClick: handleClick }]}
      />
    );

    const button = screen.getByRole('button', { name: 'Add Item' });
    expect(button).toBeInTheDocument();

    await userEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders multiple action buttons', () => {
    render(
      <EmptyState
        actions={[
          { label: 'Primary Action', variant: 'brand' },
          { label: 'Secondary Action', variant: 'ghost' },
        ]}
      />
    );

    expect(screen.getByRole('button', { name: 'Primary Action' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Secondary Action' })).toBeInTheDocument();
  });

  it('applies small size styles', () => {
    const { container } = render(<EmptyState size="sm" />);
    expect(container.firstChild).toHaveClass('py-6');
  });

  it('applies medium size styles by default', () => {
    const { container } = render(<EmptyState />);
    expect(container.firstChild).toHaveClass('py-10');
  });

  it('applies large size styles', () => {
    const { container } = render(<EmptyState size="lg" />);
    expect(container.firstChild).toHaveClass('py-16');
  });

  it('applies custom className', () => {
    const { container } = render(<EmptyState className="my-custom-class" />);
    expect(container.firstChild).toHaveClass('my-custom-class');
  });

  it('renders action with icon', () => {
    const ActionIcon = () => <span data-testid="action-icon" />;
    render(
      <EmptyState
        actions={[{ label: 'With Icon', icon: ActionIcon }]}
      />
    );

    expect(screen.getByTestId('action-icon')).toBeInTheDocument();
  });

  it('handles disabled action', () => {
    render(
      <EmptyState
        actions={[{ label: 'Disabled', disabled: true }]}
      />
    );

    expect(screen.getByRole('button', { name: 'Disabled' })).toBeDisabled();
  });

  it('handles loading action', () => {
    render(
      <EmptyState
        actions={[{ label: 'Loading', loading: true }]}
      />
    );

    const button = screen.getByRole('button', { name: 'Loading' });
    expect(button).toHaveAttribute('aria-busy', 'true');
  });
});

describe('EmptySearch', () => {
  it('renders search-specific content', () => {
    render(<EmptySearch />);
    expect(screen.getByText('Aucun résultat')).toBeInTheDocument();
    expect(screen.getByText(/modifier vos critères/i)).toBeInTheDocument();
  });

  it('renders reset button when onReset is provided', () => {
    const handleReset = vi.fn();
    render(<EmptySearch onReset={handleReset} />);
    expect(screen.getByRole('button', { name: /réinitialiser/i })).toBeInTheDocument();
  });

  it('does not render reset button when onReset is not provided', () => {
    render(<EmptySearch />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('calls onReset when button is clicked', async () => {
    const handleReset = vi.fn();
    render(<EmptySearch onReset={handleReset} />);

    await userEvent.click(screen.getByRole('button', { name: /réinitialiser/i }));
    expect(handleReset).toHaveBeenCalledTimes(1);
  });

  it('applies custom className', () => {
    const { container } = render(<EmptySearch className="my-class" />);
    expect(container.firstChild).toHaveClass('my-class');
  });
});

describe('EmptyList', () => {
  it('renders with default item name', () => {
    render(<EmptyList />);
    expect(screen.getByText('Aucun élément')).toBeInTheDocument();
    expect(screen.getByText(/premier élément/i)).toBeInTheDocument();
  });

  it('renders with custom item name', () => {
    render(<EmptyList itemName="produit" />);
    expect(screen.getByText('Aucun produit')).toBeInTheDocument();
    expect(screen.getByText(/premier produit/i)).toBeInTheDocument();
  });

  it('renders add button when onAdd is provided', () => {
    render(<EmptyList itemName="article" onAdd={() => {}} />);
    expect(screen.getByRole('button', { name: /ajouter un article/i })).toBeInTheDocument();
  });

  it('calls onAdd when button is clicked', async () => {
    const handleAdd = vi.fn();
    render(<EmptyList itemName="item" onAdd={handleAdd} />);

    await userEvent.click(screen.getByRole('button', { name: /ajouter/i }));
    expect(handleAdd).toHaveBeenCalledTimes(1);
  });

  it('applies custom className', () => {
    const { container } = render(<EmptyList className="custom" />);
    expect(container.firstChild).toHaveClass('custom');
  });
});

describe('EmptyError', () => {
  it('renders error-specific content', () => {
    render(<EmptyError />);
    expect(screen.getByText('Une erreur est survenue')).toBeInTheDocument();
    expect(screen.getByText(/impossible de charger/i)).toBeInTheDocument();
  });

  it('renders retry button when onRetry is provided', () => {
    render(<EmptyError onRetry={() => {}} />);
    expect(screen.getByRole('button', { name: /réessayer/i })).toBeInTheDocument();
  });

  it('does not render retry button when onRetry is not provided', () => {
    render(<EmptyError />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('calls onRetry when button is clicked', async () => {
    const handleRetry = vi.fn();
    render(<EmptyError onRetry={handleRetry} />);

    await userEvent.click(screen.getByRole('button', { name: /réessayer/i }));
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it('applies custom className', () => {
    const { container } = render(<EmptyError className="error-class" />);
    expect(container.firstChild).toHaveClass('error-class');
  });
});

describe('EmptyData', () => {
  it('renders data-specific content', () => {
    render(<EmptyData />);
    expect(screen.getByText('Pas de données disponibles')).toBeInTheDocument();
    expect(screen.getByText(/données apparaîtront/i)).toBeInTheDocument();
  });

  it('does not render action buttons', () => {
    render(<EmptyData />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<EmptyData className="data-class" />);
    expect(container.firstChild).toHaveClass('data-class');
  });
});
