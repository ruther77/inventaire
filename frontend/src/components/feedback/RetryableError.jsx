/**
 * RetryableError - Composant d'erreur avec retry intelligent.
 *
 * Fonctionnalités:
 * - Exponential backoff
 * - Compteur de tentatives
 * - Messages contextuels par type d'erreur
 * - Actions alternatives
 */

import { useState, useCallback, useEffect } from 'react';

// Types d'erreurs reconnus
const ErrorTypes = {
  NETWORK: 'network',
  TIMEOUT: 'timeout',
  AUTH: 'auth',
  PERMISSION: 'permission',
  NOT_FOUND: 'not_found',
  VALIDATION: 'validation',
  SERVER: 'server',
  UNKNOWN: 'unknown',
};

// Détection automatique du type d'erreur
function detectErrorType(error) {
  if (!error) return ErrorTypes.UNKNOWN;

  const message = error.message?.toLowerCase() || '';
  const status = error.response?.status || error.status;

  if (message.includes('network') || message.includes('fetch')) {
    return ErrorTypes.NETWORK;
  }
  if (message.includes('timeout') || message.includes('timed out')) {
    return ErrorTypes.TIMEOUT;
  }
  if (status === 401) return ErrorTypes.AUTH;
  if (status === 403) return ErrorTypes.PERMISSION;
  if (status === 404) return ErrorTypes.NOT_FOUND;
  if (status === 422 || status === 400) return ErrorTypes.VALIDATION;
  if (status >= 500) return ErrorTypes.SERVER;

  return ErrorTypes.UNKNOWN;
}

// Messages par type d'erreur
const errorMessages = {
  [ErrorTypes.NETWORK]: {
    title: 'Connexion impossible',
    description: 'Vérifiez votre connexion internet et réessayez.',
    icon: '📡',
    canRetry: true,
  },
  [ErrorTypes.TIMEOUT]: {
    title: 'Délai dépassé',
    description: 'Le serveur met trop de temps à répondre.',
    icon: '⏱️',
    canRetry: true,
  },
  [ErrorTypes.AUTH]: {
    title: 'Session expirée',
    description: 'Veuillez vous reconnecter pour continuer.',
    icon: '🔐',
    canRetry: false,
    action: { label: 'Se reconnecter', href: '/login' },
  },
  [ErrorTypes.PERMISSION]: {
    title: 'Accès refusé',
    description: 'Vous n\'avez pas les droits nécessaires.',
    icon: '🚫',
    canRetry: false,
  },
  [ErrorTypes.NOT_FOUND]: {
    title: 'Introuvable',
    description: 'La ressource demandée n\'existe pas ou a été supprimée.',
    icon: '🔍',
    canRetry: false,
    action: { label: 'Retour', onClick: () => window.history.back() },
  },
  [ErrorTypes.VALIDATION]: {
    title: 'Données invalides',
    description: 'Vérifiez les informations saisies.',
    icon: '⚠️',
    canRetry: false,
  },
  [ErrorTypes.SERVER]: {
    title: 'Erreur serveur',
    description: 'Un problème est survenu. Nos équipes ont été notifiées.',
    icon: '🔧',
    canRetry: true,
  },
  [ErrorTypes.UNKNOWN]: {
    title: 'Une erreur est survenue',
    description: 'Veuillez réessayer ou contacter le support.',
    icon: '❌',
    canRetry: true,
  },
};

export default function RetryableError({
  error,
  onRetry,
  maxRetries = 3,
  initialDelay = 1000,
  maxDelay = 30000,
  variant = 'card', // card | inline | full
  className = '',
  children,
}) {
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);
  const [countdown, setCountdown] = useState(0);

  const errorType = detectErrorType(error);
  const errorConfig = errorMessages[errorType];

  // Calculer le délai avec exponential backoff
  const getDelay = useCallback(
    (attempt) => {
      const delay = initialDelay * Math.pow(2, attempt);
      return Math.min(delay, maxDelay);
    },
    [initialDelay, maxDelay]
  );

  // Auto-retry avec countdown
  useEffect(() => {
    if (!errorConfig.canRetry || !onRetry || retryCount >= maxRetries) return;

    const delay = getDelay(retryCount);
    let remaining = Math.ceil(delay / 1000);
    setCountdown(remaining);

    const interval = setInterval(() => {
      remaining -= 1;
      setCountdown(remaining);
      if (remaining <= 0) {
        clearInterval(interval);
      }
    }, 1000);

    const timeout = setTimeout(() => {
      handleRetry();
    }, delay);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [retryCount, errorConfig.canRetry, maxRetries, getDelay, onRetry]);

  const handleRetry = useCallback(async () => {
    if (!onRetry || isRetrying) return;

    setIsRetrying(true);
    try {
      await onRetry();
    } catch {
      setRetryCount((prev) => prev + 1);
    } finally {
      setIsRetrying(false);
    }
  }, [onRetry, isRetrying]);

  const handleManualRetry = () => {
    setRetryCount(0);
    handleRetry();
  };

  const canRetry = errorConfig.canRetry && retryCount < maxRetries;

  if (variant === 'inline') {
    return (
      <div className={`flex items-center gap-3 text-sm ${className}`}>
        <span className="text-lg">{errorConfig.icon}</span>
        <span className="text-slate-700">{errorConfig.title}</span>
        {canRetry && onRetry && (
          <button
            onClick={handleManualRetry}
            disabled={isRetrying}
            className="font-semibold text-brand-600 hover:text-brand-700 disabled:opacity-50"
          >
            {isRetrying ? 'Réessai...' : countdown > 0 ? `Réessai dans ${countdown}s` : 'Réessayer'}
          </button>
        )}
      </div>
    );
  }

  if (variant === 'full') {
    return (
      <div className={`flex min-h-[300px] flex-col items-center justify-center p-8 ${className}`}>
        <div className="mb-4 text-6xl">{errorConfig.icon}</div>
        <h2 className="text-xl font-semibold text-slate-900">{errorConfig.title}</h2>
        <p className="mt-2 text-slate-600">{errorConfig.description}</p>

        <div className="mt-6 flex gap-3">
          {canRetry && onRetry && (
            <button
              onClick={handleManualRetry}
              disabled={isRetrying}
              className="rounded-xl bg-brand-600 px-6 py-3 font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
            >
              {isRetrying ? (
                <span className="flex items-center gap-2">
                  <LoadingSpinner /> Réessai en cours...
                </span>
              ) : countdown > 0 ? (
                `Réessai automatique dans ${countdown}s`
              ) : (
                'Réessayer maintenant'
              )}
            </button>
          )}
          {errorConfig.action && (
            errorConfig.action.href ? (
              <a
                href={errorConfig.action.href}
                className="rounded-xl border border-slate-300 px-6 py-3 font-semibold text-slate-700 hover:bg-slate-50"
              >
                {errorConfig.action.label}
              </a>
            ) : (
              <button
                onClick={errorConfig.action.onClick}
                className="rounded-xl border border-slate-300 px-6 py-3 font-semibold text-slate-700 hover:bg-slate-50"
              >
                {errorConfig.action.label}
              </button>
            )
          )}
        </div>

        {retryCount >= maxRetries && (
          <p className="mt-4 text-sm text-rose-600">
            Échec après {maxRetries} tentatives. Veuillez réessayer plus tard.
          </p>
        )}

        {children}
      </div>
    );
  }

  // Card variant (default)
  return (
    <div className={`rounded-2xl border border-rose-200 bg-rose-50 p-6 ${className}`}>
      <div className="flex items-start gap-4">
        <div className="text-3xl">{errorConfig.icon}</div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-rose-900">{errorConfig.title}</h3>
          <p className="mt-1 text-sm text-rose-700">{errorConfig.description}</p>

          <div className="mt-4 flex flex-wrap gap-3">
            {canRetry && onRetry && (
              <button
                onClick={handleManualRetry}
                disabled={isRetrying}
                className="inline-flex items-center gap-2 rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-700 disabled:opacity-50"
              >
                {isRetrying ? (
                  <>
                    <LoadingSpinner size="sm" /> Réessai...
                  </>
                ) : countdown > 0 ? (
                  `Réessai dans ${countdown}s`
                ) : (
                  'Réessayer'
                )}
              </button>
            )}
            {errorConfig.action && (
              errorConfig.action.href ? (
                <a
                  href={errorConfig.action.href}
                  className="rounded-lg px-4 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-100"
                >
                  {errorConfig.action.label}
                </a>
              ) : (
                <button
                  onClick={errorConfig.action.onClick}
                  className="rounded-lg px-4 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-100"
                >
                  {errorConfig.action.label}
                </button>
              )
            )}
          </div>

          {retryCount > 0 && retryCount < maxRetries && (
            <p className="mt-2 text-xs text-rose-600">
              Tentative {retryCount + 1}/{maxRetries}
            </p>
          )}
        </div>
      </div>
      {children}
    </div>
  );
}

function LoadingSpinner({ size = 'md' }) {
  const sizes = { sm: 'h-4 w-4', md: 'h-5 w-5' };
  return (
    <svg className={`animate-spin ${sizes[size]}`} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

export { ErrorTypes };
