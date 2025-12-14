import StatCard from './StatCard.jsx';
import { DollarSign } from 'lucide-react';

export default {
  title: 'newCMS/StatCard',
  component: StatCard,
};

const Template = (args) => <StatCard {...args} />;

export const Default = Template.bind({});
Default.args = {
  label: 'CA Jour',
  value: '12 450 €',
  trend: 'up',
  trendValue: '+8.2%',
  icon: DollarSign,
};

export const Down = Template.bind({});
Down.args = {
  label: 'Marge',
  value: '34.5%',
  trend: 'down',
  trendValue: '-1.4%',
  icon: DollarSign,
};
