import { v4 as uuidv4 } from 'uuid';
// Store for conversation contexts
const contexts = new Map();
export class ReactAgentExecutor {
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
        const taskId = existingTask?.id || uuidv4();
        const contextId = userMessage.contextId || existingTask?.contextId || uuidv4();
        console.log(`[ReactAgentExecutor] Processing message ${userMessage.messageId} for task ${taskId} (context: ${contextId})`);
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
                    messageId: uuidv4(),
                    parts: [{ kind: 'text', text: 'Processing your request...' }],
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
        // Convert A2A messages to LangChain format
        const messages = historyForAgent.map(m => ({
            role: m.role === 'agent' ? 'assistant' : 'user',
            content: m.parts
                .filter((p) => p.kind === 'text' && !!p.text)
                .map(p => p.text)
                .join('\n')
        }));
        if (messages.length === 0) {
            console.warn(`[ReactAgentExecutor] No valid text messages found in history for task ${taskId}.`);
            const failureUpdate = {
                kind: 'status-update',
                taskId: taskId,
                contextId: contextId,
                status: {
                    state: "failed",
                    message: {
                        kind: 'message',
                        role: 'agent',
                        messageId: uuidv4(),
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
            // 4. Run the React agent
            const input = { messages };
            const config = { configurable: { thread_id: contextId } };
            // Check if the task has been cancelled before starting
            if (this.cancelledTasks.has(taskId)) {
                console.log(`[ReactAgentExecutor] Request cancelled for task: ${taskId}`);
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
            // Stream the agent execution
            let finalResponse = '';
            let isInputRequired = false;
            // Use the existing config object
            const stream = await this.agent.stream(input, {
                ...config,
                streamMode: "values",
            });
            for await (const chunk of stream) {
                // Extract messages from the chunk
                const messages = chunk.messages || [];
                // Check for cancellation during execution
                if (this.cancelledTasks.has(taskId)) {
                    console.log(`[ReactAgentExecutor] Request cancelled during execution for task: ${taskId}`);
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
                // Get the latest message content if available
                const lastMessage = messages.length > 0 ? messages[messages.length - 1] : null;
                let messageContent = '';
                if (lastMessage) {
                    if (lastMessage.content) {
                        messageContent = typeof lastMessage.content === 'string'
                            ? lastMessage.content
                            : lastMessage.content.toString();
                    }
                    else if (lastMessage.tool_calls && lastMessage.tool_calls.length > 0) {
                        messageContent = JSON.stringify(lastMessage.tool_calls);
                    }
                    else {
                        messageContent = JSON.stringify(lastMessage);
                    }
                }
                else {
                    // If no message is available, use the entire chunk for debugging
                    messageContent = JSON.stringify(chunk);
                }
                // Update the final response
                finalResponse = messageContent;
                // Check if we need more input based on the agent's state
                isInputRequired = chunk.next !== 'END';
                // Send intermediate updates
                const intermediateUpdate = {
                    kind: 'status-update',
                    taskId: taskId,
                    contextId: contextId,
                    status: {
                        state: "working",
                        message: {
                            kind: 'message',
                            role: 'agent',
                            messageId: uuidv4(),
                            parts: [{ kind: 'text', text: messageContent }],
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
                messageId: uuidv4(),
                parts: [{ kind: 'text', text: finalResponse || "Completed." }],
                taskId: taskId,
                contextId: contextId,
            };
            historyForAgent.push(agentMessage);
            contexts.set(contextId, historyForAgent);
            // 6. Publish final task status update
            const finalState = isInputRequired ? "input-required" : "completed";
            const finalUpdate = {
                kind: 'status-update',
                taskId: taskId,
                contextId: contextId,
                status: {
                    state: finalState,
                    message: agentMessage,
                    timestamp: new Date().toISOString(),
                },
                final: true,
            };
            eventBus.publish(finalUpdate);
            console.log(`[ReactAgentExecutor] Task ${taskId} finished with state: ${finalState}`);
        }
        catch (error) {
            console.error(`[ReactAgentExecutor] Error processing task ${taskId}:`, error);
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
    }
}
//# sourceMappingURL=agent_executor.js.map