import { BaseAgentExecutor } from './baseAgentExecutor.js';
export class ReactAgentExecutor extends BaseAgentExecutor {
    constructor(agent) {
        super(agent);
    }
    convertMessages(historyForAgent) {
        // Convert A2A messages to correct format
        return historyForAgent.map(m => ({
            role: m.role === 'agent' ? 'assistant' : 'user',
            content: m.parts
                .filter((p) => p.kind === 'text' && !!p.text)
                .map(p => p.text)
                .join('\n')
        }));
    }
    async runAgent(messages, contextId) {
        const convertedMessages = this.convertMessages(messages);
        const input = { convertedMessages };
        const config = { configurable: { thread_id: contextId } };
        return await this.agent.stream(input, {
            ...config,
            streamMode: "values",
        });
    }
}
//# sourceMappingURL=agentExecutor.js.map