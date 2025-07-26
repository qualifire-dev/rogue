import { v4 as uuidv4 } from 'uuid';
// Store for conversation contexts
const contexts = new Map();
export class BaseAgentExecutor {
    constructor(agent) {
        this.cancelledTasks = new Set();
        this.cancelTask = async (taskId, eventBus) => {
            this.cancelledTasks.add(taskId);
            // The execute loop is responsible for publishing the final state
        };
        this.agent = agent;
    }
    publishInitialTask(eventBus, taskId, contextId, userMessage) {
        const initialTask = {
            kind: 'task',
            id: taskId,
            contextId: contextId,
            status: {
                state: "submitted",
                timestamp: new Date().toISOString(),
            },
            history: [userMessage], // Start history with the current user message
            metadata: userMessage.metadata, // Carry over metadata from message if any
        };
        eventBus.publish(initialTask);
    }
    publishStatusUpdate(eventBus, taskId, contextId, messageText = null, state = "working", final = false) {
        const workingStatusUpdate = {
            kind: 'status-update',
            taskId: taskId,
            contextId: contextId,
            status: {
                state: state,
                message: {
                    kind: 'message',
                    role: 'agent',
                    messageId: uuidv4(),
                    parts: messageText ? [{ kind: 'text', text: messageText }] : [],
                    taskId: taskId,
                    contextId: contextId,
                },
                timestamp: new Date().toISOString(),
            },
            final: final,
        };
        eventBus.publish(workingStatusUpdate);
    }
    /**
     * Handles the cancellation of a task by publishing a "canceled" status update.
     */
    publishTaskCancellation(taskId, contextId, eventBus) {
        console.log(`[AgentExecutor] Request cancelled for task: ${taskId}`);
        const cancelledUpdate = {
            kind: 'status-update',
            taskId: taskId,
            contextId: contextId,
            status: {
                state: 'canceled',
                timestamp: new Date().toISOString(),
            },
            final: true,
        };
        eventBus.publish(cancelledUpdate);
    }
    publishTaskCompletion(taskId, contextId, eventBus) {
        const finalUpdate = {
            kind: 'status-update',
            taskId: taskId,
            contextId: contextId,
            status: {
                state: "completed",
                timestamp: new Date().toISOString(),
            },
            final: true,
        };
        eventBus.publish(finalUpdate);
    }
    publishTaskError(taskId, contextId, eventBus, error) {
        const errorUpdate = {
            kind: 'status-update',
            taskId: taskId,
            contextId: contextId,
            status: {
                state: "failed",
                message: {
                    kind: 'message',
                    role: 'agent',
                    messageId: uuidv4(),
                    parts: [{ kind: 'text', text: `Agent error: ${error.message}` }],
                    taskId: taskId,
                    contextId: contextId,
                },
                timestamp: new Date().toISOString(),
            },
            final: true,
        };
        eventBus.publish(errorUpdate);
    }
    addMessageToHistory(contextId, message) {
        const historyForAgent = contexts.get(contextId) || [];
        if (!historyForAgent.find(m => m.messageId === message.messageId)) {
            historyForAgent.push(message);
            contexts.set(contextId, historyForAgent);
        }
        return historyForAgent;
    }
    async handleStreamResponse(eventBus, taskId, contextId, existingTask, userMessage, response) {
        let finalResponse = "";
        // 1. Publish initial Task event if it's a new task
        if (!existingTask) {
            this.publishInitialTask(eventBus, taskId, contextId, userMessage);
        }
        // 2. Publish "working" status update
        this.publishStatusUpdate(eventBus, taskId, contextId);
        // 3. Stream the agent's response
        for await (const textPart of response) {
            finalResponse += textPart;
            this.publishStatusUpdate(eventBus, taskId, contextId, textPart);
        }
        // 4. Publish "completed" status update
        this.publishTaskCompletion(taskId, contextId, eventBus);
        return finalResponse;
    }
    async handleNonStreamResponse(eventBus, agentMessage) {
        eventBus.publish(agentMessage);
    }
    async execute(requestContext, eventBus) {
        const userMessage = requestContext.userMessage;
        const existingTask = requestContext.task;
        // Determine IDs for the task and context
        const taskId = existingTask?.id || uuidv4();
        const contextId = userMessage.contextId || existingTask?.contextId || uuidv4();
        console.log(`[AgentExecutor] Processing message ${userMessage.messageId} for task ${taskId} (context: ${contextId})`);
        const historyForAgent = this.addMessageToHistory(contextId, userMessage);
        // Check if the task has been cancelled before starting
        if (this.cancelledTasks.has(taskId)) {
            this.publishTaskCancellation(taskId, contextId, eventBus);
            return;
        }
        try {
            // Run the agent - Can return a stream or a string.
            const response = await this.runAgent(historyForAgent);
            // Create the agent's final message for the history - we will fill the parts later
            const agentMessage = {
                kind: 'message',
                role: 'agent',
                messageId: uuidv4(),
                parts: [], // We will fill this later
                taskId: taskId,
                contextId: contextId,
            };
            if (response instanceof ReadableStream) {
                const aggregatedResponse = await this.handleStreamResponse(eventBus, taskId, contextId, existingTask, userMessage, response);
                agentMessage.parts.push({ kind: 'text', text: aggregatedResponse });
            }
            else { // response is a string
                agentMessage.parts.push({ kind: 'text', text: response });
                await this.handleNonStreamResponse(eventBus, agentMessage);
            }
            this.addMessageToHistory(contextId, agentMessage);
            console.log(`[AgentExecutor] Task ${taskId} finished with state: completed`);
        }
        catch (error) {
            console.error(`[AgentExecutor] Error processing task ${taskId}:`, error);
            this.publishTaskError(taskId, contextId, eventBus, error);
        }
    }
}
//# sourceMappingURL=baseAgentExecutor.js.map