/**
 * InvoiceImportActions - Actions d'import de facture
 *
 * Responsabilites:
 * - Formulaire de parametres (fournisseur, date, type mouvement, utilisateur)
 * - Bouton import mouvements stock
 * - Bouton import catalogue
 * - Affichage des resultats d'import
 */

import { useState } from 'react';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import {
  useInvoiceImport,
  useInvoiceCatalogImport,
  useInvoiceZeroClick,
  useConfirmInvoiceStock,
} from '../../../hooks/useInvoiceImport.js';
import CardExpandable from '../../../components/ui/CardExpandable.jsx';
import AIConfidenceBadge from '../../../components/ui/AIConfidenceBadge.jsx';

function Metric({ label, value, className }) {
  return (
    <div className={`rounded-2xl border border-slate-200 bg-white p-4 ${className ?? ''}`}>
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</p>
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

const extractErrorMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) return detail.join(', ');
  if (typeof detail === 'string' && detail.trim()) return detail;
  return fallback;
};

export default function InvoiceImportActions({
  lines,
  supplier,
  onSupplierChange,
  invoiceDate,
  onInvoiceDateChange,
  onImportSuccess,
}) {
  const [movementType, setMovementType] = useState('ENTREE');
  const [username, setUsername] = useState('');
  const [initializeStock, setInitializeStock] = useState(false);
  const [summary, setSummary] = useState(null);
  const [catalogSummary, setCatalogSummary] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const importMutation = useInvoiceImport();
  const catalogImportMutation = useInvoiceCatalogImport();
  const zeroClickMutation = useInvoiceZeroClick();
  const confirmStockMutation = useConfirmInvoiceStock();

  const normaliseInvoiceDate = () => (invoiceDate ? invoiceDate : undefined);

  const handleImport = () => {
    if (!lines.length) return;
    setErrorMessage('');
    importMutation.mutate(
      {
        lines,
        supplier,
        movementType,
        username,
        invoiceDate: normaliseInvoiceDate(),
      },
      {
        onSuccess: (data) => {
          setSummary(data);
          setErrorMessage('');
          onImportSuccess?.();
        },
        onError: (error) => setErrorMessage(extractErrorMessage(error, 'Import impossible')),
      },
    );
  };

  const handleCatalogImport = () => {
    if (!lines.length) return;
    setErrorMessage('');
    catalogImportMutation.mutate(
      {
        lines,
        supplier,
        username,
        initializeStock,
        invoiceDate: normaliseInvoiceDate(),
      },
      {
        onSuccess: (data) => {
          setCatalogSummary(data);
          setErrorMessage('');
          onImportSuccess?.();
        },
        onError: (error) => setErrorMessage(extractErrorMessage(error, 'Import catalogue impossible')),
      },
    );
  };

  const isDisabled = !lines.length;

  return (
    <>
      <CardExpandable
        title="Zero-Click (API)"
        subtitle="PDF → Stock + fact_invoices"
        summary="Import auto sans confirmation"
        variant="info"
        defaultExpanded={false}
      >
        <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
          <AIConfidenceBadge confidence={0.9} label="Extract" variant="pill" size="sm" />
          <AIConfidenceBadge confidence={0.85} label="Match catalogue" variant="pill" size="sm" />
          <AIConfidenceBadge confidence={0.8} label="Stock" variant="pill" size="sm" />
          <Button
            size="sm"
            variant="brand"
            disabled={zeroClickMutation.isPending || isDisabled}
            onClick={() => {
              const file = lines?.[0]?.__file;
              if (!file) {
                setErrorMessage("Fichier PDF manquant pour l'import zero-click");
                return;
              }
              zeroClickMutation.mutate({
                file,
                supplierHint: supplier || undefined,
                marginPercent: 40,
                autoConfirm: true,
              });
            }}
          >
            {zeroClickMutation.isPending ? 'Import...' : 'Lancer zero-click'}
          </Button>
        </div>
      </CardExpandable>

      {/* Message d'erreur */}
      {errorMessage && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      )}

      {/* Parametres d'import */}
      <Card className="flex flex-col gap-4">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm text-slate-600">
            Fournisseur
            <input
              type="text"
              value={supplier}
              onChange={(e) => onSupplierChange(e.target.value)}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
              placeholder="Metro, Promocash..."
            />
          </label>
          <label className="text-sm text-slate-600">
            Date facture
            <input
              type="date"
              value={invoiceDate}
              onChange={(e) => onInvoiceDateChange(e.target.value)}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
            />
          </label>
          <label className="text-sm text-slate-600">
            Type de mouvement
            <select
              value={movementType}
              onChange={(e) => setMovementType(e.target.value)}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
            >
              <option value="ENTREE">Entree</option>
              <option value="TRANSFERT">Transfert</option>
            </select>
          </label>
          <label className="text-sm text-slate-600">
            Utilisateur
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 w-full rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
              placeholder="operateur"
            />
          </label>
        </div>

        {/* Bouton import mouvements */}
        <Button
          variant="brand"
          size="lg"
          onClick={handleImport}
          disabled={isDisabled || importMutation.isPending}
        >
          {importMutation.isPending ? 'Import en cours...' : 'Creer les mouvements'}
        </Button>

        <Button
          variant="outline"
          size="lg"
          onClick={() => {
            if (!lines.length) return;
            setErrorMessage('');
            confirmStockMutation.mutate(
              {
                lines,
                supplier,
                movementType,
                invoiceDate: normaliseInvoiceDate(),
                username,
              },
              {
                onSuccess: (data) => {
                  setSummary(data);
                },
                onError: (error) => setErrorMessage(extractErrorMessage(error, 'Validation stock impossible')),
              }
            );
          }}
          disabled={isDisabled || confirmStockMutation.isPending}
        >
          {confirmStockMutation.isPending ? 'Validation...' : 'Valider stock (API)'}
        </Button>

        {/* Resultat import mouvements */}
        {summary && (
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-700">
            <p>Mouvements crees : {summary.movements_created}</p>
            <p>Quantite totale : {summary.quantity_total}</p>
            {summary.errors?.length ? (
              <ul className="mt-2 list-disc pl-4 text-rose-600">
                {summary.errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-emerald-600">Import reussi.</p>
            )}
          </div>
        )}
      </Card>

      {/* Import catalogue */}
      <Card className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-slate-900">Mettre a jour le catalogue</h3>
        <p className="text-sm text-slate-600">
          Ajoute ou met a jour les produits existants, initialise le stock et historise les prix d&apos;achat.
        </p>

        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 text-brand-500 focus:ring-brand-400"
            checked={initializeStock}
            onChange={(e) => setInitializeStock(e.target.checked)}
          />
          Alimenter automatiquement le stock avec les quantites detectees
        </label>

        <Button
          variant="brand"
          onClick={handleCatalogImport}
          disabled={isDisabled || catalogImportMutation.isPending}
        >
          {catalogImportMutation.isPending ? 'Import en cours...' : 'Importer dans le catalogue'}
        </Button>

        {/* Resultat import catalogue */}
        {catalogSummary && (
          <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-700">
            <div className="grid gap-4 md:grid-cols-3">
              <Metric label="Lignes traitees" value={catalogSummary.rows_processed} />
              <Metric label="Creees" value={catalogSummary.created} />
              <Metric label="Mises a jour" value={catalogSummary.updated} />
            </div>
            <div className="mt-3 grid gap-4 md:grid-cols-3">
              <Metric label="Stocks init" value={catalogSummary.stock_initialized} />
              <Metric label="Codes ajoutes" value={catalogSummary.barcode?.added ?? 0} />
              <Metric label="Conflits codes" value={catalogSummary.barcode?.conflicts ?? 0} />
            </div>
            {catalogSummary.errors?.length ? (
              <ul className="mt-3 list-disc pl-5 text-rose-600">
                {catalogSummary.errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-emerald-600">Catalogue synchronise.</p>
            )}
          </div>
        )}
      </Card>
    </>
  );
}
