/**
 * ProductScannerPage - Page dédiée au scan de produits
 *
 * Démonstration complète de l'utilisation du scanner de code-barres
 * dans un contexte de gestion d'inventaire mobile.
 *
 * Features:
 * - Scanner de code-barres fullscreen
 * - Recherche automatique de produit
 * - Affichage des résultats
 * - Actions rapides (ajuster stock, voir détails)
 * - Historique des scans
 * - Mode continu pour scans multiples
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ScanBarcode,
  Package,
  Check,
  X,
  AlertCircle,
  ArrowRight,
  History,
  Settings,
  Zap,
  RefreshCw,
  Plus,
  Minus,
  Eye,
} from 'lucide-react';
import { toast } from 'sonner';
import BarcodeScannerModal from '../../components/ui/BarcodeScannerModal.jsx';
import Card from '../../components/ui/Card.jsx';
import Button from '../../components/ui/Button.jsx';
import api from '../../api/client.js';

export default function ProductScannerPage() {
  const navigate = useNavigate();
  const [isScanning, setIsScanning] = useState(false);
  const [scanHistory, setScanHistory] = useState([]);
  const [currentProduct, setCurrentProduct] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [continuousMode, setContinuousMode] = useState(false);

  // Search product by barcode
  const searchProductByBarcode = async (barcode) => {
    setIsLoading(true);
    try {
      const { data } = await api.get(`/catalog/products/search`, {
        params: { barcode },
      });

      if (data && data.id) {
        setCurrentProduct(data);
        addToHistory(barcode, data, 'success');
        toast.success(`Produit trouvé: ${data.nom}`);
        return data;
      } else {
        addToHistory(barcode, null, 'not_found');
        toast.error('Produit non trouvé');
        setCurrentProduct(null);
        return null;
      }
    } catch (err) {
      console.error('Error searching product:', err);
      addToHistory(barcode, null, 'error');
      toast.error('Erreur lors de la recherche');
      setCurrentProduct(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  // Add scan to history
  const addToHistory = (barcode, product, status) => {
    const historyItem = {
      id: Date.now(),
      barcode,
      product,
      status,
      timestamp: new Date(),
    };

    setScanHistory((prev) => [historyItem, ...prev].slice(0, 20)); // Keep last 20
  };

  // Handle barcode scan
  const handleBarcodeScanned = async (code, format) => {
    await searchProductByBarcode(code);

    // In continuous mode, keep scanner open
    if (!continuousMode) {
      setIsScanning(false);
    }
  };

  // Handle stock adjustment
  const handleStockAdjustment = async (productId, adjustment) => {
    try {
      await api.post(`/stock/movements`, {
        product_id: productId,
        quantity: adjustment,
        type: adjustment > 0 ? 'ENTREE' : 'SORTIE',
        source: 'Ajustement mobile',
      });

      toast.success('Stock mis à jour');

      // Refresh product data
      if (currentProduct?.id === productId) {
        const updated = await searchProductByBarcode(currentProduct.barcode);
        setCurrentProduct(updated);
      }
    } catch (err) {
      console.error('Error adjusting stock:', err);
      toast.error('Erreur lors de la mise à jour du stock');
    }
  };

  // Clear history
  const clearHistory = () => {
    setScanHistory([]);
    toast.success('Historique effacé');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-900/50 backdrop-blur-xl border-b border-white/10 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                <ScanBarcode className="h-8 w-8 text-blue-400" />
                Scanner de produits
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                Scannez les codes-barres pour rechercher et gérer vos produits
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setContinuousMode(!continuousMode)}
              >
                <Zap className={`h-4 w-4 ${continuousMode ? 'text-yellow-400' : ''}`} />
                {continuousMode ? 'Continu' : 'Simple'}
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Scanner Section */}
          <div className="lg:col-span-2 space-y-6">
            {/* Scan Button */}
            {!isScanning && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card className="text-center p-12 bg-gradient-to-br from-blue-500/20 to-purple-500/20 border-blue-500/30">
                  <div className="max-w-md mx-auto">
                    <div className="w-24 h-24 mx-auto mb-6 bg-blue-500/20 rounded-full flex items-center justify-center">
                      <ScanBarcode className="h-12 w-12 text-blue-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-4">
                      Prêt à scanner
                    </h2>
                    <p className="text-slate-300 mb-8">
                      Appuyez sur le bouton pour ouvrir la caméra et scanner un code-barres
                    </p>
                    <Button
                      variant="brand"
                      size="xl"
                      onClick={() => setIsScanning(true)}
                      className="w-full"
                    >
                      <ScanBarcode className="h-6 w-6 mr-2" />
                      Ouvrir le scanner
                    </Button>

                    <div className="mt-6 flex items-center justify-center gap-4 text-sm text-slate-400">
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
                        QR Code
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            )}

            {/* Current Product Result */}
            <AnimatePresence>
              {currentProduct && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                >
                  <Card className="border-green-500/30 bg-green-500/10">
                    <div className="flex items-start gap-4">
                      <div className="p-4 bg-green-500/20 rounded-xl">
                        <Package className="h-8 w-8 text-green-400" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <h3 className="text-xl font-bold text-white">
                              {currentProduct.nom}
                            </h3>
                            <p className="text-sm text-slate-400 mt-1">
                              {currentProduct.categorie || 'Sans catégorie'}
                            </p>
                          </div>
                          <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-medium">
                            Trouvé
                          </span>
                        </div>

                        <div className="grid grid-cols-3 gap-4 my-4">
                          <div>
                            <p className="text-xs text-slate-500 uppercase">Stock</p>
                            <p className="text-2xl font-bold text-white">
                              {currentProduct.stock_actuel || 0}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500 uppercase">Prix</p>
                            <p className="text-2xl font-bold text-white">
                              {(currentProduct.prix_vente || 0).toFixed(2)} €
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500 uppercase">Code-barres</p>
                            <p className="text-sm font-mono text-white mt-1">
                              {currentProduct.barcode || '-'}
                            </p>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-2 mt-4">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStockAdjustment(currentProduct.id, 1)}
                          >
                            <Plus className="h-4 w-4" />
                            +1
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStockAdjustment(currentProduct.id, -1)}
                          >
                            <Minus className="h-4 w-4" />
                            -1
                          </Button>
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => navigate(`/inventory/products/${currentProduct.id}`)}
                          >
                            <Eye className="h-4 w-4" />
                            Voir détails
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setIsScanning(true)}
                          >
                            <RefreshCw className="h-4 w-4" />
                            Scanner à nouveau
                          </Button>
                        </div>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Sidebar - Scan History */}
          <div className="lg:col-span-1">
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <History className="h-5 w-5" />
                  Historique
                </h3>
                {scanHistory.length > 0 && (
                  <button
                    onClick={clearHistory}
                    className="text-xs text-slate-400 hover:text-white transition-colors"
                  >
                    Effacer
                  </button>
                )}
              </div>

              {scanHistory.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <History className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p className="text-sm">Aucun scan effectué</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {scanHistory.map((item) => (
                    <motion.div
                      key={item.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className={`p-2 rounded-lg ${
                            item.status === 'success'
                              ? 'bg-green-500/20'
                              : item.status === 'not_found'
                              ? 'bg-amber-500/20'
                              : 'bg-rose-500/20'
                          }`}
                        >
                          {item.status === 'success' ? (
                            <Check className="h-4 w-4 text-green-400" />
                          ) : item.status === 'not_found' ? (
                            <AlertCircle className="h-4 w-4 text-amber-400" />
                          ) : (
                            <X className="h-4 w-4 text-rose-400" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-white truncate">
                            {item.product?.nom || 'Non trouvé'}
                          </p>
                          <p className="text-xs font-mono text-slate-400 mt-1">
                            {item.barcode}
                          </p>
                          <p className="text-xs text-slate-500 mt-1">
                            {new Date(item.timestamp).toLocaleTimeString('fr-FR')}
                          </p>
                        </div>
                        {item.product && (
                          <button
                            onClick={() =>
                              navigate(`/inventory/products/${item.product.id}`)
                            }
                            className="p-1 hover:bg-white/10 rounded"
                          >
                            <ArrowRight className="h-4 w-4 text-slate-400" />
                          </button>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </Card>

            {/* Scanner Tips */}
            <Card className="mt-4 bg-blue-500/10 border-blue-500/30">
              <h4 className="font-semibold text-blue-400 mb-3 flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Conseils
              </h4>
              <ul className="space-y-2 text-sm text-slate-300">
                <li className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <span>Alignez le code-barres dans le cadre</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <span>Assurez un bon éclairage</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <span>Évitez les reflets sur l'emballage</span>
                </li>
                <li className="flex items-start gap-2">
                  <Check className="h-4 w-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <span>Utilisez la lampe torche si nécessaire</span>
                </li>
              </ul>
            </Card>
          </div>
        </div>
      </div>

      {/* Barcode Scanner Modal */}
      <BarcodeScannerModal
        isOpen={isScanning}
        onClose={() => setIsScanning(false)}
        onConfirm={handleBarcodeScanned}
        onScan={(code) => console.log('Scanned:', code)}
        title="Scanner un code-barres"
        subtitle="Placez le code dans le cadre"
        continuous={continuousMode}
        autoConfirm={!continuousMode}
        autoConfirmDelay={1000}
        showTorchButton={true}
        showCameraSwitch={true}
      />
    </div>
  );
}
