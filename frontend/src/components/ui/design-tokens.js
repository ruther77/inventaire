/**
 * Design Tokens - Dark Theme Design System (2025 Next-Gen)
 *
 * Centralise les tokens de design pour la consistance systémique.
 * Basé sur le design system newCMS avec dark mode glass morphism.
 *
 * Version 3.0 - Unifié dark theme
 */

// ============================================
// COLORS - Dark Theme Palette
// ============================================

export const colors = {
  // Backgrounds (dark to light)
  bg: {
    primary: 'bg-slate-950',           // #0a0a0f - Darkest
    secondary: 'bg-slate-900',          // #12121a
    tertiary: 'bg-slate-800',           // #1e293b
    card: 'bg-white/5',                 // Glass effect
    cardHover: 'bg-white/10',
    elevated: 'bg-slate-800/80',
  },

  // Text colors (light to dark for dark theme)
  text: {
    primary: 'text-white',              // Pure white
    secondary: 'text-slate-300',        // #cbd5e1
    muted: 'text-slate-400',            // #94a3b8
    dimmed: 'text-slate-500',           // #64748b
    inverse: 'text-slate-900',          // For light surfaces
  },

  // Borders
  border: {
    default: 'border-white/10',
    hover: 'border-white/20',
    active: 'border-white/30',
    subtle: 'border-white/5',
    strong: 'border-white/40',
  },

  // Accent colors
  accent: {
    blue: 'text-blue-400',
    blueHover: 'text-blue-300',
    purple: 'text-violet-400',
    emerald: 'text-emerald-400',
    amber: 'text-amber-400',
    rose: 'text-rose-400',
    orange: 'text-orange-400',
  },
};

// ============================================
// STATUS COLORS - Dark Theme Variants
// ============================================

export const statusColors = {
  success: {
    bg: 'bg-emerald-500/10',
    bgSolid: 'bg-emerald-500',
    text: 'text-emerald-400',
    textLight: 'text-emerald-300',
    border: 'border-emerald-500/30',
    borderSolid: 'border-emerald-500',
    dot: 'bg-emerald-500',
    ring: 'ring-emerald-500/50',
    glow: 'shadow-[0_0_20px_rgba(16,185,129,0.25)]',
  },
  warning: {
    bg: 'bg-amber-500/10',
    bgSolid: 'bg-amber-500',
    text: 'text-amber-400',
    textLight: 'text-amber-300',
    border: 'border-amber-500/30',
    borderSolid: 'border-amber-500',
    dot: 'bg-amber-500',
    ring: 'ring-amber-500/50',
    glow: 'shadow-[0_0_20px_rgba(245,158,11,0.25)]',
  },
  error: {
    bg: 'bg-rose-500/10',
    bgSolid: 'bg-rose-500',
    text: 'text-rose-400',
    textLight: 'text-rose-300',
    border: 'border-rose-500/30',
    borderSolid: 'border-rose-500',
    dot: 'bg-rose-500',
    ring: 'ring-rose-500/50',
    glow: 'shadow-[0_0_20px_rgba(244,63,94,0.25)]',
  },
  info: {
    bg: 'bg-blue-500/10',
    bgSolid: 'bg-blue-500',
    text: 'text-blue-400',
    textLight: 'text-blue-300',
    border: 'border-blue-500/30',
    borderSolid: 'border-blue-500',
    dot: 'bg-blue-500',
    ring: 'ring-blue-500/50',
    glow: 'shadow-[0_0_20px_rgba(59,130,246,0.25)]',
  },
  neutral: {
    bg: 'bg-slate-500/10',
    bgSolid: 'bg-slate-500',
    text: 'text-slate-400',
    textLight: 'text-slate-300',
    border: 'border-slate-500/30',
    borderSolid: 'border-slate-500',
    dot: 'bg-slate-500',
    ring: 'ring-slate-500/50',
    glow: 'shadow-none',
  },
  disabled: {
    bg: 'bg-slate-800',
    bgSolid: 'bg-slate-700',
    text: 'text-slate-500',
    textLight: 'text-slate-500',
    border: 'border-slate-700',
    borderSolid: 'border-slate-600',
    dot: 'bg-slate-600',
    ring: 'ring-slate-600/50',
    glow: 'shadow-none',
  },
};

// Trends (pour MetricCard, charts)
export const trendColors = {
  positive: 'bg-emerald-500/10 text-emerald-400',
  negative: 'bg-rose-500/10 text-rose-400',
  neutral: 'bg-slate-500/10 text-slate-400',
};

// ============================================
// SPACING - Echelle harmonique (ratio 1.5)
// ============================================

export const spacing = {
  xs: 'gap-1',      // 4px
  sm: 'gap-2',      // 8px
  md: 'gap-3',      // 12px
  lg: 'gap-4',      // 16px
  xl: 'gap-6',      // 24px
  '2xl': 'gap-8',   // 32px
  '3xl': 'gap-12',  // 48px
};

export const padding = {
  xs: 'p-1',
  sm: 'p-2',
  md: 'p-3',
  lg: 'p-4',
  xl: 'p-6',
  '2xl': 'p-8',
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
// BORDER RADIUS
// ============================================

export const radius = {
  none: 'rounded-none',
  xs: 'rounded',          // 4px
  sm: 'rounded-md',       // 6px
  md: 'rounded-lg',       // 8px
  lg: 'rounded-xl',       // 12px - Buttons, badges
  xl: 'rounded-2xl',      // 16px - Cards, panels
  '2xl': 'rounded-3xl',   // 24px - Large panels
  full: 'rounded-full',   // Pills, avatars
};

export const radiusSemantic = {
  button: 'rounded-xl',
  input: 'rounded-xl',
  card: 'rounded-2xl',
  modal: 'rounded-2xl',
  panel: 'rounded-2xl',
  badge: 'rounded-full',
  avatar: 'rounded-full',
};

// ============================================
// SHADOWS - Dark Theme
// ============================================

export const shadows = {
  none: 'shadow-none',
  sm: 'shadow-[0_2px_8px_rgba(0,0,0,0.3)]',
  md: 'shadow-[0_4px_16px_rgba(0,0,0,0.4)]',
  lg: 'shadow-[0_8px_24px_rgba(0,0,0,0.5)]',
  xl: 'shadow-[0_12px_32px_rgba(0,0,0,0.6)]',
  inner: 'shadow-inner',
  // Glow effects
  glowBlue: 'shadow-[0_0_20px_rgba(59,130,246,0.25)]',
  glowPurple: 'shadow-[0_0_20px_rgba(139,92,246,0.25)]',
  glowEmerald: 'shadow-[0_0_20px_rgba(16,185,129,0.25)]',
  glowAmber: 'shadow-[0_0_20px_rgba(245,158,11,0.25)]',
  glowRose: 'shadow-[0_0_20px_rgba(244,63,94,0.25)]',
};

// ============================================
// TYPOGRAPHY - Dark Theme
// ============================================

export const typography = {
  // Labels
  label: 'text-xs font-medium uppercase tracking-wider text-slate-400',
  labelSm: 'text-[11px] font-medium uppercase tracking-widest text-slate-500',
  labelMd: 'text-sm font-medium text-slate-400',

  // Headings - White for dark theme
  h1: 'text-4xl font-bold text-white tracking-tight',
  h2: 'text-2xl font-bold text-white',
  h3: 'text-xl font-semibold text-white',
  h4: 'text-lg font-semibold text-white',
  h5: 'text-base font-semibold text-white',
  h6: 'text-sm font-semibold text-white',

  // Body
  body: 'text-sm text-slate-300 leading-relaxed',
  bodySm: 'text-xs text-slate-400 leading-relaxed',
  bodyLg: 'text-base text-slate-300 leading-relaxed',

  // Metrics - Large numbers
  metric: 'text-3xl font-bold text-white tabular-nums',
  metricSm: 'text-2xl font-bold text-white tabular-nums',
  metricLg: 'text-4xl font-bold text-white tabular-nums',
  metricXl: 'text-5xl font-bold text-white tabular-nums',

  // Interactive
  link: 'text-blue-400 hover:text-blue-300 underline-offset-2 hover:underline',
  linkSubtle: 'text-slate-400 hover:text-white hover:underline',
};

// ============================================
// TRANSITIONS
// ============================================

export const transitions = {
  fastest: 'transition-all duration-75',
  fast: 'transition-all duration-150',
  default: 'transition-all duration-200',
  slow: 'transition-all duration-300',

  colors: 'transition-colors duration-150',
  opacity: 'transition-opacity duration-150',
  transform: 'transition-transform duration-200',
  shadow: 'transition-shadow duration-200',

  button: 'transition-[background-color,border-color,color,transform,box-shadow] duration-150',
  card: 'transition-[box-shadow,border-color,transform] duration-200',
  input: 'transition-[border-color,box-shadow] duration-150',
};

export const easing = {
  default: 'ease-out',
  smooth: 'ease-in-out',
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  spring: 'cubic-bezier(0.16, 1, 0.3, 1)',
};

// ============================================
// FOCUS STATES - Dark Theme
// ============================================

export const focus = {
  default: 'focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',
  brand: 'focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',
  destructive: 'focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',
  success: 'focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',
  subtle: 'focus:outline-none focus-visible:ring-1 focus-visible:ring-white/30',
};

// ============================================
// TACTILE - Touch targets (Apple HIG: 44px)
// ============================================

export const tactile = {
  target: 'min-w-[44px] min-h-[44px]',
  targetSm: 'min-w-[36px] min-h-[36px]',
  targetLg: 'min-w-[48px] min-h-[48px]',
};

// ============================================
// COMPONENT PRESETS - Dark Theme
// ============================================

export const presets = {
  // Cards - Glass morphism
  card: 'rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm',
  cardHover: 'rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 hover:border-white/20 transition-all duration-200',
  cardInteractive: 'rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 hover:border-white/20 active:scale-[0.99] transition-all duration-200 cursor-pointer',
  cardElevated: 'rounded-2xl bg-slate-800/80 border border-white/10 backdrop-blur-md shadow-lg',
  cardGradient: 'rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10',

  // Section containers
  section: 'p-6 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-white/10',
  sectionCompact: 'p-4 rounded-xl bg-white/5 border border-white/10',

  // Badges
  badge: 'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium bg-white/10 text-slate-300 border border-white/10',
  badgeSm: 'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium bg-white/10 text-slate-300',
  badgeLg: 'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium bg-white/10 text-slate-300',

  // Badge colors
  badgeSuccess: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  badgeWarning: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  badgeError: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
  badgeInfo: 'bg-blue-500/20 text-blue-400 border-blue-500/30',

  // Lists
  listItem: 'flex items-center justify-between rounded-xl border border-white/10 px-4 py-3 bg-white/5',
  listItemHover: 'flex items-center justify-between rounded-xl border border-white/10 px-4 py-3 bg-white/5 hover:bg-white/10 hover:border-white/20 transition-colors duration-150',
  listItemInteractive: 'flex items-center justify-between rounded-xl border border-white/10 px-4 py-3 bg-white/5 hover:bg-white/10 hover:border-white/20 active:bg-white/15 transition-colors duration-150 cursor-pointer',

  // Inputs
  inputBase: 'w-full rounded-xl border border-white/20 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 transition-[border-color,box-shadow] duration-150',
  inputFocus: 'focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50',
  inputError: 'border-rose-500/50 focus:ring-rose-500/50 focus:border-rose-500/50 bg-rose-500/5',
  inputSuccess: 'border-emerald-500/50 focus:ring-emerald-500/50 focus:border-emerald-500/50',

  // Buttons (used with Button component)
  buttonPrimary: 'bg-gradient-to-r from-blue-500 to-violet-500 text-white hover:from-blue-400 hover:to-violet-400 shadow-lg shadow-blue-500/25',
  buttonSecondary: 'bg-white/10 text-white hover:bg-white/20 border border-white/20',
  buttonGhost: 'bg-transparent text-slate-300 hover:bg-white/10 hover:text-white',
  buttonDanger: 'bg-rose-500 text-white hover:bg-rose-400',

  // Overlays
  overlay: 'fixed inset-0 bg-black/60 backdrop-blur-sm',
  overlayLight: 'fixed inset-0 bg-slate-950/80 backdrop-blur-sm',

  // Status dots
  statusDot: 'h-2 w-2 rounded-full',
  statusDotLg: 'h-3 w-3 rounded-full',
  statusDotPulse: 'h-2 w-2 rounded-full animate-pulse',

  // Dividers
  divider: 'h-px bg-white/10',
  dividerVertical: 'w-px h-full bg-white/10',

  // Skeleton
  skeleton: 'animate-pulse bg-slate-700 rounded',
};

// ============================================
// ANIMATIONS
// ============================================

export const animations = {
  fadeIn: 'animate-in fade-in duration-200',
  fadeInFast: 'animate-in fade-in duration-150',
  fadeInSlow: 'animate-in fade-in duration-300',

  slideInBottom: 'animate-in slide-in-from-bottom fade-in duration-200',
  slideInTop: 'animate-in slide-in-from-top fade-in duration-200',
  slideInLeft: 'animate-in slide-in-from-left fade-in duration-200',
  slideInRight: 'animate-in slide-in-from-right fade-in duration-200',

  zoomIn: 'animate-in zoom-in-95 fade-in duration-200',
  fadeOut: 'animate-out fade-out duration-150',
  zoomOut: 'animate-out zoom-out-95 fade-out duration-150',

  spin: 'animate-spin',
  pulse: 'animate-pulse',
  bounce: 'animate-bounce',

  stagger: (index, baseDelay = 50) => ({
    animationDelay: `${index * baseDelay}ms`,
  }),
};

// ============================================
// Z-INDEX
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
// HELPERS
// ============================================

/**
 * Get status classes for a given status
 */
export function getStatusClasses(status, type = 'all') {
  const colors = statusColors[status] || statusColors.neutral;
  if (type === 'all') {
    return `${colors.bg} ${colors.text} ${colors.border}`;
  }
  return colors[type] || '';
}

/**
 * Get trend classes for a value
 */
export function getTrendClasses(value) {
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (numValue > 0) return trendColors.positive;
  if (numValue < 0) return trendColors.negative;
  return trendColors.neutral;
}

/**
 * Combine classes conditionally
 */
export function cx(...classes) {
  return classes.filter(Boolean).join(' ');
}

/**
 * Get stagger delay for animations
 */
export function getStaggerDelay(index, baseDelay = 50) {
  return { style: { animationDelay: `${index * baseDelay}ms` } };
}

/**
 * Get focus classes for context
 */
export function getFocusClasses(context = 'default') {
  return focus[context] || focus.default;
}

export default {
  colors,
  statusColors,
  trendColors,
  spacing,
  padding,
  paddingX,
  paddingY,
  radius,
  radiusSemantic,
  shadows,
  typography,
  transitions,
  easing,
  focus,
  tactile,
  presets,
  animations,
  zIndex,
  getStatusClasses,
  getTrendClasses,
  cx,
  getStaggerDelay,
  getFocusClasses,
};
