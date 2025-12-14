import { Toaster, toast } from 'sonner';

export function notifySuccess(message) {
  toast.success(message);
}

export function notifyError(message) {
  toast.error(message);
}

export default function ToastManager() {
  return (
    <Toaster
      position="top-right"
      toastOptions={{
        style: { background: '#0f172a', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.08)' },
      }}
    />
  );
}
