import { Package, Edit, Trash2 } from 'lucide-react';
import { SwipeableRow } from '@/components/ui/SwipeableRow.jsx';

/**
 * MobileIngredientRow - Composant optimisé cuisine pour affichage mobile
 *
 * Features:
 * - Swipe actions pour édition rapide
 * - Grands indicateurs de stock (critique/bas/OK)
 * - Touch targets larges (min 48px)
 * - Contraste élevé pour visibilité en cuisine
 */
export default function MobileIngredientRow({
  ingredient,
  onOpenDetail,
  onQuickStockUpdate,
  onDelete,
  formatCurrency,
}) {
  const isCritical = ingredient.stock_min && ingredient.stock_actuel <= ingredient.stock_min;
  const isLow = ingredient.stock_min && ingredient.stock_actuel <= ingredient.stock_min * 1.5 && !isCritical;

  return (
    <SwipeableRow
      id={`ingredient-${ingredient.id}`}
      leftActions={[
        {
          label: 'Modifier stock',
          icon: Package,
          variant: 'primary',
          onAction: () => onQuickStockUpdate(ingredient),
        },
        {
          label: 'Supprimer',
          icon: Trash2,
          variant: 'danger',
          onAction: () => onDelete(ingredient),
        },
      ]}
      rightActions={[
        {
          label: 'Modifier',
          icon: Edit,
          variant: 'primary',
          onAction: () => onOpenDetail(ingredient),
        },
      ]}
      className="mb-2"
    >
      {/* Kitchen-optimized ingredient card with large touch targets */}
      <div
        onClick={() => onOpenDetail(ingredient)}
        className={`
          p-4 rounded-xl bg-slate-800/50 border cursor-pointer
          hover:bg-slate-800/70 active:bg-slate-800/80 transition-all
          ${isCritical ? 'border-rose-500/50 bg-rose-500/5' : isLow ? 'border-amber-500/30 bg-amber-500/5' : 'border-white/10'}
          min-h-[80px] flex items-center
        `}
      >
        <div className="flex items-center gap-4 flex-1">
          {/* Icon */}
          <div className={`
            w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0
            ${isCritical ? 'bg-rose-500/20 border-rose-500/30' : isLow ? 'bg-amber-500/20 border-amber-500/30' : 'bg-gradient-to-br from-teal-500/20 to-cyan-500/20'}
            border
          `}>
            <Package className={`w-6 h-6 ${isCritical ? 'text-rose-400' : isLow ? 'text-amber-400' : 'text-teal-400'}`} />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Name - Bold and large for kitchen visibility */}
            <h3 className="text-lg font-bold text-white truncate mb-1">
              {ingredient.nom}
            </h3>

            {/* Meta info */}
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="text-slate-400">
                {ingredient.categorie || 'Sans catégorie'}
              </span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-400">
                {ingredient.fournisseur || 'Sans fournisseur'}
              </span>
            </div>
          </div>

          {/* Stock and Price - High contrast for kitchen */}
          <div className="flex flex-col items-end gap-2 flex-shrink-0">
            {/* Stock with high visibility */}
            <div className="text-right">
              <p className={`text-xl font-bold ${isCritical ? 'text-rose-400' : isLow ? 'text-amber-400' : 'text-emerald-400'}`}>
                {ingredient.stock_actuel?.toFixed(1) || 0}
              </p>
              <p className="text-xs text-slate-500 uppercase">
                {ingredient.unite_base}
              </p>
            </div>

            {/* Stock status badge */}
            {isCritical && (
              <span className="text-xs px-3 py-1 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/40 font-semibold">
                CRITIQUE
              </span>
            )}
            {isLow && (
              <span className="text-xs px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/40 font-semibold">
                BAS
              </span>
            )}
            {!isCritical && !isLow && ingredient.stock_min && (
              <span className="text-xs px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-semibold">
                OK
              </span>
            )}
          </div>

          {/* Price */}
          <div className="text-right flex-shrink-0 min-w-[80px]">
            <p className="text-base font-bold text-white">
              {formatCurrency(ingredient.cout_unitaire)}
            </p>
            <p className="text-xs text-slate-500">
              / {ingredient.unite_base}
            </p>
          </div>
        </div>
      </div>
    </SwipeableRow>
  );
}
