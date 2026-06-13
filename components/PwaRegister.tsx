'use client';

import { useEffect, useState } from 'react';

const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || '';

export function PwaRegister() {
  const [deferredPrompt, setDeferredPrompt] = useState<Event | null>(null);
  const [showInstall, setShowInstall] = useState(false);
  const [isInstalled, setIsInstalled] = useState(true);
  const [pushSupported, setPushSupported] = useState(false);
  const [pushEnabled, setPushEnabled] = useState(false);

  useEffect(() => {
    if (window.matchMedia('(display-mode: standalone)').matches || (window.navigator as any).standalone === true) {
      setIsInstalled(true);
      return;
    }

    setIsInstalled(false);

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }

    if ('PushManager' in window) {
      setPushSupported(true);
      navigator.serviceWorker.ready.then((reg) => {
        reg.pushManager.getSubscription().then((sub) => {
          if (sub) setPushEnabled(true);
        });
      });
    }

    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstall(true);
    };

    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    (deferredPrompt as any).prompt();
    const result = await (deferredPrompt as any).userChoice;
    if (result.outcome === 'accepted') {
      setShowInstall(false);
      setIsInstalled(true);
    }
    setDeferredPrompt(null);
  };

  const handleDismiss = () => {
    setShowInstall(false);
    sessionStorage.setItem('pwa-install-dismissed', '1');
  };

  const subscribeToPush = async () => {
    try {
      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY) as BufferSource,
      });

      await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sub.toJSON()),
      });
      setPushEnabled(true);
    } catch (e) {
      console.error('Push subscription failed:', e);
    }
  };

  if (isInstalled) return null;
  if (!showInstall && !pushSupported) return null;

  return (
    <>
      {showInstall && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-blue-600 text-white px-4 py-3 flex items-center justify-between shadow-lg md:bottom-4 md:left-auto md:right-4 md:top-auto md:max-w-sm md:rounded-lg">
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-sm truncate">Установить AIgent на экран</span>
            <button
              onClick={handleInstall}
              className="bg-white text-blue-600 px-3 py-1 rounded text-sm font-medium shrink-0 hover:bg-blue-50"
            >
              Установить
            </button>
          </div>
          <button
            onClick={handleDismiss}
            className="text-blue-200 hover:text-white ml-2 shrink-0 text-lg leading-none"
            aria-label="Закрыть"
          >
            ✕
          </button>
        </div>
      )}
      {pushSupported && !pushEnabled && !showInstall && (
        <button
          onClick={subscribeToPush}
          className="fixed bottom-4 left-4 z-50 bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded-lg shadow-lg text-xs"
        >
          🔔 Уведомления
        </button>
      )}
    </>
  );
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const output = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    output[i] = rawData.charCodeAt(i);
  }
  return output;
}
