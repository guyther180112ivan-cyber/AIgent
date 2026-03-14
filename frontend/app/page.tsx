'use client';

import React, { useState, useEffect, useRef } from 'react';
import './globals.css';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Skill {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

interface Tool {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

interface ScheduledTask {
  id: string;
  name: string;
  description: string;
  schedule_type: 'once' | 'recurring';
  cron_expression?: string;
  scheduled_at?: string;
  next_run?: string;
  is_active: boolean;
  prompt: string;
}

export default function Home() {
  const [tab, setTab] = useState('chat');
  const [skills, setSkills] = useState<Skill[]>([
    { id: "1", name: "Помощник с кодом", description: "Помогает с программированием", enabled: true },
    { id: "2", name: "Составитель писем", description: "Составляет профессиональные письма", enabled: false },
    { id: "3", name: "Аналитик данных", description: "Анализирует данные", enabled: true },
  ]);
  const [tools, setTools] = useState<Tool[]>([
    { id: "1", name: "Поиск в интернете", description: "Ищет информацию в интернете", enabled: true },
    { id: "2", name: "Калькулятор", description: "Выполняет вычисления", enabled: true },
    { id: "3", name: "Календарь", description: "Планирует события", enabled: false },
  ]);
  const [messages, setMessages] = useState<Message[]>([{ role: 'assistant', content: 'Привет! Как я могу помочь вам сегодня?' }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scheduler state
  const [tasks, setTasks] = useState<ScheduledTask[]>([]);
  const [showTaskForm, setShowTaskForm] = useState(false);
  const [newTask, setNewTask] = useState({
    name: '',
    description: '',
    schedule_type: 'once' as 'once' | 'recurring',
    cron_expression: '',
    prompt: '',
    scheduled_at: ''
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load scheduled tasks
  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await fetch(`${API_URL}/api/scheduler/tasks`, {
        headers: {
          'Authorization': 'Bearer dev-token'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setTasks(data.tasks || []);
      }
    } catch (error) {
      console.error('Ошибка загрузки задач:', error);
    }
  };

  const createTask = async () => {
    try {
      // Преобразуем schedule_type в формат бэкенда
      let scheduleType = 'once';
      if (newTask.schedule_type === 'recurring') {
        scheduleType = newTask.cron_expression ? 'cron' : 'daily';
      }

      // Преобразуем local time в UTC
      let scheduledAtUtc = null;
      if (newTask.schedule_type === 'once' && newTask.scheduled_at) {
        const localDate = new Date(newTask.scheduled_at);
        scheduledAtUtc = localDate.toISOString();
      }

      const response = await fetch(`${API_URL}/api/scheduler/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev-token'
        },
        body: JSON.stringify({
          name: newTask.name,
          description: newTask.description,
          action_type: 'telegram_message',
          schedule_type: scheduleType,
          cron_expression: newTask.schedule_type === 'recurring' ? newTask.cron_expression : undefined,
          scheduled_at: scheduledAtUtc,
          message_text: newTask.prompt,
          target_id: '5234290635',
          target_type: 'telegram',
          is_active: true
        })
      });
      if (response.ok) {
        setShowTaskForm(false);
        setNewTask({
          name: '',
          description: '',
          schedule_type: 'once',
          cron_expression: '',
          prompt: '',
          scheduled_at: ''
        });
        fetchTasks();
      } else {
        const errorData = await response.json();
        console.error('Ошибка сервера:', errorData);
      }
    } catch (error) {
      console.error('Ошибка создания задачи:', error);
    }
  };

  const toggleTask = async (id: string, isActive: boolean) => {
    try {
      const response = await fetch(`${API_URL}/api/scheduler/tasks/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev-token'
        },
        body: JSON.stringify({ is_active: !isActive })
      });
      if (response.ok) {
        fetchTasks();
      }
    } catch (error) {
      console.error('Ошибка обновления задачи:', error);
    }
  };

  const deleteTask = async (id: string) => {
    try {
      const response = await fetch(`${API_URL}/api/scheduler/tasks/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer dev-token'
        }
      });
      if (response.ok) {
        fetchTasks();
      }
    } catch (error) {
      console.error('Ошибка удаления задачи:', error);
    }
  };

  const toggleSkill = (id: string) => {
    setSkills(skills.map(s => s.id === id ? { ...s, enabled: !s.enabled } : s));
  };

  const toggleTool = (id: string) => {
    setTools(tools.map(t => t.id === id ? { ...t, enabled: !t.enabled } : t));
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    
    const userMessage = input.trim();
    setInput('');
    setLoading(true);
    
    // Add user message immediately
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      // Direct request to OpenRouter API
      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer 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',
          'HTTP-Referer': 'http://localhost:3000',
          'X-Title': 'AIgent Platform',
        },
        body: JSON.stringify({
          model: 'openrouter/free',
          messages: [
            { role: 'system', content: 'Вы - полезный ИИ-ассистент. Отвечайте на русском языке.' },
            ...messages.map(m => ({ role: m.role, content: m.content })),
            { role: 'user', content: userMessage }
          ],
        }),
      });

      if (!response.ok) {
        throw new Error('Не удалось получить ответ от OpenRouter');
      }

      const data = await response.json();
      
      // Add assistant response
      const assistantContent = data.choices?.[0]?.message?.content || 'Нет ответа';
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: assistantContent
      }]);
    } catch (error) {
      console.error('Ошибка:', error);
      // Fallback to local response if API fails
      const activeSkills = skills.filter(s => s.enabled).map(s => s.name).join(', ');
      const activeTools = tools.filter(t => t.enabled).map(t => t.name).join(', ');
      
      const fallbackResponse = `Я получил ваше сообщение: "${userMessage}"

Мои активные навыки: ${activeSkills || 'нет'}
Доступные инструменты: ${activeTools || 'нет'}

Примечание: OpenRouter API настроен, но может потребоваться перезапуск.`;

      setMessages(prev => [...prev, { role: 'assistant', content: fallbackResponse }]);
    } finally {
      setLoading(false);
    }
  };

  const renderContent = () => {
    switch (tab) {
      case 'chat':
        return (
          <div className="chat-container">
            <div className="messages">
              {messages.map((m, i) => (
                <div key={i} className={`message ${m.role}`}>{m.content}</div>
              ))}
              {loading && <div className="message assistant">Думаю...</div>}
              <div ref={messagesEndRef} />
            </div>
            <div className="input-area">
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyPress={e => e.key === 'Enter' && sendMessage()}
                placeholder="Введите сообщение..."
                disabled={loading}
              />
              <button onClick={sendMessage} disabled={loading}>Отправить</button>
            </div>
          </div>
        );
      case 'skills':
        return (
          <div>
            <h2>Навыки</h2>
            {skills.map(s => (
              <div key={s.id} className="card flex flex-between">
                <div className="skill-card">
                  <div className="icon" style={{ background: '#eef2ff' }}>✨</div>
                  <div className="skill-info">
                    <h3>{s.name}</h3>
                    <p>{s.description}</p>
                  </div>
                </div>
                <div className={`toggle ${s.enabled ? 'active' : ''}`} onClick={() => toggleSkill(s.id)} />
              </div>
            ))}
          </div>
        );
      case 'tools':
        return (
          <div>
            <h2>Инструменты</h2>
            <div className="tool-grid">
              {tools.map(t => (
                <div key={t.id} className="card">
                  <div className="flex flex-between" style={{ marginBottom: 12 }}>
                    <div className="icon" style={{ background: '#f3e8ff' }}>🔧</div>
                    <span className={`badge ${t.enabled ? 'active' : 'inactive'}`}>{t.enabled ? 'Активен' : 'Неактивен'}</span>
                  </div>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>{t.name}</h3>
                  <p style={{ fontSize: 14, color: '#6b7280', marginBottom: 16 }}>{t.description}</p>
                  <button onClick={() => toggleTool(t.id)} style={{ width: '100%' }}>
                    {t.enabled ? 'Отключить' : 'Включить'}
                  </button>
                </div>
              ))}
            </div>
          </div>
        );
      case 'scheduler':
        return (
          <div>
            <div className="flex flex-between" style={{ marginBottom: 24 }}>
              <h2>Регулярные действия</h2>
              <button onClick={() => setShowTaskForm(true)}>+ Новая задача</button>
            </div>

            {showTaskForm && (
              <div className="card" style={{ marginBottom: 24, background: '#f9fafb' }}>
                <h3 style={{ marginBottom: 16 }}>Создать задачу</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <input
                    placeholder="Название задачи"
                    value={newTask.name}
                    onChange={e => setNewTask({...newTask, name: e.target.value})}
                  />
                  <input
                    placeholder="Описание"
                    value={newTask.description}
                    onChange={e => setNewTask({...newTask, description: e.target.value})}
                  />
                  <select
                    value={newTask.schedule_type}
                    onChange={e => setNewTask({...newTask, schedule_type: e.target.value as 'once' | 'recurring'})}
                  >
                    <option value="once">Однократно</option>
                    <option value="recurring">Повторяющееся</option>
                  </select>
                  {newTask.schedule_type === 'once' ? (
                    <input
                      type="datetime-local"
                      placeholder="Дата и время"
                      value={newTask.scheduled_at}
                      onChange={e => setNewTask({...newTask, scheduled_at: e.target.value})}
                    />
                  ) : (
                    <input
                      placeholder="Cron выражение (например: 0 9 * * *)"
                      value={newTask.cron_expression}
                      onChange={e => setNewTask({...newTask, cron_expression: e.target.value})}
                    />
                  )}
                  <textarea
                    placeholder="Что нужно сделать (prompt для ИИ)"
                    value={newTask.prompt}
                    onChange={e => setNewTask({...newTask, prompt: e.target.value})}
                    rows={3}
                    style={{ padding: 8, borderRadius: 6, border: '1px solid #d1d5db' }}
                  />
                  <div className="flex" style={{ gap: 8, marginTop: 8 }}>
                    <button onClick={createTask}>Создать</button>
                    <button onClick={() => setShowTaskForm(false)} style={{ background: '#6b7280' }}>Отмена</button>
                  </div>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {tasks.length === 0 && (
                <div className="card" style={{ textAlign: 'center', color: '#6b7280' }}>
                  Нет запланированных задач. Создайте первую!
                </div>
              )}
              {tasks.map(task => (
                <div key={task.id} className="card">
                  <div className="flex flex-between" style={{ marginBottom: 8 }}>
                    <div className="flex" style={{ gap: 12, alignItems: 'center' }}>
                      <div className="icon" style={{ background: task.is_active ? '#dcfce7' : '#f3f4f6' }}>
                        {task.schedule_type === 'recurring' ? '🔄' : '⏰'}
                      </div>
                      <div>
                        <h3 style={{ fontSize: 16, fontWeight: 600 }}>{task.name}</h3>
                        <p style={{ fontSize: 14, color: '#6b7280' }}>{task.description}</p>
                      </div>
                    </div>
                    <div className="flex" style={{ gap: 8 }}>
                      <button
                        onClick={() => toggleTask(task.id, task.is_active)}
                        style={{ background: task.is_active ? '#22c55e' : '#6b7280', padding: '6px 12px', fontSize: 12 }}
                      >
                        {task.is_active ? 'Активна' : 'Неактивна'}
                      </button>
                      <button
                        onClick={() => deleteTask(task.id)}
                        style={{ background: '#ef4444', padding: '6px 12px', fontSize: 12 }}
                      >
                        Удалить
                      </button>
                    </div>
                  </div>
                  <div style={{ fontSize: 13, color: '#6b7280', marginTop: 8 }}>
                    {task.schedule_type === 'recurring' ? (
                      <span>🔄 Повторяется: {task.cron_expression}</span>
                    ) : (
                      <span>⏰ Однократно в: {task.scheduled_at}</span>
                    )}
                    {task.next_run && <span style={{ marginLeft: 16 }}>📅 Следующий запуск: {new Date(task.next_run).toLocaleString('ru-RU')}</span>}
                  </div>
                  <div style={{ marginTop: 8, padding: 8, background: '#f9fafb', borderRadius: 6, fontSize: 13 }}>
                    <strong>Задание:</strong> {task.prompt}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      default:
        return (
          <div>
            <h2>Панель управления</h2>
            <div className="grid-3">
              <div className="stat-card">
                <div className="stat-label">Диалоги</div>
                <div className="stat-value">{messages.length}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Активные навыки</div>
                <div className="stat-value">{skills.filter(s => s.enabled).length}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Активные инструменты</div>
                <div className="stat-value">{tools.filter(t => t.enabled).length}</div>
              </div>
            </div>
            <div className="card" style={{ marginTop: 24 }}>
              <h3 style={{ marginBottom: 12 }}>Настройка OpenRouter</h3>
              <p style={{ color: '#6b7280' }}>API ключ: Настроен</p>
              <p style={{ color: '#6b7280' }}>Модель: openrouter/free</p>
            </div>
          </div>
        );
    }
  };

  const navItems = [
    { id: 'dashboard', label: 'Панель управления', icon: '📊' },
    { id: 'chat', label: 'Чат', icon: '💬' },
    { id: 'skills', label: 'Навыки', icon: '✨' },
    { id: 'tools', label: 'Инструменты', icon: '🔧' },
    { id: 'scheduler', label: 'Регулярные действия', icon: '📅' },
  ];

  return (
    <div style={{ display: 'flex' }}>
      <div className="sidebar">
        <div className="logo">
          <div className="logo-icon">ИИ</div>
          <span>Агент</span>
        </div>
        {navItems.map(item => (
          <div key={item.id} className={`nav-item ${tab === item.id ? 'active' : ''}`} onClick={() => setTab(item.id)}>
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </div>
        ))}
      </div>
      <div className="main">
        {renderContent()}
      </div>
    </div>
  );
}
