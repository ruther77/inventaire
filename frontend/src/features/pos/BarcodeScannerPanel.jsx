import { useEffect, useMemo, useRef, useState } from 'react';
import Button from '../../components/ui/Button.jsx';
import Card from '../../components/ui/Card.jsx';
import { lookupProductByBarcode } from '../../api/client.js';

const SUPPORTED_FORMATS = ['ean_13', 'code_128', 'ean_8', 'code_39', 'qr_code', 'upc_a'];

export default function BarcodeScannerPanel({ autoAddEnabled, onProductDetected }) {
  const videoRef = useRef(null);
  const lastCodeRef = useRef('');
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');
  const [lastCode, setLastCode] = useState('');
  const [manualCode, setManualCode] = useState('');
  const [lookupMessage, setLookupMessage] = useState('');
  const [lookups, setLookups] = useState([]);

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
      } catch (detectorError) {
        setError("Impossible d'initialiser la détection vidéo.");
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
      } catch (cameraError) {
        setError('Accès caméra refusé ou indisponible.');
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
    setLookupMessage(`Recherche du code ${trimmed}…`);
    try {
      const product = await lookupProductByBarcode(trimmed);
      setLookupMessage(product?.nom ? `Ajouté : ${product.nom}` : 'Aucun produit trouvé');
      setLookups((prev) => [{ code: trimmed, product }, ...prev].slice(0, 5));
      if (product && typeof onProductDetected === 'function') {
        onProductDetected(product, autoAddEnabled);
      }
    } catch (lookupError) {
      setLookupMessage('Produit introuvable');
    }
  };

  const latestLookups = useMemo(
    () =>
      lookups.map((entry) => ({
        ...entry,
        label: entry.product?.nom ?? 'Non trouvé',
      })),
    [lookups],
  );

  const handleManualLookup = () => {
    performLookup(manualCode);
    setManualCode('');
  };

  return (
    <Card className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.4em] text-slate-400">scanner</p>
          <h3 className="text-lg font-semibold text-slate-900">Codes-barres</h3>
          <p className="text-xs text-slate-500">
            Visez l&apos;article et nous tentons de le placer automatiquement dans votre panier.
          </p>
        </div>
        <Button variant={scanning ? 'ghost' : 'brand'} onClick={() => setScanning((prev) => !prev)}>
          {scanning ? 'Couper la caméra' : 'Activer la caméra'}
        </Button>
      </div>
      {error && <p className="rounded-xl bg-rose-50 px-4 py-2 text-sm text-rose-700">{error}</p>}
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
        <video ref={videoRef} className="mx-auto max-h-[220px] w-full rounded-xl bg-black object-contain" muted playsInline />
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <label className="text-sm text-slate-600">
          Code manuel
          <div className="mt-1 flex gap-2">
            <input
              type="text"
              value={manualCode}
              onChange={(event) => setManualCode(event.target.value)}
              className="flex-1 rounded-2xl border border-slate-200 px-4 py-2 text-sm focus:border-brand-400 focus:outline-none"
              placeholder="1234567890123"
            />
            <Button variant="ghost" onClick={handleManualLookup}>
              Chercher
            </Button>
          </div>
        </label>
        <div className="rounded-2xl border border-slate-100 bg-white p-3 text-sm text-slate-600">
          <p className="text-xs uppercase tracking-widest text-slate-400">Dernier code</p>
          <p className="text-lg font-semibold text-slate-900">{lastCode || '—'}</p>
          <p className="text-xs text-slate-500">{lookupMessage || 'En attente de scan.'}</p>
        </div>
      </div>
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Derniers résultats</p>
        {latestLookups.length === 0 ? (
          <p className="text-sm text-slate-500">Aucun scan traité pour le moment.</p>
        ) : (
          <ul className="mt-2 divide-y divide-slate-100 text-sm">
            {latestLookups.map((entry) => (
              <li key={`${entry.code}-${entry.label}`} className="flex items-center justify-between py-1">
                <span className="font-medium text-slate-900">{entry.code}</span>
                <span className="text-xs text-slate-500">{entry.label}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  );
}
