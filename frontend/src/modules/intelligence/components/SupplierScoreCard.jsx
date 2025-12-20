/**
 * SupplierScoreCard - Carte de scoring fournisseur
 *
 * Composant du plan de restructuration 2025-12 pour l'Intelligence Module.
 * Affiche le score multi-dimensionnel d'un fournisseur.
 */

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Truck,
  Clock,
  DollarSign,
  BarChart3,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Star,
} from 'lucide-react';
import clsx from 'clsx';

// ============================================================================
// UTILITIES
// ============================================================================

const DIMENSIONS = {
  price: {
    id: 'price',
    label: 'Prix',
    icon: DollarSign,
    description: 'Compétitivité tarifaire',
  },
  delivery: {
    id: 'delivery',
    label: 'Livraison',
    icon: Truck,
    description: 'Fiabilité des délais',
  },
  quality: {
    id: 'quality',
    label: 'Qualité',
    icon: Star,
    description: 'Conformité produits',
  },
  responsiveness: {
    id: 'responsiveness',
    label: 'Réactivité',
    icon: Clock,
    description: 'Rapidité de réponse',
  },
};

const getScoreColor = (score) => {
  if (score >= 80) return { color: 'emerald', label: 'Excellent' };
  if (score >= 60) return { color: 'blue', label: 'Bon' };
  if (score >= 40) return { color: 'amber', label: 'Moyen' };
  return { color: 'rose', label: 'Faible' };
};

const colorClasses = {
  emerald: {
    bg: 'bg-emerald-500/20',
    border: 'border-emerald-500/40',
    text: 'text-emerald-400',
    fill: 'fill-emerald-500',
    stroke: 'stroke-emerald-500',
  },
  blue: {
    bg: 'bg-blue-500/20',
    border: 'border-blue-500/40',
    text: 'text-blue-400',
    fill: 'fill-blue-500',
    stroke: 'stroke-blue-500',
  },
  amber: {
    bg: 'bg-amber-500/20',
    border: 'border-amber-500/40',
    text: 'text-amber-400',
    fill: 'fill-amber-500',
    stroke: 'stroke-amber-500',
  },
  rose: {
    bg: 'bg-rose-500/20',
    border: 'border-rose-500/40',
    text: 'text-rose-400',
    fill: 'fill-rose-500',
    stroke: 'stroke-rose-500',
  },
};

// ============================================================================
// RADAR CHART (Simple SVG)
// ============================================================================

function ScoreRadar({ dimensions, size = 120 }) {
  const center = size / 2;
  const radius = size / 2 - 10;
  const angles = Object.keys(dimensions).map((_, i, arr) => (2 * Math.PI * i) / arr.length - Math.PI / 2);

  // Points du polygone de fond
  const bgPoints = angles
    .map((angle) => {
      const x = center + radius * Math.cos(angle);
      const y = center + radius * Math.sin(angle);
      return `${x},${y}`;
    })
    .join(' ');

  // Points du polygone des scores
  const scorePoints = Object.entries(dimensions)
    .map(([, value], i) => {
      const score = (value / 100) * radius;
      const x = center + score * Math.cos(angles[i]);
      const y = center + score * Math.sin(angles[i]);
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg width={size} height={size} className="mx-auto">
      {/* Grilles concentriques */}
      {[0.25, 0.5, 0.75, 1].map((scale) => (
        <polygon
          key={scale}
          points={angles
            .map((angle) => {
              const r = radius * scale;
              const x = center + r * Math.cos(angle);
              const y = center + r * Math.sin(angle);
              return `${x},${y}`;
            })
            .join(' ')}
          fill="none"
          stroke="#374151"
          strokeWidth="1"
        />
      ))}

      {/* Axes */}
      {angles.map((angle, i) => (
        <line
          key={i}
          x1={center}
          y1={center}
          x2={center + radius * Math.cos(angle)}
          y2={center + radius * Math.sin(angle)}
          stroke="#374151"
          strokeWidth="1"
        />
      ))}

      {/* Zone de score */}
      <motion.polygon
        points={scorePoints}
        fill="#8B5CF6"
        fillOpacity="0.3"
        stroke="#8B5CF6"
        strokeWidth="2"
        initial={{ opacity: 0, scale: 0.5 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        style={{ transformOrigin: 'center' }}
      />

      {/* Points aux sommets */}
      {Object.entries(dimensions).map(([key, value], i) => {
        const score = (value / 100) * radius;
        const x = center + score * Math.cos(angles[i]);
        const y = center + score * Math.sin(angles[i]);
        return (
          <circle key={key} cx={x} cy={y} r="4" fill="#8B5CF6" stroke="#fff" strokeWidth="2" />
        );
      })}

      {/* Labels */}
      {Object.keys(dimensions).map((key, i) => {
        const labelRadius = radius + 15;
        const x = center + labelRadius * Math.cos(angles[i]);
        const y = center + labelRadius * Math.sin(angles[i]);
        const dim = DIMENSIONS[key];
        return (
          <text
            key={key}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-xs fill-slate-400"
          >
            {dim?.label || key}
          </text>
        );
      })}
    </svg>
  );
}

// ============================================================================
// DIMENSION BAR COMPONENT
// ============================================================================

function DimensionBar({ dimension, score, trend }) {
  const config = DIMENSIONS[dimension] || { label: dimension, icon: BarChart3 };
  const { color, label: scoreLabel } = getScoreColor(score);
  const colors = colorClasses[color];
  const Icon = config.icon;

  return (
    <div className="flex items-center gap-3">
      <div className={clsx('p-1.5 rounded', colors.bg)}>
        <Icon className={clsx('w-4 h-4', colors.text)} />
      </div>

      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm text-slate-300">{config.label}</span>
          <div className="flex items-center gap-1">
            <span className={clsx('text-sm font-medium', colors.text)}>{score}%</span>
            {trend !== undefined && (
              <span className={clsx(
                'text-xs',
                trend >= 0 ? 'text-emerald-400' : 'text-rose-400'
              )}>
                {trend >= 0 ? '+' : ''}{trend}%
              </span>
            )}
          </div>
        </div>
        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${score}%` }}
            transition={{ duration: 0.5 }}
            className={clsx('h-full rounded-full', `bg-${color}-500`)}
          />
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// SUPPLIER SCORE CARD COMPONENT
// ============================================================================

export default function SupplierScoreCard({
  supplier,
  globalScore,
  dimensions = {},
  trend,
  invoiceCount,
  lastDelivery,
  showRadar = true,
  showDetails = true,
  onClick,
  className,
}) {
  const { color, label } = useMemo(() => getScoreColor(globalScore), [globalScore]);
  const colors = colorClasses[color];

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      onClick={onClick}
      className={clsx(
        'p-4 rounded-xl border cursor-pointer',
        'bg-gradient-to-br from-slate-800/50 to-slate-900/50',
        colors.border,
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h4 className="font-semibold text-white">{supplier}</h4>
          {invoiceCount && (
            <p className="text-xs text-slate-500">{invoiceCount} factures analysées</p>
          )}
        </div>

        {/* Global Score Badge */}
        <div className={clsx('px-3 py-1.5 rounded-lg', colors.bg)}>
          <div className="flex items-center gap-2">
            <span className={clsx('text-2xl font-bold', colors.text)}>{globalScore}</span>
            <div className="flex flex-col">
              <span className={clsx('text-xs', colors.text)}>{label}</span>
              {trend !== undefined && (
                <span className={clsx(
                  'text-xs flex items-center gap-0.5',
                  trend >= 0 ? 'text-emerald-400' : 'text-rose-400'
                )}>
                  {trend >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                  {trend >= 0 ? '+' : ''}{trend}%
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Radar Chart */}
      {showRadar && Object.keys(dimensions).length >= 3 && (
        <div className="mb-4">
          <ScoreRadar dimensions={dimensions} size={140} />
        </div>
      )}

      {/* Dimensions Details */}
      {showDetails && Object.keys(dimensions).length > 0 && (
        <div className="space-y-3">
          {Object.entries(dimensions).map(([key, value]) => (
            <DimensionBar key={key} dimension={key} score={value} />
          ))}
        </div>
      )}

      {/* Footer */}
      {lastDelivery && (
        <div className="mt-4 pt-3 border-t border-white/10">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Dernière livraison</span>
            <span>{new Date(lastDelivery).toLocaleDateString('fr-FR')}</span>
          </div>
        </div>
      )}
    </motion.div>
  );
}

// Export named
export { ScoreRadar, DimensionBar, DIMENSIONS };
