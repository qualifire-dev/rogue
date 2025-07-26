import { AgentExecutor, ExecutionEventBus, RequestContext } from '@a2a-js/sdk/server';
import { VercelAgent } from './agent';
export declare class VercelAgentExecutor implements AgentExecutor {
    private cancelledTasks;
    private agent;
    constructor(agent: VercelAgent);
    cancelTask: (taskId: string, eventBus: ExecutionEventBus) => Promise<void>;
    execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void>;
}
