import { readFileSync, writeFileSync, existsSync } from 'fs';
import path from 'path';
import { ScheduledTask } from '@/types';

const SCHEDULER_FILE = path.join(process.cwd(), 'data', 'scheduled-tasks.json');

function readTasks(): ScheduledTask[] {
  if (!existsSync(SCHEDULER_FILE)) return [];
  try {
    return JSON.parse(readFileSync(SCHEDULER_FILE, 'utf-8'));
  } catch {
    return [];
  }
}

function writeTasks(tasks: ScheduledTask[]) {
  writeFileSync(SCHEDULER_FILE, JSON.stringify(tasks, null, 2));
}

export function getTasksByUserId(userId: string): ScheduledTask[] {
  return readTasks().filter(t => t.user_id === userId);
}

export function getActiveTasks(): ScheduledTask[] {
  return readTasks().filter(t => t.is_active);
}

export function getTaskById(taskId: string): ScheduledTask | undefined {
  return readTasks().find(t => t.id === taskId);
}

export function createTask(data: {
  agent_id: string;
  user_id: string;
  name: string;
  description?: string;
  prompt: string;
  cron_expr: string;
  preset: string;
  schedule_time?: string;
  schedule_day?: string;
}): ScheduledTask {
  const tasks = readTasks();
  const now = new Date().toISOString();
  const task: ScheduledTask = {
    id: crypto.randomUUID(),
    agent_id: data.agent_id,
    user_id: data.user_id,
    name: data.name,
    description: data.description,
    prompt: data.prompt,
    cron_expr: data.cron_expr,
    preset: data.preset as any,
    schedule_time: data.schedule_time,
    schedule_day: data.schedule_day,
    is_active: true,
    daily_limit: 10,
    run_count_today: 0,
    created_at: now,
    updated_at: now,
  };
  tasks.push(task);
  writeTasks(tasks);
  return task;
}

export function updateTask(taskId: string, updates: Partial<ScheduledTask>): ScheduledTask | undefined {
  const tasks = readTasks();
  const index = tasks.findIndex(t => t.id === taskId);
  if (index === -1) return undefined;
  tasks[index] = { ...tasks[index], ...updates, updated_at: new Date().toISOString() };
  writeTasks(tasks);
  return tasks[index];
}

export function deleteTask(taskId: string): boolean {
  const tasks = readTasks();
  const filtered = tasks.filter(t => t.id !== taskId);
  if (filtered.length === tasks.length) return false;
  writeTasks(filtered);
  return true;
}

export function toggleTask(taskId: string): ScheduledTask | undefined {
  const tasks = readTasks();
  const index = tasks.findIndex(t => t.id === taskId);
  if (index === -1) return undefined;
  tasks[index].is_active = !tasks[index].is_active;
  tasks[index].updated_at = new Date().toISOString();
  writeTasks(tasks);
  return tasks[index];
}

export function incrementRunCount(taskId: string): void {
  const tasks = readTasks();
  const index = tasks.findIndex(t => t.id === taskId);
  if (index === -1) return;

  const task = tasks[index];
  const today = new Date().toISOString().split('T')[0];
  const lastRunDate = task.last_run_at?.split('T')[0];

  if (lastRunDate !== today) {
    task.run_count_today = 1;
  } else {
    task.run_count_today += 1;
  }
  task.last_run_at = new Date().toISOString();
  task.updated_at = new Date().toISOString();
  writeTasks(tasks);
}

export function resetDailyCounts(): void {
  const tasks = readTasks();
  const today = new Date().toISOString().split('T')[0];
  let changed = false;
  for (const task of tasks) {
    const lastRunDate = task.last_run_at?.split('T')[0];
    if (lastRunDate !== today && task.run_count_today > 0) {
      task.run_count_today = 0;
      changed = true;
    }
  }
  if (changed) writeTasks(tasks);
}
