/**
 * UI Components - Exports centralisés
 * Import unique : import { Button, Modal, Input } from '@/components/ui';
 *
 * Version 2.0 - Refactoré selon audit UX/UI expert
 */

// Primitives
export { default as Button } from './Button.jsx';
export { default as Input } from './Input.jsx';
export { default as Select } from './Select.jsx';
export {
  default as Card,
  CardHeader,
  CardContent,
  CardFooter,
} from './Card.jsx';

// Layout - Grid System
export {
  default as Grid,
  GridItem,
  AutoGrid,
  MasonryGrid,
  Stack,
  Inline,
  Cluster,
} from './Grid.jsx';

// Feedback - Skeletons (avec shimmer et stagger)
export {
  default as Skeleton,
  SkeletonText,
  SkeletonCircle,
  SkeletonAvatar,
  MetricCardSkeleton,
  CardSkeleton,
  TableSkeleton,
  TableRowSkeleton,
  ListSkeleton,
  ListItemSkeleton,
  ChartSkeleton,
  ProductCardSkeleton,
  FormFieldSkeleton,
  FormSkeleton,
  SidebarNavSkeleton,
  DashboardSkeleton,
  PageSkeleton,
} from './Skeleton.jsx';

export {
  default as EmptyState,
  EmptySearch,
  EmptyList,
  EmptyError,
  EmptyData,
} from './EmptyState.jsx';

// Overlay
export { default as Modal, ConfirmDialog } from './Modal.jsx';
export { default as FiltersDrawer } from './FiltersDrawer.jsx';
export {
  default as Toast,
  ToastProvider,
  useToast,
} from './Toast.jsx';

// Command Palette
export {
  default as CommandPalette,
  CommandPaletteProvider,
  useCommandPalette,
} from './CommandPalette.jsx';

// Keyboard Shortcuts
export {
  default as KeyCombo,
  ShortcutsProvider,
  useShortcuts,
  ShortcutsHelpModal,
  ShortcutHint,
  GlobalShortcuts,
  useSequentialHotkey,
} from './KeyboardShortcuts.jsx';

// Data Display
export {
  default as MetricCard,
  MetricCardGroup,
  CompactMetricCard,
} from './MetricCard.jsx';

export { default as AnimatedMetricCard } from './AnimatedMetricCard.jsx';

export {
  default as Badge,
  StatusBadge,
  CountBadge,
  BadgeGroup,
} from './Badge.jsx';

// DataTable
export { default as DataTable } from './DataTable.jsx';

export {
  default as Tooltip,
  TooltipTrigger,
  InfoTooltip,
} from './Tooltip.jsx';

// Layout
export { default as SectionHeader } from './SectionHeader.jsx';
export { default as MegaSectionNav } from './MegaSectionNav.jsx';

// Design System - Tokens complets
export {
  default as designTokens,
  // Spacing
  spacing,
  padding,
  paddingX,
  paddingY,
  // Radius
  radius,
  radiusSemantic,
  // Shadows
  shadows,
  // Colors
  statusColors,
  trendColors,
  surfaceColors,
  // Typography
  typography,
  // Transitions
  transitions,
  easing,
  // Focus
  focus,
  // Tactile
  tactile,
  // Presets
  presets,
  // Animations
  animations,
  // Breakpoints
  breakpoints,
  // Z-Index
  zIndex,
  // Helpers
  getStatusClasses,
  getTrendClasses,
  cx,
  getStaggerDelay,
  getFocusClasses,
  getSurfaceClasses,
} from './design-tokens.js';
