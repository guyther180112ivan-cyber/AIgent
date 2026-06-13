import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { verifyToken } from '@/lib/auth';
import { getTaskById, updateTask, deleteTask } from '@/lib/scheduler';
import { getAgentById } from '@/lib/agents';
import { getSchedulerService } from '@/lib/scheduler-service';

type Params = { params: Promise<{ id: string }> };

async function authCheck() {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;
  if (!token) return { error: 'Не авторизован' };
  const payload = await verifyToken(token);
  if (!payload) return { error: 'Не авторизован' };
  return { userId: payload.userId };
}

export async function GET(_request: NextRequest, { params }: Params) {
  const auth = await authCheck();
  if ('error' in auth) return NextResponse.json(auth, { status: 401 });

  const { id } = await params;
  const task = getTaskById(id);
  if (!task || task.user_id !== auth.userId) {
    return NextResponse.json({ error: 'Задача не найдена' }, { status: 404 });
  }
  return NextResponse.json(task);
}

export async function PUT(request: NextRequest, { params }: Params) {
  const auth = await authCheck();
  if ('error' in auth) return NextResponse.json(auth, { status: 401 });

  const { id } = await params;
  const task = getTaskById(id);
  if (!task || task.user_id !== auth.userId) {
    return NextResponse.json({ error: 'Задача не найдена' }, { status: 404 });
  }

  const body = await request.json();
  const updated = updateTask(id, {
    name: body.name,
    description: body.description,
    prompt: body.prompt,
    cron_expr: body.cron_expr,
    preset: body.preset,
    schedule_time: body.schedule_time,
    schedule_day: body.schedule_day,
  });

  if (updated) {
    const service = getSchedulerService();
    if (updated.is_active) {
      service.registerJob(updated);
    } else {
      service.removeJob(updated.id);
    }
  }

  return NextResponse.json(updated);
}

export async function DELETE(_request: NextRequest, { params }: Params) {
  const auth = await authCheck();
  if ('error' in auth) return NextResponse.json(auth, { status: 401 });

  const { id } = await params;
  const task = getTaskById(id);
  if (!task || task.user_id !== auth.userId) {
    return NextResponse.json({ error: 'Задача не найдена' }, { status: 404 });
  }

  deleteTask(id);
  const service = getSchedulerService();
  service.removeJob(id);
  return NextResponse.json({ ok: true });
}
