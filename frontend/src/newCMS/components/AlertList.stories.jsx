import AlertList from './AlertList.jsx';

export default {
  title: 'newCMS/AlertList',
  component: AlertList,
};

const sample = [
  { id: 'a1', title: 'Rupture tomates', severity: 'critical', message: '2kg restants' },
  { id: 'a2', title: 'Factures en attente', severity: 'warning', message: '3 factures à valider' },
];

export const Default = {
  args: { alerts: sample },
};
