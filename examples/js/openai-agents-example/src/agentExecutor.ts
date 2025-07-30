import { BaseAgentExecutor } from './baseAgentExecutor.js';
import { Message, TextPart } from '@a2a-js/sdk';
import { AgentInputItem, run } from '@openai/agents';
import { Readable } from 'stream';

export class OpenAIStreamExecutor extends BaseAgentExecutor {
  public constructor(agent: any) {
    super(agent);
  }

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

  protected async runAgent(messages: Message[]): Promise<Readable> {
    const convertedMessages: AgentInputItem[] = this.convertMessages(messages);
    const stream = await run(this.agent, convertedMessages, {stream: true});
    return stream.toTextStream({compatibleWithNodeStreams: true}) as Readable;
  }
}
