/**
 * AnomalyActionsInline - Actions correctives inline (S3 - Anomalie Prix)
 *
 * Composant d'actions rapides pour traiter les anomalies:
 * - Boutons d'action contextuelle
 * - Feedback instantane
 * - Actions avec confirmation
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Check,
  X,
  DollarSign,
  Truck,
  RotateCcw,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  ChevronDown,
  Loader2,
  MessageSquare,
  ExternalLink,
} from 'lucide-react';
import Button from '../../../components/ui/Button.jsx';
import api from '../../../api/client.js';

// ===========================================================================
// API Functions
// ===========================================================================

const resolveAnomaly = async (anomalyId, action, reason) => {
  const { data } = await api.post(`/anomaly-detection/anomalies/${anomalyId}/resolve`, {
    action,
    reason,
  });
  return data;
};

const updatePrice = async (productId, newPrice) => {
  const { data } = await api.patch(`/catalog/products/${productId}`, {
    prix_achat: newPrice,
  });
  return data;
};

const submitFeedback = async (anomalyId, isCorrect) => {
  const { data } = await api.post(`/anomaly-detection/anomalies/${anomalyId}/feedback`, {
    is_correct: isCorrect,
  });
  return data;
};

// ===========================================================================
// Sub-components
// ===========================================================================

function QuickActionButton({ icon: Icon, label, onClick, loading, disabled, variant = 'default' }) {
  const variants = {
    default: 'bg-white/5 hover:bg-white/10 text-slate-300 border-white/10',
    success: 'bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    warning: 'bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border-amber-500/30',
    danger: 'bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border-rose-500/30',
    primary: 'bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  };

  return (
    <motion.button
      type="button"
      onClick={onClick}
      disabled={loading || disabled}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition-all disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]}`}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Icon className="w-4 h-4" />
      )}
      {label}
    </motion.button>
  );
}

function ConfirmationPopover({ isOpen, onConfirm, onCancel, title, message }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: 10, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 10, scale: 0.95 }}
          className="absolute bottom-full left-0 mb-2 p-4 rounded-xl bg-slate-800 border border-white/10 shadow-xl z-10 min-w-64"
        >
          <p className="font-medium text-white mb-1">{title}</p>
          <p className="text-sm text-slate-400 mb-4">{message}</p>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={onCancel}>
              Annuler
            </Button>
            <Button variant="primary" size="sm" onClick={onConfirm}>
              Confirmer
            </Button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function FeedbackButtons({ anomalyId, onFeedback }) {
  const queryClient = useQueryClient();
  const [submitted, setSubmitted] = useState(false);

  const feedbackMutation = useMutation({
    mutationFn: ({ isCorrect }) => submitFeedback(anomalyId, isCorrect),
    onSuccess: () => {
      setSubmitted(true);
      queryClient.invalidateQueries(['anomalies']);
      onFeedback?.();
    },
  });

  if (submitted) {
    return (
      <motion.span
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-emerald-400 bg-emerald-500/10"
      >
        <Check className="w-4 h-4" />
        Merci pour le feedback
      </motion.span>
    );
  }

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10">
      <span className="text-xs text-slate-400">Anomalie correcte?</span>
      <button
        type="button"
        onClick={() => feedbackMutation.mutate({ isCorrect: true })}
        disabled={feedbackMutation.isPending}
        className="p-1 rounded hover:bg-emerald-500/20 text-slate-400 hover:text-emerald-400 transition"
        title="Oui, anomalie valide"
      >
        <ThumbsUp className="w-4 h-4" />
      </button>
      <button
        type="button"
        onClick={() => feedbackMutation.mutate({ isCorrect: false })}
        disabled={feedbackMutation.isPending}
        className="p-1 rounded hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition"
        title="Non, faux positif"
      >
        <ThumbsDown className="w-4 h-4" />
      </button>
    </div>
  );
}

function PriceUpdateInline({ anomaly, onSuccess }) {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [newPrice, setNewPrice] = useState(anomaly?.details?.expected_amount || '');

  const updateMutation = useMutation({
    mutationFn: () => updatePrice(anomaly?.entity_id, parseFloat(newPrice)),
    onSuccess: () => {
      queryClient.invalidateQueries(['products']);
      queryClient.invalidateQueries(['anomalies']);
      setIsEditing(false);
      onSuccess?.();
    },
  });

  if (!isEditing) {
    return (
      <QuickActionButton
        icon={DollarSign}
        label="Ajuster prix"
        onClick={() => setIsEditing(true)}
        variant="warning"
      />
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, width: 0 }}
      animate={{ opacity: 1, width: 'auto' }}
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30"
    >
      <input
        type="number"
        value={newPrice}
        onChange={(e) => setNewPrice(e.target.value)}
        className="w-20 px-2 py-1 text-sm bg-white/10 border border-white/20 rounded text-white focus:outline-none focus:border-amber-500"
        placeholder="Prix"
        step="0.01"
        autoFocus
      />
      <span className="text-sm text-amber-400">EUR</span>
      <button
        type="button"
        onClick={() => updateMutation.mutate()}
        disabled={updateMutation.isPending || !newPrice}
        className="p-1 rounded hover:bg-amber-500/20 text-amber-400 disabled:opacity-50"
      >
        {updateMutation.isPending ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Check className="w-4 h-4" />
        )}
      </button>
      <button
        type="button"
        onClick={() => setIsEditing(false)}
        className="p-1 rounded hover:bg-white/10 text-slate-400"
      >
        <X className="w-4 h-4" />
      </button>
    </motion.div>
  );
}

// ===========================================================================
// Main Component
// ===========================================================================

export default function AnomalyActionsInline({
  anomaly,
  onResolve,
  onIgnore,
  onViewDetails,
  onNavigateToEntity,
  showFeedback = true,
  compact = false,
}) {
  const queryClient = useQueryClient();
  const [showConfirm, setShowConfirm] = useState(null);
  const [showMoreActions, setShowMoreActions] = useState(false);

  // Mutations
  const resolveMutation = useMutation({
    mutationFn: ({ action, reason }) => resolveAnomaly(anomaly.id, action, reason),
    onSuccess: () => {
      queryClient.invalidateQueries(['anomalies']);
      setShowConfirm(null);
      onResolve?.(anomaly.id);
    },
  });

  // Handlers
  const handleResolve = () => {
    setShowConfirm('resolve');
  };

  const handleIgnore = () => {
    setShowConfirm('ignore');
  };

  const confirmAction = (action) => {
    resolveMutation.mutate({ action, reason: '' });
  };

  // Determine available actions based on anomaly type
  const getContextualActions = () => {
    const actions = [];

    switch (anomaly?.type) {
      case 'price_spike':
      case 'amount_outlier':
        actions.push({
          icon: DollarSign,
          label: 'Ajuster prix',
          variant: 'warning',
          component: (
            <PriceUpdateInline
              anomaly={anomaly}
              onSuccess={() => onResolve?.(anomaly.id)}
            />
          ),
        });
        actions.push({
          icon: Truck,
          label: 'Voir fournisseur',
          variant: 'default',
          onClick: () => onNavigateToEntity?.('supplier', anomaly?.details?.supplier_id),
        });
        break;

      case 'duplicate_transaction':
      case 'duplicate_invoice':
        actions.push({
          icon: RotateCcw,
          label: 'Annuler doublon',
          variant: 'danger',
          onClick: handleResolve,
        });
        break;

      case 'stock_variance':
        actions.push({
          icon: AlertTriangle,
          label: 'Ajuster stock',
          variant: 'warning',
          onClick: () => onNavigateToEntity?.('stock', anomaly?.entity_id),
        });
        break;

      default:
        break;
    }

    return actions;
  };

  const contextualActions = getContextualActions();

  if (compact) {
    return (
      <div className="inline-flex items-center gap-2">
        <QuickActionButton
          icon={Check}
          label="OK"
          onClick={handleResolve}
          loading={resolveMutation.isPending}
          variant="success"
        />
        <QuickActionButton
          icon={X}
          label="Ignorer"
          onClick={handleIgnore}
          loading={resolveMutation.isPending}
          variant="danger"
        />
        {onViewDetails && (
          <QuickActionButton
            icon={ExternalLink}
            label="Details"
            onClick={() => onViewDetails(anomaly)}
            variant="default"
          />
        )}
      </div>
    );
  }

  return (
    <div className="relative space-y-3">
      {/* Primary actions */}
      <div className="flex flex-wrap items-center gap-2">
        <QuickActionButton
          icon={Check}
          label="Marquer resolu"
          onClick={handleResolve}
          loading={resolveMutation.isPending && showConfirm === 'resolve'}
          variant="success"
        />

        {/* Contextual actions */}
        {contextualActions.map((action, idx) =>
          action.component ? (
            <span key={idx}>{action.component}</span>
          ) : (
            <QuickActionButton
              key={idx}
              icon={action.icon}
              label={action.label}
              onClick={action.onClick}
              variant={action.variant}
            />
          )
        )}

        {/* More actions dropdown */}
        <div className="relative">
          <QuickActionButton
            icon={ChevronDown}
            label="Plus"
            onClick={() => setShowMoreActions(!showMoreActions)}
            variant="default"
          />

          <AnimatePresence>
            {showMoreActions && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="absolute top-full right-0 mt-2 w-48 py-2 rounded-xl bg-slate-800 border border-white/10 shadow-xl z-20"
              >
                <button
                  type="button"
                  onClick={() => {
                    handleIgnore();
                    setShowMoreActions(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-slate-300 hover:bg-white/10 flex items-center gap-2"
                >
                  <X className="w-4 h-4" />
                  Ignorer l'anomalie
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onViewDetails?.(anomaly);
                    setShowMoreActions(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-slate-300 hover:bg-white/10 flex items-center gap-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  Voir les details
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onNavigateToEntity?.(anomaly?.entity_type, anomaly?.entity_id);
                    setShowMoreActions(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-slate-300 hover:bg-white/10 flex items-center gap-2"
                >
                  <MessageSquare className="w-4 h-4" />
                  Voir l'entite
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Feedback section */}
      {showFeedback && (
        <FeedbackButtons
          anomalyId={anomaly?.id}
          onFeedback={() => {}}
        />
      )}

      {/* Confirmation popovers */}
      <ConfirmationPopover
        isOpen={showConfirm === 'resolve'}
        onConfirm={() => confirmAction('resolved')}
        onCancel={() => setShowConfirm(null)}
        title="Marquer comme resolu?"
        message="L'anomalie sera archivee et ne sera plus affichee."
      />

      <ConfirmationPopover
        isOpen={showConfirm === 'ignore'}
        onConfirm={() => confirmAction('ignored')}
        onCancel={() => setShowConfirm(null)}
        title="Ignorer l'anomalie?"
        message="L'anomalie sera marquee comme faux positif."
      />
    </div>
  );
}

// ===========================================================================
// Exports
// ===========================================================================

export { QuickActionButton, FeedbackButtons, PriceUpdateInline };
