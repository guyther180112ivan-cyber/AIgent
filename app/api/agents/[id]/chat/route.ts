import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { verifyToken, findUserById } from '@/lib/auth';
import { getAgentById } from '@/lib/agents';
import { createConversation, getConversationById, updateConversation, getConversationsByAgentId } from '@/lib/conversations';
import { createMessage, getMessagesByConversationId } from '@/lib/messages';
import { AgentRuntime } from '@/modules/core/agent-runtime';
import { ContextMemoryModule } from '@/modules/memory/context-memory';

type Params = { params: Promise<{ id: string }> };

export async function GET(request: NextRequest, { params }: Params) {
  const { id: agentId } = await params;
  const conversationId = request.nextUrl.searchParams.get('conversation_id');

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

  if (conversationId) {
    const conv = getConversationById(conversationId);
    if (!conv || conv.agent_id !== agentId) {
      return NextResponse.json({ error: 'Разговор не найден' }, { status: 404 });
    }
    const messages = getMessagesByConversationId(conversationId);
    return NextResponse.json(messages);
  }

  const conversations = getConversationsByAgentId(agentId, user.id);
  return NextResponse.json(conversations);
}

export async function POST(request: NextRequest, { params }: Params) {
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

  const body = await request.json() as { message: string; conversation_id?: string; file_contents?: { name: string; content: string }[] };
  if (!body.message?.trim()) {
    return NextResponse.json({ error: 'message обязателен' }, { status: 400 });
  }

  const agent = getAgentById(agentId);
  if (!agent || agent.user_id !== user.id) {
    return NextResponse.json({ error: 'Агент не найден' }, { status: 404 });
  }

  let conversationId = body.conversation_id;
  if (!conversationId) {
    const conv = createConversation({
      agent_id: agentId,
      user_id: user.id,
      title: body.message.substring(0, 50),
    });
    conversationId = conv.id;
  } else {
    updateConversation(conversationId, {});
  }

  createMessage({
    conversation_id: conversationId,
    role: 'user',
    content: body.message,
  });

  const fileBlock = (body.file_contents || [])
    .map(f => {
      if (f.content) {
        return `\n\n[Прикреплённый файл: ${f.name}]\n${f.content}`;
      }
      return `\n\n[Прикреплённый файл: ${f.name} — содержимое недоступно]`;
    })
    .join('');

  const systemPrompt = (agent.system_prompt || '') + fileBlock;

  const runtime = new AgentRuntime();

  try {
    const ctx = {
      agentId,
      userId: user.id,
      conversationId,
      messages: [{ role: 'user' as const, content: body.message }],
      systemPrompt,
      metadata: { model: agent.model },
    };

    const contextModule = new ContextMemoryModule();
    const enrichedCtx = await contextModule.onBeforeMessage(ctx);

    const response = await runtime.processMessage(enrichedCtx);

    createMessage({
      conversation_id: conversationId,
      role: 'assistant',
      content: response.content,
    });

    updateConversation(conversationId, {});

    return NextResponse.json({
      content: response.content,
      conversation_id: conversationId,
      model: response.model,
    });
  } catch (err) {
    console.error('[chat/route] Ошибка:', err);
    return NextResponse.json(
      { error: 'Ошибка обработки сообщения' },
      { status: 500 }
    );
  }
}
