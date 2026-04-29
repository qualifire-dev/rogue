import { Message, Task, TaskStatusUpdateEvent, TextPart } from '@a2a-js/sdk';
import { AgentExecutor, ExecutionEventBus, RequestContext } from '@a2a-js/sdk/server';
import {
  Agent,
  AgentInputItem,
  isOpenAIResponsesRawModelStreamEvent,
  run,
} from '@openai/agents';

import { v4 as uuidv4 } from 'uuid';

const MAX_CONTEXTS = 500;
const MAX_MESSAGES_PER_CONTEXT = 100;
const CONTEXT_TTL_MS = 30 * 60 * 1000; // 30 minutes

export class OpenAIAgentExecutor implements AgentExecutor {
  private cancelledTasks = new Set<string>();
  private agent: Agent;
  private contexts = new Map<string, Message[]>();
  private contextLastAccess = new Map<string, number>();
  private cleanupTimer: ReturnType<typeof setInterval>;

  constructor(agent: Agent) {
    this.agent = agent;
    this.cleanupTimer = setInterval(() => this.evictExpiredContexts(), 5 * 60 * 1000);
    this.cleanupTimer.unref();
  }

  private evictExpiredContexts(): void {
    const now = Date.now();
    for (const [contextId, lastAccess] of this.contextLastAccess) {
      if (now - lastAccess > CONTEXT_TTL_MS) {
        this.contexts.delete(contextId);
        this.contextLastAccess.delete(contextId);
      }
    }
  }

  private touchContext(contextId: string, history: Message[]): void {
    // Trim to keep only the most recent messages
    if (history.length > MAX_MESSAGES_PER_CONTEXT) {
      history.splice(0, history.length - MAX_MESSAGES_PER_CONTEXT);
    }

    // Evict the oldest entry when at capacity
    if (!this.contexts.has(contextId) && this.contexts.size >= MAX_CONTEXTS) {
      let oldestId: string | null = null;
      let oldestTime = Infinity;
      for (const [id, time] of this.contextLastAccess) {
        if (time < oldestTime) {
          oldestTime = time;
          oldestId = id;
        }
      }
      if (oldestId) {
        this.contexts.delete(oldestId);
        this.contextLastAccess.delete(oldestId);
      }
    }

    this.contexts.set(contextId, history);
    this.contextLastAccess.set(contextId, Date.now());
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
          state: 'submitted',
          timestamp: new Date().toISOString(),
        },
        history: [userMessage],
        metadata: userMessage.metadata,
      };
      eventBus.publish(initialTask);
    }

    // 2. Publish "working" status update
    const workingStatusUpdate: TaskStatusUpdateEvent = {
      kind: 'status-update',
      taskId: taskId,
      contextId: contextId,
      status: {
        state: 'working',
        message: {
          kind: 'message',
          role: 'agent',
          messageId: uuidv4(),
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
    const historyForAgent = this.contexts.get(contextId) || [];
    this.contextLastAccess.set(contextId, Date.now());
    if (!historyForAgent.find(m => m.messageId === userMessage.messageId)) {
      historyForAgent.push(userMessage);
    }
    this.touchContext(contextId, historyForAgent);

    // Convert A2A messages to OpenAI format, dropping entries with no usable text
    const messages: AgentInputItem[] = historyForAgent
      .map(m => ({
        role: (m.role === 'agent' ? 'assistant' : 'user') as 'assistant' | 'user',
        content: m.parts
          .filter((p): p is TextPart => p.kind === 'text' && !!(p as TextPart).text)
          .map(p => (p as TextPart).text)
          .join('\n'),
      }))
      .filter(m => m.content.trim().length > 0);

    if (messages.length === 0) {
      console.warn(
        `[OpenAIAgentExecutor] No valid text messages found in history for task ${taskId}.`
      );
      const failureUpdate: TaskStatusUpdateEvent = {
        kind: 'status-update',
        taskId: taskId,
        contextId: contextId,
        status: {
          state: 'failed',
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
      this.cancelledTasks.delete(taskId);
      return;
    }

    try {
      // Check if the task has been cancelled before starting
      if (this.cancelledTasks.has(taskId)) {
        console.log(`[OpenAIAgentExecutor] Request cancelled for task: ${taskId}`);

        const cancelledUpdate: TaskStatusUpdateEvent = {
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
        this.cancelledTasks.delete(taskId);
        return;
      }

      // 4. Run the OpenAI agent with streaming
      const controller = new AbortController();
      const stream = await run(this.agent, messages, {
        stream: true,
        signal: controller.signal,
      });

      let finalResponse = '';

      for await (const event of stream) {
        // Check for cancellation during execution
        if (this.cancelledTasks.has(taskId)) {
          console.log(`[OpenAIAgentExecutor] Request cancelled during execution for task: ${taskId}`);

          controller.abort();

          const cancelledUpdate: TaskStatusUpdateEvent = {
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
          this.cancelledTasks.delete(taskId);
          return;
        }

        // Handle text delta events from the underlying model
        if (
          isOpenAIResponsesRawModelStreamEvent(event) &&
          event.data.type === 'model' &&
          event.data.event.type === 'response.output_text.delta'
        ) {
          const delta = event.data.event.delta;
          finalResponse += delta;

          const intermediateUpdate: TaskStatusUpdateEvent = {
            kind: 'status-update',
            taskId: taskId,
            contextId: contextId,
            status: {
              state: 'working',
              message: {
                kind: 'message',
                role: 'agent',
                messageId: uuidv4(),
                parts: [{ kind: 'text', text: delta }],
                taskId: taskId,
                contextId: contextId,
              },
              timestamp: new Date().toISOString(),
            },
            final: false,
          };
          eventBus.publish(intermediateUpdate);
        }
      }

      // Fall back to finalOutput if no text deltas were streamed (e.g. tool-only turns)
      await stream.completed;
      if (!finalResponse) {
        finalResponse = stream.finalOutput ?? 'Completed.';
      }

      // 5. Create the agent's final message
      const agentMessage: Message = {
        kind: 'message',
        role: 'agent',
        messageId: uuidv4(),
        parts: [{ kind: 'text', text: finalResponse }],
        taskId: taskId,
        contextId: contextId,
      };
      historyForAgent.push(agentMessage);
      this.touchContext(contextId, historyForAgent);

      // 6. Publish final task status update
      const finalUpdate: TaskStatusUpdateEvent = {
        kind: 'status-update',
        taskId: taskId,
        contextId: contextId,
        status: {
          state: 'completed',
          message: agentMessage,
          timestamp: new Date().toISOString(),
        },
        final: true,
      };
      eventBus.publish(finalUpdate);
      this.cancelledTasks.delete(taskId);

      console.log(
        `[OpenAIAgentExecutor] Task ${taskId} finished with state: completed`
      );

    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      console.error(
        `[OpenAIAgentExecutor] Error processing task ${taskId}:`,
        error
      );
      const errorUpdate: TaskStatusUpdateEvent = {
        kind: 'status-update',
        taskId: taskId,
        contextId: contextId,
        status: {
          state: 'failed',
          message: {
            kind: 'message',
            role: 'agent',
            messageId: uuidv4(),
            parts: [{ kind: 'text', text: `Agent error: ${errorMessage}` }],
            taskId: taskId,
            contextId: contextId,
          },
          timestamp: new Date().toISOString(),
        },
        final: true,
      };
      eventBus.publish(errorUpdate);
      this.cancelledTasks.delete(taskId);
    }
  }
}
