/**
 * ErrorBoundary - Gestion avancée des erreurs React.
 *
 * Fonctionnalités:
 * - Capture toutes les erreurs React
 * - UI de fallback élégante
 * - Retry automatique
 * - Reporting d'erreurs
 * - Recovery par section
 */

import { Component } from 'react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });

    // Reporter l'erreur (analytics, Sentry, etc.)
    this.reportError(error, errorInfo);
  }

  reportError(error, errorInfo) {
    // En production, envoyer à un service de monitoring
    console.error('[ErrorBoundary] Caught error:', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo?.componentStack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    });

    // Hook pour reporting externe
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    const { maxRetries = 3 } = this.props;
    const { retryCount } = this.state;

    if (retryCount < maxRetries) {
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null,
        retryCount: retryCount + 1,
      });
    }
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
    });

    // Callback de reset
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    const { hasError, error, errorInfo, retryCount } = this.state;
    const {
      children,
      fallback,
      level = 'page', // page | section | component
      maxRetries = 3,
      showDetails = process.env.NODE_ENV === 'development',
    } = this.props;

    if (!hasError) {
      return children;
    }

    // Fallback custom
    if (fallback) {
      return typeof fallback === 'function'
        ? fallback({ error, errorInfo, retry: this.handleRetry, reset: this.handleReset })
        : fallback;
    }

    // UI par défaut selon le niveau
    const canRetry = retryCount < maxRetries;

    if (level === 'component') {
      return (
        <ComponentErrorFallback
          error={error}
          canRetry={canRetry}
          onRetry={this.handleRetry}
          showDetails={showDetails}
        />
      );
    }

    if (level === 'section') {
      return (
        <SectionErrorFallback
          error={error}
          canRetry={canRetry}
          onRetry={this.handleRetry}
          onReset={this.handleReset}
          showDetails={showDetails}
        />
      );
    }

    return (
      <PageErrorFallback
        error={error}
        errorInfo={errorInfo}
        canRetry={canRetry}
        onRetry={this.handleRetry}
        onReset={this.handleReset}
        showDetails={showDetails}
      />
    );
  }
}

// Fallback niveau composant (inline, minimal)
function ComponentErrorFallback({ error, canRetry, onRetry, showDetails }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <span>Erreur</span>
      {canRetry && (
        <button onClick={onRetry} className="font-semibold underline hover:no-underline">
          Réessayer
        </button>
      )}
      {showDetails && <span className="text-xs opacity-60">({error?.message})</span>}
    </div>
  );
}

// Fallback niveau section (card)
function SectionErrorFallback({ error, canRetry, onRetry, onReset, showDetails }) {
  return (
    <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-rose-100">
          <svg className="h-5 w-5 text-rose-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-rose-900">Cette section n'a pas pu se charger</h3>
          <p className="mt-1 text-sm text-rose-700">
            Une erreur inattendue s'est produite. Vous pouvez réessayer ou rafraîchir la page.
          </p>
          {showDetails && (
            <pre className="mt-2 overflow-auto rounded bg-rose-100 p-2 text-xs text-rose-800">
              {error?.message}
            </pre>
          )}
          <div className="mt-4 flex gap-3">
            {canRetry && (
              <button
                onClick={onRetry}
                className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-700"
              >
                Réessayer
              </button>
            )}
            <button
              onClick={onReset}
              className="rounded-lg px-4 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-100"
            >
              Réinitialiser
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Fallback niveau page (full screen)
function PageErrorFallback({ error, errorInfo, canRetry, onRetry, onReset, showDetails }) {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center p-8 text-center">
      {/* Illustration */}
      <div className="mb-6">
        <svg className="h-24 w-24 text-rose-200" viewBox="0 0 200 200" fill="none">
          <circle cx="100" cy="100" r="80" fill="currentColor" />
          <circle cx="100" cy="100" r="50" fill="white" />
          <path
            d="M100 70v35M100 120v5"
            stroke="#f43f5e"
            strokeWidth="8"
            strokeLinecap="round"
          />
        </svg>
      </div>

      <h1 className="text-2xl font-bold text-slate-900">Oups, quelque chose s'est mal passé</h1>
      <p className="mt-2 max-w-md text-slate-600">
        L'application a rencontré une erreur inattendue. Nos équipes ont été notifiées.
      </p>

      {/* Actions */}
      <div className="mt-8 flex flex-wrap justify-center gap-4">
        {canRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-3 font-semibold text-white shadow-sm hover:bg-brand-700"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Réessayer
          </button>
        )}
        <button
          onClick={() => window.location.reload()}
          className="inline-flex items-center gap-2 rounded-xl border border-slate-300 px-6 py-3 font-semibold text-slate-700 hover:bg-slate-50"
        >
          Rafraîchir la page
        </button>
        <a
          href="/"
          className="inline-flex items-center gap-2 rounded-xl px-6 py-3 font-semibold text-slate-600 hover:text-brand-600"
        >
          Retour à l'accueil
        </a>
      </div>

      {/* Détails techniques (dev only) */}
      {showDetails && (
        <details className="mt-8 w-full max-w-2xl text-left">
          <summary className="cursor-pointer text-sm text-slate-500 hover:text-slate-700">
            Détails techniques
          </summary>
          <div className="mt-2 space-y-2">
            <pre className="overflow-auto rounded-lg bg-slate-100 p-4 text-xs text-slate-700">
              <strong>Error:</strong> {error?.message}
              {'\n\n'}
              <strong>Stack:</strong>
              {'\n'}
              {error?.stack}
            </pre>
            {errorInfo?.componentStack && (
              <pre className="overflow-auto rounded-lg bg-slate-100 p-4 text-xs text-slate-700">
                <strong>Component Stack:</strong>
                {'\n'}
                {errorInfo.componentStack}
              </pre>
            )}
          </div>
        </details>
      )}
    </div>
  );
}

export default ErrorBoundary;
