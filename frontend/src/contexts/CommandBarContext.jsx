import { createContext, useContext, useState, useCallback, useMemo, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { allRoutes, navigationSections } from '../app/routes.jsx';
import { useQueryClient } from '@tanstack/react-query';
import {
  Search,
  FileText,
  Package,
  Users,
  Calculator,
  TrendingUp,
  AlertTriangle,
  Settings,
  Plus,
  ArrowRight,
  Gauge,
  Clock,
  Link2,
} from 'lucide-react';

// ============================================================================
// COMMAND BAR CONTEXT - Gestion centralisée de la Command Bar
// ============================================================================

const CommandBarContext = createContext(null);

// Actions rapides disponibles
const quickActions = [
  {
    id: 'new-invoice',
    label: 'Importer une facture',
    description: 'Glisser-déposer ou scanner',
    icon: Plus,
    category: 'actions',
    action: (navigate) => navigate('/operations/factures'),
    keywords: ['facture', 'import', 'nouveau', 'ajouter'],
  },
  {
    id: 'new-product',
    label: 'Ajouter un produit',
    description: 'Créer une nouvelle référence',
    icon: Package,
    category: 'actions',
    action: (navigate) => navigate('/operations/catalogue?action=new'),
    keywords: ['produit', 'nouveau', 'ajouter', 'créer'],
  },
  {
    id: 'check-stock',
    label: 'Vérifier le stock',
    description: 'Alertes et niveaux',
    icon: AlertTriangle,
    category: 'actions',
    action: (navigate) => navigate('/operations/catalogue?filter=low-stock'),
    keywords: ['stock', 'rupture', 'alerte', 'niveau'],
  },
  {
    id: 'view-margins',
    label: 'Analyser les marges',
    description: 'PAMP et rentabilité',
    icon: Calculator,
    category: 'actions',
    action: (navigate) => navigate('/intelligence/marges'),
    keywords: ['marge', 'pamp', 'rentabilité', 'profit'],
  },
  {
    id: 'view-forecasts',
    label: 'Voir les prévisions',
    description: 'IA et projections',
    icon: TrendingUp,
    category: 'actions',
    action: (navigate) => navigate('/intelligence/previsions'),
    keywords: ['prévision', 'forecast', 'projection', 'tendance'],
  },
  {
    id: 'supplier-scoring',
    label: 'Scoring fournisseurs',
    description: 'Évaluation et comparaison',
    icon: Users,
    category: 'actions',
    action: (navigate) => navigate('/intelligence/scoring'),
    keywords: ['fournisseur', 'scoring', 'évaluation', 'note'],
  },
];

// Transformer les routes en items de recherche
const navigationItems = allRoutes.map((route) => ({
  id: `nav-${route.path}`,
  label: route.label,
  description: route.description,
  icon: route.icon,
  category: 'navigation',
  path: route.path,
  keywords: [route.label.toLowerCase(), route.description?.toLowerCase()].filter(Boolean),
}));

// Sections pour la navigation rapide
const sectionItems = navigationSections.map((section) => ({
  id: `section-${section.id}`,
  label: section.label,
  description: section.description,
  icon: section.icon,
  category: 'sections',
  path: section.routes[0]?.path || '/',
  color: section.color,
  keywords: [section.label.toLowerCase(), section.description?.toLowerCase()].filter(Boolean),
}));

export function CommandBarProvider({ children }) {
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentSearches, setRecentSearches] = useState([]);
  const navigate = useNavigate();
  const location = useLocation();

  // Charger les recherches récentes du localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem('commandbar-recent');
      if (stored) {
        setRecentSearches(JSON.parse(stored));
      }
    } catch {
      // Ignore
    }
  }, []);

  // Ouvrir la command bar
  const open = useCallback(() => {
    setIsOpen(true);
    setQuery('');
    setSelectedIndex(0);
  }, []);

  // Fermer la command bar
  const close = useCallback(() => {
    setIsOpen(false);
    setQuery('');
    setSelectedIndex(0);
  }, []);

  // Toggle
  const toggle = useCallback(() => {
    if (isOpen) {
      close();
    } else {
      open();
    }
  }, [isOpen, open, close]);

  // Contexte actuel basé sur la route
  const currentContext = useMemo(() => {
    const path = location.pathname;
    const section = navigationSections.find((s) =>
      s.routes.some((r) => path.startsWith(r.path.split('/').slice(0, 2).join('/')))
    );
    return section || navigationSections[0];
  }, [location.pathname]);

  const contextualItems = useMemo(() => {
    switch (currentContext?.id) {
      case 'operations':
        return [
          {
            id: 'ctx-low-stock',
            label: 'Voir les ruptures',
            description: 'Filtres SmartTable (stock < seuil)',
            icon: AlertTriangle,
            category: 'context',
            action: (navigate) => navigate('/operations/catalogue?filter=low-stock'),
            keywords: ['stock', 'rupture', 'catalogue'],
          },
          {
            id: 'ctx-invoices',
            label: 'Importer une facture',
            description: 'Scenario 3.2 zero-click',
            icon: FileText,
            category: 'context',
            action: (navigate) => navigate('/operations/factures'),
            keywords: ['facture', 'import'],
          },
        ];
      case 'finances':
        return [
          {
            id: 'ctx-reco',
            label: 'Rapprochement IA',
            description: 'Valider les suggestions',
            icon: Link2,
            category: 'context',
            action: (navigate) => navigate('/finances/rapprochement'),
            keywords: ['rapprochement', 'ia'],
          },
        ];
      case 'intelligence':
        return [
          {
            id: 'ctx-intel',
            label: 'Alertes anomalies',
            description: 'Analyser les anomalies critiques',
            icon: AlertTriangle,
            category: 'context',
            action: (navigate) => navigate('/intelligence/anomalies'),
            keywords: ['anomalie', 'ia'],
          },
        ];
      default:
        return [
          {
            id: 'ctx-cockpit',
            label: 'Aller au cockpit',
            description: 'Brief du jour',
            icon: Gauge,
            category: 'context',
            action: (navigate) => navigate('/'),
            keywords: ['cockpit', 'brief'],
          },
        ];
    }
  }, [currentContext]);

  // Suggestions basées sur les données présentes en cache (pas d’appel réseau)
  const liveSuggestions = useMemo(() => {
    const items = [];
    const cockpit = queryClient.getQueryData(['cockpit-overview']);
    if (cockpit?.alerts?.length) {
      items.push({
        id: 'live-alerts',
        label: `${cockpit.alerts.length} alertes cockpit`,
        description: 'Traiter les alertes du jour',
        icon: AlertTriangle,
        category: 'context',
        action: (navigate) => navigate('/'),
        keywords: ['alertes', 'cockpit'],
      });
    }

    const productsCache = queryClient.getQueryData(['products']);
    const products = Array.isArray(productsCache?.items) ? productsCache.items : Array.isArray(productsCache) ? productsCache : [];
    const lowStock = products.filter((p) => (p.stock_actuel || 0) < (p.seuil_alerte || 8));
    if (lowStock.length) {
      items.push({
        id: 'live-low-stock',
        label: `${lowStock.length} produits en alerte stock`,
        description: 'Ouvrir le catalogue filtré stock critique',
        icon: Package,
        category: 'context',
        action: (navigate) => navigate('/operations/catalogue?filter=low-stock'),
        keywords: ['stock', 'rupture'],
      });
    }

    return items;
  }, [queryClient]);

  const recentItems = useMemo(() => (
    recentSearches.map((r, idx) => ({
      id: `recent-${idx}-${r.item.id}`,
      label: r.item.label,
      description: `Rechercher "${r.query}"`,
      icon: Clock,
      category: 'recent',
      query: r.query,
    }))
  ), [recentSearches]);

  // Recherche fuzzy simple
  const searchItems = useCallback((searchQuery) => {
    const lowerQuery = searchQuery.toLowerCase();
    const allItems = [...quickActions, ...navigationItems, ...sectionItems, ...contextualItems];

    return allItems
      .map((item) => {
        let score = 0;

        // Match sur le label
        if (item.label.toLowerCase().includes(lowerQuery)) {
          score += item.label.toLowerCase().startsWith(lowerQuery) ? 100 : 50;
        }

        // Match sur la description
        if (item.description?.toLowerCase().includes(lowerQuery)) {
          score += 25;
        }

        // Match sur les keywords
        item.keywords?.forEach((keyword) => {
          if (keyword.includes(lowerQuery)) {
            score += 30;
          }
        });

        return { ...item, score };
      })
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 10);
  }, [contextualItems]);

  // Résultats de recherche
  const results = useMemo(() => {
    if (!query.trim()) {
      return [
        ...liveSuggestions.slice(0, 2),
        ...contextualItems.slice(0, 3),
        ...recentItems.slice(0, 3),
        ...sectionItems.slice(0, 4),
        ...quickActions.slice(0, 4),
      ];
    }
    return searchItems(query);
  }, [query, contextualItems, recentItems, searchItems, liveSuggestions]);

  // Reset selected index quand les résultats changent
  useEffect(() => {
    setSelectedIndex(0);
  }, [results]);

  // Exécuter une action
  const executeItem = useCallback((item) => {
    if (!item) return;

    // Recharger une recherche récente sans quitter
    if (item.category === 'recent' && item.query) {
      setQuery(item.query);
      return;
    }

    // Sauvegarder dans les recherches récentes
    if (query.trim()) {
      const newRecent = [
        { query, item: { id: item.id, label: item.label } },
        ...recentSearches.filter((r) => r.item.id !== item.id),
      ].slice(0, 5);
      setRecentSearches(newRecent);
      try {
        localStorage.setItem('commandbar-recent', JSON.stringify(newRecent));
      } catch {
        // Ignore
      }
    }

    // Exécuter l'action
    if (item.action) {
      item.action(navigate);
    } else if (item.path) {
      navigate(item.path);
    }

    close();
  }, [query, recentSearches, navigate, close]);

  // Navigation clavier
  const handleKeyDown = useCallback((e) => {
    if (!isOpen) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (results[selectedIndex]) {
          executeItem(results[selectedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        close();
        break;
    }
  }, [isOpen, results, selectedIndex, executeItem, close]);

  const value = useMemo(() => ({
    isOpen,
    open,
    close,
    toggle,
    query,
    setQuery,
    results,
    selectedIndex,
    setSelectedIndex,
    executeItem,
    handleKeyDown,
    currentContext,
    recentSearches,
    quickActions,
    navigationItems,
    sectionItems,
  }), [
    isOpen, open, close, toggle, query, results,
    selectedIndex, executeItem, handleKeyDown,
    currentContext, recentSearches,
  ]);

  return (
    <CommandBarContext.Provider value={value}>
      {children}
    </CommandBarContext.Provider>
  );
}

export function useCommandBar() {
  const context = useContext(CommandBarContext);
  if (!context) {
    throw new Error('useCommandBar must be used within a CommandBarProvider');
  }
  return context;
}

export default CommandBarContext;
