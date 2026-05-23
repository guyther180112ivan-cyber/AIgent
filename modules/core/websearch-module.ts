import { AgentContext, AgentModuleInterface } from '@/types';
import { webSearch, formatSearchResults, weatherSearch, formatWeatherData } from '@/lib/websearch';

export class WebSearchModule implements AgentModuleInterface {
  name = 'websearch';

  async onBeforeMessage(ctx: AgentContext): Promise<AgentContext> {
    const lastUserMessage = ctx.messages[ctx.messages.length - 1]?.content || '';
    const lowerMessage = lastUserMessage.toLowerCase();

    const searchIndicators = [
      'найди', 'поиск', 'загугли', 'загуглить', 'погугли',
      'что такое', 'кто такой', 'кто такие', 'что это',
      'узнай', 'найди информацию', 'найди в интернете',
      'актуальн', 'последн', 'новост', '2024', '2025', '2026',
      'current', 'latest', 'today', 'now', 'recent',
      'погода', 'курс', 'цена', 'стоимость',
      'википедия', 'wikipedia',
    ];

    const needsSearch = searchIndicators.some(indicator =>
      lowerMessage.includes(indicator.toLowerCase())
    );

    if (needsSearch) {
      try {
        let query = lastUserMessage
          .replace(/найди|поиск|загугли|загуглить|погугли|что такое|кто такой|кто такие|что это|узнай|в интернете|в сети|покажи|расскажи/gi, '')
          .replace(/\s+/g, ' ')
          .trim();

        if (query.length < 2) {
          query = lastUserMessage;
        }

        query = query.substring(0, 200);
        console.log('[WebSearchModule] Query:', query);

        const extraBlocks: string[] = [];

        const isWeather = lowerMessage.includes('погода') || lowerMessage.includes('weather');
        if (isWeather) {
          const weatherResult = await weatherSearch(query);
          if (weatherResult.success && weatherResult.data) {
            extraBlocks.push(formatWeatherData(weatherResult.data));
          }
        }

        const searchResults = await webSearch(query, 5);
        console.log('[WebSearchModule] Bing results:', searchResults.results.length);

        if (searchResults.results.length > 0) {
          extraBlocks.push(formatSearchResults(searchResults));
        }

        if (extraBlocks.length > 0) {
          return {
            ...ctx,
            systemPrompt: ctx.systemPrompt + `\n\n## Веб-поиск (выполнен перед ответом):\n${extraBlocks.join('\n\n')}\n\nИспользуй эту актуальную информацию из интернета для ответа.`,
          };
        }
      } catch (err) {
        console.error('[WebSearchModule] Ошибка поиска:', err);
      }
    }

    return ctx;
  }
}