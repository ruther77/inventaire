import { useMemo } from 'react';

/**
 * Sparkline - Mini graphique inline pour visualiser les tendances
 * Dark Theme Design System (2025 Next-Gen)
 */
export default function Sparkline({
  data = [],
  width = 100,
  height = 30,
  trend = 'neutral', // 'up' | 'down' | 'neutral'
  strokeWidth = 1.5,
  showDots = false,
  className = '',
}) {
  const { path, points, min, max } = useMemo(() => {
    if (!data || data.length < 2) {
      return { path: '', points: [], min: 0, max: 0 };
    }

    const values = data.map(v => (typeof v === 'number' ? v : 0));
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    const range = maxVal - minVal || 1;

    const padding = 4;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    const pts = values.map((val, i) => ({
      x: padding + (i / (values.length - 1)) * chartWidth,
      y: padding + chartHeight - ((val - minVal) / range) * chartHeight,
    }));

    // Créer le path SVG
    let d = `M ${pts[0].x} ${pts[0].y}`;
    for (let i = 1; i < pts.length; i++) {
      d += ` L ${pts[i].x} ${pts[i].y}`;
    }

    return { path: d, points: pts, min: minVal, max: maxVal };
  }, [data, width, height]);

  if (!data || data.length < 2) {
    return (
      <div
        className={`flex items-center justify-center text-xs text-slate-500 ${className}`}
        style={{ width, height }}
      >
        —
      </div>
    );
  }

  // Couleurs selon la tendance
  const strokeColor = {
    up: '#f43f5e', // rose-500
    down: '#10b981', // emerald-500
    neutral: '#64748b', // slate-500
  }[trend];

  const gradientId = `sparkline-gradient-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <svg
      width={width}
      height={height}
      className={className}
      viewBox={`0 0 ${width} ${height}`}
    >
      {/* Gradient pour le remplissage */}
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={strokeColor} stopOpacity="0.3" />
          <stop offset="100%" stopColor={strokeColor} stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* Zone remplie sous la courbe */}
      <path
        d={`${path} L ${points[points.length - 1]?.x || 0} ${height} L ${points[0]?.x || 0} ${height} Z`}
        fill={`url(#${gradientId})`}
      />

      {/* Ligne principale */}
      <path
        d={path}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Points optionnels */}
      {showDots && points.map((pt, i) => (
        <circle
          key={i}
          cx={pt.x}
          cy={pt.y}
          r={2}
          fill={strokeColor}
        />
      ))}

      {/* Point final mis en évidence */}
      {points.length > 0 && (
        <circle
          cx={points[points.length - 1].x}
          cy={points[points.length - 1].y}
          r={3}
          fill={strokeColor}
          className="animate-pulse"
        />
      )}
    </svg>
  );
}
