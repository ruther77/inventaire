/**
 * BarcodeScannerDemo - Page de démonstration du scanner de code-barres
 *
 * Utilisez cette page pour tester le scanner dans différents modes.
 * Accessible via une route de dev/demo.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ScanBarcode,
  Zap,
  ZapOff,
  Check,
  X,
  Info,
  Settings,
  RotateCw,
} from 'lucide-react';
import BarcodeScannerModal from './BarcodeScannerModal.jsx';
import Button from './Button.jsx';
import Card from './Card.jsx';

export default function BarcodeScannerDemo() {
  const [isScanning, setIsScanning] = useState(false);
  const [scanHistory, setScanHistory] = useState([]);
  const [settings, setSettings] = useState({
    continuous: false,
    autoConfirm: true,
    autoConfirmDelay: 1500,
    showTorchButton: true,
    showCameraSwitch: true,
    formats: null, // null = tous les formats
  });

  const handleBarcodeScanned = (code, format) => {
    const scan = {
      id: Date.now(),
      code,
      format,
      timestamp: new Date(),
    };

    setScanHistory((prev) => [scan, ...prev].slice(0, 50));
    console.log('Code scanné:', code, format);
  };

  const clearHistory = () => {
    setScanHistory([]);
  };

  const formatTimestamp = (date) => {
    return date.toLocaleTimeString('fr-FR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const formatLabels = {
    ean_13: 'EAN-13',
    ean_8: 'EAN-8',
    code_128: 'Code 128',
    code_39: 'Code 39',
    code_93: 'Code 93',
    upc_a: 'UPC-A',
    upc_e: 'UPC-E',
    qr_code: 'QR Code',
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <ScanBarcode className="h-10 w-10 text-blue-400" />
            <h1 className="text-3xl font-bold text-white">
              Scanner de Code-Barres - Démo
            </h1>
          </div>
          <p className="text-slate-400">
            Testez le scanner dans différentes configurations et consultez l'historique
            des scans
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Demo Section */}
          <div className="lg:col-span-2 space-y-6">
            {/* Scanner Card */}
            <Card className="bg-gradient-to-br from-blue-500/20 to-purple-500/20 border-blue-500/30">
              <div className="text-center p-8">
                <div className="w-20 h-20 mx-auto mb-6 bg-blue-500/20 rounded-full flex items-center justify-center">
                  <ScanBarcode className="h-10 w-10 text-blue-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">
                  Prêt à scanner
                </h2>
                <p className="text-slate-300 mb-6">
                  Configuration actuelle:{' '}
                  <span className="font-semibold text-white">
                    {settings.continuous ? 'Mode Continu' : 'Scan Simple'}
                  </span>
                </p>

                <Button
                  variant="brand"
                  size="xl"
                  onClick={() => setIsScanning(true)}
                  className="w-full max-w-md"
                >
                  <ScanBarcode className="h-6 w-6 mr-2" />
                  Ouvrir le Scanner
                </Button>

                <div className="mt-6 flex flex-wrap items-center justify-center gap-3 text-sm text-slate-400">
                  <div className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-400" />
                    EAN-13/8
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-400" />
                    Code 128
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-400" />
                    UPC-A/E
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-400" />
                    QR Code
                  </div>
                </div>
              </div>
            </Card>

            {/* Scan History */}
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <RotateCw className="h-5 w-5" />
                  Historique des scans
                </h3>
                {scanHistory.length > 0 && (
                  <button
                    onClick={clearHistory}
                    className="text-sm text-slate-400 hover:text-white transition-colors"
                  >
                    Effacer
                  </button>
                )}
              </div>

              {scanHistory.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <RotateCw className="h-16 w-16 mx-auto mb-4 opacity-50" />
                  <p>Aucun scan effectué</p>
                  <p className="text-sm mt-2">
                    Les codes scannés apparaîtront ici
                  </p>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {scanHistory.map((scan) => (
                    <motion.div
                      key={scan.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="p-4 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="px-2 py-0.5 text-xs rounded-full bg-blue-500/20 text-blue-400 font-medium">
                              {formatLabels[scan.format] || scan.format}
                            </span>
                            <span className="text-xs text-slate-500">
                              {formatTimestamp(scan.timestamp)}
                            </span>
                          </div>
                          <p className="text-lg font-mono font-semibold text-white">
                            {scan.code}
                          </p>
                        </div>
                        <Check className="h-5 w-5 text-green-400 flex-shrink-0" />
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}

              {scanHistory.length > 0 && (
                <div className="mt-4 pt-4 border-t border-white/10 text-sm text-slate-400">
                  Total: {scanHistory.length} scan{scanHistory.length > 1 ? 's' : ''}
                </div>
              )}
            </Card>
          </div>

          {/* Settings Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <h3 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                <Settings className="h-5 w-5" />
                Configuration
              </h3>

              <div className="space-y-4">
                {/* Continuous Mode */}
                <div>
                  <label className="flex items-center justify-between cursor-pointer">
                    <span className="text-sm text-slate-300">Mode Continu</span>
                    <button
                      onClick={() =>
                        setSettings((s) => ({ ...s, continuous: !s.continuous }))
                      }
                      className={`relative w-12 h-6 rounded-full transition-colors ${
                        settings.continuous
                          ? 'bg-blue-500'
                          : 'bg-slate-700'
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                          settings.continuous ? 'translate-x-6' : ''
                        }`}
                      />
                    </button>
                  </label>
                  <p className="text-xs text-slate-500 mt-1">
                    Scanner en continu sans confirmation
                  </p>
                </div>

                {/* Auto Confirm */}
                <div>
                  <label className="flex items-center justify-between cursor-pointer">
                    <span className="text-sm text-slate-300">
                      Auto-confirmation
                    </span>
                    <button
                      onClick={() =>
                        setSettings((s) => ({ ...s, autoConfirm: !s.autoConfirm }))
                      }
                      className={`relative w-12 h-6 rounded-full transition-colors ${
                        settings.autoConfirm
                          ? 'bg-blue-500'
                          : 'bg-slate-700'
                      }`}
                      disabled={settings.continuous}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                          settings.autoConfirm ? 'translate-x-6' : ''
                        }`}
                      />
                    </button>
                  </label>
                  <p className="text-xs text-slate-500 mt-1">
                    Confirmer automatiquement après détection
                  </p>
                </div>

                {/* Auto Confirm Delay */}
                {settings.autoConfirm && !settings.continuous && (
                  <div>
                    <label className="text-sm text-slate-300 block mb-2">
                      Délai auto-confirmation: {settings.autoConfirmDelay}ms
                    </label>
                    <input
                      type="range"
                      min="500"
                      max="3000"
                      step="500"
                      value={settings.autoConfirmDelay}
                      onChange={(e) =>
                        setSettings((s) => ({
                          ...s,
                          autoConfirmDelay: parseInt(e.target.value),
                        }))
                      }
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-slate-500 mt-1">
                      <span>500ms</span>
                      <span>3000ms</span>
                    </div>
                  </div>
                )}

                {/* Torch Button */}
                <div>
                  <label className="flex items-center justify-between cursor-pointer">
                    <span className="text-sm text-slate-300">
                      Bouton Lampe Torche
                    </span>
                    <button
                      onClick={() =>
                        setSettings((s) => ({
                          ...s,
                          showTorchButton: !s.showTorchButton,
                        }))
                      }
                      className={`relative w-12 h-6 rounded-full transition-colors ${
                        settings.showTorchButton
                          ? 'bg-blue-500'
                          : 'bg-slate-700'
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                          settings.showTorchButton ? 'translate-x-6' : ''
                        }`}
                      />
                    </button>
                  </label>
                </div>

                {/* Camera Switch */}
                <div>
                  <label className="flex items-center justify-between cursor-pointer">
                    <span className="text-sm text-slate-300">
                      Changement Caméra
                    </span>
                    <button
                      onClick={() =>
                        setSettings((s) => ({
                          ...s,
                          showCameraSwitch: !s.showCameraSwitch,
                        }))
                      }
                      className={`relative w-12 h-6 rounded-full transition-colors ${
                        settings.showCameraSwitch
                          ? 'bg-blue-500'
                          : 'bg-slate-700'
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                          settings.showCameraSwitch ? 'translate-x-6' : ''
                        }`}
                      />
                    </button>
                  </label>
                </div>
              </div>
            </Card>

            {/* Info Card */}
            <Card className="bg-blue-500/10 border-blue-500/30">
              <h4 className="font-semibold text-blue-400 mb-3 flex items-center gap-2">
                <Info className="h-4 w-4" />
                Informations
              </h4>
              <ul className="space-y-2 text-sm text-slate-300">
                <li className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <span>
                    Compatible Chrome/Edge Android
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <X className="h-4 w-4 text-rose-400 mt-0.5 flex-shrink-0" />
                  <span>Non supporté sur Safari iOS</span>
                </li>
                <li className="flex items-start gap-2">
                  <Info className="h-4 w-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <span>
                    HTTPS requis pour accès caméra
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <Zap className="h-4 w-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                  <span>
                    Bon éclairage recommandé
                  </span>
                </li>
              </ul>
            </Card>
          </div>
        </div>
      </div>

      {/* Scanner Modal */}
      <BarcodeScannerModal
        isOpen={isScanning}
        onClose={() => setIsScanning(false)}
        onConfirm={handleBarcodeScanned}
        onScan={settings.continuous ? handleBarcodeScanned : undefined}
        title="Scanner - Mode Démo"
        subtitle={
          settings.continuous
            ? 'Mode continu activé'
            : 'Scannez un code-barres'
        }
        continuous={settings.continuous}
        autoConfirm={settings.autoConfirm && !settings.continuous}
        autoConfirmDelay={settings.autoConfirmDelay}
        showTorchButton={settings.showTorchButton}
        showCameraSwitch={settings.showCameraSwitch}
        formats={settings.formats}
      />
    </div>
  );
}
