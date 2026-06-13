import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { verifyToken } from '@/lib/auth';
import { getTaskById, toggleTask } from '@/lib/scheduler';
import { getSchedulerService } from '@/lib/scheduler-service';

type Params = { params: Promise<{ id: string }> };

export async function POST(_request: NextRequest, { params }: Params) {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;
  if (!token) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });

  const payload = await verifyToken(token);
  if (!payload) return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });

  const { id } = await params;
  const task = getTaskById(id);
  if (!task || task.user_id !== payload.userId) {
    return NextResponse.json({ error: 'Задача не найдена' }, { status: 404 });
  }

  const updated = toggleTask(id);
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
