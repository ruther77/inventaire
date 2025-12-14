import TabNav from './TabNav.jsx';
import { Gauge, Wallet, Utensils } from 'lucide-react';

export default {
  title: 'newCMS/TabNav',
  component: TabNav,
};

export const Default = {
  render: () => (
    <TabNav
      tabs={[
        { id: 'cockpit', label: 'Cockpit', icon: <Gauge className="w-4 h-4" /> },
        { id: 'finance', label: 'Finance', icon: <Wallet className="w-4 h-4" /> },
        { id: 'restaurant', label: 'Restaurant', icon: <Utensils className="w-4 h-4" /> },
      ]}
      active="cockpit"
      onChange={() => {}}
    />
  ),
};
