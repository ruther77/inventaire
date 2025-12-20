/* @refresh reload */
import { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import api, { registerUnauthorizedHandler } from '../api/client.js';

const STORAGE_KEY = 'auth/user';

export const AuthContext = createContext({
  user: null,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
  loading: false,
  error: null,
  clearError: () => {},
});

function readStoredUser() {
  if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
    return null;
  }
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    // On ne stocke plus que les infos user, pas le token
    if (parsed?.id && parsed?.username) {
      return parsed;
    }
  } catch (error) {
    console.warn('Session invalide en cache, purge…', error);
  }
  return null;
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => readStoredUser());
  const [initializing, setInitializing] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handler = () => {
      setUser(null);
      if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
        localStorage.removeItem(STORAGE_KEY);
      }
    };
    registerUnauthorizedHandler(handler);
    return () => registerUnauthorizedHandler(null);
  }, []);

  useEffect(() => {
    // Persister uniquement les infos user (pas de token côté JS)
    if (user) {
      if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
      }
    } else {
      if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    setInitializing(false);
  }, [user]);

  const login = useCallback(async ({ username, password, tenant }) => {
    setLoading(true);
    setError(null);
    try {
      const body = new URLSearchParams();
      body.set('grant_type', 'password');
      body.set('username', username);
      body.set('password', password);
      body.set('tenant', tenant);
      // Utilise /auth/login qui set les cookies HTTP-Only
      const response = await api.post('/auth/login', body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      // API returns: { message, expires_in, user } - pas de token dans la réponse
      const payload = response.data?.data ?? response.data;
      const userInfo = payload.user;
      if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(userInfo));
      }
      setUser(userInfo);
      return payload;
    } catch (authError) {
      const errorData = authError?.response?.data;
      const detail = errorData?.error?.message ?? errorData?.detail ?? 'Authentification impossible';
      setError(detail);
      throw authError;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      // Appel backend pour supprimer les cookies HTTP-Only
      await api.post('/auth/logout');
    } catch (err) {
      console.warn('Erreur lors du logout:', err);
    }
    setUser(null);
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      initializing,
      login,
      logout,
      loading,
      error,
      clearError: () => setError(null),
    }),
    [error, loading, login, logout, user, initializing],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthContext;
