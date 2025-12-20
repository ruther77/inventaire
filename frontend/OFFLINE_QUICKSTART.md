# Mode Offline - Guide rapide

## Installation

Aucune dépendance supplémentaire requise ! Le mode offline utilise :
- IndexedDB (natif navigateur)
- TanStack Query (déjà installé)
- Framer Motion (déjà installé)

## Utilisation rapide

### 1. Créer une mutation offline-aware

```jsx
import { useOfflineCreate } from '@/hooks';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

function CreateProductForm() {
  const queryClient = useQueryClient();

  const createMutation = useOfflineCreate({
    endpoint: '/catalog/products',
    mutationFn: (data) => api.post('/catalog/products', data),
    onSuccess: (data) => {
      if (data.queued) {
        toast.info('Enregistré. Sera synchronisé à la reconnexion.');
      } else {
        toast.success('Produit créé');
        queryClient.invalidateQueries(['products']);
      }
    },
  });

  return (
    <button onClick={() => createMutation.mutate({ name: 'Nouveau produit' })}>
      Créer
    </button>
  );
}
```

### 2. Afficher le statut offline

```jsx
import { useOfflineContext } from '@/contexts/OfflineContext';

function StatusBar() {
  const { isOnline, pendingMutations } = useOfflineContext();

  return (
    <div>
      {!isOnline && (
        <div className="bg-amber-100 p-2">
          Hors-ligne - {pendingMutations.length} modification(s) en attente
        </div>
      )}
    </div>
  );
}
```

### 3. La bannière est déjà intégrée !

Le composant `OfflineBanner` est déjà ajouté dans `AppShell.jsx`.
Il s'affiche automatiquement quand vous êtes offline.

## Tester

1. Ouvrir les DevTools (F12)
2. Network → Offline
3. Créer/modifier/supprimer des données
4. Network → Online
5. Observer la synchronisation automatique

## Hooks disponibles

```jsx
// Détection du statut
useOffline()

// Contexte global
useOfflineContext()

// Mutations
useOfflineCreate()
useOfflineUpdate()
useOfflinePatch()
useOfflineDelete()
```

## Documentation complète

Voir `OFFLINE_MODE.md` pour la documentation complète.
