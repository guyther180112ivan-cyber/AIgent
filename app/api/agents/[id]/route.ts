import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@/modules/core/supabase/server';
import { AgentUpdate, Agent } from '@/types';

type Params = { params: Promise<{ id: string }> };

/** GET /api/agents/[id] */
export async function GET(_req: NextRequest, { params }: Params) {
  const { id } = await params;
  const supabase = await createClient();

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });
  }

  const { data: agent, error } = await supabase
    .from('agents')
    .select('*')
    .eq('id', id)
    .eq('user_id', user.id)
    .single();

  if (error) return NextResponse.json({ error: 'Агент не найден' }, { status: 404 });
  return NextResponse.json(agent as Agent);
}

/** PUT /api/agents/[id] */
export async function PUT(request: NextRequest, { params }: Params) {
  const { id } = await params;
  const supabase = await createClient();

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });
  }

  const body: AgentUpdate = await request.json();

  const { data: agent, error } = await supabase
    .from('agents')
    .update(body)
    .eq('id', id)
    .eq('user_id', user.id)
    .select()
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(agent as Agent);
}

/** DELETE /api/agents/[id] */
export async function DELETE(_req: NextRequest, { params }: Params) {
  const { id } = await params;
  const supabase = await createClient();

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json({ error: 'Не авторизован' }, { status: 401 });
  }

  const { error } = await supabase
    .from('agents')
    .delete()
    .eq('id', id)
    .eq('user_id', user.id);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return new NextResponse(null, { status: 204 });
}
