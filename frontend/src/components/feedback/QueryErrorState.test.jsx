import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import QueryErrorState, { OfflineBanner } from './QueryErrorState';

// Mock useOnlineStatus
let mockIsOnline = true;
vi.mock('../../hooks/useQueryConfig.js', async () => {
  const actual = await vi.importActual('../../hooks/useQueryConfig.js');
  return {
    ...actual,
    useOnlineStatus: () => mockIsOnline,
  };
});

describe('QueryErrorState', () => {
  beforeEach(() => {
    mockIsOnline = true;
  });

  it('renders with default error message', () => {
    render(<QueryErrorState error={{ message: 'Test error' }} />);
    // Component displays errorMessages title/description, not the raw error message
    // For unknown errors, it shows "Une erreur est survenue"
    expect(screen.getByText('Une erreur est survenue')).toBeInTheDocument();
  });

  it('renders network error correctly', () => {
    const networkError = { message: 'Network error occurred' };
    render(<QueryErrorState error={networkError} />);
    expect(screen.getByText('Connexion impossible')).toBeInTheDocument();
  });

  it('renders auth error correctly', () => {
    const authError = { response: { status: 401 } };
    render(<QueryErrorState error={authError} />);
    expect(screen.getByText('Session expirée')).toBeInTheDocument();
  });

  it('renders server error correctly', () => {
    const serverError = { response: { status: 500 } };
    render(<QueryErrorState error={serverError} />);
    expect(screen.getByText('Erreur serveur')).toBeInTheDocument();
  });

  it('renders retry button when error is retryable', () => {
    const handleRetry = vi.fn();
    render(<QueryErrorState error={{ message: 'Test' }} onRetry={handleRetry} autoRetry={false} />);
    expect(screen.getByRole('button', { name: /réessayer/i })).toBeInTheDocument();
  });

  it('does not render retry for auth errors', () => {
    const authError = { response: { status: 401 } };
    render(<QueryErrorState error={authError} onRetry={() => {}} autoRetry={false} />);
    expect(screen.queryByRole('button', { name: /réessayer/i })).not.toBeInTheDocument();
  });

  it('renders in inline variant', () => {
    const { container } = render(
      <QueryErrorState error={{ message: 'Test' }} variant="inline" />
    );
    expect(container.firstChild).toHaveClass('flex', 'items-center');
  });

  it('renders in full variant', () => {
    const { container } = render(
      <QueryErrorState error={{ message: 'Test' }} variant="full" />
    );
    expect(container.firstChild).toHaveClass('min-h-[400px]');
  });

  it('renders in card variant by default', () => {
    const { container } = render(
      <QueryErrorState error={{ message: 'Test' }} />
    );
    expect(container.firstChild).toHaveClass('rounded-2xl', 'border');
  });

  it('applies custom className', () => {
    const { container } = render(
      <QueryErrorState error={{ message: 'Test' }} className="my-custom-class" />
    );
    expect(container.firstChild).toHaveClass('my-custom-class');
  });

  it('shows offline indicator when offline', () => {
    mockIsOnline = false;
    render(<QueryErrorState error={{ message: 'Test' }} variant="full" />);
    expect(screen.getByText(/hors ligne/i)).toBeInTheDocument();
  });
});

describe('OfflineBanner', () => {
  beforeEach(() => {
    mockIsOnline = true;
  });

  it('renders when offline', () => {
    mockIsOnline = false;
    render(<OfflineBanner />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/hors ligne/i)).toBeInTheDocument();
  });

  it('does not render when online', () => {
    mockIsOnline = true;
    const { container } = render(<OfflineBanner />);
    expect(container).toBeEmptyDOMElement();
  });

  it('applies custom className', () => {
    mockIsOnline = false;
    const { container } = render(<OfflineBanner className="my-class" />);
    expect(container.firstChild).toHaveClass('my-class');
  });
});
