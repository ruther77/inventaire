/**
 * ProgressiveDisclosure - Composants de divulgation progressive.
 *
 * Fonctionnalités:
 * - Révélation progressive du contenu
 * - Accordéons avec sections dépliables
 * - Show more/less patterns
 * - Wizard multi-étapes
 * - Truncation intelligente avec expansion
 */

import { memo, useState, useCallback, useRef, useEffect, createContext, useContext } from 'react';
import { Collapse } from '../animations/Transitions';

/**
 * Context pour Accordion group.
 */
const AccordionContext = createContext(null);

/**
 * Accordion - Conteneur pour sections dépliables.
 */
export function Accordion({
  children,
  allowMultiple = false,
  defaultOpenItems = [],
  className = '',
}) {
  const [openItems, setOpenItems] = useState(new Set(defaultOpenItems));

  const toggleItem = useCallback((id) => {
    setOpenItems((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        if (!allowMultiple) {
          next.clear();
        }
        next.add(id);
      }
      return next;
    });
  }, [allowMultiple]);

  const isOpen = useCallback((id) => openItems.has(id), [openItems]);

  return (
    <AccordionContext.Provider value={{ toggleItem, isOpen }}>
      <div className={`divide-y divide-slate-200 ${className}`}>
        {children}
      </div>
    </AccordionContext.Provider>
  );
}

/**
 * AccordionItem - Section dépliable individuelle.
 */
export const AccordionItem = memo(function AccordionItem({
  id,
  title,
  subtitle,
  icon,
  children,
  disabled = false,
  className = '',
}) {
  const context = useContext(AccordionContext);
  const [localOpen, setLocalOpen] = useState(false);

  // Support standalone ou dans Accordion
  const isOpen = context ? context.isOpen(id) : localOpen;
  const toggle = context
    ? () => !disabled && context.toggleItem(id)
    : () => !disabled && setLocalOpen(!localOpen);

  return (
    <div className={className}>
      <button
        type="button"
        onClick={toggle}
        disabled={disabled}
        aria-expanded={isOpen}
        aria-controls={`accordion-panel-${id}`}
        className={`
          flex w-full items-center justify-between gap-4 py-4 text-left
          transition-colors duration-150
          ${disabled ? 'cursor-not-allowed opacity-50' : 'hover:bg-slate-50'}
        `}
      >
        <div className="flex items-center gap-3">
          {icon && <span className="text-slate-400">{icon}</span>}
          <div>
            <div className="font-medium text-slate-900">{title}</div>
            {subtitle && <div className="text-sm text-slate-500">{subtitle}</div>}
          </div>
        </div>
        <ChevronIcon isOpen={isOpen} />
      </button>

      <Collapse open={isOpen}>
        <div
          id={`accordion-panel-${id}`}
          role="region"
          aria-labelledby={`accordion-header-${id}`}
          className="pb-4 text-slate-600"
        >
          {children}
        </div>
      </Collapse>
    </div>
  );
});

function ChevronIcon({ isOpen }) {
  return (
    <svg
      className={`h-5 w-5 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
}

/**
 * ShowMore - Bouton pour afficher plus de contenu.
 */
export function ShowMore({
  children,
  maxHeight = 200,
  showLabel = 'Voir plus',
  hideLabel = 'Voir moins',
  className = '',
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [needsExpansion, setNeedsExpansion] = useState(false);
  const contentRef = useRef(null);

  useEffect(() => {
    if (contentRef.current) {
      setNeedsExpansion(contentRef.current.scrollHeight > maxHeight);
    }
  }, [children, maxHeight]);

  return (
    <div className={className}>
      <div
        ref={contentRef}
        className="overflow-hidden transition-all duration-300"
        style={{
          maxHeight: isExpanded ? contentRef.current?.scrollHeight : maxHeight,
        }}
      >
        {children}
      </div>

      {needsExpansion && (
        <>
          {!isExpanded && (
            <div
              className="pointer-events-none relative -mt-12 h-12 bg-gradient-to-t from-white to-transparent"
              aria-hidden="true"
            />
          )}
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-2 text-sm font-medium text-brand-600 hover:text-brand-700"
          >
            {isExpanded ? hideLabel : showLabel}
          </button>
        </>
      )}
    </div>
  );
}

/**
 * TruncatedText - Texte tronqué avec expansion.
 */
export const TruncatedText = memo(function TruncatedText({
  text,
  maxLength = 150,
  showMoreLabel = '... Voir plus',
  showLessLabel = 'Voir moins',
  className = '',
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const needsTruncation = text.length > maxLength;

  if (!needsTruncation) {
    return <span className={className}>{text}</span>;
  }

  const displayText = isExpanded ? text : text.slice(0, maxLength);

  return (
    <span className={className}>
      {displayText}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="ml-1 font-medium text-brand-600 hover:text-brand-700"
      >
        {isExpanded ? showLessLabel : showMoreLabel}
      </button>
    </span>
  );
});

/**
 * Tabs - Navigation par onglets avec contenu progressif.
 */
export function Tabs({
  tabs,
  defaultTab,
  onChange,
  variant = 'underline', // underline | pills | boxed
  className = '',
}) {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);

  const handleTabChange = useCallback((tabId) => {
    setActiveTab(tabId);
    onChange?.(tabId);
  }, [onChange]);

  const variants = {
    underline: {
      container: 'border-b border-slate-200',
      tab: 'px-4 py-2 -mb-px border-b-2 transition-colors duration-150',
      active: 'border-brand-600 text-brand-600',
      inactive: 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300',
    },
    pills: {
      container: 'gap-2 p-1 bg-slate-100 rounded-xl',
      tab: 'px-4 py-2 rounded-lg transition-all duration-150',
      active: 'bg-white text-slate-900 shadow-sm',
      inactive: 'text-slate-500 hover:text-slate-700',
    },
    boxed: {
      container: 'border border-slate-200 rounded-xl overflow-hidden',
      tab: 'px-4 py-2 border-r border-slate-200 last:border-r-0 transition-colors duration-150',
      active: 'bg-brand-50 text-brand-700',
      inactive: 'bg-white text-slate-500 hover:bg-slate-50',
    },
  };

  const v = variants[variant];

  return (
    <div className={className}>
      <div
        role="tablist"
        className={`flex ${v.container}`}
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`tabpanel-${tab.id}`}
            onClick={() => handleTabChange(tab.id)}
            className={`
              ${v.tab}
              ${activeTab === tab.id ? v.active : v.inactive}
              font-medium text-sm
            `}
          >
            {tab.icon && <span className="mr-2">{tab.icon}</span>}
            {tab.label}
            {tab.badge && (
              <span className="ml-2 rounded-full bg-slate-200 px-2 py-0.5 text-xs">
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      <div className="mt-4">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            role="tabpanel"
            id={`tabpanel-${tab.id}`}
            aria-labelledby={tab.id}
            hidden={activeTab !== tab.id}
          >
            {activeTab === tab.id && tab.content}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Stepper - Wizard multi-étapes.
 */
export function Stepper({
  steps,
  currentStep,
  onStepChange,
  allowNavigation = false,
  variant = 'horizontal', // horizontal | vertical
  className = '',
}) {
  const isVertical = variant === 'vertical';

  return (
    <div className={`${isVertical ? '' : 'flex items-center'} ${className}`}>
      {steps.map((step, index) => {
        const isActive = index === currentStep;
        const isCompleted = index < currentStep;
        const isClickable = allowNavigation && (isCompleted || index === currentStep + 1);

        return (
          <div
            key={step.id || index}
            className={`
              flex items-center
              ${isVertical ? 'flex-row' : 'flex-1'}
              ${index < steps.length - 1 ? (isVertical ? 'pb-8' : '') : ''}
            `}
          >
            {/* Step indicator */}
            <button
              type="button"
              onClick={() => isClickable && onStepChange?.(index)}
              disabled={!isClickable}
              className={`
                flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full
                text-sm font-semibold transition-all duration-200
                ${isActive
                  ? 'bg-brand-600 text-white ring-4 ring-brand-100'
                  : isCompleted
                    ? 'bg-emerald-500 text-white'
                    : 'bg-slate-200 text-slate-500'
                }
                ${isClickable ? 'cursor-pointer hover:ring-2 hover:ring-brand-200' : 'cursor-default'}
              `}
            >
              {isCompleted ? (
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                index + 1
              )}
            </button>

            {/* Step content */}
            <div className={`${isVertical ? 'ml-4' : 'ml-3'} ${isVertical ? '' : 'hidden sm:block'}`}>
              <div className={`text-sm font-medium ${isActive ? 'text-brand-600' : 'text-slate-900'}`}>
                {step.title}
              </div>
              {step.description && (
                <div className="text-xs text-slate-500">{step.description}</div>
              )}
            </div>

            {/* Connector line */}
            {index < steps.length - 1 && (
              <div
                className={`
                  ${isVertical
                    ? 'absolute left-5 top-10 h-full w-0.5 -translate-x-1/2'
                    : 'mx-4 h-0.5 flex-1'
                  }
                  ${isCompleted ? 'bg-emerald-500' : 'bg-slate-200'}
                  transition-colors duration-200
                `}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

/**
 * RevealOnScroll - Révèle le contenu au scroll.
 */
export function RevealOnScroll({
  children,
  threshold = 0.1,
  rootMargin = '0px',
  animation = 'fadeUp',
  delay = 0,
  className = '',
}) {
  const [isVisible, setIsVisible] = useState(false);
  const elementRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTimeout(() => setIsVisible(true), delay);
          observer.disconnect();
        }
      },
      { threshold, rootMargin }
    );

    if (elementRef.current) {
      observer.observe(elementRef.current);
    }

    return () => observer.disconnect();
  }, [threshold, rootMargin, delay]);

  const animations = {
    fadeUp: {
      hidden: { opacity: 0, transform: 'translateY(20px)' },
      visible: { opacity: 1, transform: 'translateY(0)' },
    },
    fadeIn: {
      hidden: { opacity: 0 },
      visible: { opacity: 1 },
    },
    scaleIn: {
      hidden: { opacity: 0, transform: 'scale(0.95)' },
      visible: { opacity: 1, transform: 'scale(1)' },
    },
    slideRight: {
      hidden: { opacity: 0, transform: 'translateX(-20px)' },
      visible: { opacity: 1, transform: 'translateX(0)' },
    },
  };

  const anim = animations[animation];

  return (
    <div
      ref={elementRef}
      className={className}
      style={{
        ...anim[isVisible ? 'visible' : 'hidden'],
        transition: 'all 0.6s ease-out',
      }}
    >
      {children}
    </div>
  );
}

export default {
  Accordion,
  AccordionItem,
  ShowMore,
  TruncatedText,
  Tabs,
  Stepper,
  RevealOnScroll,
};
