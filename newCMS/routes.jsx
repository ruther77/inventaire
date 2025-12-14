/**
 * newCMS Routes Configuration
 * Architecture UX Next-Gen 2025
 */

import {
  Gauge,
  ShoppingBag,
  Wallet,
  Utensils,
  Brain,
  Settings,
  Bell,
  Smartphone,
} from 'lucide-react';

import {
  CockpitPage,
  OperationsPage,
  FinancePage,
  RestaurantPage,
  IntelligencePage,
  ConfigPage,
  AlertsCenter,
  MobileInventoryPage,
} from './pages';

/**
 * Routes principales - 6 vues + extras
 */
export const routes = [
  {
    path: '/',
    label: 'Cockpit',
    description: 'Vue 360° Morning Brief',
    icon: Gauge,
    element: <CockpitPage />,
    gradient: 'from-blue-500 to-cyan-400',
    color: 'blue',
  },
  {
    path: '/operations',
    label: 'Opérations',
    description: 'Catalogue | Factures | Stock | Prix',
    icon: ShoppingBag,
    element: <OperationsPage />,
    gradient: 'from-emerald-500 to-teal-400',
    color: 'emerald',
  },
  {
    path: '/finances',
    label: 'Finances',
    description: 'Transactions | Rapprochement | Comptes',
    icon: Wallet,
    element: <FinancePage />,
    gradient: 'from-violet-500 to-purple-400',
    color: 'violet',
  },
  {
    path: '/restaurant',
    label: 'Restaurant',
    description: 'Menus | Charges | Stock | Prévisions',
    icon: Utensils,
    element: <RestaurantPage />,
    gradient: 'from-orange-500 to-amber-400',
    color: 'orange',
  },
  {
    path: '/intelligence',
    label: 'Intelligence',
    description: 'IA & Analytics',
    icon: Brain,
    element: <IntelligencePage />,
    gradient: 'from-pink-500 to-rose-400',
    color: 'pink',
  },
  {
    path: '/config',
    label: 'Configuration',
    description: 'Règles | Audit | Utilisateurs',
    icon: Settings,
    element: <ConfigPage />,
    gradient: 'from-slate-500 to-slate-400',
    color: 'slate',
  },
  {
    path: '/alerts',
    label: 'Alertes',
    description: 'Centre de notifications',
    icon: Bell,
    element: <AlertsCenter />,
    gradient: 'from-rose-500 to-red-400',
    color: 'rose',
    badge: 3, // Dynamic badge count
  },
  {
    path: '/mobile/inventory',
    label: 'Inventaire Mobile',
    description: 'Scanner et ajustement',
    icon: Smartphone,
    element: <MobileInventoryPage />,
    gradient: 'from-cyan-500 to-blue-400',
    color: 'cyan',
    mobileOnly: true,
  },
];

/**
 * Sections de navigation pour sidebar
 */
export const navigationSections = [
  {
    id: 'cockpit',
    label: 'Cockpit',
    icon: Gauge,
    path: '/',
    gradient: 'from-blue-500 to-cyan-400',
    isHome: true,
  },
  {
    id: 'operations',
    label: 'Opérations',
    icon: ShoppingBag,
    path: '/operations',
    gradient: 'from-emerald-500 to-teal-400',
  },
  {
    id: 'finances',
    label: 'Finances',
    icon: Wallet,
    path: '/finances',
    gradient: 'from-violet-500 to-purple-400',
  },
  {
    id: 'restaurant',
    label: 'Restaurant',
    icon: Utensils,
    path: '/restaurant',
    gradient: 'from-orange-500 to-amber-400',
  },
  {
    id: 'intelligence',
    label: 'Intelligence',
    icon: Brain,
    path: '/intelligence',
    gradient: 'from-pink-500 to-rose-400',
  },
  {
    id: 'config',
    label: 'Config',
    icon: Settings,
    path: '/config',
    gradient: 'from-slate-500 to-slate-400',
  },
];

/**
 * Raccourcis clavier globaux
 */
export const keyboardShortcuts = [
  { key: '⌘K', action: 'Command bar' },
  { key: '⌘/', action: 'Aide contextuelle' },
  { key: '⌘1', action: 'Cockpit' },
  { key: '⌘2', action: 'Opérations' },
  { key: '⌘3', action: 'Finances' },
  { key: '⌘4', action: 'Restaurant' },
  { key: '⌘5', action: 'Intelligence' },
  { key: '⌘6', action: 'Config' },
  { key: '⌘N', action: 'Nouvelle entrée' },
  { key: '⌘S', action: 'Sauvegarder' },
  { key: 'Esc', action: 'Fermer modal/drawer' },
];

export default routes;
