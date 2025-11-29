import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { useAuth } from '../hooks/useAuth.js';

const STORAGE_KEY = 'tenant/code';
const DEFAULT_TENANT = { id: 1, code: 'epicerie', label: 'Épicerie HQ' };

export const tenants = [
  DEFAULT_TENANT,
  { id: 2, code: 'restaurant', label: 'Restaurant HQ' },
];

const TenantContext = createContext({
  tenant: DEFAULT_TENANT,
  preferredTenant: DEFAULT_TENANT,
  setTenant: () => {},
  isTenantLocked: false,
});

export function TenantProvider({ children }) {
  const { user, isAuthenticated } = useAuth();
  const [preferredCode, setPreferredCode] = useState(() => {
    if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
      return DEFAULT_TENANT.code;
    }
    return localStorage.getItem(STORAGE_KEY) ?? DEFAULT_TENANT.code;
  });

  const sessionTenant = useMemo(() => {
    if (!user) return null;
    return {
      id: user.tenant_id,
      code: user.tenant_code,
      label: user.tenant_name ?? user.tenant_code,
    };
  }, [user]);

  const preferredTenant = useMemo(() => {
    return tenants.find((entry) => entry.code === preferredCode) ?? DEFAULT_TENANT;
  }, [preferredCode]);

  const effectiveTenant = sessionTenant ?? preferredTenant;

  useEffect(() => {
    if (sessionTenant && preferredCode !== sessionTenant.code) {
      setPreferredCode(sessionTenant.code);
    }
  }, [preferredCode, sessionTenant]);

  useEffect(() => {
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, effectiveTenant.code);
    }
  }, [effectiveTenant.code]);

  const value = useMemo(
    () => ({
      tenant: effectiveTenant,
      preferredTenant,
      setTenant: (nextTenant) => {
        if (!nextTenant?.code) return;
        if (isAuthenticated && sessionTenant && sessionTenant.code !== nextTenant.code) {
          // Pendant une session authentifiée, on mémorise juste la préférence pour la prochaine connexion.
          setPreferredCode(nextTenant.code);
          return;
        }
        setPreferredCode(nextTenant.code);
      },
      isTenantLocked: Boolean(sessionTenant),
    }),
    [effectiveTenant, preferredTenant, isAuthenticated, sessionTenant],
  );

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export function useTenant() {
  return useContext(TenantContext);
}
