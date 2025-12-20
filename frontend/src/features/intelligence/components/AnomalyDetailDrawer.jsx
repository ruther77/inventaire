/**
 * AnomalyDetailDrawer - Drawer de detail anomalie (S3 - Anomalie Prix)
 *
 * Panneau contextuel affichant:
 * - Informations completes de l'anomalie
 * - Historique et contexte
 * - Comparatifs et graphiques
 * - Actions correctives
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Calendar,
  User,
  FileText,
  BarChart3,
  CheckCircle,
  XCircle,
  Clock,
  ExternalLink,
  ChevronRight,
  Info,
  Truck,
  Package,
  History,
  ArrowRight,
} from 'lucide-react';
import Button from '../../../components/ui/Button.jsx';
import Card from '../../../components/ui/Card.jsx';
import api from '../../../api/client.js';

// ===========================================================================
// Constants
// ===========================================================================

const SEVERITY_CONFIG = {
  critical: {
    bg: 'bg-rose-500/20',
    text: 'text-rose-400',
    border: 'border-rose-500/30',
    label: 'Critique',
    icon: XCircle,
  },
  high: {
    bg: 'bg-amber-500/20',
    text: 'text-amber-400',
    border: 'border-amber-500/30',
    label: 'Haute',
    icon: AlertTriangle,
  },
  medium: {
    bg: 'bg-blue-500/20',
    text: 'text-blue-400',
    border: 'border-blue-500/30',
    label: 'Moyenne',
    icon: Info,
  },
  low: {
    bg: 'bg-slate-500/20',
    text: 'text-slate-400',
    border: 'border-slate-500/30',
    label: 'Basse',
    icon: Info,
  },
};

const TYPE_LABELS = {
  price_spike: 'Pic de prix',
  amount_outlier: 'Montant anormal',
  duplicate_transaction: 'Transaction doublon',
  duplicate_invoice: 'Facture doublon',
  stock_variance: 'Ecart stock',
  unusual_amount: 'Montant inhabituel',
  supplier_behavior: 'Comportement fournisseur',
  sequence_gap: 'Gap de sequence',
  missing_invoice: 'Facture manquante',
  category_mismatch: 'Categorie incorrecte',
  velocity_spike: 'Pic de transactions',
};

// ===========================================================================
// API Functions
// ===========================================================================

const fetchAnomalyDetail = async (anomalyId) => {
  const { data } = await api.get(`/anomaly-detection/anomalies/${anomalyId}`);
  return data;
};

const fetchAnomalyContext = async (anomalyId) => {
  try {
    const { data } = await api.get(`/anomaly-detection/anomalies/${anomalyId}/context`);
    return data;
  } catch {
    return null;
  }
};

const fetchPriceHistory = async (productId) => {
  try {
    const { data } = await api.get(`/prices/history/${productId}`);
    return data;
  } catch {
    return [];
  }
};

// ===========================================================================
// Sub-components
// ===========================================================================

function SeverityBadge({ severity }) {
  const config = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.medium;
  const Icon = config.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium border ${config.bg} ${config.text} ${config.border}`}
    >
      <Icon className="w-4 h-4" />
      {config.label}
    </span>
  );
}

function MetricCard({ icon: Icon, label, value, subvalue, accent = 'text-white' }) {
  return (
    <div className="p-4 rounded-xl bg-white/5 border border-white/10">
      <div className="flex items-center gap-2 text-slate-400 text-xs uppercase tracking-wider mb-2">
        <Icon className="w-4 h-4" />
        {label}
      </div>
      <p className={`text-xl font-semibold ${accent}`}>{value}</p>
      {subvalue && <p className="text-xs text-slate-500 mt-1">{subvalue}</p>}
    </div>
  );
}

function TimelineItem({ event, isLast }) {
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center">
        <div className="w-2 h-2 rounded-full bg-slate-500" />
        {!isLast && <div className="w-0.5 flex-1 bg-white/10 my-1" />}
      </div>
      <div className="flex-1 pb-4">
        <p className="text-sm text-white">{event.description}</p>
        <p className="text-xs text-slate-500 mt-1">{formatDate(event.date)}</p>
      </div>
    </div>
  );
}

function ComparisonBar({ label, current, average, unit = 'EUR' }) {
  const diff = current - average;
  const diffPct = average > 0 ? ((diff / average) * 100) : 0;
  const isHigher = diff > 0;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">{label}</span>
        <span className={isHigher ? 'text-rose-400' : 'text-emerald-400'}>
          {isHigher ? '+' : ''}{diffPct.toFixed(1)}%
        </span>
      </div>
      <div className="relative h-2 bg-white/10 rounded-full overflow-hidden">
        <div
          className="absolute left-0 top-0 h-full bg-slate-500 rounded-full"
          style={{ width: `${Math.min(100, (average / Math.max(current, average)) * 100)}%` }}
        />
        <div
          className={`absolute left-0 top-0 h-full rounded-full ${isHigher ? 'bg-rose-500' : 'bg-emerald-500'}`}
          style={{ width: `${Math.min(100, (current / Math.max(current, average)) * 100)}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-slate-500">
        <span>Moyenne: {average.toFixed(2)} {unit}</span>
        <span>Actuel: {current.toFixed(2)} {unit}</span>
      </div>
    </div>
  );
}

function ActionButton({ icon: Icon, label, description, onClick, variant = 'default' }) {
  const variants = {
    default: 'border-white/10 hover:border-white/20 hover:bg-white/5',
    primary: 'border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20',
    warning: 'border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20',
    danger: 'border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20',
  };

  const iconColors = {
    default: 'text-slate-400',
    primary: 'text-cyan-400',
    warning: 'text-amber-400',
    danger: 'text-rose-400',
  };

  return (
    <motion.button
      type="button"
      onClick={onClick}
      className={`w-full p-4 rounded-xl border text-left transition-all ${variants[variant]}`}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 ${iconColors[variant]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <p className="font-medium text-white">{label}</p>
          <p className="text-sm text-slate-400 mt-0.5">{description}</p>
        </div>
        <ChevronRight className="w-5 h-5 text-slate-500" />
      </div>
    </motion.button>
  );
}

// ===========================================================================
// Main Component
// ===========================================================================

export default function AnomalyDetailDrawer({
  isOpen,
  onClose,
  anomaly,
  onResolve,
  onIgnore,
  onNavigate,
}) {
  const [activeTab, setActiveTab] = useState('details');

  // Queries
  const detailQuery = useQuery({
    queryKey: ['anomaly-detail', anomaly?.id],
    queryFn: () => fetchAnomalyDetail(anomaly?.id),
    enabled: isOpen && !!anomaly?.id,
  });

  const contextQuery = useQuery({
    queryKey: ['anomaly-context', anomaly?.id],
    queryFn: () => fetchAnomalyContext(anomaly?.id),
    enabled: isOpen && !!anomaly?.id,
  });

  const detail = detailQuery.data || anomaly;
  const context = contextQuery.data;

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Mock timeline data (would come from API)
  const timeline = context?.timeline || [
    { description: 'Prix mis a jour par fournisseur', date: detail?.detected_at },
    { description: 'Anomalie detectee automatiquement', date: detail?.detected_at },
    { description: 'Notification envoyee', date: detail?.detected_at },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 z-40"
            onClick={onClose}
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full max-w-lg bg-slate-900 border-l border-white/10 z-50 overflow-hidden flex flex-col"
          >
            {/* Header */}
            <div className="flex items-start justify-between p-6 border-b border-white/10">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <SeverityBadge severity={detail?.severity} />
                  <span className="text-xs text-slate-500">
                    #{detail?.id?.slice(0, 8) || 'N/A'}
                  </span>
                </div>
                <h2 className="text-xl font-semibold text-white">
                  {detail?.title || 'Anomalie detectee'}
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  {TYPE_LABELS[detail?.type] || detail?.type} - {formatDate(detail?.detected_at)}
                </p>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-white/10 transition"
              >
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 px-6 py-3 border-b border-white/10 bg-white/5">
              {[
                { id: 'details', label: 'Details' },
                { id: 'context', label: 'Contexte' },
                { id: 'actions', label: 'Actions' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    activeTab === tab.id
                      ? 'bg-white/10 text-white'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <AnimatePresence mode="wait">
                {activeTab === 'details' && (
                  <motion.div
                    key="details"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="space-y-6"
                  >
                    {/* Description */}
                    <div>
                      <h4 className="text-sm font-medium text-slate-300 mb-2">Description</h4>
                      <p className="text-slate-400">{detail?.description || 'Aucune description disponible.'}</p>
                    </div>

                    {/* Metrics */}
                    <div className="grid grid-cols-2 gap-4">
                      <MetricCard
                        icon={DollarSign}
                        label="Impact estime"
                        value={`${(detail?.impact || 0).toLocaleString('fr-FR')} EUR`}
                        subvalue="Sur la periode"
                        accent={detail?.impact > 500 ? 'text-rose-400' : 'text-amber-400'}
                      />
                      <MetricCard
                        icon={BarChart3}
                        label="Confiance"
                        value={`${((detail?.confidence || 0.85) * 100).toFixed(0)}%`}
                        subvalue="Score IA"
                        accent="text-cyan-400"
                      />
                    </div>

                    {/* Comparison */}
                    {detail?.details?.expected_amount && (
                      <div className="space-y-4">
                        <h4 className="text-sm font-medium text-slate-300">Comparaison</h4>
                        <ComparisonBar
                          label="Montant"
                          current={detail?.details?.actual_amount || 0}
                          average={detail?.details?.expected_amount || 0}
                        />
                      </div>
                    )}

                    {/* Details JSON */}
                    {detail?.details && (
                      <div>
                        <h4 className="text-sm font-medium text-slate-300 mb-2">Donnees brutes</h4>
                        <pre className="p-3 rounded-lg bg-white/5 text-xs text-slate-400 overflow-x-auto">
                          {JSON.stringify(detail.details, null, 2)}
                        </pre>
                      </div>
                    )}
                  </motion.div>
                )}

                {activeTab === 'context' && (
                  <motion.div
                    key="context"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="space-y-6"
                  >
                    {/* Entity info */}
                    {detail?.entity_type && (
                      <Card className="border-white/10 bg-white/5">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-white/10">
                            {detail.entity_type === 'product' ? (
                              <Package className="w-5 h-5 text-slate-400" />
                            ) : detail.entity_type === 'supplier' ? (
                              <Truck className="w-5 h-5 text-slate-400" />
                            ) : (
                              <FileText className="w-5 h-5 text-slate-400" />
                            )}
                          </div>
                          <div className="flex-1">
                            <p className="text-sm text-slate-400">Entite concernee</p>
                            <p className="font-medium text-white">
                              {detail.entity_name || `${detail.entity_type} #${detail.entity_id}`}
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onNavigate?.(detail.entity_type, detail.entity_id)}
                          >
                            <ExternalLink className="w-4 h-4" />
                          </Button>
                        </div>
                      </Card>
                    )}

                    {/* Timeline */}
                    <div>
                      <h4 className="text-sm font-medium text-slate-300 mb-4">Chronologie</h4>
                      <div className="space-y-0">
                        {timeline.map((event, idx) => (
                          <TimelineItem
                            key={idx}
                            event={event}
                            isLast={idx === timeline.length - 1}
                          />
                        ))}
                      </div>
                    </div>

                    {/* Similar anomalies */}
                    {context?.similar_anomalies?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-slate-300 mb-3">Anomalies similaires</h4>
                        <div className="space-y-2">
                          {context.similar_anomalies.map((similar, idx) => (
                            <div
                              key={idx}
                              className="p-3 rounded-lg bg-white/5 border border-white/10 flex items-center justify-between"
                            >
                              <div>
                                <p className="text-sm text-white">{similar.title}</p>
                                <p className="text-xs text-slate-500">{similar.date}</p>
                              </div>
                              <span className="text-xs text-slate-400">{similar.status}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}

                {activeTab === 'actions' && (
                  <motion.div
                    key="actions"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="space-y-4"
                  >
                    <p className="text-sm text-slate-400 mb-4">
                      Selectionnez une action pour traiter cette anomalie.
                    </p>

                    <ActionButton
                      icon={CheckCircle}
                      label="Marquer comme resolu"
                      description="L'anomalie a ete corrigee manuellement"
                      onClick={() => onResolve?.(detail?.id, 'resolved')}
                      variant="primary"
                    />

                    <ActionButton
                      icon={DollarSign}
                      label="Ajuster le prix"
                      description="Mettre a jour le prix dans le catalogue"
                      onClick={() => onNavigate?.('prices', detail?.entity_id)}
                      variant="default"
                    />

                    <ActionButton
                      icon={Truck}
                      label="Contacter le fournisseur"
                      description="Negocier ou signaler le probleme"
                      onClick={() => onNavigate?.('supplier', detail?.details?.supplier_id)}
                      variant="warning"
                    />

                    <ActionButton
                      icon={History}
                      label="Voir l'historique complet"
                      description="Analyser les variations passees"
                      onClick={() => onNavigate?.('history', detail?.entity_id)}
                      variant="default"
                    />

                    <ActionButton
                      icon={XCircle}
                      label="Ignorer l'anomalie"
                      description="Faux positif ou non pertinent"
                      onClick={() => onIgnore?.(detail?.id)}
                      variant="danger"
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Footer actions */}
            <div className="p-6 border-t border-white/10 bg-white/5">
              <div className="flex gap-3">
                <Button variant="ghost" className="flex-1" onClick={onClose}>
                  Fermer
                </Button>
                <Button
                  variant="primary"
                  className="flex-1"
                  onClick={() => onResolve?.(detail?.id, 'resolved')}
                >
                  <CheckCircle className="w-4 h-4" />
                  Resoudre
                </Button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
