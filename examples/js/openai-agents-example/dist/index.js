import { A2AExpressApp, DefaultRequestHandler, InMemoryTaskStore } from '@a2a-js/sdk/server';
import express from 'express';
import { agent } from './agent.js';
import { OpenAINonStreamExecutor, OpenAIStreamExecutor } from './agentExecutor.js';
function getAgentCard() {
    const skills = [
        {
            id: 'sell_tshirt',
            name: 'Sell T-Shirt',
            description: 'Helps with selling T-Shirts',
            tags: ['sell'],
        },
    ];
    const host = process.env.HOST || 'localhost';
    const port = Number(process.env.PORT || 3000);
    return {
        name: 'Shirtify TShirt Store Agent',
        description: 'Sells Shirtify T-Shirts',
        url: `http://${host}:${port}/`,
        version: '1.0.0',
        defaultInputModes: ['text'],
        defaultOutputModes: ['text'],
        capabilities: { streaming: true },
        skills,
    };
}
async function main() {
    const stream = (process.env.STREAM || "").toLowerCase() === 'true';
    const taskStore = new InMemoryTaskStore();
    let agentExecutor;
    if (stream) {
        agentExecutor = new OpenAIStreamExecutor(agent);
        console.log("[A2A Agent] Using OpenAIStreamExecutor");
    }
    else {
        agentExecutor = new OpenAINonStreamExecutor(agent);
        console.log("[A2A Agent] Using OpenAINonStreamExecutor");
    }
    // 3. Create DefaultRequestHandler
    const requestHandler = new DefaultRequestHandler(getAgentCard(), taskStore, agentExecutor);
    // 4. Create and setup A2AExpressApp
    const app = express();
    const appBuilder = new A2AExpressApp(requestHandler);
    // Use type assertion to work around Express type incompatibility
    const expressApp = appBuilder.setupRoutes(app);
    // 5. Start the server
    const PORT = Number(process.env.PORT || 3000);
    const server = expressApp.listen(PORT, () => {
        console.log(`[A2A Agent] Server using @openai/agents framework and A2A started on http://localhost:${PORT}`);
        console.log(`[A2A Agent] Agent Card: http://localhost:${PORT}/.well-known/agent.json`);
        console.log('[A2A Agent] Press Ctrl+C to stop the server');
    });
    // 6. Setup graceful shutdown
    const shutdown = async () => {
        console.log('\n[A2A Agent] Shutting down server...');
        // Close the HTTP server
        server.close(() => {
            console.log('[A2A Agent] HTTP server closed');
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
//# sourceMappingURL=index.js.map