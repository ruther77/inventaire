/**
 * BarcodeScannerQuickTest - Test rapide du scanner
 *
 * Composant minimal pour tester rapidement le scanner.
 * Utilisez-le en l'important dans n'importe quelle page.
 */

import { useState } from 'react';
import BarcodeScannerModal from './BarcodeScannerModal.jsx';

export default function BarcodeScannerQuickTest() {
  const [isOpen, setIsOpen] = useState(false);
  const [lastScan, setLastScan] = useState(null);

  const handleScan = (code, format) => {
    setLastScan({ code, format, time: new Date().toLocaleTimeString() });
    console.log('✅ Scanné:', code, format);
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Bouton flottant */}
      <button
        onClick={() => setIsOpen(true)}
        className="w-14 h-14 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-full shadow-2xl hover:scale-110 transition-transform flex items-center justify-center"
        title="Tester le scanner"
      >
        <svg
          className="w-7 h-7"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"
          />
        </svg>
      </button>

      {/* Dernier scan */}
      {lastScan && (
        <div className="mb-2 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg text-sm">
          <div className="font-bold">{lastScan.code}</div>
          <div className="text-xs opacity-75">
            {lastScan.format} - {lastScan.time}
          </div>
        </div>
      )}

      {/* Scanner Modal */}
      <BarcodeScannerModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        onConfirm={handleScan}
        title="Test Scanner"
        subtitle="Mode test rapide"
        autoConfirm={true}
        autoConfirmDelay={1000}
      />
    </div>
  );
}
