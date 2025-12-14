import AnomalyList from './AnomalyList.jsx';

export default {
  title: 'newCMS/AnomalyList',
  component: AnomalyList,
};

const sample = [
  { id: 'n1', title: 'Prix huile +23%', severity: 'critical', impact: '240€ / mois' },
  { id: 'n2', title: 'Rupture prévue steak', severity: 'warning', impact: 'en 3 jours' },
];

export const Default = {
  args: { anomalies: sample },
};
