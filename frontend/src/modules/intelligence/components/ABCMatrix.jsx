/**
 * ABCMatrix - Matrice de classification ABC-XYZ
 *
 * Composant du plan de restructuration 2025-12 pour l'Intelligence Module.
 * Visualise la classification des produits selon valeur (ABC) et variabilité (XYZ).
 */

import { useMemo } from 'react';
import { motion } from 'framer-motion';
import clsx from 'clsx';

// ============================================================================
// MATRIX CONFIGURATION
// ============================================================================

const MATRIX_CONFIG = {
  // Colonnes: Classification ABC (valeur)
  columns: [
    { id: 'A', label: 'A - Haute valeur', color: 'emerald', description: '~80% de la valeur' },
    { id: 'B', label: 'B - Valeur moyenne', color: 'blue', description: '~15% de la valeur' },
    { id: 'C', label: 'C - Faible valeur', color: 'slate', description: '~5% de la valeur' },
  ],
  // Lignes: Classification XYZ (variabilité)
  rows: [
    { id: 'X', label: 'X - Stable', color: 'emerald', description: 'Demande prévisible' },
    { id: 'Y', label: 'Y - Variable', color: 'amber', description: 'Demande saisonnière' },
    { id: 'Z', label: 'Z - Erratique', color: 'rose', description: 'Demande imprévisible' },
  ],
};

// Priorités de gestion par cellule
const CELL_PRIORITIES = {
  AX: { priority: 1, strategy: 'JIT', color: 'from-emerald-500/20 to-emerald-600/20', border: 'border-emerald-500/40' },
  AY: { priority: 2, strategy: 'Stock sécurité', color: 'from-emerald-500/15 to-amber-500/15', border: 'border-emerald-500/30' },
  AZ: { priority: 3, strategy: 'Attention critique', color: 'from-emerald-500/10 to-rose-500/10', border: 'border-amber-500/40' },
  BX: { priority: 4, strategy: 'Réapprovisionnement régulier', color: 'from-blue-500/15 to-blue-600/15', border: 'border-blue-500/30' },
  BY: { priority: 5, strategy: 'Stock modéré', color: 'from-blue-500/10 to-amber-500/10', border: 'border-blue-500/20' },
  BZ: { priority: 6, strategy: 'Commandes à la demande', color: 'from-blue-500/10 to-rose-500/10', border: 'border-slate-500/30' },
  CX: { priority: 7, strategy: 'Stock minimum', color: 'from-slate-500/15 to-slate-600/15', border: 'border-slate-500/30' },
  CY: { priority: 8, strategy: 'Réduction stock', color: 'from-slate-500/10 to-amber-500/10', border: 'border-slate-500/20' },
  CZ: { priority: 9, strategy: 'Déréférencement?', color: 'from-slate-500/10 to-rose-500/10', border: 'border-rose-500/30' },
};

// ============================================================================
// MATRIX CELL COMPONENT
// ============================================================================

function MatrixCell({ cellId, items = [], total = 0, onClick, isSelected }) {
  const config = CELL_PRIORITIES[cellId] || {};
  const percentage = total > 0 ? ((items.length / total) * 100).toFixed(1) : 0;

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => onClick?.(cellId, items)}
      className={clsx(
        'relative p-3 rounded-lg cursor-pointer',
        'border transition-all duration-200',
        `bg-gradient-to-br ${config.color}`,
        config.border,
        isSelected && 'ring-2 ring-white/50'
      )}
    >
      {/* Cell ID */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-white/80">{cellId}</span>
        <span className="text-xs px-1.5 py-0.5 rounded bg-black/20 text-white/70">
          P{config.priority}
        </span>
      </div>

      {/* Count */}
      <p className="text-2xl font-bold text-white">{items.length}</p>
      <p className="text-xs text-white/60">{percentage}%</p>

      {/* Strategy tooltip on hover */}
      <div className="mt-2">
        <p className="text-xs text-white/50 truncate" title={config.strategy}>
          {config.strategy}
        </p>
      </div>
    </motion.div>
  );
}

// ============================================================================
// ABC MATRIX COMPONENT
// ============================================================================

export default function ABCMatrix({
  data = [],
  onCellClick,
  selectedCell,
  showLegend = true,
  className,
}) {
  // Grouper les données par cellule
  const groupedData = useMemo(() => {
    const groups = {};
    MATRIX_CONFIG.rows.forEach((row) => {
      MATRIX_CONFIG.columns.forEach((col) => {
        groups[`${col.id}${row.id}`] = [];
      });
    });

    data.forEach((item) => {
      const abc = item.abc_class || item.value_class || 'C';
      const xyz = item.xyz_class || item.variability_class || 'Z';
      const cellId = `${abc}${xyz}`;
      if (groups[cellId]) {
        groups[cellId].push(item);
      }
    });

    return groups;
  }, [data]);

  return (
    <div className={clsx('p-4 rounded-2xl bg-slate-800/50 border border-white/10', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-white">Classification ABC-XYZ</h3>
        <span className="text-sm text-slate-400">{data.length} produits</span>
      </div>

      {/* Matrix Grid */}
      <div className="overflow-x-auto">
        <div className="min-w-[400px]">
          {/* Column Headers */}
          <div className="grid grid-cols-4 gap-2 mb-2">
            <div /> {/* Empty corner */}
            {MATRIX_CONFIG.columns.map((col) => (
              <div key={col.id} className="text-center">
                <span className={clsx('text-xs font-medium', `text-${col.color}-400`)}>
                  {col.id}
                </span>
                <p className="text-xs text-slate-500">{col.description}</p>
              </div>
            ))}
          </div>

          {/* Rows with cells */}
          {MATRIX_CONFIG.rows.map((row) => (
            <div key={row.id} className="grid grid-cols-4 gap-2 mb-2">
              {/* Row Header */}
              <div className="flex flex-col justify-center">
                <span className={clsx('text-xs font-medium', `text-${row.color}-400`)}>
                  {row.id}
                </span>
                <p className="text-xs text-slate-500">{row.description}</p>
              </div>

              {/* Cells */}
              {MATRIX_CONFIG.columns.map((col) => {
                const cellId = `${col.id}${row.id}`;
                return (
                  <MatrixCell
                    key={cellId}
                    cellId={cellId}
                    items={groupedData[cellId]}
                    total={data.length}
                    onClick={onCellClick}
                    isSelected={selectedCell === cellId}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      {showLegend && (
        <div className="mt-4 pt-4 border-t border-white/10">
          <p className="text-xs text-slate-500 mb-2">Priorité de gestion</p>
          <div className="flex flex-wrap gap-2">
            {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((p) => (
              <span
                key={p}
                className={clsx(
                  'text-xs px-2 py-0.5 rounded',
                  p <= 3 && 'bg-emerald-500/20 text-emerald-400',
                  p > 3 && p <= 6 && 'bg-blue-500/20 text-blue-400',
                  p > 6 && 'bg-slate-500/20 text-slate-400'
                )}
              >
                P{p}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Export named
export { MatrixCell, MATRIX_CONFIG, CELL_PRIORITIES };
