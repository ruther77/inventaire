import Card from './Card.jsx';

export default {
  title: 'UI/Card',
  component: Card,
  parameters: {
    layout: 'centered',
  },
};

export const Default = {
  args: {
    children: (
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Exemple</p>
        <p className="text-lg font-semibold text-slate-900">Carte générique</p>
        <p className="text-sm text-slate-500">Utilisée pour structurer les modules HQ.</p>
      </div>
    ),
  },
};
