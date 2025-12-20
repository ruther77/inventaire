/**
 * ForecastChart - Graphique de prévisions avec intervalles de confiance
 *
 * Composant du plan de restructuration 2025-12 pour l'Intelligence Module.
 * Affiche les prévisions de ventes/stock avec bandes de confiance.
 */

import { useMemo } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { fr } from 'date-fns/locale';
import clsx from 'clsx';

// ============================================================================
// UTILITIES
// ============================================================================

const formatCurrency = (value) => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    maximumFractionDigits: 0,
  }).format(value);
};

const formatNumber = (value) => {
  return new Intl.NumberFormat('fr-FR').format(value);
};

const formatDate = (dateStr) => {
  try {
    const date = typeof dateStr === 'string' ? parseISO(dateStr) : dateStr;
    return format(date, 'dd MMM', { locale: fr });
  } catch {
    return dateStr;
  }
};

// ============================================================================
// CUSTOM TOOLTIP
// ============================================================================

function CustomTooltip({ active, payload, label, unit = '€' }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="bg-slate-800 border border-white/20 rounded-lg p-3 shadow-xl">
      <p className="text-xs text-slate-400 mb-2">{formatDate(label)}</p>
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center gap-2 text-sm">
          <span
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-slate-300">{entry.name}:</span>
          <span className="font-medium text-white">
            {unit === '€' ? formatCurrency(entry.value) : formatNumber(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// FORECAST CHART COMPONENT
// ============================================================================

export default function ForecastChart({
  data = [],
  actualKey = 'actual',
  forecastKey = 'forecast',
  lowerBoundKey = 'lower_bound',
  upperBoundKey = 'upper_bound',
  dateKey = 'date',
  unit = '€',
  title = 'Prévisions',
  subtitle,
  height = 300,
  showConfidenceBand = true,
  showReferenceLine = true,
  referenceValue,
  referenceLabel = 'Objectif',
  className,
}) {
  // Préparer les données
  const chartData = useMemo(() => {
    return data.map((item) => ({
      ...item,
      date: item[dateKey],
      actual: item[actualKey],
      forecast: item[forecastKey],
      lowerBound: item[lowerBoundKey],
      upperBound: item[upperBoundKey],
      // Pour la bande de confiance (Area entre lower et upper)
      confidenceBand: item[upperBoundKey] ? [item[lowerBoundKey], item[upperBoundKey]] : null,
    }));
  }, [data, dateKey, actualKey, forecastKey, lowerBoundKey, upperBoundKey]);

  // Calculer le domaine Y
  const yDomain = useMemo(() => {
    if (!chartData.length) return ['auto', 'auto'];

    let min = Infinity;
    let max = -Infinity;

    chartData.forEach((item) => {
      if (item.actual !== null && item.actual !== undefined) {
        min = Math.min(min, item.actual);
        max = Math.max(max, item.actual);
      }
      if (item.forecast !== null && item.forecast !== undefined) {
        min = Math.min(min, item.forecast);
        max = Math.max(max, item.forecast);
      }
      if (item.lowerBound !== null && item.lowerBound !== undefined) {
        min = Math.min(min, item.lowerBound);
      }
      if (item.upperBound !== null && item.upperBound !== undefined) {
        max = Math.max(max, item.upperBound);
      }
    });

    // Ajouter 10% de marge
    const padding = (max - min) * 0.1;
    return [Math.max(0, min - padding), max + padding];
  }, [chartData]);

  // Trouver l'index où commence la prévision (dernier point avec actual)
  const forecastStartIndex = useMemo(() => {
    for (let i = chartData.length - 1; i >= 0; i--) {
      if (chartData[i].actual !== null && chartData[i].actual !== undefined) {
        return i;
      }
    }
    return 0;
  }, [chartData]);

  return (
    <div className={clsx('p-4 rounded-2xl bg-slate-800/50 border border-white/10', className)}>
      {/* Header */}
      {(title || subtitle) && (
        <div className="mb-4">
          {title && <h3 className="font-semibold text-white">{title}</h3>}
          {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
        </div>
      )}

      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.05} />
            </linearGradient>
            <linearGradient id="actualGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />

          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fill: '#9CA3AF', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={{ stroke: '#374151' }}
          />

          <YAxis
            domain={yDomain}
            tickFormatter={(v) => unit === '€' ? `${(v / 1000).toFixed(0)}k` : formatNumber(v)}
            tick={{ fill: '#9CA3AF', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={{ stroke: '#374151' }}
          />

          <Tooltip content={<CustomTooltip unit={unit} />} />

          <Legend
            wrapperStyle={{ paddingTop: 10 }}
            formatter={(value) => <span className="text-slate-300 text-sm">{value}</span>}
          />

          {/* Bande de confiance */}
          {showConfidenceBand && (
            <Area
              type="monotone"
              dataKey="upperBound"
              stackId="confidence"
              stroke="none"
              fill="url(#confidenceGradient)"
              name="Intervalle de confiance"
            />
          )}

          {/* Zone sous actual */}
          <Area
            type="monotone"
            dataKey="actual"
            stroke="none"
            fill="url(#actualGradient)"
            name=""
          />

          {/* Ligne actual */}
          <Line
            type="monotone"
            dataKey="actual"
            stroke="#10B981"
            strokeWidth={2}
            dot={{ fill: '#10B981', strokeWidth: 0, r: 3 }}
            activeDot={{ fill: '#10B981', strokeWidth: 2, stroke: '#fff', r: 5 }}
            name="Réalisé"
            connectNulls={false}
          />

          {/* Ligne forecast */}
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#8B5CF6"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ fill: '#8B5CF6', strokeWidth: 0, r: 3 }}
            activeDot={{ fill: '#8B5CF6', strokeWidth: 2, stroke: '#fff', r: 5 }}
            name="Prévision"
          />

          {/* Ligne de référence (objectif) */}
          {showReferenceLine && referenceValue && (
            <ReferenceLine
              y={referenceValue}
              stroke="#F59E0B"
              strokeDasharray="3 3"
              label={{
                value: referenceLabel,
                position: 'right',
                fill: '#F59E0B',
                fontSize: 11,
              }}
            />
          )}

          {/* Ligne verticale pour séparer réalisé/prévision */}
          {forecastStartIndex > 0 && forecastStartIndex < chartData.length - 1 && (
            <ReferenceLine
              x={chartData[forecastStartIndex]?.date}
              stroke="#6B7280"
              strokeDasharray="3 3"
              label={{
                value: 'Aujourd\'hui',
                position: 'top',
                fill: '#9CA3AF',
                fontSize: 10,
              }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      {/* Legend additionnel */}
      <div className="flex items-center justify-center gap-4 mt-2 text-xs text-slate-400">
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-emerald-500" />
          Données réelles
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-0.5 bg-violet-500 opacity-50" style={{ backgroundImage: 'repeating-linear-gradient(90deg, #8B5CF6, #8B5CF6 3px, transparent 3px, transparent 6px)' }} />
          Prévisions
        </span>
        {showConfidenceBand && (
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-violet-500/30 rounded" />
            Intervalle 95%
          </span>
        )}
      </div>
    </div>
  );
}

// Export
export { CustomTooltip };
