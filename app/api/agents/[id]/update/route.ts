import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { verifyToken } from '@/lib/auth';
import { getAgentById, updateAgent } from '@/lib/agents';

type Params = { params: Promise<{ id: string }> };

export async function PATCH(request: NextRequest, { params }: Params) {
  const { id } = await params;
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;

  if (!token) {
    return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });
  }

  const payload = await verifyToken(token);
  if (!payload) {
    return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });
  }

  const agent = getAgentById(id);
  if (!agent || agent.user_id !== payload.userId) {
    return NextResponse.json({ error: 'Агент не найден' }, { status: 404 });
  }

  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Неверный JSON' }, { status: 400 });
  }

  const allowed = ['model', 'name', 'description', 'system_prompt', 'is_active'];
  const updates: Record<string, unknown> = {};
  for (const key of allowed) {
    if (key in body) updates[key] = body[key];
  }

  if (Object.keys(updates).length === 0) {
    return NextResponse.json({ error: 'Нет полей для обновления' }, { status: 400 });
  }

  const updated = updateAgent(id, updates);
  return NextResponse.json(updated);
}
