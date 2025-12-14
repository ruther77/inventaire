import { useState, useEffect, useMemo } from 'react';
import { Card, CardHeader, CardContent, Button, Input } from '@/components/ui';
import { Calculator, TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

/**
 * PriceSimulatorPanel - Simulateur de prix pour un plat
 *
 * Props:
 * - platData: {
 *     id, nom, prix_vente_ttc, cout_matiere, marge_brute, marge_pct, food_cost_pct
 *   }
 * - onSimulate: (newPrice, targetMargin) => void
 * - onApply: (newPrice) => Promise<void>
 * - isSimulating: boolean
 */
export default function PriceSimulatorPanel({
  platData = {},
  onSimulate,
  onApply,
  isSimulating = false
}) {
  const { prix_vente_ttc = 0, cout_matiere = 0, marge_pct = 0, food_cost_pct = 0 } = platData;

  const [mode, setMode] = useState('price'); // 'price' | 'margin'
  const [newPrice, setNewPrice] = useState(prix_vente_ttc);
  const [targetMargin, setTargetMargin] = useState(marge_pct);
  const [isApplying, setIsApplying] = useState(false);

  // Mise à jour si platData change
  useEffect(() => {
    setNewPrice(prix_vente_ttc);
    setTargetMargin(marge_pct);
  }, [prix_vente_ttc, marge_pct]);

  // Calculs
  const simulation = useMemo(() => {
    let calculatedPrice = newPrice;
    let calculatedMargin = 0;
    let calculatedFoodCost = 0;
    let calculatedMargeBrute = 0;

    if (mode === 'price') {
      // L'utilisateur a saisi un nouveau prix
      calculatedPrice = parseFloat(newPrice) || 0;
      calculatedMargeBrute = calculatedPrice - cout_matiere;
      calculatedMargin = calculatedPrice > 0 ? (calculatedMargeBrute / calculatedPrice) * 100 : 0;
      calculatedFoodCost = calculatedPrice > 0 ? (cout_matiere / calculatedPrice) * 100 : 0;
    } else {
      // L'utilisateur a saisi une marge cible
      const targetMarginDecimal = parseFloat(targetMargin) / 100 || 0;
      // prix = cout_matiere / (1 - marge_pct)
      calculatedPrice = targetMarginDecimal < 1 ? cout_matiere / (1 - targetMarginDecimal) : 0;
      calculatedMargeBrute = calculatedPrice - cout_matiere;
      calculatedMargin = parseFloat(targetMargin) || 0;
      calculatedFoodCost = calculatedPrice > 0 ? (cout_matiere / calculatedPrice) * 100 : 0;
    }

    return {
      prix: calculatedPrice,
      marge_brute: calculatedMargeBrute,
      marge_pct: calculatedMargin,
      food_cost_pct: calculatedFoodCost,
      evolution_prix: ((calculatedPrice - prix_vente_ttc) / prix_vente_ttc) * 100,
      evolution_marge: calculatedMargin - marge_pct,
      evolution_food_cost: calculatedFoodCost - food_cost_pct,
    };
  }, [mode, newPrice, targetMargin, cout_matiere, prix_vente_ttc, marge_pct, food_cost_pct]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value) => `${value.toFixed(1)}%`;

  const handleApply = async () => {
    if (!onApply) return;
    setIsApplying(true);
    try {
      await onApply(simulation.prix);
    } finally {
      setIsApplying(false);
    }
  };

  const getMarginColor = (value) => {
    if (value > 60) return 'text-emerald-600';
    if (value >= 40) return 'text-amber-600';
    return 'text-rose-600';
  };

  const getFoodCostColor = (value) => {
    if (value < 30) return 'text-emerald-600';
    if (value <= 35) return 'text-amber-600';
    return 'text-rose-600';
  };

  return (
    <Card className="border-blue-200 bg-blue-50/30">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Calculator className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-slate-900">Simulateur de prix</h3>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-6">
          {/* Mode de simulation */}
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-2">Mode de simulation</label>
            <div className="flex gap-2">
              <Button
                variant={mode === 'price' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setMode('price')}
              >
                Nouveau prix
              </Button>
              <Button
                variant={mode === 'margin' ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setMode('margin')}
              >
                Marge cible
              </Button>
            </div>
          </div>

          {/* Input selon le mode */}
          <div>
            {mode === 'price' ? (
              <Input
                label="Nouveau prix de vente TTC"
                type="number"
                step="0.01"
                min="0"
                value={newPrice}
                onChange={(e) => setNewPrice(e.target.value)}
                suffix="€"
              />
            ) : (
              <Input
                label="Marge cible"
                type="number"
                step="0.1"
                min="0"
                max="100"
                value={targetMargin}
                onChange={(e) => setTargetMargin(e.target.value)}
                suffix="%"
              />
            )}
          </div>

          {/* Résultats de simulation */}
          <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-4">
            <h4 className="text-sm font-semibold text-slate-700">Résultat de la simulation</h4>

            {/* Avant / Après */}
            <div className="grid grid-cols-2 gap-4">
              {/* Avant */}
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-wider text-slate-400">Avant</p>
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Prix:</span>
                    <span className="font-semibold text-slate-900">{formatCurrency(prix_vente_ttc)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Marge:</span>
                    <span className={`font-semibold ${getMarginColor(marge_pct)}`}>{formatPercent(marge_pct)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Food Cost:</span>
                    <span className={`font-semibold ${getFoodCostColor(food_cost_pct)}`}>{formatPercent(food_cost_pct)}</span>
                  </div>
                </div>
              </div>

              {/* Après */}
              <div className="space-y-2 border-l-2 border-blue-200 pl-4">
                <p className="text-xs uppercase tracking-wider text-blue-600">Après</p>
                <div className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Prix:</span>
                    <span className="font-semibold text-slate-900">{formatCurrency(simulation.prix)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Marge:</span>
                    <span className={`font-semibold ${getMarginColor(simulation.marge_pct)}`}>
                      {formatPercent(simulation.marge_pct)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Food Cost:</span>
                    <span className={`font-semibold ${getFoodCostColor(simulation.food_cost_pct)}`}>
                      {formatPercent(simulation.food_cost_pct)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Évolutions */}
            <div className="pt-4 border-t border-slate-100 space-y-2">
              <p className="text-xs font-semibold text-slate-700 mb-2">Impact</p>

              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-600">Prix:</span>
                <div className={`flex items-center gap-1 font-semibold ${simulation.evolution_prix > 0 ? 'text-emerald-600' : simulation.evolution_prix < 0 ? 'text-rose-600' : 'text-slate-600'}`}>
                  {simulation.evolution_prix > 0 ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : simulation.evolution_prix < 0 ? (
                    <TrendingDown className="w-3 h-3" />
                  ) : null}
                  <span>{simulation.evolution_prix > 0 ? '+' : ''}{formatPercent(Math.abs(simulation.evolution_prix))}</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-600">Marge:</span>
                <div className={`flex items-center gap-1 font-semibold ${simulation.evolution_marge > 0 ? 'text-emerald-600' : simulation.evolution_marge < 0 ? 'text-rose-600' : 'text-slate-600'}`}>
                  {simulation.evolution_marge > 0 ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : simulation.evolution_marge < 0 ? (
                    <TrendingDown className="w-3 h-3" />
                  ) : null}
                  <span>{simulation.evolution_marge > 0 ? '+' : ''}{formatPercent(Math.abs(simulation.evolution_marge))}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Avertissements */}
          {simulation.marge_pct < 40 && (
            <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-amber-800">
                Attention: La marge est inférieure à 40%. Vérifiez la rentabilité du plat.
              </p>
            </div>
          )}

          {simulation.food_cost_pct > 35 && (
            <div className="flex items-start gap-2 p-3 bg-rose-50 border border-rose-200 rounded-lg">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-rose-800">
                Attention: Le food cost est supérieur à 35%. Risque de rentabilité.
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            <Button
              variant="primary"
              onClick={handleApply}
              disabled={isApplying || !onApply}
              className="flex-1"
            >
              {isApplying ? 'Application...' : 'Appliquer le nouveau prix'}
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setNewPrice(prix_vente_ttc);
                setTargetMargin(marge_pct);
              }}
            >
              Réinitialiser
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
