import ActionableCard from './ActionableCard.jsx';

export default {
  title: 'newCMS/ActionableCard',
  component: ActionableCard,
};

export const Default = {
  render: () => (
    <ActionableCard
      title="Rapprocher 12 transactions"
      description="67 suggestions IA disponibles"
      actions={[
        <button key="1" className="px-3 py-2 rounded-lg bg-blue-500 text-white text-sm">Ouvrir</button>,
      ]}
    />
  ),
};
