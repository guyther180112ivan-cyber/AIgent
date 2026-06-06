import { NextRequest, NextResponse } from 'next/server';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import path from 'path';

interface PushSubscription {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
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

    const subs = readSubscriptions();
    const exists = subs.some((s) => s.endpoint === sub.endpoint);
    if (!exists) {
      subs.push(sub);
      writeSubscriptions(subs);
    }

    return NextResponse.json({ status: 'subscribed' });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
