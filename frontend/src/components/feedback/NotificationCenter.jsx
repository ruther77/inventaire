/**
 * NotificationCenter - Centre de notifications avancé.
 *
 * Fonctionnalités:
 * - Stack de notifications avec animation
 * - Actions (retry, undo, custom)
 * - Priorités et auto-dismiss
 * - Icônes et couleurs par type
 * - Accessibilité (aria-live)
 */

import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useFeedback, NotificationType } from '../../contexts/FeedbackContext';

// Icônes inline pour éviter les dépendances
const Icons = {
  success: (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
    </svg>
  ),
  error: (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
  warning: (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  ),
  info: (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  ),
  close: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
};

// Styles par type
const typeStyles = {
  [NotificationType.SUCCESS]: {
    container: 'bg-emerald-50 border-emerald-200',
    icon: 'text-emerald-500 bg-emerald-100',
    title: 'text-emerald-900',
    message: 'text-emerald-700',
  },
  [NotificationType.ERROR]: {
    container: 'bg-rose-50 border-rose-200',
    icon: 'text-rose-500 bg-rose-100',
    title: 'text-rose-900',
    message: 'text-rose-700',
  },
  [NotificationType.WARNING]: {
    container: 'bg-amber-50 border-amber-200',
    icon: 'text-amber-500 bg-amber-100',
    title: 'text-amber-900',
    message: 'text-amber-700',
  },
  [NotificationType.INFO]: {
    container: 'bg-sky-50 border-sky-200',
    icon: 'text-sky-500 bg-sky-100',
    title: 'text-sky-900',
    message: 'text-sky-700',
  },
};

export default function NotificationCenter() {
  const { notifications, dismiss } = useFeedback();

  if (notifications.length === 0) return null;

  return createPortal(
    <div
      className="pointer-events-none fixed inset-0 z-[110] flex flex-col items-end justify-start gap-3 p-4"
      aria-live="polite"
      aria-label="Notifications"
    >
      {notifications.slice(0, 5).map((notification, index) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onDismiss={() => dismiss(notification.id)}
          index={index}
        />
      ))}
    </div>,
    document.body
  );
}

function NotificationItem({ notification, onDismiss, index }) {
  const { type, title, message, action, undoAction } = notification;
  const styles = typeStyles[type] || typeStyles[NotificationType.INFO];
  const ref = useRef(null);

  // Animation d'entrée
  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // Reset initial state
    el.style.opacity = '0';
    el.style.transform = 'translateX(100%)';

    // Trigger animation
    requestAnimationFrame(() => {
      el.style.transition = 'all 300ms cubic-bezier(0.16, 1, 0.3, 1)';
      el.style.opacity = '1';
      el.style.transform = 'translateX(0)';
    });
  }, []);

  const handleDismiss = () => {
    const el = ref.current;
    if (!el) {
      onDismiss();
      return;
    }

    // Animation de sortie
    el.style.transition = 'all 200ms ease-in';
    el.style.opacity = '0';
    el.style.transform = 'translateX(100%)';

    setTimeout(onDismiss, 200);
  };

  return (
    <div
      ref={ref}
      role="alert"
      className={`
        pointer-events-auto flex w-full max-w-sm items-start gap-3
        rounded-xl border p-4 shadow-lg
        ${styles.container}
      `}
      style={{
        animationDelay: `${index * 50}ms`,
      }}
    >
      {/* Icon */}
      <div className={`flex-shrink-0 rounded-full p-1.5 ${styles.icon}`}>
        {Icons[type] || Icons.info}
      </div>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <p className={`text-sm font-semibold ${styles.title}`}>{title}</p>
        {message && <p className={`mt-0.5 text-sm ${styles.message}`}>{message}</p>}

        {/* Actions */}
        {(action || undoAction) && (
          <div className="mt-2 flex gap-2">
            {action && (
              <button
                onClick={action.onClick}
                className={`
                  rounded-lg px-3 py-1.5 text-xs font-semibold
                  transition-colors duration-150
                  ${styles.icon} hover:opacity-80
                `}
              >
                {action.label}
              </button>
            )}
            {undoAction && (
              <button
                onClick={() => {
                  undoAction();
                  handleDismiss();
                }}
                className="rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-white/50"
              >
                Annuler
              </button>
            )}
          </div>
        )}
      </div>

      {/* Close button */}
      <button
        onClick={handleDismiss}
        className={`
          flex-shrink-0 rounded-full p-1
          transition-colors duration-150
          hover:bg-white/50
          ${styles.message}
        `}
        aria-label="Fermer la notification"
      >
        {Icons.close}
      </button>
    </div>
  );
}
