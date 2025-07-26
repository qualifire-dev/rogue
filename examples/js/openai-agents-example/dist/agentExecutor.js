import { BaseAgentExecutor } from './baseAgentExecutor.js';
import { run } from '@openai/agents';
class BaseOpenAIAgentExecutor extends BaseAgentExecutor {
    convertMessages(historyForAgent) {
        // Convert A2A messages to correct format
        return historyForAgent.map(m => ({
            role: m.role === 'agent' ? 'assistant' : 'user',
            content: m.parts
                .filter((p) => p.kind === 'text' && !!p.text)
                .map(p => ({
                type: "input_text",
                text: p.text
            }))
        }));
    }
}
export class OpenAIStreamExecutor extends BaseOpenAIAgentExecutor {
    constructor(agent) {
        super(agent);
    }
    async runAgent(messages) {
        const convertedMessages = this.convertMessages(messages);
        const stream = await run(this.agent, convertedMessages, { stream: true });
        return stream.toTextStream();
    }
}
export class OpenAINonStreamExecutor extends BaseOpenAIAgentExecutor {
    constructor(agent) {
        super(agent);
    }
    async runAgent(messages) {
        const convertedMessages = this.convertMessages(messages);
        const result = await run(this.agent, convertedMessages, { stream: false });
        return result.finalOutput;
    }
}
//# sourceMappingURL=agentExecutor.js.map