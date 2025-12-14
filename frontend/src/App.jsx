import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import AppShell from './app/AppShell.jsx';
import { allRoutes } from './app/routes.jsx';
import { useAuth } from './hooks/useAuth.js';
import LoginPage from './features/auth/LoginPage.jsx';
import ErrorBoundary from './components/feedback/ErrorBoundary.jsx';

// newCMS Demo - Plein écran (hors AppShell)
const NewCMSDemo = lazy(() => import('@/newCMS/Demo.jsx'));

// ============================================================================
// APP 2025 - Unified Application Router
// ============================================================================

/**
 * Application unifiée avec une seule structure de navigation.
 * Plus de système multi-tenant - une seule interface cohérente
 * avec accès à toutes les fonctionnalités.
 *
 * Structure:
 * - Login → Cockpit (Vue 360°)
 * - Cockpit → Opérations / Finances / Restaurant / Intelligence / Paramètres
 */

export default function App() {
  const { isAuthenticated, initializing } = useAuth();

  // Protected route wrapper
  const ProtectedRoute = ({ children }) => {
    if (initializing) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-full border-2 border-blue-500/20 border-t-blue-500 animate-spin" />
              <div
                className="absolute inset-0 w-16 h-16 rounded-full border-2 border-purple-500/20 border-b-purple-500 animate-spin"
                style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}
              />
            </div>
            <p className="text-sm text-slate-500 animate-pulse">Chargement...</p>
          </div>
        </div>
      );
    }

    if (!isAuthenticated) {
      return <Navigate to="/login" replace />;
    }

    return children;
  };

  return (
    <ErrorBoundary level="page">
      <Routes>
        {/* Public route - Login */}
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />}
        />

        {/* newCMS Demo - Plein écran (hors AppShell) */}
        <Route
          path="/newcms-demo/*"
          element={
            <Suspense fallback={<div className="min-h-screen bg-slate-950 flex items-center justify-center"><div className="text-white">Chargement...</div></div>}>
              <NewCMSDemo />
            </Suspense>
          }
        />
        {/* Alias /newcms vers la démo newCMS */}
        <Route
          path="/newcms/*"
          element={
            <Suspense fallback={<div className="min-h-screen bg-slate-950 flex items-center justify-center"><div className="text-white">Chargement...</div></div>}>
              <NewCMSDemo />
            </Suspense>
          }
        />

        {/* Protected routes - All inside AppShell */}
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <ErrorBoundary level="section">
                <AppShell />
              </ErrorBoundary>
            </ProtectedRoute>
          }
        >
          {/* Map all routes from the unified route structure */}
          {allRoutes.map(({ path, element }) => {
            // Handle root path specially
            const routePath = path === '/' ? '' : path.replace(/^\//, '');
            return (
              <Route
                key={path}
                path={routePath}
                element={element}
                index={path === '/'}
              />
            );
          })}

          {/* Fallback - redirect to Cockpit */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
}
