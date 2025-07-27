import { BaseAgentExecutor } from './baseAgentExecutor.js';
import { Message, TextPart } from '@a2a-js/sdk';

export class VercelAgentExecutor extends BaseAgentExecutor {
  public constructor(agent: any) {
    super(agent);
  }

  protected convertMessages(historyForAgent: Message[]): {role: 'user' | 'assistant', content: string}[]  {
    // Convert A2A messages to Vercel format
    return historyForAgent.map(m => ({
      role: m.role === 'agent' ? 'assistant' : 'user',
      content: m.parts
        .filter((p): p is TextPart => p.kind === 'text' && !!(p as TextPart).text)
        .map(p => ((p as TextPart).text))
        .join("")
    }));
  }

  protected async runAgent(messages: Message[]): Promise<string | ReadableStream<string>> {
    const convertedMessages: {role: 'user' | 'assistant', content: string}[] = this.convertMessages(messages);
    return this.agent.stream(convertedMessages);
  }
}
