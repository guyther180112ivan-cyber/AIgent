'use client';

import { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight, MessageSquare, Plus, Clock } from 'lucide-react';

interface Conversation {
  id: string;
  title: string;
  source?: 'user' | 'scheduled';
  created_at: string;
  updated_at: string;
}

interface ChatHistoryProps {
  agentId: string;
  currentConversationId?: string;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
}

export default function ChatHistory({
  agentId,
  currentConversationId,
  onSelectConversation,
  onNewChat,
}: ChatHistoryProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchConversations();
  }, [agentId]);

  const fetchConversations = async () => {
    try {
      const res = await fetch(`/api/agents/${agentId}/conversations`);
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
      }
    } catch {
      console.error('Failed to fetch conversations');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Сегодня';
    if (days === 1) return 'Вчера';
    if (days < 7) return `${days} дней назад`;
    return date.toLocaleDateString('ru-RU');
  };

  return (
    <div className="border-b border-gray-800">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-2 px-4 py-3 text-sm text-gray-400 hover:text-white hover:bg-gray-800/50 transition"
      >
        {isExpanded ? (
          <ChevronDown className="w-4 h-4" />
        ) : (
          <ChevronRight className="w-4 h-4" />
        )}
        <MessageSquare className="w-4 h-4" />
        <span className="flex-1 text-left font-medium">История чатов</span>
        <span className="text-xs text-gray-500">{conversations.length}</span>
      </button>

      {isExpanded && (
        <div className="px-2 pb-2">
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-indigo-400 hover:bg-indigo-600/10 rounded-lg transition mb-1"
          >
            <Plus className="w-4 h-4" />
            Новый чат
          </button>

          {loading ? (
            <div className="px-3 py-2 text-xs text-gray-500">Загрузка...</div>
          ) : conversations.length === 0 ? (
            <div className="px-3 py-2 text-xs text-gray-500">Нет переписок</div>
          ) : (
            <div className="space-y-0.5 max-h-64 overflow-y-auto">
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition ${
                    currentConversationId === conv.id
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/20'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                  }`}
                >
                  <div className="flex items-center gap-1.5 truncate">
                    {conv.source === 'scheduled' && <Clock className="w-3 h-3 text-indigo-400 flex-shrink-0" />}
                    <span className="truncate">{conv.title || 'Без названия'}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    {formatDate(conv.updated_at || conv.created_at)}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}