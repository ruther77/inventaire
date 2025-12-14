import RecommendationCard from './RecommendationCard.jsx';

export default {
  title: 'newCMS/RecommendationCard',
  component: RecommendationCard,
};

export const Default = {
  args: {
    title: 'Optimiser prix huile olive',
    description: 'Baisse de 12% recommandée vs marché',
    impact: '+240 € marge/mois',
    priority: 'high',
    actions: [{ label: 'Appliquer', primary: true }, { label: 'Voir détail' }],
  },
};
