import { useState, useRef, useEffect } from 'react';
import clsx from 'clsx';

/**
 * Composant Tooltip.
 *
 * Info-bulle accessible qui affiche du contenu supplémentaire au survol ou au focus.
 * S'ajuste automatiquement si l'espace manque (repositionnement intelligent).
 * Supporte 4 positions (top, bottom, left, right) et un délai d'affichage configurable.
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {React.ReactNode} props.children - Élément déclencheur du tooltip
 * @param {React.ReactNode} props.content - Contenu du tooltip
 * @param {string} [props.position='top'] - Position par défaut ('top' | 'bottom' | 'left' | 'right')
 * @param {number} [props.delay=200] - Délai en ms avant affichage du tooltip
 * @param {string} [props.className] - Classes CSS additionnelles pour le tooltip
 *
 * @example
 * <Tooltip content="Cliquez pour copier">
 *   <button>Copier</button>
 * </Tooltip>
 *
 * @example
 * <Tooltip content="Informations supplémentaires" position="right" delay={500}>
 *   <InfoIcon />
 * </Tooltip>
 */
export default function Tooltip({
  children,
  content,
  position = 'top',
  delay = 200,
  className,
}) {
  const [isVisible, setIsVisible] = useState(false);
  const [actualPosition, setActualPosition] = useState(position);
  const timeoutRef = useRef(null);
  const tooltipRef = useRef(null);
  const triggerRef = useRef(null);

  const positions = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  const arrows = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-slate-800 border-x-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-slate-800 border-x-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-slate-800 border-y-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-slate-800 border-y-transparent border-l-transparent',
  };

  // Ajuster la position si le tooltip sort de l'écran
  useEffect(() => {
    if (isVisible && tooltipRef.current && triggerRef.current) {
      const tooltip = tooltipRef.current.getBoundingClientRect();
      const trigger = triggerRef.current.getBoundingClientRect();
      const viewport = {
        width: window.innerWidth,
        height: window.innerHeight,
      };

      let newPosition = position;

      // Vérifier si dépasse en haut
      if (position === 'top' && trigger.top - tooltip.height < 0) {
        newPosition = 'bottom';
      }
      // Vérifier si dépasse en bas
      if (position === 'bottom' && trigger.bottom + tooltip.height > viewport.height) {
        newPosition = 'top';
      }
      // Vérifier si dépasse à gauche
      if (position === 'left' && trigger.left - tooltip.width < 0) {
        newPosition = 'right';
      }
      // Vérifier si dépasse à droite
      if (position === 'right' && trigger.right + tooltip.width > viewport.width) {
        newPosition = 'left';
      }

      if (newPosition !== actualPosition) {
        setActualPosition(newPosition);
      }
    }
  }, [isVisible, position, actualPosition]);

  const handleMouseEnter = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  const handleFocus = () => {
    setIsVisible(true);
  };

  const handleBlur = () => {
    setIsVisible(false);
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  if (!content) return children;

  return (
    <div
      ref={triggerRef}
      className="relative inline-flex"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleFocus}
      onBlur={handleBlur}
    >
      {children}
      {isVisible && (
        <div
          ref={tooltipRef}
          role="tooltip"
          className={clsx(
            'absolute z-50 px-3 py-1.5 text-xs font-medium text-white',
            'bg-slate-800 rounded-lg shadow-lg',
            'whitespace-nowrap pointer-events-none',
            'animate-in fade-in zoom-in-95 duration-150',
            positions[actualPosition],
            className
          )}
        >
          {content}
          <span
            className={clsx(
              'absolute w-0 h-0 border-4',
              arrows[actualPosition]
            )}
            aria-hidden="true"
          />
        </div>
      )}
    </div>
  );
}

/**
 * TooltipTrigger - Wrapper simplifié pour ajouter un tooltip.
 *
 * Composant wrapper qui simplifie l'ajout d'un tooltip à n'importe quel élément.
 * Alternative plus concise à l'utilisation directe du composant Tooltip.
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {React.ReactNode} props.children - Élément déclencheur
 * @param {React.ReactNode} props.tooltip - Contenu du tooltip
 *
 * @example
 * <TooltipTrigger tooltip="Supprimer">
 *   <DeleteButton />
 * </TooltipTrigger>
 */
export function TooltipTrigger({ children, tooltip, ...props }) {
  return (
    <Tooltip content={tooltip} {...props}>
      {children}
    </Tooltip>
  );
}

/**
 * InfoTooltip - Icône d'information avec tooltip intégré.
 *
 * Composant prêt à l'emploi affichant une icône d'information circulaire avec un tooltip.
 * Idéal pour ajouter des aides contextuelles dans les formulaires et interfaces.
 *
 * @component
 *
 * @param {Object} props - Propriétés du composant
 * @param {React.ReactNode} props.content - Contenu du tooltip
 * @param {string} [props.className] - Classes CSS additionnelles
 *
 * @example
 * <InfoTooltip content="Ce champ est optionnel mais recommandé" />
 */
export function InfoTooltip({ content, className }) {
  return (
    <Tooltip content={content}>
      <button
        type="button"
        className={clsx(
          'inline-flex items-center justify-center',
          'h-4 w-4 rounded-full',
          'bg-slate-100 text-slate-500',
          'hover:bg-slate-200 hover:text-slate-700',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
          'transition-colors',
          className
        )}
        aria-label="Plus d'informations"
      >
        <svg
          className="h-3 w-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </button>
    </Tooltip>
  );
}
