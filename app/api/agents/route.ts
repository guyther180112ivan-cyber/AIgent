import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { verifyToken } from '@/lib/auth';
import { getAgentsByUserId, createAgent } from '@/lib/agents';

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;

  if (!token) {
    return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });
  }

  const payload = await verifyToken(token);
  if (!payload) {
    return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });
  }

  const agents = getAgentsByUserId(payload.userId);
  return NextResponse.json(agents);
}

export async function POST(request: NextRequest) {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;

  if (!token) {
    return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });
  }

  const payload = await verifyToken(token);
  if (!payload) {
    return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });
  }

  let body: Record<string, string>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Неверный JSON' }, { status: 400 });
  }

  if (!body.name || !body.system_prompt) {
    return NextResponse.json(
      { error: 'name и system_prompt обязательны' },
      { status: 400 }
    );
  }

  const agent = createAgent({
    user_id: payload.userId,
    name: body.name,
    description: body.description || '',
    system_prompt: body.system_prompt,
    model: body.model || 'qwen/qwen3-coder:free',
    is_active: true,
  });

  return NextResponse.json(agent, { status: 201 });
}
