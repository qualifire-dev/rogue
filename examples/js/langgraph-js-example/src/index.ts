import { A2AExpressApp, DefaultRequestHandler, InMemoryTaskStore, TaskStore } from '@a2a-js/sdk/server';
import { ReactAgentExecutor } from './agentExecutor.js';
import express from 'express';
import { AgentCapabilities, AgentCard, AgentSkill } from '@a2a-js/sdk';
import { agent } from './agent.js';

function getAgentCard(): AgentCard {
  const skills = [
    {
      id: 'sell_tshirt',
      name: 'Sell T-Shirt',
      description: 'Helps with selling T-Shirts',
      tags: ['sell'],
    } as AgentSkill,
  ];

  const host = process.env.HOST || 'localhost';
  const port = process.env.PORT || 3000

  return {
    name: 'Shirtify TShirt Store Agent',
    description: 'Sells Shirtify T-Shirts',
    url: `http://${host}:${port}/`,
    version: '1.0.0',
    defaultInputModes: ['text'],
    defaultOutputModes: ['text'],
    capabilities: { streaming: true } as AgentCapabilities,
    skills,
  } as AgentCard;
}

async function main() {
  const taskStore: TaskStore = new InMemoryTaskStore();
  const agentExecutor: ReactAgentExecutor = new ReactAgentExecutor(agent);

  // 3. Create DefaultRequestHandler
  const requestHandler = new DefaultRequestHandler(
    getAgentCard(),
    taskStore,
    agentExecutor
  );

  // 4. Create and setup A2AExpressApp
  const app = express();
  const appBuilder = new A2AExpressApp(requestHandler);
  // Use type assertion to work around Express type incompatibility
  const expressApp = appBuilder.setupRoutes(app as any);

  // 5. Start the server
  const PORT = process.env.PORT || 3000;
  const server = expressApp.listen(PORT, () => {
    console.log(`[ReactAgent] Server using langchain framework and A2A started on http://localhost:${PORT}`);
    console.log(`[ReactAgent] Agent Card: http://localhost:${PORT}/.well-known/agent.json`);
    console.log('[ReactAgent] Press Ctrl+C to stop the server');
  });

  // 6. Setup graceful shutdown
  const shutdown = async () => {
    console.log('\n[ReactAgent] Shutting down server...');

    // Close the HTTP server
    server.close(() => {
      console.log('[ReactAgent] HTTP server closed');
    });

    process.exit(0);
  };

  // Handle termination signals
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

// Call the main function to start the server
main().catch(error => {
  console.error('Error starting server:', error);
  process.exit(1);
});
