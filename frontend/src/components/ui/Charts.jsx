/**
 * Charts - Composants de graphiques pour tableaux de bord
 * Design System Next-Gen 2025 (Dark Theme)
 *
 * Composants:
 * - BarChart: Graphique à barres verticales
 * - AreaChart: Graphique en aires avec gradient
 * - DonutChart: Graphique en anneau avec légende
 * - ProgressRings: Groupe d'anneaux de progression
 * - SparklineCard: Carte avec mini graphique
 */

import { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';

// ============================================================================
// COULEURS DU DESIGN SYSTEM
// ============================================================================

const CHART_COLORS = {
  emerald: { solid: '#10b981', fill: 'rgba(16, 185, 129, 0.2)' },
  teal: { solid: '#06b6d4', fill: 'rgba(6, 182, 212, 0.2)' },
  amber: { solid: '#f59e0b', fill: 'rgba(245, 158, 11, 0.2)' },
  rose: { solid: '#f43f5e', fill: 'rgba(244, 63, 94, 0.2)' },
  blue: { solid: '#3b82f6', fill: 'rgba(59, 130, 246, 0.2)' },
  violet: { solid: '#8b5cf6', fill: 'rgba(139, 92, 246, 0.2)' },
  slate: { solid: 'rgba(255,255,255,0.2)', fill: 'rgba(255,255,255,0.05)' },
};

// ============================================================================
// BAR CHART - Graphique à barres verticales
// ============================================================================

/**
 * BarChart - Graphique à barres verticales avec légende
 *
 * @param {Object[]} data - Données [{label: 'Lun', value: 120, color: 'emerald'}]
 * @param {Object[]} series - Séries multiples [{name: 'Cette semaine', key: 'current', color: 'emerald'}]
 * @param {string} title - Titre du graphique
 * @param {Object[]} legend - Légende [{label: 'Cette semaine', color: 'emerald'}]
 * @param {number} height - Hauteur du graphique (défaut: 200)
 * @param {boolean} animate - Animation (défaut: true)
 * @param {boolean} showLabels - Afficher les labels (défaut: true)
 * @param {string} className - Classes CSS additionnelles
 */
export function BarChart({
  data = [],
  series,
  title,
  legend = [],
  height = 200,
  animate = true,
  showLabels = true,
  barWidth = 40,
  gap = 16,
  className,
}) {
  const [hoveredBar, setHoveredBar] = useState(null);

  const maxValue = useMemo(() => {
    if (series) {
      return Math.max(...data.flatMap(d => series.map(s => d[s.key] || 0)));
    }
    return Math.max(...data.map(d => d.value || 0), 1);
  }, [data, series]);

  const getColor = (colorName) => CHART_COLORS[colorName] || CHART_COLORS.emerald;

  return (
    <div className={clsx('', className)}>
      {/* Header */}
      {(title || legend.length > 0) && (
        <div className="flex justify-between items-center mb-6">
          {title && <span className="text-base font-semibold text-white">{title}</span>}
          {legend.length > 0 && (
            <div className="flex gap-4">
              {legend.map((item, idx) => (
                <div key={idx} className="flex items-center gap-1.5 text-xs text-slate-400">
                  <div
                    className="w-2.5 h-2.5 rounded-sm"
                    style={{ background: getColor(item.color).solid }}
                  />
                  <span>{item.label}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Chart */}
      <div
        className="flex items-end justify-around px-5"
        style={{ height }}
      >
        {data.map((item, index) => (
          <div
            key={index}
            className="flex flex-col items-center gap-2"
            style={{ flex: 1, maxWidth: barWidth + gap }}
          >
            {/* Bar(s) */}
            <div className="flex gap-1 items-end" style={{ height: height - 30 }}>
              {series ? (
                series.map((s, sIdx) => {
                  const value = item[s.key] || 0;
                  const barHeight = (value / maxValue) * (height - 30);
                  const colorObj = getColor(s.color);

                  return (
                    <motion.div
                      key={sIdx}
                      className="rounded-t-md cursor-pointer transition-opacity hover:opacity-80"
                      style={{
                        width: barWidth / series.length - 2,
                        background: colorObj.solid,
                      }}
                      initial={animate ? { height: 0 } : { height: barHeight }}
                      animate={{ height: barHeight }}
                      transition={{ duration: 0.5, delay: index * 0.05 + sIdx * 0.02 }}
                      onMouseEnter={() => setHoveredBar(`${index}-${sIdx}`)}
                      onMouseLeave={() => setHoveredBar(null)}
                    />
                  );
                })
              ) : (
                <motion.div
                  className="rounded-t-md cursor-pointer transition-opacity hover:opacity-80"
                  style={{
                    width: barWidth,
                    background: getColor(item.color || 'emerald').solid,
                  }}
                  initial={animate ? { height: 0 } : { height: (item.value / maxValue) * (height - 30) }}
                  animate={{ height: (item.value / maxValue) * (height - 30) }}
                  transition={{ duration: 0.5, delay: index * 0.05 }}
                  onMouseEnter={() => setHoveredBar(index)}
                  onMouseLeave={() => setHoveredBar(null)}
                />
              )}
            </div>

            {/* Label */}
            {showLabels && (
              <span className="text-[11px] text-slate-400">{item.label}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// AREA CHART - Graphique en aires avec gradient
// ============================================================================

/**
 * AreaChart - Graphique linéaire avec aire remplie
 *
 * @param {number[]} data - Valeurs numériques
 * @param {string[]} labels - Labels de l'axe X
 * @param {string} title - Titre du graphique
 * @param {string} color - Couleur (emerald, blue, amber, etc.)
 * @param {number} height - Hauteur du graphique (défaut: 200)
 * @param {boolean} animate - Animation (défaut: true)
 * @param {boolean} showGrid - Afficher la grille (défaut: true)
 * @param {string} className - Classes CSS additionnelles
 */
export function AreaChart({
  data = [],
  labels = [],
  title,
  color = 'emerald',
  height = 200,
  animate = true,
  showGrid = true,
  showDots = false,
  className,
}) {
  const [hoveredPoint, setHoveredPoint] = useState(null);

  const colorObj = CHART_COLORS[color] || CHART_COLORS.emerald;
  const gradientId = `area-gradient-${color}-${Math.random().toString(36).substr(2, 9)}`;

  const { linePath, areaPath, points } = useMemo(() => {
    if (!data || data.length < 2) return { linePath: '', areaPath: '', points: [] };

    const width = 400;
    const h = height;
    const padding = 10;

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    const pts = data.map((value, index) => {
      const x = padding + (index / (data.length - 1)) * (width - padding * 2);
      const y = h - padding - ((value - min) / range) * (h - padding * 2);
      return { x, y, value };
    });

    // Créer un chemin lissé avec courbes de Bézier
    let lineD = `M ${pts[0].x},${pts[0].y}`;

    for (let i = 1; i < pts.length; i++) {
      const prev = pts[i - 1];
      const curr = pts[i];
      const cpx = (prev.x + curr.x) / 2;
      lineD += ` Q ${cpx},${prev.y} ${cpx},${(prev.y + curr.y) / 2}`;
      lineD += ` T ${curr.x},${curr.y}`;
    }

    // Chemin simplifié pour meilleure compatibilité
    lineD = `M ${pts.map(p => `${p.x},${p.y}`).join(' L ')}`;

    const areaD = `${lineD} L ${pts[pts.length - 1].x},${h} L ${pts[0].x},${h} Z`;

    return { linePath: lineD, areaPath: areaD, points: pts };
  }, [data, height]);

  if (!data || data.length < 2) {
    return (
      <div className={clsx('flex items-center justify-center text-slate-500', className)} style={{ height }}>
        Pas de données
      </div>
    );
  }

  return (
    <div className={className}>
      {title && (
        <div className="mb-6">
          <span className="text-base font-semibold text-white">{title}</span>
        </div>
      )}

      <div style={{ height }} className="relative">
        {/* Grid lines */}
        {showGrid && (
          <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
            {[0, 1, 2, 3].map(i => (
              <div key={i} className="border-b border-white/5" />
            ))}
          </div>
        )}

        {/* SVG Chart */}
        <svg
          viewBox={`0 0 400 ${height}`}
          preserveAspectRatio="none"
          className="w-full h-full"
        >
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={colorObj.solid} stopOpacity="0.3" />
              <stop offset="100%" stopColor={colorObj.solid} stopOpacity="0" />
            </linearGradient>
          </defs>

          {/* Area fill */}
          <motion.path
            d={areaPath}
            fill={`url(#${gradientId})`}
            initial={animate ? { opacity: 0 } : undefined}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          />

          {/* Line */}
          <motion.path
            d={linePath}
            fill="none"
            stroke={colorObj.solid}
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={animate ? { pathLength: 0 } : undefined}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1, ease: 'easeOut' }}
          />

          {/* Dots */}
          {showDots && points.map((point, idx) => (
            <motion.circle
              key={idx}
              cx={point.x}
              cy={point.y}
              r={hoveredPoint === idx ? 6 : 4}
              fill={colorObj.solid}
              className="cursor-pointer"
              initial={animate ? { scale: 0 } : undefined}
              animate={{ scale: 1 }}
              transition={{ duration: 0.3, delay: idx * 0.05 }}
              onMouseEnter={() => setHoveredPoint(idx)}
              onMouseLeave={() => setHoveredPoint(null)}
            />
          ))}
        </svg>
      </div>

      {/* X-axis labels */}
      {labels.length > 0 && (
        <div className="flex justify-between pt-2 text-[11px] text-slate-400">
          {labels.map((label, idx) => (
            <span key={idx}>{label}</span>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// DONUT CHART - Graphique en anneau
// ============================================================================

/**
 * DonutChart - Graphique en anneau avec légende et valeur centrale
 *
 * @param {Object[]} data - Données [{label: 'Épicerie', value: 40, color: 'emerald'}]
 * @param {string} title - Titre du graphique
 * @param {string} centerValue - Valeur affichée au centre
 * @param {string} centerLabel - Label sous la valeur centrale
 * @param {number} size - Taille du graphique (défaut: 160)
 * @param {number} strokeWidth - Épaisseur de l'anneau (défaut: 12)
 * @param {boolean} showLegend - Afficher la légende (défaut: true)
 * @param {boolean} animate - Animation (défaut: true)
 * @param {string} className - Classes CSS additionnelles
 */
export function DonutChart({
  data = [],
  title,
  centerValue,
  centerLabel,
  size = 160,
  strokeWidth = 12,
  showLegend = true,
  animate = true,
  className,
}) {
  const [hoveredSegment, setHoveredSegment] = useState(null);

  const total = useMemo(() => data.reduce((sum, item) => sum + (item.value || 0), 0), [data]);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  const segments = useMemo(() => {
    let currentOffset = 0;

    return data.map((item, index) => {
      const percentage = total > 0 ? (item.value / total) * 100 : 0;
      const dashLength = (percentage / 100) * circumference;
      const dashOffset = -currentOffset;
      currentOffset += dashLength;

      const colorObj = CHART_COLORS[item.color] || CHART_COLORS.emerald;

      return {
        ...item,
        percentage,
        dashLength,
        dashOffset,
        color: colorObj.solid,
      };
    });
  }, [data, total, circumference]);

  const getColor = (colorName) => CHART_COLORS[colorName] || CHART_COLORS.emerald;

  return (
    <div className={className}>
      {title && (
        <div className="mb-6">
          <span className="text-base font-semibold text-white">{title}</span>
        </div>
      )}

      <div className="flex items-center gap-10">
        {/* Donut */}
        <div className="relative" style={{ width: size, height: size }}>
          <svg width={size} height={size} className="-rotate-90">
            {/* Background circle */}
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              strokeWidth={strokeWidth}
              className="stroke-white/5"
            />

            {/* Segments */}
            {segments.map((segment, idx) => (
              <motion.circle
                key={idx}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={segment.color}
                strokeWidth={hoveredSegment === idx ? strokeWidth + 2 : strokeWidth}
                strokeDasharray={`${segment.dashLength} ${circumference}`}
                strokeDashoffset={segment.dashOffset}
                strokeLinecap="round"
                className="cursor-pointer transition-all"
                initial={animate ? { strokeDasharray: `0 ${circumference}` } : undefined}
                animate={{ strokeDasharray: `${segment.dashLength} ${circumference}` }}
                transition={{ duration: 0.8, delay: idx * 0.1 }}
                onMouseEnter={() => setHoveredSegment(idx)}
                onMouseLeave={() => setHoveredSegment(null)}
              />
            ))}
          </svg>

          {/* Center value */}
          {(centerValue || centerLabel) && (
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              {centerValue && (
                <span className="text-2xl font-bold text-white">{centerValue}</span>
              )}
              {centerLabel && (
                <span className="text-xs text-slate-400">{centerLabel}</span>
              )}
            </div>
          )}
        </div>

        {/* Legend */}
        {showLegend && (
          <div className="flex flex-col gap-3">
            {data.map((item, idx) => {
              const colorObj = getColor(item.color);
              const percentage = total > 0 ? Math.round((item.value / total) * 100) : 0;

              return (
                <div
                  key={idx}
                  className={clsx(
                    'flex items-center gap-2.5 transition-opacity',
                    hoveredSegment !== null && hoveredSegment !== idx && 'opacity-50'
                  )}
                  onMouseEnter={() => setHoveredSegment(idx)}
                  onMouseLeave={() => setHoveredSegment(null)}
                >
                  <div
                    className="w-4 h-4 rounded"
                    style={{ background: colorObj.solid }}
                  />
                  <span className="text-sm text-slate-300 min-w-[80px]">{item.label}</span>
                  <span className="text-sm font-semibold text-white ml-auto">{percentage}%</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// PROGRESS RINGS - Groupe d'anneaux de progression
// ============================================================================

/**
 * ProgressRings - Groupe d'anneaux de progression pour objectifs
 *
 * @param {Object[]} rings - Anneaux [{label: 'CA Mensuel', value: 75, color: 'emerald'}]
 * @param {string} title - Titre du groupe
 * @param {number} size - Taille de chaque anneau (défaut: 80)
 * @param {number} strokeWidth - Épaisseur de l'anneau (défaut: 8)
 * @param {boolean} animate - Animation (défaut: true)
 * @param {string} className - Classes CSS additionnelles
 */
export function ProgressRings({
  rings = [],
  title,
  size = 80,
  strokeWidth = 8,
  animate = true,
  className,
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  const getColor = (colorName) => CHART_COLORS[colorName] || CHART_COLORS.emerald;

  return (
    <div className={className}>
      {title && (
        <div className="mb-6">
          <span className="text-base font-semibold text-white">{title}</span>
        </div>
      )}

      <div className="flex justify-around py-5">
        {rings.map((ring, idx) => {
          const percentage = Math.min(Math.max(ring.value || 0, 0), 100);
          const offset = circumference - (percentage / 100) * circumference;
          const colorObj = getColor(ring.color);

          return (
            <div key={idx} className="text-center">
              <svg
                width={size}
                height={size}
                className="-rotate-90"
              >
                {/* Background ring */}
                <circle
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  fill="none"
                  strokeWidth={strokeWidth}
                  className="stroke-white/10"
                />

                {/* Progress ring */}
                <motion.circle
                  cx={size / 2}
                  cy={size / 2}
                  r={radius}
                  fill="none"
                  stroke={colorObj.solid}
                  strokeWidth={strokeWidth}
                  strokeLinecap="round"
                  strokeDasharray={circumference}
                  initial={animate ? { strokeDashoffset: circumference } : { strokeDashoffset: offset }}
                  animate={{ strokeDashoffset: offset }}
                  transition={{ duration: 1, ease: 'easeOut', delay: idx * 0.1 }}
                />
              </svg>

              <div className="mt-2">
                <div className="text-sm font-semibold text-white">{percentage}%</div>
                <div className="text-xs text-slate-400">{ring.label}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================================
// SPARKLINE CARD - Carte avec mini graphique
// ============================================================================

/**
 * SparklineCard - Carte KPI avec sparkline intégré
 *
 * @param {string} title - Titre de la métrique
 * @param {string} subtitle - Sous-titre optionnel
 * @param {string|number} value - Valeur principale
 * @param {number[]} data - Données pour le sparkline
 * @param {string} color - Couleur du sparkline
 * @param {string} trend - Tendance ('up', 'down', 'neutral')
 * @param {string} trendValue - Valeur de la tendance (ex: '+12%')
 * @param {string} className - Classes CSS additionnelles
 */
export function SparklineCard({
  title,
  subtitle,
  value,
  data = [],
  color = 'emerald',
  trend,
  trendValue,
  className,
}) {
  const colorObj = CHART_COLORS[color] || CHART_COLORS.emerald;

  const sparklinePath = useMemo(() => {
    if (!data || data.length < 2) return '';

    const width = 100;
    const height = 40;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    const points = data.map((val, idx) => {
      const x = (idx / (data.length - 1)) * width;
      const y = height - ((val - min) / range) * height * 0.8 - height * 0.1;
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  }, [data]);

  const trendColors = {
    up: 'text-emerald-400',
    down: 'text-rose-400',
    neutral: 'text-slate-400',
  };

  return (
    <div className={clsx(
      'flex items-center gap-4 p-4 bg-white/[0.03] rounded-xl border border-white/10',
      className
    )}>
      {/* Info */}
      <div className="flex-1">
        <div className="text-sm font-medium text-white">{title}</div>
        {subtitle && <div className="text-xs text-slate-400">{subtitle}</div>}
      </div>

      {/* Sparkline */}
      {data.length >= 2 && (
        <svg width={100} height={40} className="shrink-0">
          <motion.path
            d={sparklinePath}
            fill="none"
            stroke={colorObj.solid}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1 }}
          />
        </svg>
      )}

      {/* Value */}
      <div className="text-right">
        <div className="text-lg font-bold text-white">{value}</div>
        {trend && trendValue && (
          <div className={clsx('text-xs font-medium', trendColors[trend])}>
            {trend === 'up' && '↑'}
            {trend === 'down' && '↓'}
            {trendValue}
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// CHART CARD - Wrapper pour graphiques
// ============================================================================

/**
 * ChartCard - Carte wrapper pour les graphiques
 */
export function ChartCard({ children, className }) {
  return (
    <div className={clsx(
      'bg-white/[0.03] border border-white/10 rounded-2xl p-6',
      className
    )}>
      {children}
    </div>
  );
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  BarChart,
  AreaChart,
  DonutChart,
  ProgressRings,
  SparklineCard,
  ChartCard,
  CHART_COLORS,
};
