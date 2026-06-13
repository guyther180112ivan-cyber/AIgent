import { ChatCompletionMessage, AgentContext } from '@/types';
import { webSearch, formatSearchResults, weatherSearch, formatWeatherData } from '@/lib/websearch';

export interface ToolDefinition {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: {
      type: 'object';
      properties: Record<string, {
        type: string;
        description: string;
        enum?: string[];
      }>;
      required: string[];
    };
  };
}

export const TOOLS: ToolDefinition[] = [
  {
    type: 'function',
    function: {
      name: 'web_search',
      description: 'Поиск информации в интернете. Используй когда пользователь просит найти что-то, узнать актуальную информацию, погоду, новости, цены и т.д.',
      parameters: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'Поисковый запрос',
          },
        },
        required: ['query'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_weather',
      description: 'Получить текущую погоду и прогноз в указанном городе.',
      parameters: {
        type: 'object',
        properties: {
          city: {
            type: 'string',
            description: 'Название города (например: Москва, London, Paris)',
          },
        },
        required: ['city'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'fetch_url',
      description: 'Загрузить и прочитать содержимое веб-страницы по URL. Используй когда пользователь даёт ссылку или просит прочитать сайт.',
      parameters: {
        type: 'object',
        properties: {
          url: {
            type: 'string',
            description: 'URL страницы для загрузки',
          },
        },
        required: ['url'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'save_memory',
      description: 'Сохранить факт о пользователе в долгосрочную память. Используй когда пользователь просит запомнить, записать, не забыть что-то.',
      parameters: {
        type: 'object',
        properties: {
          content: {
            type: 'string',
            description: 'Текст для запоминания',
          },
        },
        required: ['content'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'get_memory',
      description: 'Получить ранее сохранённые факты о пользователе из долгосрочной памяти.',
      parameters: {
        type: 'object',
        properties: {},
        required: [],
      },
    },
  },
];

export async function executeTool(
  name: string,
  args: Record<string, string>,
  ctx: AgentContext
): Promise<string> {
  switch (name) {
    case 'web_search': {
      const results = await webSearch(args.query, 5);
      return formatSearchResults(results);
    }

    case 'get_weather': {
      const result = await weatherSearch(args.city);
      if (result.success && result.data) {
        return formatWeatherData(result.data);
      }
      return `Ошибка получения погоды: ${result.error || 'Город не найден'}`;
    }

    case 'fetch_url': {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
        const res = await fetch(`${baseUrl}/api/fetch_url?url=${encodeURIComponent(args.url)}`);
        if (res.ok) {
          const data = await res.json();
          return `Заголовок: ${data.title}\n\nСодержимое:\n${data.content}`;
        }
        const err = await res.json();
        return `Ошибка загрузки: ${err.error || 'Неизвестная ошибка'}`;
      } catch (err) {
        return `Ошибка загрузки: ${String(err)}`;
      }
    }

    case 'save_memory': {
      try {
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/memory/user/${ctx.userId}`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              content: args.content,
              agent_id: ctx.agentId,
              importance: 5,
              tags: ['user-fact'],
            }),
          }
        );
        return `Запомнил: "${args.content}"`;
      } catch {
        return 'Не удалось сохранить в память';
      }
    }

    case 'get_memory': {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/memory/user/${ctx.userId}?agent_id=${ctx.agentId}&limit=20`
        );
        if (res.ok) {
          const memories = await res.json();
          if (memories && memories.length > 0) {
            return memories.map((m: any, i: number) => `[${i + 1}] ${m.content}`).join('\n');
          }
          return 'Нет сохранённых фактов.';
        }
        return 'Ошибка чтения памяти.';
      } catch {
        return 'Ошибка чтения памяти.';
      }
    }

    default:
      return `Неизвестный инструмент: ${name}`;
  }
}
