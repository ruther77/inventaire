import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import Modal, { ConfirmDialog } from './Modal';

describe('Modal', () => {
  const defaultProps = {
    open: true,
    title: 'Test Modal',
    onClose: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    document.body.style.overflow = '';
  });

  it('renders when open is true', () => {
    render(<Modal {...defaultProps} />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
  });

  it('does not render when open is false', () => {
    render(<Modal {...defaultProps} open={false} />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('displays title and description', () => {
    render(
      <Modal {...defaultProps} description="This is a description" />
    );
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('This is a description')).toBeInTheDocument();
  });

  it('renders children content', () => {
    render(
      <Modal {...defaultProps}>
        <p>Modal content</p>
      </Modal>
    );
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const onClose = vi.fn();
    render(<Modal {...defaultProps} onClose={onClose} />);

    const closeButton = screen.getByRole('button', { name: /fermer/i });
    await userEvent.click(closeButton);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when Escape key is pressed', () => {
    const onClose = vi.fn();
    render(<Modal {...defaultProps} onClose={onClose} />);

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when overlay is clicked', async () => {
    const onClose = vi.fn();
    render(<Modal {...defaultProps} onClose={onClose} />);

    const overlay = screen.getByRole('presentation');
    await userEvent.click(overlay);

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('does not call onClose when overlay click is disabled', async () => {
    const onClose = vi.fn();
    render(
      <Modal {...defaultProps} onClose={onClose} closeOnOverlayClick={false} />
    );

    const overlay = screen.getByRole('presentation');
    await userEvent.click(overlay);

    expect(onClose).not.toHaveBeenCalled();
  });

  it('hides close button when showCloseButton is false', () => {
    render(<Modal {...defaultProps} showCloseButton={false} />);
    expect(screen.queryByRole('button', { name: /fermer/i })).not.toBeInTheDocument();
  });

  it('renders action buttons', async () => {
    const handleAction = vi.fn();
    render(
      <Modal
        {...defaultProps}
        actions={[
          { label: 'Cancel', variant: 'ghost', onClick: vi.fn() },
          { label: 'Confirm', variant: 'brand', onClick: handleAction },
        ]}
      />
    );

    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }));
    expect(handleAction).toHaveBeenCalledTimes(1);
  });

  it('applies correct size class', () => {
    const { rerender } = render(<Modal {...defaultProps} size="sm" />);
    expect(screen.getByRole('dialog')).toHaveClass('max-w-md');

    rerender(<Modal {...defaultProps} size="xl" />);
    expect(screen.getByRole('dialog')).toHaveClass('max-w-4xl');
  });

  it('prevents body scroll when open', () => {
    render(<Modal {...defaultProps} />);
    expect(document.body.style.overflow).toBe('hidden');
  });

  it('restores body scroll when closed', () => {
    const { rerender } = render(<Modal {...defaultProps} />);
    expect(document.body.style.overflow).toBe('hidden');

    rerender(<Modal {...defaultProps} open={false} />);
    expect(document.body.style.overflow).toBe('');
  });

  it('has correct ARIA attributes', () => {
    render(
      <Modal {...defaultProps} description="Description text" />
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby');
    expect(dialog).toHaveAttribute('aria-describedby');
  });
});

describe('ConfirmDialog', () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    onConfirm: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with default props', () => {
    render(<ConfirmDialog {...defaultProps} />);
    expect(screen.getByText("Confirmer l'action")).toBeInTheDocument();
    expect(screen.getByText('Êtes-vous sûr de vouloir continuer ?')).toBeInTheDocument();
  });

  it('renders custom title and description', () => {
    render(
      <ConfirmDialog
        {...defaultProps}
        title="Delete Item"
        description="This action cannot be undone."
      />
    );
    expect(screen.getByText('Delete Item')).toBeInTheDocument();
    expect(screen.getByText('This action cannot be undone.')).toBeInTheDocument();
  });

  it('calls onConfirm when confirm button is clicked', async () => {
    const onConfirm = vi.fn();
    render(<ConfirmDialog {...defaultProps} onConfirm={onConfirm} />);

    await userEvent.click(screen.getByRole('button', { name: 'Confirmer' }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when cancel button is clicked', async () => {
    const onClose = vi.fn();
    render(<ConfirmDialog {...defaultProps} onClose={onClose} />);

    await userEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('renders custom button labels', () => {
    render(
      <ConfirmDialog
        {...defaultProps}
        confirmLabel="Delete"
        cancelLabel="Keep"
      />
    );
    expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Keep' })).toBeInTheDocument();
  });

  it('shows loading state on confirm button', () => {
    render(<ConfirmDialog {...defaultProps} loading />);
    const confirmButton = screen.getByRole('button', { name: 'Confirmer' });
    expect(confirmButton).toHaveAttribute('aria-busy', 'true');
  });
});
