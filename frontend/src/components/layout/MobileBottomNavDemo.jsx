/**
 * DEMO - Visualisation de la Bottom Nav Mobile
 *
 * Ce fichier sert de démo/test pour la navigation mobile.
 * Il n'est pas utilisé en production mais permet de visualiser
 * tous les états possibles de la bottom bar.
 *
 * Usage: Importer ce composant dans une page de démo
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import MobileBottomNav from './MobileBottomNav.jsx';

export default function MobileBottomNavDemo() {
  const [currentDemo, setCurrentDemo] = useState('default');

  const demos = [
    {
      id: 'default',
      name: 'État par défaut',
      description: 'Navigation normale avec Cockpit actif',
    },
    {
      id: 'operations',
      name: 'Opérations actif',
      description: 'Item Opérations sélectionné',
    },
    {
      id: 'more-open',
      name: 'Menu Plus ouvert',
      description: 'Menu secondaire affiché',
    },
    {
      id: 'secondary-active',
      name: 'Intelligence actif',
      description: 'Item secondaire actif, indicateur sur "Plus"',
    },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Mobile Bottom Navigation - Demo
          </h1>
          <p className="text-slate-400">
            Visualisation interactive de la navigation mobile
          </p>
        </div>

        {/* Demo Selector */}
        <div className="glass-panel rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-semibold">États de démonstration</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {demos.map((demo) => (
              <button
                key={demo.id}
                onClick={() => setCurrentDemo(demo.id)}
                className={`
                  p-4 rounded-xl text-left transition-all
                  ${currentDemo === demo.id
                    ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/10 border-2 border-blue-500/50'
                    : 'bg-white/5 border-2 border-transparent hover:bg-white/10'
                  }
                `}
              >
                <p className="font-medium">{demo.name}</p>
                <p className="text-sm text-slate-400 mt-1">{demo.description}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Specs */}
        <div className="glass-panel rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-semibold">Spécifications techniques</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-blue-400">Dimensions</h3>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>• Hauteur: 64px (h-16)</li>
                <li>• Z-index: 50 (au-dessus du contenu)</li>
                <li>• Safe area: env(safe-area-inset-bottom)</li>
              </ul>
            </div>

            <div className="space-y-2">
              <h3 className="text-sm font-medium text-purple-400">Animations</h3>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>• Tap scale: 0.92 (spring)</li>
                <li>• Pulse: 1.5s infinite</li>
                <li>• Menu slide: spring (400/35)</li>
              </ul>
            </div>

            <div className="space-y-2">
              <h3 className="text-sm font-medium text-emerald-400">Items principaux</h3>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>• Cockpit (Gauge)</li>
                <li>• Opérations (ShoppingBag)</li>
                <li>• Finances (Wallet)</li>
                <li>• Restaurant (Utensils)</li>
              </ul>
            </div>

            <div className="space-y-2">
              <h3 className="text-sm font-medium text-pink-400">Items secondaires</h3>
              <ul className="text-sm text-slate-300 space-y-1">
                <li>• Intelligence (Brain)</li>
                <li>• Paramètres (Settings)</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Features */}
        <div className="glass-panel rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-semibold">Fonctionnalités</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-blue-400 mt-2" />
              <div>
                <p className="font-medium text-sm">Indicateur actif</p>
                <p className="text-xs text-slate-400 mt-1">
                  Barre gradient en haut + dot lumineux
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-purple-400 mt-2" />
              <div>
                <p className="font-medium text-sm">Menu Plus</p>
                <p className="text-xs text-slate-400 mt-1">
                  Slide-up avec backdrop blur
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-pink-400 mt-2" />
              <div>
                <p className="font-medium text-sm">Touch optimisé</p>
                <p className="text-xs text-slate-400 mt-1">
                  40px+ targets, no tap highlight
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Code Example */}
        <div className="glass-panel rounded-2xl p-6 space-y-4">
          <h2 className="text-lg font-semibold">Utilisation du hook</h2>
          <pre className="bg-slate-950 rounded-lg p-4 text-sm overflow-x-auto">
            <code className="text-emerald-400">{`import { useMobileNav } from '@/hooks';

function MyComponent() {
  const {
    primaryItems,      // 4 items principaux
    secondaryItems,    // 2 items secondaires
    activeItem,        // Item actif
    isMoreMenuOpen,    // État menu Plus
    toggleMoreMenu,    // Toggle menu
    isItemActive,      // Check si path actif
  } = useMobileNav();

  return (
    <div>
      {activeItem && (
        <p>Route active: {activeItem.label}</p>
      )}
    </div>
  );
}`}</code>
          </pre>
        </div>

        {/* Spacer for bottom nav */}
        <div className="h-24" />
      </div>

      {/* Bottom Nav (simulé en overlay) */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-slate-950/50" />
      </div>
    </div>
  );
}
