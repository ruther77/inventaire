/**
 * InvoiceLinesEditor - Editeur de lignes de facture
 *
 * Responsabilites:
 * - Affichage des lignes detectees en tableau editable
 * - Edition inline des champs (nom, code, quantite, prix, TVA)
 * - Suppression/duplication de lignes
 * - Calcul des totaux
 */

import { useMemo } from 'react';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import { useLinkInvoiceLine, useCreateProductFromLine } from '../../../hooks/useInvoiceImport.js';
import ProductMatchSuggestions from './ProductMatchSuggestions.jsx';

const numberFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 });

function Metric({ label, value, className }) {
  return (
    <div className={`rounded-2xl border border-slate-200 bg-white p-4 ${className ?? ''}`}>
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</p>
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export default function InvoiceLinesEditor({
  lines,
  onLinesChange,
  onDownloadCsv,
}) {
  const linkMutation = useLinkInvoiceLine();
  const createProductMutation = useCreateProductFromLine();
  // Calcul des totaux
  const totals = useMemo(() => {
    if (!lines.length) {
      return { qty: 0, total: 0, catalog: 0, vat: 0 };
    }
    return lines.reduce(
      (acc, line) => {
        const qty = Number(line.quantite_recue ?? line.qte_init ?? 0);
        const purchase = Number(line.prix_achat ?? 0);
        const amount = purchase * qty;
        const catalogUnit = Number(line.prix_achat_catalogue ?? purchase);
        const vatPct = Number(line.tva ?? 0);
        return {
          qty: acc.qty + qty,
          total: acc.total + amount,
          catalog: acc.catalog + catalogUnit * qty,
          vat: acc.vat + amount * (vatPct / 100),
        };
      },
      { qty: 0, total: 0, catalog: 0, vat: 0 },
    );
  }, [lines]);

  const handleFieldChange = (index, field, value) => {
    const numericFields = ['prix_achat', 'prix_vente', 'tva', 'qte_init', 'quantite_recue', 'produit_id'];
    const nextLines = lines.map((line, idx) =>
      idx === index
        ? {
            ...line,
            [field]: numericFields.includes(field) ? parseFloat(value) || 0 : value,
          }
        : line,
    );
    onLinesChange(nextLines);
  };

  const handleRemoveLine = (index) => {
    onLinesChange(lines.filter((_, idx) => idx !== index));
  };

  const handleDuplicateLine = (index) => {
    const lineToDuplicate = { ...lines[index] };
    const nextLines = [...lines];
    nextLines.splice(index + 1, 0, lineToDuplicate);
    onLinesChange(nextLines);
  };

  const handleClearAll = () => {
    onLinesChange([]);
  };

  return (
    <>
      {/* Metriques */}
      <Card className="flex flex-col gap-4">
        <div className="grid gap-4 md:grid-cols-4">
          <Metric label="Articles analyses" value={lines.length} />
          <Metric label="Unites" value={numberFormatter.format(totals.qty)} />
          <Metric label="Montant HT" value={`${numberFormatter.format(totals.total)} €`} />
          <Metric label="TVA estimee" value={`${numberFormatter.format(totals.vat)} €`} />
          <Metric
            label="Valeur catalogue"
            value={`${numberFormatter.format(totals.catalog)} €`}
            className="md:col-span-2"
          />
          <Metric
            label="Ecart vs catalogue"
            value={`${numberFormatter.format(totals.total - totals.catalog)} €`}
            className="md:col-span-2"
          />
        </div>
        <div className="flex flex-wrap gap-3">
          <Button variant="ghost" size="sm" onClick={onDownloadCsv} disabled={!lines.length}>
            Telecharger la selection
          </Button>
        </div>
      </Card>

      {/* Tableau des lignes */}
      <Card className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">lignes detectees</p>
            <h3 className="text-xl font-semibold text-slate-900">{lines.length} articles</h3>
          </div>
          <div className="flex flex-wrap gap-2 text-sm text-slate-600">
            <p>Unites : {numberFormatter.format(totals.qty)}</p>
            <p>Montant HT : {numberFormatter.format(totals.total)} €</p>
          </div>
          {lines.length > 0 && (
            <Button variant="ghost" size="sm" onClick={handleClearAll}>
              Effacer
            </Button>
          )}
        </div>

        {lines.length === 0 ? (
          <p className="text-sm text-slate-500">Analysez une facture pour afficher les lignes ici.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-widest text-slate-500">
                  <th className="px-3 py-2">Produit</th>
                  <th className="px-3 py-2">EAN</th>
                  <th className="px-3 py-2">Qte</th>
                  <th className="px-3 py-2">Recue</th>
                  <th className="px-3 py-2">Prix achat</th>
                  <th className="px-3 py-2">TVA</th>
                  <th className="px-3 py-2">Produit ID</th>
                  <th className="px-3 py-2 text-right whitespace-nowrap">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {lines.map((line, index) => (
                  <tr key={`${line.nom}-${index}`}>
                    <td className="px-3 py-2">
                      <input
                        type="text"
                        value={line.nom ?? ''}
                        onChange={(e) => handleFieldChange(index, 'nom', e.target.value)}
                        className="w-full rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="text"
                        value={line.codes ?? ''}
                        onChange={(e) => handleFieldChange(index, 'codes', e.target.value)}
                        className="w-full rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        value={line.quantite ?? ''}
                        onChange={(e) => handleFieldChange(index, 'quantite', e.target.value)}
                        className="w-20 rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        value={line.quantite_recue ?? line.qte_init ?? ''}
                        onChange={(e) => handleFieldChange(index, 'quantite_recue', e.target.value)}
                        className="w-20 rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        step="0.01"
                        value={line.prix_achat ?? ''}
                        onChange={(e) => handleFieldChange(index, 'prix_achat', e.target.value)}
                        className="w-24 rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        step="0.01"
                        value={line.tva ?? ''}
                        onChange={(e) => handleFieldChange(index, 'tva', e.target.value)}
                        className="w-16 rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="text"
                        value={line.produit_id ?? ''}
                        onChange={(e) => handleFieldChange(index, 'produit_id', e.target.value)}
                        className="w-20 rounded-xl border border-slate-200 px-3 py-1 focus:border-brand-400 focus:outline-none"
                      />
                    </td>
                    <td className="px-3 py-2 text-right whitespace-nowrap">
                      <div className="flex flex-wrap gap-2 justify-end">
                        {/* Afficher les suggestions de matching si pas de produit_id */}
                        {!line.produit_id && line.nom && (
                          <ProductMatchSuggestions
                            productName={line.nom}
                            onSelectMatch={(suggestion) => {
                              // Lier automatiquement au produit suggéré
                              linkMutation.mutate(
                                { line, productId: suggestion.produit_id },
                                {
                                  onSuccess: (enriched) => {
                                    const next = [...lines];
                                    next[index] = enriched;
                                    onLinesChange(next);
                                  },
                                }
                              );
                            }}
                            onCreateNew={() => {
                              // Créer un nouveau produit
                              createProductMutation.mutate(
                                {
                                  line,
                                  supplier: line.catalogue_nom || line.catalogue_categorie,
                                  initializeStock: true,
                                  invoiceDate: line.facture_date,
                                },
                                {
                                  onSuccess: () => {
                                    const next = [...lines];
                                    next[index] = {
                                      ...line,
                                      produit_id: line.produit_id || line.numero_article || null,
                                    };
                                    onLinesChange(next);
                                  },
                                }
                              );
                            }}
                          />
                        )}
                        <Button
                          variant="outline"
                          size="xs"
                          disabled={linkMutation.isPending || !line.produit_id}
                          onClick={() => {
                            if (!line.produit_id) return;
                            linkMutation.mutate(
                              { line, productId: line.produit_id },
                              {
                                onSuccess: (enriched) => {
                                  const next = [...lines];
                                  next[index] = enriched;
                                  onLinesChange(next);
                                },
                              }
                            );
                          }}
                        >
                          Lier
                        </Button>
                        <Button
                          variant="outline"
                          size="xs"
                          disabled={createProductMutation.isPending}
                          onClick={() => {
                            createProductMutation.mutate(
                              {
                                line,
                                supplier: line.catalogue_nom || line.catalogue_categorie,
                                initializeStock: true,
                                invoiceDate: line.facture_date,
                              },
                              {
                                onSuccess: () => {
                                  const next = [...lines];
                                  next[index] = {
                                    ...line,
                                    produit_id: line.produit_id || line.numero_article || null,
                                  };
                                  onLinesChange(next);
                                },
                              }
                            );
                          }}
                        >
                          Créer
                        </Button>
                        <Button variant="ghost" size="xs" onClick={() => handleDuplicateLine(index)}>
                          Dupliquer
                        </Button>
                        <Button
                          variant="ghost"
                          size="xs"
                          className="text-rose-600"
                          onClick={() => handleRemoveLine(index)}
                        >
                          Supprimer
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
}
