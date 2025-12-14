/**
 * AnomaliesPage - Detection et gestion des anomalies
 *
 * Affiche les anomalies detectees automatiquement:
 * - Prix inhabituels
 * - Ecarts de stock
 * - Transactions suspectes
 * - Comportements fournisseurs
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import Skeleton from '../../components/ui/Skeleton.jsx';
import {
  fetchAnomalySummary,
  scanForAnomalies,
  resolveAnomaly,
} from '../../api/client.js';
import { staggerContainer, staggerItem, expandRow, kpiCard } from '../../ui/motion.js';

const SEVERITY_CONFIG = {
  critical: { bg: 'bg-rose-100', text: 'text-rose-700', border: 'border-rose-300', label: 'Critique' },
  high: { bg: 'bg-amber-100', text: 'text-amber-700', border: 'border-amber-300', label: 'Haute' },
  medium: { bg: 'bg-blue-100', text: 'text-blue-700', border: 'border-blue-300', label: 'Moyenne' },
  low: { bg: 'bg-slate-100', text: 'text-slate-700', border: 'border-slate-300', label: 'Basse' },
};

const TYPE_LABELS = {
  price_spike: 'Pic de prix',
  stock_variance: 'Ecart stock',
  duplicate_invoice: 'Facture doublon',
  unusual_amount: 'Montant inhabituel',
  supplier_behavior: 'Comportement fournisseur',
  sequence_gap: 'Gap de sequence',
};

function FilterChip({ label, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3 py-1 text-sm font-medium transition ${
        active
          ? 'bg-slate-900 text-white'
          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
      }`}
    >
      {label}
    </button>
  );
}

function StatCard({ label, value, severity }) {
  const config = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.low;
  return (
    <motion.div
      className={`rounded-2xl border p-4 ${config.border} ${config.bg} cursor-pointer`}
      variants={staggerItem}
      whileHover={kpiCard.hover}
      whileTap={kpiCard.tap}
    >
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">{label}</p>
      <p className={`text-3xl font-bold ${config.text}`}>{value}</p>
    </motion.div>
  );
}

function AnomalyRow({ anomaly, onResolve, onIgnore, isResolving }) {
  const config = SEVERITY_CONFIG[anomaly.severity] || SEVERITY_CONFIG.low;
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      className={`rounded-xl border ${config.border} ${config.bg} overflow-hidden`}
      variants={staggerItem}
      layout
    >
      <motion.div
        className="flex cursor-pointer items-center justify-between p-4"
        onClick={() => setExpanded(!expanded)}
        whileHover={{ backgroundColor: 'rgba(0,0,0,0.02)' }}
      >
        <div className="flex items-center gap-4">
          <motion.span
            className={`rounded-full px-2 py-1 text-xs font-medium ${config.bg} ${config.text}`}
            animate={anomaly.severity === 'critical' ? { scale: [1, 1.05, 1] } : {}}
            transition={{ duration: 1.5, repeat: Infinity }}
          >
            {config.label}
          </motion.span>
          <div>
            <p className="font-medium text-slate-900">{anomaly.title}</p>
            <p className="text-sm text-slate-600">
              {TYPE_LABELS[anomaly.type] || anomaly.type} - {anomaly.detected_at}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm font-semibold text-slate-700">
            Impact: {anomaly.impact?.toLocaleString('fr-FR')} €
          </span>
          <motion.span
            className="text-slate-400"
            animate={{ rotate: expanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            ▼
          </motion.span>
        </div>
      </motion.div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial="hidden"
            animate="visible"
            exit="exit"
            variants={expandRow}
            className="border-t border-slate-200 bg-white overflow-hidden"
          >
            <div className="p-4">
              <p className="mb-4 text-sm text-slate-600">{anomaly.description}</p>

              {/* Details */}
              {anomaly.details && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="mb-4 rounded-lg bg-slate-50 p-3"
                >
                  <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">
                    Details
                  </p>
                  <pre className="text-xs text-slate-700">
                    {JSON.stringify(anomaly.details, null, 2)}
                  </pre>
                </motion.div>
              )}

              {/* Actions */}
              <motion.div
                className="flex gap-3"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.15 }}
              >
                <Button
                  variant="brand"
                  size="sm"
                  onClick={() => onResolve(anomaly.id)}
                  disabled={isResolving}
                >
                  {isResolving ? 'Resolution...' : 'Marquer resolu'}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onIgnore(anomaly.id)}
                  disabled={isResolving}
                >
                  Ignorer
                </Button>
                {anomaly.entity_type && anomaly.entity_id && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      window.location.href = `/${anomaly.entity_type}/${anomaly.entity_id}`
                    }
                  >
                    Voir {anomaly.entity_type}
                  </Button>
                )}
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function AnomaliesPage() {
  const queryClient = useQueryClient();
  const [severityFilter, setSeverityFilter] = useState(null);
  const [typeFilter, setTypeFilter] = useState(null);

  // Queries
  const anomaliesQuery = useQuery({
    queryKey: ['anomalies', severityFilter, typeFilter],
    queryFn: () => fetchAnomalySummary({ severity: severityFilter, type: typeFilter }),
    staleTime: 30000,
    refetchInterval: 60000, // Auto-refresh every minute
  });

  // Mutations
  const scanMutation = useMutation({
    mutationFn: scanForAnomalies,
    onSuccess: () => {
      queryClient.invalidateQueries(['anomalies']);
    },
  });

  const resolveMutation = useMutation({
    mutationFn: ({ anomalyId, action }) => resolveAnomaly(anomalyId, { action }),
    onSuccess: () => {
      queryClient.invalidateQueries(['anomalies']);
    },
  });

  const isLoading = anomaliesQuery.isLoading;
  const data = anomaliesQuery.data || { items: [], total: 0, critical: 0, high: 0, medium: 0, low: 0 };

  const handleResolve = (anomalyId) => {
    resolveMutation.mutate({ anomalyId, action: 'resolved' });
  };

  const handleIgnore = (anomalyId) => {
    resolveMutation.mutate({ anomalyId, action: 'ignored' });
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">intelligence</p>
          <h1 className="text-2xl font-semibold text-slate-900">Anomalies</h1>
          <p className="text-sm text-slate-500">
            Detection automatique des ecarts et comportements inhabituels.
          </p>
        </div>
        <Button
          variant="brand"
          onClick={() => scanMutation.mutate()}
          disabled={scanMutation.isPending}
        >
          {scanMutation.isPending ? 'Analyse...' : 'Lancer un scan'}
        </Button>
      </div>

      {/* Stats */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24 rounded-2xl" />
          ))}
        </div>
      ) : (
        <motion.div
          className="grid gap-4 md:grid-cols-4"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <StatCard label="Total actives" value={data.total} severity="medium" />
          <StatCard label="Critiques" value={data.critical} severity="critical" />
          <StatCard label="Hautes" value={data.high} severity="high" />
          <StatCard
            label="Impact total"
            value={`${data.total_impact?.toLocaleString('fr-FR') || 0} €`}
            severity="medium"
          />
        </motion.div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <span className="text-sm font-medium text-slate-500">Severite:</span>
        <FilterChip
          label="Toutes"
          active={severityFilter === null}
          onClick={() => setSeverityFilter(null)}
        />
        <FilterChip
          label="Critique"
          active={severityFilter === 'critical'}
          onClick={() => setSeverityFilter('critical')}
        />
        <FilterChip
          label="Haute"
          active={severityFilter === 'high'}
          onClick={() => setSeverityFilter('high')}
        />
        <FilterChip
          label="Moyenne"
          active={severityFilter === 'medium'}
          onClick={() => setSeverityFilter('medium')}
        />
      </div>

      {/* List */}
      {isLoading ? (
        <div className="flex flex-col gap-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
      ) : data.items?.length > 0 ? (
        <motion.div
          className="flex flex-col gap-3"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <AnimatePresence>
            {data.items.map((anomaly) => (
              <AnomalyRow
                key={anomaly.id}
                anomaly={anomaly}
                onResolve={handleResolve}
                onIgnore={handleIgnore}
                isResolving={resolveMutation.isPending}
              />
            ))}
          </AnimatePresence>
        </motion.div>
      ) : (
        <Card className="border-emerald-200 bg-emerald-50">
          <div className="flex items-center gap-4 p-6">
            <span className="text-4xl">✓</span>
            <div>
              <h3 className="font-semibold text-emerald-900">Aucune anomalie detectee</h3>
              <p className="text-sm text-emerald-700">
                Votre activite est saine. Le systeme surveille en permanence vos donnees.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Scan info */}
      <Card className="bg-slate-50">
        <div className="flex items-start gap-4">
          <span className="text-xl">ℹ️</span>
          <div>
            <h3 className="font-medium text-slate-900">Detection automatique</h3>
            <p className="text-sm text-slate-600">
              Le systeme analyse en permanence vos transactions, prix et stocks pour detecter:
            </p>
            <ul className="mt-2 list-inside list-disc text-sm text-slate-600">
              <li>Variations de prix superieures a 20%</li>
              <li>Ecarts d'inventaire non expliques</li>
              <li>Factures potentiellement en double</li>
              <li>Montants inhabituels par rapport a l'historique</li>
              <li>Gaps dans les sequences de factures</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
}
