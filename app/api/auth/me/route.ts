import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { verifyToken, findUserById } from '@/lib/auth';

export async function GET() {
  try {
    const cookieStore = await cookies();
    const token = cookieStore.get('auth-token')?.value;

    if (!token) {
      return NextResponse.json({ user: null });
    }

    const payload = await verifyToken(token);

    if (!payload) {
      return NextResponse.json({ user: null });
    }

    const user = findUserById(payload.userId);

    if (!user) {
      return NextResponse.json({ user: null });
    }

    return NextResponse.json({ user: { id: user.id, username: user.username } });
  } catch {
    return NextResponse.json({ user: null });
  }
}
