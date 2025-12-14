/**
 * newCMS Demo - Wrapper qui applique la layout et les interactions globales.
 * Navigation pilotée par l'URL (pas de state local) pour refléter l'usage dev.
 */

import { useEffect, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import CMSLayout from './layouts/CMSLayout.jsx';
import { routes } from './routes.jsx';

import CockpitPage from './pages/CockpitPage.jsx';
import OperationsPage from './pages/OperationsPage.jsx';
import FinancePage from './pages/FinancePage.jsx';
import RestaurantPage from './pages/RestaurantPage.jsx';
import IntelligencePage from './pages/IntelligencePage.jsx';
import ConfigPage from './pages/ConfigPage.jsx';
import AlertsCenter from './pages/AlertsCenter.jsx';
import MobileInventoryPage from './pages/MobileInventoryPage.jsx';

const pageMap = {
  '/': CockpitPage,
  '/operations': OperationsPage,
  '/finances': FinancePage,
  '/restaurant': RestaurantPage,
  '/intelligence': IntelligencePage,
  '/config': ConfigPage,
  '/alerts': AlertsCenter,
  '/mobile/inventory': MobileInventoryPage,
};

export default function Demo() {
  const navigate = useNavigate();
  const location = useLocation();

  const basePath = location.pathname.startsWith('/newcms-demo') ? '/newcms-demo' : '/newcms';
  const viewPath = (() => {
    const suffix = location.pathname.slice(basePath.length) || '/';
    return suffix.startsWith('/') ? suffix : `/${suffix}`;
  })();

  const CurrentPageComponent = useMemo(() => pageMap[viewPath] || CockpitPage, [viewPath]);

  useEffect(() => {
    if (!pageMap[viewPath] && viewPath !== '/') {
      navigate(basePath, { replace: true });
    }
  }, [basePath, navigate, viewPath]);

  const handleNavigate = (path) => {
    const target = `${basePath}${path === '/' ? '' : path}`;
    navigate(target);
    if (typeof window !== 'undefined') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <CMSLayout activePath={viewPath} onNavigate={handleNavigate}>
      <CurrentPageComponent />
    </CMSLayout>
  );
}
