'use client';

import { Clock, Play, Pause, Trash2, Edit } from 'lucide-react';
import { ScheduledTask } from '@/types';

interface TaskCardProps {
  task: ScheduledTask;
  agentName: string;
  onToggle: (id: string) => void;
  onEdit: (task: ScheduledTask) => void;
  onDelete: (id: string) => void;
}

const PRESET_LABELS: Record<string, string> = {
  hourly: 'Каждый час',
  daily: 'Ежедневно',
  weekly: 'Еженедельно',
  custom: 'Cron',
};

export default function TaskCard({ task, agentName, onToggle, onEdit, onDelete }: TaskCardProps) {
  const formatCron = (cron: string, preset?: string) => {
    if (preset && PRESET_LABELS[preset]) {
      let label = PRESET_LABELS[preset];
      if ((preset === 'daily' || preset === 'weekly') && task.schedule_time) {
        label += ` ${task.schedule_time}`;
      }
      if (preset === 'weekly' && task.schedule_day) {
        const days: Record<string, string> = { mon: 'Пн', tue: 'Вт', wed: 'Ср', thu: 'Чт', fri: 'Пт', sat: 'Сб', sun: 'Вс' };
        label += ` (${days[task.schedule_day] || task.schedule_day})`;
      }
      return label;
    }
    return cron;
  };

  const formatLastRun = (iso?: string) => {
    if (!iso) return 'Никогда';
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Только что';
    if (mins < 60) return `${mins} мин назад`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} ч назад`;
    return `${Math.floor(hours / 24)} дн назад`;
  };

  return (
    <div className={`bg-gray-900 rounded-xl border p-4 transition ${task.is_active ? 'border-gray-700' : 'border-gray-800 opacity-60'}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-white truncate">{task.name}</h4>
          {task.description && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">{task.description}</p>
          )}
        </div>
        <div className="flex items-center gap-1 ml-2">
          <button
            onClick={() => onToggle(task.id)}
            className={`p-1.5 rounded-lg transition ${task.is_active ? 'text-green-400 hover:bg-green-900/30' : 'text-gray-500 hover:bg-gray-800'}`}
            title={task.is_active ? 'Выключить' : 'Включить'}
          >
            {task.is_active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <button
            onClick={() => onEdit(task)}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition"
            title="Редактировать"
          >
            <Edit className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(task.id)}
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-900/20 transition"
            title="Удалить"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex items-center gap-3 text-xs text-gray-500">
        <span className="bg-gray-800 px-2 py-0.5 rounded">{agentName}</span>
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {formatCron(task.cron_expr, task.preset)}
        </span>
      </div>

      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
        <span>Последний: {formatLastRun(task.last_run_at)}</span>
        <span className={task.run_count_today >= task.daily_limit ? 'text-red-400' : ''}>
          Запусков: {task.run_count_today}/{task.daily_limit}
        </span>
      </div>
    </div>
  );
}
