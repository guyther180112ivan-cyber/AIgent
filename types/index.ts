// ============================================================
// ГЛОБАЛЬНЫЕ ТИПЫ ПРОЕКТА AIgent v3
// Принцип: добавляем типы, не изменяем существующие
// ============================================================

// --- AUTH ---
export interface User {
  id: string;
  email: string;
  created_at: string;
}

// --- AGENTS ---
export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  system_prompt: string;
  model: string;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  name: string;
  description?: string;
  system_prompt: string;
  model?: string;
  avatar_url?: string;
}

export interface AgentUpdate extends Partial<AgentCreate> {
  is_active?: boolean;
}

// --- CONVERSATIONS ---
export interface Conversation {
  id: string;
  agent_id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

// --- MESSAGES ---
export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface MessageCreate {
  conversation_id: string;
  role: MessageRole;
  content: string;
  metadata?: Record<string, unknown>;
}

// --- SKILLS ---
export interface Skill {
  id: string;
  name: string;
  description: string;
  prompt_template: string;
  parameters: SkillParameter[];
  type: 'prompt' | 'anthropic';
  created_at: string;
}

export interface SkillParameter {
  name: string;
  type: 'string' | 'number' | 'boolean';
  description: string;
  required: boolean;
  default?: unknown;
}

export interface AgentSkill {
  agent_id: string;
  skill_id: string;
  config?: Record<string, unknown>;
  skill?: Skill;
}

// --- TOOLS ---
export type ToolType = 'http' | 'toolhouse' | 'custom';

export interface Tool {
  id: string;
  name: string;
  description: string;
  type: ToolType;
  config: Record<string, unknown>;
  input_schema: JSONSchema;
  created_at: string;
}

export interface AgentTool {
  agent_id: string;
  tool_id: string;
  config?: Record<string, unknown>;
  tool?: Tool;
}

// --- MEMORY ---
export interface MemoryItem {
  id: string;
  user_id: string;
  agent_id?: string;
  content: string;
  importance: number; // 1-10
  tags: string[];
  created_at: string;
  expires_at?: string;
}

// --- RAG ---
export interface RAGDocument {
  id: string;
  user_id: string;
  name: string;
  content: string;
  source?: string;
  created_at: string;
}

// --- SCHEDULER ---
export interface ScheduledTask {
  id: string;
  agent_id: string;
  user_id: string;
  name: string;
  description?: string;
  cron_expr: string;
  action: TaskAction;
  is_active: boolean;
  last_run_at?: string;
  next_run_at?: string;
  created_at: string;
}

export interface TaskAction {
  type: 'message' | 'tool';
  payload: Record<string, unknown>;
}

// --- REMINDERS ---
export type ReminderChannel = 'web' | 'telegram' | 'email';

export interface Reminder {
  id: string;
  user_id: string;
  agent_id?: string;
  text: string;
  remind_at: string;
  channel: ReminderChannel;
  is_sent: boolean;
  created_at: string;
}

// --- TELEGRAM ---
export interface TelegramLink {
  id: string;
  user_id: string;
  telegram_id: string;
  username?: string;
  first_name?: string;
  linked_at: string;
}

// --- LLM ---
export interface ChatCompletionMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string | null;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
  name?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface LLMConfig {
  model: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
}

// --- AGENT RUNTIME ---
export interface AgentModuleInterface {
  name: string;
  onBeforeMessage?: (ctx: AgentContext) => Promise<AgentContext>;
  onAfterMessage?: (ctx: AgentContext, response: string) => Promise<void>;
}

export interface AgentContext {
  agentId: string;
  userId: string;
  conversationId: string;
  messages: ChatCompletionMessage[];
  systemPrompt: string;
  metadata: Record<string, unknown>;
}

// --- FILE ATTACHMENTS ---
export interface FileAttachment {
  id: string;
  name: string;
  size: number;
  type: string;
  url: string;
  content?: string;
}

// --- PUSH NOTIFICATIONS ---
export interface PushSubscription {
  endpoint: string;
  expirationTime?: number | null;
  keys: {
    p256dh: string;
    auth: string;
  };
}

export interface PushNotificationPayload {
  title: string;
  body?: string;
  icon?: string;
  badge?: string;
  data?: Record<string, unknown>;
  vibrate?: number[];
}

// --- UTILS ---
export interface JSONSchema {
  type: string;
  properties?: Record<string, JSONSchemaProperty>;
  required?: string[];
}

export interface JSONSchemaProperty {
  type: string;
  description?: string;
  enum?: unknown[];
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
}
