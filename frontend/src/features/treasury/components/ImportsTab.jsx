import React, { useState, useCallback } from 'react';
import { Upload, FileText, CheckCircle, XCircle, Clock, RefreshCw } from 'lucide-react';
import Card from '../../../components/ui/Card.jsx';
import Button from '../../../components/ui/Button.jsx';
import Select from '../../../components/ui/Select.jsx';

const STATUS_ICONS = {
  pending: Clock,
  processing: RefreshCw,
  completed: CheckCircle,
  error: XCircle,
};

const STATUS_STYLES = {
  pending: 'text-amber-600 bg-amber-50',
  processing: 'text-blue-600 bg-blue-50',
  completed: 'text-emerald-600 bg-emerald-50',
  error: 'text-rose-600 bg-rose-50',
};

export default function ImportsTab({
  accounts = [],
  imports = [],
  onImport,
  onRefresh,
  isLoading = false,
}) {
  const [selectedAccountId, setSelectedAccountId] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileSelect = useCallback((event) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError('');
      setSuccess('');
    }
  }, []);

  const handleSubmit = async () => {
    if (!selectedAccountId) {
      setError('Sélectionnez un compte bancaire');
      return;
    }
    if (!selectedFile) {
      setError('Sélectionnez un fichier à importer');
      return;
    }

    setError('');
    setSuccess('');

    try {
      const result = await onImport({ accountId: selectedAccountId, file: selectedFile });
      setSuccess(`Import réussi : ${result?.inserted || 0} transactions ajoutées`);
      setSelectedFile(null);
    } catch (err) {
      setError(err.message || "Erreur lors de l'import");
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <Card className="p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-blue-50">
            <Upload className="w-6 h-6 text-blue-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-slate-900">Importer des relevés</h3>
            <p className="text-sm text-slate-500 mt-1">
              Importez vos relevés bancaires au format CSV ou PDF pour alimenter vos transactions.
            </p>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Compte bancaire
                </label>
                <Select
                  value={selectedAccountId}
                  onChange={(e) => setSelectedAccountId(e.target.value)}
                  className="w-full"
                >
                  <option value="">Sélectionner un compte</option>
                  {accounts.map((acc) => (
                    <option key={acc.id} value={acc.id}>
                      {acc.label}
                    </option>
                  ))}
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Fichier
                </label>
                <label className="flex items-center justify-center w-full h-[42px] px-4 border-2 border-dashed border-slate-300 rounded-lg cursor-pointer hover:border-slate-400 transition-colors">
                  <input
                    type="file"
                    accept=".csv,.pdf"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <span className="text-sm text-slate-600">
                    {selectedFile ? selectedFile.name : 'Choisir un fichier (.csv, .pdf)'}
                  </span>
                </label>
              </div>
            </div>

            {error && (
              <div className="mt-4 p-3 rounded-lg bg-rose-50 text-rose-700 text-sm">
                {error}
              </div>
            )}

            {success && (
              <div className="mt-4 p-3 rounded-lg bg-emerald-50 text-emerald-700 text-sm">
                {success}
              </div>
            )}

            <div className="mt-4 flex gap-2">
              <Button
                variant="brand"
                onClick={handleSubmit}
                disabled={isLoading || !selectedAccountId || !selectedFile}
              >
                {isLoading ? 'Import en cours...' : 'Importer'}
              </Button>
              <Button variant="ghost" onClick={onRefresh}>
                Actualiser
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Import History */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-900">Historique des imports</h3>
            <p className="text-sm text-slate-500">Suivez le statut de vos imports</p>
          </div>
          <Button variant="ghost" size="sm" onClick={onRefresh}>
            <RefreshCw className="w-4 h-4 mr-1" />
            Actualiser
          </Button>
        </div>

        <div className="space-y-2">
          {imports.map((imp) => {
            const StatusIcon = STATUS_ICONS[imp.status] || Clock;
            const statusStyle = STATUS_STYLES[imp.status] || STATUS_STYLES.pending;
            return (
              <div
                key={imp.id}
                className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-white"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${statusStyle}`}>
                    <StatusIcon className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {imp.filename || `Import #${imp.id}`}
                    </p>
                    <p className="text-xs text-slate-500">
                      {imp.account_label || `Compte ${imp.account_id}`} • {imp.created_at?.slice(0, 10) || '—'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-slate-900">
                    {imp.inserted ?? 0} lignes
                  </p>
                  <p className="text-xs text-slate-500">
                    {imp.duplicates ? `${imp.duplicates} doublon(s)` : ''}
                  </p>
                </div>
              </div>
            );
          })}

          {imports.length === 0 && (
            <div className="text-center py-8 text-slate-500">
              <FileText className="w-12 h-12 mx-auto mb-2 opacity-30" />
              <p>Aucun import récent</p>
            </div>
          )}
        </div>
      </Card>

      {/* Help */}
      <Card className="p-4 bg-slate-50 border-slate-200">
        <h4 className="text-sm font-semibold text-slate-900 mb-2">Formats supportés</h4>
        <ul className="text-sm text-slate-600 space-y-1">
          <li>• <strong>CSV</strong> : Format standard avec colonnes date, libellé, montant</li>
          <li>• <strong>PDF</strong> : Relevés bancaires (Crédit Agricole, BNP, Société Générale...)</li>
        </ul>
      </Card>
    </div>
  );
}
