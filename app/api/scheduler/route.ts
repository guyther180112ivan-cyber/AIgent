import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { verifyToken } from '@/lib/auth';
import { getTasksByUserId, createTask } from '@/lib/scheduler';
import { getAgentById } from '@/lib/agents';
import { getSchedulerService } from '@/lib/scheduler-service';

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;
  if (!token) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });

  const payload = await verifyToken(token);
  if (!payload) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });

  const tasks = getTasksByUserId(payload.userId);
  return NextResponse.json(tasks);
}

export async function POST(request: NextRequest) {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;
  if (!token) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });

  const payload = await verifyToken(token);
  if (!payload) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });

  const body = await request.json();
  if (!body.name?.trim() || !body.agent_id || !body.prompt?.trim() || !body.cron_expr?.trim()) {
    return NextResponse.json({ error: 'name, agent_id, prompt и cron_expr обязательны' }, { status: 400 });
  }

  const agent = getAgentById(body.agent_id);
  if (!agent || agent.user_id !== payload.userId) {
    return NextResponse.json({ error: 'Агент не найден' }, { status: 404 });
  }

  const task = createTask({
    agent_id: body.agent_id,
    user_id: payload.userId,
    name: body.name,
    description: body.description,
    prompt: body.prompt,
    cron_expr: body.cron_expr,
    preset: body.preset || 'custom',
    schedule_time: body.schedule_time,
    schedule_day: body.schedule_day,
  });

  const service = getSchedulerService();
  service.registerJob(task);

  return NextResponse.json(task, { status: 201 });
}
