import { useEffect, useId, useRef, useState, useCallback } from 'react';
import clsx from 'clsx';
import { X } from 'lucide-react';
import Button from './Button.jsx';

/**
 * Modal - Composant de dialogue accessible avec animations
 * WCAG 2.1 Level AA compliant
 *
 * Accessibility features:
 * - Focus trap (Tab key cycles through modal elements only)
 * - Focus management (restores focus on close)
 * - Keyboard navigation (Escape to close)
 * - ARIA attributes (role="dialog", aria-modal, aria-labelledby, aria-describedby)
 * - Screen reader announcements
 * - Body scroll lock with iOS compatibility
 * - Minimum touch target size (44x44px for close button)
 *
 * @param {boolean} open - Controls modal visibility
 * @param {string} title - Modal title (required for accessibility)
 * @param {string} description - Optional description
 * @param {ReactNode} children - Modal content
 * @param {Array} actions - Action buttons
 * @param {Function} onClose - Close handler
 * @param {string} size - Modal size (sm, md, lg, xl, full)
 * @param {boolean} closeOnOverlayClick - Allow closing by clicking overlay
 * @param {boolean} showCloseButton - Show close button
 */
export default function Modal({
  open,
  title,
  description,
  children,
  actions,
  onClose,
  size = 'md',
  closeOnOverlayClick = true,
  showCloseButton = true,
}) {
  const titleId = useId();
  const descriptionId = useId();
  const modalRef = useRef(null);
  const previousActiveElement = useRef(null);
  const scrollY = useRef(0);
  const [isVisible, setIsVisible] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-xl',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-[90vw]',
  };

  // Handle close with animation
  const handleClose = useCallback(() => {
    setIsClosing(true);
    setTimeout(() => {
      setIsClosing(false);
      setIsVisible(false);
      onClose?.();
    }, 150);
  }, [onClose]);

  // Handle open/close visibility
  useEffect(() => {
    if (open && !isVisible) {
      setIsVisible(true);
      setIsClosing(false);
    }
  }, [open, isVisible]);

  // Handle Escape key to close modal (WCAG 2.1 SC 2.1.2)
  useEffect(() => {
    if (!isVisible) return;
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        handleClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isVisible, handleClose]);

  // Prevent body scroll when modal is open (iOS compatible)
  useEffect(() => {
    if (isVisible && !isClosing) {
      scrollY.current = window.scrollY;
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed';
      document.body.style.width = '100%';
      document.body.style.top = `-${scrollY.current}px`;
    } else if (!isVisible) {
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.width = '';
      document.body.style.top = '';
      window.scrollTo(0, scrollY.current);
    }
    return () => {
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.width = '';
      document.body.style.top = '';
    };
  }, [isVisible, isClosing]);

  // Focus management
  useEffect(() => {
    if (isVisible && !isClosing) {
      previousActiveElement.current = document.activeElement;
      modalRef.current?.focus();
    } else if (!isVisible && previousActiveElement.current) {
      previousActiveElement.current.focus();
    }
  }, [isVisible, isClosing]);

  // Focus trap (WCAG 2.1 SC 2.4.3 - Focus Order)
  useEffect(() => {
    if (!isVisible || isClosing) return;

    const handleTab = (e) => {
      if (e.key !== 'Tab') return;

      const modal = modalRef.current;
      if (!modal) return;

      // Get all focusable elements within the modal
      const focusableElements = modal.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      // Trap focus within modal
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement?.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement?.focus();
      }
    };

    document.addEventListener('keydown', handleTab);
    return () => document.removeEventListener('keydown', handleTab);
  }, [isVisible, isClosing]);

  if (!isVisible) return null;

  return (
    <div
      className={clsx(
        'fixed inset-0 z-50 flex items-center justify-center p-4',
        'bg-slate-900/60 backdrop-blur-sm',
        isClosing ? 'animate-out fade-out duration-150' : 'animate-in fade-in duration-200'
      )}
      role="presentation"
      onClick={(e) => {
        if (closeOnOverlayClick && e.target === e.currentTarget) handleClose();
      }}
    >
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={-1}
        className={clsx(
          'glass-panel w-full p-6 outline-none',
          sizes[size],
          isClosing ? 'animate-out zoom-out-95 duration-150' : 'animate-in zoom-in-95 duration-200'
        )}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h3 id={titleId} className="text-xl font-semibold text-slate-900">
              {title}
            </h3>
            {description && (
              <p id={descriptionId} className="mt-1 text-sm text-slate-500">
                {description}
              </p>
            )}
          </div>
          {showCloseButton && (
            <button
              type="button"
              className={clsx(
                'group rounded-full p-3 -mr-3 -mt-3 min-w-[44px] min-h-[44px]',
                'flex items-center justify-center',
                'text-slate-400 transition-all duration-150',
                'hover:bg-slate-100 hover:text-slate-800',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2',
                'active:scale-95 active:bg-slate-200'
              )}
              onClick={handleClose}
              aria-label="Fermer la modale"
            >
              <X className="h-5 w-5 transition-transform group-hover:scale-110" aria-hidden="true" />
            </button>
          )}
        </div>

        <div className="mt-4 flex flex-col gap-4">{children}</div>

        {actions && actions.length > 0 && (
          <div className="mt-6 flex flex-wrap justify-end gap-2" role="group" aria-label="Actions">
            {actions.map(({ label, variant = 'subtle', onClick, type = 'button', disabled, loading }) => (
              <Button
                key={label}
                type={type}
                variant={variant}
                onClick={onClick}
                disabled={disabled}
                loading={loading}
              >
                {label}
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * ConfirmDialog - Modal de confirmation pour les actions destructives
 */
export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = 'Confirmer l\'action',
  description = 'Êtes-vous sûr de vouloir continuer ?',
  confirmLabel = 'Confirmer',
  cancelLabel = 'Annuler',
  variant = 'destructive',
  loading = false,
}) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      description={description}
      size="sm"
      actions={[
        { label: cancelLabel, variant: 'ghost', onClick: onClose },
        { label: confirmLabel, variant, onClick: onConfirm, loading },
      ]}
    />
  );
}
