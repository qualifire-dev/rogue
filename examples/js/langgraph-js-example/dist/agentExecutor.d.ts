import { BaseAgentExecutor } from './baseAgentExecutor.js';
import { Message } from '@a2a-js/sdk';
export declare class ReactAgentExecutor extends BaseAgentExecutor {
    constructor(agent: any);
    protected convertMessages(historyForAgent: Message[]): {
        role: string;
        content: string;
    }[];
    protected runAgent(messages: Message[], contextId: string): Promise<string | ReadableStream<string>>;
}
