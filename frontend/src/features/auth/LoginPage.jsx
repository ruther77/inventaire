import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/ui/Button.jsx';
import { tenants, useTenant } from '../../context/TenantContext.jsx';
import { useAuth } from '../../hooks/useAuth.js';

export default function LoginPage() {
  const navigate = useNavigate();
  const { preferredTenant, setTenant } = useTenant();
  const { login, loading, error, clearError, isAuthenticated } = useAuth();
  const [formState, setFormState] = useState({
    username: '',
    password: '',
    tenant: preferredTenant.code,
  });

  useEffect(() => {
    if (preferredTenant.code !== formState.tenant) {
      setFormState((prev) => ({ ...prev, tenant: preferredTenant.code }));
    }
  }, [preferredTenant.code]);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    if (error) clearError();
    setFormState((prev) => ({ ...prev, [name]: value }));
  };

  const handleTenantChange = (event) => {
    const nextCode = event.target.value;
    const nextTenant = tenants.find((entry) => entry.code === nextCode);
    if (nextTenant) {
      setTenant(nextTenant);
      setFormState((prev) => ({ ...prev, tenant: nextCode }));
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (loading) return;
    try {
      await login({
        username: formState.username.trim(),
        password: formState.password,
        tenant: formState.tenant,
      });
      navigate('/', { replace: true });
    } catch (authError) {
      console.warn('Échec de connexion', authError);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 px-4 py-12">
      <div className="w-full max-w-md rounded-3xl bg-white/95 p-8 shadow-2xl shadow-slate-900/40">
        <div className="mb-8 text-center">
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-brand-500">Inventaire HQ</p>
          <h1 className="mt-3 text-2xl font-bold text-slate-900">Connexion sécurisée</h1>
          <p className="mt-2 text-sm text-slate-500">
            Sélectionnez l’entreprise puis identifiez-vous pour accéder aux outils.
          </p>
        </div>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label htmlFor="tenant" className="text-sm font-medium text-slate-700">
              Entreprise
            </label>
            <select
              id="tenant"
              name="tenant"
              value={formState.tenant}
              onChange={handleTenantChange}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-slate-900 focus:border-brand-500 focus:outline-none"
            >
              {tenants.map((entry) => (
                <option key={entry.code} value={entry.code}>
                  {entry.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label htmlFor="username" className="text-sm font-medium text-slate-700">
              Identifiant
            </label>
            <input
              id="username"
              name="username"
              type="text"
              autoComplete="username"
              required
              value={formState.username}
              onChange={handleChange}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-slate-900 focus:border-brand-500 focus:outline-none"
              placeholder="ex: admin"
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium text-slate-700">
              Mot de passe
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={formState.password}
              onChange={handleChange}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-slate-900 focus:border-brand-500 focus:outline-none"
              placeholder="Mot de passe"
            />
          </div>
          {error && (
            <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>
          )}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Connexion…' : 'Se connecter'}
          </Button>
        </form>
        <p className="mt-6 text-center text-xs text-slate-400">
          Rôle appliqué côté API : admin, manager ou standard selon votre profil.
        </p>
      </div>
    </div>
  );
}
