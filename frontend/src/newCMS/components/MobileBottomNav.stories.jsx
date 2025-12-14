import MobileBottomNav from './MobileBottomNav.jsx';

export default {
  title: 'newCMS/MobileBottomNav',
  component: MobileBottomNav,
};

export const Default = {
  args: {
    items: [
      { icon: '🎯', label: 'Cockpit', active: true },
      { icon: '📦', label: 'Ops' },
      { icon: '💰', label: 'Finance' },
    ],
  },
};
