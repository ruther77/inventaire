import { useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Layers3, ChevronDown } from 'lucide-react';
import clsx from 'clsx';

const ROUTE_SECTIONS = {
  '/': [
    {
      id: 'overview.core',
      label: 'Cockpit & KPIs',
      description: 'Vue héro et indicateurs clés.',
    },
    {
      id: 'inventory.catalog',
      label: 'Catalogue',
      description: 'Filtres et top listes.',
    },
    {
      id: 'inventory.flows',
      label: 'Flux & mix',
      description: 'Entrées/sorties et mix catégories.',
    },
    {
      id: 'overview.productFile',
      label: 'Fiches produit',
      description: 'Recherche par code EAN.',
    },
  ],
  '/inventory': [
    {
      id: 'operations.manage',
      label: 'Catalogue',
      description: 'Recherche et listing produits.',
    },
    {
      id: 'insights.health',
      label: 'Santé stock',
      description: 'Répartition critique / OK.',
    },
  ],
  '/stock': [
    {
      id: 'overview.core',
      label: 'Vue globale',
      description: 'Filtres, KPIs et graphiques.',
    },
    {
      id: 'analytics.history',
      label: 'Top & journal',
      description: 'Classements et historique.',
    },
    {
      id: 'operations.adjust',
      label: 'Ajustements',
      description: 'Inventaire et corrections.',
    },
  ],
  '/import': [
    {
      id: 'workspace.intake',
      label: 'Factures & import',
      description: 'Analyse, nettoyage et création des mouvements.',
    },
    {
      id: 'workspace.catalog',
      label: 'Catalogue',
      description: 'Synchronisation des fiches et gestion des rejets.',
    },
    {
      id: 'history.list',
      label: 'Historique',
      description: 'Factures traitées récemment.',
    },
  ],
};

export default function SidebarNav({ routes, isOpen, onClose }) {
  const location = useLocation();
  const [openRoute, setOpenRoute] = useState(null);
  const basePath = location.pathname === '/' ? '/' : `/${location.pathname.split('/')[1] ?? ''}`;

  useEffect(() => {
    if (ROUTE_SECTIONS[basePath]) {
      setOpenRoute(basePath);
    } else {
      setOpenRoute(null);
    }
  }, [basePath]);

  return (
    <>
      <div
        className={clsx(
          'fixed inset-0 z-40 bg-slate-900/60 transition-opacity lg:hidden',
          isOpen ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
        onClick={onClose}
      />
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-white/10 bg-slate-950/95 px-6 pb-8 pt-6 text-white shadow-2xl transition-transform lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        )}
      >
        <div className="flex items-center gap-3 pb-8">
          <div className="rounded-2xl bg-white/10 p-3">
            <Layers3 className="h-6 w-6 text-brand-100" />
          </div>
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-slate-300">Inventaire</p>
            <p className="font-display text-xl font-semibold">Épicerie</p>
          </div>
        </div>

        <nav className="flex flex-1 flex-col gap-2">
          {routes.map(({ path, label, description, icon: Icon }) => {
            const sections = ROUTE_SECTIONS[path];
            const showSections = sections && openRoute === path;
            return (
              <div key={path} className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <NavLink
                    to={path}
                    end={path === '/'}
                    className={({ isActive }) =>
                      clsx(
                        'flex flex-1 flex-col gap-1 rounded-2xl border border-white/5 px-4 py-3 text-sm transition-all',
                        isActive ? 'bg-white text-slate-900 shadow-lg' : 'bg-white/5 text-slate-200 hover:bg-white/10',
                      )
                    }
                    onClick={onClose}
                  >
                    <div className="flex items-center gap-2 font-medium">
                      <Icon className="h-4 w-4" />
                      {label}
                    </div>
                    <p className="text-xs text-slate-400">{description}</p>
                  </NavLink>
                  {sections && (
                    <button
                      type="button"
                      className="rounded-full border border-white/20 p-2 text-white hover:border-white/40"
                      onClick={(event) => {
                        event.stopPropagation();
                        setOpenRoute(showSections ? null : path);
                      }}
                      aria-label={`Ouvrir les sous-sections pour ${label}`}
                    >
                      <ChevronDown
                        className={clsx(
                          'h-4 w-4 transition-transform',
                          showSections ? 'rotate-180' : 'rotate-0',
                        )}
                      />
                    </button>
                  )}
                </div>
                {sections && showSections && (
                  <div className="rounded-2xl border border-white/5 bg-white/5 px-4 py-3 text-xs text-slate-200">
                    <ul className="space-y-2">
                      {sections.map((section) => (
                        <li key={section.id}>
                          <NavLink
                            to={`${path}?section=${section.id}`}
                            className="flex flex-col rounded-xl border border-white/0 px-3 py-2 transition hover:border-white/20 hover:bg-white/10"
                            onClick={onClose}
                          >
                            <span className="font-semibold text-white">{section.label}</span>
                            <span className="text-[11px] text-slate-300">{section.description}</span>
                          </NavLink>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        <div className="mt-8 rounded-2xl border border-white/10 bg-gradient-to-r from-brand-500/30 to-slate-900/40 p-4 text-xs text-slate-200">
          <p className="font-semibold text-white">Besoin d'aide ?</p>
          <p className="mt-1">
            Contactez l&apos;équipe opérations pour activer de nouveaux modules ou intégrer vos outils métier.
          </p>
        </div>
      </aside>
    </>
  );
}
