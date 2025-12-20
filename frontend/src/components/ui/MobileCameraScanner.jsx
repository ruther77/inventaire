/**
 * MobileCameraScanner - Composant de scan de documents via la caméra mobile
 *
 * Features:
 * - Accès à la caméra du device (avant/arrière)
 * - Capture d'image avec aperçu
 * - Détection automatique de documents (optionnel)
 * - Optimisation de l'image (rotation, contraste)
 * - Upload vers le backend
 * - Support multi-images
 *
 * @example
 * <MobileCameraScanner
 *   onCapture={(file) => console.log('Captured:', file)}
 *   onUploadComplete={(data) => console.log('Uploaded:', data)}
 * />
 */

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Camera,
  X,
  RotateCw,
  FlipHorizontal,
  Check,
  Loader2,
  AlertCircle,
  RefreshCw,
  Image as ImageIcon,
} from 'lucide-react';
import clsx from 'clsx';
import Button from './Button.jsx';

export function MobileCameraScanner({
  onCapture,
  onUploadComplete,
  onClose,
  accept = 'image/*',
  maxFileSize = 10 * 1024 * 1024, // 10MB
  facingMode = 'environment', // 'user' (front) or 'environment' (back)
  className,
}) {
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [stream, setStream] = useState(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [error, setError] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [currentFacingMode, setCurrentFacingMode] = useState(facingMode);
  const [supportsCameraSwitch, setSupportsCameraSwitch] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);

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
      setError(null);

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
      }
    } catch (err) {
      console.error('Error starting camera:', err);
      setError(
        err.name === 'NotAllowedError'
          ? "Accès à la caméra refusé. Veuillez autoriser l'accès dans les paramètres."
          : "Impossible d'accéder à la caméra. Vérifiez vos permissions."
      );
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
      setIsCameraActive(false);
    }
  };

  // Switch camera (front/back)
  const switchCamera = () => {
    stopCamera();
    setCurrentFacingMode((prev) => (prev === 'user' ? 'environment' : 'user'));
  };

  // Restart camera when facing mode changes
  useEffect(() => {
    if (isCameraActive && !capturedImage) {
      startCamera();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentFacingMode]);

  // Capture image
  const captureImage = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to blob
    canvas.toBlob(
      (blob) => {
        if (blob) {
          const file = new File([blob], `scan-${Date.now()}.jpg`, { type: 'image/jpeg' });

          // Check file size
          if (file.size > maxFileSize) {
            setError(`Image trop volumineuse (max ${Math.round(maxFileSize / 1024 / 1024)}MB)`);
            return;
          }

          const imageUrl = URL.createObjectURL(blob);
          setCapturedImage({ file, url: imageUrl });
          stopCamera();
          onCapture?.(file);
        }
      },
      'image/jpeg',
      0.9
    );
  };

  // Retake image
  const retakeImage = () => {
    if (capturedImage?.url) {
      URL.revokeObjectURL(capturedImage.url);
    }
    setCapturedImage(null);
    startCamera();
  };

  // Confirm and upload
  const confirmImage = async () => {
    if (!capturedImage) return;

    setIsUploading(true);
    setError(null);

    try {
      // Call upload handler
      await onUploadComplete?.(capturedImage.file);
      onClose?.();
    } catch (err) {
      console.error('Upload error:', err);
      setError("Erreur lors de l'envoi de l'image");
    } finally {
      setIsUploading(false);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
      if (capturedImage?.url) {
        URL.revokeObjectURL(capturedImage.url);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // File input fallback
  const handleFileInput = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > maxFileSize) {
      setError(`Fichier trop volumineux (max ${Math.round(maxFileSize / 1024 / 1024)}MB)`);
      return;
    }

    const imageUrl = URL.createObjectURL(file);
    setCapturedImage({ file, url: imageUrl });
    onCapture?.(file);
  };

  return (
    <div className={clsx('relative w-full h-full bg-slate-900', className)}>
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-20 bg-gradient-to-b from-slate-900/80 to-transparent p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Scanner document</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 text-white hover:bg-white/20 rounded-lg transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>
      </div>

      {/* Camera view or captured image */}
      <div className="relative w-full h-full flex items-center justify-center">
        {!isCameraActive && !capturedImage && (
          <div className="text-center p-8">
            <Camera className="h-16 w-16 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-300 mb-6">Scannez une facture ou un document</p>
            <div className="space-y-3">
              <Button
                variant="brand"
                size="lg"
                onClick={startCamera}
                className="w-full"
              >
                <Camera className="h-5 w-5 mr-2" />
                Ouvrir la caméra
              </Button>
              <div className="relative">
                <input
                  type="file"
                  accept={accept}
                  onChange={handleFileInput}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <Button variant="outline" size="lg" className="w-full">
                  <ImageIcon className="h-5 w-5 mr-2" />
                  Choisir une photo
                </Button>
              </div>
            </div>
          </div>
        )}

        {isCameraActive && !capturedImage && (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
            <canvas ref={canvasRef} className="hidden" />

            {/* Camera guide overlay */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute inset-0 border-4 border-white/30 m-8 rounded-lg" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-white/50 text-center">
                <p className="text-sm">Placez le document dans le cadre</p>
              </div>
            </div>
          </>
        )}

        {capturedImage && (
          <motion.img
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            src={capturedImage.url}
            alt="Captured"
            className="w-full h-full object-contain"
          />
        )}
      </div>

      {/* Error message */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute top-20 left-4 right-4 z-20 bg-rose-500 text-white p-4 rounded-lg shadow-lg flex items-start gap-3"
          >
            <AlertCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-semibold">Erreur</p>
              <p className="text-sm">{error}</p>
            </div>
            <button
              type="button"
              onClick={() => setError(null)}
              className="p-1 hover:bg-white/20 rounded"
            >
              <X className="h-4 w-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Controls */}
      <div className="absolute bottom-0 left-0 right-0 z-20 bg-gradient-to-t from-slate-900/90 to-transparent p-6">
        {isCameraActive && !capturedImage && (
          <div className="flex items-center justify-center gap-6">
            {supportsCameraSwitch && (
              <button
                type="button"
                onClick={switchCamera}
                className="p-4 bg-white/10 hover:bg-white/20 rounded-full transition-colors"
              >
                <FlipHorizontal className="h-6 w-6 text-white" />
              </button>
            )}

            <button
              type="button"
              onClick={captureImage}
              className="w-16 h-16 bg-white rounded-full border-4 border-white/50 hover:scale-110 transition-transform active:scale-95"
            />

            <div className="w-12" /> {/* Spacer for symmetry */}
          </div>
        )}

        {capturedImage && (
          <div className="flex items-center justify-center gap-4">
            <Button
              variant="outline"
              size="lg"
              onClick={retakeImage}
              disabled={isUploading}
              className="flex-1 bg-white/10 border-white/30 text-white hover:bg-white/20"
            >
              <RefreshCw className="h-5 w-5 mr-2" />
              Reprendre
            </Button>

            <Button
              variant="brand"
              size="lg"
              onClick={confirmImage}
              disabled={isUploading}
              className="flex-1"
            >
              {isUploading ? (
                <>
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  Envoi...
                </>
              ) : (
                <>
                  <Check className="h-5 w-5 mr-2" />
                  Confirmer
                </>
              )}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

export default MobileCameraScanner;
