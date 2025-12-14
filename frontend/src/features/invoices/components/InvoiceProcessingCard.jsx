/**
 * InvoiceProcessingCard - Traitement intelligent de facture
 * Scénario 3.2 du UX_NEXT_GEN_2025.md
 *
 * Affiche le processus de traitement en temps réel:
 * - OCR terminé → X lignes extraites
 * - Matching produits → X/Y matchés
 * - Prix analysés → X anomalies
 * - Catégorisation → X% auto-catégorisé
 * - Mise à jour stock → En cours...
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Link2,
  Tag,
  Package,
  TrendingUp,
  Plus,
  X,
  ChevronDown,
  ChevronUp,
  Eye,
  Sparkles,
} from 'lucide-react';
import clsx from 'clsx';
import ConfidenceBadge from '../../../components/ai/ConfidenceBadge.jsx';
import QuickAction, { QuickActionGroup } from '../../../components/ai/QuickAction.jsx';

// ============================================================================
// PROCESSING STEPS
// ============================================================================

const PROCESSING_STEPS = [
  { id: 'ocr', label: 'OCR', icon: FileText, description: 'Extraction du texte' },
  { id: 'matching', label: 'Matching produits', icon: Link2, description: 'Correspondance catalogue' },
  { id: 'pricing', label: 'Prix analysés', icon: TrendingUp, description: 'Détection anomalies' },
  { id: 'categorization', label: 'Catégorisation', icon: Tag, description: 'Classification auto' },
  { id: 'stock', label: 'Mise à jour stock', icon: Package, description: 'Calcul mouvements' },
];

/**
 * ProcessingStep - Étape individuelle de traitement
 */
function ProcessingStep({ step, status, result }) {
  const StepIcon = step.icon;

  const statusConfig = {
    pending: { color: 'text-slate-500', bg: 'bg-slate-500/10' },
    processing: { color: 'text-blue-400', bg: 'bg-blue-500/10' },
    completed: { color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    warning: { color: 'text-amber-400', bg: 'bg-amber-500/10' },
    error: { color: 'text-rose-400', bg: 'bg-rose-500/10' },
  };

  const config = statusConfig[status] || statusConfig.pending;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className={clsx(
        'flex items-center gap-3 p-3 rounded-lg',
        config.bg
      )}
    >
      <div className={clsx('p-2 rounded-lg bg-white/10', config.color)}>
        {status === 'processing' ? (
          <RefreshCw className="w-4 h-4 animate-spin" />
        ) : status === 'completed' ? (
          <CheckCircle className="w-4 h-4" />
        ) : status === 'warning' ? (
          <AlertTriangle className="w-4 h-4" />
        ) : (
          <StepIcon className="w-4 h-4" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <p className={clsx('text-sm font-medium', config.color)}>
            {step.label}
          </p>
          {result && (
            <span className="text-xs text-slate-400">{result}</span>
          )}
        </div>
      </div>
    </motion.div>
  );
}

/**
 * AttentionItem - Élément nécessitant attention
 */
function AttentionItem({ item, onAction }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const typeConfig = {
    new_product: {
      icon: Plus,
      color: 'amber',
      label: 'Nouveau produit',
    },
    price_anomaly: {
      icon: TrendingUp,
      color: 'rose',
      label: 'Anomalie prix',
    },
    no_match: {
      icon: Link2,
      color: 'blue',
      label: 'Sans correspondance',
    },
  };

  const config = typeConfig[item.type] || typeConfig.new_product;
  const ItemIcon = config.icon;

  const colorClasses = {
    amber: 'border-amber-500/30 bg-amber-500/5',
    rose: 'border-rose-500/30 bg-rose-500/5',
    blue: 'border-blue-500/30 bg-blue-500/5',
  };

  return (
    <motion.div
      layout
      className={clsx(
        'rounded-lg border overflow-hidden',
        colorClasses[config.color]
      )}
    >
      <div className="p-3">
        <div className="flex items-start gap-3">
          <div className={clsx(
            'p-1.5 rounded-lg',
            `bg-${config.color}-500/20 text-${config.color}-400`
          )}>
            <ItemIcon className="w-4 h-4" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={clsx(
                'px-1.5 py-0.5 rounded text-[10px] font-bold uppercase',
                `bg-${config.color}-500/20 text-${config.color}-400`
              )}>
                {config.label}
              </span>
            </div>

            <p className="text-sm font-medium text-white">{item.title}</p>
            {item.description && (
              <p className="text-xs text-slate-400 mt-0.5">{item.description}</p>
            )}

            {/* Suggestion IA */}
            {item.suggestion && (
              <div className="flex items-start gap-2 mt-2 p-2 rounded bg-white/5">
                <Sparkles className="w-3 h-3 text-violet-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-slate-300">{item.suggestion}</p>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="mt-3 flex flex-wrap gap-2">
          {item.actions?.map((action, index) => (
            <QuickAction
              key={action.id || index}
              icon={action.icon}
              label={action.label}
              variant={index === 0 ? 'primary' : 'default'}
              size="sm"
              onClick={() => onAction(action.id, item.id)}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
}

/**
 * InvoiceSummary - Résumé de la facture
 */
function InvoiceSummary({ data }) {
  return (
    <div className="grid grid-cols-4 gap-3">
      {[
        { label: 'Total HT', value: `${data?.totalHT?.toFixed(2) || '0.00'}€` },
        { label: 'TVA', value: `${data?.tva?.toFixed(2) || '0.00'}€` },
        { label: 'Total TTC', value: `${data?.totalTTC?.toFixed(2) || '0.00'}€` },
        { label: 'Lignes', value: data?.lineCount || 0 },
      ].map((item, index) => (
        <div
          key={index}
          className="text-center p-3 rounded-lg bg-white/5 border border-white/10"
        >
          <p className="text-xs text-slate-500 mb-1">{item.label}</p>
          <p className="text-lg font-bold text-white">{item.value}</p>
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function InvoiceProcessingCard({
  isProcessing = false,
  fileName,
  steps = [],
  attentionItems = [],
  summary,
  onAction,
  onValidate,
  onCancel,
  className,
}) {
  const [showAttention, setShowAttention] = useState(true);

  // Données de démo si pas de données fournies
  const demoSteps = [
    { id: 'ocr', status: 'completed', result: '47 lignes extraites' },
    { id: 'matching', status: 'completed', result: '45/47 matchés (96%)' },
    { id: 'pricing', status: 'warning', result: '2 anomalies détectées' },
    { id: 'categorization', status: 'completed', result: '100% auto-catégorisé' },
    { id: 'stock', status: 'processing', result: 'En cours...' },
  ];

  const demoAttention = [
    {
      id: 'new-1',
      type: 'new_product',
      title: '"Huile Olive Extra 5L" → Nouveau produit',
      description: null,
      suggestion: 'Similaire à: "Huile Olive 5L" (existant)',
      actions: [
        { id: 'link', label: 'Lier à existant', icon: Link2 },
        { id: 'create', label: 'Créer nouveau', icon: Plus },
      ],
    },
    {
      id: 'price-1',
      type: 'price_anomaly',
      title: '"Tomates Grappe" → Prix +18% vs dernier achat',
      description: 'Avant: 2.40€/kg → Maintenant: 2.83€/kg',
      suggestion: 'Saisonnier (décembre) - Historique similaire',
      actions: [
        { id: 'accept', label: 'Accepter', icon: CheckCircle },
        { id: 'reject', label: 'Contester', icon: X },
        { id: 'history', label: 'Voir historique', icon: Eye },
      ],
    },
  ];

  const displaySteps = steps.length > 0 ? steps : demoSteps;
  const displayAttention = attentionItems.length > 0 ? attentionItems : demoAttention;
  const displaySummary = summary || {
    totalHT: 847.32,
    tva: 72.45,
    totalTTC: 919.77,
    lineCount: 47,
  };

  const completedSteps = displaySteps.filter((s) => s.status === 'completed').length;
  const totalSteps = displaySteps.length;
  const progress = (completedSteps / totalSteps) * 100;

  return (
    <div className={clsx(
      'rounded-2xl border border-white/10 overflow-hidden',
      'bg-gradient-to-br from-slate-800/50 to-slate-900/50',
      className
    )}>
      {/* Header */}
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/20">
              <FileText className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold text-white">
                {fileName || 'Facture_METRO_2025-12-10.pdf'}
              </h3>
              <p className="text-xs text-slate-400">Traitement en cours</p>
            </div>
          </div>

          <ConfidenceBadge value={0.96} size="md" showLabel />
        </div>

        {/* Progress bar */}
        <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-blue-500 to-emerald-500"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
      </div>

      {/* Processing Steps */}
      <div className="p-4 space-y-2">
        {displaySteps.map((stepData) => {
          const stepDef = PROCESSING_STEPS.find((s) => s.id === stepData.id);
          if (!stepDef) return null;
          return (
            <ProcessingStep
              key={stepData.id}
              step={stepDef}
              status={stepData.status}
              result={stepData.result}
            />
          );
        })}
      </div>

      {/* Attention Items */}
      {displayAttention.length > 0 && (
        <div className="border-t border-white/10">
          <button
            onClick={() => setShowAttention(!showAttention)}
            className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-white/5 transition-colors"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span className="text-sm font-medium text-white">
                {displayAttention.length} point{displayAttention.length > 1 ? 's' : ''} d'attention
              </span>
            </div>
            {showAttention ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </button>

          <AnimatePresence>
            {showAttention && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="px-4 pb-4 space-y-3">
                  {displayAttention.map((item) => (
                    <AttentionItem
                      key={item.id}
                      item={item}
                      onAction={onAction}
                    />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Summary */}
      <div className="p-4 border-t border-white/10">
        <h4 className="text-xs uppercase tracking-wider text-slate-500 mb-3">
          Résumé Import
        </h4>
        <InvoiceSummary data={displaySummary} />
      </div>

      {/* Actions */}
      <div className="p-4 border-t border-white/10 flex items-center justify-between">
        <QuickAction
          icon={Eye}
          label="Modifier avant validation"
          variant="default"
          onClick={() => {}}
        />

        <QuickActionGroup>
          <QuickAction
            icon={X}
            label="Annuler"
            variant="default"
            onClick={onCancel}
          />
          <QuickAction
            icon={CheckCircle}
            label="Valider et mettre à jour stock"
            variant="success"
            onClick={onValidate}
          />
        </QuickActionGroup>
      </div>
    </div>
  );
}
