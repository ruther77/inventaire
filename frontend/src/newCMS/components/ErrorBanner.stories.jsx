import ErrorBanner from './ErrorBanner.jsx';

export default {
  title: 'newCMS/ErrorBanner',
  component: ErrorBanner,
};

export const Default = {
  args: {
    message: "Impossible de charger l'API",
  },
};

export const Dense = {
  args: {
    message: 'Erreur compacte',
    dense: true,
  },
};
