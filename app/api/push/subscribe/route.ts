import { NextRequest, NextResponse } from 'next/server';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import path from 'path';
import { verifyToken } from '@/lib/auth';

interface PushSubscription {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
  user_id?: string;
}

const SUBSCRIPTIONS_FILE = path.join(process.cwd(), 'data', 'push-subscriptions.json');

function readSubscriptions(): PushSubscription[] {
  if (!existsSync(SUBSCRIPTIONS_FILE)) return [];
  try {
    return JSON.parse(readFileSync(SUBSCRIPTIONS_FILE, 'utf-8'));
  } catch {
    return [];
  }
}

function writeSubscriptions(subs: PushSubscription[]) {
  const dir = path.dirname(SUBSCRIPTIONS_FILE);
  if (!existsSync(dir)) {
    const { mkdirSync } = require('fs');
    mkdirSync(dir, { recursive: true });
  }
  writeFileSync(SUBSCRIPTIONS_FILE, JSON.stringify(subs, null, 2));
}

export async function POST(request: NextRequest) {
  try {
    const sub: PushSubscription = await request.json();
    if (!sub.endpoint || !sub.keys?.p256dh || !sub.keys?.auth) {
      return NextResponse.json({ error: 'Invalid subscription' }, { status: 400 });
    }

    let userId: string | undefined;
    try {
      const cookieStore = await request.cookies;
      const token = cookieStore.get('auth-token')?.value;
      if (token) {
        const payload = await verifyToken(token);
        if (payload) userId = payload.userId;
      }
    } catch {}

    const subs = readSubscriptions();
    const exists = subs.some((s) => s.endpoint === sub.endpoint);
    if (!exists) {
      subs.push({ ...sub, user_id: userId });
      writeSubscriptions(subs);
    } else if (userId) {
      const idx = subs.findIndex((s) => s.endpoint === sub.endpoint);
      if (idx !== -1 && !subs[idx].user_id) {
        subs[idx].user_id = userId;
        writeSubscriptions(subs);
      }
    }

    return NextResponse.json({ status: 'subscribed' });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
