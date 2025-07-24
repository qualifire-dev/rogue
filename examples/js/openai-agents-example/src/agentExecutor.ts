import { BaseAgentExecutor } from './baseAgentExecutor.js';
import { Message, TextPart } from '@a2a-js/sdk';
import { AgentInputItem, run } from '@openai/agents';

abstract class BaseOpenAIAgentExecutor extends BaseAgentExecutor {
  protected convertMessages(historyForAgent: Message[]): AgentInputItem[] {
    // Convert A2A messages to correct format
    return historyForAgent.map(m => ({
        role: m.role === 'agent' ? 'assistant' : 'user',
        content: m.parts
          .filter((p): p is TextPart => p.kind === 'text' && !!(p as TextPart).text)
          .map(p => ({
            type: "input_text",
            text: (p as TextPart).text
          }))
      } as AgentInputItem)
    );
  }
}

export class OpenAIStreamExecutor extends BaseOpenAIAgentExecutor {
  public constructor(agent: any) {
    super(agent);
  }

  protected async runAgent(messages: Message[]): Promise<string | ReadableStream<string>> {
    const convertedMessages: AgentInputItem[] = this.convertMessages(messages);
    const stream = await run(this.agent, convertedMessages, {stream: true});
    return stream.toTextStream() as ReadableStream<string>;
  }
}

export class OpenAINonStreamExecutor extends BaseOpenAIAgentExecutor {
  public constructor(agent: any) {
    super(agent);
  }

  protected async runAgent(messages: Message[]): Promise<string | ReadableStream<string>> {
    const convertedMessages: AgentInputItem[] = this.convertMessages(messages);
    const result = await run(this.agent, convertedMessages, {stream: false});
    return result.finalOutput;
  }
}
