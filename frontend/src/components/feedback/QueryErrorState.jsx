/**
 * QueryErrorState - Composant d'erreur pour les queries TanStack
 *
 * Phase 1 - États d'erreur récupérables
 *
 * Features:
 * - Détection automatique du type d'erreur
 * - Retry automatique avec countdown
 * - Messages contextuels
 * - Support offline
 */

import { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, WifiOff, RefreshCw, LogIn, ArrowLeft } from 'lucide-react';
import Button from '../ui/Button.jsx';
import { getErrorType, errorMessages, useOnlineStatus } from '../../hooks/useQueryConfig.js';

export default function QueryErrorState({
  error,
  onRetry,
  maxRetries = 3,
  autoRetry = true,
  autoRetryDelay = 5000,
  variant = 'card', // card | inline | full
  className = '',
}) {
  const [retryCount, setRetryCount] = useState(0);
  const [isRetrying, setIsRetrying] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const isOnline = useOnlineStatus();

  const errorType = getErrorType(error);
  const errorConfig = errorMessages[errorType] || errorMessages.unknown;

  // Auto-retry countdown
  useEffect(() => {
    if (!autoRetry || !errorConfig.canRetry || !onRetry || retryCount >= maxRetries || !isOnline) {
      return;
    }

    const delaySeconds = Math.ceil(autoRetryDelay / 1000);
    let remaining = delaySeconds;
    setCountdown(remaining);

    const interval = setInterval(() => {
      remaining -= 1;
      setCountdown(remaining);
    }, 1000);

    const timeout = setTimeout(() => {
      handleRetry();
    }, autoRetryDelay);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [retryCount, errorConfig.canRetry, maxRetries, autoRetry, autoRetryDelay, onRetry, isOnline]);

  const handleRetry = useCallback(async () => {
    if (!onRetry || isRetrying) return;

    setIsRetrying(true);
    setCountdown(0);
    try {
      await onRetry();
      setRetryCount(0);
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

  const canRetry = errorConfig.canRetry && retryCount < maxRetries && isOnline;

  // Icon based on error type
  const getIcon = () => {
    if (!isOnline || errorType === 'network') {
      return <WifiOff className="h-8 w-8" />;
    }
    return <AlertTriangle className="h-8 w-8" />;
  };

  // Inline variant
  if (variant === 'inline') {
    return (
      <div className={`flex items-center gap-3 text-sm ${className}`}>
        <span className="text-rose-400">{getIcon()}</span>
        <span className="text-slate-300">{errorConfig.title}</span>
        {canRetry && onRetry && (
          <button
            onClick={handleManualRetry}
            disabled={isRetrying}
            className="font-semibold text-brand-400 hover:text-brand-300 disabled:opacity-50"
          >
            {isRetrying ? 'Réessai...' : countdown > 0 ? `Réessai dans ${countdown}s` : 'Réessayer'}
          </button>
        )}
      </div>
    );
  }

  // Full variant (page-level)
  if (variant === 'full') {
    return (
      <div className={`flex min-h-[400px] flex-col items-center justify-center p-8 ${className}`}>
        <div className="mb-6 text-rose-400">{getIcon()}</div>

        <h2 className="text-xl font-semibold text-white">{errorConfig.title}</h2>
        <p className="mt-2 text-slate-300 text-center max-w-md">{errorConfig.description}</p>

        {!isOnline && (
          <div className="mt-4 flex items-center gap-2 text-amber-400 text-sm">
            <WifiOff className="h-4 w-4" />
            <span>Vous êtes hors ligne</span>
          </div>
        )}

        <div className="mt-8 flex gap-3">
          {canRetry && onRetry && (
            <Button
              onClick={handleManualRetry}
              disabled={isRetrying}
              loading={isRetrying}
              variant="brand"
            >
              <RefreshCw className="h-4 w-4" />
              {countdown > 0 ? `Réessai dans ${countdown}s` : 'Réessayer'}
            </Button>
          )}

          {errorConfig.action?.href && (
            <Button
              as="a"
              href={errorConfig.action.href}
              variant="outline"
            >
              <LogIn className="h-4 w-4" />
              {errorConfig.action.label}
            </Button>
          )}

          {errorConfig.action?.onClick && (
            <Button
              onClick={errorConfig.action.onClick}
              variant="outline"
            >
              <ArrowLeft className="h-4 w-4" />
              {errorConfig.action.label}
            </Button>
          )}
        </div>

        {retryCount > 0 && retryCount < maxRetries && (
          <p className="mt-4 text-xs text-slate-400">
            Tentative {retryCount + 1}/{maxRetries}
          </p>
        )}

        {retryCount >= maxRetries && (
          <p className="mt-4 text-sm text-rose-400">
            Échec après {maxRetries} tentatives. Veuillez réessayer plus tard.
          </p>
        )}
      </div>
    );
  }

  // Card variant (default)
  return (
    <div className={`rounded-2xl border border-rose-500/30 bg-rose-500/10 p-6 ${className}`}>
      <div className="flex items-start gap-4">
        <div className="text-rose-400">{getIcon()}</div>

        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-rose-300">{errorConfig.title}</h3>
          <p className="mt-1 text-sm text-rose-200/80">{errorConfig.description}</p>

          {!isOnline && (
            <div className="mt-2 flex items-center gap-2 text-amber-400 text-xs">
              <WifiOff className="h-3 w-3" />
              <span>Mode hors ligne</span>
            </div>
          )}

          <div className="mt-4 flex flex-wrap gap-3">
            {canRetry && onRetry && (
              <Button
                size="sm"
                onClick={handleManualRetry}
                disabled={isRetrying}
                loading={isRetrying}
              >
                <RefreshCw className="h-4 w-4" />
                {countdown > 0 ? `Réessai dans ${countdown}s` : 'Réessayer'}
              </Button>
            )}

            {errorConfig.action?.href && (
              <Button
                as="a"
                href={errorConfig.action.href}
                variant="ghost"
                size="sm"
              >
                {errorConfig.action.label}
              </Button>
            )}
          </div>

          {retryCount > 0 && retryCount < maxRetries && (
            <p className="mt-2 text-xs text-rose-300/60">
              Tentative {retryCount + 1}/{maxRetries}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * OfflineBanner - Bannière affichée quand l'utilisateur est hors ligne
 */
export function OfflineBanner({ className = '' }) {
  const isOnline = useOnlineStatus();

  if (isOnline) return null;

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-50 bg-amber-500 text-amber-900 px-4 py-2 text-center text-sm font-medium ${className}`}
      role="alert"
    >
      <WifiOff className="inline h-4 w-4 mr-2" />
      Vous êtes hors ligne. Certaines fonctionnalités peuvent être limitées.
    </div>
  );
}
