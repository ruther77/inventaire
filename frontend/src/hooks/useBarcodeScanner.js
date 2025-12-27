/**
 * Module de hooks pour la détection de codes-barres et QR codes via la caméra.
 * @module hooks/useBarcodeScanner
 */

import { useState, useRef, useEffect, useCallback } from 'react';

/**
 * Vérifie si l'API BarcodeDetector est disponible dans le navigateur.
 * @private
 * @returns {boolean} True si supportée
 */
const isBarcodeDetectorSupported = () => {
  return 'BarcodeDetector' in window;
};

/**
 * Formats de codes-barres supportés par défaut.
 * @constant
 * @type {string[]}
 */
const DEFAULT_FORMATS = [
  'ean_13',
  'ean_8',
  'code_128',
  'qr_code',
  'code_39',
  'code_93',
  'upc_a',
  'upc_e',
];

/**
 * Hook pour scanner des codes-barres et QR codes via la BarcodeDetector API.
 *
 * Utilise l'API native BarcodeDetector pour détecter les codes-barres en temps réel
 * depuis un flux vidéo. Supporte de nombreux formats (EAN-13, QR Code, Code128, etc.)
 * et deux modes de scan : continu ou single-shot. Gère automatiquement les permissions
 * caméra et fournit un feedback sonore lors de la détection.
 *
 * IMPORTANT: L'API BarcodeDetector n'est pas disponible sur tous les navigateurs.
 * Vérifiez la propriété `isSupported` avant utilisation.
 *
 * @param {Object} options - Options de configuration
 * @param {Function} [options.onDetected] - Callback appelé lors d'une détection (code, format)
 * @param {Function} [options.onError] - Callback appelé en cas d'erreur
 * @param {boolean} [options.continuous=false] - Mode de scan continu ou single-shot
 * @param {string[]} [options.formats] - Formats à détecter (voir DEFAULT_FORMATS)
 * @param {number} [options.scanInterval=300] - Intervalle entre scans en mode continu (ms)
 * @param {boolean} [options.beepOnDetection=true] - Émettre un bip lors de la détection
 *
 * @returns {Object} État et méthodes du scanner
 * @property {boolean} isScanning - Indique si le scan est en cours
 * @property {Object} detectedCode - Code détecté {code, format, boundingBox}
 * @property {string} error - Message d'erreur éventuel
 * @property {boolean} hasPermission - Permission caméra accordée
 * @property {boolean} isSupported - API BarcodeDetector supportée
 * @property {Function} startScanning - Démarre le scan (videoElement)
 * @property {Function} stopScanning - Arrête le scan
 * @property {Function} resetDetection - Réinitialise l'état de détection
 * @property {Function} manualScan - Effectue un scan manuel
 * @property {Function} checkPermission - Vérifie la permission caméra
 * @property {Function} getSupportedFormats - Liste les formats supportés
 *
 * @example
 * const {
 *   isScanning,
 *   detectedCode,
 *   startScanning,
 *   stopScanning,
 *   isSupported,
 *   error
 * } = useBarcodeScanner({
 *   onDetected: (code, format) => {
 *     console.log(`Code détecté: ${code} (${format})`);
 *     // Rechercher le produit dans la base
 *   },
 *   continuous: false, // Arrêter après la première détection
 *   formats: ['ean_13', 'ean_8', 'qr_code'],
 *   beepOnDetection: true
 * });
 *
 * // Dans le composant
 * const videoRef = useRef();
 * const handleStart = () => startScanning(videoRef.current);
 *
 * if (!isSupported) {
 *   return <div>Votre navigateur ne supporte pas le scan de codes-barres</div>;
 * }
 */
export function useBarcodeScanner({
  onDetected,
  onError,
  continuous = false,
  formats = DEFAULT_FORMATS,
  scanInterval = 300, // ms between scans in continuous mode
  beepOnDetection = true,
} = {}) {
  const [isScanning, setIsScanning] = useState(false);
  const [detectedCode, setDetectedCode] = useState(null);
  const [error, setError] = useState(null);
  const [hasPermission, setHasPermission] = useState(null);
  const [isSupported, setIsSupported] = useState(false);

  const scanIntervalRef = useRef(null);
  const detectorRef = useRef(null);
  const lastDetectedRef = useRef(null);
  const videoRef = useRef(null);

  // Audio beep feedback
  const playBeep = useCallback(() => {
    if (!beepOnDetection) return;

    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);

      oscillator.frequency.value = 1000;
      oscillator.type = 'sine';
      gainNode.gain.value = 0.3;

      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.1);
    } catch (err) {
      console.warn('Could not play beep:', err);
    }
  }, [beepOnDetection]);

  // Check API support on mount
  useEffect(() => {
    const supported = isBarcodeDetectorSupported();
    setIsSupported(supported);

    if (!supported) {
      setError('BarcodeDetector API non disponible sur ce navigateur');
      console.warn('BarcodeDetector API not supported. Consider using a polyfill or alternative library.');
    }
  }, []);

  // Initialize BarcodeDetector
  const initializeDetector = useCallback(async () => {
    if (!isSupported) return false;

    try {
      // Check which formats are actually supported
      const supportedFormats = await window.BarcodeDetector.getSupportedFormats();
      const requestedFormats = formats.filter(format =>
        supportedFormats.includes(format)
      );

      if (requestedFormats.length === 0) {
        throw new Error('Aucun format de code-barres supporté');
      }

      detectorRef.current = new window.BarcodeDetector({
        formats: requestedFormats,
      });

      return true;
    } catch (err) {
      console.error('Failed to initialize BarcodeDetector:', err);
      setError(`Erreur d'initialisation: ${err.message}`);
      return false;
    }
  }, [isSupported, formats]);

  // Scan video frame for barcodes
  const scanFrame = useCallback(async (video) => {
    if (!detectorRef.current || !video || video.readyState !== video.HAVE_ENOUGH_DATA) {
      return;
    }

    try {
      const barcodes = await detectorRef.current.detect(video);

      if (barcodes.length > 0) {
        const barcode = barcodes[0]; // Take first detected barcode
        const code = barcode.rawValue;
        const format = barcode.format;

        // Avoid duplicate detections
        const codeKey = `${code}_${format}`;
        if (lastDetectedRef.current === codeKey) {
          return;
        }

        lastDetectedRef.current = codeKey;

        // Update state
        setDetectedCode({ code, format, boundingBox: barcode.boundingBox });

        // Play feedback
        playBeep();

        // Call callback
        onDetected?.(code, format);

        // Stop scanning if not continuous
        if (!continuous) {
          stopScanning();
        }
      }
    } catch (err) {
      console.error('Error scanning frame:', err);
      // Don't set error state for individual frame failures
    }
  }, [continuous, onDetected, playBeep]);

  // Start continuous scanning
  const startContinuousScanning = useCallback((video) => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
    }

    scanIntervalRef.current = setInterval(() => {
      scanFrame(video);
    }, scanInterval);
  }, [scanFrame, scanInterval]);

  // Start scanning
  const startScanning = useCallback(async (video) => {
    if (!video) {
      setError('Référence vidéo non fournie');
      return false;
    }

    setError(null);
    videoRef.current = video;

    // Initialize detector if not already done
    if (!detectorRef.current) {
      const initialized = await initializeDetector();
      if (!initialized) {
        onError?.('Impossible d\'initialiser le détecteur');
        return false;
      }
    }

    setIsScanning(true);
    lastDetectedRef.current = null;

    // Start continuous scanning
    if (continuous) {
      startContinuousScanning(video);
    } else {
      // Single scan mode - check periodically until detection
      startContinuousScanning(video);
    }

    return true;
  }, [initializeDetector, continuous, startContinuousScanning, onError]);

  // Stop scanning
  const stopScanning = useCallback(() => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    setIsScanning(false);
  }, []);

  // Reset detection state
  const resetDetection = useCallback(() => {
    setDetectedCode(null);
    lastDetectedRef.current = null;
    setError(null);
  }, []);

  // Manual scan (one-shot)
  const manualScan = useCallback(async () => {
    if (videoRef.current) {
      await scanFrame(videoRef.current);
    }
  }, [scanFrame]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopScanning();
    };
  }, [stopScanning]);

  // Check camera permission
  const checkPermission = useCallback(async () => {
    try {
      if (!navigator.permissions) {
        setHasPermission(null);
        return null;
      }

      const result = await navigator.permissions.query({ name: 'camera' });
      setHasPermission(result.state === 'granted');

      result.addEventListener('change', () => {
        setHasPermission(result.state === 'granted');
      });

      return result.state;
    } catch (err) {
      console.warn('Could not check camera permission:', err);
      setHasPermission(null);
      return null;
    }
  }, []);

  // Get supported formats
  const getSupportedFormats = useCallback(async () => {
    if (!isSupported) return [];

    try {
      return await window.BarcodeDetector.getSupportedFormats();
    } catch (err) {
      console.error('Failed to get supported formats:', err);
      return [];
    }
  }, [isSupported]);

  return {
    // State
    isScanning,
    detectedCode,
    error,
    hasPermission,
    isSupported,

    // Actions
    startScanning,
    stopScanning,
    resetDetection,
    manualScan,
    checkPermission,
    getSupportedFormats,
  };
}

export default useBarcodeScanner;
