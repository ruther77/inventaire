/**
 * BarcodeScanner - Composant de scan de codes-barres via la caméra mobile
 *
 * Features:
 * - Accès à la caméra arrière (facingMode: environment)
 * - Détection en temps réel via BarcodeDetector API
 * - Support des formats: EAN-13, EAN-8, Code128, QR Code, etc.
 * - Overlay visuel avec zone de scan animée
 * - Feedback visuel et sonore lors de la détection
 * - Bouton lampe torche (si disponible)
 * - Gestion des permissions caméra
 * - Mode continu ou single-scan
 *
 * @example
 * <BarcodeScanner
 *   onDetected={(code, format) => console.log('Scanned:', code, format)}
 *   continuous={false}
 *   showTorchButton={true}
 * />
 */

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Camera,
  Zap,
  ZapOff,
  FlipHorizontal,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Info,
} from 'lucide-react';
import clsx from 'clsx';
import useBarcodeScanner from '../../hooks/useBarcodeScanner.js';

export function BarcodeScanner({
  onDetected,
  onError,
  continuous = false,
  formats,
  facingMode = 'environment',
  showTorchButton = true,
  showCameraSwitch = true,
  className,
}) {
  const [stream, setStream] = useState(null);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const [currentFacingMode, setCurrentFacingMode] = useState(facingMode);
  const [torchEnabled, setTorchEnabled] = useState(false);
  const [torchSupported, setTorchSupported] = useState(false);
  const [supportsCameraSwitch, setSupportsCameraSwitch] = useState(false);

  const videoRef = useRef(null);
  const scanLineRef = useRef(null);

  const {
    isScanning,
    detectedCode,
    error: scanError,
    isSupported,
    startScanning,
    stopScanning,
    resetDetection,
    checkPermission,
  } = useBarcodeScanner({
    onDetected: (code, format) => {
      onDetected?.(code, format);
    },
    onError: (err) => {
      onError?.(err);
    },
    continuous,
    formats,
    beepOnDetection: true,
  });

  // Check if device supports camera switching
  useEffect(() => {
    if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
      navigator.mediaDevices.enumerateDevices().then((devices) => {
        const videoDevices = devices.filter((device) => device.kind === 'videoinput');
        setSupportsCameraSwitch(videoDevices.length > 1);
      });
    }
  }, []);

  // Start camera
  const startCamera = async () => {
    try {
      setCameraError(null);

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Votre navigateur ne supporte pas l'accès à la caméra");
      }

      const constraints = {
        video: {
          facingMode: currentFacingMode,
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      };

      const mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
      setStream(mediaStream);

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        await videoRef.current.play();
        setIsCameraActive(true);

        // Check torch support
        const track = mediaStream.getVideoTracks()[0];
        const capabilities = track.getCapabilities?.();
        setTorchSupported(capabilities?.torch === true);

        // Start barcode scanning
        await startScanning(videoRef.current);
      }
    } catch (err) {
      console.error('Error starting camera:', err);
      setCameraError(
        err.name === 'NotAllowedError'
          ? "Accès à la caméra refusé. Veuillez autoriser l'accès dans les paramètres."
          : err.name === 'NotFoundError'
          ? "Aucune caméra trouvée sur cet appareil."
          : "Impossible d'accéder à la caméra. Vérifiez vos permissions."
      );
      onError?.(err.message);
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
      setIsCameraActive(false);
      setTorchEnabled(false);
    }
    stopScanning();
  };

  // Toggle torch
  const toggleTorch = async () => {
    if (!stream || !torchSupported) return;

    try {
      const track = stream.getVideoTracks()[0];
      const newTorchState = !torchEnabled;

      await track.applyConstraints({
        advanced: [{ torch: newTorchState }],
      });

      setTorchEnabled(newTorchState);
    } catch (err) {
      console.error('Error toggling torch:', err);
    }
  };

  // Switch camera (front/back)
  const switchCamera = () => {
    stopCamera();
    setCurrentFacingMode((prev) => (prev === 'user' ? 'environment' : 'user'));
  };

  // Restart camera when facing mode changes
  useEffect(() => {
    if (isCameraActive) {
      startCamera();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentFacingMode]);

  // Auto-start camera on mount
  useEffect(() => {
    checkPermission();
    startCamera();

    return () => {
      stopCamera();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Combined error message
  const errorMessage = cameraError || scanError;

  return (
    <div className={clsx('relative w-full h-full bg-slate-900 overflow-hidden', className)}>
      {/* Video stream */}
      {isCameraActive ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="absolute inset-0 w-full h-full object-cover"
        />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center p-8">
            {errorMessage ? (
              <>
                <AlertCircle className="h-16 w-16 text-rose-400 mx-auto mb-4" />
                <p className="text-slate-300 mb-4">{errorMessage}</p>
                <button
                  type="button"
                  onClick={startCamera}
                  className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Réessayer
                </button>
              </>
            ) : (
              <>
                <Loader2 className="h-16 w-16 text-slate-400 mx-auto mb-4 animate-spin" />
                <p className="text-slate-300">Démarrage de la caméra...</p>
              </>
            )}
          </div>
        </div>
      )}

      {/* Scanning overlay */}
      {isCameraActive && (
        <>
          {/* Scan zone overlay */}
          <div className="absolute inset-0 pointer-events-none">
            {/* Darkened corners */}
            <svg className="absolute inset-0 w-full h-full">
              <defs>
                <mask id="scan-mask">
                  <rect width="100%" height="100%" fill="white" />
                  <rect
                    x="10%"
                    y="30%"
                    width="80%"
                    height="40%"
                    rx="12"
                    fill="black"
                  />
                </mask>
              </defs>
              <rect
                width="100%"
                height="100%"
                fill="rgba(0, 0, 0, 0.5)"
                mask="url(#scan-mask)"
              />
            </svg>

            {/* Scan frame */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="relative w-4/5 h-2/5">
                {/* Frame corners */}
                <div className="absolute top-0 left-0 w-8 h-8 border-l-4 border-t-4 border-blue-400 rounded-tl-xl" />
                <div className="absolute top-0 right-0 w-8 h-8 border-r-4 border-t-4 border-blue-400 rounded-tr-xl" />
                <div className="absolute bottom-0 left-0 w-8 h-8 border-l-4 border-b-4 border-blue-400 rounded-bl-xl" />
                <div className="absolute bottom-0 right-0 w-8 h-8 border-r-4 border-b-4 border-blue-400 rounded-br-xl" />

                {/* Animated scan line */}
                <motion.div
                  ref={scanLineRef}
                  className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-blue-400 to-transparent shadow-lg shadow-blue-400/50"
                  animate={{
                    top: ['0%', '100%'],
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: 'linear',
                  }}
                />

                {/* Center aim point */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full shadow-lg shadow-blue-400/50" />
                </div>
              </div>
            </div>

            {/* Instruction text */}
            {!detectedCode && (
              <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-12 text-center">
                <p className="text-white text-sm font-medium bg-slate-900/80 px-4 py-2 rounded-lg backdrop-blur-sm">
                  Placez le code-barres dans le cadre
                </p>
              </div>
            )}
          </div>

          {/* Detection feedback */}
          <AnimatePresence>
            {detectedCode && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.8, y: -20 }}
                className="absolute top-24 left-1/2 -translate-x-1/2 z-20"
              >
                <div className="bg-green-500 text-white px-6 py-4 rounded-xl shadow-2xl shadow-green-500/50 flex items-center gap-3">
                  <CheckCircle2 className="h-6 w-6" />
                  <div>
                    <p className="font-semibold">Code détecté!</p>
                    <p className="text-sm text-green-100">
                      {detectedCode.code} ({detectedCode.format})
                    </p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* API Support warning */}
          {!isSupported && (
            <div className="absolute top-4 left-4 right-4 z-20 bg-amber-500/90 text-white p-4 rounded-lg shadow-lg flex items-start gap-3 backdrop-blur-sm">
              <Info className="h-5 w-5 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">API non disponible</p>
                <p className="text-sm">
                  BarcodeDetector API n'est pas supporté par ce navigateur. Utilisez Chrome ou Edge pour Android.
                </p>
              </div>
            </div>
          )}

          {/* Camera controls */}
          <div className="absolute bottom-6 left-0 right-0 z-20 flex items-center justify-center gap-4 px-6">
            {/* Torch toggle */}
            {showTorchButton && torchSupported && (
              <motion.button
                whileTap={{ scale: 0.95 }}
                type="button"
                onClick={toggleTorch}
                className={clsx(
                  'p-4 rounded-full backdrop-blur-md transition-colors shadow-lg',
                  torchEnabled
                    ? 'bg-yellow-500 text-white shadow-yellow-500/50'
                    : 'bg-white/20 text-white hover:bg-white/30'
                )}
              >
                {torchEnabled ? (
                  <Zap className="h-6 w-6" />
                ) : (
                  <ZapOff className="h-6 w-6" />
                )}
              </motion.button>
            )}

            {/* Camera switch */}
            {showCameraSwitch && supportsCameraSwitch && (
              <motion.button
                whileTap={{ scale: 0.95 }}
                type="button"
                onClick={switchCamera}
                className="p-4 bg-white/20 hover:bg-white/30 rounded-full backdrop-blur-md transition-colors shadow-lg text-white"
              >
                <FlipHorizontal className="h-6 w-6" />
              </motion.button>
            )}

            {/* Rescan button (only in single-scan mode) */}
            {!continuous && detectedCode && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                whileTap={{ scale: 0.95 }}
                type="button"
                onClick={() => {
                  resetDetection();
                  startScanning(videoRef.current);
                }}
                className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-full backdrop-blur-md transition-colors shadow-lg shadow-blue-500/50 font-medium"
              >
                Scanner à nouveau
              </motion.button>
            )}
          </div>

          {/* Scanning indicator */}
          {isScanning && !detectedCode && (
            <div className="absolute top-6 left-1/2 -translate-x-1/2 z-20">
              <div className="bg-blue-500/90 text-white px-4 py-2 rounded-full backdrop-blur-sm flex items-center gap-2 shadow-lg shadow-blue-500/30">
                <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                <span className="text-sm font-medium">Scan en cours...</span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default BarcodeScanner;
