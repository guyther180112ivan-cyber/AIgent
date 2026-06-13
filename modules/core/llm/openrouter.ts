import { ChatCompletionMessage, LLMConfig } from '@/types';
import { ToolDefinition } from '@/modules/core/tools';

const OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions';

export const DEFAULT_MODEL = 'openrouter/free';

const FREE_MODELS = [
  'openrouter/free',
  'google/gemma-3-1b-it:free',
  'google/gemma-3-4b-it:free',
  'meta-llama/llama-3.3-70b-instruct:free',
  'meta-llama/llama-3.1-8b-instruct:free',
  'qwen/qwen3-235b-a22b:free',
  'qwen/qwen3-coder:free',
  'deepseek/deepseek-r1:free',
  'deepseek/deepseek-chat-v3-0324:free',
  'microsoft/phi-4-reasoning-plus:free',
];

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

  const requestedModel = config.model || DEFAULT_MODEL;
  const modelsToTry = requestedModel === 'openrouter/free'
    ? FREE_MODELS
    : [requestedModel];

  let lastError: Error | null = null;

  for (const model of modelsToTry) {
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

    try {
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
          console.log(`[LLM] ${model} rate limited, trying next...`);
          lastError = new Error(`RATE_LIMIT: ${model}`);
          continue;
        }
        if (response.status === 404) {
          console.log(`[LLM] ${model} not found, trying next...`);
          lastError = new Error(`404: ${model}`);
          continue;
        }
        throw new Error(`OpenRouter error ${response.status}: ${errorBody}`);
      }

      const data = await response.json();
      const choice = data.choices[0];

      if (model !== requestedModel) {
        console.log(`[LLM] Used fallback model: ${model}`);
      }

      return {
        content: choice?.message?.content || '',
        model: data.model,
        tool_calls: choice?.message?.tool_calls,
        usage: data.usage,
      };
    } catch (err: any) {
      if (err.message?.startsWith('RATE_LIMIT:') || err.message?.startsWith('404:')) {
        lastError = err;
        continue;
      }
      throw err;
    }
  }

  if (lastError?.message?.startsWith('RATE_LIMIT:')) {
    const retryMatch = lastError.message.match(/retry_after_seconds.*?(\d+)/);
    const retryAfter = retryMatch ? parseInt(retryMatch[1]) : 25;
    throw new Error(`RATE_LIMIT:${retryAfter}`);
  }

  throw lastError || new Error('All models failed');
}

export async function chatCompletionStream(
  messages: ChatCompletionMessage[],
  config: Partial<LLMConfig> = {}
): Promise<ReadableStream<Uint8Array>> {
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error('OPENROUTER_API_KEY не задан');
  }

  const requestedModel = config.model || DEFAULT_MODEL;
  const modelsToTry = requestedModel === 'openrouter/free'
    ? FREE_MODELS
    : [requestedModel];

  let lastError: Error | null = null;

  for (const model of modelsToTry) {
    try {
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
          stream: true,
          temperature: config.temperature ?? 0.7,
        }),
      });

      if (!response.ok) {
        if (response.status === 429 || response.status === 404) {
          console.log(`[LLM] ${model} ${response.status === 429 ? 'rate limited' : 'not found'}, trying next...`);
          lastError = new Error(`${response.status}: ${model}`);
          continue;
        }
        throw new Error(`OpenRouter stream error ${response.status}`);
      }

      return response.body!;
    } catch (err: any) {
      if (err.message?.startsWith('429:') || err.message?.startsWith('404:')) {
        lastError = err;
        continue;
      }
      throw err;
    }
  }

  throw lastError || new Error('All stream models failed');
}
