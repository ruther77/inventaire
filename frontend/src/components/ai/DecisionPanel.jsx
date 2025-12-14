/**
 * DecisionPanel - Panneau de décisions assistées par IA
 * Scénario 3.5 du UX_NEXT_GEN_2025.md
 *
 * Affiche les décisions recommandées avec:
 * - Impact prévisionnel
 * - Actions groupées
 * - Filtres par type de décision
 */

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Package,
  DollarSign,
  Users,
  AlertTriangle,
  CheckCircle,
  Filter,
  Sparkles,
  ChevronRight,
  Zap,
} from 'lucide-react';
import clsx from 'clsx';
import SuggestionCard, { SuggestionList } from './SuggestionCard.jsx';
import QuickAction, { QuickActionGroup } from './QuickAction.jsx';
import { ImpactGrid } from './ImpactPreview.jsx';

// ============================================================================
// DECISION TYPES
// ============================================================================

const DECISION_TYPES = [
  { id: 'all', label: 'Toutes', icon: Brain },
  { id: 'pricing', label: 'Prix', icon: DollarSign },
  { id: 'stock', label: 'Stock', icon: Package },
  { id: 'supplier', label: 'Fournisseurs', icon: Users },
  { id: 'anomaly', label: 'Anomalies', icon: AlertTriangle },
];

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

/**
 * DecisionTypeFilter - Filtres par type de décision
 */
function DecisionTypeFilter({ value, onChange }) {
  return (
    <div className="flex flex-wrap gap-2">
      {DECISION_TYPES.map((type) => {
        const TypeIcon = type.icon;
        const isActive = value === type.id;

        return (
          <button
            key={type.id}
            onClick={() => onChange(type.id)}
            className={clsx(
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium',
              'transition-all duration-200',
              isActive
                ? 'bg-violet-500/20 text-violet-400 border border-violet-500/30'
                : 'bg-white/5 text-slate-400 border border-white/10 hover:bg-white/10'
            )}
          >
            <TypeIcon className="w-3.5 h-3.5" />
            {type.label}
          </button>
        );
      })}
    </div>
  );
}

/**
 * ImpactSummary - Résumé de l'impact total
 */
function ImpactSummary({ decisions }) {
  const totalImpact = useMemo(() => {
    const monthlyGain = decisions.reduce((acc, d) => {
      if (!d.impact?.monthly) return acc;
      const value = parseFloat(d.impact.monthly.replace(/[^\d.-]/g, '')) || 0;
      return acc + value;
    }, 0);

    const stockSavings = decisions
      .filter((d) => d.type === 'stock')
      .reduce((acc, d) => {
        if (!d.impact?.savings) return acc;
        const value = parseFloat(d.impact.savings.replace(/[^\d.-]/g, '')) || 0;
        return acc + value;
      }, 0);

    const anomaliesFixed = decisions.filter((d) => d.type === 'anomaly').length;

    return { monthlyGain, stockSavings, anomaliesFixed };
  }, [decisions]);

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
        <p className="text-xs text-emerald-400/70 mb-1">Gain mensuel potentiel</p>
        <p className="text-2xl font-bold text-emerald-400">
          +{totalImpact.monthlyGain.toLocaleString('fr-FR')}€
        </p>
      </div>
      <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
        <p className="text-xs text-blue-400/70 mb-1">Économies stock</p>
        <p className="text-2xl font-bold text-blue-400">
          {totalImpact.stockSavings.toLocaleString('fr-FR')}€
        </p>
      </div>
      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
        <p className="text-xs text-amber-400/70 mb-1">Anomalies à corriger</p>
        <p className="text-2xl font-bold text-amber-400">
          {totalImpact.anomaliesFixed}
        </p>
      </div>
    </div>
  );
}

/**
 * QuickDecision - Décision rapide (version compacte)
 */
function QuickDecision({ decision, onApply, onDismiss }) {
  const typeConfig = {
    pricing: { icon: DollarSign, color: 'amber' },
    stock: { icon: Package, color: 'blue' },
    supplier: { icon: Users, color: 'violet' },
    anomaly: { icon: AlertTriangle, color: 'rose' },
    optimization: { icon: TrendingUp, color: 'emerald' },
  };

  const config = typeConfig[decision.type] || typeConfig.optimization;
  const TypeIcon = config.icon;

  const colorClasses = {
    amber: 'border-amber-500/20 bg-amber-500/5',
    blue: 'border-blue-500/20 bg-blue-500/5',
    violet: 'border-violet-500/20 bg-violet-500/5',
    rose: 'border-rose-500/20 bg-rose-500/5',
    emerald: 'border-emerald-500/20 bg-emerald-500/5',
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -50 }}
      className={clsx(
        'p-3 rounded-lg border flex items-center gap-3',
        colorClasses[config.color]
      )}
    >
      <div className={`p-2 rounded-lg bg-${config.color}-500/20`}>
        <TypeIcon className={`w-4 h-4 text-${config.color}-400`} />
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{decision.title}</p>
        {decision.impact?.value && (
          <p className="text-xs text-emerald-400">{decision.impact.value}</p>
        )}
      </div>

      <QuickActionGroup>
        <QuickAction
          icon={CheckCircle}
          label="Appliquer"
          variant="success"
          size="sm"
          onClick={() => onApply(decision.id)}
        />
      </QuickActionGroup>
    </motion.div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function DecisionPanel({
  decisions = [],
  onApply,
  onApplyAll,
  onDismiss,
  className,
}) {
  const [filterType, setFilterType] = useState('all');
  const [viewMode, setViewMode] = useState('detailed'); // 'detailed' | 'compact'

  // Données de démo
  const demoDecisions = [
    {
      id: '1',
      type: 'optimization',
      title: 'Augmenter prix: Café Premium 500g',
      description: 'Marge actuelle: 18%. Marge marché: 32%.',
      impact: { value: '+124€/mois', monthly: '124' },
      confidence: 0.94,
    },
    {
      id: '2',
      type: 'stock',
      title: 'Réduire commande: Huile Olive 5L',
      description: 'Stock mort détecté. Rotation: 45 jours.',
      impact: { value: '-340€ immobilisés', savings: '340' },
      confidence: 0.89,
    },
    {
      id: '3',
      type: 'supplier',
      title: 'Changer fournisseur: Viande boeuf',
      description: 'Fournisseur B: -12% même qualité.',
      impact: { value: '+780€/mois', monthly: '780' },
      confidence: 0.86,
    },
    {
      id: '4',
      type: 'anomaly',
      title: 'Corriger: Double facturation METRO',
      description: 'Facture F-2025-847 présente en double.',
      impact: { value: 'Éviter 412€ de perte', savings: '412' },
      confidence: 0.98,
    },
    {
      id: '5',
      type: 'pricing',
      title: 'Ajuster: Miel Bio 500g sous-margé',
      description: 'Prix actuel: 12.50€. Suggestion: 14.90€.',
      impact: { value: '+216€/mois', monthly: '216' },
      confidence: 0.91,
    },
  ];

  const displayDecisions = decisions.length > 0 ? decisions : demoDecisions;

  // Filtrage
  const filteredDecisions = useMemo(() => {
    if (filterType === 'all') return displayDecisions;
    return displayDecisions.filter((d) => d.type === filterType);
  }, [displayDecisions, filterType]);

  // Décisions haute confiance
  const highConfidenceDecisions = filteredDecisions.filter((d) => d.confidence >= 0.9);

  const handleApply = (id) => {
    if (onApply) onApply(id);
  };

  const handleApplyAll = () => {
    if (onApplyAll) onApplyAll(highConfidenceDecisions.map((d) => d.id));
  };

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20">
            <Brain className="w-6 h-6 text-violet-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Décisions Assistées</h2>
            <p className="text-sm text-slate-400">
              {filteredDecisions.length} recommandation{filteredDecisions.length > 1 ? 's' : ''} IA
            </p>
          </div>
        </div>

        {highConfidenceDecisions.length > 0 && (
          <QuickAction
            icon={Zap}
            label={`Appliquer ${highConfidenceDecisions.length} fiables`}
            variant="success"
            onClick={handleApplyAll}
          />
        )}
      </div>

      {/* Impact Summary */}
      <ImpactSummary decisions={filteredDecisions} />

      {/* Filters */}
      <div className="flex items-center justify-between">
        <DecisionTypeFilter value={filterType} onChange={setFilterType} />

        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('detailed')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              viewMode === 'detailed'
                ? 'bg-white/10 text-white'
                : 'text-slate-400 hover:text-white'
            )}
          >
            Détaillé
          </button>
          <button
            onClick={() => setViewMode('compact')}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
              viewMode === 'compact'
                ? 'bg-white/10 text-white'
                : 'text-slate-400 hover:text-white'
            )}
          >
            Compact
          </button>
        </div>
      </div>

      {/* Decisions List */}
      <AnimatePresence mode="popLayout">
        {viewMode === 'detailed' ? (
          <div className="space-y-4">
            {filteredDecisions.map((decision) => (
              <SuggestionCard
                key={decision.id}
                id={decision.id}
                type={decision.type}
                title={decision.title}
                description={decision.description}
                impact={{ value: decision.impact?.value, period: '' }}
                confidence={decision.confidence}
                onAction={(action, id) => {
                  if (action === 'apply') handleApply(id);
                }}
                onDismiss={onDismiss}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {filteredDecisions.map((decision) => (
              <QuickDecision
                key={decision.id}
                decision={decision}
                onApply={handleApply}
                onDismiss={onDismiss}
              />
            ))}
          </div>
        )}
      </AnimatePresence>

      {filteredDecisions.length === 0 && (
        <div className="text-center py-12">
          <CheckCircle className="w-16 h-16 mx-auto mb-4 text-emerald-400/50" />
          <p className="text-lg font-medium text-white mb-1">
            Aucune action recommandée
          </p>
          <p className="text-sm text-slate-400">
            Toutes les optimisations sont à jour
          </p>
        </div>
      )}
    </div>
  );
}
