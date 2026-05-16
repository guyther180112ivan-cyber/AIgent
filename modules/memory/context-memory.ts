/**
 * МОДУЛЬ: Контекстная память (краткосрочная)
 *
 * Хранит историю сообщений в рамках одной беседы.
 * Подгружает последние N сообщений перед каждым запросом к LLM.
 */

import { AgentContext, AgentModuleInterface } from '@/types';
import { getMessagesByConversationId } from '@/lib/messages';

const DEFAULT_HISTORY_LIMIT = 20;

export class ContextMemoryModule implements AgentModuleInterface {
  name = 'context-memory';
  private historyLimit: number;

  constructor(historyLimit = DEFAULT_HISTORY_LIMIT) {
    this.historyLimit = historyLimit;
  }

  async onBeforeMessage(ctx: AgentContext): Promise<AgentContext> {
    try {
      const messages = getMessagesByConversationId(ctx.conversationId);

      if (messages && messages.length > 0) {
        const recentMessages = messages.slice(-this.historyLimit);
        return {
          ...ctx,
          messages: recentMessages.map((m) => ({
            role: m.role as 'user' | 'assistant' | 'system',
            content: m.content,
          })),
        };
      }
    } catch (err) {
      console.error('[ContextMemoryModule] Ошибка загрузки истории:', err);
    }

    return ctx;
  }
}