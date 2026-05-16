/**
 * МОДУЛЬ: Долгосрочная память (MySQL)
 *
 * Сохраняет важные факты из диалогов в MySQL базу данных.
 * При следующих запросах — инжектирует в системный промпт.
 */

import { AgentContext, AgentModuleInterface } from '@/types';

const MAX_MEMORIES_IN_CONTEXT = 10;

export class LongTermMemoryModule implements AgentModuleInterface {
  name = 'long-term-memory';

  async onBeforeMessage(ctx: AgentContext): Promise<AgentContext> {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/memory/user/${ctx.userId}?agent_id=${ctx.agentId}&limit=${MAX_MEMORIES_IN_CONTEXT}`);
      
      if (res.ok) {
        const memories = await res.json();
        
        if (memories && memories.length > 0) {
          const memoryBlock = memories
            .map((m: any, i: number) => `[${i + 1}] ${m.content}`)
            .join('\n');

          return {
            ...ctx,
            systemPrompt:
              ctx.systemPrompt +
              `\n\n## Известные факты о пользователе:\n${memoryBlock}\n\nКогда пользователь просит запомнить что-то — ответь в формате: MEMORY: <текст для сохранения>`,
          };
        }
      }
    } catch (err) {
      console.error('[LongTermMemoryModule] Ошибка загрузки памяти:', err);
    }

    return ctx;
  }

  async onAfterMessage(ctx: AgentContext, response: string): Promise<void> {
    const match = response.match(/MEMORY:\s*(.+?)(?:\n|$)/i);
    if (match) {
      const content = match[1].trim();
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/memory/user/${ctx.userId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            content,
            agent_id: ctx.agentId,
            importance: 5,
            tags: ['user-fact'],
          }),
        });
      } catch (err) {
        console.error('[LongTermMemoryModule] Ошибка сохранения:', err);
      }
    }
  }
}