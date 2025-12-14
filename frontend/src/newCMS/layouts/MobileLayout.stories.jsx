import MobileLayout from './MobileLayout.jsx';
import EmptyState from '../components/EmptyState.jsx';

export default {
  title: 'newCMS/Layout/MobileLayout',
  component: MobileLayout,
};

export const Default = {
  render: () => (
    <MobileLayout
      header={<div className="p-4 text-white bg-slate-900/80 border-b border-white/10">Header mobile</div>}
      navItems={[
        { icon: '🎯', label: 'Cockpit', active: true },
        { icon: '📦', label: 'Ops' },
        { icon: '💰', label: 'Finance' },
      ]}
    >
      <div className="p-4">
        <EmptyState title="Contenu mobile" description="Placez ici la page." />
      </div>
    </MobileLayout>
  ),
};
