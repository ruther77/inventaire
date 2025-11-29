import { Navigate, Route, Routes } from 'react-router-dom';
import AppShell from './app/AppShell.jsx';
import RestaurantAppShell from './app/RestaurantAppShell.jsx';
import { epicerieRoutes, restaurantRoutes } from './app/routes.jsx';
import { useTenant } from './context/TenantContext.jsx';
import { useAuth } from './hooks/useAuth.js';
import LoginPage from './features/auth/LoginPage.jsx';

/**
 * App orchestre les routes selon le tenant sélectionné (épicerie vs restaurant).
 * Chaque tenant dispose d'un jeu de routes spécifiques et d'un shell dédié,
 * ce qui permet de conserver deux interfaces métiers distinctes tout en
 * partageant la même base de composants.
 */
export default function App() {
  const { tenant } = useTenant();
  const { isAuthenticated, initializing } = useAuth();
  const activeRoutes = tenant.code === 'restaurant' ? restaurantRoutes : epicerieRoutes;
  const Shell = tenant.code === 'restaurant' ? RestaurantAppShell : AppShell;

  const ProtectedShell = () => {
    if (initializing) {
      return null;
    }
    if (!isAuthenticated) {
      return <Navigate to="/login" replace />;
    }
    return <Shell routes={activeRoutes} />;
  };

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
      />
      <Route path="/*" element={<ProtectedShell />}>
        {activeRoutes.map(({ path, element }) => {
          const normalizedPath = path === '/' ? '' : path.replace(/^\//, '');
          return <Route key={path} path={normalizedPath} element={element} />;
        })}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
