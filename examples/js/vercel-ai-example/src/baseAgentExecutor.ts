import { Message, Task, TaskState, TaskStatusUpdateEvent } from '@a2a-js/sdk';
import { AgentExecutor, ExecutionEventBus, RequestContext } from '@a2a-js/sdk/server';

import { v4 as uuidv4 } from 'uuid';
import { VercelAgent } from './agent';

// Store for conversation contexts
const contexts = new Map<string, Message[]>();

export abstract class BaseAgentExecutor implements AgentExecutor {
  private cancelledTasks = new Set<string>();
  protected readonly agent: VercelAgent;

  protected constructor(agent: VercelAgent) {
    this.agent = agent;
  }

  public cancelTask = async (
    taskId: string,
    eventBus: ExecutionEventBus,
  ): Promise<void> => {
    this.cancelledTasks.add(taskId);
    // The execute loop is responsible for publishing the final state
  };

  private publishInitialTask(eventBus: ExecutionEventBus, taskId: string, contextId: string, userMessage: Message) {
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

  private publishStatusUpdate(
    eventBus: ExecutionEventBus,
    taskId: string,
    contextId: string,
    messageText: string | null = null,
    state: TaskState = "working",
    final: boolean = false,
  ) {
    const workingStatusUpdate: TaskStatusUpdateEvent = {
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

  private publishTaskCancellation(
    taskId: string,
    contextId: string,
    eventBus: ExecutionEventBus,
  ): void {
    console.log(`[AgentExecutor] Request cancelled for task: ${taskId}`);
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
  }

  private publishTaskCompletion(
    taskId: string,
    contextId: string,
    eventBus: ExecutionEventBus,
  ): void {
    const finalUpdate: TaskStatusUpdateEvent = {
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

  private publishTaskError(
    taskId: string,
    contextId: string,
    eventBus: ExecutionEventBus,
    error: any,
  ): void {
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

  private addMessageToHistory(contextId: string, message: Message): Message[] {
    const historyForAgent = contexts.get(contextId) || [];
    if (!historyForAgent.find(m => m.messageId === message.messageId)) {
      historyForAgent.push(message);
      contexts.set(contextId, historyForAgent);
    }

    return historyForAgent;
  }

  private async handleStreamResponse(
    eventBus: ExecutionEventBus,
    taskId: string,
    contextId: string,
    existingTask: Task | undefined,
    userMessage: Message,
    response: ReadableStream<string>,
  ): Promise<string> {
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

  protected abstract runAgent(messages: Message[]): Promise<string | ReadableStream<string>>;

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
      `[VercelAgentExecutor] Processing message ${userMessage.messageId} for task ${taskId} (context: ${contextId})`
    );

    const historyForAgent: Message[] = this.addMessageToHistory(contextId, userMessage);

    // Check if the task has been cancelled before starting
    if (this.cancelledTasks.has(taskId)) {
      this.publishTaskCancellation(taskId, contextId, eventBus);
      return;
    }

    try {
      // Run the agent - Can return a stream or a string.
      const response: string | ReadableStream<string> = await this.runAgent(historyForAgent);

      // Create the agent's final message for the history - we will fill the parts later
      const agentMessage: Message = {
        kind: 'message',
        role: 'agent',
        messageId: uuidv4(),
        parts: [],  // We will fill this later
        taskId: taskId,
        contextId: contextId,
      };

      if (response instanceof ReadableStream) {
        const aggregatedResponse: string = await this.handleStreamResponse(eventBus, taskId, contextId, existingTask, userMessage, response);
        agentMessage.parts.push({kind: 'text', text: aggregatedResponse});
      } else { // response is a string
        // TODO
      }

      // Adding the message to the history
      this.addMessageToHistory(contextId, agentMessage);

      console.log(`[AgentExecutor] Task ${taskId} finished with state: completed`);
    } catch (error: any) {
      console.error(`[AgentExecutor] Error processing task ${taskId}:`,error);
      this.publishTaskError(taskId, contextId, eventBus, error);
    }
  }
}
