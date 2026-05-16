import { readFileSync, existsSync, writeFileSync } from 'fs';
import path from 'path';

const MEMORY_FILE = path.join(process.cwd(), 'data', 'memory.json');

export interface MemoryItem {
  id: string;
  user_id: string;
  agent_id?: string;
  content: string;
  importance: number;
  tags: string[];
  created_at: string;
  expires_at?: string;
}

function readMemory(): MemoryItem[] {
  if (!existsSync(MEMORY_FILE)) {
    return [];
  }
  try {
    return JSON.parse(readFileSync(MEMORY_FILE, 'utf-8'));
  } catch {
    return [];
  }
}

function writeMemory(items: MemoryItem[]) {
  writeFileSync(MEMORY_FILE, JSON.stringify(items, null, 2));
}

export function getMemoriesByUserId(userId: string, agentId?: string, limit = 5): MemoryItem[] {
  const items = readMemory();
  return items
    .filter(m => m.user_id === userId && (m.agent_id === agentId || !m.agent_id))
    .sort((a, b) => b.importance - a.importance || new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, limit);
}

export function createMemory(data: Omit<MemoryItem, 'id' | 'created_at'>): MemoryItem {
  const items = readMemory();
  const item: MemoryItem = {
    ...data,
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
  };
  items.push(item);
  writeMemory(items);
  return item;
}

export function updateMemory(memoryId: string, updates: Partial<MemoryItem>): MemoryItem | undefined {
  const items = readMemory();
  const index = items.findIndex(m => m.id === memoryId);
  if (index === -1) return undefined;
  items[index] = { ...items[index], ...updates };
  writeMemory(items);
  return items[index];
}

export function deleteMemory(memoryId: string): boolean {
  const items = readMemory();
  const filtered = items.filter(m => m.id !== memoryId);
  if (filtered.length === items.length) return false;
  writeMemory(filtered);
  return true;
}