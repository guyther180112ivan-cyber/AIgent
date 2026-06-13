'use client';

import { useState, useEffect } from 'react';
import { X, Clock } from 'lucide-react';
import { ScheduledTask, SchedulePreset } from '@/types';

interface Agent {
  id: string;
  name: string;
}

interface TaskFormProps {
  agents: Agent[];
  editingTask?: ScheduledTask | null;
  onSubmit: (data: any) => Promise<void>;
  onClose: () => void;
}

const CRON_PRESETS: Record<SchedulePreset, { label: string; getCron: (time?: string, day?: string) => string }> = {
  hourly: { label: 'Каждый час', getCron: () => '0 * * * *' },
  daily: { label: 'Ежедневно', getCron: (time) => { const [h, m] = (time || '09:00').split(':'); return `${m} ${h} * * *`; } },
  weekly: { label: 'Еженедельно', getCron: (time, day) => { const [h, m] = (time || '09:00').split(':'); const d = ['sun','mon','tue','wed','thu','fri','sat'].indexOf(day || 'mon'); return `${m} ${h} * * ${d}`; } },
  custom: { label: 'Свой cron', getCron: () => '' },
};

const DAYS = [
  { value: 'mon', label: 'Пн' },
  { value: 'tue', label: 'Вт' },
  { value: 'wed', label: 'Ср' },
  { value: 'thu', label: 'Чт' },
  { value: 'fri', label: 'Пт' },
  { value: 'sat', label: 'Сб' },
  { value: 'sun', label: 'Вс' },
];

export default function TaskForm({ agents, editingTask, onSubmit, onClose }: TaskFormProps) {
  const [name, setName] = useState(editingTask?.name || '');
  const [description, setDescription] = useState(editingTask?.description || '');
  const [agentId, setAgentId] = useState(editingTask?.agent_id || (agents[0]?.id ?? ''));
  const [prompt, setPrompt] = useState(editingTask?.prompt || '');
  const [preset, setPreset] = useState<SchedulePreset>(editingTask?.preset || 'daily');
  const [customCron, setCustomCron] = useState(editingTask?.cron_expr || '');
  const [scheduleTime, setScheduleTime] = useState(editingTask?.schedule_time || '09:00');
  const [scheduleDay, setScheduleDay] = useState(editingTask?.schedule_day || 'mon');
  const [loading, setLoading] = useState(false);

  const getCronExpr = (): string => {
    if (preset === 'custom') return customCron;
    return CRON_PRESETS[preset].getCron(scheduleTime, scheduleDay);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cronExpr = getCronExpr();
    if (!cronExpr) return;

    setLoading(true);
    try {
      await onSubmit({
        name,
        description,
        agent_id: agentId,
        prompt,
        cron_expr: cronExpr,
        preset,
        schedule_time: scheduleTime,
        schedule_day: scheduleDay,
      });
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-gray-900 rounded-2xl border border-gray-800 w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <h3 className="text-lg font-semibold text-white">
            {editingTask ? 'Редактировать расписание' : 'Новое расписание'}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Название</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Утреннее приветствие"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Описание</label>
            <input
              type="text"
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Необязательно"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Агент</label>
            <select
              value={agentId}
              onChange={e => setAgentId(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              required
            >
              {agents.map(a => (
                <option key={a.id} value={a.id}>{a.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Промпт для агента</label>
            <textarea
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              rows={3}
              placeholder="Что агент должен сделать/написать по расписанию"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-2">Расписание</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
              {(['hourly', 'daily', 'weekly', 'custom'] as SchedulePreset[]).map(p => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPreset(p)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
                    preset === p
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
                  }`}
                >
                  {CRON_PRESETS[p].label}
                </button>
              ))}
            </div>

            {(preset === 'daily' || preset === 'weekly') && (
              <div className="flex gap-2 mb-3">
                <input
                  type="time"
                  value={scheduleTime}
                  onChange={e => setScheduleTime(e.target.value)}
                  className="bg-gray-800 border border-gray-700 text-white rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            )}

            {preset === 'weekly' && (
              <div className="flex gap-1.5 mb-3">
                {DAYS.map(d => (
                  <button
                    key={d.value}
                    type="button"
                    onClick={() => setScheduleDay(d.value)}
                    className={`w-10 h-10 rounded-lg text-xs font-medium transition ${
                      scheduleDay === d.value
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:text-white'
                    }`}
                  >
                    {d.label}
                  </button>
                ))}
              </div>
            )}

            {preset === 'custom' && (
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={customCron}
                  onChange={e => setCustomCron(e.target.value)}
                  className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-xl px-4 py-2.5 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="*/30 * * * *"
                  required
                />
              </div>
            )}
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 transition"
            >
              Отмена
            </button>
            <button
              type="submit"
              disabled={loading || !name.trim() || !prompt.trim()}
              className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              {loading ? 'Сохранение...' : editingTask ? 'Сохранить' : 'Создать'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
