// Shared types between frontend and backend

export interface User {
  id: string;
  email: string;
  username: string;
  name: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  system_prompt: string;
  model_name: string;
  configuration: Record<string, any>;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  skills?: AgentSkill[];
  tools?: AgentTool[];
}

export interface Skill {
  id: string;
  name: string;
  slug: string;
  description: string;
  system_prompt_template: string;
  default_config: Record<string, any>;
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface AgentSkill {
  id: string;
  agent_id: string;
  skill_id: string;
  config: Record<string, any>;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
  skill?: Skill;
}

export interface Tool {
  id: string;
  name: string;
  slug: string;
  description: string;
  function_schema: Record<string, any>;
  default_config: Record<string, any>;
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface AgentTool {
  id: string;
  agent_id: string;
  tool_id: string;
  config: Record<string, any>;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
  tool?: Tool;
}

export interface Conversation {
  id: string;
  agent_id: string;
  channel_type: 'web' | 'telegram' | 'voice';
  channel_id: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata: Record<string, any>;
  created_at: string;
  tool_calls?: ToolCall[];
}

export interface ToolCall {
  id: string;
  message_id: string;
  tool_name: string;
  arguments: Record<string, any>;
  result?: string;
  status: 'pending' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
}

export interface Session {
  id: string;
  user_id: string;
  token_hash: string;
  expires_at: string;
  created_at: string;
  is_active: boolean;
}

// API Request/Response types
export interface CreateAgentRequest {
  name: string;
  description?: string;
  model_name?: string;
  configuration?: Record<string, any>;
}

export interface UpdateAgentRequest {
  name?: string;
  description?: string;
  model_name?: string;
  configuration?: Record<string, any>;
}

export interface CreateSkillRequest {
  name: string;
  slug: string;
  description: string;
  system_prompt_template: string;
  default_config?: Record<string, any>;
}

export interface UpdateSkillRequest {
  name?: string;
  description?: string;
  system_prompt_template?: string;
  default_config?: Record<string, any>;
}

export interface CreateToolRequest {
  name: string;
  slug: string;
  description: string;
  function_schema: Record<string, any>;
  default_config?: Record<string, any>;
}

export interface UpdateToolRequest {
  name?: string;
  description?: string;
  function_schema?: Record<string, any>;
  default_config?: Record<string, any>;
}

export interface AddSkillToAgentRequest {
  skill_id: string;
  config?: Record<string, any>;
  is_enabled?: boolean;
}

export interface AddToolToAgentRequest {
  tool_id: string;
  config?: Record<string, any>;
  is_enabled?: boolean;
}

export interface SendMessageRequest {
  conversation_id: string;
  content: string;
  channel_type: 'web' | 'telegram' | 'voice';
  channel_id: string;
}

export interface SendMessageResponse {
  message: Message;
  conversation: Conversation;
}

export interface AuthRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  name?: string;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface PaginationParams {
  page?: number;
  size?: number;
}

// Error types
export interface APIError {
  detail: string;
  error_code?: string;
  field?: string;
}

// Channel-specific types
export interface TelegramConfig {
  bot_token: string;
  webhook_url?: string;
}

export interface VoiceConfig {
  stt_provider: string;
  tts_provider: string;
  stt_config: Record<string, any>;
  tts_config: Record<string, any>;
}

export interface WebConfig {
  allowed_origins: string[];
  websocket_url: string;
}

// LLM types
export interface LLMConfig {
  provider: string;
  model: string;
  api_key?: string;
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
}

// System prompt generation
export interface SystemPromptContext {
  agent: Agent;
  enabled_skills: Skill[];
  enabled_tools: Tool[];
  channel_type: 'web' | 'telegram' | 'voice';
}

export interface SystemPromptTemplate {
  base_template: string;
  skill_template: string;
  tool_template: string;
  channel_template: Record<string, string>;
}
