import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDebouncedCallback } from './useDebounce.js';
import {
  fetchProducts,
  searchFinanceTransactions,
  fetchCockpitAlerts,
  fetchInventorySummary,
} from '../api/client.js';
import {
  Package,
  DollarSign,
  AlertTriangle,
  TrendingUp,
  ShoppingCart,
  FileText,
} from 'lucide-react';

// ============================================================================
// COMMAND BAR LIVE SUGGESTIONS
// Hook pour les suggestions temps réel avec debounce
// ============================================================================

/**
 * Hook pour obtenir des suggestions en temps réel basées sur la recherche utilisateur
 * Utilise le debounce pour éviter trop de requêtes API
 */
export function useCommandBarLiveSuggestions(query, options = {}) {
  const {
    enabled = true,
    debounceMs = 300,
    minQueryLength = 2,
  } = options;

  const [debouncedQuery, setDebouncedQuery] = useState('');

  // Debounce de la requête
  const debouncedSetQuery = useDebouncedCallback((value) => {
    setDebouncedQuery(value);
  }, debounceMs);

  useEffect(() => {
    if (query && query.length >= minQueryLength) {
      debouncedSetQuery(query);
    } else {
      setDebouncedQuery('');
    }
  }, [query, minQueryLength, debouncedSetQuery]);

  const shouldFetch = enabled && debouncedQuery.length >= minQueryLength;

  // Recherche produits catalogue
  const { data: productsData } = useQuery({
    queryKey: ['commandbar-products-search', debouncedQuery],
    queryFn: () => fetchProducts({ search: debouncedQuery, limit: 5 }),
    enabled: shouldFetch,
    staleTime: 30000, // 30s
  });

  // Recherche transactions financières
  const { data: transactionsData } = useQuery({
    queryKey: ['commandbar-transactions-search', debouncedQuery],
    queryFn: () => searchFinanceTransactions({
      q: debouncedQuery,
      size: 5,
      page: 1,
    }),
    enabled: shouldFetch,
    staleTime: 30000,
  });

  // Alertes cockpit (toujours actives, pas de recherche)
  const { data: cockpitAlerts } = useQuery({
    queryKey: ['commandbar-cockpit-alerts'],
    queryFn: () => fetchCockpitAlerts({ limit: 3, severity: 'high' }),
    enabled,
    staleTime: 60000, // 1 min
    refetchInterval: 60000, // Rafraîchir toutes les minutes
  });

  // Inventaire critique (stocks bas)
  const { data: inventorySummary } = useQuery({
    queryKey: ['commandbar-inventory-critical'],
    queryFn: () => fetchInventorySummary(),
    enabled,
    staleTime: 120000, // 2 min
  });

  // Convertir les données en suggestions
  const liveSuggestions = useMemo(() => {
    const suggestions = [];

    // Suggestions de produits
    if (shouldFetch && productsData) {
      const products = Array.isArray(productsData?.items)
        ? productsData.items
        : Array.isArray(productsData)
        ? productsData
        : [];

      products.slice(0, 3).forEach((product) => {
        suggestions.push({
          id: `live-product-${product.id}`,
          label: product.nom || product.name || 'Produit sans nom',
          description: `${product.categorie || 'Catalogue'} - Stock: ${product.stock_actuel || 0}`,
          icon: Package,
          category: 'live-catalog',
          categoryLabel: 'Catalogue',
          action: (navigate) => navigate(`/operations/catalogue?product=${product.id}`),
          keywords: ['produit', 'catalogue', product.nom?.toLowerCase()],
          meta: {
            type: 'product',
            productId: product.id,
            stock: product.stock_actuel,
          },
        });
      });
    }

    // Suggestions de transactions
    if (shouldFetch && transactionsData?.items) {
      transactionsData.items.slice(0, 3).forEach((transaction) => {
        const amount = transaction.montant || transaction.amount || 0;
        const date = transaction.date_operation || transaction.date;
        const label = transaction.libelle || transaction.description || 'Transaction';

        suggestions.push({
          id: `live-transaction-${transaction.id}`,
          label: label.substring(0, 50),
          description: `${amount.toFixed(2)}€ - ${date ? new Date(date).toLocaleDateString('fr-FR') : ''}`,
          icon: DollarSign,
          category: 'live-finance',
          categoryLabel: 'Finances',
          action: (navigate) => navigate(`/finances/transactions?id=${transaction.id}`),
          keywords: ['transaction', 'finance', label.toLowerCase()],
          meta: {
            type: 'transaction',
            transactionId: transaction.id,
            amount,
          },
        });
      });
    }

    // Alertes cockpit (toujours affichées si présentes)
    if (cockpitAlerts?.length) {
      cockpitAlerts.slice(0, 2).forEach((alert, idx) => {
        suggestions.push({
          id: `live-alert-${alert.id || idx}`,
          label: alert.title || alert.message || 'Alerte',
          description: alert.category || 'Cockpit',
          icon: AlertTriangle,
          category: 'live-alerts',
          categoryLabel: 'Alertes actives',
          action: (navigate) => navigate('/'),
          keywords: ['alerte', 'cockpit'],
          meta: {
            type: 'alert',
            severity: alert.severity,
            alertId: alert.id,
          },
          priority: 10, // Haute priorité
        });
      });
    }

    // Stocks critiques
    if (inventorySummary?.low_stock_items?.length) {
      const criticalCount = inventorySummary.low_stock_items.length;
      suggestions.push({
        id: 'live-stock-critical',
        label: `${criticalCount} produit${criticalCount > 1 ? 's' : ''} en stock critique`,
        description: 'Réapprovisionnement urgent',
        icon: ShoppingCart,
        category: 'live-operations',
        categoryLabel: 'Opérations',
        action: (navigate) => navigate('/operations/catalogue?filter=low-stock'),
        keywords: ['stock', 'rupture', 'critique', 'réappro'],
        meta: {
          type: 'stock-alert',
          count: criticalCount,
        },
        priority: 8,
      });
    }

    // Trier par priorité (si définie)
    return suggestions.sort((a, b) => (b.priority || 0) - (a.priority || 0));
  }, [shouldFetch, productsData, transactionsData, cockpitAlerts, inventorySummary]);

  return {
    liveSuggestions,
    isLoading: shouldFetch && !productsData && !transactionsData,
    debouncedQuery,
  };
}

/**
 * Hook pour les suggestions contextuelles basées sur la section active
 * Ces suggestions sont statiques et ne nécessitent pas de requêtes API
 */
export function useContextualSuggestions(currentSection) {
  return useMemo(() => {
    const sections = {
      operations: [
        {
          id: 'ctx-import-invoice',
          label: 'Importer une facture',
          description: 'Scanner ou glisser-déposer un PDF',
          icon: FileText,
          category: 'context-operations',
          categoryLabel: 'Opérations rapides',
          action: (navigate) => navigate('/operations/factures'),
          keywords: ['facture', 'import', 'pdf'],
        },
        {
          id: 'ctx-low-stock',
          label: 'Produits en rupture',
          description: 'Voir les stocks critiques',
          icon: AlertTriangle,
          category: 'context-operations',
          categoryLabel: 'Opérations rapides',
          action: (navigate) => navigate('/operations/catalogue?filter=low-stock'),
          keywords: ['stock', 'rupture', 'alerte'],
        },
        {
          id: 'ctx-supply-plan',
          label: 'Plan d\'approvisionnement',
          description: 'IA - Suggestions de commande',
          icon: TrendingUp,
          category: 'context-operations',
          categoryLabel: 'Opérations rapides',
          action: (navigate) => navigate('/operations/planning'),
          keywords: ['planning', 'appro', 'commande'],
        },
      ],
      finances: [
        {
          id: 'ctx-reconciliation',
          label: 'Rapprochement bancaire',
          description: 'Valider les suggestions IA',
          icon: DollarSign,
          category: 'context-finance',
          categoryLabel: 'Actions finances',
          action: (navigate) => navigate('/finances/rapprochement'),
          keywords: ['rapprochement', 'banque', 'ia'],
        },
        {
          id: 'ctx-transactions',
          label: 'Transactions récentes',
          description: 'Catégoriser et analyser',
          icon: FileText,
          category: 'context-finance',
          categoryLabel: 'Actions finances',
          action: (navigate) => navigate('/finances/transactions'),
          keywords: ['transaction', 'catégorie'],
        },
      ],
      intelligence: [
        {
          id: 'ctx-anomalies',
          label: 'Détecter les anomalies',
          description: 'Scanner les transactions suspectes',
          icon: AlertTriangle,
          category: 'context-intelligence',
          categoryLabel: 'Intelligence',
          action: (navigate) => navigate('/intelligence/anomalies'),
          keywords: ['anomalie', 'détection', 'ia'],
        },
        {
          id: 'ctx-forecasts',
          label: 'Prévisions IA',
          description: 'Ventes, stocks, trésorerie',
          icon: TrendingUp,
          category: 'context-intelligence',
          categoryLabel: 'Intelligence',
          action: (navigate) => navigate('/intelligence/previsions'),
          keywords: ['prévision', 'forecast', 'ia'],
        },
      ],
    };

    return sections[currentSection] || [];
  }, [currentSection]);
}

export default useCommandBarLiveSuggestions;
