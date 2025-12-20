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
import useCommandBarLiveSuggestions, { useContextualSuggestions } from '../hooks/useCommandBarLiveSuggestions.js';

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

  // Section actuelle pour les suggestions contextuelles
  const currentSectionId = useMemo(() => {
    const path = location.pathname;
    if (path.startsWith('/operations')) return 'operations';
    if (path.startsWith('/finances')) return 'finances';
    if (path.startsWith('/intelligence')) return 'intelligence';
    return 'cockpit';
  }, [location.pathname]);

  // Suggestions temps réel avec debounce
  const { liveSuggestions, isLoading: isLoadingLive } = useCommandBarLiveSuggestions(query, {
    enabled: isOpen,
    debounceMs: 300,
    minQueryLength: 2,
  });

  // Suggestions contextuelles statiques
  const contextualSuggestions = useContextualSuggestions(currentSectionId);

  // Anciens items contextuels (fallback si les nouveaux ne marchent pas)
  const contextualItems = useMemo(() => {
    // On utilise maintenant contextualSuggestions, mais on garde la logique legacy pour compatibilité
    if (contextualSuggestions.length > 0) {
      return contextualSuggestions;
    }

    // Fallback legacy
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
  }, [currentContext, contextualSuggestions]);

  // Note: liveSuggestions est maintenant géré par le hook useCommandBarLiveSuggestions
  // (défini plus haut dans le composant)

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
    const allItems = [
      ...quickActions,
      ...navigationItems,
      ...sectionItems,
      ...contextualItems,
      ...liveSuggestions, // Intégrer les suggestions temps réel
    ];

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

        // Boost pour les items live (fraîchement récupérés)
        if (item.category?.startsWith('live-')) {
          score += 20;
        }

        return { ...item, score };
      })
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 12); // Augmenter légèrement le nombre de résultats
  }, [contextualItems, liveSuggestions]);

  // Résultats de recherche
  const results = useMemo(() => {
    if (!query.trim()) {
      // Vue par défaut : prioriser les suggestions temps réel et contextuelles
      return [
        ...liveSuggestions.slice(0, 3), // Suggestions temps réel en premier
        ...contextualItems.slice(0, 3), // Suggestions contextuelles
        ...recentItems.slice(0, 2),     // Recherches récentes
        ...sectionItems.slice(0, 3),    // Sections principales
        ...quickActions.slice(0, 3),    // Actions rapides
      ];
    }
    // Vue de recherche : utiliser la recherche fuzzy avec les suggestions live
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
    liveSuggestions,
    isLoadingLive,
    currentSectionId,
  }), [
    isOpen, open, close, toggle, query, results,
    selectedIndex, executeItem, handleKeyDown,
    currentContext, recentSearches, liveSuggestions,
    isLoadingLive, currentSectionId,
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
