import { AgentContext, AgentModuleInterface, ChatCompletionMessage } from '@/types';
import { chatCompletion, chatCompletionStream, LLMResponse } from '@/modules/core/llm/openrouter';

/**
 * AgentRuntime — ядро исполнения агента.
 *
 * Принцип «Добавляй — не меняй»:
 * Новые модули регистрируются через registerModule().
 * Ядро вызывает хуки модулей в нужном порядке.
 */
export class AgentRuntime {
  private modules: AgentModuleInterface[] = [];

  /** Регистрация нового модуля */
  registerModule(module: AgentModuleInterface): this {
    this.modules.push(module);
    return this;
  }

  /**
   * Обработка сообщения пользователя.
   * 1. Вызывает onBeforeMessage у всех модулей (модификация контекста)
   * 2. Выполняет LLM запрос
   * 3. Вызывает onAfterMessage у всех модулей (сохранение, логирование)
   */
  async processMessage(ctx: AgentContext): Promise<LLMResponse> {
    // 1. Обогащаем контекст через модули (память, RAG, системный промпт)
    let enrichedCtx = { ...ctx };
    for (const mod of this.modules) {
      if (mod.onBeforeMessage) {
        enrichedCtx = await mod.onBeforeMessage(enrichedCtx);
      }
    }

    // 2. Собираем сообщения для LLM
    const messages: ChatCompletionMessage[] = [
      { role: 'system', content: enrichedCtx.systemPrompt },
      ...enrichedCtx.messages,
    ];

    // 3. Вызов LLM
    const response = await chatCompletion(messages, {
      model: enrichedCtx.metadata.model as string | undefined,
    });

    // 4. Постобработка через модули (сохранение в память и т.д.)
    for (const mod of this.modules) {
      if (mod.onAfterMessage) {
        await mod.onAfterMessage(enrichedCtx, response.content).catch((err) =>
          console.error(`[AgentRuntime] Module ${mod.name} onAfterMessage error:`, err)
        );
      }
    }

    return response;
  }

  /** Стриминговая обработка */
  async processMessageStream(ctx: AgentContext): Promise<ReadableStream<Uint8Array>> {
    let enrichedCtx = { ...ctx };
    for (const mod of this.modules) {
      if (mod.onBeforeMessage) {
        enrichedCtx = await mod.onBeforeMessage(enrichedCtx);
      }
    }

    const messages: ChatCompletionMessage[] = [
      { role: 'system', content: enrichedCtx.systemPrompt },
      ...enrichedCtx.messages,
    ];

    return chatCompletionStream(messages, {
      model: enrichedCtx.metadata.model as string | undefined,
    });
  }
}

/** Singleton рантайм (без модулей — добавляются в api routes / server) */
export const agentRuntime = new AgentRuntime();
