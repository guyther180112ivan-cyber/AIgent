import { AgentContext, AgentModuleInterface } from '@/types';

interface FetchResult {
  url: string;
  title: string;
  content: string;
}

const URL_REGEX = /https?:\/\/[^\s<>"']+/gi;

function extractUrls(text: string): string[] {
  const matches = text.matchAll(URL_REGEX);
  const urls: string[] = [];
  for (const m of matches) {
    const clean = m[0].replace(/[.,;:!?)]+$/, '');
    try {
      new URL(clean);
      urls.push(clean);
    } catch {}
  }
  return urls;
}

export class FetchURLModule implements AgentModuleInterface {
  name = 'fetch-url';

  async onBeforeMessage(ctx: AgentContext): Promise<AgentContext> {
    const lastUserMessage = ctx.messages[ctx.messages.length - 1]?.content || '';
    const lower = lastUserMessage.toLowerCase();

    const urls = extractUrls(lastUserMessage);
    const hasFetchIntent =
      urls.length > 0 ||
      lower.includes('прочитай сайт') ||
      lower.includes('открой сайт') ||
      lower.includes('перейди по ссылке') ||
      lower.includes('fetch url') ||
      lower.includes('прочитай страницу') ||
      lower.includes('что на сайте') ||
      lower.includes('что по ссылке');

    if (!hasFetchIntent) {
      return {
        ...ctx,
        systemPrompt: ctx.systemPrompt + `\n\nТы можешь читать содержимое веб-страниц по URL. Если пользователь просит прочитать сайт или даёт ссылку, используй функцию fetch_url. Для этого напиши в ответе: [FETCH_URL: https://...] и бот подставит содержимое страницы перед следующим ответом.`,
      };
    }

    const results: FetchResult[] = [];

    for (const url of urls) {
      try {
        console.log('[FetchURLModule] Fetching:', url);
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/api/fetch_url?url=${encodeURIComponent(url)}`
        );

        if (response.ok) {
          const data = await response.json();
          results.push(data);
        } else {
          const err = await response.json();
          results.push({
            url,
            title: 'Ошибка',
            content: `[Ошибка загрузки: ${err.error || 'Неизвестная ошибка'}]`,
          });
        }
      } catch (err) {
        console.error('[FetchURLModule] Error fetching', url, err);
        results.push({
          url,
          title: 'Ошибка',
          content: `[Ошибка загрузки: ${err}]`,
        });
      }
    }

    if (results.length > 0) {
      const resultsBlock = results
        .map(
          (r) =>
            `\n\nURL: ${r.url}\nЗаголовок: ${r.title}\n\nСодержимое:\n${r.content}`
        )
        .join('\n---\n');

      return {
        ...ctx,
        systemPrompt:
          ctx.systemPrompt +
          `\n\n## Загруженные веб-страницы:\n${resultsBlock}\n\nИспользуй содержимое страниц для ответа пользователю.`,
      };
    }

    return ctx;
  }
}