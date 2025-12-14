/**
 * ForecastPage - Page de previsions interactives
 *
 * Permet de visualiser et explorer les previsions:
 * - Ventes
 * - Tresorerie (Cash Flow)
 * - Stock
 * - Prix
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import Skeleton from '../../components/ui/Skeleton.jsx';
import {
  forecastSales,
  fetchCashFlowForecast,
  fetchStockDepletionForecast,
} from '../../api/client.js';
import { tabContent, staggerContainer, staggerItem } from '../../ui/motion.js';

const HORIZONS = [
  { value: 7, label: '7 jours' },
  { value: 30, label: '30 jours' },
  { value: 90, label: '90 jours' },
];

const FORECAST_TYPES = [
  { value: 'sales', label: 'Ventes' },
  { value: 'cashflow', label: 'Tresorerie' },
  { value: 'stock', label: 'Stock' },
];

function normalizeForecastData(type, raw) {
  if (!raw) return [];

  // Réponses avec prédictions sous forme d'objet (sales, cash-flow)
  if (!Array.isArray(raw) && Array.isArray(raw.predictions)) {
    const confidence = raw.confidence ?? 0.8;
    const model = raw.method ?? (type === 'cashflow' ? 'cash-flow' : 'forecast');
    return raw.predictions.map((point) => ({
      date: point.date,
      predicted_value: Number(point.value) || 0,
      confidence_lower: Number(point.lower_bound ?? point.value ?? 0),
      confidence_upper: Number(point.upper_bound ?? point.value ?? 0),
      confidence,
      model,
    }));
  }

  // Stock depletion renvoie directement une liste
  if (type === 'stock' && Array.isArray(raw)) {
    return raw.map((item) => ({
      date: item.predicted_depletion_date || item.product_name,
      predicted_value: Number(item.days_until_depletion ?? 0),
      confidence_lower: Number(item.days_until_depletion ?? 0),
      confidence_upper: Number(item.days_until_depletion ?? 0),
      confidence: Number(item.confidence ?? 0.85),
      model: 'stock-depletion',
      product_name: item.product_name,
    }));
  }

  // Si la forme ne correspond pas, mieux vaut retourner un tableau vide
  return [];
}

function SegmentedControl({ options, value, onChange, layoutId = 'segment' }) {
  return (
    <div className="inline-flex rounded-xl bg-slate-100 p-1 relative">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className="relative rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          {value === option.value && (
            <motion.span
              layoutId={layoutId}
              className="absolute inset-0 bg-white rounded-lg shadow-sm"
              transition={{ type: 'spring', stiffness: 500, damping: 35 }}
            />
          )}
          <span className={`relative z-10 ${value === option.value ? 'text-slate-900' : 'text-slate-600 hover:text-slate-900'}`}>
            {option.label}
          </span>
        </button>
      ))}
    </div>
  );
}

function ForecastChart({ data }) {
  if (!data?.length) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex h-64 items-center justify-center rounded-xl border border-slate-200 bg-slate-50"
      >
        <p className="text-sm text-slate-500">Aucune donnee de prevision disponible</p>
      </motion.div>
    );
  }

  // Simple bar chart representation
  const maxValue = Math.max(...data.map((d) => d.predicted_value || 0));
  const minValue = Math.min(...data.map((d) => d.confidence_lower || 0));
  const range = maxValue - minValue || 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="rounded-xl border border-slate-200 bg-white p-4"
    >
      <div className="flex h-64 items-end gap-1">
        {data.slice(0, 30).map((point, index) => {
          const height = ((point.predicted_value - minValue) / range) * 100;
          const lowerHeight = ((point.confidence_lower - minValue) / range) * 100;
          const upperHeight = ((point.confidence_upper - minValue) / range) * 100;

          return (
            <motion.div
              key={index}
              initial={{ scaleY: 0 }}
              animate={{ scaleY: 1 }}
              transition={{ duration: 0.4, delay: index * 0.02, ease: [0.16, 1, 0.3, 1] }}
              style={{ originY: 1 }}
              className="group relative flex-1 flex flex-col items-center justify-end"
            >
              {/* Confidence interval */}
              <div
                className="absolute w-full bg-blue-100 rounded-t"
                style={{
                  height: `${upperHeight}%`,
                  bottom: `${lowerHeight}%`,
                }}
              />
              {/* Predicted value bar */}
              <motion.div
                className="relative z-10 w-full rounded-t bg-blue-500"
                style={{ height: `${height}%` }}
                whileHover={{ backgroundColor: 'rgb(37 99 235)', scale: 1.05 }}
                transition={{ duration: 0.15 }}
              />
              {/* Tooltip */}
              <div className="absolute bottom-full mb-2 hidden rounded bg-slate-900 px-2 py-1 text-xs text-white group-hover:block z-20">
                {point.date}: {point.predicted_value?.toLocaleString('fr-FR')} €
              </div>
            </motion.div>
          );
        })}
      </div>
      <div className="mt-2 flex justify-between text-xs text-slate-500">
        <span>{data[0]?.date}</span>
        <span>{data[data.length - 1]?.date}</span>
      </div>
    </motion.div>
  );
}

function MetricRow({ label, value, subtext }) {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 py-3 last:border-0">
      <span className="text-sm text-slate-600">{label}</span>
      <div className="text-right">
        <span className="font-semibold text-slate-900">{value}</span>
        {subtext && <p className="text-xs text-slate-500">{subtext}</p>}
      </div>
    </div>
  );
}

export default function ForecastPage() {
  const [forecastType, setForecastType] = useState('sales');
  const [horizon, setHorizon] = useState(30);

  // Fetch data based on type
  const forecastQuery = useQuery({
    queryKey: ['forecast', forecastType, horizon],
    queryFn: async () => {
      switch (forecastType) {
        case 'sales':
          return forecastSales({ horizon_days: horizon });
        case 'cashflow':
          return fetchCashFlowForecast({ horizonDays: horizon });
        case 'stock':
          return fetchStockDepletionForecast(horizon);
        default:
          return [];
      }
    },
    staleTime: 60000,
  });

  const isLoading = forecastQuery.isLoading;
  const isError = forecastQuery.isError;
  const errorMessage = forecastQuery.error?.response?.data?.detail || forecastQuery.error?.message;
  const rawData = forecastQuery.data;
  const data = normalizeForecastData(forecastType, rawData);

  // Calculate summary stats
  const summary = {
    total: data.reduce((sum, d) => sum + (Number(d.predicted_value) || 0), 0),
    avgConfidence: data.length
      ? data.reduce((sum, d) => sum + (Number(d.confidence) || 0.8), 0) / data.length
      : 0,
    trend: data.length > 1
      ? data[data.length - 1]?.predicted_value > data[0]?.predicted_value
        ? 'up'
        : 'down'
      : 'stable',
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <p className="text-xs uppercase tracking-[0.4em] text-slate-400">intelligence</p>
        <h1 className="text-2xl font-semibold text-slate-900">Previsions</h1>
        <p className="text-sm text-slate-500">
          Explorez les projections de votre activite basees sur l'historique.
        </p>
      </div>

      {/* Controls */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="flex flex-wrap items-center gap-4"
      >
        <SegmentedControl
          options={FORECAST_TYPES}
          value={forecastType}
          onChange={setForecastType}
          layoutId="forecast-type"
        />
        <SegmentedControl
          options={HORIZONS}
          value={horizon}
          onChange={setHorizon}
          layoutId="forecast-horizon"
        />
        <Button variant="ghost" size="sm" onClick={() => forecastQuery.refetch()}>
          Actualiser
        </Button>
      </motion.div>

      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col gap-4"
          >
            <Skeleton className="h-64 rounded-2xl" />
            <Skeleton className="h-32 rounded-2xl" />
          </motion.div>
        ) : isError ? (
          <motion.div
            key="error"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
          >
            <Card className="border-rose-200 bg-rose-50 text-rose-800">
              <div className="flex items-start gap-3">
                <span className="text-xl">⚠️</span>
                <div>
                  <h3 className="font-semibold">Impossible de charger la prevision</h3>
                  <p className="text-sm">
                    {errorMessage || "Erreur lors de l'appel /forecasting. Verifiez l'historique disponible (minimum 7 jours pour les ventes)."}
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>
        ) : (
          <motion.div
            key={`content-${forecastType}-${horizon}`}
            variants={tabContent}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="flex flex-col gap-6"
          >
            {/* Chart */}
            <Card>
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-slate-900">
                  {FORECAST_TYPES.find((t) => t.value === forecastType)?.label} - {horizon} jours
                </h2>
                <p className="text-sm text-slate-500">
                  Zone claire = intervalle de confiance
                </p>
              </div>
              <ForecastChart data={data} />
            </Card>

            {/* Summary */}
            <motion.div
              className="grid gap-4 md:grid-cols-2"
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
            >
              <motion.div variants={staggerItem}>
                <Card>
                  <h3 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-500">
                    Resume
                  </h3>
                  <MetricRow
                    label="Total prevu"
                    value={`${summary.total.toLocaleString('fr-FR')} €`}
                  />
                  <MetricRow
                    label="Confiance moyenne"
                    value={`${Math.round(summary.avgConfidence * 100)}%`}
                  />
                  <MetricRow
                    label="Tendance"
                    value={summary.trend === 'up' ? '↑ Hausse' : summary.trend === 'down' ? '↓ Baisse' : '→ Stable'}
                  />
                  <MetricRow
                    label="Points de donnees"
                    value={data.length}
                  />
                </Card>
              </motion.div>

              <motion.div variants={staggerItem}>
                <Card>
                  <h3 className="mb-3 text-sm font-semibold uppercase tracking-widest text-slate-500">
                    Methodologie
                  </h3>
                  <MetricRow
                    label="Modele"
                    value={data[0]?.model || 'Holt-Winters'}
                  />
                  <MetricRow
                    label="Historique utilise"
                    value="90 jours"
                  />
                  <MetricRow
                    label="Mise a jour"
                    value="Quotidienne"
                  />
                  <MetricRow
                    label="Saisonnalite"
                    value="Hebdomadaire"
                  />
                </Card>
              </motion.div>
            </motion.div>

            {/* Alerts */}
            <AnimatePresence>
              {summary.trend === 'down' && forecastType === 'cashflow' && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <Card className="border-amber-300 bg-amber-50">
                    <div className="flex items-start gap-4">
                      <motion.span
                        className="text-2xl"
                        animate={{ scale: [1, 1.1, 1] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                      >
                        ⚠️
                      </motion.span>
                      <div>
                        <h3 className="font-semibold text-amber-900">Alerte tresorerie</h3>
                        <p className="text-sm text-amber-700">
                          La prevision indique une tendance negative sur les {horizon} prochains jours.
                          Considerez reporter certaines depenses ou accelerer les encaissements.
                        </p>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
