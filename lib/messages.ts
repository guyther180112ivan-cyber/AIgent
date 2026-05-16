import { readFileSync, existsSync, writeFileSync } from 'fs';
import path from 'path';

const MESSAGES_FILE = path.join(process.cwd(), 'data', 'messages.json');

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

function readMessages(): Message[] {
  if (!existsSync(MESSAGES_FILE)) {
    return [];
  }
  try {
    return JSON.parse(readFileSync(MESSAGES_FILE, 'utf-8'));
  } catch {
    return [];
  }
}

function writeMessages(msgs: Message[]) {
  writeFileSync(MESSAGES_FILE, JSON.stringify(msgs, null, 2));
}

export function getMessagesByConversationId(conversationId: string): Message[] {
  const msgs = readMessages();
  return msgs
    .filter(m => m.conversation_id === conversationId)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
}

export function createMessage(data: Omit<Message, 'id' | 'created_at'>): Message {
  const msgs = readMessages();
  const msg: Message = {
    ...data,
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
  };
  msgs.push(msg);
  writeMessages(msgs);
  return msg;
}