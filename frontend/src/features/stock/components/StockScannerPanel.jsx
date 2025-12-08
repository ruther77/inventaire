import { useEffect, useRef, useState } from 'react';
import { Camera, CameraOff, Search } from 'lucide-react';
import Button from '../../../components/ui/Button.jsx';
import { lookupProductByBarcode } from '../../../api/client.js';

const SUPPORTED_FORMATS = ['ean_13', 'code_128', 'ean_8', 'code_39', 'qr_code', 'upc_a'];

export default function StockScannerPanel({ onProductFound }) {
  const videoRef = useRef(null);
  const lastCodeRef = useRef('');
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');
  const [lastCode, setLastCode] = useState('');
  const [manualCode, setManualCode] = useState('');
  const [lookupStatus, setLookupStatus] = useState('');
  const [foundProduct, setFoundProduct] = useState(null);

  useEffect(() => {
    lastCodeRef.current = lastCode;
  }, [lastCode]);

  useEffect(() => {
    let stream;
    let intervalId;
    let detector;

    const stopCapture = () => {
      if (intervalId) window.clearInterval(intervalId);
      if (stream) stream.getTracks().forEach((track) => track.stop());
      if (videoRef.current) {
        videoRef.current.pause();
        videoRef.current.srcObject = null;
      }
    };

    if (!scanning) {
      stopCapture();
      return stopCapture;
    }

    async function start() {
      if (typeof window === 'undefined' || !('BarcodeDetector' in window)) {
        setError("Votre navigateur ne supporte pas l'API BarcodeDetector.");
        return;
      }
      try {
        detector = new window.BarcodeDetector({ formats: SUPPORTED_FORMATS });
      } catch {
        setError("Impossible d'initialiser la detection video.");
        return;
      }

      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } },
          audio: false,
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
      } catch {
        setError('Acces camera refuse ou indisponible.');
        return;
      }

      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      intervalId = window.setInterval(async () => {
        if (!videoRef.current || videoRef.current.readyState < 2) {
          return;
        }
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
        try {
          const detections = await detector.detect(canvas);
          if (detections.length) {
            const value = detections[0].rawValue || detections[0].value;
            if (value && value !== lastCodeRef.current) {
              lastCodeRef.current = value;
              setLastCode(value);
              performLookup(value);
            }
          }
        } catch {
          // ignore transient detection errors
        }
      }, 700);
    }

    start();
    return stopCapture;
  }, [scanning]);

  const performLookup = async (code) => {
    if (!code) return;
    const trimmed = code.trim();
    if (!trimmed) return;
    setLookupStatus('searching');
    setFoundProduct(null);
    try {
      const product = await lookupProductByBarcode(trimmed);
      if (product) {
        setFoundProduct(product);
        setLookupStatus('found');
        if (typeof onProductFound === 'function') {
          onProductFound(product);
        }
      } else {
        setLookupStatus('not_found');
      }
    } catch {
      setLookupStatus('not_found');
    }
  };

  const handleManualLookup = () => {
    if (!manualCode.trim()) return;
    setLastCode(manualCode.trim());
    performLookup(manualCode);
    setManualCode('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleManualLookup();
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-widest text-slate-400">Scanner</p>
          <p className="text-sm font-medium text-slate-700">Scannez ou saisissez un code-barres</p>
        </div>
        <Button
          variant={scanning ? 'ghost' : 'subtle'}
          size="sm"
          onClick={() => setScanning((prev) => !prev)}
          className="flex items-center gap-2"
        >
          {scanning ? (
            <>
              <CameraOff className="w-4 h-4" />
              Arreter
            </>
          ) : (
            <>
              <Camera className="w-4 h-4" />
              Scanner
            </>
          )}
        </Button>
      </div>

      {error && (
        <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>
      )}

      {scanning && (
        <div className="rounded-xl border border-slate-200 bg-black overflow-hidden">
          <video
            ref={videoRef}
            className="mx-auto max-h-[180px] w-full object-contain"
            muted
            playsInline
          />
        </div>
      )}

      <div className="flex gap-2">
        <input
          type="text"
          value={manualCode}
          onChange={(e) => setManualCode(e.target.value)}
          onKeyDown={handleKeyDown}
          className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
          placeholder="Code-barres manuel..."
        />
        <Button variant="ghost" size="sm" onClick={handleManualLookup}>
          <Search className="w-4 h-4" />
        </Button>
      </div>

      {lastCode && (
        <div className={`rounded-xl p-3 text-sm ${
          lookupStatus === 'found'
            ? 'bg-emerald-50 border border-emerald-200'
            : lookupStatus === 'not_found'
            ? 'bg-amber-50 border border-amber-200'
            : 'bg-slate-100 border border-slate-200'
        }`}>
          <p className="text-xs text-slate-500">Code: {lastCode}</p>
          {lookupStatus === 'searching' && (
            <p className="text-slate-600">Recherche en cours...</p>
          )}
          {lookupStatus === 'found' && foundProduct && (
            <p className="font-medium text-emerald-800">
              {foundProduct.nom} (stock: {foundProduct.stock_actuel ?? 0})
            </p>
          )}
          {lookupStatus === 'not_found' && (
            <p className="text-amber-700">Produit non trouve</p>
          )}
        </div>
      )}
    </div>
  );
}
