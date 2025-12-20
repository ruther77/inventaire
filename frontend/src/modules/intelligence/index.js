/**
 * Intelligence Module - Re-exports from features
 *
 * Plan de restructuration 2025-12
 */

// Main pages
export { default as IntelligencePage } from '@/features/intelligence/IntelligencePage.jsx';
export { default as InventoryIntelligencePage } from '@/features/intelligence/InventoryIntelligencePage.jsx';
export { default as ForecastPage } from '@/features/intelligence/ForecastPage.jsx';
export { default as AnomaliesPage } from '@/features/intelligence/AnomaliesPage.jsx';
export { default as ScoringPage } from '@/features/intelligence/ScoringPage.jsx';
export { default as MarginsPage } from '@/features/intelligence/MarginsPage.jsx';

// Components
export {
  ABCMatrix,
  MatrixCell,
  MATRIX_CONFIG,
  CELL_PRIORITIES,
  ForecastChart,
  CustomTooltip,
  SupplierScoreCard,
  ScoreRadar,
  DimensionBar,
  DIMENSIONS,
  AnomalyList,
  AnomalyItem,
  SEVERITY_CONFIG,
  ANOMALY_TYPES,
} from './components/index.js';
