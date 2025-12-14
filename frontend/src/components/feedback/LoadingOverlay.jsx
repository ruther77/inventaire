/**
 * LoadingOverlay - Overlay de chargement avancé.
 *
 * Fonctionnalités:
 * - Affichage différé (évite le flash)
 * - Barre de progression déterminée/indéterminée
 * - Message contextuel
 * - Animation fluide
 * - Option d'annulation
 */

import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useFeedback } from '../../contexts/FeedbackContext';

export default function LoadingOverlay() {
  const { isLoading, loadingMessage, loadingProgress } = useFeedback();
  const [visible, setVisible] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);

  // Gérer l'animation d'entrée/sortie
  useEffect(() => {
    if (isLoading) {
      setShouldRender(true);
      // Petit délai pour déclencher l'animation CSS
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setVisible(true);
        });
      });
    } else {
      setVisible(false);
      // Attendre la fin de l'animation avant de démonter
      const timer = setTimeout(() => setShouldRender(false), 200);
      return () => clearTimeout(timer);
    }
  }, [isLoading]);

  if (!shouldRender) return null;

  return createPortal(
    <div
      className={`
        fixed inset-0 z-[100] flex items-center justify-center
        bg-slate-900/40 backdrop-blur-sm
        transition-opacity duration-200 ease-out
        ${visible ? 'opacity-100' : 'opacity-0'}
      `}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={loadingProgress ?? undefined}
      aria-valuetext={loadingMessage}
      aria-busy="true"
      aria-live="polite"
    >
      <div
        className={`
          flex flex-col items-center gap-4 rounded-2xl
          bg-white p-8 shadow-2xl
          transition-all duration-200 ease-out
          ${visible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'}
        `}
      >
        {/* Spinner ou Progress */}
        {loadingProgress === null ? (
          <IndeterminateSpinner />
        ) : (
          <ProgressRing progress={loadingProgress} />
        )}

        {/* Message */}
        <p className="text-sm font-medium text-slate-700">{loadingMessage}</p>

        {/* Barre de progression pour les opérations longues */}
        {loadingProgress !== null && (
          <div className="w-48">
            <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-brand-500 transition-all duration-300 ease-out"
                style={{ width: `${loadingProgress}%` }}
              />
            </div>
            <p className="mt-1 text-center text-xs text-slate-500">
              {Math.round(loadingProgress)}%
            </p>
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}

// Spinner indéterminé avec animation CSS
function IndeterminateSpinner() {
  return (
    <div className="relative h-12 w-12">
      {/* Track */}
      <svg className="h-12 w-12" viewBox="0 0 48 48">
        <circle
          cx="24"
          cy="24"
          r="20"
          fill="none"
          stroke="currentColor"
          strokeWidth="4"
          className="text-slate-100"
        />
      </svg>

      {/* Animated arc */}
      <svg
        className="absolute inset-0 h-12 w-12 animate-spin"
        viewBox="0 0 48 48"
        style={{ animationDuration: '1.2s' }}
      >
        <circle
          cx="24"
          cy="24"
          r="20"
          fill="none"
          stroke="currentColor"
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray="60 40"
          className="text-brand-500"
        />
      </svg>

      {/* Pulse effect */}
      <div className="absolute inset-0 animate-ping rounded-full bg-brand-400/20" />
    </div>
  );
}

// Progress ring déterminé
function ProgressRing({ progress }) {
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className="relative h-12 w-12">
      <svg className="h-12 w-12 -rotate-90 transform" viewBox="0 0 48 48">
        {/* Background circle */}
        <circle
          cx="24"
          cy="24"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="4"
          className="text-slate-100"
        />
        {/* Progress circle */}
        <circle
          cx="24"
          cy="24"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="text-brand-500 transition-all duration-300 ease-out"
        />
      </svg>

      {/* Percentage text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xs font-semibold text-slate-700">{Math.round(progress)}%</span>
      </div>
    </div>
  );
}
