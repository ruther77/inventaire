import DrawerShell from './DrawerShell.jsx';
import EmptyState from './EmptyState.jsx';

export default {
  title: 'newCMS/DrawerShell',
  component: DrawerShell,
};

export const Default = {
  args: {
    open: true,
    title: 'Détail plat',
    children: <EmptyState title="Contenu" description="Placez ici votre fiche technique." />,
    footer: <div className="flex justify-end gap-2"><button className="px-3 py-2 rounded-lg bg-white/10 text-slate-200">Fermer</button><button className="px-3 py-2 rounded-lg bg-blue-500 text-white">Valider</button></div>,
  },
};
