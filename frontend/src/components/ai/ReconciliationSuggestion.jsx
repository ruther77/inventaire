/**
 * ReconciliationSuggestion - Suggestion IA pour rapprochement bancaire
 * Scénario 3.4 du UX_NEXT_GEN_2025.md
 *
 * Affiche une suggestion de correspondance avec:
 * - Transaction bancaire
 * - Facture/Pièce associée
 * - Score de confiance
 * - Actions (Valider / Rejeter / Modifier)
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Link2,
  CheckCircle,
  X,
  ChevronDown,
  ChevronUp,
  FileText,
  CreditCard,
  Sparkles,
  Eye,
  AlertTriangle,
} from 'lucide-react';
import clsx from 'clsx';
import ConfidenceBadge from './ConfidenceBadge.jsx';
import QuickAction, { QuickActionGroup } from './QuickAction.jsx';

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

/**
 * TransactionCard - Affichage d'une transaction bancaire
 */
function TransactionCard({ transaction, isSelected, onClick }) {
  const isDebit = transaction.amount < 0;

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      onClick={onClick}
      className={clsx(
        'p-3 rounded-lg cursor-pointer transition-all duration-200',
        'border',
        isSelected
          ? 'border-blue-500/50 bg-blue-500/10'
          : 'border-white/10 bg-white/5 hover:bg-white/10'
      )}
    >
      <div className="flex items-center gap-3">
        <div className={clsx(
          'p-2 rounded-lg',
          isDebit ? 'bg-rose-500/20' : 'bg-emerald-500/20'
        )}>
          <CreditCard className={clsx(
            'w-4 h-4',
            isDebit ? 'text-rose-400' : 'text-emerald-400'
          )} />
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">
            {transaction.label}
          </p>
          <p className="text-xs text-slate-400">
            {transaction.date} • {transaction.bank_account}
          </p>
        </div>

        <p className={clsx(
          'text-sm font-bold font-mono',
          isDebit ? 'text-rose-400' : 'text-emerald-400'
        )}>
          {isDebit ? '' : '+'}{transaction.amount?.toFixed(2)}€
        </p>
      </div>
    </motion.div>
  );
}

/**
 * InvoiceCard - Affichage d'une facture
 */
function InvoiceCard({ invoice, isSelected, onClick }) {
  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      onClick={onClick}
      className={clsx(
        'p-3 rounded-lg cursor-pointer transition-all duration-200',
        'border',
        isSelected
          ? 'border-violet-500/50 bg-violet-500/10'
          : 'border-white/10 bg-white/5 hover:bg-white/10'
      )}
    >
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-violet-500/20">
          <FileText className="w-4 h-4 text-violet-400" />
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">
            {invoice.supplier} - {invoice.reference}
          </p>
          <p className="text-xs text-slate-400">
            {invoice.date} • {invoice.line_count || 0} lignes
          </p>
        </div>

        <p className="text-sm font-bold font-mono text-white">
          {invoice.amount?.toFixed(2)}€
        </p>
      </div>
    </motion.div>
  );
}

/**
 * MatchReason - Explication du matching IA
 */
function MatchReason({ reasons = [] }) {
  const defaultReasons = [
    { text: 'Montants identiques à ±0.01€', weight: 'high' },
    { text: 'Date facture dans fenêtre de 5j', weight: 'medium' },
    { text: 'Nom fournisseur détecté dans libellé', weight: 'high' },
  ];

  const displayReasons = reasons.length > 0 ? reasons : defaultReasons;

  const weightColors = {
    high: 'text-emerald-400',
    medium: 'text-amber-400',
    low: 'text-slate-400',
  };

  return (
    <div className="space-y-2">
      <p className="text-xs text-slate-500 uppercase tracking-wider">Raisons du match</p>
      <ul className="space-y-1">
        {displayReasons.map((reason, index) => (
          <li key={index} className="flex items-center gap-2 text-xs">
            <span className={clsx(
              'w-1.5 h-1.5 rounded-full',
              weightColors[reason.weight] || 'bg-slate-400'
            )} />
            <span className="text-slate-300">{reason.text}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function ReconciliationSuggestion({
  id,
  transaction,
  invoice,
  confidence = 0.92,
  reasons = [],
  alternativeMatches = [],
  onValidate,
  onReject,
  onViewAlternatives,
  className,
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // Données de démo si pas fournies
  const demoTransaction = {
    label: 'VIR METRO CASH & CARRY',
    date: '10/12/2025',
    amount: -847.32,
    bank_account: 'LCL Pro',
  };

  const demoInvoice = {
    supplier: 'METRO',
    reference: 'F-2025-12847',
    date: '08/12/2025',
    amount: 847.32,
    line_count: 23,
  };

  const displayTransaction = transaction || demoTransaction;
  const displayInvoice = invoice || demoInvoice;

  const handleValidate = async () => {
    setIsProcessing(true);
    try {
      if (onValidate) await onValidate(id);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReject = async () => {
    setIsProcessing(true);
    try {
      if (onReject) await onReject(id);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={clsx(
        'rounded-xl border border-white/10 overflow-hidden',
        'bg-gradient-to-br from-slate-800/50 to-slate-900/50',
        className
      )}
    >
      {/* Header avec confiance */}
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-blue-500/20">
              <Link2 className="w-4 h-4 text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">Correspondance suggérée</p>
              <p className="text-xs text-slate-400">Matching automatique</p>
            </div>
          </div>

          <ConfidenceBadge value={confidence} size="md" showLabel />
        </div>
      </div>

      {/* Contenu: Transaction ↔ Facture */}
      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Transaction */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              Transaction bancaire
            </p>
            <TransactionCard transaction={displayTransaction} isSelected />
          </div>

          {/* Lien visuel */}
          <div className="hidden md:flex items-center justify-center -mx-4">
            <div className="w-8 h-0.5 bg-gradient-to-r from-blue-500 to-violet-500" />
            <Link2 className="w-5 h-5 text-slate-400 mx-2" />
            <div className="w-8 h-0.5 bg-gradient-to-r from-violet-500 to-blue-500" />
          </div>

          {/* Facture */}
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
              Facture associée
            </p>
            <InvoiceCard invoice={displayInvoice} isSelected />
          </div>
        </div>

        {/* Zone dépliable avec détails */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="mt-4 pt-4 border-t border-white/10">
                <MatchReason reasons={reasons} />

                {alternativeMatches.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                      Alternatives possibles ({alternativeMatches.length})
                    </p>
                    <div className="space-y-2">
                      {alternativeMatches.slice(0, 2).map((alt, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-2 rounded bg-white/5"
                        >
                          <span className="text-xs text-slate-300">
                            {alt.supplier} - {alt.reference}
                          </span>
                          <ConfidenceBadge value={alt.confidence} size="sm" showLabel={false} />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Actions */}
      <div className="px-4 pb-4 flex items-center justify-between">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              Réduire
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              Détails
            </>
          )}
        </button>

        <QuickActionGroup>
          <QuickAction
            icon={X}
            label="Rejeter"
            variant="default"
            size="sm"
            onClick={handleReject}
            disabled={isProcessing}
          />
          <QuickAction
            icon={Eye}
            label="Autres"
            variant="default"
            size="sm"
            onClick={onViewAlternatives}
            disabled={isProcessing}
          />
          <QuickAction
            icon={CheckCircle}
            label="Valider"
            variant="success"
            size="sm"
            onClick={handleValidate}
            loading={isProcessing}
          />
        </QuickActionGroup>
      </div>

      {/* Badge IA */}
      <div className="absolute top-2 right-2">
        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-violet-500/20 text-violet-400 text-[10px] font-medium">
          <Sparkles className="w-3 h-3" />
          IA
        </span>
      </div>
    </motion.div>
  );
}

/**
 * ReconciliationSuggestionList - Liste de suggestions
 */
export function ReconciliationSuggestionList({
  suggestions = [],
  onValidate,
  onReject,
  onValidateAll,
  title,
  className,
}) {
  const [visibleSuggestions, setVisibleSuggestions] = useState(suggestions);

  // Données de démo si vide
  const demoSuggestions = [
    {
      id: '1',
      transaction: { label: 'VIR METRO CASH & CARRY', date: '10/12/2025', amount: -847.32, bank_account: 'LCL Pro' },
      invoice: { supplier: 'METRO', reference: 'F-2025-12847', date: '08/12/2025', amount: 847.32, line_count: 23 },
      confidence: 0.98,
    },
    {
      id: '2',
      transaction: { label: 'PRLV BRAKE FRANCE', date: '09/12/2025', amount: -412.50, bank_account: 'LCL Pro' },
      invoice: { supplier: 'BRAKE', reference: 'F-2025-8754', date: '05/12/2025', amount: 412.50, line_count: 12 },
      confidence: 0.94,
    },
    {
      id: '3',
      transaction: { label: 'CB PROMOCASH', date: '08/12/2025', amount: -156.80, bank_account: 'LCL Pro' },
      invoice: { supplier: 'PROMOCASH', reference: 'T-458712', date: '08/12/2025', amount: 156.80, line_count: 8 },
      confidence: 0.89,
    },
  ];

  const displaySuggestions = visibleSuggestions.length > 0 ? visibleSuggestions : demoSuggestions;

  const handleValidate = async (id) => {
    setVisibleSuggestions((prev) => prev.filter((s) => s.id !== id));
    if (onValidate) onValidate(id);
  };

  const handleReject = async (id) => {
    setVisibleSuggestions((prev) => prev.filter((s) => s.id !== id));
    if (onReject) onReject(id);
  };

  const highConfidence = displaySuggestions.filter((s) => s.confidence >= 0.9);

  return (
    <div className={className}>
      {title && (
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-white flex items-center gap-2">
            <Link2 className="w-5 h-5 text-blue-400" />
            {title}
          </h3>

          {highConfidence.length > 0 && (
            <QuickAction
              icon={CheckCircle}
              label={`Valider ${highConfidence.length} fiables`}
              variant="success"
              size="sm"
              onClick={() => {
                highConfidence.forEach((s) => handleValidate(s.id));
                if (onValidateAll) onValidateAll(highConfidence.map((s) => s.id));
              }}
            />
          )}
        </div>
      )}

      <div className="space-y-4">
        <AnimatePresence mode="popLayout">
          {displaySuggestions.map((suggestion) => (
            <ReconciliationSuggestion
              key={suggestion.id}
              {...suggestion}
              onValidate={handleValidate}
              onReject={handleReject}
            />
          ))}
        </AnimatePresence>

        {displaySuggestions.length === 0 && (
          <div className="text-center py-8 text-slate-400">
            <CheckCircle className="w-12 h-12 mx-auto mb-2 text-emerald-400" />
            <p>Toutes les correspondances ont été traitées</p>
          </div>
        )}
      </div>
    </div>
  );
}
