// ============================================================================
// MOTION VARIANTS - Optimized for performance (reduced animations)
// ============================================================================

export const overlayFade = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.15 } },
  exit: { opacity: 0, transition: { duration: 0.1 } },
};

export const sidebarSlide = {
  hidden: { x: '-100%' },
  visible: { x: 0, transition: { duration: 0.2, ease: 'easeOut' } },
  exit: { x: '-100%', transition: { duration: 0.15 } },
};

// Simplified card hover - no scale/transform
export const cardGlow = {
  rest: { boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)' },
  hover: { boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2)', transition: { duration: 0.15 } },
};

export const accordion = {
  hidden: { height: 0, opacity: 0 },
  visible: { height: 'auto', opacity: 1, transition: { duration: 0.15 } },
  exit: { height: 0, opacity: 0, transition: { duration: 0.1 } },
};

export const pageTransition = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.15 } },
  exit: { opacity: 0, transition: { duration: 0.1 } },
};

// KPI Card - simplified, no scale transforms
export const kpiCard = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.2 } },
  hover: { transition: { duration: 0.15 } },
  tap: {},
};

// Stagger children - reduced delays
export const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.03,
      delayChildren: 0.05,
    },
  },
};

export const staggerItem = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.15 } },
};

// Alert slide-in - simplified
export const alertSlideIn = {
  hidden: { opacity: 0, x: 20 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.2 } },
  exit: { opacity: 0, x: 10, transition: { duration: 0.15 } },
};

// Segmented control
export const segmentedIndicator = {
  layout: true,
  transition: { type: 'spring', stiffness: 600, damping: 40 },
};

// Badge pulse - disabled for performance
export const badgePulse = {
  initial: { scale: 1 },
  animate: { scale: 1 }, // No animation
};

// Drawer slide
export const drawerSlide = {
  hidden: { x: '100%' },
  visible: { x: 0, transition: { duration: 0.2, ease: 'easeOut' } },
  exit: { x: '100%', transition: { duration: 0.15 } },
};

// Modal - simplified
export const modalScale = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.15 } },
  exit: { opacity: 0, transition: { duration: 0.1 } },
};

// Expand/collapse row
export const expandRow = {
  hidden: { height: 0, opacity: 0 },
  visible: { height: 'auto', opacity: 1, transition: { duration: 0.15 } },
  exit: { height: 0, opacity: 0, transition: { duration: 0.1 } },
};

// Dropzone - simplified
export const dropzone = {
  idle: { borderColor: 'rgba(255, 255, 255, 0.1)', backgroundColor: 'rgba(255, 255, 255, 0.02)' },
  hover: { borderColor: 'rgb(59 130 246)', backgroundColor: 'rgba(59, 130, 246, 0.05)', transition: { duration: 0.15 } },
  active: { borderColor: 'rgb(37 99 235)', backgroundColor: 'rgba(59, 130, 246, 0.1)', transition: { duration: 0.1 } },
};

// Progress bar
export const progressBar = {
  initial: { width: 0 },
  animate: (progress) => ({
    width: `${progress}%`,
    transition: { duration: 0.3, ease: 'easeOut' },
  }),
};

// Chart entry - simplified
export const chartEntry = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.3 } },
};

// Tab content - simplified
export const tabContent = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.15 } },
  exit: { opacity: 0, transition: { duration: 0.1 } },
};
