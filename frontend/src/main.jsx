import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App.jsx';
import './styles.css';
import { TenantProvider } from './context/TenantContext.jsx';
import { AuthProvider } from './context/AuthContext.jsx';

const queryClient = new QueryClient();

/**
 * Point d'entrée React : on enveloppe toute l'application avec le client
 * TanStack Query (cache des requêtes HTTP) et le TenantProvider qui expose
 * l’entreprise active (épicerie vs restaurant).
 */
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <TenantProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </TenantProvider>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
