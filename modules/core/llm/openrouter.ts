import { ChatCompletionMessage, LLMConfig } from '@/types';

const OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions';

export const DEFAULT_MODEL = 'openai/gpt-4o-mini';

export interface LLMResponse {
  content: string;
  model: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

/**
 * Выполняет запрос к LLM через OpenRouter API.
 * Используется только на сервере (API Routes / Server Actions).
 */
export async function chatCompletion(
  messages: ChatCompletionMessage[],
  config: Partial<LLMConfig> = {}
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

  const response = await fetch(OPENROUTER_API_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
      'X-Title': 'AIgent Platform',
    },
    body: JSON.stringify({
      model,
      messages,
      temperature: config.temperature ?? 0.7,
      max_tokens: config.max_tokens ?? 4096,
    }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`OpenRouter error ${response.status}: ${errorBody}`);
  }

  const data = await response.json();
  return {
    content: data.choices[0]?.message?.content || '',
    model: data.model,
    usage: data.usage,
  };
}

/**
 * Стриминг ответа от LLM (возвращает ReadableStream).
 */
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
