import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  getErrorType,
  isRetryableError,
  useOnlineStatus,
  useManualRetry,
  createQueryOptions,
  errorMessages,
  defaultQueryConfig,
  defaultMutationConfig,
} from './useQueryConfig';

describe('getErrorType', () => {
  it('returns "unknown" for null/undefined errors', () => {
    expect(getErrorType(null)).toBe('unknown');
    expect(getErrorType(undefined)).toBe('unknown');
  });

  it('returns "network" for network errors', () => {
    expect(getErrorType({ message: 'Network error' })).toBe('network');
    expect(getErrorType({ message: 'fetch failed' })).toBe('network');
  });

  it('returns "timeout" for timeout errors', () => {
    expect(getErrorType({ message: 'Request timeout' })).toBe('timeout');
  });

  it('returns "auth" for 401 errors', () => {
    expect(getErrorType({ response: { status: 401 } })).toBe('auth');
    expect(getErrorType({ status: 401 })).toBe('auth');
  });

  it('returns "permission" for 403 errors', () => {
    expect(getErrorType({ response: { status: 403 } })).toBe('permission');
    expect(getErrorType({ status: 403 })).toBe('permission');
  });

  it('returns "not_found" for 404 errors', () => {
    expect(getErrorType({ response: { status: 404 } })).toBe('not_found');
  });

  it('returns "validation" for 400/422 errors', () => {
    expect(getErrorType({ response: { status: 400 } })).toBe('validation');
    expect(getErrorType({ response: { status: 422 } })).toBe('validation');
  });

  it('returns "server" for 5xx errors', () => {
    expect(getErrorType({ response: { status: 500 } })).toBe('server');
    expect(getErrorType({ response: { status: 502 } })).toBe('server');
    expect(getErrorType({ response: { status: 503 } })).toBe('server');
  });
});

describe('isRetryableError', () => {
  it('returns true for network errors', () => {
    expect(isRetryableError({ message: 'Network error' })).toBe(true);
  });

  it('returns true for timeout errors', () => {
    expect(isRetryableError({ message: 'timeout' })).toBe(true);
  });

  it('returns true for server errors', () => {
    expect(isRetryableError({ response: { status: 500 } })).toBe(true);
  });

  it('returns true for unknown errors', () => {
    expect(isRetryableError({ message: 'some error' })).toBe(true);
  });

  it('returns false for auth errors', () => {
    expect(isRetryableError({ response: { status: 401 } })).toBe(false);
  });

  it('returns false for permission errors', () => {
    expect(isRetryableError({ response: { status: 403 } })).toBe(false);
  });

  it('returns false for not_found errors', () => {
    expect(isRetryableError({ response: { status: 404 } })).toBe(false);
  });

  it('returns false for validation errors', () => {
    expect(isRetryableError({ response: { status: 422 } })).toBe(false);
  });
});

describe('useOnlineStatus', () => {
  const originalNavigator = window.navigator;

  beforeEach(() => {
    Object.defineProperty(window, 'navigator', {
      value: { onLine: true },
      writable: true,
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'navigator', {
      value: originalNavigator,
      writable: true,
    });
  });

  it('returns true when online', () => {
    const { result } = renderHook(() => useOnlineStatus());
    expect(result.current).toBe(true);
  });

  it('updates when going offline', async () => {
    const { result } = renderHook(() => useOnlineStatus());

    act(() => {
      Object.defineProperty(window.navigator, 'onLine', { value: false });
      window.dispatchEvent(new Event('offline'));
    });

    await waitFor(() => {
      expect(result.current).toBe(false);
    });
  });

  it('updates when going back online', async () => {
    Object.defineProperty(window.navigator, 'onLine', { value: false });
    const { result } = renderHook(() => useOnlineStatus());

    act(() => {
      Object.defineProperty(window.navigator, 'onLine', { value: true });
      window.dispatchEvent(new Event('online'));
    });

    await waitFor(() => {
      expect(result.current).toBe(true);
    });
  });
});

describe('useManualRetry', () => {
  it('tracks retry count', async () => {
    const onRetry = vi.fn().mockRejectedValue(new Error('Failed'));

    const { result } = renderHook(() => useManualRetry(onRetry, 3));

    expect(result.current.retryCount).toBe(0);
    expect(result.current.canRetry).toBe(true);
    expect(result.current.retriesLeft).toBe(3);

    await act(async () => {
      await result.current.retry();
    });

    expect(result.current.retryCount).toBe(1);
    expect(result.current.retriesLeft).toBe(2);
  });

  it('resets retry count on success', async () => {
    const onRetry = vi.fn().mockResolvedValue();

    const { result } = renderHook(() => useManualRetry(onRetry, 3));

    await act(async () => {
      await result.current.retry();
    });

    expect(result.current.retryCount).toBe(0);
    expect(result.current.canRetry).toBe(true);
  });

  it('stops retrying after max retries', async () => {
    const onRetry = vi.fn().mockRejectedValue(new Error('Failed'));

    const { result } = renderHook(() => useManualRetry(onRetry, 2));

    // First retry
    await act(async () => {
      await result.current.retry();
    });
    // Second retry
    await act(async () => {
      await result.current.retry();
    });

    expect(result.current.canRetry).toBe(false);
    expect(result.current.retriesLeft).toBe(0);
  });

  it('resets state manually', async () => {
    const onRetry = vi.fn().mockRejectedValue(new Error('Failed'));

    const { result } = renderHook(() => useManualRetry(onRetry, 3));

    await act(async () => {
      await result.current.retry();
    });

    expect(result.current.retryCount).toBe(1);

    act(() => {
      result.current.reset();
    });

    expect(result.current.retryCount).toBe(0);
    expect(result.current.canRetry).toBe(true);
  });
});

describe('createQueryOptions', () => {
  it('returns default config when no options provided', () => {
    const options = createQueryOptions();
    expect(options.staleTime).toBe(defaultQueryConfig.staleTime);
    expect(options.gcTime).toBe(defaultQueryConfig.gcTime);
  });

  it('enables retry by default', () => {
    const options = createQueryOptions();
    expect(typeof options.retry).toBe('function');
  });

  it('disables retry when enableRetry is false', () => {
    const options = createQueryOptions({ enableRetry: false });
    expect(options.retry).toBe(false);
  });

  it('retry function returns false for auth errors', () => {
    const options = createQueryOptions();
    const authError = { response: { status: 401 } };
    expect(options.retry(0, authError)).toBe(false);
  });

  it('retry function returns false for permission errors', () => {
    const options = createQueryOptions();
    const permissionError = { response: { status: 403 } };
    expect(options.retry(0, permissionError)).toBe(false);
  });

  it('retry function returns true for server errors by default', () => {
    const options = createQueryOptions();
    const serverError = { response: { status: 500 } };
    expect(options.retry(0, serverError)).toBe(true);
  });

  it('retry function returns false after max retries', () => {
    const options = createQueryOptions({ maxRetries: 2 });
    const serverError = { response: { status: 500 } };
    expect(options.retry(2, serverError)).toBe(false);
  });

  it('respects retryOnNetworkError option', () => {
    const options = createQueryOptions({ retryOnNetworkError: false });
    const networkError = { message: 'network error' };
    expect(options.retry(0, networkError)).toBe(false);
  });

  it('respects retryOnServerError option', () => {
    const options = createQueryOptions({ retryOnServerError: false });
    const serverError = { response: { status: 500 } };
    expect(options.retry(0, serverError)).toBe(false);
  });
});

describe('errorMessages', () => {
  it('has all required error types', () => {
    const expectedTypes = [
      'network',
      'timeout',
      'auth',
      'permission',
      'not_found',
      'validation',
      'server',
      'unknown',
    ];

    expectedTypes.forEach((type) => {
      expect(errorMessages[type]).toBeDefined();
      expect(errorMessages[type].title).toBeDefined();
      expect(errorMessages[type].description).toBeDefined();
      expect(typeof errorMessages[type].canRetry).toBe('boolean');
    });
  });

  it('marks network errors as retryable', () => {
    expect(errorMessages.network.canRetry).toBe(true);
  });

  it('marks timeout errors as retryable', () => {
    expect(errorMessages.timeout.canRetry).toBe(true);
  });

  it('marks server errors as retryable', () => {
    expect(errorMessages.server.canRetry).toBe(true);
  });

  it('marks auth errors as not retryable', () => {
    expect(errorMessages.auth.canRetry).toBe(false);
  });

  it('marks permission errors as not retryable', () => {
    expect(errorMessages.permission.canRetry).toBe(false);
  });

  it('auth error has login action', () => {
    expect(errorMessages.auth.action).toBeDefined();
    expect(errorMessages.auth.action.href).toBe('/login');
  });
});

describe('defaultQueryConfig', () => {
  it('has reasonable staleTime', () => {
    expect(defaultQueryConfig.staleTime).toBeGreaterThan(0);
    expect(defaultQueryConfig.staleTime).toBe(5 * 60 * 1000); // 5 minutes
  });

  it('has reasonable gcTime', () => {
    expect(defaultQueryConfig.gcTime).toBeGreaterThan(0);
    expect(defaultQueryConfig.gcTime).toBe(30 * 60 * 1000); // 30 minutes
  });

  it('has retry count of 3', () => {
    expect(defaultQueryConfig.retry).toBe(3);
  });

  it('has exponential retryDelay function', () => {
    expect(typeof defaultQueryConfig.retryDelay).toBe('function');
    expect(defaultQueryConfig.retryDelay(0)).toBe(1000); // 2^0 * 1000
    expect(defaultQueryConfig.retryDelay(1)).toBe(2000); // 2^1 * 1000
    expect(defaultQueryConfig.retryDelay(2)).toBe(4000); // 2^2 * 1000
  });

  it('caps retryDelay at 30 seconds', () => {
    expect(defaultQueryConfig.retryDelay(10)).toBe(30000);
  });

  it('refetches on reconnect', () => {
    expect(defaultQueryConfig.refetchOnReconnect).toBe(true);
  });

  it('does not refetch on window focus', () => {
    expect(defaultQueryConfig.refetchOnWindowFocus).toBe(false);
  });
});

describe('defaultMutationConfig', () => {
  it('has retry count of 1', () => {
    expect(defaultMutationConfig.retry).toBe(1);
  });

  it('has retryDelay of 1 second', () => {
    expect(defaultMutationConfig.retryDelay).toBe(1000);
  });
});
