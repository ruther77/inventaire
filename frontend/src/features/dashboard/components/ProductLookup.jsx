import { useState, useMemo, useCallback } from 'react';
import { Search, Package, Truck, Euro, Calendar, Barcode, X } from 'lucide-react';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import Input from '../../../components/ui/Input.jsx';
import { Skeleton } from '../../../components/ui/Skeleton.jsx';
import { EmptySearch } from '../../../components/ui/EmptyState.jsx';
import { StatusBadge } from '../../../components/ui/Badge.jsx';

/**
 * ProductLookup - Recherche de produit par code EAN avec validation temps réel
 * Pattern: Real-time validation, debounced search, rich product card
 */
export default function ProductLookup({ onLookup, loading = false }) {
  const [eanSearch, setEanSearch] = useState('');
  const [product, setProduct] = useState(null);
  const [error, setError] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  // Validation temps réel du code EAN
  const validation = useMemo(() => {
    const trimmed = eanSearch.trim();

    if (!trimmed) {
      return { valid: true, message: '' };
    }

    // Vérifier si c'est uniquement des chiffres
    if (!/^\d*$/.test(trimmed)) {
      return { valid: false, message: 'Le code EAN ne doit contenir que des chiffres' };
    }

    // Vérifier la longueur
    if (trimmed.length < 8) {
      return { valid: false, message: `Encore ${8 - trimmed.length} chiffre(s) minimum` };
    }

    if (trimmed.length > 14) {
      return { valid: false, message: 'Le code EAN ne peut pas dépasser 14 chiffres' };
    }

    // Longueurs valides: 8 (EAN-8), 12 (UPC-A), 13 (EAN-13), 14 (GTIN-14)
    if (![8, 12, 13, 14].includes(trimmed.length)) {
      return {
        valid: true,
        message: `Format inhabituel (${trimmed.length} chiffres)`,
        warning: true
      };
    }

    return { valid: true, message: 'Format valide', success: true };
  }, [eanSearch]);

  const canSearch = eanSearch.trim().length >= 8 && validation.valid && !loading;

  const handleSearch = useCallback(async () => {
    if (!canSearch) return;

    setError('');
    setHasSearched(true);

    try {
      const result = await onLookup(eanSearch.trim());
      if (result) {
        setProduct(result);
      } else {
        setProduct(null);
        setError('Produit introuvable dans la base de données');
      }
    } catch (err) {
      setProduct(null);
      setError('Erreur lors de la recherche. Veuillez réessayer.');
    }
  }, [canSearch, eanSearch, onLookup]);

  const handleClear = () => {
    setEanSearch('');
    setProduct(null);
    setError('');
    setHasSearched(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && canSearch) {
      handleSearch();
    }
    if (e.key === 'Escape') {
      handleClear();
    }
  };

  return (
    <Card className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <p className="text-xs uppercase tracking-[0.4em] text-slate-400">
          Fiches produit
        </p>
        <h3 className="text-lg font-semibold text-slate-900">
          Recherche par code EAN
        </h3>
        <p className="text-sm text-slate-500 mt-1">
          Identifiez rapidement un produit et consultez ses informations.
        </p>
      </div>

      {/* Search form */}
      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="flex-1">
          <Input
            label="Code EAN"
            value={eanSearch}
            onChange={(e) => setEanSearch(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ex. 5411188114526"
            icon={Barcode}
            error={!validation.valid ? validation.message : undefined}
            hint={validation.valid && validation.message ? validation.message : undefined}
            success={validation.success}
            autoComplete="off"
            inputMode="numeric"
          />
        </div>
        <div className="flex gap-2 sm:self-start sm:mt-6">
          <Button
            variant="brand"
            onClick={handleSearch}
            disabled={!canSearch}
            loading={loading}
          >
            <Search className="h-4 w-4" />
            Rechercher
          </Button>
          {(eanSearch || product) && (
            <Button
              variant="ghost"
              onClick={handleClear}
              title="Effacer"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Results */}
      {loading && <ProductCardSkeleton />}

      {!loading && error && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      {!loading && !error && !product && hasSearched && (
        <EmptySearch onReset={handleClear} />
      )}

      {!loading && !error && !product && !hasSearched && (
        <div className="text-center py-8 text-slate-500">
          <Barcode className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">
            Saisissez un code EAN pour afficher la fiche produit
          </p>
        </div>
      )}

      {!loading && product && (
        <ProductCard product={product} />
      )}
    </Card>
  );
}

/**
 * ProductCard - Carte détaillée d'un produit
 */
function ProductCard({ product }) {
  const stockStatus = useMemo(() => {
    const stock = product.stock_actuel ?? 0;
    const threshold = product.seuil_alerte ?? 8;

    if (stock === 0) return 'critical';
    if (stock < threshold) return 'low';
    return 'ok';
  }, [product]);

  return (
    <div className="grid gap-6 md:grid-cols-3 animate-in slide-in-from-bottom duration-300">
      {/* Image */}
      <div className="md:col-span-1">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={`Visuel ${product.nom ?? ''}`}
            className="w-full aspect-square object-cover rounded-2xl border border-slate-200"
            loading="lazy"
          />
        ) : (
          <div className="w-full aspect-square flex items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50">
            <Package className="h-16 w-16 text-slate-300" />
          </div>
        )}
      </div>

      {/* Details */}
      <div className="md:col-span-2 space-y-4">
        {/* Header */}
        <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
                Produit
              </p>
              <h4 className="text-lg font-semibold text-slate-900">
                {product.nom ?? '—'}
              </h4>
              <p className="text-sm text-slate-500 mt-1">
                {product.categorie ?? 'Catégorie non renseignée'}
              </p>
            </div>
            <StatusBadge status={stockStatus} />
          </div>
        </div>

        {/* Info grid */}
        <div className="grid gap-3 sm:grid-cols-2">
          <InfoCard
            icon={Truck}
            label="Fournisseur"
            value={product.fournisseur ?? '—'}
          />
          <InfoCard
            icon={Package}
            label="Stock actuel"
            value={`${Number(product.stock_actuel ?? 0).toLocaleString('fr-FR')} unités`}
            highlight={stockStatus !== 'ok'}
          />
          <InfoCard
            icon={Euro}
            label="Prix d'achat"
            value={product.prix_achat ? `${product.prix_achat} €` : '—'}
          />
          <InfoCard
            icon={Calendar}
            label="Dernière MAJ"
            value={product.updated_at ? formatDate(product.updated_at) : '—'}
          />
        </div>

        {/* Codes associés */}
        {Array.isArray(product.codes) && product.codes.length > 0 && (
          <div className="rounded-2xl border border-slate-100 px-4 py-3">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400 mb-2">
              Codes associés
            </p>
            <div className="flex flex-wrap gap-2">
              {product.codes.map((code, i) => (
                <span
                  key={i}
                  className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-1 text-xs font-mono text-slate-700"
                >
                  {code}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * InfoCard - Carte d'information compacte
 */
function InfoCard({ icon: Icon, label, value, highlight }) {
  return (
    <div className="rounded-2xl border border-slate-100 px-4 py-3">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="h-3.5 w-3.5 text-slate-400" />
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">
          {label}
        </p>
      </div>
      <p className={`text-sm font-semibold ${highlight ? 'text-amber-600' : 'text-slate-900'}`}>
        {value}
      </p>
    </div>
  );
}

/**
 * ProductCardSkeleton - Skeleton de la carte produit
 */
function ProductCardSkeleton() {
  return (
    <div className="grid gap-6 md:grid-cols-3">
      <Skeleton className="aspect-square rounded-2xl" />
      <div className="md:col-span-2 space-y-4">
        <Skeleton className="h-24 rounded-2xl" />
        <div className="grid gap-3 sm:grid-cols-2">
          <Skeleton className="h-16 rounded-2xl" />
          <Skeleton className="h-16 rounded-2xl" />
          <Skeleton className="h-16 rounded-2xl" />
          <Skeleton className="h-16 rounded-2xl" />
        </div>
      </div>
    </div>
  );
}

function formatDate(dateString) {
  try {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateString;
  }
}
