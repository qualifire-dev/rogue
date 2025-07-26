"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.VercelAgentExecutor = void 0;
const uuid_1 = require("uuid");
// Store for conversation contexts
const contexts = new Map();
class VercelAgentExecutor {
    constructor(agent) {
        this.cancelledTasks = new Set();
        this.cancelTask = async (taskId, eventBus) => {
            this.cancelledTasks.add(taskId);
            // The execute loop is responsible for publishing the final state
        };
        this.agent = agent;
    }
    async execute(requestContext, eventBus) {
        const userMessage = requestContext.userMessage;
        const existingTask = requestContext.task;
        // Determine IDs for the task and context
        const taskId = existingTask?.id || (0, uuid_1.v4)();
        const contextId = userMessage.contextId || existingTask?.contextId || (0, uuid_1.v4)();
        console.log(`[VercelAgentExecutor] Processing message ${userMessage.messageId} for task ${taskId} (context: ${contextId})`);
        // 1. Publish initial Task event if it's a new task
        if (!existingTask) {
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
        // 2. Publish "working" status update
        const workingStatusUpdate = {
            kind: 'status-update',
            taskId: taskId,
            contextId: contextId,
            status: {
                state: "working",
                message: {
                    kind: 'message',
                    role: 'agent',
                    messageId: (0, uuid_1.v4)(),
                    parts: [],
                    taskId: taskId,
                    contextId: contextId,
                },
                timestamp: new Date().toISOString(),
            },
            final: false,
        };
        eventBus.publish(workingStatusUpdate);
        // 3. Prepare messages for the agent
        const historyForAgent = contexts.get(contextId) || [];
        if (!historyForAgent.find(m => m.messageId === userMessage.messageId)) {
            historyForAgent.push(userMessage);
        }
        contexts.set(contextId, historyForAgent);
        // Convert A2A messages to Vercel format
        const messages = historyForAgent.map(m => ({
            role: m.role === 'agent' ? 'assistant' : 'user',
            content: m.parts
                .filter((p) => p.kind === 'text' && !!p.text)
                .map(p => (p.text))
                .join("")
        }));
        if (messages.length === 0) {
            console.warn(`[VercelAgentExecutor] No valid text messages found in history for task ${taskId}.`);
            const failureUpdate = {
                kind: 'status-update',
                taskId: taskId,
                contextId: contextId,
                status: {
                    state: "failed",
                    message: {
                        kind: 'message',
                        role: 'agent',
                        messageId: (0, uuid_1.v4)(),
                        parts: [{ kind: 'text', text: 'No message found to process.' }],
                        taskId: taskId,
                        contextId: contextId,
                    },
                    timestamp: new Date().toISOString(),
                },
                final: true,
            };
            eventBus.publish(failureUpdate);
            return;
        }
        try {
            // Check if the task has been cancelled before starting
            if (this.cancelledTasks.has(taskId)) {
                console.log(`[VercelAgentExecutor] Request cancelled for task: ${taskId}`);
                const cancelledUpdate = {
                    kind: 'status-update',
                    taskId: taskId,
                    contextId: contextId,
                    status: {
                        state: "canceled",
                        timestamp: new Date().toISOString(),
                    },
                    final: true,
                };
                eventBus.publish(cancelledUpdate);
                return;
            }
            // Use the existing config object
            const stream = this.agent.stream(messages);
            for await (const textPart of stream) {
                const intermediateUpdate = {
                    kind: 'status-update',
                    taskId: taskId,
                    contextId: contextId,
                    status: {
                        state: "working",
                        message: {
                            kind: 'message',
                            role: 'agent',
                            messageId: (0, uuid_1.v4)(),
                            parts: [{ kind: 'text', text: textPart }],
                            taskId: taskId,
                            contextId: contextId,
                        },
                        timestamp: new Date().toISOString(),
                    },
                    final: false,
                };
                eventBus.publish(intermediateUpdate);
            }
            // 5. Create the agent's final message
            const agentMessage = {
                kind: 'message',
                role: 'agent',
                messageId: (0, uuid_1.v4)(),
                parts: [],
                taskId: taskId,
                contextId: contextId,
            };
            historyForAgent.push(agentMessage);
            contexts.set(contextId, historyForAgent);
            // 6. Publish final task status update
            const finalUpdate = {
                kind: 'status-update',
                taskId: taskId,
                contextId: contextId,
                status: {
                    state: "completed",
                    message: agentMessage,
                    timestamp: new Date().toISOString(),
                },
                final: true,
            };
            eventBus.publish(finalUpdate);
            console.log(`[VercelAgentExecutor] Task ${taskId} finished with state: completed`);
        }
        catch (error) {
            console.error(`[VercelAgentExecutor] Error processing task ${taskId}:`, error);
            const errorUpdate = {
                kind: 'status-update',
                taskId: taskId,
                contextId: contextId,
                status: {
                    state: "failed",
                    message: {
                        kind: 'message',
                        role: 'agent',
                        messageId: (0, uuid_1.v4)(),
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
    }
}
exports.VercelAgentExecutor = VercelAgentExecutor;
//# sourceMappingURL=agentExecutor.js.map