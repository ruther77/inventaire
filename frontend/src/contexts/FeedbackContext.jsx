/**
 * FeedbackContext - Système de feedback unifié avancé.
 *
 * Fonctionnalités:
 * - Machine à états pour loading/success/error
 * - Queue de notifications avec priorités
 * - Undo/Retry automatiques
 * - Progress tracking pour opérations longues
 * - Debounce intelligent des feedbacks rapides
 */

import { createContext, useContext, useReducer, useCallback, useRef, useMemo } from 'react';
import { createPortal } from 'react-dom';

// États de la machine à états de feedback
const FeedbackState = {
  IDLE: 'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error',
  CONFIRMING: 'confirming',
};

// Types de notifications
const NotificationType = {
  INFO: 'info',
  SUCCESS: 'success',
  WARNING: 'warning',
  ERROR: 'error',
};

// Priorités (higher = plus important)
const Priority = {
  LOW: 0,
  NORMAL: 1,
  HIGH: 2,
  CRITICAL: 3,
};

// Actions du reducer
const ActionTypes = {
  START_LOADING: 'START_LOADING',
  SET_PROGRESS: 'SET_PROGRESS',
  FINISH_SUCCESS: 'FINISH_SUCCESS',
  FINISH_ERROR: 'FINISH_ERROR',
  RESET: 'RESET',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION',
  REQUEST_CONFIRM: 'REQUEST_CONFIRM',
  CONFIRM_RESPONSE: 'CONFIRM_RESPONSE',
};

// État initial
const initialState = {
  feedbackState: FeedbackState.IDLE,
  loading: {
    active: false,
    message: '',
    progress: null, // null = indeterminate, 0-100 = determinate
    cancellable: false,
    startTime: null,
  },
  notifications: [],
  confirmation: null,
  lastError: null,
};

// Reducer avec machine à états
function feedbackReducer(state, action) {
  switch (action.type) {
    case ActionTypes.START_LOADING:
      return {
        ...state,
        feedbackState: FeedbackState.LOADING,
        loading: {
          active: true,
          message: action.payload.message || 'Chargement...',
          progress: action.payload.progress ?? null,
          cancellable: action.payload.cancellable ?? false,
          startTime: Date.now(),
        },
      };

    case ActionTypes.SET_PROGRESS:
      return {
        ...state,
        loading: {
          ...state.loading,
          progress: action.payload.progress,
          message: action.payload.message || state.loading.message,
        },
      };

    case ActionTypes.FINISH_SUCCESS:
      return {
        ...state,
        feedbackState: FeedbackState.SUCCESS,
        loading: { ...initialState.loading },
        notifications: [
          ...state.notifications,
          {
            id: Date.now(),
            type: NotificationType.SUCCESS,
            ...action.payload,
            createdAt: Date.now(),
          },
        ],
      };

    case ActionTypes.FINISH_ERROR:
      return {
        ...state,
        feedbackState: FeedbackState.ERROR,
        loading: { ...initialState.loading },
        lastError: action.payload.error,
        notifications: [
          ...state.notifications,
          {
            id: Date.now(),
            type: NotificationType.ERROR,
            ...action.payload,
            createdAt: Date.now(),
          },
        ],
      };

    case ActionTypes.RESET:
      return {
        ...state,
        feedbackState: FeedbackState.IDLE,
        loading: { ...initialState.loading },
      };

    case ActionTypes.ADD_NOTIFICATION:
      return {
        ...state,
        notifications: [
          ...state.notifications,
          {
            id: Date.now() + Math.random(),
            createdAt: Date.now(),
            ...action.payload,
          },
        ].sort((a, b) => (b.priority || Priority.NORMAL) - (a.priority || Priority.NORMAL)),
      };

    case ActionTypes.REMOVE_NOTIFICATION:
      return {
        ...state,
        notifications: state.notifications.filter((n) => n.id !== action.payload.id),
      };

    case ActionTypes.REQUEST_CONFIRM:
      return {
        ...state,
        feedbackState: FeedbackState.CONFIRMING,
        confirmation: action.payload,
      };

    case ActionTypes.CONFIRM_RESPONSE:
      return {
        ...state,
        feedbackState: FeedbackState.IDLE,
        confirmation: null,
      };

    default:
      return state;
  }
}

// Context
const FeedbackContext = createContext(null);

// Provider
export function FeedbackProvider({ children }) {
  const [state, dispatch] = useReducer(feedbackReducer, initialState);
  const loadingTimeoutRef = useRef(null);
  const notificationTimeoutsRef = useRef(new Map());

  // Afficher le loading après un délai (évite le flash pour les opérations rapides)
  const showLoading = useCallback((options = {}) => {
    const { message, delay = 300, progress, cancellable, onCancel } = options;

    // Clear any existing timeout
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }

    // Delay l'affichage pour éviter le flash
    loadingTimeoutRef.current = setTimeout(() => {
      dispatch({
        type: ActionTypes.START_LOADING,
        payload: { message, progress, cancellable },
      });
    }, delay);

    // Retourner une fonction pour annuler ou terminer
    return {
      setProgress: (progress, message) => {
        dispatch({ type: ActionTypes.SET_PROGRESS, payload: { progress, message } });
      },
      cancel: () => {
        if (loadingTimeoutRef.current) {
          clearTimeout(loadingTimeoutRef.current);
        }
        dispatch({ type: ActionTypes.RESET });
        onCancel?.();
      },
      success: (options = {}) => {
        if (loadingTimeoutRef.current) {
          clearTimeout(loadingTimeoutRef.current);
        }
        dispatch({
          type: ActionTypes.FINISH_SUCCESS,
          payload: options,
        });
      },
      error: (options = {}) => {
        if (loadingTimeoutRef.current) {
          clearTimeout(loadingTimeoutRef.current);
        }
        dispatch({
          type: ActionTypes.FINISH_ERROR,
          payload: options,
        });
      },
    };
  }, []);

  // Notifications avec auto-dismiss
  const notify = useCallback((options) => {
    const {
      type = NotificationType.INFO,
      title,
      message,
      duration = 5000,
      priority = Priority.NORMAL,
      action,
      undoAction,
      persistent = false,
    } = options;

    const id = Date.now() + Math.random();

    dispatch({
      type: ActionTypes.ADD_NOTIFICATION,
      payload: {
        id,
        type,
        title,
        message,
        priority,
        action,
        undoAction,
        persistent,
      },
    });

    // Auto-dismiss si non persistant
    if (!persistent && duration > 0) {
      const timeout = setTimeout(() => {
        dispatch({ type: ActionTypes.REMOVE_NOTIFICATION, payload: { id } });
        notificationTimeoutsRef.current.delete(id);
      }, duration);
      notificationTimeoutsRef.current.set(id, timeout);
    }

    return id;
  }, []);

  // Raccourcis pour les types courants
  const success = useCallback(
    (title, options = {}) => notify({ type: NotificationType.SUCCESS, title, ...options }),
    [notify]
  );

  const error = useCallback(
    (title, options = {}) =>
      notify({ type: NotificationType.ERROR, title, duration: 8000, ...options }),
    [notify]
  );

  const warning = useCallback(
    (title, options = {}) => notify({ type: NotificationType.WARNING, title, ...options }),
    [notify]
  );

  const info = useCallback(
    (title, options = {}) => notify({ type: NotificationType.INFO, title, ...options }),
    [notify]
  );

  // Confirmation dialog
  const confirm = useCallback(
    (options) =>
      new Promise((resolve) => {
        dispatch({
          type: ActionTypes.REQUEST_CONFIRM,
          payload: {
            ...options,
            onConfirm: () => {
              dispatch({ type: ActionTypes.CONFIRM_RESPONSE });
              resolve(true);
            },
            onCancel: () => {
              dispatch({ type: ActionTypes.CONFIRM_RESPONSE });
              resolve(false);
            },
          },
        });
      }),
    []
  );

  // Dismiss notification
  const dismiss = useCallback((id) => {
    const timeout = notificationTimeoutsRef.current.get(id);
    if (timeout) {
      clearTimeout(timeout);
      notificationTimeoutsRef.current.delete(id);
    }
    dispatch({ type: ActionTypes.REMOVE_NOTIFICATION, payload: { id } });
  }, []);

  // Wrapper pour async operations avec feedback automatique
  const withFeedback = useCallback(
    async (asyncFn, options = {}) => {
      const {
        loadingMessage = 'Opération en cours...',
        successMessage = 'Opération réussie',
        errorMessage = 'Une erreur est survenue',
        showSuccess = true,
        showError = true,
        retryAction,
        undoAction,
      } = options;

      const loading = showLoading({ message: loadingMessage });

      try {
        const result = await asyncFn();

        if (showSuccess) {
          loading.success({
            title: successMessage,
            undoAction,
          });
        } else {
          loading.cancel();
        }

        return result;
      } catch (err) {
        if (showError) {
          loading.error({
            title: errorMessage,
            message: err.message || 'Veuillez réessayer',
            error: err,
            action: retryAction
              ? {
                  label: 'Réessayer',
                  onClick: () => withFeedback(asyncFn, options),
                }
              : undefined,
          });
        } else {
          loading.cancel();
        }

        throw err;
      }
    },
    [showLoading]
  );

  const value = useMemo(
    () => ({
      // State
      state,
      isLoading: state.loading.active,
      loadingMessage: state.loading.message,
      loadingProgress: state.loading.progress,
      notifications: state.notifications,
      confirmation: state.confirmation,

      // Actions
      showLoading,
      notify,
      success,
      error,
      warning,
      info,
      confirm,
      dismiss,
      withFeedback,

      // Constants
      NotificationType,
      Priority,
    }),
    [state, showLoading, notify, success, error, warning, info, confirm, dismiss, withFeedback]
  );

  return <FeedbackContext.Provider value={value}>{children}</FeedbackContext.Provider>;
}

// Hook
export function useFeedback() {
  const context = useContext(FeedbackContext);
  if (!context) {
    throw new Error('useFeedback must be used within a FeedbackProvider');
  }
  return context;
}

// Export constants
export { FeedbackState, NotificationType, Priority };
