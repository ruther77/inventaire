import { createContext, useContext, useState, useCallback, useMemo, useEffect } from 'react';
import { createPortal } from 'react-dom';
import clsx from 'clsx';
import { X, CheckCircle2, AlertTriangle, AlertCircle, Info, Loader2 } from 'lucide-react';

// Context
const ToastContext = createContext(null);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
}

/**
 * ToastProvider - Provider pour le système de notifications
 */
export function ToastProvider({ children, position = 'bottom-right', maxToasts = 5 }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback(
    (toast) => {
      const id = toast.id || `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const newToast = {
        id,
        type: 'info',
        duration: 5000,
        dismissible: true,
        ...toast,
      };

      setToasts((prev) => {
        // Limiter le nombre de toasts
        const updated = [...prev, newToast];
        if (updated.length > maxToasts) {
          return updated.slice(-maxToasts);
        }
        return updated;
      });

      // Auto-dismiss
      if (newToast.duration > 0) {
        setTimeout(() => {
          dismissToast(id);
        }, newToast.duration);
      }

      return id;
    },
    [maxToasts]
  );

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const dismissAll = useCallback(() => {
    setToasts([]);
  }, []);

  // Helpers pour les types courants
  const toast = useMemo(
    () => ({
      show: addToast,
      dismiss: dismissToast,
      dismissAll,

      success: (title, options = {}) =>
        addToast({ type: 'success', title, ...options }),

      error: (title, options = {}) =>
        addToast({ type: 'error', title, duration: 8000, ...options }),

      warning: (title, options = {}) =>
        addToast({ type: 'warning', title, duration: 6000, ...options }),

      info: (title, options = {}) =>
        addToast({ type: 'info', title, ...options }),

      loading: (title, options = {}) =>
        addToast({
          type: 'loading',
          title,
          duration: 0, // Pas d'auto-dismiss
          dismissible: false,
          ...options,
        }),

      promise: async (promise, { loading, success, error }) => {
        const id = addToast({
          type: 'loading',
          title: loading || 'Chargement...',
          duration: 0,
          dismissible: false,
        });

        try {
          const result = await promise;
          dismissToast(id);
          addToast({
            type: 'success',
            title: typeof success === 'function' ? success(result) : success || 'Succès',
          });
          return result;
        } catch (err) {
          dismissToast(id);
          addToast({
            type: 'error',
            title: typeof error === 'function' ? error(err) : error || 'Erreur',
            duration: 8000,
          });
          throw err;
        }
      },
    }),
    [addToast, dismissToast, dismissAll]
  );

  const value = useMemo(
    () => ({ toasts, toast }),
    [toasts, toast]
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} position={position} onDismiss={dismissToast} />
    </ToastContext.Provider>
  );
}

/**
 * ToastContainer - Conteneur des toasts
 */
function ToastContainer({ toasts, position, onDismiss }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-center': 'top-4 left-1/2 -translate-x-1/2',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2',
    'bottom-right': 'bottom-4 right-4',
  };

  return createPortal(
    <div
      className={clsx(
        'fixed z-[200] flex flex-col gap-2 pointer-events-none',
        positionClasses[position]
      )}
      aria-live="polite"
      aria-atomic="true"
    >
      {toasts.map((toast, index) => (
        <Toast
          key={toast.id}
          toast={toast}
          onDismiss={() => onDismiss(toast.id)}
          style={{
            '--toast-index': index,
          }}
        />
      ))}
    </div>,
    document.body
  );
}

/**
 * Toast - Composant de notification individuel
 */
function Toast({ toast, onDismiss, style }) {
  const {
    type,
    title,
    description,
    action,
    dismissible,
    icon: CustomIcon,
  } = toast;

  const icons = {
    success: CheckCircle2,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info,
    loading: Loader2,
  };

  const Icon = CustomIcon || icons[type] || Info;

  const typeStyles = {
    success: 'bg-emerald-50 border-emerald-200 text-emerald-900',
    error: 'bg-rose-50 border-rose-200 text-rose-900',
    warning: 'bg-amber-50 border-amber-200 text-amber-900',
    info: 'bg-sky-50 border-sky-200 text-sky-900',
    loading: 'bg-slate-50 border-slate-200 text-slate-900',
  };

  const iconStyles = {
    success: 'text-emerald-600',
    error: 'text-rose-600',
    warning: 'text-amber-600',
    info: 'text-sky-600',
    loading: 'text-slate-600',
  };

  return (
    <div
      className={clsx(
        'pointer-events-auto w-80 max-w-[calc(100vw-2rem)]',
        'rounded-xl border shadow-lg',
        'animate-in slide-in-from-right fade-in duration-300',
        typeStyles[type]
      )}
      style={style}
      role="alert"
    >
      <div className="flex gap-3 p-4">
        {/* Icon */}
        <div className="flex-shrink-0">
          <Icon
            className={clsx(
              'h-5 w-5',
              iconStyles[type],
              type === 'loading' && 'animate-spin'
            )}
          />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium">{title}</p>
          {description && (
            <p className="mt-1 text-sm opacity-80">{description}</p>
          )}
          {action && (
            <button
              type="button"
              onClick={action.onClick}
              className="mt-2 text-sm font-medium underline hover:no-underline"
            >
              {action.label}
            </button>
          )}
        </div>

        {/* Dismiss button */}
        {dismissible && (
          <button
            type="button"
            onClick={onDismiss}
            className="flex-shrink-0 rounded-lg p-1 opacity-60 hover:opacity-100 hover:bg-black/5 transition-all"
            aria-label="Fermer"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Progress bar for timed toasts */}
      {toast.duration > 0 && (
        <div className="h-1 bg-black/5 overflow-hidden rounded-b-xl">
          <div
            className={clsx(
              'h-full',
              type === 'success' && 'bg-emerald-500',
              type === 'error' && 'bg-rose-500',
              type === 'warning' && 'bg-amber-500',
              type === 'info' && 'bg-sky-500'
            )}
            style={{
              animation: `toast-progress ${toast.duration}ms linear forwards`,
            }}
          />
        </div>
      )}

      <style>{`
        @keyframes toast-progress {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );
}

export default Toast;
