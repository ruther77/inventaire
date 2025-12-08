/**
 * Design Tokens - Tokens de design pour la consistance systémique
 * Centralise les espacements, rayons, couleurs et autres constantes visuelles
 *
 * Version 2.0 - Refactoré selon audit UX/UI expert
 */

// ============================================
// SPACING - Échelle harmonique (ratio 1.5)
// ============================================
export const spacing = {
  xs: 'gap-1',      // 4px  - Micro (icons, inline)
  sm: 'gap-2',      // 8px  - Compact (tight groups)
  md: 'gap-3',      // 12px - Default (form fields)
  lg: 'gap-4',      // 16px - Comfortable (cards)
  xl: 'gap-6',      // 24px - Spacious (sections)
  '2xl': 'gap-8',   // 32px - Large (page sections)
  '3xl': 'gap-12',  // 48px - Extra large (page)
};

export const padding = {
  xs: 'p-1',        // 4px
  sm: 'p-2',        // 8px
  md: 'p-3',        // 12px
  lg: 'p-4',        // 16px
  xl: 'p-6',        // 24px
  '2xl': 'p-8',     // 32px
};

export const paddingX = {
  xs: 'px-1',
  sm: 'px-2',
  md: 'px-3',
  lg: 'px-4',
  xl: 'px-6',
  '2xl': 'px-8',
};

export const paddingY = {
  xs: 'py-1',
  sm: 'py-2',
  md: 'py-3',
  lg: 'py-4',
  xl: 'py-6',
  '2xl': 'py-8',
};

// ============================================
// BORDER RADIUS - Échelle harmonique (3 niveaux principaux)
// ============================================
export const radius = {
  none: 'rounded-none',   // 0px
  xs: 'rounded',          // 4px  - Subtle
  sm: 'rounded-md',       // 6px  - Small elements
  md: 'rounded-lg',       // 8px  - Inputs, small buttons
  lg: 'rounded-xl',       // 12px - Buttons, badges, inputs
  xl: 'rounded-2xl',      // 16px - Cards, panels, modals
  '2xl': 'rounded-3xl',   // 24px - Large panels, hero
  full: 'rounded-full',   // Pills, avatars, chips
};

// Semantic radius aliases
export const radiusSemantic = {
  button: 'rounded-xl',     // 12px
  input: 'rounded-xl',      // 12px
  card: 'rounded-2xl',      // 16px
  modal: 'rounded-2xl',     // 16px
  panel: 'rounded-2xl',     // 16px
  badge: 'rounded-full',    // Full
  avatar: 'rounded-full',   // Full
  chip: 'rounded-full',     // Full
};

// ============================================
// SHADOWS - Échelle progressive
// ============================================
export const shadows = {
  none: 'shadow-none',
  xs: 'shadow-[0_1px_2px_0_rgba(0,0,0,0.05)]',
  sm: 'shadow-sm',
  md: 'shadow',
  lg: 'shadow-lg',
  xl: 'shadow-xl',
  '2xl': 'shadow-2xl',
  soft: 'shadow-soft',    // Custom défini dans tailwind.config.js
  inner: 'shadow-inner',
  // Colored shadows
  brand: 'shadow-lg shadow-brand-600/20',
  success: 'shadow-lg shadow-emerald-600/20',
  warning: 'shadow-lg shadow-amber-600/20',
  error: 'shadow-lg shadow-rose-600/20',
};

// ============================================
// COLORS - Couleurs sémantiques complètes
// ============================================
export const statusColors = {
  success: {
    bg: 'bg-emerald-50',
    bgSolid: 'bg-emerald-500',
    text: 'text-emerald-700',
    textLight: 'text-emerald-600',
    border: 'border-emerald-200',
    borderSolid: 'border-emerald-500',
    dot: 'bg-emerald-500',
    ring: 'ring-emerald-500',
  },
  warning: {
    bg: 'bg-amber-50',
    bgSolid: 'bg-amber-500',
    text: 'text-amber-700',
    textLight: 'text-amber-600',
    border: 'border-amber-200',
    borderSolid: 'border-amber-500',
    dot: 'bg-amber-500',
    ring: 'ring-amber-500',
  },
  error: {
    bg: 'bg-rose-50',
    bgSolid: 'bg-rose-500',
    text: 'text-rose-700',
    textLight: 'text-rose-600',
    border: 'border-rose-200',
    borderSolid: 'border-rose-500',
    dot: 'bg-rose-500',
    ring: 'ring-rose-500',
  },
  info: {
    bg: 'bg-sky-50',
    bgSolid: 'bg-sky-500',
    text: 'text-sky-700',
    textLight: 'text-sky-600',
    border: 'border-sky-200',
    borderSolid: 'border-sky-500',
    dot: 'bg-sky-500',
    ring: 'ring-sky-500',
  },
  neutral: {
    bg: 'bg-slate-50',
    bgSolid: 'bg-slate-500',
    text: 'text-slate-700',
    textLight: 'text-slate-600',
    border: 'border-slate-200',
    borderSolid: 'border-slate-500',
    dot: 'bg-slate-500',
    ring: 'ring-slate-500',
  },
  disabled: {
    bg: 'bg-slate-100',
    bgSolid: 'bg-slate-300',
    text: 'text-slate-400',
    textLight: 'text-slate-400',
    border: 'border-slate-200',
    borderSolid: 'border-slate-300',
    dot: 'bg-slate-300',
    ring: 'ring-slate-300',
  },
};

// Trends (pour MetricCard)
export const trendColors = {
  positive: 'bg-emerald-50 text-emerald-600',
  negative: 'bg-rose-50 text-rose-600',
  neutral: 'bg-slate-50 text-slate-600',
};

// Surface colors (pour backgrounds)
export const surfaceColors = {
  primary: 'bg-white',
  secondary: 'bg-slate-50',
  tertiary: 'bg-slate-100',
  elevated: 'bg-white shadow-lg',
  overlay: 'bg-slate-900/60 backdrop-blur-sm',
  inverse: 'bg-slate-900',
};

// ============================================
// TYPOGRAPHY - Typographie complète
// ============================================
export const typography = {
  // Labels
  label: 'text-xs font-semibold uppercase tracking-widest text-slate-400',
  labelSm: 'text-[11px] font-semibold uppercase tracking-[0.3em] text-slate-400',
  labelMd: 'text-sm font-medium text-slate-600',

  // Headings
  h1: 'font-display text-4xl font-semibold text-slate-900 tracking-tight',
  h2: 'font-display text-2xl font-semibold text-slate-900',
  h3: 'text-xl font-semibold text-slate-900',
  h4: 'text-lg font-semibold text-slate-900',
  h5: 'text-base font-semibold text-slate-900',
  h6: 'text-sm font-semibold text-slate-900',

  // Body
  body: 'text-sm text-slate-600 leading-relaxed',
  bodySm: 'text-xs text-slate-500 leading-relaxed',
  bodyLg: 'text-base text-slate-600 leading-relaxed',
  bodyXl: 'text-lg text-slate-600 leading-relaxed',

  // Values (pour MetricCard)
  metric: 'text-3xl font-semibold text-slate-900 tabular-nums',
  metricSm: 'text-2xl font-semibold text-slate-900 tabular-nums',
  metricLg: 'text-4xl font-semibold text-slate-900 tabular-nums',
  metricXl: 'text-5xl font-semibold text-slate-900 tabular-nums',

  // Interactive
  link: 'text-brand-600 hover:text-brand-700 underline-offset-2 hover:underline',
  linkSubtle: 'text-slate-600 hover:text-slate-900 hover:underline',
};

// ============================================
// TRANSITIONS - Animations et transitions
// ============================================
export const transitions = {
  // Durées
  fastest: 'transition-all duration-75',
  fast: 'transition-all duration-150',
  default: 'transition-all duration-200',
  slow: 'transition-all duration-300',
  slower: 'transition-all duration-500',

  // Propriétés spécifiques
  colors: 'transition-colors duration-150',
  opacity: 'transition-opacity duration-150',
  transform: 'transition-transform duration-200',
  shadow: 'transition-shadow duration-200',

  // Combinaisons communes
  button: 'transition-[background-color,border-color,color,transform,box-shadow] duration-150',
  card: 'transition-[box-shadow,border-color,transform] duration-200',
  input: 'transition-[border-color,box-shadow] duration-150',
};

// Easing functions
export const easing = {
  default: 'ease-out',
  smooth: 'ease-in-out',
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  spring: 'cubic-bezier(0.16, 1, 0.3, 1)',
};

// ============================================
// FOCUS - États de focus accessibles (multi-contexte)
// ============================================
export const focus = {
  default: 'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2',
  brand: 'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2',
  destructive: 'focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 focus-visible:ring-offset-2',
  success: 'focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2',
  warning: 'focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2',

  // Pour fond sombre
  dark: 'focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',

  // Variantes
  within: 'focus-within:ring-2 focus-within:ring-brand-500',
  inset: 'focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand-500',
  subtle: 'focus:outline-none focus-visible:ring-1 focus-visible:ring-brand-400',
};

// ============================================
// TACTILE - Tailles minimales pour touch (Apple HIG: 44px)
// ============================================
export const tactile = {
  target: 'min-w-[44px] min-h-[44px]',
  targetSm: 'min-w-[36px] min-h-[36px]',
  targetLg: 'min-w-[48px] min-h-[48px]',
};

// ============================================
// COMPONENT PRESETS - Presets pour composants courants
// ============================================
export const presets = {
  // Cards
  card: 'rounded-2xl bg-white border border-slate-200 shadow-sm',
  cardHover: 'rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-200',
  cardInteractive: 'rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-md hover:border-slate-300 active:scale-[0.99] transition-all duration-200 cursor-pointer',
  glassCard: 'glass-panel',

  // Badges
  badge: 'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium',
  badgeSm: 'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium',
  badgeLg: 'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium',

  // Lists
  listItem: 'flex items-center justify-between rounded-xl border border-slate-100 px-4 py-3',
  listItemHover: 'flex items-center justify-between rounded-xl border border-slate-100 px-4 py-3 hover:bg-slate-50 hover:border-slate-200 transition-colors duration-150',
  listItemInteractive: 'flex items-center justify-between rounded-xl border border-slate-100 px-4 py-3 hover:bg-slate-50 hover:border-slate-200 active:bg-slate-100 transition-colors duration-150 cursor-pointer',

  // Inputs
  inputBase: 'w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 transition-[border-color,box-shadow] duration-150',
  inputFocus: 'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
  inputError: 'border-rose-400 focus:ring-rose-500 focus:border-rose-500 bg-rose-50/50',
  inputSuccess: 'border-emerald-400 focus:ring-emerald-500 focus:border-emerald-500',

  // Overlays
  overlay: 'fixed inset-0 bg-slate-900/60 backdrop-blur-sm',
  overlayLight: 'fixed inset-0 bg-white/80 backdrop-blur-sm',

  // Status dots
  statusDot: 'h-2 w-2 rounded-full',
  statusDotLg: 'h-3 w-3 rounded-full',
  statusDotWithPulse: 'h-2 w-2 rounded-full animate-pulse',

  // Dividers
  divider: 'h-px bg-slate-200',
  dividerVertical: 'w-px h-full bg-slate-200',

  // Skeleton
  skeleton: 'animate-pulse bg-slate-200 rounded',
  skeletonShimmer: 'skeleton-shimmer rounded',
};

// ============================================
// ANIMATIONS - Classes d'animation
// ============================================
export const animations = {
  // Entrées
  fadeIn: 'animate-in fade-in duration-200',
  fadeInFast: 'animate-in fade-in duration-150',
  fadeInSlow: 'animate-in fade-in duration-300',

  slideInBottom: 'animate-in slide-in-from-bottom fade-in duration-200',
  slideInTop: 'animate-in slide-in-from-top fade-in duration-200',
  slideInLeft: 'animate-in slide-in-from-left fade-in duration-200',
  slideInRight: 'animate-in slide-in-from-right fade-in duration-200',

  zoomIn: 'animate-in zoom-in-95 fade-in duration-200',

  // Sorties
  fadeOut: 'animate-out fade-out duration-150',
  zoomOut: 'animate-out zoom-out-95 fade-out duration-150',

  // Continues
  spin: 'animate-spin',
  pulse: 'animate-pulse',
  bounce: 'animate-bounce',

  // Staggered (pour listes)
  stagger: (index, baseDelay = 50) => ({
    animationDelay: `${index * baseDelay}ms`,
  }),
};

// ============================================
// BREAKPOINTS - Points de rupture
// ============================================
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

// ============================================
// Z-INDEX - Couches de profondeur
// ============================================
export const zIndex = {
  base: 'z-0',
  dropdown: 'z-10',
  sticky: 'z-20',
  fixed: 'z-30',
  modalBackdrop: 'z-40',
  modal: 'z-50',
  popover: 'z-60',
  tooltip: 'z-70',
  toast: 'z-80',
  max: 'z-[9999]',
};

// ============================================
// HELPERS - Fonctions utilitaires
// ============================================

/**
 * Retourne les classes de couleur pour un statut donné
 * @param {'success' | 'warning' | 'error' | 'info' | 'neutral' | 'disabled'} status
 * @param {'bg' | 'bgSolid' | 'text' | 'textLight' | 'border' | 'borderSolid' | 'dot' | 'ring' | 'all'} type
 */
export function getStatusClasses(status, type = 'all') {
  const colors = statusColors[status] || statusColors.neutral;
  if (type === 'all') {
    return `${colors.bg} ${colors.text} ${colors.border}`;
  }
  return colors[type] || '';
}

/**
 * Retourne les classes de trend pour une valeur
 * @param {number | string} value
 */
export function getTrendClasses(value) {
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (numValue > 0) return trendColors.positive;
  if (numValue < 0) return trendColors.negative;
  return trendColors.neutral;
}

/**
 * Combine plusieurs classes conditionnellement
 * @param {...(string | false | null | undefined)} classes
 */
export function cx(...classes) {
  return classes.filter(Boolean).join(' ');
}

/**
 * Génère des classes de délai d'animation pour effet stagger
 * @param {number} index - Index de l'élément
 * @param {number} baseDelay - Délai de base en ms
 */
export function getStaggerDelay(index, baseDelay = 50) {
  return { style: { animationDelay: `${index * baseDelay}ms` } };
}

/**
 * Retourne les classes de focus pour un contexte donné
 * @param {'default' | 'brand' | 'destructive' | 'success' | 'warning' | 'dark'} context
 */
export function getFocusClasses(context = 'default') {
  return focus[context] || focus.default;
}

/**
 * Retourne les classes de surface pour un niveau d'élévation
 * @param {'primary' | 'secondary' | 'tertiary' | 'elevated' | 'overlay' | 'inverse'} level
 */
export function getSurfaceClasses(level = 'primary') {
  return surfaceColors[level] || surfaceColors.primary;
}

export default {
  spacing,
  padding,
  paddingX,
  paddingY,
  radius,
  radiusSemantic,
  shadows,
  statusColors,
  trendColors,
  surfaceColors,
  typography,
  transitions,
  easing,
  focus,
  tactile,
  presets,
  animations,
  breakpoints,
  zIndex,
  getStatusClasses,
  getTrendClasses,
  cx,
  getStaggerDelay,
  getFocusClasses,
  getSurfaceClasses,
};
