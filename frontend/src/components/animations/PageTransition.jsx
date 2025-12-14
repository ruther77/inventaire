/**
 * PageTransition - Animations de transition de page
 * Design Next-Gen 2025
 */

import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';

// Variantes d'animation
const variants = {
  fadeSlide: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 },
  },
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },
  slideRight: {
    initial: { opacity: 0, x: -30 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 30 },
  },
  slideLeft: {
    initial: { opacity: 0, x: 30 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -30 },
  },
  scale: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 1.05 },
  },
  blur: {
    initial: { opacity: 0, filter: 'blur(10px)' },
    animate: { opacity: 1, filter: 'blur(0px)' },
    exit: { opacity: 0, filter: 'blur(10px)' },
  },
};

/**
 * PageTransition - Wrapper pour animer les transitions de page
 */
export default function PageTransition({
  children,
  variant = 'fadeSlide',
  duration = 0.3,
  delay = 0,
  className,
}) {
  const selectedVariant = variants[variant] || variants.fadeSlide;

  return (
    <motion.div
      initial={selectedVariant.initial}
      animate={selectedVariant.animate}
      exit={selectedVariant.exit}
      transition={{ duration, delay, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/**
 * StaggerContainer - Container pour animations en cascade
 */
export function StaggerContainer({
  children,
  staggerDelay = 0.1,
  initialDelay = 0,
  className,
}) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            delayChildren: initialDelay,
            staggerChildren: staggerDelay,
          },
        },
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/**
 * StaggerItem - Élément animé dans un StaggerContainer
 */
export function StaggerItem({ children, className }) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 },
      }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/**
 * FadeInView - Animation au scroll (viewport)
 */
export function FadeInView({
  children,
  className,
  threshold = 0.1,
  once = true,
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once, amount: threshold }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/**
 * AnimatedCounter - Compteur animé
 */
export function AnimatedCounter({
  value,
  duration = 1,
  decimals = 0,
  prefix = '',
  suffix = '',
  className,
}) {
  return (
    <motion.span
      className={className}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
    >
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        {prefix}
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: duration }}
        >
          {typeof value === 'number' ? value.toFixed(decimals) : value}
        </motion.span>
        {suffix}
      </motion.span>
    </motion.span>
  );
}

/**
 * PulseOnHover - Effet pulse au survol
 */
export function PulseOnHover({ children, className, color = 'blue' }) {
  const colorClasses = {
    blue: 'hover:shadow-blue-500/30',
    emerald: 'hover:shadow-emerald-500/30',
    amber: 'hover:shadow-amber-500/30',
    rose: 'hover:shadow-rose-500/30',
    violet: 'hover:shadow-violet-500/30',
  };

  return (
    <motion.div
      whileHover={{
        scale: 1.02,
        boxShadow: '0 0 30px -5px currentColor',
      }}
      whileTap={{ scale: 0.98 }}
      className={clsx('transition-shadow', colorClasses[color], className)}
    >
      {children}
    </motion.div>
  );
}

/**
 * ShimmerEffect - Effet shimmer/skeleton loading
 */
export function ShimmerEffect({ className, height = 'h-4', rounded = 'rounded' }) {
  return (
    <div
      className={clsx(
        'animate-pulse bg-gradient-to-r from-white/5 via-white/10 to-white/5',
        'bg-[length:200%_100%]',
        height,
        rounded,
        className
      )}
      style={{
        animation: 'shimmer 1.5s infinite',
      }}
    />
  );
}

/**
 * FloatingElement - Élément flottant animé
 */
export function FloatingElement({
  children,
  className,
  amplitude = 10,
  duration = 3,
}) {
  return (
    <motion.div
      animate={{
        y: [-amplitude / 2, amplitude / 2, -amplitude / 2],
      }}
      transition={{
        duration,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/**
 * GlowingBorder - Bordure lumineuse animée
 */
export function GlowingBorder({
  children,
  className,
  color = 'blue',
  intensity = 'medium',
}) {
  const intensityClasses = {
    low: 'shadow-md',
    medium: 'shadow-lg',
    high: 'shadow-xl',
  };

  const colorClasses = {
    blue: 'shadow-blue-500/30',
    emerald: 'shadow-emerald-500/30',
    amber: 'shadow-amber-500/30',
    rose: 'shadow-rose-500/30',
    violet: 'shadow-violet-500/30',
  };

  return (
    <motion.div
      animate={{
        boxShadow: [
          `0 0 20px -5px var(--glow-color)`,
          `0 0 40px -5px var(--glow-color)`,
          `0 0 20px -5px var(--glow-color)`,
        ],
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut',
      }}
      className={clsx(intensityClasses[intensity], colorClasses[color], className)}
      style={{
        '--glow-color': `var(--color-${color}-500)`,
      }}
    >
      {children}
    </motion.div>
  );
}
