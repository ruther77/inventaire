/**
 * GlassCard - Carte avec effet glassmorphism
 * Design Next-Gen 2025
 */

import { forwardRef } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

const GlassCard = forwardRef(function GlassCard({
  children,
  className,
  variant = 'default', // 'default', 'elevated', 'bordered', 'gradient'
  gradient,
  glow,
  hover = true,
  padding = 'md',
  onClick,
  as: Component = 'div',
  ...props
}, ref) {
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
    xl: 'p-8',
  };

  const variantClasses = {
    default: 'bg-white/5 border-white/10',
    elevated: 'bg-white/10 border-white/20 shadow-xl shadow-black/20',
    bordered: 'bg-transparent border-white/20',
    gradient: 'bg-gradient-to-br border-white/10',
  };

  const MotionComponent = motion[Component] || motion.div;

  return (
    <MotionComponent
      ref={ref}
      onClick={onClick}
      className={clsx(
        'relative rounded-2xl border backdrop-blur-xl overflow-hidden',
        variantClasses[variant],
        paddingClasses[padding],
        hover && onClick && 'cursor-pointer',
        gradient && variant === 'gradient' && gradient,
        className
      )}
      whileHover={hover && onClick ? { scale: 1.01, y: -2 } : undefined}
      whileTap={hover && onClick ? { scale: 0.99 } : undefined}
      style={glow ? {
        boxShadow: `0 0 40px -10px ${glow}`,
      } : undefined}
      {...props}
    >
      {children}
    </MotionComponent>
  );
});

export default GlassCard;

/**
 * GlassCardHeader - Header de carte
 */
export function GlassCardHeader({ children, className, icon: Icon, title, subtitle, actions }) {
  if (children) {
    return (
      <div className={clsx('flex items-center justify-between mb-4', className)}>
        {children}
      </div>
    );
  }

  return (
    <div className={clsx('flex items-center justify-between mb-4', className)}>
      <div className="flex items-center gap-3">
        {Icon && (
          <div className="p-2 rounded-lg bg-white/10">
            <Icon className="w-4 h-4 text-white" />
          </div>
        )}
        <div>
          {title && <h3 className="font-semibold text-white">{title}</h3>}
          {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

/**
 * GlassCardContent - Contenu de carte
 */
export function GlassCardContent({ children, className }) {
  return (
    <div className={className}>
      {children}
    </div>
  );
}

/**
 * GlassCardFooter - Footer de carte
 */
export function GlassCardFooter({ children, className }) {
  return (
    <div className={clsx('mt-4 pt-4 border-t border-white/10', className)}>
      {children}
    </div>
  );
}
