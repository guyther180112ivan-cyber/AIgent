import { cookies } from 'next/headers';
import { verifyToken } from '@/lib/auth';
import { getAgentsByUserId } from '@/lib/agents';
import Link from 'next/link';
import { Bot, Plus } from 'lucide-react';
import type { Agent } from '@/lib/agents';

export default async function AgentsPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth-token')?.value;
  const payload = token ? await verifyToken(token) : null;

  const agents: Agent[] = payload ? getAgentsByUserId(payload.userId) : [];

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Мои агенты</h1>
          <p className="text-gray-400 text-sm mt-1">
            Создавайте и управляйте AI агентами
          </p>
        </div>
        <Link
          href="/agents/new"
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition shadow-lg shadow-indigo-500/20"
        >
          <Plus className="w-4 h-4" />
          Новый агент
        </Link>
      </div>

      {/* Grid */}
      {agents && agents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent: Agent) => (
            <Link
              key={agent.id}
              href={`/agents/${agent.id}`}
              className="group bg-gray-900 border border-gray-800 hover:border-indigo-500/50 rounded-2xl p-6 transition-all hover:shadow-lg hover:shadow-indigo-500/10"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-indigo-600/20 border border-indigo-500/30 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Bot className="w-6 h-6 text-indigo-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-white group-hover:text-indigo-300 transition truncate">
                    {agent.name}
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {agent.model}
                  </p>
                  {agent.description && (
                    <p className="text-sm text-gray-400 mt-2 line-clamp-2">
                      {agent.description}
                    </p>
                  )}
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <span
                  className={`text-xs px-2 py-1 rounded-full ${
                    agent.is_active
                      ? 'bg-green-900/30 text-green-400 border border-green-700/30'
                      : 'bg-gray-800 text-gray-500'
                  }`}
                >
                  {agent.is_active ? '● Активен' : '○ Отключён'}
                </span>
                <span className="text-xs text-gray-600">
                  {new Date(agent.created_at).toLocaleDateString('ru-RU')}
                </span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-24">
          <div className="w-20 h-20 bg-gray-800 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <Bot className="w-10 h-10 text-gray-600" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">Нет агентов</h3>
          <p className="text-gray-500 text-sm mb-6">
            Создайте своего первого AI агента
          </p>
          <Link
            href="/agents/new"
            className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition"
          >
            <Plus className="w-4 h-4" />
            Создать агента
          </Link>
        </div>
      )}
    </div>
  );
}
