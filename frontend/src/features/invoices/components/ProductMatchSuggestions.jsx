/**
 * ProductMatchSuggestions - Composant de suggestions de matching fuzzy
 *
 * Responsabilités:
 * - Afficher une dropdown avec les suggestions de match fuzzy
 * - Montrer le score de confiance en pourcentage
 * - Permettre de sélectionner un produit existant
 * - Option pour créer un nouveau produit
 */

import { useState, useRef, useEffect } from 'react';
import { useProductMatchSuggestions } from '../../../hooks/useInvoiceImport.js';
import Button from '../../../components/ui/Button.jsx';

export default function ProductMatchSuggestions({
  productName,
  onSelectMatch,
  onCreateNew,
  className = '',
}) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Récupérer les suggestions via le hook
  const { data: suggestions = [], isLoading, isError } = useProductMatchSuggestions(
    productName,
    { enabled: isOpen && Boolean(productName) }
  );

  // Fermer le dropdown si on clique en dehors
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const handleSelectSuggestion = (suggestion) => {
    onSelectMatch(suggestion);
    setIsOpen(false);
  };

  const handleCreateNew = () => {
    onCreateNew();
    setIsOpen(false);
  };

  // Badge de score avec couleur selon la confiance
  const ScoreBadge = ({ score }) => {
    let colorClass = 'bg-slate-100 text-slate-600';
    if (score >= 90) {
      colorClass = 'bg-emerald-100 text-emerald-700';
    } else if (score >= 75) {
      colorClass = 'bg-green-100 text-green-700';
    } else if (score >= 60) {
      colorClass = 'bg-amber-100 text-amber-700';
    }

    return (
      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${colorClass}`}>
        {Math.round(score)}%
      </span>
    );
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Bouton pour ouvrir les suggestions */}
      <Button
        variant="outline"
        size="xs"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1"
      >
        <svg
          className="h-4 w-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        Suggestions
      </Button>

      {/* Dropdown des suggestions */}
      {isOpen && (
        <div className="absolute right-0 z-50 mt-2 w-96 rounded-xl border border-slate-200 bg-white shadow-lg">
          <div className="border-b border-slate-100 px-4 py-3">
            <h4 className="text-sm font-semibold text-slate-900">
              Suggestions de matching
            </h4>
            <p className="text-xs text-slate-500">
              Produits similaires dans le catalogue
            </p>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {isLoading && (
              <div className="px-4 py-8 text-center">
                <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-slate-200 border-t-brand-500"></div>
                <p className="mt-2 text-sm text-slate-500">Recherche en cours...</p>
              </div>
            )}

            {isError && (
              <div className="px-4 py-6 text-center">
                <p className="text-sm text-rose-600">Erreur lors de la recherche</p>
              </div>
            )}

            {!isLoading && !isError && suggestions.length === 0 && (
              <div className="px-4 py-6 text-center">
                <p className="text-sm text-slate-500">Aucune suggestion trouvée</p>
                <p className="mt-1 text-xs text-slate-400">
                  Essayez de créer un nouveau produit
                </p>
              </div>
            )}

            {!isLoading && !isError && suggestions.length > 0 && (
              <div className="divide-y divide-slate-100">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={`${suggestion.produit_id}-${index}`}
                    onClick={() => handleSelectSuggestion(suggestion)}
                    className="w-full px-4 py-3 text-left transition-colors hover:bg-slate-50"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-slate-900 truncate">
                            {suggestion.produit_nom}
                          </p>
                          <ScoreBadge score={suggestion.score} />
                        </div>
                        {suggestion.categorie && (
                          <p className="mt-0.5 text-xs text-slate-500">
                            {suggestion.categorie}
                          </p>
                        )}
                        <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-slate-600">
                          {suggestion.barcode && (
                            <span>EAN: {suggestion.barcode}</span>
                          )}
                          {suggestion.prix_achat > 0 && (
                            <span>Prix achat: {suggestion.prix_achat.toFixed(2)} €</span>
                          )}
                          {suggestion.prix_vente > 0 && (
                            <span>Prix vente: {suggestion.prix_vente.toFixed(2)} €</span>
                          )}
                        </div>
                      </div>
                      <div className="flex-shrink-0">
                        <svg
                          className="h-5 w-5 text-slate-400"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 5l7 7-7 7"
                          />
                        </svg>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer avec option de créer un nouveau produit */}
          <div className="border-t border-slate-100 px-4 py-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCreateNew}
              className="w-full justify-center"
            >
              <svg
                className="mr-2 h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              Créer un nouveau produit
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
