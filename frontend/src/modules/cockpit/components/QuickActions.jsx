/**
 * QuickActions - Actions rapides du Cockpit
 *
 * Composant du plan de restructuration 2025-12 pour le Cockpit Central.
 * Fournit des raccourcis vers les actions les plus fréquentes.
 */

import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Receipt,
  Package,
  Wallet,
  BarChart3,
  Zap,
  FileText,
  ShoppingCart,
  TrendingUp,
  Settings,
  Download,
  Upload,
  Scan,
} from 'lucide-react';
import clsx from 'clsx';

// ============================================================================
// UTILITIES
// ============================================================================

const defaultActions = [
  {
    id: 'import-invoice',
    icon: Receipt,
    label: 'Scanner facture',
    description: 'Import PDF → Stock',
    path: '/operations/factures',
    variant: 'primary',
    gradient: 'from-blue-500 to-cyan-500',
  },
  {
    id: 'check-stock',
    icon: Package,
    label: 'Vérifier stock',
    description: 'Alertes & ruptures',
    path: '/operations/catalogue',
    variant: 'default',
    gradient: 'from-emerald-500 to-teal-500',
  },
  {
    id: 'treasury',
    icon: Wallet,
    label: 'Trésorerie',
    description: 'Flux & soldes',
    path: '/finances/tresorerie',
    variant: 'default',
    gradient: 'from-violet-500 to-purple-500',
  },
  {
    id: 'reports',
    icon: BarChart3,
    label: 'Rapports',
    description: 'Analytics',
    path: '/intelligence',
    variant: 'default',
    gradient: 'from-pink-500 to-rose-500',
  },
];

// ============================================================================
// ACTION BUTTON COMPONENT
// ============================================================================

function ActionButton({
  icon: Icon,
  label,
  description,
  variant = 'default',
  gradient,
  onClick,
  disabled = false,
  size = 'md',
}) {
  const sizeClasses = {
    sm: 'p-2 text-xs',
    md: 'p-3 text-sm',
    lg: 'p-4 text-base',
  };

  const variantClasses = {
    primary: 'bg-gradient-to-r text-white shadow-lg shadow-blue-500/25',
    default: 'bg-white/5 hover:bg-white/10 text-white',
    ghost: 'hover:bg-white/5 text-slate-300',
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02, y: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        'relative flex items-center gap-3 rounded-xl border border-white/10',
        'transition-all duration-200 w-full text-left',
        sizeClasses[size],
        variant === 'primary' && gradient
          ? `bg-gradient-to-r ${gradient}`
          : variantClasses[variant],
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      <div className={clsx(
        'p-2 rounded-lg',
        variant === 'primary'
          ? 'bg-white/20'
          : 'bg-white/5'
      )}>
        <Icon className="w-4 h-4" />
      </div>

      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{label}</p>
        {description && (
          <p className={clsx(
            'text-xs truncate mt-0.5',
            variant === 'primary' ? 'text-white/70' : 'text-slate-500'
          )}>
            {description}
          </p>
        )}
      </div>

      <Zap className={clsx(
        'w-4 h-4',
        variant === 'primary' ? 'text-white/50' : 'text-slate-500'
      )} />
    </motion.button>
  );
}

// ============================================================================
// QUICK ACTIONS PANEL COMPONENT
// ============================================================================

export default function QuickActionsPanel({
  actions = defaultActions,
  title = 'Actions rapides',
  columns = 2,
  showHeader = true,
  className,
}) {
  const navigate = useNavigate();

  const handleAction = (action) => {
    if (action.onClick) {
      action.onClick();
    } else if (action.path) {
      navigate(action.path);
    }
  };

  return (
    <div className={clsx(
      'p-4 rounded-2xl',
      'bg-gradient-to-br from-slate-800/50 to-slate-900/50',
      'border border-white/10',
      className
    )}>
      {/* Header */}
      {showHeader && (
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-amber-400" />
          <h3 className="font-semibold text-white">{title}</h3>
        </div>
      )}

      {/* Actions Grid */}
      <div className={clsx(
        'grid gap-2',
        columns === 1 && 'grid-cols-1',
        columns === 2 && 'grid-cols-2',
        columns === 3 && 'grid-cols-3',
        columns === 4 && 'grid-cols-4'
      )}>
        {actions.map((action) => (
          <ActionButton
            key={action.id}
            icon={action.icon}
            label={action.label}
            description={action.description}
            variant={action.variant}
            gradient={action.gradient}
            onClick={() => handleAction(action)}
            disabled={action.disabled}
          />
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// MINI ACTIONS ROW - Compact version for inline use
// ============================================================================

export function QuickActionsRow({ actions = defaultActions, className }) {
  const navigate = useNavigate();

  return (
    <div className={clsx('flex items-center gap-2 overflow-x-auto', className)}>
      {actions.map((action) => (
        <motion.button
          key={action.id}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => action.path && navigate(action.path)}
          className={clsx(
            'flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap',
            'border border-white/10 bg-white/5 hover:bg-white/10',
            'text-sm text-white transition-colors'
          )}
        >
          <action.icon className="w-4 h-4" />
          {action.label}
        </motion.button>
      ))}
    </div>
  );
}

// Export named components
export { ActionButton, defaultActions };
