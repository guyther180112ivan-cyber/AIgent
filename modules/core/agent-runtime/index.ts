import { AgentContext, AgentModuleInterface, ChatCompletionMessage } from '@/types';
import { chatCompletion, chatCompletionStream, LLMResponse } from '@/modules/core/llm/openrouter';

const FETCH_URL_RE = /\[FETCH_URL:\s*(https?:\/\/[^\]]+)\]/i;

export class AgentRuntime {
  private modules: AgentModuleInterface[] = [];

  registerModule(module: AgentModuleInterface): this {
    this.modules.push(module);
    return this;
  }

  async processMessage(ctx: AgentContext): Promise<LLMResponse> {
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

    const response = await chatCompletion(messages, {
      model: enrichedCtx.metadata.model as string | undefined,
    });

    let finalContent = response.content;

    const fetchMatch = finalContent.match(FETCH_URL_RE);
    if (fetchMatch) {
      const url = fetchMatch[1];
      console.log('[AgentRuntime] Fetching URL from LLM response:', url);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
        const fetchRes = await fetch(`${baseUrl}/api/fetch_url?url=${encodeURIComponent(url)}`);
        if (fetchRes.ok) {
          const data = await fetchRes.json();
          const fetchBlock = `\n\n## Содержимое ${url}:\n${data.content || data.title}\n\nОтветь пользователю на основе этой информации.`;
          const reQueryMessages: ChatCompletionMessage[] = [
            { role: 'system', content: enrichedCtx.systemPrompt + fetchBlock },
            ...enrichedCtx.messages,
          ];
          const reResponse = await chatCompletion(reQueryMessages, {
            model: enrichedCtx.metadata.model as string | undefined,
          });
          finalContent = reResponse.content;
        }
      } catch (err) {
        console.error('[AgentRuntime] Error fetching URL after LLM response:', err);
      }
    }

    for (const mod of this.modules) {
      if (mod.onAfterMessage) {
        await mod.onAfterMessage(enrichedCtx, finalContent).catch((err) =>
          console.error(`[AgentRuntime] Module ${mod.name} onAfterMessage error:`, err)
        );
      }
    }

    return { ...response, content: finalContent };
  }

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

export const agentRuntime = new AgentRuntime();