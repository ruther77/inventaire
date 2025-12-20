# Mode Offline - Documentation

## Vue d'ensemble

Le mode offline permet à l'application de fonctionner de manière dégradée lorsque la connexion Internet est perdue. Les modifications effectuées hors ligne sont automatiquement synchronisées lorsque la connexion est rétablie.

## Architecture

### Composants principaux

1. **`useOffline`** - Hook pour détecter le statut online/offline
2. **`OfflineContext`** - Contexte React pour gérer l'état offline global
3. **`offlineStorage`** - Service pour gérer IndexedDB (cache + queue)
4. **`OfflineBanner`** - Composant UI pour afficher le statut
5. **`useOfflineMutation`** - Hook pour les mutations avec support offline

### Flux de données

```
Online  → Mutation → API → Succès
                    ↓
                  Erreur

Offline → Mutation → Queue IndexedDB → Attente reconnexion
                                      ↓
                              Online → Synchronisation → API
```

## Utilisation

### 1. Détecter le statut offline

```jsx
import { useOffline } from '@/hooks';

function MyComponent() {
  const { isOnline, wasOffline, offlineSince } = useOffline();

  return (
    <div>
      {isOnline ? 'En ligne' : 'Hors ligne'}
      {offlineSince && `Depuis ${offlineSince}`}
    </div>
  );
}
```

### 2. Utiliser le contexte offline

```jsx
import { useOfflineContext } from '@/contexts/OfflineContext';

function MyComponent() {
  const {
    isOnline,
    pendingMutations,
    isSyncing,
    syncError,
    addPendingMutation,
  } = useOfflineContext();

  return (
    <div>
      <p>Mutations en attente: {pendingMutations.length}</p>
      {isSyncing && <p>Synchronisation en cours...</p>}
    </div>
  );
}
```

### 3. Créer une mutation offline-aware

```jsx
import { useOfflineCreate } from '@/hooks';
import { createProduct } from '@/api/client';

function CreateProductForm() {
  const queryClient = useQueryClient();

  const createMutation = useOfflineCreate({
    endpoint: '/catalog/products',
    mutationFn: (data) => createProduct(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['products']);
      toast.success('Produit créé avec succès');
    },
    onError: (error) => {
      toast.error('Erreur lors de la création');
    },
  });

  const handleSubmit = (data) => {
    createMutation.mutate(data);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Formulaire */}
    </form>
  );
}
```

### 4. Mettre en cache des données

```jsx
import { saveToCache, loadFromCache, CACHE_KEYS } from '@/services/offlineStorage';

// Sauvegarder
await saveToCache(CACHE_KEYS.PRODUCTS, productsData);

// Charger
const cachedProducts = await loadFromCache(CACHE_KEYS.PRODUCTS);
```

### 5. Gérer la queue de mutations

```jsx
import {
  queueMutation,
  getPendingMutations,
  updateMutationStatus,
} from '@/services/offlineStorage';

// Ajouter une mutation à la queue
const id = await queueMutation({
  type: 'CREATE',
  endpoint: '/catalog/products',
  method: 'POST',
  payload: { name: 'Nouveau produit' },
  metadata: { category: 'groceries' },
});

// Récupérer les mutations en attente
const pending = await getPendingMutations();

// Mettre à jour le statut
await updateMutationStatus(id, 'completed');
```

## Configuration React Query

La configuration React Query a été optimisée pour le mode offline :

```javascript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      networkMode: 'offlineFirst', // Utiliser le cache même offline
      refetchOnReconnect: true,    // Rafraîchir à la reconnexion
      retry: (failureCount, error) => {
        if (!navigator.onLine) return false; // Pas de retry si offline
        return failureCount < 2;
      },
    },
    mutations: {
      networkMode: 'offlineFirst', // Permettre les mutations offline
    },
  },
});
```

## Stockage IndexedDB

### Structure de la base de données

- **Store `cache`** : Données critiques pour utilisation offline
  - Produits
  - Fournisseurs
  - Catégories
  - Transactions financières
  - Comptes bancaires
  - Overview cockpit

- **Store `mutations`** : Queue des mutations en attente
  - ID auto-incrémenté
  - Type (CREATE, UPDATE, DELETE)
  - Endpoint API
  - Méthode HTTP
  - Payload
  - Statut (pending, processing, completed, failed)
  - Métadonnées

- **Store `metadata`** : Métadonnées système
  - Dernière synchronisation
  - Version du schéma
  - Paramètres utilisateur

### Clés de cache disponibles

```javascript
import { CACHE_KEYS } from '@/services/offlineStorage';

CACHE_KEYS.PRODUCTS
CACHE_KEYS.VENDORS
CACHE_KEYS.CATEGORIES
CACHE_KEYS.FINANCE_TRANSACTIONS
CACHE_KEYS.FINANCE_ACCOUNTS
CACHE_KEYS.RESTAURANT_PLATS
CACHE_KEYS.RESTAURANT_INGREDIENTS
CACHE_KEYS.COCKPIT_OVERVIEW
```

## Composant OfflineBanner

Le composant `OfflineBanner` affiche automatiquement :

- **Hors ligne** : Bannière orange avec durée offline et nombre de mutations en attente
- **Reconnecté** : Bannière verte avec état de synchronisation
- **Erreur de sync** : Bannière rouge avec message d'erreur

```jsx
import OfflineBanner from '@/components/feedback/OfflineBanner';

function App() {
  return (
    <>
      <OfflineBanner />
      {/* Reste de l'application */}
    </>
  );
}
```

### Version compacte (mobile)

```jsx
import { OfflineBannerCompact } from '@/components/feedback/OfflineBanner';

function MobileApp() {
  return (
    <>
      <OfflineBannerCompact />
      {/* Reste de l'application */}
    </>
  );
}
```

## Hooks disponibles

### useOffline

Détecte le statut online/offline.

```javascript
const {
  isOnline,      // true si en ligne
  wasOffline,    // true si vient de se reconnecter
  lastOnlineAt,  // Date de dernière connexion
  offlineSince,  // Date du début de la déconnexion
} = useOffline();
```

### useOfflineContext

Accède au contexte offline global.

```javascript
const {
  isOnline,
  wasOffline,
  pendingMutations,    // Liste des mutations en attente
  addPendingMutation,  // Ajouter une mutation
  syncPendingMutations, // Synchroniser manuellement
  isSyncing,           // État de synchronisation
  syncError,           // Erreur de synchronisation
  storageStats,        // Statistiques de stockage
  refreshStats,        // Rafraîchir les statistiques
} = useOfflineContext();
```

### useOfflineMutation

Hook générique pour les mutations offline.

```javascript
const mutation = useOfflineMutation({
  mutationFn: (data) => api.post('/endpoint', data),
  endpoint: '/endpoint',
  method: 'POST',
  mutationType: 'CREATE',
  onSuccess: (data) => { /* ... */ },
  onError: (error) => { /* ... */ },
  metadata: { /* métadonnées personnalisées */ },
});
```

### Hooks spécialisés

```javascript
// Création
const create = useOfflineCreate({
  endpoint: '/endpoint',
  mutationFn: (data) => api.post('/endpoint', data),
});

// Mise à jour complète
const update = useOfflineUpdate({
  endpoint: '/endpoint/:id',
  mutationFn: (data) => api.put(`/endpoint/${data.id}`, data),
});

// Mise à jour partielle
const patch = useOfflinePatch({
  endpoint: '/endpoint/:id',
  mutationFn: (data) => api.patch(`/endpoint/${data.id}`, data),
});

// Suppression
const remove = useOfflineDelete({
  endpoint: '/endpoint/:id',
  mutationFn: (id) => api.delete(`/endpoint/${id}`),
});
```

## Exemples pratiques

### Créer un produit avec support offline

```jsx
import { useOfflineCreate } from '@/hooks';
import { createProduct } from '@/api/client';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

function CreateProductButton() {
  const queryClient = useQueryClient();

  const createMutation = useOfflineCreate({
    endpoint: '/catalog/products',
    mutationFn: (product) => createProduct(product),
    onSuccess: (data) => {
      if (data.queued) {
        toast.info('Produit enregistré. Sera synchronisé à la reconnexion.');
      } else {
        toast.success('Produit créé avec succès');
        queryClient.invalidateQueries(['products']);
      }
    },
    onError: (error) => {
      toast.error('Erreur lors de la création du produit');
    },
  });

  return (
    <button onClick={() => createMutation.mutate({ name: 'Nouveau produit' })}>
      Créer un produit
    </button>
  );
}
```

### Mettre à jour une transaction financière

```jsx
import { useOfflinePatch } from '@/hooks';
import { updateFinanceTransaction } from '@/api/client';

function UpdateTransactionButton({ transactionId }) {
  const updateMutation = useOfflinePatch({
    endpoint: `/finance/transactions/${transactionId}`,
    mutationFn: (data) => updateFinanceTransaction({ transactionId, payload: data }),
    onSuccess: () => {
      queryClient.invalidateQueries(['finance', 'transactions']);
    },
  });

  return (
    <button onClick={() => updateMutation.mutate({ category_id: 42 })}>
      Mettre à jour
    </button>
  );
}
```

### Afficher les mutations en attente

```jsx
import { useOfflineContext } from '@/contexts/OfflineContext';

function PendingMutationsList() {
  const { pendingMutations, isSyncing } = useOfflineContext();

  if (pendingMutations.length === 0) {
    return <p>Aucune modification en attente</p>;
  }

  return (
    <div>
      <h3>Modifications en attente ({pendingMutations.length})</h3>
      {isSyncing && <p>Synchronisation en cours...</p>}

      <ul>
        {pendingMutations.map((mutation) => (
          <li key={mutation.id}>
            {mutation.type} - {mutation.endpoint}
            <span>{new Date(mutation.timestamp).toLocaleString()}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

## Gestion des erreurs

### Erreurs de synchronisation

Les erreurs de synchronisation sont gérées automatiquement :

1. La mutation est marquée comme `failed`
2. L'erreur est stockée dans la mutation
3. Le callback `onError` est appelé
4. L'erreur est affichée dans `syncError` du contexte

### Retry manuel

```jsx
function RetryButton() {
  const { syncPendingMutations, isSyncing } = useOfflineContext();

  return (
    <button onClick={syncPendingMutations} disabled={isSyncing}>
      {isSyncing ? 'Synchronisation...' : 'Réessayer'}
    </button>
  );
}
```

## Limitations

1. **Pas de résolution de conflits** : Si les données ont changé sur le serveur, la dernière mutation écrase les données
2. **Pas de validation côté serveur** : Les mutations offline ne peuvent pas être validées avant la synchronisation
3. **Pas de transactions** : Les mutations sont rejouées individuellement, pas en transaction atomique
4. **Cache limité** : Seules les données essentielles sont mises en cache

## Bonnes pratiques

1. **Utilisez les hooks spécialisés** : `useOfflineCreate`, `useOfflineUpdate`, etc. plutôt que `useOfflineMutation`
2. **Gérez les réponses en queue** : Vérifiez `data.queued` dans `onSuccess`
3. **Invalidez les queries** : Toujours invalider les queries après une mutation
4. **Messages utilisateur** : Informez l'utilisateur que la modification sera synchronisée
5. **Testez offline** : Utilisez les DevTools Chrome (Network → Offline) pour tester

## Debugging

### Activer les logs

Les logs sont automatiquement activés en développement. Pour voir les logs :

```javascript
// Console
[Offline] Ajout de la mutation CREATE à la queue
[Offline] Mutation ajoutée à la queue avec succès
[App] Gone offline
[App] Back online
[Offline] Synchronisation de 3 mutations en attente...
[Offline] Mutation 1 synchronisée avec succès
```

### Inspecter IndexedDB

1. Ouvrir les DevTools Chrome
2. Aller dans Application → Storage → IndexedDB
3. Ouvrir la base `inventaire-offline`
4. Inspecter les stores `cache`, `mutations`, `metadata`

### Simuler le mode offline

```javascript
// Dans la console
navigator.serviceWorker.controller.postMessage({ type: 'SIMULATE_OFFLINE' });

// Ou dans les DevTools
// Network → Throttling → Offline
```

## Maintenance

### Nettoyer les mutations terminées

```javascript
import { clearCompletedMutations } from '@/services/offlineStorage';

const deletedCount = await clearCompletedMutations();
console.log(`${deletedCount} mutations supprimées`);
```

### Vider tout le cache

```javascript
import { clearAllCache } from '@/services/offlineStorage';

await clearAllCache();
console.log('Cache vidé');
```

### Statistiques de stockage

```javascript
import { getStorageStats } from '@/services/offlineStorage';

const stats = await getStorageStats();
console.log(stats);
// {
//   cacheEntries: 5,
//   totalMutations: 12,
//   pendingMutations: 3,
//   completedMutations: 9
// }
```
