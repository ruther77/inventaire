/**
 * MiniChart - Graphiques miniatures pour cartes et dashboards
 * Design Next-Gen 2025
 */

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

// ============================================================================
// SPARKLINE - Graphique en ligne simple
// ============================================================================

export function Sparkline({
  data = [],
  width = 100,
  height = 30,
  color = 'blue',
  showArea = true,
  animate = true,
  className,
}) {
  const colorClasses = {
    blue: { stroke: '#3b82f6', fill: 'rgba(59, 130, 246, 0.2)' },
    emerald: { stroke: '#10b981', fill: 'rgba(16, 185, 129, 0.2)' },
    amber: { stroke: '#f59e0b', fill: 'rgba(245, 158, 11, 0.2)' },
    rose: { stroke: '#f43f5e', fill: 'rgba(244, 63, 94, 0.2)' },
    violet: { stroke: '#8b5cf6', fill: 'rgba(139, 92, 246, 0.2)' },
  };

  const colors = colorClasses[color] || colorClasses.blue;

  const path = useMemo(() => {
    if (!data || data.length < 2) return '';

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    const points = data.map((value, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((value - min) / range) * height * 0.8 - height * 0.1;
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  }, [data, width, height]);

  const areaPath = useMemo(() => {
    if (!path) return '';
    return `${path} L ${width},${height} L 0,${height} Z`;
  }, [path, width, height]);

  if (!data || data.length < 2) {
    return (
      <div
        className={clsx('flex items-center justify-center text-slate-500 text-xs', className)}
        style={{ width, height }}
      >
        No data
      </div>
    );
  }

  return (
    <svg
      width={width}
      height={height}
      className={className}
      viewBox={`0 0 ${width} ${height}`}
    >
      {showArea && (
        <motion.path
          d={areaPath}
          fill={colors.fill}
          initial={animate ? { opacity: 0 } : undefined}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        />
      )}
      <motion.path
        d={path}
        fill="none"
        stroke={colors.stroke}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={animate ? { pathLength: 0 } : undefined}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1, ease: 'easeOut' }}
      />
    </svg>
  );
}

// ============================================================================
// MINI BAR CHART - Barres verticales miniatures
// ============================================================================

export function MiniBarChart({
  data = [],
  width = 100,
  height = 30,
  color = 'blue',
  gap = 2,
  animate = true,
  className,
}) {
  const colorClasses = {
    blue: 'fill-blue-500',
    emerald: 'fill-emerald-500',
    amber: 'fill-amber-500',
    rose: 'fill-rose-500',
    violet: 'fill-violet-500',
  };

  const barColor = colorClasses[color] || colorClasses.blue;

  const bars = useMemo(() => {
    if (!data || data.length === 0) return [];

    const max = Math.max(...data, 1);
    const barWidth = (width - gap * (data.length - 1)) / data.length;

    return data.map((value, index) => ({
      x: index * (barWidth + gap),
      width: barWidth,
      height: (value / max) * height * 0.9,
      y: height - (value / max) * height * 0.9,
    }));
  }, [data, width, height, gap]);

  if (!data || data.length === 0) {
    return (
      <div
        className={clsx('flex items-center justify-center text-slate-500 text-xs', className)}
        style={{ width, height }}
      >
        No data
      </div>
    );
  }

  return (
    <svg
      width={width}
      height={height}
      className={className}
      viewBox={`0 0 ${width} ${height}`}
    >
      {bars.map((bar, index) => (
        <motion.rect
          key={index}
          x={bar.x}
          width={bar.width}
          rx="2"
          className={clsx(barColor, 'opacity-80')}
          initial={animate ? { y: height, height: 0 } : { y: bar.y, height: bar.height }}
          animate={{ y: bar.y, height: bar.height }}
          transition={{ duration: 0.5, delay: index * 0.05 }}
        />
      ))}
    </svg>
  );
}

// ============================================================================
// PROGRESS RING - Cercle de progression
// ============================================================================

export function ProgressRing({
  value = 0,
  max = 100,
  size = 60,
  strokeWidth = 6,
  color = 'blue',
  showValue = true,
  animate = true,
  className,
}) {
  const colorClasses = {
    blue: 'stroke-blue-500',
    emerald: 'stroke-emerald-500',
    amber: 'stroke-amber-500',
    rose: 'stroke-rose-500',
    violet: 'stroke-violet-500',
  };

  const ringColor = colorClasses[color] || colorClasses.blue;
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className={clsx('relative inline-flex items-center justify-center', className)}>
      <svg width={size} height={size} className="-rotate-90">
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
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          className={ringColor}
          strokeDasharray={circumference}
          initial={animate ? { strokeDashoffset: circumference } : { strokeDashoffset: offset }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: 'easeOut' }}
        />
      </svg>
      {showValue && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold text-white">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// TREND INDICATOR - Indicateur de tendance
// ============================================================================

export function TrendIndicator({
  value,
  previousValue,
  format = 'percent',
  showIcon = true,
  size = 'md',
  className,
}) {
  const diff = previousValue !== 0 ? ((value - previousValue) / Math.abs(previousValue)) * 100 : 0;
  const isPositive = diff > 0;
  const isNeutral = diff === 0;

  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const colorClass = isNeutral
    ? 'text-slate-400'
    : isPositive
      ? 'text-emerald-400'
      : 'text-rose-400';

  const formatValue = () => {
    if (format === 'percent') {
      return `${isPositive ? '+' : ''}${diff.toFixed(1)}%`;
    }
    if (format === 'absolute') {
      const absDiff = value - previousValue;
      return `${isPositive ? '+' : ''}${absDiff.toFixed(0)}`;
    }
    return diff.toFixed(1);
  };

  return (
    <span className={clsx('inline-flex items-center gap-1', colorClass, sizeClasses[size], className)}>
      {showIcon && (
        <svg
          className={clsx(
            'w-3 h-3',
            isNeutral ? '' : isPositive ? '' : 'rotate-180'
          )}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          {isNeutral ? (
            <path strokeLinecap="round" strokeWidth={2} d="M5 12h14" />
          ) : (
            <path strokeLinecap="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          )}
        </svg>
      )}
      <span className="font-medium">{formatValue()}</span>
    </span>
  );
}

// ============================================================================
// MINI PIE - Camembert miniature
// ============================================================================

export function MiniPie({
  data = [],
  size = 60,
  animate = true,
  className,
}) {
  const colors = [
    '#3b82f6', // blue
    '#10b981', // emerald
    '#f59e0b', // amber
    '#f43f5e', // rose
    '#8b5cf6', // violet
    '#06b6d4', // cyan
  ];

  const total = data.reduce((sum, item) => sum + (item.value || 0), 0);
  const radius = size / 2;
  const center = size / 2;

  const paths = useMemo(() => {
    if (!data || data.length === 0 || total === 0) return [];

    let currentAngle = -90;

    return data.map((item, index) => {
      const percentage = (item.value / total) * 100;
      const angle = (percentage / 100) * 360;
      const startAngle = currentAngle;
      const endAngle = currentAngle + angle;
      currentAngle = endAngle;

      const startRad = (startAngle * Math.PI) / 180;
      const endRad = (endAngle * Math.PI) / 180;

      const x1 = center + radius * Math.cos(startRad);
      const y1 = center + radius * Math.sin(startRad);
      const x2 = center + radius * Math.cos(endRad);
      const y2 = center + radius * Math.sin(endRad);

      const largeArcFlag = angle > 180 ? 1 : 0;

      const d = `M ${center} ${center} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;

      return {
        d,
        color: item.color || colors[index % colors.length],
        label: item.label,
        percentage,
      };
    });
  }, [data, total, size]);

  if (!data || data.length === 0) {
    return (
      <div
        className={clsx('flex items-center justify-center text-slate-500 text-xs', className)}
        style={{ width: size, height: size }}
      >
        No data
      </div>
    );
  }

  return (
    <svg width={size} height={size} className={className}>
      {paths.map((path, index) => (
        <motion.path
          key={index}
          d={path.d}
          fill={path.color}
          initial={animate ? { opacity: 0, scale: 0.8 } : undefined}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: index * 0.1 }}
          className="hover:opacity-80 transition-opacity cursor-pointer"
        />
      ))}
    </svg>
  );
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  Sparkline,
  MiniBarChart,
  ProgressRing,
  TrendIndicator,
  MiniPie,
};
