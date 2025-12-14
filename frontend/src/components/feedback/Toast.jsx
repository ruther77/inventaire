/**
 * Toast - Système de notifications avec actions
 * Phase 4 UX Next-Gen 2025
 *
 * Types: success, warning, error, info
 * Features:
 * - Actions intégrées
 * - Auto-dismiss configurable
 * - Progress bar
 * - Animations Framer Motion
 */

import { useState, useEffect, createContext, useContext, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  Info,
  X,
  ChevronRight,
} from 'lucide-react';
import clsx from 'clsx';

// ============================================================================
// TOAST CONTEXT
// ============================================================================

const ToastContext = createContext(null);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

// ============================================================================
// TOAST COMPONENT
// ============================================================================

const toastConfig = {
  success: {
    icon: CheckCircle,
    bgClass: 'bg-emerald-500/10 border-emerald-500/30',
    iconClass: 'text-emerald-400',
    progressClass: 'bg-emerald-500',
  },
  warning: {
    icon: AlertTriangle,
    bgClass: 'bg-amber-500/10 border-amber-500/30',
    iconClass: 'text-amber-400',
    progressClass: 'bg-amber-500',
  },
  error: {
    icon: XCircle,
    bgClass: 'bg-rose-500/10 border-rose-500/30',
    iconClass: 'text-rose-400',
    progressClass: 'bg-rose-500',
  },
  info: {
    icon: Info,
    bgClass: 'bg-blue-500/10 border-blue-500/30',
    iconClass: 'text-blue-400',
    progressClass: 'bg-blue-500',
  },
};

function Toast({
  id,
  type = 'info',
  title,
  message,
  actions,
  duration = 5000,
  persistent = false,
  onDismiss,
  onAction,
}) {
  const [progress, setProgress] = useState(100);
  const [isPaused, setIsPaused] = useState(false);

  const config = toastConfig[type] || toastConfig.info;
  const ToastIcon = config.icon;

  useEffect(() => {
    if (persistent || isPaused || duration === 0) return;

    const startTime = Date.now();
    const endTime = startTime + duration;

    const updateProgress = () => {
      const now = Date.now();
      const remaining = Math.max(0, endTime - now);
      const newProgress = (remaining / duration) * 100;
      setProgress(newProgress);

      if (remaining > 0) {
        requestAnimationFrame(updateProgress);
      } else {
        onDismiss(id);
      }
    };

    const animationId = requestAnimationFrame(updateProgress);
    return () => cancelAnimationFrame(animationId);
  }, [id, duration, persistent, isPaused, onDismiss]);

  const handleAction = (action) => {
    if (action.onClick) {
      action.onClick();
    }
    if (onAction) {
      onAction(action.id, id);
    }
    if (action.dismissOnClick !== false) {
      onDismiss(id);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      className={clsx(
        'relative w-full max-w-md rounded-xl border overflow-hidden',
        'backdrop-blur-xl shadow-2xl',
        config.bgClass
      )}
    >
      {/* Progress bar */}
      {!persistent && duration > 0 && (
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-white/10">
          <motion.div
            className={clsx('h-full', config.progressClass)}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className={clsx('p-2 rounded-lg bg-white/10', config.iconClass)}>
            <ToastIcon className="w-4 h-4" />
          </div>

          <div className="flex-1 min-w-0">
            {title && (
              <p className="font-medium text-white text-sm">{title}</p>
            )}
            {message && (
              <p className="text-xs text-slate-400 mt-0.5">{message}</p>
            )}

            {/* Actions */}
            {actions && actions.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {actions.map((action, index) => (
                  <button
                    key={action.id || index}
                    onClick={() => handleAction(action)}
                    className={clsx(
                      'inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium',
                      'transition-colors duration-200',
                      index === 0
                        ? `${config.bgClass} ${config.iconClass} hover:bg-white/10`
                        : 'bg-white/5 text-slate-300 hover:bg-white/10'
                    )}
                  >
                    {action.icon && <action.icon className="w-3 h-3" />}
                    {action.label}
                    {action.showArrow && <ChevronRight className="w-3 h-3" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Close button */}
          <button
            onClick={() => onDismiss(id)}
            className="p-1 rounded-lg text-slate-500 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}

// ============================================================================
// TOAST CONTAINER
// ============================================================================

function ToastContainer({ toasts, onDismiss, onAction }) {
  return createPortal(
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <Toast
              {...toast}
              onDismiss={onDismiss}
              onAction={onAction}
            />
          </div>
        ))}
      </AnimatePresence>
    </div>,
    document.body
  );
}

// ============================================================================
// TOAST PROVIDER
// ============================================================================

let toastId = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((options) => {
    const id = `toast-${++toastId}`;
    const toast = {
      id,
      type: 'info',
      duration: 5000,
      ...options,
    };
    setToasts((prev) => [...prev, toast]);
    return id;
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const dismissAll = useCallback(() => {
    setToasts([]);
  }, []);

  // Shorthand methods
  const success = useCallback((title, options = {}) => {
    return addToast({ type: 'success', title, ...options });
  }, [addToast]);

  const warning = useCallback((title, options = {}) => {
    return addToast({ type: 'warning', title, ...options });
  }, [addToast]);

  const error = useCallback((title, options = {}) => {
    return addToast({ type: 'error', title, persistent: true, ...options });
  }, [addToast]);

  const info = useCallback((title, options = {}) => {
    return addToast({ type: 'info', title, ...options });
  }, [addToast]);

  const value = {
    toasts,
    addToast,
    dismissToast,
    dismissAll,
    success,
    warning,
    error,
    info,
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer
        toasts={toasts}
        onDismiss={dismissToast}
      />
    </ToastContext.Provider>
  );
}

export default Toast;
