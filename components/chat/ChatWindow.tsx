'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, Trash2, Search } from 'lucide-react';
import ChatHistory from './ChatHistory';
import { webSearch, formatSearchResults } from './useWebSearch';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatWindowProps {
  agentId: string;
  agentName: string;
}

export default function ChatWindow({ agentId, agentName }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [historyKey, setHistoryKey] = useState(0);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const needsSearch = (text: string): boolean => {
    const lower = text.toLowerCase();
    const keywords = [
      'найди', 'поиск', 'загугли', 'погугли', 'что такое', 'кто такой',
      'узнай', 'актуальн', 'новост', '2024', '2025', '2026',
      'погода', 'курс', 'цена', 'стоимость', 'википедия',
      'search', 'latest', 'news', 'current',
    ];
    return keywords.some(kw => lower.includes(kw));
  };

  const extractSearchQuery = (text: string): string => {
    return text
      .replace(/найди|поиск|загугли|погугли|что такое|кто такой|узнай|в интернете|покажи|расскажи/gi, '')
      .replace(/\s+/g, ' ')
      .trim()
      .substring(0, 200);
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    setMessages([]);
    setConversationId(undefined);
  }, [agentId]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    let searchResults = '';
    
    if (needsSearch(text)) {
      setSearching(true);
      try {
        const query = extractSearchQuery(text);
        if (query.length > 2) {
          const searchResponse = await webSearch(query);
          searchResults = formatSearchResults(searchResponse);
        }
      } catch (err) {
        console.error('[Chat] Search error:', err);
      } finally {
        setSearching(false);
      }
    }

    try {
      const messageWithSearch = searchResults 
        ? `${text}\n\n[WEB_SEARCH_RESULTS]:\n${searchResults}`
        : text;

      const res = await fetch(`/api/agents/${agentId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: messageWithSearch, 
          conversation_id: conversationId,
          has_web_search: !!searchResults,
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setConversationId(data.conversation_id);
        setHistoryKey(prev => prev + 1);
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: data.content },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `❌ Ошибка: ${data.error || 'Неизвестная ошибка'}`,
          },
        ]);
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '❌ Ошибка сети' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setConversationId(undefined);
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(undefined);
  };

  const loadConversationMessages = async (convId: string) => {
    try {
      const res = await fetch(`/api/agents/${agentId}/chat?conversation_id=${convId}`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.map((m: any) => ({ role: m.role, content: m.content })));
      }
    } catch {
      console.error('Failed to load messages');
    }
  };

  useEffect(() => {
    if (conversationId) {
      loadConversationMessages(conversationId);
    }
  }, [conversationId]);

  return (
    <div className="flex flex-col h-full bg-gray-950">
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600/20 border border-indigo-500/30 rounded-lg flex items-center justify-center">
            <Bot className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">{agentName}</h2>
            <p className="text-xs text-gray-500">
              {conversationId ? 'Активная беседа' : 'Новая беседа'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {searching && (
            <span className="text-xs text-indigo-400 flex items-center gap-1">
              <Search className="w-3 h-3 animate-spin" />
              Поиск...
            </span>
          )}
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="text-gray-500 hover:text-red-400 transition p-2 rounded-lg hover:bg-red-900/20"
              title="Очистить чат"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      <div className="border-b border-gray-800 bg-gray-900/50">
        <ChatHistory
          key={historyKey}
          agentId={agentId}
          currentConversationId={conversationId}
          onSelectConversation={(id) => {
            setConversationId(id);
          }}
          onNewChat={handleNewChat}
        />
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-16">
            <div className="w-16 h-16 bg-indigo-600/10 border border-indigo-500/20 rounded-2xl flex items-center justify-center mb-4">
              <Bot className="w-8 h-8 text-indigo-400" />
            </div>
            <h3 className="text-white font-semibold mb-2">{agentName}</h3>
            <p className="text-gray-500 text-sm">
              Начните разговор — напишите сообщение
            </p>
            <p className="text-gray-600 text-xs mt-2">
              Подсказка: используй &quot;найди...&quot; или &quot;что такое...&quot; для поиска в интернете
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex items-start gap-3 ${
              msg.role === 'user' ? 'flex-row-reverse' : ''
            }`}
          >
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                msg.role === 'assistant'
                  ? 'bg-indigo-600/20 border border-indigo-500/30'
                  : 'bg-gray-700'
              }`}
            >
              {msg.role === 'assistant' ? (
                <Bot className="w-4 h-4 text-indigo-400" />
              ) : (
                <User className="w-4 h-4 text-gray-300" />
              )}
            </div>

            <div
              className={`max-w-[72%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-tr-sm'
                  : 'bg-gray-900 border border-gray-800 text-gray-100 rounded-tl-sm'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {(loading || searching) && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-indigo-600/20 border border-indigo-500/30 rounded-lg flex items-center justify-center">
              <Bot className="w-4 h-4 text-indigo-400" />
            </div>
            <div className="bg-gray-900 border border-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="px-6 py-4 border-t border-gray-800 bg-gray-900">
        <div className="flex items-end gap-3">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Напишите сообщение... (Enter — отправить, Shift+Enter — новая строка)"
            rows={1}
            className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-gray-500 resize-none transition max-h-32 overflow-y-auto"
            style={{ minHeight: '48px' }}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="w-11 h-11 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl flex items-center justify-center transition flex-shrink-0"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}