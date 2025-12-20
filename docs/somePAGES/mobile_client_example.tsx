/**
 * Mobile Client Example - React Native / TypeScript
 *
 * Example implementation of newCMS mobile endpoints
 * for inventory scanning and stock adjustment.
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Camera, BarCodeScanner } from 'expo-barcode-scanner';

// ============================================================================
// Types
// ============================================================================

interface MobileInventoryItem {
  id: number;
  nom: string;
  code_barre: string | null;
  stock_actuel: number;
  seuil_alerte: number;
  categorie: string | null;
}

interface MobileScanResponse {
  found: boolean;
  product: MobileInventoryItem | null;
  message: string | null;
}

interface MobileAdjustResponse {
  product_id: number;
  product_name: string;
  old_stock: number;
  new_stock: number;
  adjustment: number;
  reason: string;
  timestamp: string;
}

type AdjustmentReason = 'breakage' | 'theft' | 'error' | 'expiry' | 'other';

// ============================================================================
// API Client
// ============================================================================

class NewCMSClient {
  private baseUrl: string;
  private token: string;

  constructor(baseUrl: string, token: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Get inventory list (paginated)
  async getInventory(
    page: number = 1,
    pageSize: number = 50,
    search?: string
  ) {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      ...(search && { search }),
    });

    return this.request<{
      items: MobileInventoryItem[];
      total: number;
      page: number;
      page_size: number;
    }>(`/newcms/mobile/inventory?${params}`);
  }

  // Scan barcode
  async scanBarcode(codeBarres: string): Promise<MobileScanResponse> {
    return this.request<MobileScanResponse>('/newcms/mobile/scan', {
      method: 'POST',
      body: JSON.stringify({ code_barre: codeBarres }),
    });
  }

  // Adjust stock
  async adjustStock(
    productId: number,
    adjustment: number,
    adjustmentType: 'delta' | 'absolute',
    reason: AdjustmentReason,
    notes?: string
  ): Promise<MobileAdjustResponse> {
    return this.request<MobileAdjustResponse>('/newcms/mobile/adjust', {
      method: 'POST',
      body: JSON.stringify({
        product_id: productId,
        adjustment,
        adjustment_type: adjustmentType,
        reason,
        notes,
      }),
    });
  }
}

// ============================================================================
// React Native Component - Barcode Scanner
// ============================================================================

interface BarcodeScannerScreenProps {
  apiClient: NewCMSClient;
  onScanComplete: (product: MobileInventoryItem) => void;
}

const BarcodeScannerScreen: React.FC<BarcodeScannerScreenProps> = ({
  apiClient,
  onScanComplete,
}) => {
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [scanned, setScanned] = useState(false);
  const [loading, setLoading] = useState(false);

  React.useEffect(() => {
    (async () => {
      const { status } = await BarCodeScanner.requestPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  const handleBarCodeScanned = useCallback(
    async ({ type, data }: { type: string; data: string }) => {
      if (scanned || loading) return;

      setScanned(true);
      setLoading(true);

      try {
        const result = await apiClient.scanBarcode(data);

        if (result.found && result.product) {
          // Vibrate on success
          Vibration.vibrate(100);

          // Show product found
          Alert.alert(
            'Produit trouvé',
            `${result.product.nom}\nStock: ${result.product.stock_actuel}`,
            [
              {
                text: 'OK',
                onPress: () => {
                  onScanComplete(result.product!);
                  setScanned(false);
                },
              },
            ]
          );
        } else {
          Alert.alert('Produit non trouvé', result.message || 'Code-barres inconnu', [
            { text: 'Réessayer', onPress: () => setScanned(false) },
          ]);
        }
      } catch (error) {
        Alert.alert('Erreur', 'Impossible de scanner le code-barres', [
          { text: 'Réessayer', onPress: () => setScanned(false) },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [scanned, loading, apiClient, onScanComplete]
  );

  if (hasPermission === null) {
    return <Text>Demande de permission caméra...</Text>;
  }

  if (hasPermission === false) {
    return <Text>Pas d'accès à la caméra</Text>;
  }

  return (
    <View style={styles.container}>
      <BarCodeScanner
        onBarCodeScanned={scanned ? undefined : handleBarCodeScanned}
        style={StyleSheet.absoluteFillObject}
      />

      {loading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#fff" />
          <Text style={styles.loadingText}>Recherche du produit...</Text>
        </View>
      )}

      {scanned && !loading && (
        <TouchableOpacity
          style={styles.resetButton}
          onPress={() => setScanned(false)}
        >
          <Text style={styles.resetButtonText}>Scanner à nouveau</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

// ============================================================================
// React Native Component - Stock Adjustment
// ============================================================================

interface StockAdjustmentScreenProps {
  apiClient: NewCMSClient;
  product: MobileInventoryItem;
  onAdjustComplete: (response: MobileAdjustResponse) => void;
}

const StockAdjustmentScreen: React.FC<StockAdjustmentScreenProps> = ({
  apiClient,
  product,
  onAdjustComplete,
}) => {
  const [loading, setLoading] = useState(false);

  const handleAdjustment = async (
    delta: number,
    reason: AdjustmentReason,
    notes?: string
  ) => {
    setLoading(true);

    try {
      const result = await apiClient.adjustStock(
        product.id,
        delta,
        'delta',
        reason,
        notes
      );

      Alert.alert(
        'Ajustement effectué',
        `Stock: ${result.old_stock} → ${result.new_stock}`,
        [{ text: 'OK', onPress: () => onAdjustComplete(result) }]
      );
    } catch (error) {
      Alert.alert('Erreur', "Impossible d'ajuster le stock");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{product.nom}</Text>
      <Text style={styles.stock}>Stock actuel: {product.stock_actuel}</Text>

      <View style={styles.buttonGrid}>
        {/* Quick adjustments */}
        <TouchableOpacity
          style={[styles.button, styles.buttonDecrease]}
          onPress={() => handleAdjustment(-1, 'breakage', 'Scan mobile')}
          disabled={loading}
        >
          <Text style={styles.buttonText}>-1 (Casse)</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.buttonIncrease]}
          onPress={() => handleAdjustment(+1, 'error', 'Scan mobile')}
          disabled={loading}
        >
          <Text style={styles.buttonText}>+1 (Correction)</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.buttonExpiry]}
          onPress={() => handleAdjustment(-1, 'expiry', 'Scan mobile')}
          disabled={loading}
        >
          <Text style={styles.buttonText}>Périmé</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.button, styles.buttonTheft]}
          onPress={() => handleAdjustment(-1, 'theft', 'Scan mobile')}
          disabled={loading}
        >
          <Text style={styles.buttonText}>Vol</Text>
        </TouchableOpacity>
      </View>

      {loading && <ActivityIndicator size="large" color="#3742FA" />}
    </View>
  );
};

// ============================================================================
// Styles
// ============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  stock: {
    fontSize: 18,
    color: '#666',
    marginBottom: 20,
  },
  buttonGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  button: {
    flex: 1,
    minWidth: '45%',
    padding: 20,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonDecrease: {
    backgroundColor: '#FF6B6B',
  },
  buttonIncrease: {
    backgroundColor: '#51CF66',
  },
  buttonExpiry: {
    backgroundColor: '#95A5A6',
  },
  buttonTheft: {
    backgroundColor: '#FF4757',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.7)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    color: '#fff',
    marginTop: 10,
    fontSize: 16,
  },
  resetButton: {
    position: 'absolute',
    bottom: 40,
    left: 20,
    right: 20,
    padding: 15,
    backgroundColor: '#3742FA',
    borderRadius: 8,
    alignItems: 'center',
  },
  resetButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

// ============================================================================
// Usage Example
// ============================================================================

export default function App() {
  const [apiClient] = useState(
    () => new NewCMSClient('https://api.example.com', 'your_jwt_token')
  );
  const [scannedProduct, setScannedProduct] = useState<MobileInventoryItem | null>(
    null
  );

  const handleScanComplete = (product: MobileInventoryItem) => {
    setScannedProduct(product);
  };

  const handleAdjustComplete = (response: MobileAdjustResponse) => {
    console.log('Adjustment complete:', response);
    setScannedProduct(null);
  };

  return (
    <View style={{ flex: 1 }}>
      {!scannedProduct ? (
        <BarcodeScannerScreen
          apiClient={apiClient}
          onScanComplete={handleScanComplete}
        />
      ) : (
        <StockAdjustmentScreen
          apiClient={apiClient}
          product={scannedProduct}
          onAdjustComplete={handleAdjustComplete}
        />
      )}
    </View>
  );
}
