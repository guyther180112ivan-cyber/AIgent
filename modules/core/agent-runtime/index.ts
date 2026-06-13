import { AgentContext, ChatCompletionMessage } from '@/types';
import { chatCompletion, chatCompletionStream, LLMResponse } from '@/modules/core/llm/openrouter';
import { TOOLS, executeTool, ToolDefinition } from '@/modules/core/tools';

const MAX_TOOL_ROUNDS = 6;

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

  async processMessage(ctx: AgentContext): Promise<LLMResponse> {
    const allTools = [...TOOLS, ...this.extraTools];

    const messages: ChatCompletionMessage[] = [
      { role: 'system', content: ctx.systemPrompt },
      ...ctx.messages,
    ];

    for (let round = 0; round < MAX_TOOL_ROUNDS; round++) {
      const response = await chatCompletion(messages, {
        model: ctx.metadata.model as string | undefined,
      }, allTools);

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

    const finalResponse = await chatCompletion(messages, {
      model: ctx.metadata.model as string | undefined,
    }, allTools);

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
