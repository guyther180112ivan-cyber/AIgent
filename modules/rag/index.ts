/**
 * МОДУЛЬ: RAG (Retrieval-Augmented Generation)
 *
 * Полнотекстовый поиск по загруженным документам.
 * В будущем: pgvector для семантического поиска.
 */

import { AgentContext, AgentModuleInterface } from '@/types';
import { createServiceClient } from '@/modules/core/supabase/server';

const MAX_RAG_CHUNKS = 5;

export class RAGModule implements AgentModuleInterface {
  name = 'rag';

  async onBeforeMessage(ctx: AgentContext): Promise<AgentContext> {
    try {
      const lastUserMessage = [...ctx.messages]
        .reverse()
        .find((m) => m.role === 'user');

      if (!lastUserMessage) return ctx;

      const query = lastUserMessage.content.substring(0, 200);
      const supabase = await createServiceClient();

      const { data: chunks } = await supabase
        .from('rag_chunks')
        .select('content, rag_documents(name)')
        .textSearch('content', query)
        .limit(MAX_RAG_CHUNKS);

      if (chunks && chunks.length > 0) {
        const ragBlock = chunks
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          .map((c: any) =>
            `[${c.rag_documents?.name || 'Документ'}]: ${c.content}`
          )
          .join('\n\n');

        return {
          ...ctx,
          systemPrompt:
            ctx.systemPrompt +
            `\n\n## Релевантные документы из базы знаний:\n${ragBlock}`,
        };
      }
    } catch (err) {
      console.error('[RAGModule] Ошибка:', err);
    }

    return ctx;
  }
}

export { RAGModule as default };
