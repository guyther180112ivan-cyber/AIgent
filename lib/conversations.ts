import { readFileSync, existsSync, writeFileSync } from 'fs';
import path from 'path';

const CONVERSATIONS_FILE = path.join(process.cwd(), 'data', 'conversations.json');

export interface Conversation {
  id: string;
  agent_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

function readConversations(): Conversation[] {
  if (!existsSync(CONVERSATIONS_FILE)) {
    return [];
  }
  try {
    return JSON.parse(readFileSync(CONVERSATIONS_FILE, 'utf-8'));
  } catch {
    return [];
  }
}

function writeConversations(convs: Conversation[]) {
  writeFileSync(CONVERSATIONS_FILE, JSON.stringify(convs, null, 2));
}

export function getConversationsByAgentId(agentId: string, userId: string): Conversation[] {
  const convs = readConversations();
  return convs
    .filter(c => c.agent_id === agentId && c.user_id === userId)
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
}

export function getConversationById(conversationId: string): Conversation | undefined {
  const convs = readConversations();
  return convs.find(c => c.id === conversationId);
}

export function createConversation(data: Omit<Conversation, 'id' | 'created_at' | 'updated_at'>): Conversation {
  const convs = readConversations();
  const now = new Date().toISOString();
  const conv: Conversation = {
    ...data,
    id: crypto.randomUUID(),
    created_at: now,
    updated_at: now,
  };
  convs.push(conv);
  writeConversations(convs);
  return conv;
}

export function updateConversation(conversationId: string, updates: Partial<Conversation>): Conversation | undefined {
  const convs = readConversations();
  const index = convs.findIndex(c => c.id === conversationId);
  if (index === -1) return undefined;
  convs[index] = { ...convs[index], ...updates, updated_at: new Date().toISOString() };
  writeConversations(convs);
  return convs[index];
}