/**
 * BarcodeScannerModal - Modal fullscreen pour le scan de codes-barres
 *
 * Features:
 * - Interface fullscreen optimisée mobile
 * - Header avec titre et bouton fermer
 * - Affichage du dernier code scanné
 * - Boutons d'action: confirmer ou rescanner
 * - Animations d'entrée/sortie fluides
 * - Support des modes continu et single-scan
 * - Callback onConfirm avec le code détecté
 *
 * @example
 * <BarcodeScannerModal
 *   isOpen={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   onConfirm={(code, format) => {
 *     console.log('Confirmed:', code, format);
 *     handleProductSearch(code);
 *   }}
 *   title="Scanner un produit"
 *   continuous={false}
 * />
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Check,
  RotateCcw,
  Barcode,
  QrCode,
  Package,
  ArrowRight,
} from 'lucide-react';
import clsx from 'clsx';
import BarcodeScanner from './BarcodeScanner.jsx';
import Button from './Button.jsx';

// Format icons mapping
const formatIcons = {
  ean_13: Barcode,
  ean_8: Barcode,
  code_128: Barcode,
  code_39: Barcode,
  code_93: Barcode,
  upc_a: Barcode,
  upc_e: Barcode,
  qr_code: QrCode,
};

// Format labels mapping
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

export function BarcodeScannerModal({
  isOpen = false,
  onClose,
  onConfirm,
  onScan,
  title = 'Scanner un code-barres',
  subtitle,
  continuous = false,
  formats,
  confirmButtonText = 'Confirmer',
  cancelButtonText = 'Annuler',
  showTorchButton = true,
  showCameraSwitch = true,
  autoConfirm = false,
  autoConfirmDelay = 1000,
  className,
}) {
  const [scannedCode, setScannedCode] = useState(null);
  const [isConfirming, setIsConfirming] = useState(false);
  const [autoConfirmTimer, setAutoConfirmTimer] = useState(null);

  // Handle code detection
  const handleDetected = (code, format) => {
    const detectedData = { code, format };
    setScannedCode(detectedData);

    // Call onScan callback
    onScan?.(code, format);

    // Auto-confirm if enabled
    if (autoConfirm && !continuous) {
      const timer = setTimeout(() => {
        handleConfirm(detectedData);
      }, autoConfirmDelay);
      setAutoConfirmTimer(timer);
    }
  };

  // Handle confirm
  const handleConfirm = async (codeData = scannedCode) => {
    if (!codeData) return;

    setIsConfirming(true);

    try {
      await onConfirm?.(codeData.code, codeData.format);
      handleClose();
    } catch (err) {
      console.error('Error confirming code:', err);
    } finally {
      setIsConfirming(false);
    }
  };

  // Handle rescan
  const handleRescan = () => {
    if (autoConfirmTimer) {
      clearTimeout(autoConfirmTimer);
      setAutoConfirmTimer(null);
    }
    setScannedCode(null);
  };

  // Handle close
  const handleClose = () => {
    if (autoConfirmTimer) {
      clearTimeout(autoConfirmTimer);
      setAutoConfirmTimer(null);
    }
    setScannedCode(null);
    setIsConfirming(false);
    onClose?.();
  };

  // Cleanup auto-confirm timer on unmount
  useEffect(() => {
    return () => {
      if (autoConfirmTimer) {
        clearTimeout(autoConfirmTimer);
      }
    };
  }, [autoConfirmTimer]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setScannedCode(null);
      setIsConfirming(false);
    }
  }, [isOpen]);

  // Get format icon
  const FormatIcon = scannedCode?.format
    ? formatIcons[scannedCode.format] || Barcode
    : Barcode;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className={clsx('fixed inset-0 z-50 bg-slate-900', className)}
        >
          {/* Header */}
          <motion.div
            initial={{ y: -100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -100, opacity: 0 }}
            transition={{ delay: 0.1 }}
            className="absolute top-0 left-0 right-0 z-30 bg-gradient-to-b from-slate-900 via-slate-900/90 to-transparent"
          >
            <div className="safe-area-inset-top">
              <div className="flex items-center justify-between px-6 py-4">
                <div className="flex-1">
                  <h2 className="text-lg font-semibold text-white">{title}</h2>
                  {subtitle && (
                    <p className="text-sm text-slate-400 mt-0.5">{subtitle}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={handleClose}
                  className="p-2.5 text-white hover:bg-white/10 rounded-xl transition-colors active:scale-95"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
            </div>
          </motion.div>

          {/* Scanner */}
          <div className="w-full h-full">
            <BarcodeScanner
              onDetected={handleDetected}
              continuous={continuous}
              formats={formats}
              showTorchButton={showTorchButton}
              showCameraSwitch={showCameraSwitch}
            />
          </div>

          {/* Detected code panel */}
          <AnimatePresence>
            {scannedCode && !continuous && (
              <motion.div
                initial={{ y: 100, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: 100, opacity: 0 }}
                className="absolute bottom-0 left-0 right-0 z-30 bg-gradient-to-t from-slate-900 via-slate-900 to-transparent"
              >
                <div className="p-6 pb-8 safe-area-inset-bottom">
                  {/* Code info card */}
                  <div className="bg-slate-800/90 backdrop-blur-xl rounded-2xl p-6 mb-4 border border-slate-700/50 shadow-2xl">
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-green-500/20 rounded-xl">
                        <FormatIcon className="h-8 w-8 text-green-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-slate-400 uppercase font-medium tracking-wider mb-1">
                          {formatLabels[scannedCode.format] || scannedCode.format}
                        </p>
                        <p className="text-2xl font-bold text-white font-mono tracking-tight break-all">
                          {scannedCode.code}
                        </p>
                      </div>
                    </div>

                    {/* Auto-confirm countdown */}
                    {autoConfirm && autoConfirmTimer && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="mt-4 pt-4 border-t border-slate-700/50"
                      >
                        <div className="flex items-center gap-2 text-slate-400 text-sm">
                          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                          <span>Confirmation automatique dans {autoConfirmDelay / 1000}s...</span>
                        </div>
                      </motion.div>
                    )}
                  </div>

                  {/* Action buttons */}
                  <div className="flex items-center gap-3">
                    <Button
                      variant="outline"
                      size="lg"
                      onClick={handleRescan}
                      disabled={isConfirming}
                      className="flex-1 bg-slate-800/50 border-slate-700 text-white hover:bg-slate-700/50 backdrop-blur-sm"
                    >
                      <RotateCcw className="h-5 w-5 mr-2" />
                      Rescanner
                    </Button>

                    <Button
                      variant="brand"
                      size="lg"
                      onClick={() => handleConfirm()}
                      loading={isConfirming}
                      disabled={isConfirming}
                      className="flex-1"
                    >
                      {isConfirming ? (
                        'Confirmation...'
                      ) : (
                        <>
                          <Check className="h-5 w-5 mr-2" />
                          {confirmButtonText}
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Continuous mode info */}
          {continuous && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute bottom-6 left-6 right-6 z-20"
            >
              <div className="bg-blue-500/90 backdrop-blur-md text-white px-4 py-3 rounded-xl shadow-lg flex items-center gap-3">
                <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                <p className="text-sm font-medium">
                  Mode continu activé - Les codes sont détectés automatiquement
                </p>
              </div>
            </motion.div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default BarcodeScannerModal;
