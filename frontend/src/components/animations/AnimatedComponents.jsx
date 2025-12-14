/**
 * AnimatedComponents - Composants avec micro-interactions avancées.
 *
 * Fonctionnalités:
 * - Animations fluides et naturelles
 * - Respect de prefers-reduced-motion
 * - Spring physics pour effets réalistes
 * - Stagger animations pour listes
 * - Gesture support (drag, press, hover)
 */

import { memo, forwardRef } from 'react';
import { useReducedMotion } from '../../hooks/useAccessibility';

// Configuration d'animation partagée
const springConfig = {
  gentle: { tension: 120, friction: 14 },
  snappy: { tension: 200, friction: 20 },
  bouncy: { tension: 300, friction: 10 },
  stiff: { tension: 400, friction: 30 },
};

const duration = {
  instant: 100,
  fast: 150,
  normal: 250,
  slow: 400,
};

/**
 * FadeIn - Animation d'apparition avec fade.
 */
export const FadeIn = memo(function FadeIn({
  children,
  delay = 0,
  duration: dur = duration.normal,
  className = '',
  as: Component = 'div',
  ...props
}) {
  const reducedMotion = useReducedMotion();

  const style = reducedMotion
    ? {}
    : {
        animation: `fadeIn ${dur}ms ease-out ${delay}ms both`,
      };

  return (
    <Component className={className} style={style} {...props}>
      {children}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
    </Component>
  );
});

/**
 * SlideIn - Animation d'entrée avec slide.
 */
export const SlideIn = memo(function SlideIn({
  children,
  direction = 'up', // up, down, left, right
  delay = 0,
  duration: dur = duration.normal,
  distance = 20,
  className = '',
  as: Component = 'div',
  ...props
}) {
  const reducedMotion = useReducedMotion();

  const transforms = {
    up: `translateY(${distance}px)`,
    down: `translateY(-${distance}px)`,
    left: `translateX(${distance}px)`,
    right: `translateX(-${distance}px)`,
  };

  const animationName = `slideIn-${direction}-${distance}`;

  const style = reducedMotion
    ? {}
    : {
        animation: `${animationName} ${dur}ms ease-out ${delay}ms both`,
      };

  return (
    <Component className={className} style={style} {...props}>
      {children}
      <style>{`
        @keyframes ${animationName} {
          from {
            opacity: 0;
            transform: ${transforms[direction]};
          }
          to {
            opacity: 1;
            transform: translateX(0) translateY(0);
          }
        }
      `}</style>
    </Component>
  );
});

/**
 * ScaleIn - Animation d'apparition avec scale.
 */
export const ScaleIn = memo(function ScaleIn({
  children,
  delay = 0,
  duration: dur = duration.fast,
  initialScale = 0.95,
  className = '',
  as: Component = 'div',
  ...props
}) {
  const reducedMotion = useReducedMotion();

  const animationName = `scaleIn-${initialScale}`;

  const style = reducedMotion
    ? {}
    : {
        animation: `${animationName} ${dur}ms ease-out ${delay}ms both`,
      };

  return (
    <Component className={className} style={style} {...props}>
      {children}
      <style>{`
        @keyframes ${animationName} {
          from {
            opacity: 0;
            transform: scale(${initialScale});
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>
    </Component>
  );
});

/**
 * StaggerChildren - Animation stagger pour listes.
 */
export const StaggerChildren = memo(function StaggerChildren({
  children,
  staggerDelay = 50,
  initialDelay = 0,
  animation = 'fadeSlideUp',
  className = '',
  as: Component = 'div',
  ...props
}) {
  const reducedMotion = useReducedMotion();

  const animations = {
    fadeSlideUp: `
      @keyframes fadeSlideUp {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
    `,
    fadeSlideRight: `
      @keyframes fadeSlideRight {
        from {
          opacity: 0;
          transform: translateX(-10px);
        }
        to {
          opacity: 1;
          transform: translateX(0);
        }
      }
    `,
    scaleIn: `
      @keyframes scaleIn {
        from {
          opacity: 0;
          transform: scale(0.9);
        }
        to {
          opacity: 1;
          transform: scale(1);
        }
      }
    `,
  };

  return (
    <Component className={className} {...props}>
      {Array.isArray(children)
        ? children.map((child, index) => (
            <div
              key={index}
              style={
                reducedMotion
                  ? {}
                  : {
                      animation: `${animation} 200ms ease-out ${initialDelay + index * staggerDelay}ms both`,
                    }
              }
            >
              {child}
            </div>
          ))
        : children}
      <style>{animations[animation]}</style>
    </Component>
  );
});

/**
 * Pressable - Effet de press (scale down on click).
 */
export const Pressable = forwardRef(function Pressable(
  {
    children,
    scale = 0.97,
    duration: dur = duration.instant,
    disabled = false,
    className = '',
    as: Component = 'button',
    ...props
  },
  ref
) {
  const reducedMotion = useReducedMotion();

  const style = reducedMotion || disabled
    ? {}
    : {
        transition: `transform ${dur}ms ease-out`,
      };

  const activeStyle = reducedMotion || disabled
    ? ''
    : `transform: scale(${scale});`;

  return (
    <Component
      ref={ref}
      className={`pressable-component ${className}`}
      style={style}
      disabled={disabled}
      {...props}
    >
      {children}
      <style>{`
        .pressable-component:active {
          ${activeStyle}
        }
      `}</style>
    </Component>
  );
});

/**
 * Hoverable - Effet de hover avec scale et shadow.
 */
export const Hoverable = memo(function Hoverable({
  children,
  scale = 1.02,
  shadow = true,
  duration: dur = duration.fast,
  className = '',
  as: Component = 'div',
  ...props
}) {
  const reducedMotion = useReducedMotion();
  const id = `hoverable-${Math.random().toString(36).slice(2, 8)}`;

  const baseStyle = reducedMotion
    ? {}
    : {
        transition: `transform ${dur}ms ease-out, box-shadow ${dur}ms ease-out`,
      };

  return (
    <Component className={`${id} ${className}`} style={baseStyle} {...props}>
      {children}
      {!reducedMotion && (
        <style>{`
          .${id}:hover {
            transform: scale(${scale});
            ${shadow ? 'box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.15);' : ''}
          }
        `}</style>
      )}
    </Component>
  );
});

/**
 * Pulse - Animation de pulse pour attirer l'attention.
 */
export const Pulse = memo(function Pulse({
  children,
  active = true,
  color = 'rgba(59, 130, 246, 0.5)',
  className = '',
  ...props
}) {
  const reducedMotion = useReducedMotion();

  if (reducedMotion || !active) {
    return <div className={className} {...props}>{children}</div>;
  }

  return (
    <div className={`pulse-container ${className}`} {...props}>
      {children}
      <style>{`
        .pulse-container {
          position: relative;
        }
        .pulse-container::after {
          content: '';
          position: absolute;
          inset: -4px;
          border-radius: inherit;
          background: ${color};
          animation: pulse 2s ease-in-out infinite;
          z-index: -1;
        }
        @keyframes pulse {
          0%, 100% {
            opacity: 0;
            transform: scale(0.95);
          }
          50% {
            opacity: 0.5;
            transform: scale(1.05);
          }
        }
      `}</style>
    </div>
  );
});

/**
 * Skeleton - Animation de chargement skeleton.
 */
export const Skeleton = memo(function Skeleton({
  width = '100%',
  height = '1rem',
  rounded = 'md',
  className = '',
  ...props
}) {
  const reducedMotion = useReducedMotion();

  const roundedClasses = {
    none: 'rounded-none',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    full: 'rounded-full',
  };

  return (
    <div
      className={`${roundedClasses[rounded]} bg-slate-200 ${className}`}
      style={{ width, height }}
      {...props}
    >
      {!reducedMotion && (
        <div
          className="h-full w-full"
          style={{
            background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.5) 50%, transparent 100%)',
            backgroundSize: '200% 100%',
            animation: 'skeleton-shimmer 1.5s ease-in-out infinite',
          }}
        />
      )}
      <style>{`
        @keyframes skeleton-shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
});

/**
 * CountUp - Animation de comptage numérique.
 */
export function CountUp({
  end,
  start = 0,
  duration: dur = 1000,
  decimals = 0,
  prefix = '',
  suffix = '',
  className = '',
}) {
  const reducedMotion = useReducedMotion();
  const [current, setCurrent] = React.useState(reducedMotion ? end : start);

  React.useEffect(() => {
    if (reducedMotion) {
      setCurrent(end);
      return;
    }

    const startTime = performance.now();
    const diff = end - start;

    const animate = (time) => {
      const elapsed = time - startTime;
      const progress = Math.min(elapsed / dur, 1);

      // Easing function (ease-out)
      const eased = 1 - Math.pow(1 - progress, 3);

      setCurrent(start + diff * eased);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [end, start, dur, reducedMotion]);

  const formatted = current.toFixed(decimals);

  return (
    <span className={className}>
      {prefix}{formatted}{suffix}
    </span>
  );
}

// Import React for CountUp
import * as React from 'react';

/**
 * ProgressBar - Barre de progression animée.
 */
export const ProgressBar = memo(function ProgressBar({
  value = 0,
  max = 100,
  showLabel = true,
  color = 'brand',
  size = 'md',
  animated = true,
  className = '',
}) {
  const reducedMotion = useReducedMotion();
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  const colors = {
    brand: 'bg-brand-600',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    danger: 'bg-rose-500',
  };

  const sizes = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <div className={className}>
      <div className={`overflow-hidden rounded-full bg-slate-200 ${sizes[size]}`}>
        <div
          className={`${sizes[size]} ${colors[color]} transition-all duration-500 ease-out`}
          style={{ width: `${percentage}%` }}
        >
          {animated && !reducedMotion && (
            <div
              className="h-full w-full"
              style={{
                background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%)',
                backgroundSize: '200% 100%',
                animation: 'progress-shimmer 2s linear infinite',
              }}
            />
          )}
        </div>
      </div>
      {showLabel && (
        <div className="mt-1 text-right text-xs text-slate-500">
          {Math.round(percentage)}%
        </div>
      )}
      <style>{`
        @keyframes progress-shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
});

export default {
  FadeIn,
  SlideIn,
  ScaleIn,
  StaggerChildren,
  Pressable,
  Hoverable,
  Pulse,
  Skeleton,
  CountUp,
  ProgressBar,
  springConfig,
  duration,
};
