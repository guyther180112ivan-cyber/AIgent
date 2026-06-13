'use client';

import { useState, useEffect } from 'react';
import { Plus, Calendar } from 'lucide-react';
import { ScheduledTask } from '@/types';
import TaskCard from './TaskCard';
import TaskForm from './TaskForm';

interface Agent {
  id: string;
  name: string;
}

export default function SchedulerPage() {
  const [tasks, setTasks] = useState<ScheduledTask[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingTask, setEditingTask] = useState<ScheduledTask | null>(null);

  useEffect(() => {
    fetchTasks();
    fetchAgents();
  }, []);

  const fetchTasks = async () => {
    try {
      const res = await fetch('/api/scheduler');
      if (res.ok) setTasks(await res.json());
    } finally {
      setLoading(false);
    }
  };

  const fetchAgents = async () => {
    try {
      const res = await fetch('/api/agents');
      if (res.ok) setAgents(await res.json());
    } catch {}
  };

  const handleCreate = async (data: any) => {
    const res = await fetch('/api/scheduler', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (res.ok) {
      const task = await res.json();
      setTasks(prev => [...prev, task]);
    }
  };

  const handleUpdate = async (data: any) => {
    if (!editingTask) return;
    const res = await fetch(`/api/scheduler/${editingTask.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (res.ok) {
      const updated = await res.json();
      setTasks(prev => prev.map(t => t.id === updated.id ? updated : t));
    }
  };

  const handleToggle = async (id: string) => {
    const res = await fetch(`/api/scheduler/${id}/toggle`, { method: 'POST' });
    if (res.ok) {
      const updated = await res.json();
      setTasks(prev => prev.map(t => t.id === updated.id ? updated : t));
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Удалить расписание?')) return;
    const res = await fetch(`/api/scheduler/${id}`, { method: 'DELETE' });
    if (res.ok) {
      setTasks(prev => prev.filter(t => t.id !== id));
    }
  };

  const getAgentName = (agentId: string) => agents.find(a => a.id === agentId)?.name || 'Неизвестный';

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Calendar className="w-6 h-6 text-indigo-400" />
          <h1 className="text-xl font-bold text-white">Расписание задач</h1>
        </div>
        <button
          onClick={() => { setEditingTask(null); setShowForm(true); }}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-sm font-medium transition"
        >
          <Plus className="w-4 h-4" />
          Новое
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Загрузка...</div>
      ) : tasks.length === 0 ? (
        <div className="text-center py-12">
          <Calendar className="w-12 h-12 text-gray-700 mx-auto mb-3" />
          <p className="text-gray-500">Нет расписаний</p>
          <p className="text-gray-600 text-sm mt-1">Создайте первое расписание, чтобы агент писал по расписанию</p>
        </div>
      ) : (
        <div className="space-y-3">
          {tasks.map(task => (
            <TaskCard
              key={task.id}
              task={task}
              agentName={getAgentName(task.agent_id)}
              onToggle={handleToggle}
              onEdit={(t) => { setEditingTask(t); setShowForm(true); }}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {showForm && (
        <TaskForm
          agents={agents}
          editingTask={editingTask}
          onSubmit={editingTask ? handleUpdate : handleCreate}
          onClose={() => { setShowForm(false); setEditingTask(null); }}
        />
      )}
    </div>
  );
}
