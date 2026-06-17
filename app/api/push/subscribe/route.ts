import { NextRequest, NextResponse } from 'next/server';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import path from 'path';
import { verifyToken } from '@/lib/auth';

interface PushSubscription {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
  user_id?: string;
  expirationTime?: number | null;
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
    mkdirSync(dir, { recursive: true });
  }
  writeFileSync(SUBSCRIPTIONS_FILE, JSON.stringify(subs, null, 2));
}

export async function POST(request: NextRequest) {
  try {
    const cookieStore = await request.cookies;
    const token = cookieStore.get('auth-token')?.value;
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    const payload = await verifyToken(token);
    if (!payload?.userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const sub: PushSubscription = await request.json();
    if (!sub.endpoint || !sub.keys?.p256dh || !sub.keys?.auth) {
      return NextResponse.json({ error: 'Invalid subscription' }, { status: 400 });
    }

    const userId = payload.userId;
    const subs = readSubscriptions();
    const existingIndex = subs.findIndex((s) => s.endpoint === sub.endpoint);

    if (existingIndex !== -1) {
      subs[existingIndex] = { ...sub, user_id: userId };
    } else {
      subs.push({ ...sub, user_id: userId });
    }

    writeSubscriptions(subs);
    return NextResponse.json({ status: 'subscribed' });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
