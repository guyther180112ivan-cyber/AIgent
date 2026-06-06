'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, Trash2, Search, Paperclip, X, FileText } from 'lucide-react';
import ChatHistory from './ChatHistory';
import { webSearch, formatSearchResults } from './useWebSearch';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface AttachedFile {
  id: string;
  name: string;
  size: number;
  content?: string;
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
  const [uploading, setUploading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [historyKey, setHistoryKey] = useState(0);
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files?.length) return;

    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        if (file.size > 10 * 1024 * 1024) continue;

        const formData = new FormData();
        formData.append('file', file);

        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        if (res.ok) {
          const data = await res.json();
          setAttachedFiles(prev => [...prev, {
            id: data.id,
            name: data.name,
            size: data.size,
            content: data.content,
          }]);
        }
      }
    } catch (err) {
      console.error('[Chat] Upload error:', err);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const removeFile = (id: string) => {
    setAttachedFiles(prev => prev.filter(f => f.id !== id));
  };

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleSend = async () => {
    const text = input.trim();
    if ((!text && attachedFiles.length === 0) || loading) return;

    const fileNames = attachedFiles.map(f => f.name);
    const displayText = text + (fileNames.length > 0 ? `\n📎 ${fileNames.join(', ')}` : '');

    const userMsg: Message = { role: 'user', content: displayText };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setAttachedFiles([]);
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
          file_contents: attachedFiles.map(f => ({ name: f.name, content: f.content })),
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
      <div className="flex items-center justify-between px-3 sm:px-6 py-3 sm:py-4 border-b border-gray-800 bg-gray-900">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 bg-indigo-600/20 border border-indigo-500/30 rounded-lg flex items-center justify-center flex-shrink-0">
            <Bot className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-white truncate">{agentName}</h2>
            <p className="text-xs text-gray-500">
              {conversationId ? 'Активная беседа' : 'Новая беседа'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 sm:gap-2 flex-shrink-0">
          {searching && (
            <span className="hidden sm:flex text-xs text-indigo-400 items-center gap-1">
              <Search className="w-3 h-3 animate-spin" />
              Поиск...
            </span>
          )}
          {uploading && (
            <span className="hidden sm:flex text-xs text-indigo-400 items-center gap-1">
              <Loader2 className="w-3 h-3 animate-spin" />
              Загрузка...
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

      <div className="flex-1 overflow-y-auto px-3 sm:px-6 py-3 sm:py-4 space-y-4 sm:space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center py-12 sm:py-16 px-4">
            <div className="w-14 h-14 sm:w-16 sm:h-16 bg-indigo-600/10 border border-indigo-500/20 rounded-2xl flex items-center justify-center mb-4">
              <Bot className="w-7 h-7 sm:w-8 sm:h-8 text-indigo-400" />
            </div>
            <h3 className="text-white font-semibold mb-2">{agentName}</h3>
            <p className="text-gray-500 text-sm">
              Начните разговор — напишите сообщение
            </p>
            <p className="text-gray-600 text-xs mt-2">
              Подсказка: используй &quot;найди...&quot; для поиска или прикрепи файл
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
              className={`max-w-[85%] sm:max-w-[72%] rounded-2xl px-3.5 py-2.5 sm:px-4 sm:py-3 text-sm leading-relaxed whitespace-pre-wrap ${
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

      <div className="px-3 sm:px-6 py-3 sm:py-4 border-t border-gray-800 bg-gray-900">
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {attachedFiles.map((f) => (
              <div
                key={f.id}
                className="flex items-center gap-1.5 bg-gray-800 border border-gray-700 rounded-lg px-2.5 py-1.5 text-xs"
              >
                <FileText className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                <span className="text-gray-200 truncate max-w-[100px] sm:max-w-[160px]">{f.name}</span>
                <span className="text-gray-500 flex-shrink-0 hidden sm:inline">{formatSize(f.size)}</span>
                <button
                  onClick={() => removeFile(f.id)}
                  className="text-gray-500 hover:text-red-400 transition ml-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="flex items-end gap-2 sm:gap-3">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={loading || uploading}
            className="w-9 h-9 sm:w-10 sm:h-10 bg-gray-800 hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed text-gray-400 hover:text-gray-200 rounded-xl flex items-center justify-center transition flex-shrink-0 border border-gray-700"
            title="Прикрепить файл"
          >
            <Paperclip className="w-4 h-4" />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            accept=".txt,.md,.csv,.json,.xml,.yaml,.yml,.js,.ts,.jsx,.tsx,.py,.rb,.java,.c,.cpp,.h,.html,.css,.sql,.sh,.env,.cfg,.ini,.toml,.docx"
          />

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Сообщение..."
            rows={1}
            className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-xl px-3 sm:px-4 py-2.5 sm:py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-gray-500 resize-none transition max-h-32 overflow-y-auto"
            style={{ minHeight: '44px' }}
          />
          <button
            onClick={handleSend}
            disabled={(!input.trim() && attachedFiles.length === 0) || loading || uploading}
            className="w-10 h-10 sm:w-11 sm:h-11 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl flex items-center justify-center transition flex-shrink-0"
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