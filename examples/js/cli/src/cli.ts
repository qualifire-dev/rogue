#!/usr/bin/env node

import readline from 'node:readline';
import crypto from 'node:crypto';

import {
  AgentCard, DataPart, FilePart, Message, MessageSendParams, Part, Task, TaskArtifactUpdateEvent, TaskStatusUpdateEvent,
} from '@a2a-js/sdk';

import { A2AClient } from '@a2a-js/sdk/client';

// --- ANSI Colors ---
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  dim: "\x1b[2m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m",
  gray: "\x1b[90m",
};

// --- Helper Functions ---
function colorize(color: keyof typeof colors, text: string): string {
  return `${colors[color]}${text}${colors.reset}`;
}

function generateId(): string {
  return crypto.randomUUID();
}

// --- State ---
let currentTaskId: string | undefined = undefined;
let currentContextId: string | undefined = undefined;
const serverUrl = process.argv[2] || "http://localhost:3000";
const client = new A2AClient(serverUrl);
let agentName = "ReactAgent";

// --- Readline Setup ---
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: colorize("cyan", "You: "),
});

// --- Response Handling ---
function printAgentEvent(
  event: TaskStatusUpdateEvent | TaskArtifactUpdateEvent
) {
  const timestamp = new Date().toLocaleTimeString();
  const prefix = colorize("magenta", `\n${agentName} [${timestamp}]:`);

  // Check if it's a TaskStatusUpdateEvent
  if (event.kind === "status-update") {
    const update = event as TaskStatusUpdateEvent;
    const state = update.status.state;
    let stateEmoji = "❓";
    let stateColor: keyof typeof colors = "yellow";

    switch (state) {
      case "working":
        stateEmoji = "⏳";
        stateColor = "blue";
        break;
      case "input-required":
        stateEmoji = "🤔";
        stateColor = "yellow";
        break;
      case "completed":
        stateEmoji = "✅";
        stateColor = "green";
        break;
      case "canceled":
        stateEmoji = "⏹️";
        stateColor = "gray";
        break;
      case "failed":
        stateEmoji = "❌";
        stateColor = "red";
        break;
      default:
        stateEmoji = "ℹ️";
        stateColor = "dim";
        break;
    }

    console.log(
      `${prefix} ${stateEmoji} Status: ${colorize(stateColor, state)} (Task: ${update.taskId}, Context: ${update.contextId}) ${update.final ? colorize("bright", "[FINAL]") : ""}`
    );

    if (update.status.message) {
      printMessageContent(update.status.message);
    }
  }
  // Check if it's a TaskArtifactUpdateEvent
  else if (event.kind === "artifact-update") {
    const update = event as TaskArtifactUpdateEvent;
    console.log(
      `${prefix} 📄 Artifact Received: ${update.artifact.name || "(unnamed)"
      } (ID: ${update.artifact.artifactId}, Task: ${update.taskId}, Context: ${update.contextId})`
    );
    // Create a temporary message-like structure to reuse printMessageContent
    printMessageContent({
      messageId: generateId(),
      kind: "message",
      role: "agent",
      parts: update.artifact.parts,
      taskId: update.taskId,
      contextId: update.contextId,
    });
  } else {
    console.log(
      prefix,
      colorize("yellow", "Received unknown event type in printAgentEvent:"),
      event
    );
  }
}

function printMessageContent(message: Message) {
  message.parts.forEach((part: Part, index: number) => {
    const partPrefix = colorize("red", `  Part ${index + 1}:`);
    if (part.kind === "text") {
      console.log(`${partPrefix} ${colorize("green", "📝 Text:")}`, part.text);
    } else if (part.kind === "file") {
      const filePart = part as FilePart;
      console.log(
        `${partPrefix} ${colorize("blue", "📄 File:")} Name: ${filePart.file.name || "N/A"
        }, Type: ${filePart.file.mimeType || "N/A"}, Source: ${("bytes" in filePart.file) ? "Inline (bytes)" : filePart.file.uri
        }`
      );
    } else if (part.kind === "data") {
      const dataPart = part as DataPart;
      console.log(
        `${partPrefix} ${colorize("yellow", "📊 Data:")}`,
        JSON.stringify(dataPart.data, null, 2)
      );
    } else {
      console.log(`${partPrefix} ${colorize("yellow", "Unsupported part kind:")}`, part);
    }
  });
}

// --- Agent Card Fetching ---
async function fetchAndDisplayAgentCard() {
  console.log(
    colorize("dim", `Attempting to fetch agent card from agent at: ${serverUrl}`)
  );
  try {
    const card: AgentCard = await client.getAgentCard();
    agentName = card.name || "ReactAgent";
    console.log(colorize("green", `✓ Agent Card Found:`));
    console.log(`  Name:        ${colorize("bright", agentName)}`);
    if (card.description) {
      console.log(`  Description: ${card.description}`);
    }
    console.log(`  Version:     ${card.version || "N/A"}`);
    if (card.capabilities?.streaming) {
      console.log(`  Streaming:   ${colorize("green", "Supported")}`);
    } else {
      console.log(`  Streaming:   ${colorize("yellow", "Not Supported (or not specified)")}`);
    }
  } catch (error: any) {
    console.log(
      colorize("yellow", `⚠️ Error fetching or parsing agent card`)
    );
    throw error;
  }
}

// --- Main Loop ---
async function main() {
  console.log(colorize("bright", `A2A Terminal Client`));
  console.log(colorize("dim", `Agent Base URL: ${serverUrl}`));

  await fetchAndDisplayAgentCard();

  console.log(colorize("dim", `No active task or context initially. Use '/new' to start a fresh session or send a message.`));
  console.log(
    colorize("green", `Enter messages, or use '/new' to start a new session. '/exit' to quit.`)
  );

  rl.setPrompt(colorize("cyan", `${agentName} > You: `));
  rl.prompt();

  rl.on("line", async (line) => {
    const input = line.trim();
    rl.setPrompt(colorize("cyan", `${agentName} > You: `));

    if (!input) {
      rl.prompt();
      return;
    }

    if (input.toLowerCase() === "/new") {
      currentTaskId = undefined;
      currentContextId = undefined;
      console.log(
        colorize("bright", `✨ Starting new session. Task and Context IDs are cleared.`)
      );
      rl.prompt();
      return;
    }

    if (input.toLowerCase() === "/exit") {
      rl.close();
      return;
    }

    // Construct params for sendMessageStream
    const messageId = generateId();

    const messagePayload: Message = {
      messageId: messageId,
      kind: "message",
      role: "user",
      parts: [
        {
          kind: "text",
          text: input,
        },
      ],
    };

    // Conditionally add taskId to the message payload
    if (currentTaskId) {
      messagePayload.taskId = currentTaskId;
    }
    // Conditionally add contextId to the message payload
    if (currentContextId) {
      messagePayload.contextId = currentContextId;
    }

    const params: MessageSendParams = {
      message: messagePayload,
    };

    try {
      console.log(colorize("red", "Sending message..."));
      // Use sendMessageStream
      const stream = client.sendMessageStream(params);

      // Iterate over the events from the stream
      for await (const event of stream) {
        const timestamp = new Date().toLocaleTimeString();
        const prefix = colorize("magenta", `\n${agentName} [${timestamp}]:`);

        if (event.kind === "status-update" || event.kind === "artifact-update") {
          const typedEvent = event as TaskStatusUpdateEvent | TaskArtifactUpdateEvent;
          printAgentEvent(typedEvent);

          // If the event is a TaskStatusUpdateEvent and it's final, reset currentTaskId
          if (typedEvent.kind === "status-update" && (typedEvent as TaskStatusUpdateEvent).final && (typedEvent as TaskStatusUpdateEvent).status.state !== "input-required") {
            console.log(colorize("yellow", `   Task ${typedEvent.taskId} is final. Clearing current task ID.`));
            currentTaskId = undefined;
          }

        } else if (event.kind === "message") {
          const msg = event as Message;
          console.log(`${prefix} ${colorize("green", "✉️ Message Stream Event:")}`);
          printMessageContent(msg);
          if (msg.taskId && msg.taskId !== currentTaskId) {
            console.log(colorize("dim", `   Task ID context updated to ${msg.taskId} based on message event.`));
            currentTaskId = msg.taskId;
          }
          if (msg.contextId && msg.contextId !== currentContextId) {
            console.log(colorize("dim", `   Context ID updated to ${msg.contextId} based on message event.`));
            currentContextId = msg.contextId;
          }
        } else if (event.kind === "task") {
          const task = event as Task;
          console.log(`${prefix} ${colorize("blue", "ℹ️ Task Stream Event:")} ID: ${task.id}, Context: ${task.contextId}, Status: ${task.status.state}`);
          if (task.id !== currentTaskId) {
            console.log(colorize("dim", `   Task ID updated from ${currentTaskId || 'N/A'} to ${task.id}`));
            currentTaskId = task.id;
          }
          if (task.contextId && task.contextId !== currentContextId) {
            console.log(colorize("dim", `   Context ID updated from ${currentContextId || 'N/A'} to ${task.contextId}`));
            currentContextId = task.contextId;
          }
          if (task.status.message) {
            console.log(colorize("gray", "   Task includes message:"));
            printMessageContent(task.status.message);
          }
          if (task.artifacts && task.artifacts.length > 0) {
            console.log(colorize("gray", `   Task includes ${task.artifacts.length} artifact(s).`));
          }
        } else {
          console.log(prefix, colorize("yellow", "Received unknown event structure from stream:"), event);
        }
      }
      console.log(colorize("dim", `--- End of response stream for this input ---`));
    } catch (error: any) {
      const timestamp = new Date().toLocaleTimeString();
      const prefix = colorize("red", `\n${agentName} [${timestamp}] ERROR:`);
      console.error(
        prefix,
        `Error communicating with agent:`,
        error.message || error
      );
      if (error.code) {
        console.error(colorize("gray", `   Code: ${error.code}`));
      }
      if (error.data) {
        console.error(
          colorize("gray", `   Data: ${JSON.stringify(error.data)}`)
        );
      }
      if (!(error.code || error.data) && error.stack) {
        console.error(colorize("gray", error.stack.split('\n').slice(1, 3).join('\n')));
      }
    } finally {
      rl.prompt();
    }
  }).on("close", () => {
    console.log(colorize("yellow", "\nExiting A2A Terminal Client. Goodbye!"));
    process.exit(0);
  });
}

// --- Start ---
main().catch(err => {
  console.error(colorize("red", "Unhandled error in main:"), err);
  process.exit(1);
});
