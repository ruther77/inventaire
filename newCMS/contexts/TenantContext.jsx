import { createContext, useContext, useMemo, useState } from 'react';

const TenantContext = createContext(null);

const DEFAULT_TENANTS = [
  { id: 1, name: 'Épicerie', slug: 'epicerie', color: 'emerald' },
  { id: 2, name: 'Restaurant', slug: 'restaurant', color: 'orange' },
  { id: 3, name: 'Intelligence', slug: 'intelligence', color: 'pink' },
];

export function TenantProvider({ children, initialTenantId = 2 }) {
  const [tenants] = useState(DEFAULT_TENANTS);
  const [activeTenantId, setActiveTenantId] = useState(initialTenantId);

  const value = useMemo(() => {
    const activeTenant = tenants.find((t) => t.id === activeTenantId) || tenants[0];

    return {
      tenants,
      activeTenant,
      activeTenantId,
      switchTenant: setActiveTenantId,
    };
  }, [activeTenantId, tenants]);

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export function useTenant() {
  const ctx = useContext(TenantContext);
  if (!ctx) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  return ctx;
}
