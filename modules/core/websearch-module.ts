import { AgentContext, AgentModuleInterface } from '@/types';
import { webSearch, formatSearchResults } from '@/lib/websearch';

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

        console.log('[WebSearchModule] Searching for:', query);
        
        const searchResults = await webSearch(query, 5);
        console.log('[WebSearchModule] Found results:', searchResults.results.length);

        if (searchResults.results.length > 0) {
          const formattedResults = formatSearchResults(searchResults);
          
          return {
            ...ctx,
            systemPrompt: ctx.systemPrompt + `\n\n## Веб-поиск (выполнен перед ответом):\n${formattedResults}\n\nИспользуй эту актуальную информацию из интернета для ответа.`,
          };
        }
      } catch (err) {
        console.error('[WebSearchModule] Ошибка поиска:', err);
      }
    }

    return ctx;
  }
}