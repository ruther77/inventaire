import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import {
  saveToCache,
  loadFromCache,
  isCacheValid,
  clearCacheEntry,
  clearAllCache,
  queueMutation,
  getPendingMutations,
  updateMutationStatus,
  deleteMutation,
  clearCompletedMutations,
  saveMetadata,
  loadMetadata,
  getStorageStats,
  CACHE_KEYS,
} from '../offlineStorage.js';

describe('offlineStorage', () => {
  beforeEach(async () => {
    // Nettoyer avant chaque test
    await clearAllCache();
    const mutations = await getPendingMutations();
    for (const mutation of mutations) {
      await deleteMutation(mutation.id);
    }
  });

  afterEach(async () => {
    // Nettoyer après chaque test
    await clearAllCache();
    const mutations = await getPendingMutations();
    for (const mutation of mutations) {
      await deleteMutation(mutation.id);
    }
  });

  describe('Cache', () => {
    it('should save and load data from cache', async () => {
      const testData = { id: 1, name: 'Test Product' };

      await saveToCache(CACHE_KEYS.PRODUCTS, testData);
      const loaded = await loadFromCache(CACHE_KEYS.PRODUCTS);

      expect(loaded).toEqual(testData);
    });

    it('should return null for non-existent cache key', async () => {
      const loaded = await loadFromCache('non-existent-key');
      expect(loaded).toBeNull();
    });

    it('should validate cache freshness', async () => {
      const testData = { id: 1, name: 'Test Product' };

      await saveToCache(CACHE_KEYS.PRODUCTS, testData);

      // Cache devrait être valide immédiatement
      const isValid = await isCacheValid(CACHE_KEYS.PRODUCTS, 5 * 60 * 1000);
      expect(isValid).toBe(true);

      // Cache devrait être invalide avec un maxAge très court
      const isInvalid = await isCacheValid(CACHE_KEYS.PRODUCTS, 0);
      expect(isInvalid).toBe(false);
    });

    it('should clear cache entry', async () => {
      const testData = { id: 1, name: 'Test Product' };

      await saveToCache(CACHE_KEYS.PRODUCTS, testData);
      await clearCacheEntry(CACHE_KEYS.PRODUCTS);

      const loaded = await loadFromCache(CACHE_KEYS.PRODUCTS);
      expect(loaded).toBeNull();
    });

    it('should clear all cache', async () => {
      await saveToCache(CACHE_KEYS.PRODUCTS, { id: 1 });
      await saveToCache(CACHE_KEYS.VENDORS, { id: 2 });

      await clearAllCache();

      const products = await loadFromCache(CACHE_KEYS.PRODUCTS);
      const vendors = await loadFromCache(CACHE_KEYS.VENDORS);

      expect(products).toBeNull();
      expect(vendors).toBeNull();
    });
  });

  describe('Mutations Queue', () => {
    it('should queue a mutation', async () => {
      const mutation = {
        type: 'CREATE',
        endpoint: '/products',
        method: 'POST',
        payload: { name: 'New Product' },
      };

      const id = await queueMutation(mutation);

      expect(id).toBeDefined();
      expect(typeof id).toBe('number');
    });

    it('should get pending mutations', async () => {
      await queueMutation({
        type: 'CREATE',
        endpoint: '/products',
        method: 'POST',
        payload: { name: 'Product 1' },
      });

      await queueMutation({
        type: 'UPDATE',
        endpoint: '/products/1',
        method: 'PUT',
        payload: { name: 'Updated Product' },
      });

      const pending = await getPendingMutations();

      expect(pending).toHaveLength(2);
      expect(pending[0].status).toBe('pending');
      expect(pending[1].status).toBe('pending');
    });

    it('should update mutation status', async () => {
      const id = await queueMutation({
        type: 'CREATE',
        endpoint: '/products',
        method: 'POST',
        payload: { name: 'Product' },
      });

      await updateMutationStatus(id, 'completed');

      const pending = await getPendingMutations();
      expect(pending).toHaveLength(0);
    });

    it('should delete a mutation', async () => {
      const id = await queueMutation({
        type: 'CREATE',
        endpoint: '/products',
        method: 'POST',
        payload: { name: 'Product' },
      });

      await deleteMutation(id);

      const pending = await getPendingMutations();
      expect(pending).toHaveLength(0);
    });

    it('should clear completed mutations', async () => {
      const id1 = await queueMutation({
        type: 'CREATE',
        endpoint: '/products',
        method: 'POST',
        payload: { name: 'Product 1' },
      });

      const id2 = await queueMutation({
        type: 'CREATE',
        endpoint: '/products',
        method: 'POST',
        payload: { name: 'Product 2' },
      });

      await updateMutationStatus(id1, 'completed');
      await updateMutationStatus(id2, 'failed');

      const deletedCount = await clearCompletedMutations();

      expect(deletedCount).toBe(2);

      const pending = await getPendingMutations();
      expect(pending).toHaveLength(0);
    });
  });

  describe('Metadata', () => {
    it('should save and load metadata', async () => {
      const metadata = { lastSync: Date.now() };

      await saveMetadata('sync', metadata);
      const loaded = await loadMetadata('sync');

      expect(loaded).toEqual(metadata);
    });

    it('should return null for non-existent metadata', async () => {
      const loaded = await loadMetadata('non-existent');
      expect(loaded).toBeNull();
    });
  });

  describe('Statistics', () => {
    it('should return storage statistics', async () => {
      await saveToCache(CACHE_KEYS.PRODUCTS, { id: 1 });
      await saveToCache(CACHE_KEYS.VENDORS, { id: 2 });

      await queueMutation({
        type: 'CREATE',
        endpoint: '/products',
        method: 'POST',
        payload: {},
      });

      const stats = await getStorageStats();

      expect(stats.cacheEntries).toBe(2);
      expect(stats.totalMutations).toBe(1);
      expect(stats.pendingMutations).toBe(1);
      expect(stats.completedMutations).toBe(0);
    });
  });
});
