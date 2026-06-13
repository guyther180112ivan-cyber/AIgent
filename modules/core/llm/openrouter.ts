import { ChatCompletionMessage, LLMConfig } from '@/types';
import { ToolDefinition } from '@/modules/core/tools';

const OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions';

export const DEFAULT_MODEL = 'qwen/qwen3-coder:free';

export interface LLMResponse {
  content: string;
  model: string;
  tool_calls?: {
    id: string;
    type: 'function';
    function: { name: string; arguments: string };
  }[];
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export async function chatCompletion(
  messages: ChatCompletionMessage[],
  config: Partial<LLMConfig> = {},
  tools?: ToolDefinition[]
): Promise<LLMResponse> {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey || apiKey === 'your_openrouter_key') {
    const lastUserMsg = messages.filter(m => m.role === 'user').pop();
    return {
      content: `Тестовый ответ: "${lastUserMsg?.content || 'Привет'}"\n\n(Для реальных ответов добавьте OPENROUTER_API_KEY в .env.local)`,
      model: config.model || DEFAULT_MODEL,
    };
  }

  const model = config.model || DEFAULT_MODEL;

  const body: Record<string, unknown> = {
    model,
    messages,
    temperature: config.temperature ?? 0.7,
    max_tokens: config.max_tokens ?? 4096,
  };

  if (tools && tools.length > 0) {
    body.tools = tools;
    body.tool_choice = 'auto';
  }

  const response = await fetch(OPENROUTER_API_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
      'X-Title': 'AIgent Platform',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    if (response.status === 429) {
      const retryMatch = errorBody.match(/retry_after_seconds.*?(\d+)/);
      const retryAfter = retryMatch ? parseInt(retryMatch[1]) : 25;
      throw new Error(`RATE_LIMIT:${retryAfter}`);
    }
    throw new Error(`OpenRouter error ${response.status}: ${errorBody}`);
  }

  const data = await response.json();
  const choice = data.choices[0];

  return {
    content: choice?.message?.content || '',
    model: data.model,
    tool_calls: choice?.message?.tool_calls,
    usage: data.usage,
  };
}

export async function chatCompletionStream(
  messages: ChatCompletionMessage[],
  config: Partial<LLMConfig> = {}
): Promise<ReadableStream<Uint8Array>> {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error('OPENROUTER_API_KEY не задан');
  }

  const response = await fetch(OPENROUTER_API_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
      'X-Title': 'AIgent Platform',
    },
    body: JSON.stringify({
      model: config.model || DEFAULT_MODEL,
      messages,
      stream: true,
      temperature: config.temperature ?? 0.7,
    }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`OpenRouter stream error ${response.status}`);
  }

  return response.body;
}
