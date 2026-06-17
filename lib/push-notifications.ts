import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import path from 'path';
import { PushNotificationPayload } from '@/types';

const SUBSCRIPTIONS_FILE = path.join(process.cwd(), 'data', 'push-subscriptions.json');

interface StoredPushSubscription {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
  user_id?: string;
  expirationTime?: number | null;
}

function readSubscriptions(): StoredPushSubscription[] {
  if (!existsSync(SUBSCRIPTIONS_FILE)) return [];
  try {
    return JSON.parse(readFileSync(SUBSCRIPTIONS_FILE, 'utf-8'));
  } catch {
    return [];
  }
}

function writeSubscriptions(subs: StoredPushSubscription[]) {
  const dir = path.dirname(SUBSCRIPTIONS_FILE);
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
  writeFileSync(SUBSCRIPTIONS_FILE, JSON.stringify(subs, null, 2));
}

export async function sendPushNotificationToUser(
  userId: string,
  payload: PushNotificationPayload
): Promise<{ sent: number; total: number }> {
  if (!userId) {
    return { sent: 0, total: 0 };
  }

  const vapidPublicKey =
    process.env.VAPID_PUBLIC_KEY || process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || '';
  const vapidPrivateKey = process.env.VAPID_PRIVATE_KEY || '';

  if (!vapidPublicKey || !vapidPrivateKey) {
    console.warn('[Push] VAPID keys are not configured');
    return { sent: 0, total: 0 };
  }

  let subs = readSubscriptions();
  const userSubs = subs.filter((s) => s.user_id === userId);

  if (userSubs.length === 0) {
    return { sent: 0, total: 0 };
  }

  const webpush = await import('web-push');
  webpush.default.setVapidDetails(
    `mailto:${process.env.VAPID_EMAIL || 'admin@example.com'}`,
    vapidPublicKey,
    vapidPrivateKey
  );

  const notificationPayload = JSON.stringify({
    title: payload.title,
    body: payload.body || '',
    icon: payload.icon || '/icons/icon-192.png',
    badge: payload.badge || '/icons/icon-192.png',
    data: payload.data || { url: '/' },
  });

  const expiredEndpoints: string[] = [];
  let sent = 0;

  await Promise.allSettled(
    userSubs.map(async (sub) => {
      try {
        await webpush.default.sendNotification(
          { endpoint: sub.endpoint, keys: sub.keys, expirationTime: sub.expirationTime },
          notificationPayload
        );
        sent++;
      } catch (err) {
        const error = err as { statusCode?: number; message?: string };
        if (error.statusCode === 410 || error.statusCode === 404) {
          expiredEndpoints.push(sub.endpoint);
        } else {
          console.error('[Push] Failed to send notification to user', userId, error.message || err);
        }
      }
    })
  );

  if (expiredEndpoints.length > 0) {
    subs = subs.filter((s) => !expiredEndpoints.includes(s.endpoint));
    writeSubscriptions(subs);
  }

  return { sent, total: userSubs.length };
}
