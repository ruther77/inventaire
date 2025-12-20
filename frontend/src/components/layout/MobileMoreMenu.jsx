import { motion, AnimatePresence } from 'framer-motion';
import { NavLink } from 'react-router-dom';
import { X } from 'lucide-react';
import clsx from 'clsx';

/**
 * Menu "Plus" pour la navigation mobile
 *
 * - Slide up depuis le bottom nav
 * - Liste des items secondaires (Intelligence, Paramètres)
 * - Backdrop semi-transparent
 * - Animation Framer Motion
 * - Fermeture au tap outside
 */

const backdropVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      duration: 0.2,
      ease: 'easeOut',
    },
  },
  exit: {
    opacity: 0,
    transition: {
      duration: 0.15,
      ease: 'easeIn',
    },
  },
};

const menuVariants = {
  hidden: {
    y: '100%',
    opacity: 0,
  },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 400,
      damping: 35,
      mass: 0.8,
    },
  },
  exit: {
    y: '100%',
    opacity: 0,
    transition: {
      duration: 0.2,
      ease: [0.4, 0, 0.2, 1],
    },
  },
};

const itemVariants = {
  hidden: { x: -20, opacity: 0 },
  visible: (i) => ({
    x: 0,
    opacity: 1,
    transition: {
      delay: i * 0.05,
      duration: 0.2,
      ease: 'easeOut',
    },
  }),
};

export default function MobileMoreMenu({ isOpen, onClose, items }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm"
            onClick={onClose}
            style={{ touchAction: 'none' }}
          />

          {/* Menu Panel */}
          <motion.div
            variants={menuVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed bottom-16 inset-x-0 z-[70] mx-4 mb-2"
            style={{ touchAction: 'pan-y' }}
          >
            <div className="glass-panel-elevated rounded-2xl overflow-hidden shadow-2xl border border-white/10">
              {/* Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                <h3 className="text-sm font-semibold text-white">Plus d'options</h3>
                <button
                  onClick={onClose}
                  className="p-2 -mr-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 active:bg-white/20 transition-colors"
                  style={{
                    touchAction: 'manipulation',
                    minWidth: '40px',
                    minHeight: '40px',
                    WebkitTapHighlightColor: 'transparent',
                  }}
                  aria-label="Fermer le menu"
                  type="button"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Items List */}
              <div className="p-2">
                {items.map((item, index) => {
                  const Icon = item.section?.icon;
                  const gradient = item.section?.gradient;
                  const color = item.section?.color;

                  return (
                    <motion.div
                      key={item.id}
                      custom={index}
                      variants={itemVariants}
                      initial="hidden"
                      animate="visible"
                    >
                      <NavLink
                        to={item.path}
                        onClick={onClose}
                        className={({ isActive }) =>
                          clsx(
                            'group relative flex items-center gap-4 px-4 py-3.5 rounded-xl',
                            'transition-all duration-200',
                            'active:scale-[0.98]',
                            isActive
                              ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/10 text-white'
                              : 'text-slate-300 hover:text-white hover:bg-white/5'
                          )
                        }
                        style={{
                          touchAction: 'manipulation',
                          WebkitTapHighlightColor: 'transparent',
                        }}
                      >
                        {({ isActive }) => (
                          <>
                            {/* Active indicator */}
                            <motion.div
                              className={clsx(
                                'absolute left-0 top-1/2 -translate-y-1/2 w-1 rounded-full',
                                `bg-gradient-to-b ${gradient}`
                              )}
                              initial={{ height: 0, opacity: 0 }}
                              animate={{
                                height: isActive ? 28 : 0,
                                opacity: isActive ? 1 : 0,
                              }}
                              style={{
                                boxShadow: isActive ? `0 0 15px var(--color-accent-${color})` : 'none',
                              }}
                            />

                            {/* Icon */}
                            <div
                              className={clsx(
                                'relative p-2.5 rounded-xl transition-all duration-200',
                                isActive
                                  ? `bg-gradient-to-br ${gradient}`
                                  : 'bg-white/5 group-hover:bg-white/10'
                              )}
                            >
                              {Icon && <Icon className="w-5 h-5" />}
                              {isActive && (
                                <div className="absolute inset-0 rounded-xl bg-white/10 animate-pulse" />
                              )}
                            </div>

                            {/* Label & Description */}
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-sm">{item.label}</p>
                              {item.section?.description && (
                                <p className="text-xs text-slate-500 truncate mt-0.5">
                                  {item.section.description}
                                </p>
                              )}
                            </div>

                            {/* Active dot */}
                            {isActive && (
                              <motion.div
                                layoutId="moreMenuActiveIndicator"
                                className={clsx(
                                  'w-2 h-2 rounded-full',
                                  color === 'pink' ? 'bg-pink-400' : 'bg-blue-400'
                                )}
                                style={{
                                  boxShadow: color === 'pink'
                                    ? '0 0 10px rgba(236, 72, 153, 0.8)'
                                    : '0 0 10px rgba(59, 130, 246, 0.8)',
                                }}
                              />
                            )}
                          </>
                        )}
                      </NavLink>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
