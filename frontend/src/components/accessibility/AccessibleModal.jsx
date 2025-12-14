/**
 * AccessibleModal - Modal accessible conforme WCAG 2.1 AAA.
 *
 * Fonctionnalités:
 * - Focus trap automatique
 * - Focus restoration à la fermeture
 * - Escape pour fermer
 * - aria-modal et role="dialog"
 * - Support screen readers
 * - Animation d'entrée/sortie
 * - Backdrop click pour fermer
 */

import { useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useFocusTrap, useAnnounce } from '../../hooks/useAccessibility';

export default function AccessibleModal({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  closeOnBackdrop = true,
  closeOnEscape = true,
  initialFocus,
  className = '',
}) {
  const containerRef = useFocusTrap(isOpen);
  const { announce } = useAnnounce();
  const titleId = useRef(`modal-title-${Math.random().toString(36).slice(2)}`);
  const descId = useRef(`modal-desc-${Math.random().toString(36).slice(2)}`);

  // Annoncer l'ouverture aux screen readers
  useEffect(() => {
    if (isOpen && title) {
      announce(`Dialogue ouvert: ${title}`);
    }
  }, [isOpen, title, announce]);

  // Gérer Escape
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, closeOnEscape, onClose]);

  // Bloquer le scroll du body
  useEffect(() => {
    if (isOpen) {
      const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
      document.body.style.overflow = 'hidden';
      document.body.style.paddingRight = `${scrollbarWidth}px`;
    }
    return () => {
      document.body.style.overflow = '';
      document.body.style.paddingRight = '';
    };
  }, [isOpen]);

  // Focus initial personnalisé
  useEffect(() => {
    if (isOpen && initialFocus?.current) {
      initialFocus.current.focus();
    }
  }, [isOpen, initialFocus]);

  const handleBackdropClick = useCallback(
    (e) => {
      if (closeOnBackdrop && e.target === e.currentTarget) {
        onClose();
      }
    },
    [closeOnBackdrop, onClose]
  );

  const sizes = {
    sm: 'max-w-sm',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-[calc(100vw-2rem)]',
  };

  if (!isOpen) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={handleBackdropClick}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200"
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId.current}
        aria-describedby={description ? descId.current : undefined}
        className={`
          relative w-full ${sizes[size]}
          rounded-2xl bg-white shadow-2xl
          animate-in zoom-in-95 fade-in duration-200
          ${className}
        `}
      >
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4">
          <div>
            <h2
              id={titleId.current}
              className="text-lg font-semibold text-slate-900"
            >
              {title}
            </h2>
            {description && (
              <p
                id={descId.current}
                className="mt-1 text-sm text-slate-500"
              >
                {description}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="
              -m-1 rounded-lg p-2 text-slate-400
              transition-colors duration-150
              hover:bg-slate-100 hover:text-slate-600
              focus:outline-none focus:ring-2 focus:ring-brand-500
            "
            aria-label="Fermer le dialogue"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          {children}
        </div>
      </div>
    </div>,
    document.body
  );
}

/**
 * Footer pour les actions du modal
 */
export function ModalFooter({ children, className = '' }) {
  return (
    <div className={`flex justify-end gap-3 border-t border-slate-200 px-6 py-4 ${className}`}>
      {children}
    </div>
  );
}
