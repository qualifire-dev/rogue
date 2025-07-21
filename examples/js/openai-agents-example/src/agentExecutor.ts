import { Message, Task, TaskStatusUpdateEvent, TextPart } from '@a2a-js/sdk';
import { AgentExecutor, ExecutionEventBus, RequestContext } from '@a2a-js/sdk/server';

import { v4 as uuidv4 } from 'uuid';
import { run } from '@openai/agents';

// Store for conversation contexts
const contexts = new Map<string, Message[]>();

export class OpenAIAgentExecutor implements AgentExecutor {
  private cancelledTasks = new Set<string>();
  private agent: any;

  constructor(agent: any) {
    this.agent = agent;
  }

  public cancelTask = async (
    taskId: string,
    eventBus: ExecutionEventBus,
  ): Promise<void> => {
    this.cancelledTasks.add(taskId);
    // The execute loop is responsible for publishing the final state
  };

  async execute(
    requestContext: RequestContext,
    eventBus: ExecutionEventBus
  ): Promise<void> {
    const userMessage = requestContext.userMessage;
    const existingTask = requestContext.task;

    // Determine IDs for the task and context
    const taskId = existingTask?.id || uuidv4();
    const contextId = userMessage.contextId || existingTask?.contextId || uuidv4();

    console.log(
      `[OpenAIAgentExecutor] Processing message ${userMessage.messageId} for task ${taskId} (context: ${contextId})`
    );

    // 1. Publish initial Task event if it's a new task
    if (!existingTask) {
      const initialTask: Task = {
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
    const workingStatusUpdate: TaskStatusUpdateEvent = {
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
        .filter((p): p is TextPart => p.kind === 'text' && !!(p as TextPart).text)
        .map(p => (p as TextPart).text)
        .join('\n')
    }));

    if (messages.length === 0) {
      console.warn(
        `[OpenAIAgentExecutor] No valid text messages found in history for task ${taskId}.`
      );
      const failureUpdate: TaskStatusUpdateEvent = {
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
        console.log(`[OpenAIAgentExecutor] Request cancelled for task: ${taskId}`);

        const cancelledUpdate: TaskStatusUpdateEvent = {
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
      const stream = await run(this.agent, input, {stream: true});

      for await (const event of stream) {
        if (event.type === 'raw_model_stream_event') {
          // Send intermediate updates
          const intermediateUpdate: TaskStatusUpdateEvent = {
            kind: 'status-update',
            taskId: taskId,
            contextId: contextId,
            status: {
              state: "working",
              message: {
                kind: 'message',
                role: 'agent',
                messageId: uuidv4(),
                parts: [{ kind: 'text', text: event.data }],
                taskId: taskId,
                contextId: contextId,
              },
              timestamp: new Date().toISOString(),
            },
            final: false,
          };
          eventBus.publish(intermediateUpdate);
        }
        // agent updated events
        if (event.type === 'agent_updated_stream_event') {
          console.log(`${event.type} %s`, event.agent.name);
        }
        // Agent SDK specific events
        if (event.type === 'run_item_stream_event') {
          console.log(`${event.type} %o`, event.item);
        }
      }

      // 5. Create the agent's final message
      // const agentMessage: Message = {
      //   kind: 'message',
      //   role: 'agent',
      //   messageId: uuidv4(),
      //   parts: [{ kind: 'text', text: finalResponse || "Completed." }],
      //   taskId: taskId,
      //   contextId: contextId,
      // };
      // historyForAgent.push(agentMessage);
      // contexts.set(contextId, historyForAgent);

      // 6. Publish final task status update
      const finalState = isInputRequired ? "input-required" : "completed";

      const finalUpdate: TaskStatusUpdateEvent = {
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

      console.log(
        `[OpenAIAgentExecutor] Task ${taskId} finished with state: ${finalState}`
      );

    } catch (error: any) {
      console.error(
        `[OpenAIAgentExecutor] Error processing task ${taskId}:`,
        error
      );
      const errorUpdate: TaskStatusUpdateEvent = {
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
