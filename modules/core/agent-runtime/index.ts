import { AgentContext, ChatCompletionMessage } from '@/types';
import { chatCompletion, chatCompletionStream, LLMResponse } from '@/modules/core/llm/openrouter';
import { TOOLS, executeTool, ToolDefinition } from '@/modules/core/tools';

const MAX_TOOL_ROUNDS = 0;
const MAX_RETRIES = 3;

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export class AgentRuntime {
  private extraTools: ToolDefinition[] = [];
  private onToolCall?: (name: string, args: Record<string, string>) => void;

  registerTool(tool: ToolDefinition): this {
    this.extraTools.push(tool);
    return this;
  }

  setToolCallHandler(handler: (name: string, args: Record<string, string>) => void): this {
    this.onToolCall = handler;
    return this;
  }

  private async callWithRetry(
    messages: ChatCompletionMessage[],
    model: string | undefined,
    tools: ToolDefinition[]
  ): Promise<LLMResponse> {
    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
      try {
        return await chatCompletion(messages, { model }, tools);
      } catch (err: any) {
        if (err.message?.startsWith('RATE_LIMIT:') && attempt < MAX_RETRIES - 1) {
          const retryAfter = parseInt(err.message.split(':')[1]) || 25;
          console.log(`[AgentRuntime] Rate limited, waiting ${retryAfter}s (attempt ${attempt + 1}/${MAX_RETRIES})`);
          await sleep(retryAfter * 1000);
          continue;
        }
        throw err;
      }
    }
    throw new Error('Max retries exceeded');
  }

  async processMessage(ctx: AgentContext): Promise<LLMResponse> {
    const messages: ChatCompletionMessage[] = [
      { role: 'system', content: ctx.systemPrompt },
      ...ctx.messages,
    ];

    const tools = MAX_TOOL_ROUNDS > 0 ? [...TOOLS, ...this.extraTools] : [];

    for (let round = 0; round < MAX_TOOL_ROUNDS; round++) {
      const response = await this.callWithRetry(messages, ctx.metadata.model as string | undefined, tools);

      if (!response.tool_calls || response.tool_calls.length === 0) {
        return response;
      }

      messages.push({
        role: 'assistant',
        content: response.content || null,
        tool_calls: response.tool_calls,
      });

      for (const toolCall of response.tool_calls) {
        let args: Record<string, string> = {};
        try {
          args = JSON.parse(toolCall.function.arguments);
        } catch {
          args = {};
        }

        console.log(`[AgentRuntime] Tool call: ${toolCall.function.name}`, args);
        this.onToolCall?.(toolCall.function.name, args);

        const result = await executeTool(toolCall.function.name, args, ctx);

        messages.push({
          role: 'tool',
          content: result,
          tool_call_id: toolCall.id,
          name: toolCall.function.name,
        });
      }
    }

    const finalResponse = await this.callWithRetry(messages, ctx.metadata.model as string | undefined, tools);
    return finalResponse;
  }

  async processMessageStream(ctx: AgentContext): Promise<ReadableStream<Uint8Array>> {
    const messages: ChatCompletionMessage[] = [
      { role: 'system', content: ctx.systemPrompt },
      ...ctx.messages,
    ];

    return chatCompletionStream(messages, {
      model: ctx.metadata.model as string | undefined,
    });
  }
}

export const agentRuntime = new AgentRuntime();
