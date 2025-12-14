/**
 * ConfirmDialog - Dialog de confirmation avancé.
 *
 * Fonctionnalités:
 * - Focus trap automatique
 * - Fermeture Escape
 * - Variants (danger, warning, info)
 * - Animation fluide
 * - Accessibilité complète
 */

import { useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useFeedback } from '../../contexts/FeedbackContext';

const variants = {
  danger: {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
    ),
    iconBg: 'bg-rose-100',
    iconColor: 'text-rose-600',
    confirmButton: 'bg-rose-600 hover:bg-rose-700 focus:ring-rose-500',
  },
  warning: {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
    iconBg: 'bg-amber-100',
    iconColor: 'text-amber-600',
    confirmButton: 'bg-amber-600 hover:bg-amber-700 focus:ring-amber-500',
  },
  info: {
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
    iconBg: 'bg-sky-100',
    iconColor: 'text-sky-600',
    confirmButton: 'bg-brand-600 hover:bg-brand-700 focus:ring-brand-500',
  },
};

export default function ConfirmDialog() {
  const { confirmation } = useFeedback();

  if (!confirmation) return null;

  return createPortal(<ConfirmDialogContent confirmation={confirmation} />, document.body);
}

function ConfirmDialogContent({ confirmation }) {
  const {
    title = 'Confirmer l\'action',
    message,
    confirmLabel = 'Confirmer',
    cancelLabel = 'Annuler',
    variant = 'info',
    onConfirm,
    onCancel,
  } = confirmation;

  const dialogRef = useRef(null);
  const confirmButtonRef = useRef(null);
  const cancelButtonRef = useRef(null);

  const variantStyles = variants[variant] || variants.info;

  // Focus le bouton annuler par défaut (plus sûr)
  useEffect(() => {
    cancelButtonRef.current?.focus();
  }, []);

  // Gérer Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onCancel?.();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onCancel]);

  // Focus trap
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key !== 'Tab') return;

      const focusableElements = dialogRef.current?.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );

      if (!focusableElements || focusableElements.length === 0) return;

      const first = focusableElements[0];
      const last = focusableElements[focusableElements.length - 1];

      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    },
    []
  );

  // Empêcher le scroll du body
  useEffect(() => {
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, []);

  return (
    <div
      className="fixed inset-0 z-[120] flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
      aria-describedby="confirm-message"
      onKeyDown={handleKeyDown}
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity duration-200"
        onClick={onCancel}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        ref={dialogRef}
        className="relative w-full max-w-md animate-in zoom-in-95 duration-200 rounded-2xl bg-white p-6 shadow-2xl"
      >
        {/* Icon + Title */}
        <div className="flex items-start gap-4">
          <div
            className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full ${variantStyles.iconBg} ${variantStyles.iconColor}`}
          >
            {variantStyles.icon}
          </div>
          <div className="min-w-0 flex-1">
            <h3 id="confirm-title" className="text-lg font-semibold text-slate-900">
              {title}
            </h3>
            {message && (
              <p id="confirm-message" className="mt-1 text-sm text-slate-600">
                {message}
              </p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 flex justify-end gap-3">
          <button
            ref={cancelButtonRef}
            onClick={onCancel}
            className="
              rounded-xl px-4 py-2.5 text-sm font-semibold
              text-slate-700 transition-colors duration-150
              hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2
            "
          >
            {cancelLabel}
          </button>
          <button
            ref={confirmButtonRef}
            onClick={onConfirm}
            className={`
              rounded-xl px-4 py-2.5 text-sm font-semibold text-white
              transition-colors duration-150
              focus:outline-none focus:ring-2 focus:ring-offset-2
              ${variantStyles.confirmButton}
            `}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
