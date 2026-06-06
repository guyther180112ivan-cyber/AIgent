import { NextRequest, NextResponse } from 'next/server';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import path from 'path';

const SUBSCRIPTIONS_FILE = path.join(process.cwd(), 'data', 'push-subscriptions.json');

function readSubscriptions(): { endpoint: string; keys: { p256dh: string; auth: string } }[] {
  if (!existsSync(SUBSCRIPTIONS_FILE)) return [];
  try {
    return JSON.parse(readFileSync(SUBSCRIPTIONS_FILE, 'utf-8'));
  } catch {
    return [];
  }
}

function writeSubscriptions(subs: any[]) {
  const dir = path.dirname(SUBSCRIPTIONS_FILE);
  if (!existsSync(dir)) {
    const { mkdirSync } = require('fs');
    mkdirSync(dir, { recursive: true });
  }
  writeFileSync(SUBSCRIPTIONS_FILE, JSON.stringify(subs, null, 2));
}

export async function POST(request: NextRequest) {
  try {
    const { endpoint } = await request.json();
    if (!endpoint) {
      return NextResponse.json({ error: 'Missing endpoint' }, { status: 400 });
    }

    const subs = readSubscriptions();
    const filtered = subs.filter((s) => s.endpoint !== endpoint);

    if (filtered.length !== subs.length) {
      writeSubscriptions(filtered);
    }

    return NextResponse.json({ status: 'unsubscribed' });
  } catch {
    return NextResponse.json({ status: 'error' }, { status: 500 });
  }
}
