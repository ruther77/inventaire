/**
 * Transitions - Composants de transition pour navigation et états.
 *
 * Fonctionnalités:
 * - Page transitions fluides
 * - List item transitions (add/remove)
 * - Mode transitions (toggle between states)
 * - Layout animations
 * - Presence animations (mount/unmount)
 */

import { memo, useState, useEffect, useRef, useLayoutEffect, Children, cloneElement } from 'react';
import { useReducedMotion } from '../../hooks/useAccessibility';

/**
 * Presence - Anime l'entrée et sortie d'un élément.
 */
export function Presence({
  show,
  children,
  enter = 'fade',
  exit = 'fade',
  duration = 200,
  onExited,
}) {
  const reducedMotion = useReducedMotion();
  const [shouldRender, setShouldRender] = useState(show);
  const [isAnimating, setIsAnimating] = useState(false);
  const [phase, setPhase] = useState(show ? 'entered' : 'exited');

  useEffect(() => {
    if (show) {
      setShouldRender(true);
      setPhase('entering');
      setIsAnimating(true);

      const timer = setTimeout(() => {
        setPhase('entered');
        setIsAnimating(false);
      }, reducedMotion ? 0 : duration);

      return () => clearTimeout(timer);
    } else if (shouldRender) {
      setPhase('exiting');
      setIsAnimating(true);

      const timer = setTimeout(() => {
        setShouldRender(false);
        setPhase('exited');
        setIsAnimating(false);
        onExited?.();
      }, reducedMotion ? 0 : duration);

      return () => clearTimeout(timer);
    }
  }, [show, duration, reducedMotion, shouldRender, onExited]);

  if (!shouldRender) return null;

  const animations = {
    fade: {
      entering: { opacity: 0 },
      entered: { opacity: 1 },
      exiting: { opacity: 0 },
    },
    scale: {
      entering: { opacity: 0, transform: 'scale(0.95)' },
      entered: { opacity: 1, transform: 'scale(1)' },
      exiting: { opacity: 0, transform: 'scale(0.95)' },
    },
    slideUp: {
      entering: { opacity: 0, transform: 'translateY(10px)' },
      entered: { opacity: 1, transform: 'translateY(0)' },
      exiting: { opacity: 0, transform: 'translateY(10px)' },
    },
    slideDown: {
      entering: { opacity: 0, transform: 'translateY(-10px)' },
      entered: { opacity: 1, transform: 'translateY(0)' },
      exiting: { opacity: 0, transform: 'translateY(-10px)' },
    },
    slideLeft: {
      entering: { opacity: 0, transform: 'translateX(10px)' },
      entered: { opacity: 1, transform: 'translateX(0)' },
      exiting: { opacity: 0, transform: 'translateX(10px)' },
    },
    slideRight: {
      entering: { opacity: 0, transform: 'translateX(-10px)' },
      entered: { opacity: 1, transform: 'translateX(0)' },
      exiting: { opacity: 0, transform: 'translateX(-10px)' },
    },
  };

  const currentAnimation = phase === 'exiting' ? animations[exit] : animations[enter];
  const style = reducedMotion
    ? {}
    : {
        ...currentAnimation[phase],
        transition: `all ${duration}ms ease-out`,
      };

  return (
    <div style={style}>
      {children}
    </div>
  );
}

/**
 * SwitchTransition - Transition entre deux états.
 */
export function SwitchTransition({
  mode,
  children,
  duration = 200,
  animation = 'fade',
}) {
  const reducedMotion = useReducedMotion();
  const [currentChild, setCurrentChild] = useState(children);
  const [nextChild, setNextChild] = useState(null);
  const [phase, setPhase] = useState('idle');

  useEffect(() => {
    if (children.key !== currentChild.key) {
      setNextChild(children);
      setPhase('exiting');

      const timer = setTimeout(() => {
        setCurrentChild(children);
        setNextChild(null);
        setPhase('entering');

        setTimeout(() => {
          setPhase('idle');
        }, reducedMotion ? 0 : duration);
      }, reducedMotion ? 0 : duration);

      return () => clearTimeout(timer);
    }
  }, [children, currentChild.key, duration, reducedMotion]);

  const animations = {
    fade: {
      idle: {},
      exiting: { opacity: 0 },
      entering: { opacity: 1 },
    },
    slide: {
      idle: {},
      exiting: { opacity: 0, transform: 'translateX(-20px)' },
      entering: { opacity: 1, transform: 'translateX(0)' },
    },
  };

  const style = reducedMotion
    ? {}
    : {
        ...animations[animation][phase],
        transition: `all ${duration}ms ease-out`,
      };

  return (
    <div style={style}>
      {currentChild}
    </div>
  );
}

/**
 * Collapse - Animation d'expansion/collapse vertical.
 */
export const Collapse = memo(function Collapse({
  open,
  children,
  duration = 300,
  className = '',
}) {
  const reducedMotion = useReducedMotion();
  const contentRef = useRef(null);
  const [height, setHeight] = useState(open ? 'auto' : 0);
  const [overflow, setOverflow] = useState(open ? 'visible' : 'hidden');

  useLayoutEffect(() => {
    if (!contentRef.current) return;

    if (open) {
      const contentHeight = contentRef.current.scrollHeight;
      setHeight(contentHeight);
      setOverflow('hidden');

      const timer = setTimeout(() => {
        setHeight('auto');
        setOverflow('visible');
      }, reducedMotion ? 0 : duration);

      return () => clearTimeout(timer);
    } else {
      // Get current height before collapsing
      const contentHeight = contentRef.current.scrollHeight;
      setHeight(contentHeight);
      setOverflow('hidden');

      // Force reflow
      contentRef.current.offsetHeight;

      // Then animate to 0
      requestAnimationFrame(() => {
        setHeight(0);
      });
    }
  }, [open, duration, reducedMotion]);

  const style = {
    height,
    overflow,
    transition: reducedMotion ? 'none' : `height ${duration}ms ease-out`,
  };

  return (
    <div style={style}>
      <div ref={contentRef} className={className}>
        {children}
      </div>
    </div>
  );
});

/**
 * Flip - Animation flip pour changement de contenu.
 */
export function Flip({
  flipped,
  front,
  back,
  duration = 400,
  className = '',
}) {
  const reducedMotion = useReducedMotion();

  if (reducedMotion) {
    return <div className={className}>{flipped ? back : front}</div>;
  }

  return (
    <div
      className={`flip-container ${className}`}
      style={{
        perspective: '1000px',
      }}
    >
      <div
        className="flip-inner"
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          transition: `transform ${duration}ms ease-out`,
          transformStyle: 'preserve-3d',
          transform: flipped ? 'rotateY(180deg)' : 'rotateY(0)',
        }}
      >
        <div
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            backfaceVisibility: 'hidden',
          }}
        >
          {front}
        </div>
        <div
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            backfaceVisibility: 'hidden',
            transform: 'rotateY(180deg)',
          }}
        >
          {back}
        </div>
      </div>
    </div>
  );
}

/**
 * TransitionList - Liste avec animations pour add/remove.
 */
export function TransitionList({
  items,
  keyExtractor,
  renderItem,
  animation = 'slideUp',
  duration = 200,
  stagger = 50,
  className = '',
}) {
  const reducedMotion = useReducedMotion();
  const previousItems = useRef(new Set());
  const [animatingItems, setAnimatingItems] = useState(new Map());

  useEffect(() => {
    const currentKeys = new Set(items.map(keyExtractor));
    const prevKeys = previousItems.current;

    // Detect added items
    const addedKeys = [...currentKeys].filter(k => !prevKeys.has(k));

    // Detect removed items
    const removedKeys = [...prevKeys].filter(k => !currentKeys.has(k));

    if (!reducedMotion) {
      // Animate added items
      addedKeys.forEach((key, index) => {
        setAnimatingItems(prev => new Map(prev).set(key, { type: 'entering', delay: index * stagger }));
        setTimeout(() => {
          setAnimatingItems(prev => {
            const next = new Map(prev);
            next.delete(key);
            return next;
          });
        }, duration + index * stagger);
      });
    }

    previousItems.current = currentKeys;
  }, [items, keyExtractor, animation, duration, stagger, reducedMotion]);

  const animations = {
    slideUp: {
      entering: { opacity: 0, transform: 'translateY(20px)' },
      entered: { opacity: 1, transform: 'translateY(0)' },
    },
    slideRight: {
      entering: { opacity: 0, transform: 'translateX(-20px)' },
      entered: { opacity: 1, transform: 'translateX(0)' },
    },
    scale: {
      entering: { opacity: 0, transform: 'scale(0.9)' },
      entered: { opacity: 1, transform: 'scale(1)' },
    },
    fade: {
      entering: { opacity: 0 },
      entered: { opacity: 1 },
    },
  };

  return (
    <div className={className}>
      {items.map((item, index) => {
        const key = keyExtractor(item);
        const animState = animatingItems.get(key);

        const style = reducedMotion || !animState
          ? {}
          : {
              ...animations[animation].entering,
              animation: `item-enter ${duration}ms ease-out ${animState.delay}ms forwards`,
            };

        return (
          <div key={key} style={style}>
            {renderItem(item, index)}
          </div>
        );
      })}
      <style>{`
        @keyframes item-enter {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}

/**
 * PageTransition - Transition entre pages.
 */
export function PageTransition({
  children,
  transition = 'fade',
  duration = 300,
  className = '',
}) {
  const reducedMotion = useReducedMotion();
  const [displayChildren, setDisplayChildren] = useState(children);
  const [phase, setPhase] = useState('idle');

  useEffect(() => {
    if (children !== displayChildren) {
      setPhase('exit');

      const timer = setTimeout(() => {
        setDisplayChildren(children);
        setPhase('enter');

        setTimeout(() => {
          setPhase('idle');
        }, reducedMotion ? 0 : duration);
      }, reducedMotion ? 0 : duration);

      return () => clearTimeout(timer);
    }
  }, [children, displayChildren, duration, reducedMotion]);

  const transitions = {
    fade: {
      idle: { opacity: 1 },
      exit: { opacity: 0 },
      enter: { opacity: 1 },
    },
    slideLeft: {
      idle: { opacity: 1, transform: 'translateX(0)' },
      exit: { opacity: 0, transform: 'translateX(-30px)' },
      enter: { opacity: 1, transform: 'translateX(0)' },
    },
    slideUp: {
      idle: { opacity: 1, transform: 'translateY(0)' },
      exit: { opacity: 0, transform: 'translateY(-20px)' },
      enter: { opacity: 1, transform: 'translateY(0)' },
    },
    scale: {
      idle: { opacity: 1, transform: 'scale(1)' },
      exit: { opacity: 0, transform: 'scale(0.95)' },
      enter: { opacity: 1, transform: 'scale(1)' },
    },
  };

  const style = reducedMotion
    ? {}
    : {
        ...transitions[transition][phase],
        transition: `all ${duration}ms ease-out`,
      };

  return (
    <div className={className} style={style}>
      {displayChildren}
    </div>
  );
}

export default {
  Presence,
  SwitchTransition,
  Collapse,
  Flip,
  TransitionList,
  PageTransition,
};
