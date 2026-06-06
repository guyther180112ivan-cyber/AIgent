import { NextRequest, NextResponse } from 'next/server';
import { readFileSync, existsSync } from 'fs';
import path from 'path';
import webpush from 'web-push';

const SUBSCRIPTIONS_FILE = path.join(process.cwd(), 'data', 'push-subscriptions.json');

const vapidPublicKey = process.env.VAPID_PUBLIC_KEY || '';
const vapidPrivateKey = process.env.VAPID_PRIVATE_KEY || '';

if (vapidPublicKey && vapidPrivateKey) {
  webpush.setVapidDetails(
    'mailto:support@aigent.ai',
    vapidPublicKey,
    vapidPrivateKey
  );
}

interface PushSubscription {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

function readSubscriptions(): PushSubscription[] {
  if (!existsSync(SUBSCRIPTIONS_FILE)) return [];
  try {
    return JSON.parse(readFileSync(SUBSCRIPTIONS_FILE, 'utf-8'));
  } catch {
    return [];
  }
}

export async function POST(request: NextRequest) {
  try {
    const { title, body, data } = await request.json();
    const subs = readSubscriptions();

    if (subs.length === 0) {
      return NextResponse.json({ sent: 0, total: 0 });
    }

    let sent = 0;

    await Promise.allSettled(
      subs.map(async (sub) => {
        try {
          await webpush.sendNotification(
            sub as webpush.PushSubscription,
            JSON.stringify({ title, body, data }),
            { TTL: 86400 }
          );
          sent++;
        } catch (err: any) {
          if (err.statusCode === 410 || err.statusCode === 404) {
            // Subscription expired — remove it on next read
          }
        }
      })
    );

    return NextResponse.json({ sent, total: subs.length });
  } catch {
    return NextResponse.json({ error: 'Failed to send notifications' }, { status: 500 });
  }
}
