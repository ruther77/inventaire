import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { useOfflineContext } from '../contexts/OfflineContext.jsx';
import { useOfflineCreate, useOfflineUpdate, useOfflineDelete } from '../hooks/useOfflineMutation.js';
import { createProduct, updateProductRequest, deleteProductRequest } from '../api/client.js';

/**
 * Exemple d'utilisation du mode offline
 *
 * Démontre comment utiliser les hooks offline pour gérer les mutations
 * avec support de synchronisation automatique.
 */
export default function OfflineModeExample() {
  const queryClient = useQueryClient();
  const {
    isOnline,
    pendingMutations,
    isSyncing,
    syncError,
    syncPendingMutations,
  } = useOfflineContext();

  const [newProduct, setNewProduct] = useState({
    name: '',
    price: '',
    category: '',
  });

  // Mutation de création avec support offline
  const createMutation = useOfflineCreate({
    endpoint: '/catalog/products',
    mutationFn: (data) => createProduct(data),
    onSuccess: (data) => {
      if (data.queued) {
        toast.info('Produit enregistré. Sera synchronisé à la reconnexion.');
      } else {
        toast.success('Produit créé avec succès');
        queryClient.invalidateQueries(['products']);
        setNewProduct({ name: '', price: '', category: '' });
      }
    },
    onError: (error) => {
      toast.error(`Erreur: ${error.message}`);
    },
  });

  // Mutation de mise à jour avec support offline
  const updateMutation = useOfflineUpdate({
    endpoint: '/catalog/products/:id',
    mutationFn: ({ id, ...data }) => updateProductRequest(id, data),
    onSuccess: (data) => {
      if (data.queued) {
        toast.info('Modification enregistrée. Sera synchronisée à la reconnexion.');
      } else {
        toast.success('Produit mis à jour');
        queryClient.invalidateQueries(['products']);
      }
    },
    onError: (error) => {
      toast.error(`Erreur: ${error.message}`);
    },
  });

  // Mutation de suppression avec support offline
  const deleteMutation = useOfflineDelete({
    endpoint: '/catalog/products/:id',
    mutationFn: (id) => deleteProductRequest(id),
    onSuccess: (data) => {
      if (data.queued) {
        toast.info('Suppression enregistrée. Sera synchronisée à la reconnexion.');
      } else {
        toast.success('Produit supprimé');
        queryClient.invalidateQueries(['products']);
      }
    },
    onError: (error) => {
      toast.error(`Erreur: ${error.message}`);
    },
  });

  const handleCreateProduct = (e) => {
    e.preventDefault();
    createMutation.mutate(newProduct);
  };

  const handleUpdateProduct = (id, updates) => {
    updateMutation.mutate({ id, ...updates });
  };

  const handleDeleteProduct = (id) => {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce produit ?')) {
      deleteMutation.mutate(id);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* En-tête avec statut */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h1 className="text-2xl font-bold text-slate-900 mb-4">
          Exemple Mode Offline
        </h1>

        <div className="space-y-3">
          {/* Statut de connexion */}
          <div className="flex items-center gap-3">
            <div
              className={`w-3 h-3 rounded-full ${
                isOnline ? 'bg-emerald-500' : 'bg-amber-500'
              }`}
            />
            <span className="text-sm font-medium">
              {isOnline ? 'En ligne' : 'Hors ligne'}
            </span>
          </div>

          {/* Mutations en attente */}
          {pendingMutations.length > 0 && (
            <div className="text-sm text-slate-600">
              <strong>{pendingMutations.length}</strong> modification
              {pendingMutations.length > 1 ? 's' : ''} en attente de synchronisation
            </div>
          )}

          {/* Synchronisation en cours */}
          {isSyncing && (
            <div className="text-sm text-blue-600 font-medium">
              Synchronisation en cours...
            </div>
          )}

          {/* Erreur de synchronisation */}
          {syncError && (
            <div className="text-sm text-red-600">
              Erreur: {syncError}
            </div>
          )}
        </div>
      </div>

      {/* Formulaire de création */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">
          Créer un produit
        </h2>

        <form onSubmit={handleCreateProduct} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Nom du produit
            </label>
            <input
              type="text"
              value={newProduct.name}
              onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Prix
            </label>
            <input
              type="number"
              step="0.01"
              value={newProduct.price}
              onChange={(e) => setNewProduct({ ...newProduct, price: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Catégorie
            </label>
            <input
              type="text"
              value={newProduct.category}
              onChange={(e) => setNewProduct({ ...newProduct, category: e.target.value })}
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <button
            type="submit"
            disabled={createMutation.isPending}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {createMutation.isPending ? 'Création...' : 'Créer le produit'}
          </button>
        </form>
      </div>

      {/* Actions de démonstration */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">
          Actions de démonstration
        </h2>

        <div className="space-y-3">
          <button
            onClick={() => handleUpdateProduct(1, { name: 'Produit modifié' })}
            disabled={updateMutation.isPending}
            className="w-full px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 disabled:opacity-50 font-medium"
          >
            Modifier un produit (ID: 1)
          </button>

          <button
            onClick={() => handleDeleteProduct(1)}
            disabled={deleteMutation.isPending}
            className="w-full px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 font-medium"
          >
            Supprimer un produit (ID: 1)
          </button>

          {pendingMutations.length > 0 && (
            <button
              onClick={syncPendingMutations}
              disabled={isSyncing || !isOnline}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 font-medium"
            >
              Forcer la synchronisation
            </button>
          )}
        </div>
      </div>

      {/* Liste des mutations en attente */}
      {pendingMutations.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Mutations en attente ({pendingMutations.length})
          </h2>

          <div className="space-y-3">
            {pendingMutations.map((mutation) => (
              <div
                key={mutation.id}
                className="p-4 bg-slate-50 rounded-md border border-slate-200"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-slate-900">
                    {mutation.type}
                  </span>
                  <span
                    className={`text-xs px-2 py-1 rounded ${
                      mutation.status === 'pending'
                        ? 'bg-amber-100 text-amber-800'
                        : mutation.status === 'processing'
                        ? 'bg-blue-100 text-blue-800'
                        : mutation.status === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-emerald-100 text-emerald-800'
                    }`}
                  >
                    {mutation.status}
                  </span>
                </div>

                <div className="text-sm text-slate-600 space-y-1">
                  <div>
                    <strong>Endpoint:</strong> {mutation.endpoint}
                  </div>
                  <div>
                    <strong>Méthode:</strong> {mutation.method}
                  </div>
                  <div>
                    <strong>Date:</strong>{' '}
                    {new Date(mutation.timestamp).toLocaleString('fr-FR')}
                  </div>
                  {mutation.attempts > 0 && (
                    <div>
                      <strong>Tentatives:</strong> {mutation.attempts}
                    </div>
                  )}
                  {mutation.error && (
                    <div className="text-red-600">
                      <strong>Erreur:</strong> {mutation.error}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">
          Comment tester le mode offline ?
        </h3>

        <ol className="space-y-2 text-sm text-blue-800">
          <li>1. Ouvrez les DevTools Chrome (F12)</li>
          <li>2. Allez dans l'onglet Network</li>
          <li>3. Sélectionnez "Offline" dans le menu Throttling</li>
          <li>4. Créez, modifiez ou supprimez un produit</li>
          <li>5. Vérifiez que la mutation est ajoutée à la queue</li>
          <li>6. Remettez la connexion en ligne (Online)</li>
          <li>7. Les mutations sont automatiquement synchronisées</li>
        </ol>
      </div>
    </div>
  );
}
