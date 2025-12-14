import { createContext, useContext, useMemo } from 'react';
import { useAuth } from '../hooks/useAuth.js';

// ============================================================================
// APP CONTEXT 2025 - Simplified (no multi-tenant UI)
// ============================================================================

/**
 * Contexte simplifié - L'interface est unifiée mais le backend utilise toujours
 * le concept de tenant pour les données. On utilise 'epicerie' par défaut.
 */

const DEFAULT_TENANT = { id: 1, code: 'epicerie', label: 'Inventaire Pro' };

const DEFAULT_CONTEXT = {
  tenant: DEFAULT_TENANT,
};

const TenantContext = createContext(DEFAULT_CONTEXT);

export function TenantProvider({ children }) {
  const { user } = useAuth();

  // Create a simple context based on user info
  const value = useMemo(() => ({
    tenant: {
      id: user?.tenant_id || DEFAULT_TENANT.id,
      code: user?.tenant_code || DEFAULT_TENANT.code,
      label: user?.tenant_name || DEFAULT_TENANT.label,
    },
    // Keep for backward compatibility
    setTenant: () => {},
    isTenantLocked: true,
    preferredTenant: DEFAULT_TENANT,
  }), [user]);

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  return useContext(TenantContext);
}

// Export for backward compatibility - single tenant now
export const tenants = [DEFAULT_TENANT];
