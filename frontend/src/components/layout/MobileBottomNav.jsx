import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { MoreHorizontal } from 'lucide-react';
import clsx from 'clsx';
import useMobileNav from '@/hooks/useMobileNav.js';
import MobileMoreMenu from './MobileMoreMenu.jsx';

/**
 * Barre de navigation mobile (bottom bar)
 *
 * Fonctionnalités:
 * - Fixée en bas de l'écran (hauteur 64px)
 * - 4 items principaux + bouton "Plus"
 * - Icônes + labels courts
 * - Item actif avec indicateur visuel
 * - Animation sur tap (scale + spring)
 * - Safe area padding pour iPhones avec notch
 * - Menu "Plus" pour items secondaires
 */

// SVG Icons inline (optimisés pour la performance)
const IconGauge = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2v4m0 12v4m10-10h-4M6 12H2m15.3 7.3l-2.8-2.8M9.5 9.5 6.7 6.7m12.6 0-2.8 2.8m-6.4 6.4-2.8 2.8M21 12c0 4.97-4.03 9-9 9s-9-4.03-9-9 4.03-9 9-9 9 4.03 9 9z" />
    <circle cx="12" cy="12" r="2" />
  </svg>
);

const IconShoppingBag = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
    <line x1="3" y1="6" x2="21" y2="6" />
    <path d="M16 10a4 4 0 0 1-8 0" />
  </svg>
);

const IconWallet = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4" />
    <path d="M3 5v14a2 2 0 0 0 2 2h16v-5" />
    <path d="M18 12a2 2 0 0 0 0 4h4v-4Z" />
  </svg>
);

const IconUtensils = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2" />
    <path d="M7 2v20" />
    <path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3Zm0 0v7" />
  </svg>
);

// Mapping des icônes
const iconMap = {
  'cockpit': IconGauge,
  'operations': IconShoppingBag,
  'finances': IconWallet,
  'restaurant': IconUtensils,
};

// Animations
const tapAnimation = {
  scale: 0.92,
  transition: {
    type: 'spring',
    stiffness: 500,
    damping: 30,
  },
};

const activeIndicatorVariants = {
  hidden: { scale: 0, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 400,
      damping: 25,
    },
  },
};

export default function MobileBottomNav() {
  const {
    primaryItems,
    secondaryItems,
    isMoreMenuOpen,
    isSecondaryActive,
    toggleMoreMenu,
    closeMoreMenu,
    isItemActive,
  } = useMobileNav();

  return (
    <>
      {/* Bottom Navigation Bar */}
      <nav
        className="lg:hidden fixed bottom-0 inset-x-0 z-50 border-t border-white/10 bg-slate-900/95 backdrop-blur-xl"
        style={{
          paddingBottom: 'env(safe-area-inset-bottom)',
          WebkitBackdropFilter: 'blur(20px)',
        }}
      >
        <div className="grid grid-cols-5 h-16">
          {/* Primary Items */}
          {primaryItems.map((item) => {
            const Icon = iconMap[item.id];
            const isActive = isItemActive(item.path);
            const gradient = item.section?.gradient;
            const color = item.section?.color;

            return (
              <NavLink
                key={item.id}
                to={item.path}
                className="relative flex flex-col items-center justify-center gap-1 text-xs transition-colors"
                style={{
                  touchAction: 'manipulation',
                  WebkitTapHighlightColor: 'transparent',
                }}
              >
                {({ isActive: navActive }) => (
                  <motion.div
                    className="flex flex-col items-center justify-center gap-1 w-full"
                    whileTap={tapAnimation}
                  >
                    {/* Active indicator (top bar) */}
                    <motion.div
                      className={clsx(
                        'absolute top-0 left-1/2 -translate-x-1/2 h-0.5 rounded-full',
                        `bg-gradient-to-r ${gradient}`
                      )}
                      initial={false}
                      animate={{
                        width: navActive ? '40%' : '0%',
                        opacity: navActive ? 1 : 0,
                      }}
                      transition={{
                        type: 'spring',
                        stiffness: 300,
                        damping: 30,
                      }}
                      style={{
                        boxShadow: navActive ? `0 0 10px var(--color-accent-${color})` : 'none',
                      }}
                    />

                    {/* Icon Container */}
                    <div
                      className={clsx(
                        'relative flex h-9 w-9 items-center justify-center rounded-xl transition-all duration-200',
                        navActive
                          ? `bg-gradient-to-br ${gradient} text-white shadow-lg`
                          : 'bg-white/5 text-slate-400'
                      )}
                    >
                      {Icon && <Icon className="h-5 w-5" />}

                      {/* Pulse effect when active */}
                      {navActive && (
                        <motion.div
                          className="absolute inset-0 rounded-xl bg-white/20"
                          initial={{ opacity: 0, scale: 1 }}
                          animate={{
                            opacity: [0.5, 0],
                            scale: [1, 1.2],
                          }}
                          transition={{
                            duration: 1.5,
                            repeat: Infinity,
                            ease: 'easeOut',
                          }}
                        />
                      )}

                      {/* Active dot indicator */}
                      {navActive && (
                        <motion.div
                          variants={activeIndicatorVariants}
                          initial="hidden"
                          animate="visible"
                          className={clsx(
                            'absolute -top-1 -right-1 w-2 h-2 rounded-full',
                            color === 'blue' ? 'bg-blue-400' :
                            color === 'emerald' ? 'bg-emerald-400' :
                            color === 'violet' ? 'bg-violet-400' :
                            color === 'orange' ? 'bg-orange-400' : 'bg-blue-400'
                          )}
                          style={{
                            boxShadow: `0 0 8px currentColor`,
                          }}
                        />
                      )}
                    </div>

                    {/* Label */}
                    <span
                      className={clsx(
                        'font-medium transition-colors duration-200',
                        navActive ? 'text-white' : 'text-slate-500'
                      )}
                    >
                      {item.label}
                    </span>
                  </motion.div>
                )}
              </NavLink>
            );
          })}

          {/* More Button */}
          <button
            onClick={toggleMoreMenu}
            className="relative flex flex-col items-center justify-center gap-1 text-xs transition-colors"
            style={{
              touchAction: 'manipulation',
              WebkitTapHighlightColor: 'transparent',
            }}
            aria-label="Plus d'options"
            type="button"
          >
            <motion.div
              className="flex flex-col items-center justify-center gap-1 w-full"
              whileTap={tapAnimation}
            >
              {/* Active indicator when secondary is active */}
              <motion.div
                className="absolute top-0 left-1/2 -translate-x-1/2 h-0.5 rounded-full bg-gradient-to-r from-pink-500 to-rose-400"
                initial={false}
                animate={{
                  width: isSecondaryActive ? '40%' : '0%',
                  opacity: isSecondaryActive ? 1 : 0,
                }}
                transition={{
                  type: 'spring',
                  stiffness: 300,
                  damping: 30,
                }}
                style={{
                  boxShadow: isSecondaryActive ? '0 0 10px var(--color-accent-pink)' : 'none',
                }}
              />

              {/* Icon Container */}
              <div
                className={clsx(
                  'relative flex h-9 w-9 items-center justify-center rounded-xl transition-all duration-200',
                  isMoreMenuOpen || isSecondaryActive
                    ? 'bg-gradient-to-br from-slate-500 to-slate-600 text-white shadow-lg'
                    : 'bg-white/5 text-slate-400'
                )}
              >
                <motion.div
                  animate={{
                    rotate: isMoreMenuOpen ? 90 : 0,
                  }}
                  transition={{
                    type: 'spring',
                    stiffness: 300,
                    damping: 25,
                  }}
                >
                  <MoreHorizontal className="h-5 w-5" />
                </motion.div>

                {/* Pulse effect when menu is open or secondary active */}
                {(isMoreMenuOpen || isSecondaryActive) && (
                  <motion.div
                    className="absolute inset-0 rounded-xl bg-white/20"
                    initial={{ opacity: 0, scale: 1 }}
                    animate={{
                      opacity: [0.5, 0],
                      scale: [1, 1.2],
                    }}
                    transition={{
                      duration: 1.5,
                      repeat: Infinity,
                      ease: 'easeOut',
                    }}
                  />
                )}

                {/* Active dot when secondary is active */}
                {isSecondaryActive && (
                  <motion.div
                    variants={activeIndicatorVariants}
                    initial="hidden"
                    animate="visible"
                    className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-pink-400"
                    style={{
                      boxShadow: '0 0 8px rgba(236, 72, 153, 0.8)',
                    }}
                  />
                )}
              </div>

              {/* Label */}
              <span
                className={clsx(
                  'font-medium transition-colors duration-200',
                  isMoreMenuOpen || isSecondaryActive ? 'text-white' : 'text-slate-500'
                )}
              >
                Plus
              </span>
            </motion.div>
          </button>
        </div>
      </nav>

      {/* More Menu */}
      <MobileMoreMenu
        isOpen={isMoreMenuOpen}
        onClose={closeMoreMenu}
        items={secondaryItems}
      />
    </>
  );
}
