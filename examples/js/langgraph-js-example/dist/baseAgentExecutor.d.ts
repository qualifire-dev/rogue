import { Message } from '@a2a-js/sdk';
import { AgentExecutor, ExecutionEventBus, RequestContext } from '@a2a-js/sdk/server';
export declare abstract class BaseAgentExecutor implements AgentExecutor {
    private cancelledTasks;
    protected readonly agent: any;
    protected constructor(agent: any);
    cancelTask: (taskId: string, eventBus: ExecutionEventBus) => Promise<void>;
    private publishInitialTask;
    private publishStatusUpdate;
    /**
     * Handles the cancellation of a task by publishing a "canceled" status update.
     */
    private publishTaskCancellation;
    private publishTaskCompletion;
    private publishTaskError;
    private addMessageToHistory;
    protected abstract runAgent(messages: Message[], contextId: string): Promise<string | ReadableStream<string>>;
    private handleStreamResponse;
    private handleNonStreamResponse;
    execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void>;
}
