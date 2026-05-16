import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { verifyToken, findUserById } from '@/lib/auth';
import { getAgentById } from '@/lib/agents';
import { getConversationsByAgentId } from '@/lib/conversations';

type Params = { params: Promise<{ id: string }> };

export async function GET(request: NextRequest, { params }: Params) {
  const { id: agentId } = await params;
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;

  if (!token) {
    return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });
  }

  const payload = await verifyToken(token);
  if (!payload) {
    return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });
  }

  const user = findUserById(payload.userId);
  if (!user) {
    return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });
  }

  const agent = getAgentById(agentId);
  if (!agent || agent.user_id !== user.id) {
    return NextResponse.json({ error: 'Агент не найден' }, { status: 404 });
  }

  const conversations = getConversationsByAgentId(agentId, user.id);
  return NextResponse.json(conversations);
}