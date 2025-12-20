/**
 * Cockpit Module - Re-exports from features
 *
 * Plan de restructuration 2025-12
 */

// Main page
export { default as CockpitPage } from '@/features/cockpit/CockpitPage.jsx';

// Components
export {
  KPIStream,
  KPICard,
  AlertsPanel,
  AlertItem,
  QuickActionsPanel,
  QuickActionsRow,
  ActionButton,
  defaultActions,
  HealthScorePanel,
  HealthGauge,
  DomainMetric,
} from './components/index.js';
