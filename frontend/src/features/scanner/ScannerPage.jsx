import { useEffect, useMemo, useRef, useState } from 'react';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import { lookupProductByBarcode } from '../../api/client.js';

const numberFormatter = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 });

export default function ScannerPage() {
  const videoRef = useRef(null);
  const lastCodeRef = useRef('');
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState('');
  const [lastCode, setLastCode] = useState('');
  const [manualCode, setManualCode] = useState('');
  const [product, setProduct] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    lastCodeRef.current = lastCode;
  }, [lastCode]);

  useEffect(() => {
    let abort = false;
    if (!lastCode) {
      setProduct(null);
      return () => {
        abort = true;
      };
    }
    lookupProductByBarcode(lastCode)
      .then((data) => {
        if (!abort) setProduct(data);
      })
      .catch(() => {
        if (!abort) setProduct(null);
      });
    return () => {
      abort = true;
    };
  }, [lastCode]);

  useEffect(() => {
    let stream;
    let intervalId;
    let detector;
    if (!scanning) {
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      return () => undefined;
    }

    async function start() {
      if (typeof window === 'undefined' || !('BarcodeDetector' in window)) {
        setError("Votre navigateur ne supporte pas l'API BarcodeDetector.");
        return;
      }
      try {
        detector = new window.BarcodeDetector({
          formats: ['ean_13', 'code_128', 'ean_8', 'code_39', 'qr_code', 'upc_a'],
        });
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
              setHistory((prev) => [{ code: value, timestamp: Date.now() }, ...prev].slice(0, 10));
            }
          }
        } catch {
          // ignore detection errors
        }
      }, 800);
    }

    start();

    return () => {
      if (intervalId) window.clearInterval(intervalId);
      if (stream) stream.getTracks().forEach((track) => track.stop());
    };
  }, [scanning]);

  const latestHistory = useMemo(
    () => history.map((entry) => ({ ...entry, label: new Date(entry.timestamp).toLocaleTimeString('fr-FR') })),
    [history],
  );

  const handleManualLookup = () => {
    const value = manualCode.trim();
    if (!value) return;
    setLastCode(value);
    setHistory((prev) => [{ code: value, timestamp: Date.now() }, ...prev].slice(0, 10));
  };

  return (
    <div className="flex flex-col gap-6">
      <Card className="flex flex-col gap-4">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.4em] text-slate-400">scanner</p>
            <h2 className="text-2xl font-semibold text-slate-900">Capture caméra</h2>
            <p className="text-sm text-slate-500">
              Analysez vos codes-barres en direct et retrouvez instantanément le produit lié dans le catalogue.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant={scanning ? 'ghost' : 'brand'} onClick={() => setScanning((prev) => !prev)}>
              {scanning ? 'Arrêter la capture' : 'Activer la caméra'}
            </Button>
          </div>
        </div>
        {error && <p className="rounded-xl bg-rose-50 px-4 py-2 text-sm text-rose-700">{error}</p>}
      </Card>

      <Card className="grid gap-4 md:grid-cols-3">
        <Metric label="Dernier code" value={lastCode || '—'} />
        <Metric label="Produit trouvé" value={product?.nom ?? '—'} />
        <Metric label="Stock actuel" value={product ? numberFormatter.format(product.stock_actuel ?? 0) : '—'} />
      </Card>

      <Card className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-slate-900">Flux vidéo</h3>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <video ref={videoRef} className="mx-auto max-h-[360px] w-full rounded-xl bg-black object-contain" muted playsInline />
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <label className="text-sm text-slate-600">
            Saisie manuelle
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
          {product ? (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
              <p className="font-semibold">{product.nom}</p>
              <p className="mt-1 text-slate-600">
                Catégorie : <span className="font-medium">{product.categorie ?? '—'}</span>
              </p>
              <p className="text-slate-600">
                Prix vente TTC :{' '}
                <span className="font-medium">{numberFormatter.format(product.prix_vente ?? 0)} €</span>
             </p>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 bg-white p-3 text-sm text-slate-500">
              En attente de correspondance produit.
            </div>
          )}
        </div>
      </Card>

      <Card className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold text-slate-900">Historique récent</h3>
        {latestHistory.length ? (
          <ul className="divide-y divide-slate-100 text-sm">
            {latestHistory.map((entry) => (
              <li key={`${entry.code}-${entry.timestamp}`} className="flex items-center justify-between px-1 py-2">
                <span className="font-medium text-slate-900">{entry.code}</span>
                <span className="text-xs text-slate-500">{entry.label}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">Aucun scan pour le moment.</p>
        )}
      </Card>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400">{label}</p>
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}
