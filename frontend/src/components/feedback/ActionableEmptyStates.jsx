/**
 * ActionableEmptyStates - États vides actionnables pour les pages principales
 *
 * Phase 1 - Consolidation UX
 *
 * Chaque état vide propose une action contextuelle pour guider l'utilisateur.
 */

import {
  FileText,
  Receipt,
  Package,
  TrendingUp,
  AlertTriangle,
  CreditCard,
  Users,
  BarChart3,
  Upload,
  Plus,
  Search,
  RefreshCw,
  Download,
  Settings,
} from 'lucide-react';
import EmptyState from '../ui/EmptyState.jsx';

/**
 * Transactions vides
 */
export function EmptyTransactions({ onImport, onRefresh }) {
  return (
    <EmptyState
      icon={CreditCard}
      title="Aucune transaction"
      description="Importez vos relevés bancaires pour commencer à suivre vos transactions."
      size="lg"
      actions={[
        onImport && {
          label: 'Importer un relevé',
          onClick: onImport,
          icon: Upload,
        },
        onRefresh && {
          label: 'Rafraîchir',
          onClick: onRefresh,
          variant: 'ghost',
          icon: RefreshCw,
        },
      ].filter(Boolean)}
    />
  );
}

/**
 * Factures vides
 */
export function EmptyInvoices({ onUpload, onViewHistory }) {
  return (
    <EmptyState
      icon={FileText}
      title="Aucune facture importée"
      description="Déposez vos factures PDF pour les traiter automatiquement et mettre à jour votre stock."
      size="lg"
      actions={[
        onUpload && {
          label: 'Importer une facture',
          onClick: onUpload,
          icon: Upload,
        },
        onViewHistory && {
          label: 'Voir l\'historique',
          onClick: onViewHistory,
          variant: 'ghost',
        },
      ].filter(Boolean)}
    />
  );
}

/**
 * Produits vides (catalogue)
 */
export function EmptyProducts({ onAdd, onImport }) {
  return (
    <EmptyState
      icon={Package}
      title="Catalogue vide"
      description="Ajoutez vos premiers produits manuellement ou importez-les depuis une facture."
      size="lg"
      actions={[
        onAdd && {
          label: 'Ajouter un produit',
          onClick: onAdd,
          icon: Plus,
        },
        onImport && {
          label: 'Importer depuis facture',
          onClick: onImport,
          variant: 'outline',
          icon: Upload,
        },
      ].filter(Boolean)}
    />
  );
}

/**
 * Intelligence - Aucune anomalie
 */
export function EmptyAnomalies({ onConfigure }) {
  return (
    <EmptyState
      icon={AlertTriangle}
      title="Aucune anomalie détectée"
      description="Votre activité est saine. Le système surveille en permanence vos données pour détecter les écarts."
      size="md"
      actions={[
        onConfigure && {
          label: 'Configurer les seuils',
          onClick: onConfigure,
          variant: 'ghost',
          icon: Settings,
        },
      ].filter(Boolean)}
    />
  );
}

/**
 * Intelligence - Aucune prévision
 */
export function EmptyForecasts({ onRefresh }) {
  return (
    <EmptyState
      icon={TrendingUp}
      title="Prévisions indisponibles"
      description="Pas assez de données historiques pour générer des prévisions fiables. Continuez à enregistrer vos transactions."
      size="md"
      actions={[
        onRefresh && {
          label: 'Actualiser',
          onClick: onRefresh,
          variant: 'ghost',
          icon: RefreshCw,
        },
      ].filter(Boolean)}
    />
  );
}

/**
 * Fournisseurs vides (scoring)
 */
export function EmptySuppliers({ onImportInvoice }) {
  return (
    <EmptyState
      icon={Users}
      title="Aucun fournisseur référencé"
      description="Les fournisseurs sont automatiquement ajoutés lors de l'import de factures."
      size="md"
      actions={[
        onImportInvoice && {
          label: 'Importer une facture',
          onClick: onImportInvoice,
          icon: Upload,
        },
      ].filter(Boolean)}
    />
  );
}

/**
 * Rapprochement bancaire vide
 */
export function EmptyReconciliation({ onImportStatement, onImportInvoice }) {
  return (
    <EmptyState
      icon={Receipt}
      title="Rien à rapprocher"
      description="Importez vos relevés bancaires et factures pour commencer le rapprochement automatique."
      size="lg"
      actions={[
        onImportStatement && {
          label: 'Importer relevé',
          onClick: onImportStatement,
          icon: Download,
        },
        onImportInvoice && {
          label: 'Importer facture',
          onClick: onImportInvoice,
          variant: 'outline',
          icon: Upload,
        },
      ].filter(Boolean)}
    />
  );
}

/**
 * Stock vide
 */
export function EmptyStock({ onImportInvoice }) {
  return (
    <EmptyState
      icon={Package}
      title="Stock vide"
      description="Le stock est automatiquement mis à jour lors de l'import de factures fournisseurs."
      size="lg"
      actions={[
        onImportInvoice && {
          label: 'Importer une facture',
          onClick: onImportInvoice,
          icon: Upload,
        },
      ].filter(Boolean)}
    />
  );
}

/**
 * Rapports vides
 */
export function EmptyReports({ onGenerate }) {
  return (
    <EmptyState
      icon={BarChart3}
      title="Aucun rapport disponible"
      description="Générez votre premier rapport pour analyser votre activité."
      size="lg"
      actions={[
        onGenerate && {
          label: 'Générer un rapport',
          onClick: onGenerate,
          icon: Plus,
        },
      ].filter(Boolean)}
    />
  );
}

/**
 * Recherche sans résultat
 */
export function EmptySearchResults({ query, onClear }) {
  return (
    <EmptyState
      icon={Search}
      title={`Aucun résultat pour "${query}"`}
      description="Essayez avec d'autres termes de recherche ou vérifiez l'orthographe."
      size="md"
      actions={[
        onClear && {
          label: 'Effacer la recherche',
          onClick: onClear,
          variant: 'ghost',
        },
      ].filter(Boolean)}
    />
  );
}

/**
 * Filtres sans résultat
 */
export function EmptyFilteredResults({ onReset }) {
  return (
    <EmptyState
      icon={Search}
      title="Aucun résultat"
      description="Les filtres actuels ne correspondent à aucun élément. Modifiez vos critères."
      size="md"
      actions={[
        onReset && {
          label: 'Réinitialiser les filtres',
          onClick: onReset,
          variant: 'subtle',
        },
      ].filter(Boolean)}
    />
  );
}

export default {
  EmptyTransactions,
  EmptyInvoices,
  EmptyProducts,
  EmptyAnomalies,
  EmptyForecasts,
  EmptySuppliers,
  EmptyReconciliation,
  EmptyStock,
  EmptyReports,
  EmptySearchResults,
  EmptyFilteredResults,
};
