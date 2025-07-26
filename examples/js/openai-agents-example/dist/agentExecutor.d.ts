import { BaseAgentExecutor } from './baseAgentExecutor.js';
import { Message } from '@a2a-js/sdk';
import { AgentInputItem } from '@openai/agents';
declare abstract class BaseOpenAIAgentExecutor extends BaseAgentExecutor {
    protected convertMessages(historyForAgent: Message[]): AgentInputItem[];
}
export declare class OpenAIStreamExecutor extends BaseOpenAIAgentExecutor {
    constructor(agent: any);
    protected runAgent(messages: Message[]): Promise<string | ReadableStream<string>>;
}
export declare class OpenAINonStreamExecutor extends BaseOpenAIAgentExecutor {
    constructor(agent: any);
    protected runAgent(messages: Message[]): Promise<string | ReadableStream<string>>;
}
export {};
