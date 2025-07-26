import { AgentExecutor, ExecutionEventBus, RequestContext } from '@a2a-js/sdk/server';
export declare class OpenAIAgentExecutor implements AgentExecutor {
    private cancelledTasks;
    private agent;
    constructor(agent: any);
    cancelTask: (taskId: string, eventBus: ExecutionEventBus) => Promise<void>;
    execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void>;
}
