/* @refresh reload */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import api, {
  clearAccessToken,
  registerUnauthorizedHandler,
  setAccessToken,
} from '../api/client.js';

const STORAGE_KEY = 'auth/session';

export const AuthContext = createContext({
  user: null,
  token: null,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
  loading: false,
  error: null,
  clearError: () => {},
});

function readStoredSession() {
  if (typeof window === 'undefined' || typeof localStorage === 'undefined') {
    return null;
  }
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw);
    if (parsed?.token && parsed?.user) {
      return parsed;
    }
  } catch (error) {
    console.warn('Session invalide en cache, purge…', error);
  }
  return null;
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => readStoredSession());
  const [initializing, setInitializing] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handler = () => setSession(null);
    registerUnauthorizedHandler(handler);
    return () => registerUnauthorizedHandler(null);
  }, []);

  useEffect(() => {
    if (session?.token) {
      setAccessToken(session.token);
      if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
      }
    } else {
      clearAccessToken();
      if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    setInitializing(false);
  }, [session]);

  const login = useCallback(async ({ username, password, tenant }) => {
    setLoading(true);
    setError(null);
    try {
      const body = new URLSearchParams();
      body.set('grant_type', 'password');
      body.set('username', username);
      body.set('password', password);
      body.set('tenant', tenant);
      const response = await api.post('/auth/token', body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      // API returns wrapped response: { success, data: { access_token, user }, error, meta }
      const payload = response.data?.data ?? response.data;
      const nextSession = { token: payload.access_token, user: payload.user };
      setAccessToken(nextSession.token);
      if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
      }
      setSession(nextSession);
      return payload;
    } catch (authError) {
      // Handle wrapped error response: { success: false, error: { message } }
      const errorData = authError?.response?.data;
      const detail = errorData?.error?.message ?? errorData?.detail ?? 'Authentification impossible';
      setError(detail);
      throw authError;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setSession(null);
    clearAccessToken();
    if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const value = useMemo(
    () => ({
      user: session?.user ?? null,
      token: session?.token ?? null,
      isAuthenticated: Boolean(session?.token),
      initializing,
      login,
      logout,
      loading,
      error,
      clearError: () => setError(null),
    }),
    [error, loading, login, logout, session, initializing],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export default AuthContext;
